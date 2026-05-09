import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.ai.elevenlabs_provider import ElevenLabsProvider
from app.ai.openai_provider import OpenAiProvider
from app.ai.provider_errors import AiProviderError
from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.domain.enums import AssetRole, AssetType, MissionStatus
from app.domain.schemas import ContentApprovalRequest, ContentRejectRequest, ContentReviewUpdateRequest
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/contents", tags=["contents"])
logger = logging.getLogger(__name__)
IMAGE_PACKAGE_PARALLELISM = 5
ASSET_GENERATION_JOBS_KEY = "assetGenerationJobs"
ASSET_GENERATION_JOB_HISTORY_LIMIT = 8
_asset_package_locks: dict[str, Lock] = {}
_asset_package_locks_guard = Lock()

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
ANSWER_CUE_IMAGE_TEXTS = (
    "위험",
    "안전",
    "정답",
    "오답",
    "먼저",
    "이쪽",
    "맞음",
    "틀림",
    "체크",
    "화살표",
    "→",
    "←",
    "↑",
    "↓",
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
    _ensure_asset_generation_allowed(content)
    asset = next((candidate for candidate in content.assets if candidate.id == asset_id), None)
    if asset is None:
        raise HTTPException(status_code=404, detail={"code": "ASSET_NOT_FOUND", "message": "생성할 asset을 찾을 수 없습니다."})

    if asset.asset_type == AssetType.IMAGE:
        _refresh_image_prompts_or_raise(content)
    _generate_asset_or_raise(content, asset, force=True)

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


@router.post("/{content_id}/assets/generation-jobs")
def create_content_asset_generation_job(
    content_id: str,
    background_tasks: BackgroundTasks,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if content is None:
        raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})
    _ensure_asset_generation_allowed(content)
    _validate_required_asset_package(content)

    active_job = _get_active_asset_generation_job(content)
    if active_job is not None:
        return ok(active_job)

    job = _create_asset_generation_job(content, teacher_id=principal.id)
    demo_store.save_generated_mission_content(content)

    if job["status"] == "queued":
        background_tasks.add_task(_run_asset_generation_job, content.id, job["jobId"], principal.id, demo_store)

    return ok(job)


@router.get("/{content_id}/assets/generation-jobs/{job_id}")
def get_content_asset_generation_job(
    content_id: str,
    job_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if content is None:
        raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})
    job = _get_asset_generation_job(content, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "ASSET_GENERATION_JOB_NOT_FOUND", "message": "asset 생성 job을 찾을 수 없습니다."})
    return ok(job)


@router.post("/{content_id}/assets/generate-package")
def generate_content_asset_package(
    content_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if content is None:
        raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})
    _ensure_asset_generation_allowed(content)

    package_lock = _get_asset_package_lock(content.id)
    package_lock.acquire()
    try:
        content = demo_store.get_mission_for_teacher(content_id, teacher_id=principal.id if principal.role == "teacher" else None)
        if content is None:
            raise HTTPException(status_code=404, detail={"code": "CONTENT_NOT_FOUND", "message": "콘텐츠를 찾을 수 없습니다."})
        _ensure_asset_generation_allowed(content)
        _validate_required_asset_package(content)
        _preflight_provider_keys(content)
        if _is_required_asset_package_ready(content):
            assets = [asset.model_dump(by_alias=True) for asset in _get_package_assets(content)]
            logger.info(
                "contents.assets.package_skipped_existing content_id=%s generated_count=0 asset_count=%s",
                content.id,
                len(assets),
            )
            return ok({"contentId": content.id, "generatedCount": 0, "assets": assets})

        return _generate_content_asset_package_locked(content, principal=principal, demo_store=demo_store)
    finally:
        package_lock.release()


def _generate_content_asset_package_locked(
    content,
    *,
    principal: SessionPrincipal,
    demo_store: DemoStore,
) -> dict:
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


def _get_asset_package_lock(content_id: str) -> Lock:
    with _asset_package_locks_guard:
        if content_id not in _asset_package_locks:
            _asset_package_locks[content_id] = Lock()
        return _asset_package_locks[content_id]


def _get_package_assets(content) -> list:
    required_roles = {role.value for role in AssetRole}
    return [
        asset
        for asset in content.assets
        if asset.asset_role in required_roles and asset.asset_type in {AssetType.IMAGE, AssetType.AUDIO}
    ]


def _is_required_asset_package_ready(content) -> bool:
    assets = _get_package_assets(content)
    image_roles = {asset.asset_role for asset in assets if asset.asset_type == AssetType.IMAGE and _is_asset_ready(asset)}
    audio_roles = {asset.asset_role for asset in assets if asset.asset_type == AssetType.AUDIO and _is_asset_ready(asset)}
    required_roles = {role.value for role in AssetRole}
    return required_roles.issubset(image_roles) and required_roles.issubset(audio_roles)


def _is_asset_ready(asset) -> bool:
    return bool(asset.storage_url or asset.preview_url) and asset.qa_status == "passed"


