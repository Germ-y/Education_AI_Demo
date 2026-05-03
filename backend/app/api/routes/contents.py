from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.ai.elevenlabs_provider import ElevenLabsProvider
from app.ai.openai_provider import OpenAiProvider
from app.ai.provider_errors import AiProviderError
from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.domain.enums import AssetRole, AssetType
from app.domain.schemas import ContentApprovalRequest, ContentRejectRequest, ContentReviewUpdateRequest
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/contents", tags=["contents"])


@router.get("/{content_id}")
def get_content(
    content_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if content is None:
        raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})
    return ok(content.model_dump(by_alias=True))


@router.post("/{content_id}/approve")
def approve_content(
    content_id: str,
    payload: ContentApprovalRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.approve_mission_content(
        content_id,
        principal.id,
        payload.approved_stage_ids,
        payload.approved_asset_ids,
        payload.review_note,
    )
    if content is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "CONTENT_APPROVAL_FAILED", "message": "승인할 수 없는 콘텐츠입니다. 단계와 asset 승인 목록을 확인해 주세요."},
        )
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=content.student_id,
        action="approve_content",
        resource_type="mission_content",
        resource_id=content.id,
        payload_json={"reviewNote": payload.review_note},
    )
    return ok(content.model_dump(by_alias=True))


@router.post("/{content_id}/reject")
def reject_content(
    content_id: str,
    payload: ContentRejectRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.reject_mission_content(content_id, principal.id, payload.reason, payload.requested_changes)
    if content is None:
        raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=content.student_id,
        action="reject_content",
        resource_type="mission_content",
        resource_id=content.id,
        payload_json={"reason": payload.reason, "requestedChanges": payload.requested_changes},
    )
    return ok(content.model_dump(by_alias=True))


@router.patch("/{content_id}/review")
def update_content_review(
    content_id: str,
    payload: ContentReviewUpdateRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.update_mission_content_review(content_id, principal.id, payload.stages)
    if content is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "CONTENT_REVIEW_UPDATE_FAILED", "message": "수업 자료 수정 내용을 저장하지 못했습니다."},
        )
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=content.student_id,
        action="update_content_review",
        resource_type="mission_content",
        resource_id=content.id,
        payload_json={"stageCount": len(payload.stages)},
    )
    return ok(content.model_dump(by_alias=True))


@router.post("/{content_id}/assets/{asset_id}/generate")
def generate_content_asset(
    content_id: str,
    asset_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if content is None:
        raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})
    asset = next((candidate for candidate in content.assets if candidate.id == asset_id), None)
    if asset is None:
        raise HTTPException(status_code=404, detail={"code": "ASSET_NOT_FOUND", "message": "생성할 asset을 찾을 수 없습니다."})

    _generate_asset_or_raise(content_id, asset)

    demo_store.save_generated_mission_content(content)
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=content.student_id,
        action="generate_asset",
        resource_type="content_asset",
        resource_id=asset.id,
        payload_json={"contentId": content.id, "assetType": asset.asset_type, "assetRole": asset.asset_role},
    )
    return ok(asset.model_dump(by_alias=True))


@router.post("/{content_id}/assets/generate-package")
def generate_content_asset_package(
    content_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if content is None:
        raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})

    _validate_required_asset_package(content)
    _preflight_provider_keys(content)

    generated = []
    for asset in sorted(content.assets, key=lambda item: (item.asset_type, item.asset_role, item.id)):
        _generate_asset_or_raise(content_id, asset)
        generated.append(asset.model_dump(by_alias=True))
        demo_store.save_generated_mission_content(content)

    demo_store.save_generated_mission_content(content)
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=content.student_id,
        action="generate_asset_package",
        resource_type="mission_content",
        resource_id=content.id,
        payload_json={"generatedCount": len(generated)},
    )
    return ok({"contentId": content.id, "generatedCount": len(generated), "assets": generated})


@router.post("/{content_id}/review-summary")
def create_review_summary(
    content_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    summary = demo_store.create_review_summary_for_content(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "REVIEW_SUMMARY_NOT_AVAILABLE", "message": "요약할 학생 시도 또는 콘텐츠를 찾을 수 없습니다."},
        )
    return ok(summary.model_dump(by_alias=True))


@router.get("/{content_id}/review-summary")
def get_review_summary(
    content_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    summary = demo_store.get_latest_review_summary_for_content(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if summary is None:
        raise HTTPException(status_code=404, detail={"code": "REVIEW_SUMMARY_NOT_FOUND", "message": "리뷰 요약을 찾을 수 없습니다."})
    return ok(summary.model_dump(by_alias=True))


@router.post("/{content_id}/publish")
def publish_content(
    content_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.publish_mission_content(content_id, principal.id)
    if content is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "CONTENT_PUBLISH_FAILED", "message": "승인 완료된 콘텐츠만 배포할 수 있습니다."},
        )
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=content.student_id,
        action="publish_content",
        resource_type="mission_content",
        resource_id=content.id,
        payload_json={},
    )
    return ok(content.model_dump(by_alias=True))


