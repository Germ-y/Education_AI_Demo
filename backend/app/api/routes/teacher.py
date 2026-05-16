from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai.openai_provider import OpenAiProvider
from app.ai.output_schemas import output_json_schema
from app.ai.prompt_registry import PROMPT_SPECS, load_prompt
from app.ai.provider_errors import AiProviderError
from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.data.neis_client import NeisClient
from app.domain.models import SchoolProfile
from app.domain.schemas import (
    CaseNoteCreate,
    MemoryCardPatch,
    StudentRegistrationRequest,
    SupportProfileConfirmRequest,
    SupportProfileDraftRequest,
)
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


@router.get("/students/{student_id}/context-brief")
def get_student_context_brief(
    student_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    brief = demo_store.get_student_context_brief(student_id)
    if brief is None:
        brief = demo_store.refresh_student_context_brief(student_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if brief is None:
        raise HTTPException(status_code=404, detail={"code": "CONTEXT_BRIEF_NOT_FOUND", "message": "학생 ContextBrief를 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="view_context_brief",
        resource_type="student_context_brief",
        resource_id=brief.id,
        payload_json={"dirty": brief.dirty},
    )
    return ok(brief.model_dump(by_alias=True))


@router.post("/students/{student_id}/context-brief/refresh")
def refresh_student_context_brief(
    student_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    settings = get_settings()
    try:
        memory_override = _generate_memory_brief_with_ai(student_id, principal.id, demo_store)
    except AiProviderError as exc:
        demo_store.record_audit(
            actor_user_id=principal.id,
            student_id=student_id,
            action="refresh_context_brief_ai_failed",
            resource_type="student_context_brief",
            resource_id=student_id,
            payload_json={"code": exc.code, "message": exc.message},
        )
        raise HTTPException(
            status_code=424,
            detail={"code": exc.code, "message": exc.message, "details": {"reviewRequired": True}},
        ) from exc
    brief = demo_store.refresh_student_context_brief(
        student_id,
        teacher_id=principal.id if principal.role == "teacher" else None,
        brief_override=memory_override,
        model=settings.openai_memory_model,
    )
    if brief is None:
        raise HTTPException(status_code=404, detail={"code": "CONTEXT_BRIEF_NOT_FOUND", "message": "학생 ContextBrief를 갱신할 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="refresh_context_brief",
        resource_type="student_context_brief",
        resource_id=brief.id,
        payload_json={"dirty": brief.dirty, "generationMode": settings.openai_memory_model},
    )
    return ok({**brief.model_dump(by_alias=True), "generationMode": settings.openai_memory_model})


@router.post("/students/{student_id}/support-profile-drafts")
def create_support_profile_draft(
    student_id: str,
    payload: SupportProfileDraftRequest | None = None,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    if principal.role != "teacher":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "교사만 지원 프로필 초안을 만들 수 있습니다."})
    settings = get_settings()
    try:
        profile_override = _generate_support_profile_draft_with_ai(
            student_id,
            principal.id,
            demo_store,
            support_intake=payload.support_intake if payload else None,
            teacher_note=payload.teacher_note if payload else None,
        )
    except AiProviderError as exc:
        demo_store.record_audit(
            actor_user_id=principal.id,
            student_id=student_id,
            action="create_support_profile_draft_ai_failed",
            resource_type="student_support_profile",
            resource_id=student_id,
            payload_json={"code": exc.code, "message": exc.message},
        )
        raise HTTPException(
            status_code=424,
            detail={"code": exc.code, "message": exc.message, "details": {"reviewRequired": True}},
        ) from exc
    draft = demo_store.create_support_profile_draft(
        student_id,
        teacher_id=principal.id,
        support_intake=payload.support_intake if payload else None,
        teacher_note=payload.teacher_note if payload else None,
        profile_json_override=profile_override,
        generated_by=settings.openai_support_profile_model,
    )
    if draft is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_NOT_FOUND", "message": "지원 프로필 초안을 만들 학생을 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="create_support_profile_draft",
        resource_type="student_support_profile",
        resource_id=draft.id,
        payload_json={
            "generatedBy": draft.generated_by,
            "sourceIntakeId": draft.source_intake_id,
            "generationMode": settings.openai_support_profile_model,
        },
    )
    return ok(
        {
            "draftId": draft.id,
            "studentId": draft.student_id,
            "status": "completed",
            "generationMode": settings.openai_support_profile_model,
            "profileDraft": draft.profile_json,
            "supportProfile": draft.model_dump(by_alias=True),
        }
    )


@router.post("/students/{student_id}/support-profiles")
def confirm_support_profile(
    student_id: str,
    payload: SupportProfileConfirmRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    if principal.role != "teacher":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "교사만 지원 프로필을 확정할 수 있습니다."})
    profile = demo_store.confirm_support_profile(
        student_id,
        teacher_id=principal.id,
        draft_id=payload.draft_id,
        profile_draft=payload.profile_draft,
        teacher_note=payload.teacher_note,
    )
    if profile is None:
        raise HTTPException(status_code=404, detail={"code": "STUDENT_NOT_FOUND", "message": "확정할 지원 프로필 학생을 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=student_id,
        action="confirm_support_profile",
        resource_type="student_support_profile",
        resource_id=profile.id,
        payload_json={"draftId": payload.draft_id},
    )
    return ok(profile.model_dump(by_alias=True))


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


def _generate_support_profile_draft_with_ai(
    student_id: str,
    teacher_id: str,
    demo_store: DemoStore,
    *,
    support_intake: dict | None,
    teacher_note: str | None,
) -> dict:
    settings = get_settings()
    spec = PROMPT_SPECS["support_profile_draft"]
    output, _ = OpenAiProvider(settings).create_json_response(
        model=settings.openai_support_profile_model,
        instructions=load_prompt("support_profile_draft"),
        input_snapshot={
            **_student_ai_snapshot(student_id, teacher_id, demo_store),
            "registrationSupportIntake": support_intake or {},
            "teacherNote": teacher_note or "",
            "schemaContract": spec.output_schema_name,
        },
        output_schema_name=spec.output_schema_name,
        output_json_schema=output_json_schema(spec.output_schema_name),
        timeout_sec=settings.openai_support_profile_timeout_sec,
        max_output_tokens=2500,
    )
    return output


def _generate_memory_brief_with_ai(student_id: str, teacher_id: str, demo_store: DemoStore) -> dict:
    settings = get_settings()
    spec = PROMPT_SPECS["student_memory_brief"]
    output, _ = OpenAiProvider(settings).create_json_response(
        model=settings.openai_memory_model,
        instructions=load_prompt("student_memory_brief"),
        input_snapshot={
            **_student_ai_snapshot(student_id, teacher_id, demo_store),
            "schemaContract": spec.output_schema_name,
        },
        output_schema_name=spec.output_schema_name,
        output_json_schema=output_json_schema(spec.output_schema_name),
        timeout_sec=settings.openai_memory_timeout_sec,
        max_output_tokens=2500,
    )
    return output


def _student_ai_snapshot(student_id: str, teacher_id: str, demo_store: DemoStore) -> dict:
    case_file = demo_store.get_student_case_file(student_id) or {}
    history = demo_store.get_student_history(student_id, teacher_id=teacher_id) or {}
    dashboard_profile = case_file.get("dashboardProfile") if isinstance(case_file.get("dashboardProfile"), dict) else {}
    context_bundle = case_file.get("contextBundle") if isinstance(case_file.get("contextBundle"), dict) else {}
    return {
        "student": case_file.get("profile") or {},
        "studentType": (case_file.get("profile") or {}).get("studentType"),
        "openCase": case_file.get("openCase") or {},
        "dashboardProfile": dashboard_profile,
        "confirmedSupportProfile": case_file.get("supportProfile") or {},
        "memoryCard": case_file.get("memoryCard") or {},
        "contextBrief": case_file.get("contextBrief") or {},
        "contextBundle": {
            "studentRecord": context_bundle.get("studentRecord"),
            "previousLessons": context_bundle.get("previousLessons"),
            "teacherNotes": context_bundle.get("teacherNotes"),
            "nextGoal": context_bundle.get("nextGoal"),
        },
        "recentHistory": {
            "contents": history.get("contents") if isinstance(history, dict) else [],
            "reports": history.get("reports") if isinstance(history, dict) else [],
            "reviewSummaries": history.get("reviewSummaries") if isinstance(history, dict) else [],
        },
        "generationPolicy": {
            "profileAndMemoryAreScaffoldingOnly": True,
            "doNotUsePastScenarioAsNextTopic": True,
            "teacherContentRequestDecidesTopic": True,
        },
    }


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
                "details": {"reviewRequired": True},
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
                "details": {"reviewRequired": True},
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