def _ensure_asset_generation_allowed(content) -> None:
    if content.status in {MissionStatus.REVISION_REQUESTED, MissionStatus.ARCHIVED}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONTENT_ASSET_GENERATION_NOT_ALLOWED",
                "message": "사용 안 함 또는 보관 상태의 콘텐츠는 이미지와 음성을 생성할 수 없습니다.",
                "details": {"contentId": content.id, "status": content.status},
            },
        )


def _run_asset_generation_job(content_id: str, job_id: str, teacher_id: str, demo_store: DemoStore) -> None:
    package_lock = _get_asset_package_lock(content_id)
    package_lock.acquire()
    try:
        content = demo_store.get_mission_for_teacher(content_id, teacher_id=teacher_id)
        if content is None:
            return
        job = _get_asset_generation_job(content, job_id)
        if job is None or job["status"] not in {"queued", "running"}:
            return

        _set_asset_generation_job_status(content, job_id, "running", started_at=_now_iso())
        demo_store.save_generated_mission_content(content)

        try:
            _ensure_asset_generation_allowed(content)
            _validate_required_asset_package(content)
        except HTTPException as exc:
            _fail_asset_generation_job(content, job_id, *_error_from_http_exception(exc))
            demo_store.save_generated_mission_content(content)
            return

        target_assets = _get_job_target_assets(content, job_id)
        if not target_assets:
            _set_asset_generation_job_status(content, job_id, "succeeded", completed_at=_now_iso())
            demo_store.save_generated_mission_content(content)
            return

        image_assets = [asset for asset in target_assets if asset.asset_type == AssetType.IMAGE]
        audio_assets = [asset for asset in target_assets if asset.asset_type == AssetType.AUDIO]

        if image_assets:
            try:
                _refresh_image_prompts_or_raise(content)
            except HTTPException as exc:
                code, message = _error_from_http_exception(exc)
                for asset in image_assets:
                    _mark_asset_generation_failed(content, job_id, asset, code, message)
                demo_store.save_generated_mission_content(content)
            else:
                _run_image_asset_generation_job(content, job_id, image_assets, demo_store)

        for asset in audio_assets:
            _run_single_asset_generation_job(content, job_id, asset, demo_store)

        final_job = _finalize_asset_generation_job(content, job_id)
        demo_store.save_generated_mission_content(content)
        demo_store.record_audit(
            actor_user_id=teacher_id,
            student_id=content.student_id,
            action="generate_asset_package_job",
            resource_type="mission_content",
            resource_id=content.id,
            payload_json={
                "jobId": job_id,
                "status": final_job["status"],
                "generatedCount": final_job["generatedCount"],
                "failedCount": final_job["failedCount"],
            },
        )
    finally:
        package_lock.release()


def _run_image_asset_generation_job(content, job_id: str, image_assets: list, demo_store: DemoStore) -> None:
    with ThreadPoolExecutor(max_workers=min(IMAGE_PACKAGE_PARALLELISM, len(image_assets))) as executor:
        futures = {}
        for asset in image_assets:
            if _is_asset_ready(asset):
                _mark_asset_generation_skipped(content, job_id, asset)
                continue
            _mark_asset_generation_running(content, job_id, asset)
            futures[executor.submit(_generate_asset_or_raise, content, asset)] = asset

        demo_store.save_generated_mission_content(content)
        for future in as_completed(futures):
            asset = futures[future]
            try:
                future.result()
            except HTTPException as exc:
                _mark_asset_generation_failed(content, job_id, asset, *_error_from_http_exception(exc))
            except Exception as exc:  # noqa: BLE001 - provider wrappers can surface unexpected runtime errors.
                logger.exception("contents.asset.job_unhandled_failed content_id=%s job_id=%s asset_id=%s", content.id, job_id, asset.id)
                _mark_asset_generation_failed(content, job_id, asset, "ASSET_GENERATION_FAILED", str(exc) or "asset 생성에 실패했습니다.")
            else:
                _mark_asset_generation_succeeded(content, job_id, asset)
            demo_store.save_generated_mission_content(content)


def _run_single_asset_generation_job(content, job_id: str, asset, demo_store: DemoStore) -> None:
    if _is_asset_ready(asset):
        _mark_asset_generation_skipped(content, job_id, asset)
        demo_store.save_generated_mission_content(content)
        return

    _mark_asset_generation_running(content, job_id, asset)
    demo_store.save_generated_mission_content(content)
    try:
        _generate_asset_or_raise(content, asset)
    except HTTPException as exc:
        _mark_asset_generation_failed(content, job_id, asset, *_error_from_http_exception(exc))
    except Exception as exc:  # noqa: BLE001 - provider wrappers can surface unexpected runtime errors.
        logger.exception("contents.asset.job_unhandled_failed content_id=%s job_id=%s asset_id=%s", content.id, job_id, asset.id)
        _mark_asset_generation_failed(content, job_id, asset, "ASSET_GENERATION_FAILED", str(exc) or "asset 생성에 실패했습니다.")
    else:
        _mark_asset_generation_succeeded(content, job_id, asset)
    demo_store.save_generated_mission_content(content)


