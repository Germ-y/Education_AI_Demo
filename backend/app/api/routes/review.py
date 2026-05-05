import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.domain.schemas import TeacherReportCreateRequest
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/review-summaries", tags=["review-summaries"])
teacher_reports_router = APIRouter(prefix="/api/teacher-reports", tags=["teacher-reports"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{review_id}/report-drafts/stream")
def stream_teacher_report_draft(
    review_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> StreamingResponse:
    draft = demo_store.create_teacher_report_draft(review_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if draft is None:
        raise HTTPException(status_code=404, detail={"code": "REVIEW_SUMMARY_NOT_FOUND", "message": "AI 리포트 초안을 만들 리뷰 요약을 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=draft.student_id,
        action="create_teacher_report_draft",
        resource_type="teacher_report_draft",
        resource_id=draft.id,
        payload_json={"reviewSummaryId": review_id, "model": draft.model},
    )

    def events():
        yield _sse("draft_delta", {"text": draft.body_markdown})
        yield _sse(
            "draft_metadata",
            {
                "nextLearningSuggestions": draft.next_learning_suggestions,
                "memoryCandidates": draft.memory_candidates,
            },
        )
        yield _sse("done", {"draftId": draft.id, "status": draft.status})

    return StreamingResponse(events(), media_type="text/event-stream")


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


@teacher_reports_router.post("")
def save_teacher_report(
    payload: TeacherReportCreateRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    report = demo_store.save_teacher_report(
        draft_id=payload.draft_id,
        review_summary_id=payload.review_summary_id,
        student_id=payload.student_id,
        content_id=payload.content_id,
        teacher_body=payload.teacher_body,
        selected_memory_candidates=payload.selected_memory_candidates,
        teacher_id=principal.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail={"code": "TEACHER_REPORT_NOT_FOUND", "message": "저장할 교사 리포트 대상을 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=payload.student_id,
        action="save_teacher_report",
        resource_type="teacher_report",
        resource_id=report.id,
        payload_json={"reviewSummaryId": payload.review_summary_id, "memoryCandidateCount": len(payload.selected_memory_candidates)},
    )
    return ok(report.model_dump(by_alias=True))
