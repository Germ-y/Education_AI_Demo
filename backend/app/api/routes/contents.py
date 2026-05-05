import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
IMAGE_PACKAGE_PARALLELISM = 5

PROBLEM_ANSWER_IMAGE_PROMPT_TERMS = (
    "문제 문장",
    "문제 텍스트",
    "문항",
    "선택지",
    "정답",
    "답안",
    "풀이",
    "힌트",
    "채점",
    "오답",
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
    _generate_asset_or_raise(content, asset)

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
    image_assets = [asset for asset in sorted_assets if asset.asset_type == AssetType.IMAGE]
    audio_assets = [asset for asset in sorted_assets if asset.asset_type == AssetType.AUDIO]
    total_assets = len(sorted_assets)
    logger.info(
        "contents.assets.package_started content_id=%s student_id=%s asset_count=%s",
        content.id,
        content.student_id,
        total_assets,
    )
    generated = []
    if image_assets:
        logger.info(
            "contents.assets.image_parallel_started content_id=%s image_count=%s max_workers=%s",
            content.id,
            len(image_assets),
            min(IMAGE_PACKAGE_PARALLELISM, len(image_assets)),
        )
        generated.extend(_generate_image_assets_in_parallel(content, image_assets, total_assets=total_assets))
        demo_store.save_generated_mission_content(content)

    for index, asset in enumerate(audio_assets, start=len(image_assets) + 1):
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
        _generate_asset_or_raise(content, asset)
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


@router.post("/{content_id}/stages/{stage_id}/preview-realtime-session")
def create_preview_realtime_session(
    content_id: str,
    stage_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    stage = next((candidate for candidate in content.stages if candidate.id == stage_id), None) if content else None
    if content is None or stage is None or stage.step != 4 or stage.realtime_spec is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "PREVIEW_REALTIME_NOT_ALLOWED", "message": "검토할 4단계 실시간 연습 구성이 필요합니다."},
        )

    settings = get_settings()
    try:
        secret = OpenAiProvider(settings).create_realtime_client_secret(
            instructions=_realtime_instructions(stage.realtime_spec.model_dump(by_alias=True)),
            model=settings.openai_realtime_model,
        )
    except AiProviderError as exc:
        raise HTTPException(
            status_code=424,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled"},
            },
        ) from exc

    session = demo_store.create_preview_realtime_session(content_id, principal.id if principal.role == "teacher" else None, stage_id)
    if session is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "PREVIEW_REALTIME_NOT_ALLOWED", "message": "검토할 4단계 실시간 연습 구성이 필요합니다."},
        )
    spec = session.spec_snapshot_json
    image_asset = next((asset for asset in content.assets if asset.id == spec.get("imageAssetId")), None)
    audio_asset = next((asset for asset in content.assets if asset.asset_role == "stage_4_realtime" and asset.asset_type == "audio"), None)
    return ok(
        {
            "sessionId": session.id,
            "provider": session.provider,
            "model": session.model,
            "clientSecret": secret["value"],
            "expiresAt": datetime.fromtimestamp(int(secret["expiresAt"]), UTC).isoformat(),
            "webrtcUrl": "https://api.openai.com/v1/realtime/calls",
            "practiceSpec": {
                "practiceTitle": spec.get("practiceTitle"),
                "imageAssetUrl": image_asset.preview_url if image_asset else None,
                "openingAudioUrl": audio_asset.preview_url if audio_asset else None,
                "openingLine": spec.get("openingLine"),
                "maxTurns": spec.get("maxTurns"),
                "maxDurationSec": spec.get("maxDurationSec"),
            },
        }
    )


def _generate_image_assets_in_parallel(content, image_assets: list, *, total_assets: int) -> list[dict]:
    generated_by_id: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=min(IMAGE_PACKAGE_PARALLELISM, len(image_assets))) as executor:
        futures = {}
        for index, asset in enumerate(image_assets, start=1):
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
            futures[executor.submit(_generate_asset_or_raise, content, asset)] = asset

        for future in as_completed(futures):
            asset = futures[future]
            future.result()
            generated_by_id[asset.id] = asset.model_dump(by_alias=True)

    return [generated_by_id[asset.id] for asset in image_assets]