def _create_asset_generation_job(content, *, teacher_id: str) -> dict[str, Any]:
    now = _now_iso()
    assets = [_asset_generation_job_item(asset, "skipped" if _is_asset_ready(asset) else "queued") for asset in _sorted_package_assets(content)]
    queued_count = sum(1 for asset in assets if asset["status"] == "queued")
    job = {
        "jobId": f"asset_job_{uuid4().hex}",
        "contentId": content.id,
        "teacherId": teacher_id,
        "status": "queued" if queued_count else "succeeded",
        "queuedAt": now,
        "startedAt": None,
        "completedAt": now if queued_count == 0 else None,
        "totalCount": len(assets),
        "completedCount": len(assets) - queued_count,
        "failedCount": 0,
        "generatedCount": 0,
        "assets": assets,
        "errorCode": None,
        "errorMessage": None,
    }
    _append_asset_generation_job(content, job)
    return job


def _append_asset_generation_job(content, job: dict[str, Any]) -> None:
    jobs = _asset_generation_jobs(content)
    content.brief_json = {
        **content.brief_json,
        ASSET_GENERATION_JOBS_KEY: [*jobs, job][-ASSET_GENERATION_JOB_HISTORY_LIMIT:],
    }


def _asset_generation_jobs(content) -> list[dict[str, Any]]:
    jobs = content.brief_json.get(ASSET_GENERATION_JOBS_KEY)
    return [job for job in jobs if isinstance(job, dict)] if isinstance(jobs, list) else []


def _get_asset_generation_job(content, job_id: str) -> dict[str, Any] | None:
    return next((job for job in _asset_generation_jobs(content) if job.get("jobId") == job_id), None)


def _get_active_asset_generation_job(content) -> dict[str, Any] | None:
    return next((job for job in reversed(_asset_generation_jobs(content)) if job.get("status") in {"queued", "running"}), None)


def _replace_asset_generation_job(content, updated_job: dict[str, Any]) -> dict[str, Any]:
    jobs = _asset_generation_jobs(content)
    next_jobs = [updated_job if job.get("jobId") == updated_job.get("jobId") else job for job in jobs]
    content.brief_json = {**content.brief_json, ASSET_GENERATION_JOBS_KEY: next_jobs[-ASSET_GENERATION_JOB_HISTORY_LIMIT:]}
    return updated_job


