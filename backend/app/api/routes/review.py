from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/review-summaries", tags=["review-summaries"])


@router.post("/{review_id}/apply-to-memory")
def apply_review_summary_to_memory(
    review_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    memory_card = demo_store.apply_review_summary_to_memory(review_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if memory_card is None:
        raise HTTPException(status_code=404, detail={"code": "REVIEW_SUMMARY_NOT_FOUND", "message": "메모리에 반영할 리뷰 요약을 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=memory_card.student_id,
        action="apply_review_to_memory",
        resource_type="review_summary",
        resource_id=review_id,
        payload_json={"memoryCardId": memory_card.id},
    )
    return ok(memory_card.model_dump(by_alias=True))