def _realtime_instructions(spec: dict) -> str:
    rubric_labels = [
        str(item.get("label"))
        for item in spec.get("rubric", [])
        if isinstance(item, dict) and isinstance(item.get("label"), str)
    ]
    return "\n".join(
        [
            "You are the EduYJ teacher-review realtime practice partner.",
            "Speak in short, warm Korean sentences.",
            "This is a teacher preview of an unpublished or reviewable mission.",
            "Let the teacher verify voice tone, pacing, and instructional flow.",
            "Do not expose hidden rubrics or diagnostic labels.",
            "Accept partial, short, hesitant, or grammatically imperfect Korean as a useful attempt.",
            "If the speaker says anything related, affirm it first, then ask one gentle follow-up question.",
            "If the speaker is silent or says they do not know, offer one simple sentence starter.",
            f"Role: {spec.get('aiRole')}",
            f"Situation: {spec.get('situationText')}",
            f"Opening line: {spec.get('openingLine')}",
            f"Practice goal: {spec.get('studentGoal')}",
            f"Possible ideas to gently invite, not required answers: {rubric_labels}",
            f"Allowed feedback examples: {spec.get('allowedFeedback')}",
            f"Forbidden rules: {spec.get('forbidden')}",
        ]
    )


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


def _generate_asset_or_raise(content, asset) -> None:
    settings = get_settings()
    asset_started_at = time.perf_counter()
    try:
        if asset.asset_type == AssetType.IMAGE:
            prompt = _extract_image_prompt(asset.prompt_json)
            relative_path = _generated_asset_relative_path(content.student_id, content.id, asset)
            output_path = _generated_file_path(relative_path)
            if not _is_generated_file_ready(output_path):
                logger.info(
                    "contents.asset.image_started content_id=%s asset_id=%s role=%s stage_id=%s path=%s",
                    content.id,
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
                    content.id,
                    asset.id,
                    asset.asset_role,
                    asset.stage_id,
                    output_path,
                )
            _apply_generated_asset_metadata(asset, relative_path, provider="openai", model=settings.openai_image_model)
        elif asset.asset_type == AssetType.AUDIO:
            if not asset.source_text:
                raise HTTPException(status_code=400, detail={"code": "ASSET_SOURCE_TEXT_MISSING", "message": "TTS asset sourceText가 필요합니다."})
            relative_path = _generated_asset_relative_path(content.student_id, content.id, asset)
            output_path = _generated_file_path(relative_path)
            if not _is_generated_file_ready(output_path):
                logger.info(
                    "contents.asset.audio_started content_id=%s asset_id=%s role=%s stage_id=%s path=%s",
                    content.id,
                    asset.id,
                    asset.asset_role,
                    asset.stage_id,
                    output_path,
                )
                ElevenLabsProvider(settings).create_speech_file(source_text=asset.source_text, output_path=output_path)
            else:
                logger.info(
                    "contents.asset.audio_skipped_existing content_id=%s asset_id=%s role=%s stage_id=%s path=%s",
                    content.id,
                    asset.id,
                    asset.asset_role,
                    asset.stage_id,
                    output_path,
                )
            _apply_generated_asset_metadata(asset, relative_path, provider="elevenlabs", model=settings.elevenlabs_model_id)
        else:
            raise HTTPException(status_code=400, detail={"code": "ASSET_TYPE_NOT_SUPPORTED", "message": "지원하지 않는 assetType입니다."})
        logger.info(
            "contents.asset.succeeded content_id=%s asset_id=%s type=%s role=%s stage_id=%s elapsed_sec=%.1f",
            content.id,
            asset.id,
            asset.asset_type,
            asset.asset_role,
            asset.stage_id,
            time.perf_counter() - asset_started_at,
        )
    except AiProviderError as exc:
        logger.warning(
            "contents.asset.failed content_id=%s asset_id=%s type=%s role=%s stage_id=%s code=%s elapsed_sec=%.1f message=%s",
            content.id,
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
            model=settings.openai_image_brief_model,
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
    stages = sorted(content.stages, key=lambda item: item.step)
    return {
        "contentId": content.id,
        "contentType": content.content_type,
        "title": content.title,
        "sessionGoal": content.session_goal,
        "briefJson": content.brief_json,
        "scenarioVisualGuidance": {
            "goal": "Make the learning evidence visually dominant, not the person.",
            "cameraVariety": "Use distinct hero/stage shots in one coherent scenario.",
            "humanPresencePolicy": "People are optional and secondary unless the task is social expression or realtime role practice.",
        },
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
                "learningEvidence": _stage_learning_evidence(stage),
            }
            for stage in stages
        ],
        "imageAssets": [
            {
                "id": asset.id,
                "assetRole": asset.asset_role,
                "stageId": asset.stage_id,
                "currentPromptJson": asset.prompt_json,
                "stageEvidence": _asset_stage_evidence(asset, stages),
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
        for term in PROBLEM_ANSWER_IMAGE_PROMPT_TERMS:
            if _requests_problem_answer_image_text(prompt, term):
                raise HTTPException(
                    status_code=424,
                    detail={
                        "code": "IMAGE_BRIEF_PROBLEM_ANSWER_TEXT",
                        "message": f"{asset.asset_role} 이미지 프롬프트가 문제/정답/선택지 텍스트를 이미지에 넣도록 요청합니다: {term}",
                        "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "assetId": asset.id},
                    },
                )
        existing = asset.prompt_json if isinstance(asset.prompt_json, dict) else {}
        ocr_required = bool(brief.get("ocrRequired", False))
        text_rendering_policy = "short_scene_text_allowed_no_problem_ui" if ocr_required else "scene_only_no_problem_text"
        asset.prompt_json = {
            **existing,
            "promptVersion": "image_brief_v1",
            "prompt": prompt.strip(),
            "negativePromptRules": brief.get("negativePromptRules", []),
            "learningEvidence": brief.get("learningEvidence", {}),
            "compositionPlan": brief.get("compositionPlan", {}),
            "ocrRequired": ocr_required,
            "sceneTextLines": brief.get("sceneTextLines", []),
            "qaChecklist": brief.get("qaChecklist", []),
            "textRenderingPolicy": text_rendering_policy,
        }


def _requests_problem_answer_image_text(prompt: str, term: str) -> bool:
    index = prompt.find(term)
    while index != -1:
        window = prompt[max(0, index - 24) : index + len(term) + 56]
        if not _is_negated_image_prompt_term(window):
            return True
        index = prompt.find(term, index + len(term))
    return False


def _is_negated_image_prompt_term(text: str) -> bool:
    negation_markers = (
        "넣지 마세요",
        "넣지 않는다",
        "넣지 않",
        "포함하지 마세요",
        "포함하지 않",
        "보이지 않",
        "피하고",
        "피합니다",
        "제외",
        "금지",
        "없이",
        "없게",
        "no ",
        "not include",
        "avoid",
        "without",
    )
    lowered = text.lower()
    return any(marker in lowered for marker in negation_markers)


def _asset_stage_evidence(asset, stages: list) -> dict[str, Any] | None:
    if asset.asset_role == AssetRole.HERO:
        return {
            "purpose": "대표 장면",
            "contentTitle": "mission overview",
            "sharedAnchors": _brief_visual_anchors_from_stages(stages),
        }
    stage = next((candidate for candidate in stages if candidate.id == asset.stage_id), None)
    if stage is None:
        return None
    return _stage_learning_evidence(stage)


def _stage_learning_evidence(stage) -> dict[str, Any]:
    template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
    evidence: dict[str, Any] = {
        "step": stage.step,
        "studentTitle": stage.student_title,
        "stageRole": stage.stage_role,
        "templateType": stage.template_type,
        "studentInstruction": stage.student_instruction,
        "taskPrompt": _first_text_value(template_json, ("prompt", "question", "title", "situation")),
        "taskBody": _first_text_value(template_json, ("body", "description", "context", "sentence")),
        "sourceTextLines": _string_list(template_json.get("sourceTextLines")) + _string_list(template_json.get("sceneTextLines")),
        "choiceTexts": _extract_choice_texts(template_json),
        "matchingTexts": _extract_matching_texts(template_json),
        "sequenceTexts": _extract_sequence_texts(template_json),
        "visualAnchors": _extract_visual_anchors(template_json),
    }
    if stage.realtime_spec:
        spec = stage.realtime_spec.model_dump(by_alias=True)
        evidence["realtime"] = {
            "scenario": spec.get("scenario"),
            "openingLine": spec.get("openingLine"),
            "targetBehavior": spec.get("targetBehavior"),
            "rubric": spec.get("rubric"),
        }
    return evidence


def _brief_visual_anchors_from_stages(stages: list) -> list[str]:
    anchors: list[str] = []
    for stage in stages:
        for value in _stage_learning_evidence(stage).get("visualAnchors", []):
            if value not in anchors:
                anchors.append(value)
    return anchors[:8]


def _first_text_value(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _extract_choice_texts(template_json: dict[str, Any]) -> list[str]:
    choices = template_json.get("choices")
    if not isinstance(choices, list):
        return []
    texts: list[str] = []
    for choice in choices:
        if isinstance(choice, str) and choice.strip():
            texts.append(choice.strip())
        elif isinstance(choice, dict):
            for key in ("text", "label", "value"):
                value = choice.get(key)
                if isinstance(value, str) and value.strip():
                    texts.append(value.strip())
                    break
    return texts[:6]


def _extract_matching_texts(template_json: dict[str, Any]) -> list[str]:
    pairs = template_json.get("matchingPairs") or template_json.get("pairs")
    if not isinstance(pairs, list):
        pairs = _pairs_from_left_right_cards(template_json)
    if not isinstance(pairs, list):
        return []
    texts: list[str] = []
    for pair in pairs:
        if not isinstance(pair, dict):
            continue
        for key in ("left", "right", "leftText", "rightText"):
            value = pair.get(key)
            if isinstance(value, str) and value.strip():
                texts.append(value.strip())
    return texts[:8]


def _pairs_from_left_right_cards(template_json: dict[str, Any]) -> list[dict[str, Any]]:
    left_cards = template_json.get("leftCards")
    right_cards = template_json.get("rightCards")
    matches = template_json.get("matches")
    if not isinstance(left_cards, list) or not isinstance(right_cards, list) or not isinstance(matches, list):
        return []
    right_by_id = {card.get("id"): card for card in right_cards if isinstance(card, dict)}
    pairs: list[dict[str, Any]] = []
    for match in matches:
        if not isinstance(match, dict):
            continue
        left_id = match.get("leftId")
        right_id = match.get("rightId")
        left = next((card for card in left_cards if isinstance(card, dict) and card.get("id") == left_id), None)
        right = right_by_id.get(right_id)
        if isinstance(left, dict) and isinstance(right, dict):
            pairs.append({"left": left.get("text") or left.get("label"), "right": right.get("text") or right.get("label")})
    return pairs


def _extract_sequence_texts(template_json: dict[str, Any]) -> list[str]:
    items = template_json.get("sequenceItems") or template_json.get("cards") or template_json.get("items")
    if not isinstance(items, list):
        return []
    texts: list[str] = []
    for item in items:
        if isinstance(item, str) and item.strip():
            texts.append(item.strip())
        elif isinstance(item, dict):
            for key in ("label", "text", "caption", "title"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    texts.append(value.strip())
                    break
    return texts[:6]


def _extract_visual_anchors(template_json: dict[str, Any]) -> list[str]:
    anchors: list[str] = []
    for key in ("visualAnchors", "objects", "materials", "sourceTextLines", "sceneTextLines"):
        anchors.extend(_string_list(template_json.get(key)))
    for key in ("situation", "context", "body", "prompt", "question"):
        value = template_json.get(key)
        if isinstance(value, str) and value.strip():
            anchors.append(value.strip())
    return anchors[:8]


def _generated_asset_relative_path(student_id: str, content_id: str, asset) -> str:
    extension = "png" if asset.asset_type == AssetType.IMAGE else "mp3"
    return f"assets/students/{_safe_path_segment(student_id)}/{_safe_path_segment(content_id)}/{_safe_path_segment(asset.id)}.{extension}"


def _safe_path_segment(value: str) -> str:
    return "".join(character if character.isalnum() or character in {"_", "-"} else "_" for character in value)


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
