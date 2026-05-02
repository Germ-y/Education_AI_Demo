from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.domain.schemas import MemoryCardPatch
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
def get_student(student_id: str, _: SessionPrincipal = Depends(require_teacher), demo_store: DemoStore = Depends(get_store)) -> dict:
    case_file = demo_store.get_student_case_file(student_id)
    if case_file is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_NOT_FOUND", "message": "학생 케이스를 찾을 수 없습니다."})
    return ok(case_file)


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
