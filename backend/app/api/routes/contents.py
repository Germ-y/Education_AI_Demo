import logging
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.ai.elevenlabs_provider import ElevenLabsProvider
from app.ai.openai_provider import OpenAiProvider
from app.ai.prompt_registry import load_prompt
from app.ai.provider_errors import AiProviderError
from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.domain.enums import AssetRole, AssetType
from app.domain.schemas import ContentApprovalRequest, ContentRejectRequest, ContentReviewUpdateRequest
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/contents", tags=["contents"])
logger = logging.getLogger(__name__)

UI_LIKE_IMAGE_PROMPT_TERMS = (
    "빈 카드",
    "카드형",
    "카드 UI",
    "카드 레이아웃",
    "말풍선",
    "선택지 영역",
    "정답 영역",
    "문제 영역",
    "UI 패널",
    "버튼",
)


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

    if asset.asset_type == AssetType.IMAGE:
        _refresh_image_prompts_or_raise(content)
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
    _refresh_image_prompts_or_raise(content)

    package_started_at = time.perf_counter()
    sorted_assets = sorted(content.assets, key=lambda item: (item.asset_type, item.asset_role, item.id))
    total_assets = len(sorted_assets)
    logger.info(
        "contents.assets.package_started content_id=%s student_id=%s asset_count=%s",
        content.id,
        content.student_id,
        total_assets,
    )
    generated = []
    for index, asset in enumerate(sorted_assets, start=1):
        logger.info(
            "contents.assets.generating content_id=%s progress=%s/%s asset_id=%s type=%s role=%s stage_id=%s",
            content.id,
            index,
            total_assets,
            asset.id,
            asset.asset_type,
            asset.asset_role,
            asset.stage_id,
        )
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
    logger.info(
        "contents.assets.package_succeeded content_id=%s generated_count=%s elapsed_sec=%.1f",
        content.id,
        len(generated),
        time.perf_counter() - package_started_at,
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
    asset_started_at = time.perf_counter()
    try:
        if asset.asset_type == AssetType.IMAGE:
            prompt = _extract_image_prompt(asset.prompt_json)
            relative_path = _generated_asset_relative_path(content_id, asset)
            output_path = _generated_file_path(relative_path)
            if not _is_generated_file_ready(output_path):
                logger.info(
                    "contents.asset.image_started content_id=%s asset_id=%s role=%s stage_id=%s path=%s",
                    content_id,
                    asset.id,
                    asset.asset_role,
                    asset.stage_id,
                    output_path,
                )
                OpenAiProvider(settings).create_image_file(
                    prompt=prompt,
                    output_path=output_path,
                    model=settings.openai_image_model,
                    timeout_sec=settings.openai_image_timeout_sec,
                )
            else:
                logger.info(
                    "contents.asset.image_skipped_existing content_id=%s asset_id=%s role=%s stage_id=%s path=%s",
                    content_id,
                    asset.id,
                    asset.asset_role,
                    asset.stage_id,
                    output_path,
                )
            _apply_generated_asset_metadata(asset, relative_path, provider="openai", model=settings.openai_image_model)
        elif asset.asset_type == AssetType.AUDIO:
            if not asset.source_text:
                raise HTTPException(status_code=400, detail={"code": "ASSET_SOURCE_TEXT_MISSING", "message": "TTS asset sourceText가 필요합니다."})
            relative_path = _generated_asset_relative_path(content_id, asset)
            output_path = _generated_file_path(relative_path)
            if not _is_generated_file_ready(output_path):
                logger.info(
                    "contents.asset.audio_started content_id=%s asset_id=%s role=%s stage_id=%s path=%s",
                    content_id,
                    asset.id,
                    asset.asset_role,
                    asset.stage_id,
                    output_path,
                )
                ElevenLabsProvider(settings).create_speech_file(source_text=asset.source_text, output_path=output_path)
            else:
                logger.info(
                    "contents.asset.audio_skipped_existing content_id=%s asset_id=%s role=%s stage_id=%s path=%s",
                    content_id,
                    asset.id,
                    asset.asset_role,
                    asset.stage_id,
                    output_path,
                )
            _apply_generated_asset_metadata(asset, relative_path, provider="elevenlabs", model="eleven_multilingual_v2")
        else:
            raise HTTPException(status_code=400, detail={"code": "ASSET_TYPE_NOT_SUPPORTED", "message": "지원하지 않는 assetType입니다."})
        logger.info(
            "contents.asset.succeeded content_id=%s asset_id=%s type=%s role=%s stage_id=%s elapsed_sec=%.1f",
            content_id,
            asset.id,
            asset.asset_type,
            asset.asset_role,
            asset.stage_id,
            time.perf_counter() - asset_started_at,
        )
    except AiProviderError as exc:
        logger.warning(
            "contents.asset.failed content_id=%s asset_id=%s type=%s role=%s stage_id=%s code=%s elapsed_sec=%.1f message=%s",
            content_id,
            asset.id,
            asset.asset_type,
            asset.asset_role,
            asset.stage_id,
            exc.code,
            time.perf_counter() - asset_started_at,
            exc.message,
        )
        raise HTTPException(
            status_code=424,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "assetId": asset.id},
            },
        ) from exc


