from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.domain.schemas import CaseNoteCreate, MemoryCardPatch
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.get("/students")
def list_students(
    student_type: str | None = Query(default=None, alias="studentType"),
    q: str | None = None,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    teacher_id = principal.id if principal.role == "teacher" else None
    return ok(demo_store.list_teacher_students(student_type=student_type, q=q, teacher_id=teacher_id))


@router.get("/students/{student_id}")
def get_student(student_id: str, principal: SessionPrincipal = Depends(require_teacher), demo_store: DemoStore = Depends(get_store)) -> dict:
    case_file = demo_store.get_student_case_file(student_id)
    if case_file is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_NOT_FOUND", "message": "학생 케이스를 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="view_student_case",
        resource_type="student",
        resource_id=student_id,
        payload_json={},
    )
    return ok(case_file)


@router.get("/students/{student_id}/history")
def get_student_history(
    student_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    history = demo_store.get_student_history(student_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if history is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_HISTORY_NOT_FOUND", "message": "학생 히스토리를 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="view_student_history",
        resource_type="student",
        resource_id=student_id,
        payload_json={},
    )
    return ok(history)


@router.post("/students/{student_id}/notes")
def add_student_note(
    student_id: str,
    payload: CaseNoteCreate,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    note = demo_store.add_student_note(student_id, principal.id, payload.model_dump(by_alias=True))
    if note is None:
        raise HTTPException(status_code=404, detail={"code": "OPEN_CASE_NOT_FOUND", "message": "열린 학생 사례를 찾을 수 없습니다."})
    return ok(note.model_dump(by_alias=True))


@router.patch("/students/{student_id}/memory-card")
def patch_memory_card(
    student_id: str,
    payload: MemoryCardPatch,
    _: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    updated = demo_store.patch_memory_card(student_id, payload.model_dump(exclude_none=True))
    if updated is None:
        raise HTTPException(status_code=404, detail={"code": "MEMORY_CARD_NOT_FOUND", "message": "활성 메모리 카드를 찾을 수 없습니다."})
    return ok(updated.model_dump(by_alias=True))