def _generate_asset_or_raise(content_id: str, asset) -> None:
    settings = get_settings()
    try:
        if asset.asset_type == AssetType.IMAGE:
            prompt = _extract_image_prompt(asset.prompt_json)
            relative_path = _generated_asset_relative_path(content_id, asset)
            output_path = _generated_file_path(relative_path)
            if not _is_generated_file_ready(output_path):
                OpenAiProvider(settings).create_image_file(
                    prompt=prompt,
                    output_path=output_path,
                    model=settings.openai_image_model,
                    timeout_sec=settings.openai_image_timeout_sec,
                )
            _apply_generated_asset_metadata(asset, relative_path, provider="openai", model=settings.openai_image_model)
        elif asset.asset_type == AssetType.AUDIO:
            if not asset.source_text:
                raise HTTPException(status_code=400, detail={"code": "ASSET_SOURCE_TEXT_MISSING", "message": "TTS asset sourceText가 필요합니다."})
            relative_path = _generated_asset_relative_path(content_id, asset)
            output_path = _generated_file_path(relative_path)
            if not _is_generated_file_ready(output_path):
                ElevenLabsProvider(settings).create_speech_file(source_text=asset.source_text, output_path=output_path)
            _apply_generated_asset_metadata(asset, relative_path, provider="elevenlabs", model="eleven_multilingual_v2")
        else:
            raise HTTPException(status_code=400, detail={"code": "ASSET_TYPE_NOT_SUPPORTED", "message": "지원하지 않는 assetType입니다."})
    except AiProviderError as exc:
        raise HTTPException(
            status_code=424,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "assetId": asset.id},
            },
        ) from exc


def _generated_asset_relative_path(content_id: str, asset) -> str:
    extension = "png" if asset.asset_type == AssetType.IMAGE else "mp3"
    return f"assets/{content_id}/{asset.id}.{extension}"


def _is_generated_file_ready(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def _apply_generated_asset_metadata(asset, relative_path: str, *, provider: str, model: str) -> None:
    asset.storage_url = f"/generated/{relative_path}"
    asset.preview_url = asset.storage_url
    asset.provider = provider
    asset.model = model
    asset.qa_status = "passed"
    if asset.approval_status != "approved":
        asset.approval_status = "pending"


def _validate_required_asset_package(content) -> None:
    required_roles = {role.value for role in AssetRole}
    image_roles = {asset.asset_role for asset in content.assets if asset.asset_type == AssetType.IMAGE}
    audio_roles = {asset.asset_role for asset in content.assets if asset.asset_type == AssetType.AUDIO}
    missing_images = sorted(required_roles - set(image_roles))
    missing_audio = sorted(required_roles - set(audio_roles))
    if missing_images or missing_audio:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ASSET_PACKAGE_INCOMPLETE",
                "message": "콘텐츠 패키지는 5개 이미지와 5개 오디오 asset이 모두 필요합니다.",
                "details": {"missingImages": missing_images, "missingAudio": missing_audio},
            },
        )


def _preflight_provider_keys(content) -> None:
    settings = get_settings()
    has_images = any(asset.asset_type == AssetType.IMAGE for asset in content.assets)
    has_audio = any(asset.asset_type == AssetType.AUDIO for asset in content.assets)
    if has_images and not settings.openai_api_key:
        raise HTTPException(
            status_code=424,
            detail={
                "code": "OPENAI_API_KEY_MISSING",
                "message": "OPENAI_API_KEY가 없어 이미지 패키지 생성을 실행할 수 없습니다.",
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled"},
            },
        )
    if has_audio and not settings.elevenlabs_api_key:
        raise HTTPException(
            status_code=424,
            detail={
                "code": "ELEVENLABS_API_KEY_MISSING",
                "message": "ELEVENLABS_API_KEY가 없어 오디오 패키지 생성을 실행할 수 없습니다.",
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled"},
            },
        )
    if has_audio and not settings.elevenlabs_voice_id:
        raise HTTPException(
            status_code=424,
            detail={
                "code": "ELEVENLABS_VOICE_ID_MISSING",
                "message": "ELEVENLABS_VOICE_ID가 없어 오디오 패키지 생성을 실행할 수 없습니다.",
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled"},
            },
        )


def _extract_image_prompt(prompt_json: dict | None) -> str:
    if not prompt_json:
        raise HTTPException(status_code=400, detail={"code": "ASSET_PROMPT_MISSING", "message": "이미지 asset promptJson이 필요합니다."})
    prompt = prompt_json.get("prompt") or prompt_json.get("imagePrompt") or prompt_json.get("visualPrompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(status_code=400, detail={"code": "ASSET_PROMPT_MISSING", "message": "이미지 생성 prompt가 필요합니다."})
    return prompt


def _generated_file_path(relative_path: str):
    return Path(get_settings().generated_assets_dir) / relative_path
