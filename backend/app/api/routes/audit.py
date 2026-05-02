from fastapi import APIRouter, Depends, Query

from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("")
def list_audit_logs(
    student_id: str | None = Query(default=None, alias="studentId"),
    action: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    _: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    return ok(demo_store.list_audit_logs(student_id=student_id, action=action, limit=limit))
