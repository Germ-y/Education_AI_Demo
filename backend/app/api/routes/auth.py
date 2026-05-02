from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_store
from app.api.response import ok
from app.domain.schemas import DemoLoginRequest, StudentAccessRequest
from app.services.store import DemoStore

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/demo-login")
def demo_login(payload: DemoLoginRequest, demo_store: DemoStore = Depends(get_store)) -> dict:
    session = demo_store.create_user_session(payload.role.value, payload.email)
    if session is None:
        raise HTTPException(status_code=404, detail={"code": "DEMO_USER_NOT_FOUND", "message": "데모 사용자를 찾을 수 없습니다."})
    user = next(user for user in demo_store.db.users if user.id == session.id)
    return ok(
        {
            "user": user.model_dump(by_alias=True),
            "session": {"accessToken": session.token, "expiresAt": session.expires_at},
        }
    )


@router.post("/student-access")
def student_access(payload: StudentAccessRequest, demo_store: DemoStore = Depends(get_store)) -> dict:
    session = demo_store.create_student_session(payload.access_code)
    if session is None or session.student_id is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_ACCESS_NOT_FOUND", "message": "학생 접근 코드를 확인해 주세요."})
    student = next(student for student in demo_store.db.students if student.id == session.student_id)
    return ok(
        {
            "student": student.model_dump(by_alias=True),
            "session": {"accessToken": session.token, "expiresAt": session.expires_at},
        }
    )
