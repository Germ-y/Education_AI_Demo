from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai.provider_errors import AiProviderError
from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.data.neis_client import NeisClient
from app.domain.models import SchoolProfile
from app.domain.schemas import CaseNoteCreate, MemoryCardPatch, StudentRegistrationRequest
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


@router.post("/students")
def create_student(
    payload: StudentRegistrationRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    if principal.role != "teacher":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "교사만 학생을 등록할 수 있습니다."})
    school = _resolve_registration_school(payload, demo_store)
    created = demo_store.create_teacher_student(
        payload,
        teacher_id=principal.id,
        organization_id=demo_store.db.organizations[0].id,
        school=school,
    )
    student_file = created["student"]
    student_id = student_file["profile"]["id"] if student_file else None
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="register_student",
        resource_type="student",
        resource_id=student_id,
        payload_json={
            "created": created["created"],
            "schoolCode": school.school_code,
            "schoolName": school.school_name,
            "currentGoal": payload.current_goal,
        },
    )
    return ok({"student": student_file, "created": created["created"], "accessCode": created["accessCode"]})


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


@router.get("/students/{student_id}/context-bundle")
def get_student_context_bundle(
    student_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    bundle = demo_store.get_student_context_bundle(student_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_CONTEXT_NOT_FOUND", "message": "학생 컨텍스트를 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="view_student_context_bundle",
        resource_type="student",
        resource_id=student_id,
        payload_json={},
    )
    return ok(bundle)


@router.get("/students/{student_id}/report")
def get_student_report(
    student_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    report = demo_store.get_student_report(student_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if report is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_REPORT_NOT_FOUND", "message": "학생 리포트를 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="view_student_report",
        resource_type="student",
        resource_id=student_id,
        payload_json={},
    )
    return ok(report)


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


def _resolve_registration_school(payload: StudentRegistrationRequest, demo_store: DemoStore) -> SchoolProfile:
    if payload.school_code:
        cached = demo_store.get_school(payload.school_code)
        if cached is not None:
            return cached
    elif payload.school_name:
        cached_matches = demo_store.list_schools(q=payload.school_name)
        exact_cached = [item for item in cached_matches if item.get("schoolName") == payload.school_name]
        if len(exact_cached) == 1:
            return SchoolProfile.model_validate(exact_cached[0])

    settings = get_settings()
    if not settings.neis_api_key:
        raise HTTPException(
            status_code=424,
            detail={
                "code": "NEIS_API_KEY_MISSING",
                "message": "학생 등록 학교 확인을 위해 NEIS_API_KEY가 필요합니다.",
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled"},
            },
        )
    try:
        schools = NeisClient(settings).search_schools(
            office_code=payload.office_code,
            school_name=payload.school_name,
            school_code=payload.school_code,
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
    if not schools:
        raise HTTPException(status_code=404, detail={"code": "SCHOOL_NOT_FOUND", "message": "NEIS에서 학교 정보를 찾을 수 없습니다."})
    exact = [school for school in schools if payload.school_code and school.get("schoolCode") == payload.school_code]
    if not exact and payload.school_name:
        exact = [school for school in schools if school.get("schoolName") == payload.school_name]
    if not exact and len(schools) > 1:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SCHOOL_SELECTION_REQUIRED",
                "message": "검색된 학교가 여러 개입니다. 학교를 먼저 선택해 주세요.",
                "details": {"schools": schools[:10]},
            },
        )
    selected = exact[0] if exact else schools[0]
    demo_store.upsert_public_school_context(schools=[selected], calendar=[], timetable=[])
    return SchoolProfile.model_validate(selected)