def _set_asset_generation_job_status(
    content,
    job_id: str,
    status: str,
    *,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    job = _get_asset_generation_job(content, job_id)
    if job is None:
        raise RuntimeError(f"asset generation job not found: {job_id}")
    updated = {
        **job,
        "status": status,
        "startedAt": started_at if started_at is not None else job.get("startedAt"),
        "completedAt": completed_at if completed_at is not None else job.get("completedAt"),
        "errorCode": error_code,
        "errorMessage": error_message,
    }
    return _replace_asset_generation_job(content, _refresh_asset_generation_job_counts(updated))


def _fail_asset_generation_job(content, job_id: str, error_code: str, error_message: str) -> dict[str, Any]:
    job = _get_asset_generation_job(content, job_id)
    if job is None:
        raise RuntimeError(f"asset generation job not found: {job_id}")
    now = _now_iso()
    assets = [
        {**asset, "status": "failed", "errorCode": error_code, "errorMessage": error_message, "updatedAt": now}
        if asset.get("status") in {"queued", "running"}
        else asset
        for asset in job["assets"]
    ]
    updated = {
        **job,
        "status": "failed",
        "completedAt": now,
        "assets": assets,
        "errorCode": error_code,
        "errorMessage": error_message,
    }
    return _replace_asset_generation_job(content, _refresh_asset_generation_job_counts(updated))


def _finalize_asset_generation_job(content, job_id: str) -> dict[str, Any]:
    job = _get_asset_generation_job(content, job_id)
    if job is None:
        raise RuntimeError(f"asset generation job not found: {job_id}")
    refreshed_assets = []
    for item in job["assets"]:
        asset = _find_content_asset(content, str(item.get("assetId")))
        if asset is not None and item.get("status") in {"queued", "running"}:
            refreshed_assets.append(_asset_generation_job_item(asset, "skipped" if _is_asset_ready(asset) else "failed"))
        elif asset is not None:
            refreshed_assets.append({**item, **_asset_generation_metadata(asset)})
        else:
            refreshed_assets.append(item)

    failed_count = sum(1 for asset in refreshed_assets if asset.get("status") == "failed")
    generated_count = sum(1 for asset in refreshed_assets if asset.get("status") == "succeeded")
    if failed_count == 0:
        status = "succeeded"
        error_code = None
        error_message = None
    elif generated_count > 0 or any(asset.get("status") == "skipped" for asset in refreshed_assets):
        status = "partial_failed"
        error_code = "ASSET_GENERATION_PARTIAL_FAILED"
        error_message = "일부 이미지 또는 음성 asset 생성에 실패했습니다. 실패한 asset만 다시 생성할 수 있습니다."
    else:
        status = "failed"
        error_code = "ASSET_GENERATION_FAILED"
        error_message = "이미지와 음성 asset 생성에 실패했습니다."

    updated = {
        **job,
        "status": status,
        "completedAt": _now_iso(),
        "assets": refreshed_assets,
        "errorCode": error_code,
        "errorMessage": error_message,
    }
    return _replace_asset_generation_job(content, _refresh_asset_generation_job_counts(updated))


def _mark_asset_generation_running(content, job_id: str, asset) -> None:
    _update_asset_generation_item(content, job_id, asset, "running")


def _mark_asset_generation_skipped(content, job_id: str, asset) -> None:
    _update_asset_generation_item(content, job_id, asset, "skipped")


def _mark_asset_generation_succeeded(content, job_id: str, asset) -> None:
    _update_asset_generation_item(content, job_id, asset, "succeeded")


def _mark_asset_generation_failed(content, job_id: str, asset, error_code: str, error_message: str) -> None:
    asset.qa_status = "failed"
    _update_asset_generation_item(content, job_id, asset, "failed", error_code=error_code, error_message=error_message)


def _update_asset_generation_item(
    content,
    job_id: str,
    asset,
    status: str,
    *,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    job = _get_asset_generation_job(content, job_id)
    if job is None:
        raise RuntimeError(f"asset generation job not found: {job_id}")
    assets = []
    for item in job["assets"]:
        if item.get("assetId") != asset.id:
            assets.append(item)
            continue
        assets.append(
            {
                **item,
                **_asset_generation_metadata(asset),
                "status": status,
                "errorCode": error_code,
                "errorMessage": error_message,
                "updatedAt": _now_iso(),
            }
        )
    _replace_asset_generation_job(content, _refresh_asset_generation_job_counts({**job, "assets": assets}))


def _refresh_asset_generation_job_counts(job: dict[str, Any]) -> dict[str, Any]:
    assets = job.get("assets") if isinstance(job.get("assets"), list) else []
    completed_count = sum(1 for asset in assets if isinstance(asset, dict) and asset.get("status") in {"succeeded", "skipped"})
    failed_count = sum(1 for asset in assets if isinstance(asset, dict) and asset.get("status") == "failed")
    generated_count = sum(1 for asset in assets if isinstance(asset, dict) and asset.get("status") == "succeeded")
    return {
        **job,
        "totalCount": len(assets),
        "completedCount": completed_count,
        "failedCount": failed_count,
        "generatedCount": generated_count,
    }


def _get_job_target_assets(content, job_id: str) -> list:
    job = _get_asset_generation_job(content, job_id)
    if job is None:
        return []
    target_ids = {str(asset.get("assetId")) for asset in job.get("assets", []) if asset.get("status") in {"queued", "failed"}}
    return [asset for asset in _sorted_package_assets(content) if asset.id in target_ids and not _is_asset_ready(asset)]


def _asset_generation_job_item(asset, status: str) -> dict[str, Any]:
    return {
        "assetId": asset.id,
        "assetRole": _as_asset_role_value(asset.asset_role),
        "assetType": _as_asset_role_value(asset.asset_type),
        "stageId": asset.stage_id,
        "status": status,
        "errorCode": None,
        "errorMessage": None,
        "updatedAt": _now_iso(),
        **_asset_generation_metadata(asset),
    }


def _asset_generation_metadata(asset) -> dict[str, Any]:
    return {
        "storageUrl": asset.storage_url,
        "previewUrl": asset.preview_url,
        "qaStatus": asset.qa_status,
        "approvalStatus": asset.approval_status,
    }


def _sorted_package_assets(content) -> list:
    return sorted(_get_package_assets(content), key=lambda item: (item.asset_type, item.asset_role, item.id))


def _find_content_asset(content, asset_id: str):
    return next((asset for asset in content.assets if asset.id == asset_id), None)


def _error_from_http_exception(exc: HTTPException) -> tuple[str, str]:
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    return str(detail.get("code") or "ASSET_GENERATION_FAILED"), str(detail.get("message") or "asset 생성에 실패했습니다.")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


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


def _generate_asset_or_raise(content, asset, *, force: bool = False) -> None:
    settings = get_settings()
    asset_started_at = time.perf_counter()
    try:
        if asset.asset_type == AssetType.IMAGE:
            prompt = _extract_image_prompt(asset.prompt_json)
            relative_path = _generated_asset_relative_path(content.student_id, content.id, asset)
            output_path = _generated_file_path(relative_path)
            if force and output_path.exists():
                output_path.unlink()
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

    started_at = time.perf_counter()
    logger.info("contents.image_brief.build_started content_id=%s image_asset_count=%s", content.id, len(image_assets))
    output_json = _build_image_brief_output(content, image_assets)
    _apply_image_brief_output(content, output_json)
    logger.info("contents.image_brief.succeeded content_id=%s elapsed_sec=%.1f", content.id, time.perf_counter() - started_at)


def _uses_image_brief_prompt(prompt_json: dict | None) -> bool:
    return isinstance(prompt_json, dict) and prompt_json.get("promptVersion") == "image_brief_v1"


def _build_image_brief_output(content, image_assets: list) -> dict[str, Any]:
    stages = sorted(content.stages, key=lambda item: item.step)
    stage_visual_specs = _stage_visual_specs_by_role(content)
    return {
        "promptVersion": "image_brief_v1",
        "contentId": content.id,
        "imageBriefs": [
            _build_image_brief_for_asset(content, asset, stages, stage_visual_specs)
            for asset in image_assets
        ],
    }


def _build_image_brief_for_asset(content, asset, stages: list, stage_visual_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    spec = _stage_visual_spec_for_asset(content, asset, stages, stage_visual_specs)
    stage = next((candidate for candidate in stages if candidate.id == asset.stage_id), None)
    visual_source = _stage_visual_source(stage) if stage else {"visualAnchors": _brief_visual_anchors_from_stages(stages)}
    allowed_scene_text = _allowed_scene_text_for_asset(content, asset, stages, stage_visual_specs)
    blocked_texts = _do_not_render_text_for_asset(content, asset, stages, stage_visual_specs)
    candidate_anchors = _dedupe_strings(
        _string_list(spec.get("mustShow"))
        + _string_list(visual_source.get("visualAnchors"))
        + [_as_text(spec.get("primaryEvidenceObject"))]
    )
    must_show = _dedupe_strings(
        _sanitize_image_prompt_meta(value)
        for value in _filter_prompt_anchors(candidate_anchors, blocked_texts=blocked_texts, allowed_scene_text=allowed_scene_text)
    )[:7]
    spec_primary_object = _as_text(spec.get("primaryEvidenceObject"))
    primary_object = (
        spec_primary_object
        if spec_primary_object and not _is_blocked_prompt_anchor(spec_primary_object, blocked_texts=blocked_texts, allowed_scene_text=allowed_scene_text)
        else (must_show[0] if must_show else content.title)
    )
    primary_object = _sanitize_image_prompt_meta(primary_object) or content.title
    scene_summary = _sanitize_image_prompt_meta(_as_text(spec.get("sceneSummary"))) or content.title
    visual_purpose = _sanitize_image_prompt_meta(_as_text(spec.get("visualPurpose"))) or "학생이 확인할 장면 근거를 보여줍니다."
    composition = _sanitize_image_prompt_meta(_as_text(spec.get("composition"))) or "학습 근거가 화면 중심에 보이도록 가까운 구도로 구성합니다."
    camera = _camera_for_asset(asset.asset_role)
    human_presence = _human_presence_for_asset(content, asset, stage)
    ocr_required = bool(allowed_scene_text)
    text_policy = "short_scene_text_allowed_no_problem_ui" if ocr_required else "scene_only_no_problem_text"

    prompt_parts = [
        "Premium Korean edtech illustration, warm but not childish, clean realistic classroom or daily-life detail.",
        f"Asset role: {asset.asset_role}.",
        f"Scene summary: {scene_summary}.",
        f"Learning purpose: {visual_purpose}.",
        f"Primary learning evidence object: {primary_object}.",
    ]
    if must_show:
        prompt_parts.append(f"Must show these inspectable scene anchors: {', '.join(must_show)}.")
    prompt_parts.extend(
        [
            f"Composition: {composition}",
            f"Camera: {camera}; subject priority is learning_object_first; human presence: {human_presence}.",
            "Make the evidence object large, clear, and easy to inspect. People, if present, stay secondary and never become portrait-first.",
        ]
    )
    if allowed_scene_text:
        prompt_parts.append(
            "Readable real-world scene text is required only on the natural object in the scene. "
            f"Render exactly these short source lines: {' / '.join(allowed_scene_text)}."
        )
    else:
        prompt_parts.append(
            "Do not render any readable text inside the image. "
            "Do not add Korean labels, speech bubbles, signs, captions, badges, arrows, colored guide marks, "
            "check marks, X marks, or red/green answer cues."
        )
    prompt_parts.append(
        "Avoid app UI, worksheet layout, answer panels, scoring marks, feedback bubbles, "
        "category labels, long labels, watermarks, logos, decorative generic scenes, split-screen comparison diagrams, "
        "warning/safety signs, and any visual overlay that tells the answer. The image must look like a natural scene, not an instructional diagram."
    )

    return {
        "assetRole": asset.asset_role,
        "stageId": asset.stage_id,
        "prompt": " ".join(part for part in prompt_parts if part),
        "negativePromptRules": [
            "no app UI",
            "no answer panels",
            "no scoring marks",
            "no feedback text",
            "no category labels",
            "no watermark",
        ],
        "learningEvidence": {
            "primaryObject": primary_object,
            "mustBeReadableOrCountable": allowed_scene_text or must_show,
            "whyItMattersForThisStage": visual_purpose,
        },
        "compositionPlan": {
            "camera": camera,
            "subjectPriority": "learning_object_first",
            "humanPresence": human_presence,
            "negativeComposition": ["portrait-first framing", "generic decorative scene", "worksheet-like composition"],
        },
        "ocrRequired": ocr_required,
        "sceneTextLines": allowed_scene_text,
        "textRenderingPolicy": text_policy,
        "qaChecklist": [
            "scene matches stage purpose",
            "learning evidence is visually dominant",
            "no problem UI embedded",
            "student-safe tone",
        ],
    }


def _as_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _sanitize_image_prompt_meta(value: str) -> str:
    sanitized = value.strip()
    replacements = {
        "문제 문장": "학습 화면 문구",
        "문제 텍스트": "학습 화면 문구",
        "문항": "학습 활동",
        "선택지": "보기",
        "정답 후보": "목표 단서 후보",
        "정답 표기": "맞는 내용 표시",
        "정답": "맞는 내용",
        "답안": "학생 응답",
        "풀이": "생각 과정",
        "힌트": "도움 단서",
        "채점": "확인 표시",
        "오답": "다른 응답",
        "위험한": "사람이 많은",
        "위험": "사람이 많은 쪽",
        "안전한": "비어 있는",
        "안전": "빈 공간",
        "어느 방향이 더 비어 있는지 생각하게 한다": "주변 사람 수와 빈 공간을 살펴보게 한다",
        "어느 방향이 더": "주변 단서가 어떻게",
        "두 방향": "두 공간",
        "방향": "공간",
        "화살표": "방향 표시 없는 장면 단서",
        "빨간": "색으로 답을 암시하지 않는",
        "초록": "색으로 답을 암시하지 않는",
    }
    for term, replacement in replacements.items():
        sanitized = sanitized.replace(term, replacement)
    return sanitized.strip()


def _filter_prompt_anchors(values: list[str], *, blocked_texts: list[str], allowed_scene_text: list[str]) -> list[str]:
    return [
        value
        for value in _dedupe_strings(values)
        if not _is_blocked_prompt_anchor(value, blocked_texts=blocked_texts, allowed_scene_text=allowed_scene_text)
    ]


def _is_blocked_prompt_anchor(value: str, *, blocked_texts: list[str], allowed_scene_text: list[str]) -> bool:
    cleaned = value.strip()
    if not cleaned or cleaned in allowed_scene_text:
        return False
    for blocked in blocked_texts:
        blocked_cleaned = blocked.strip() if isinstance(blocked, str) else ""
        if not blocked_cleaned or blocked_cleaned in allowed_scene_text:
            continue
        if cleaned == blocked_cleaned or cleaned in blocked_cleaned or blocked_cleaned in cleaned:
            return True
    return False


def _camera_for_asset(asset_role: str) -> str:
    if asset_role == AssetRole.HERO:
        return "medium-close establishing shot"
    if asset_role in {AssetRole.STAGE_2, AssetRole.STAGE_3}:
        return "close-up or tabletop evidence shot"
    if asset_role == AssetRole.STAGE_4_REALTIME:
        return "medium-close role-practice shot"
    return "medium-close evidence introduction shot"


def _human_presence_for_asset(content, asset, stage) -> str:
    content_type = _as_asset_role_value(content.content_type)
    if asset.asset_role == AssetRole.STAGE_4_REALTIME:
        return "secondary interaction context"
    if content_type == "life_support":
        return "secondary or hands-only, included only if it clarifies the action"
    if stage and stage.step in {2, 3}:
        return "none or hands-only"
    return "small-background-context"


def _stage_visual_specs_by_role(content) -> dict[str, dict[str, Any]]:
    brief_json = content.brief_json if isinstance(content.brief_json, dict) else {}
    raw_specs = brief_json.get("stageVisualSpecs")
    specs: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_specs, list):
        return specs
    for item in raw_specs:
        if not isinstance(item, dict):
            continue
        role = item.get("assetRole")
        if isinstance(role, str) and role:
            specs[role] = item
    return specs


def _stage_visual_source(stage) -> dict[str, Any]:
    template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
    return {
        "sourceTextLines": _string_list(template_json.get("sourceTextLines")),
        "sceneTextLines": _string_list(template_json.get("sceneTextLines")),
        "visualAnchors": _extract_visual_anchors(template_json),
        "assetRole": _asset_role_for_step(stage.step).value,
    }


def _stage_visual_spec_for_stage(stage, stage_visual_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    role = _asset_role_for_step(stage.step).value
    return stage_visual_specs.get(role) or _fallback_stage_visual_spec(stage)


def _stage_visual_spec_for_asset(content, asset, stages: list, stage_visual_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    role = _as_asset_role_value(asset.asset_role)
    if role in stage_visual_specs:
        return stage_visual_specs[role]
    if asset.asset_role == AssetRole.HERO:
        return _fallback_hero_visual_spec(content, stages)
    stage = next((candidate for candidate in stages if candidate.id == asset.stage_id), None)
    return _fallback_stage_visual_spec(stage) if stage else {}


def _fallback_hero_visual_spec(content, stages: list) -> dict[str, Any]:
    anchors = _brief_visual_anchors_from_stages(stages)
    return {
        "assetRole": AssetRole.HERO.value,
        "step": 0,
        "visualPurpose": "미션 전체의 상황과 핵심 학습 근거를 한눈에 보여줍니다.",
        "sceneSummary": content.title,
        "primaryEvidenceObject": anchors[0] if anchors else content.title,
        "mustShow": anchors[:5],
        "allowedSceneText": _allowed_scene_text_from_stages(stages),
        "doNotRenderText": _do_not_render_text_from_stages(stages),
        "composition": "학습 근거가 화면 중심에 보이고 사람은 보조 맥락으로만 배치합니다.",
    }


def _fallback_stage_visual_spec(stage) -> dict[str, Any]:
    if stage is None:
        return {}
    template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
    allowed_scene_text = _allowed_scene_text_from_stage(stage)
    anchors = _extract_visual_anchors(template_json)
    role = _asset_role_for_step(stage.step).value
    return {
        "assetRole": role,
        "step": stage.step,
        "visualPurpose": f"{stage.student_title} 단계에서 학생이 볼 실제 장면 근거를 보여줍니다.",
        "sceneSummary": _first_text_value(template_json, ("storyText", "missionText", "context", "situation")) or stage.student_title,
        "primaryEvidenceObject": anchors[0] if anchors else (allowed_scene_text[0] if allowed_scene_text else stage.student_title),
        "mustShow": anchors[:5],
        "allowedSceneText": allowed_scene_text,
        "doNotRenderText": _stage_do_not_render_text(stage),
        "composition": "장면 근거를 크게 보여주고 문제 UI, 선택지, 정답 범주는 이미지 밖에 남깁니다.",
    }


def _allowed_scene_text_for_asset(content, asset, stages: list, stage_visual_specs: dict[str, dict[str, Any]]) -> list[str]:
    spec = _stage_visual_spec_for_asset(content, asset, stages, stage_visual_specs)
    spec_lines = _string_list(spec.get("allowedSceneText")) if isinstance(spec, dict) else []
    if asset.asset_role == AssetRole.HERO:
        return _filter_allowed_scene_text(spec_lines + _allowed_scene_text_from_stages(stages))
    stage = next((candidate for candidate in stages if candidate.id == asset.stage_id), None)
    return _filter_allowed_scene_text(spec_lines + (_allowed_scene_text_from_stage(stage) if stage else []))


def _do_not_render_text_for_asset(content, asset, stages: list, stage_visual_specs: dict[str, dict[str, Any]]) -> list[str]:
    spec = _stage_visual_spec_for_asset(content, asset, stages, stage_visual_specs)
    spec_lines = _string_list(spec.get("doNotRenderText")) if isinstance(spec, dict) else []
    spec_lines.extend(ANSWER_CUE_IMAGE_TEXTS)
    if asset.asset_role == AssetRole.HERO:
        return _dedupe_strings(spec_lines + _do_not_render_text_from_stages(stages))
    stage = next((candidate for candidate in stages if candidate.id == asset.stage_id), None)
    return _dedupe_strings(spec_lines + (_stage_do_not_render_text(stage) if stage else []))


def _filter_allowed_scene_text(lines: list[str]) -> list[str]:
    return _dedupe_strings(line for line in lines if not _is_answer_cue_image_text(line))


def _is_answer_cue_image_text(value: str) -> bool:
    cleaned = value.strip()
    if not cleaned:
        return False
    return any(term in cleaned for term in ANSWER_CUE_IMAGE_TEXTS)


def _allowed_scene_text_from_stages(stages: list) -> list[str]:
    lines: list[str] = []
    for stage in stages:
        lines.extend(_allowed_scene_text_from_stage(stage))
    return _dedupe_strings(lines)


def _allowed_scene_text_from_stage(stage) -> list[str]:
    if stage is None:
        return []
    template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
    return _dedupe_strings(_string_list(template_json.get("sourceTextLines")) + _string_list(template_json.get("sceneTextLines")))


def _do_not_render_text_from_stages(stages: list) -> list[str]:
    lines: list[str] = []
    for stage in stages:
        lines.extend(_stage_do_not_render_text(stage))
    return _dedupe_strings(lines)


def _stage_do_not_render_text(stage) -> list[str]:
    if stage is None:
        return []
    template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
    blocked = [stage.student_instruction]
    evidence = _stage_learning_evidence(stage)
    for key in ("taskPrompt", "taskBody"):
        value = evidence.get(key)
        if isinstance(value, str):
            blocked.append(value)
    for key in ("choiceTexts", "matchingTexts", "sequenceTexts"):
        value = evidence.get(key)
        if isinstance(value, list):
            blocked.extend(item for item in value if isinstance(item, str))
    blocked.extend(_template_feedback_texts(template_json))
    allowed = set(_allowed_scene_text_from_stage(stage))
    return _dedupe_strings(text for text in blocked if text and text not in allowed)


def _template_feedback_texts(template_json: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ("correctFeedback", "wrongFeedback", "hint", "explanation", "answer"):
        value = template_json.get(key)
        if isinstance(value, str):
            texts.append(value)
    return texts


def _dedupe_strings(values) -> list[str]:
    result: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped and stripped not in result:
            result.append(stripped)
    return result


def _as_asset_role_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _asset_role_for_step(step: int) -> AssetRole:
    return {
        1: AssetRole.STAGE_1,
        2: AssetRole.STAGE_2,
        3: AssetRole.STAGE_3,
        4: AssetRole.STAGE_4_REALTIME,
    }[step]


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
        blocked_text = _blocked_visible_text_in_image_prompt(content, asset, prompt)
        if blocked_text:
            raise HTTPException(
                status_code=424,
                detail={
                    "code": "IMAGE_BRIEF_UI_TEXT",
                    "message": f"{asset.asset_role} 이미지 프롬프트에 sourceTextLines가 아닌 UI/보기 문구가 들어갔습니다: {blocked_text}",
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
        window = prompt[max(0, index - 80) : index + len(term) + 120]
        if not _is_negated_image_prompt_term(window):
            return True
        index = prompt.find(term, index + len(term))
    return False


def _blocked_visible_text_in_image_prompt(content, asset, prompt: str) -> str | None:
    allowed_scene_texts = set()
    blocked_texts = []
    stages = list(content.stages)
    stage_visual_specs = _stage_visual_specs_by_role(content)
    for stage in stages:
        template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
        allowed_scene_texts.update(_string_list(template_json.get("sourceTextLines")))
        allowed_scene_texts.update(_string_list(template_json.get("sceneTextLines")))
    allowed_scene_texts.update(_allowed_scene_text_for_asset(content, asset, stages, stage_visual_specs))

    if asset.asset_role == AssetRole.HERO:
        target_stages = stages
    else:
        target_stages = [stage for stage in stages if stage.id == asset.stage_id]

    for stage in target_stages:
        evidence = _stage_learning_evidence(stage)
        for key in ("taskPrompt", "taskBody"):
            value = evidence.get(key)
            if isinstance(value, str):
                blocked_texts.append(value)
        for key in ("choiceTexts", "matchingTexts", "sequenceTexts"):
            value = evidence.get(key)
            if isinstance(value, list):
                blocked_texts.extend(item for item in value if isinstance(item, str))
    blocked_texts.extend(_do_not_render_text_for_asset(content, asset, stages, stage_visual_specs))

    for text in blocked_texts:
        cleaned = text.strip()
        if not _is_meaningful_image_ui_text(cleaned):
            continue
        if cleaned in allowed_scene_texts:
            continue
        if _contains_non_negated_prompt_text(prompt, cleaned):
            return cleaned
    return None


def _contains_non_negated_prompt_text(prompt: str, text: str) -> bool:
    index = prompt.find(text)
    while index != -1:
        window = prompt[max(0, index - 80) : index + len(text) + 120]
        if not _is_negated_image_prompt_term(window):
            return True
        index = prompt.find(text, index + len(text))
    return False


def _is_meaningful_image_ui_text(text: str) -> bool:
    return len(text) >= 5 and any("\uac00" <= character <= "\ud7a3" for character in text)


def _is_negated_image_prompt_term(text: str) -> bool:
    negation_markers = (
        "넣지 마세요",
        "넣지 않는다",
        "넣지 않",
        "넣지 않습니다",
        "포함하지 마세요",
        "포함하지 않",
        "포함하지 않는",
        "포함하지 않습니다",
        "표시하지 않",
        "표시하지 않습니다",
        "보이지 않",
        "보이지 않는",
        "보이지 않습니다",
        "노출하지",
        "노출되지",
        "노출하지 않습니다",
        "노출되지 않습니다",
        "드러나지",
        "렌더링하지",
        "렌더링하지 않습니다",
        "쓰지",
        "쓰지 않습니다",
        "사용하지",
        "사용하지 않습니다",
        "요청하지",
        "요청하지 않습니다",
        "피하고",
        "피합니다",
        "제외",
        "제외합니다",
        "금지",
        "없이",
        "없는",
        "없습니다",
        "없게",
        "아닌",
        "no ",
        "do not",
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
    if not isinstance(left_cards, list) or not isinstance(right_cards, list):
        return []
    right_by_id = {card.get("id"): card for card in right_cards if isinstance(card, dict)}
    pairs: list[dict[str, Any]] = []
    if isinstance(matches, dict):
        match_items = [{"leftId": left_id, "rightId": right_id} for left_id, right_id in matches.items()]
    elif isinstance(matches, list):
        match_items = matches
    else:
        match_items = []
    for match in match_items:
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
