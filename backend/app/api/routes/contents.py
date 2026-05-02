from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.domain.schemas import ContentApprovalRequest, ContentRejectRequest
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
    return ok(content.model_dump(by_alias=True))


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
    return ok(content.model_dump(by_alias=True))