def _refresh_image_prompts_or_raise(content) -> None:
    image_assets = [asset for asset in content.assets if asset.asset_type == AssetType.IMAGE]
    if not image_assets or all(_uses_image_brief_prompt(asset.prompt_json) for asset in image_assets):
        return

    settings = get_settings()
    started_at = time.perf_counter()
    logger.info("contents.image_brief.started content_id=%s image_asset_count=%s", content.id, len(image_assets))
    try:
        output_json, _ = OpenAiProvider(settings).create_json_response(
            model=settings.openai_reasoning_model,
            instructions=load_prompt("image_brief"),
            input_snapshot=_image_brief_input_snapshot(content, image_assets),
        )
        _apply_image_brief_output(content, output_json)
    except AiProviderError as exc:
        logger.warning(
            "contents.image_brief.failed content_id=%s code=%s elapsed_sec=%.1f message=%s",
            content.id,
            exc.code,
            time.perf_counter() - started_at,
            exc.message,
        )
        raise HTTPException(
            status_code=424,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "contentId": content.id},
            },
        ) from exc
    logger.info("contents.image_brief.succeeded content_id=%s elapsed_sec=%.1f", content.id, time.perf_counter() - started_at)


def _uses_image_brief_prompt(prompt_json: dict | None) -> bool:
    return isinstance(prompt_json, dict) and prompt_json.get("promptVersion") == "image_brief_v1"


def _image_brief_input_snapshot(content, image_assets: list) -> dict:
    return {
        "contentId": content.id,
        "contentType": content.content_type,
        "title": content.title,
        "sessionGoal": content.session_goal,
        "briefJson": content.brief_json,
        "stages": [
            {
                "id": stage.id,
                "step": stage.step,
                "stageRole": stage.stage_role,
                "templateType": stage.template_type,
                "studentTitle": stage.student_title,
                "studentInstruction": stage.student_instruction,
                "templateJson": stage.template_json,
                "realtimeSpec": stage.realtime_spec.model_dump(by_alias=True) if stage.realtime_spec else None,
            }
            for stage in sorted(content.stages, key=lambda item: item.step)
        ],
        "imageAssets": [
            {
                "id": asset.id,
                "assetRole": asset.asset_role,
                "stageId": asset.stage_id,
                "currentPromptJson": asset.prompt_json,
            }
            for asset in image_assets
        ],
    }


def _apply_image_brief_output(content, output_json: dict) -> None:
    briefs = output_json.get("imageBriefs")
    if not isinstance(briefs, list):
        raise HTTPException(
            status_code=424,
            detail={
                "code": "IMAGE_BRIEF_OUTPUT_INVALID",
                "message": "이미지 프롬프트 빌더 응답에 imageBriefs가 없습니다.",
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "contentId": content.id},
            },
        )

    briefs_by_role = {brief.get("assetRole"): brief for brief in briefs if isinstance(brief, dict)}
    for asset in content.assets:
        if asset.asset_type != AssetType.IMAGE:
            continue
        brief = briefs_by_role.get(asset.asset_role)
        prompt = brief.get("prompt") if isinstance(brief, dict) else None
        if not isinstance(prompt, str) or len(prompt.strip()) < 80:
            raise HTTPException(
                status_code=424,
                detail={
                    "code": "IMAGE_BRIEF_PROMPT_INVALID",
                    "message": f"{asset.asset_role} 이미지 프롬프트가 충분하지 않습니다.",
                    "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "assetId": asset.id},
                },
            )
        for term in UI_LIKE_IMAGE_PROMPT_TERMS:
            if term in prompt:
                raise HTTPException(
                    status_code=424,
                    detail={
                        "code": "IMAGE_BRIEF_UI_LIKE_PROMPT",
                        "message": f"{asset.asset_role} 이미지 프롬프트가 UI형 요소를 요청합니다: {term}",
                        "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "assetId": asset.id},
                    },
                )
        existing = asset.prompt_json if isinstance(asset.prompt_json, dict) else {}
        asset.prompt_json = {
            **existing,
            "promptVersion": "image_brief_v1",
            "prompt": prompt.strip(),
            "negativePromptRules": brief.get("negativePromptRules", []),
            "ocrRequired": bool(brief.get("ocrRequired", False)),
            "qaChecklist": brief.get("qaChecklist", []),
            "textRenderingPolicy": "scene_only_no_problem_text",
        }


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
