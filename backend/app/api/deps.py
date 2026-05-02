from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.services.store import DemoStore, SessionPrincipal, store


def get_store() -> DemoStore:
    return store


def _extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme != "Bearer" or not token:
        return None
    return token


def require_principal(
    authorization: Annotated[str | None, Header()] = None,
    demo_store: DemoStore = Depends(get_store),
) -> SessionPrincipal:
    principal = demo_store.get_session(_extract_token(authorization))
    if principal is None:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "로그인이 필요합니다."})
    return principal


def require_teacher(principal: SessionPrincipal = Depends(require_principal)) -> SessionPrincipal:
    if principal.role not in {"teacher", "center_admin", "content_reviewer"}:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "교사 권한이 필요합니다."})
    return principal


def require_student(principal: SessionPrincipal = Depends(require_principal)) -> SessionPrincipal:
    if principal.role != "student" or principal.student_id is None:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "학생 권한이 필요합니다."})
    return principal
