from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai.provider_errors import AiProviderError
from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.data.neis_client import NeisClient
from app.domain.schemas import PublicDataSyncRequest
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/public-data", tags=["public-data"])


@router.get("/sources")
def list_sources(_: SessionPrincipal = Depends(require_teacher), demo_store: DemoStore = Depends(get_store)) -> dict:
    return ok([source.model_dump(by_alias=True) for source in demo_store.db.public_data_sources])


@router.get("/schools")
def list_schools(_: SessionPrincipal = Depends(require_teacher), demo_store: DemoStore = Depends(get_store)) -> dict:
    return ok(demo_store.list_schools())


@router.get("/schools/{school_code}/context")
def get_school_context(
    school_code: str,
    from_date: str | None = Query(default=None, alias="fromDate"),
    to_date: str | None = Query(default=None, alias="toDate"),
    timetable_date: str | None = Query(default=None, alias="timetableDate"),
    grade: str | None = None,
    class_name: str | None = Query(default=None, alias="className"),
    _: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    school = demo_store.get_school(school_code)
    if school is None:
        raise HTTPException(status_code=404, detail={"code": "SCHOOL_NOT_FOUND", "message": "학교 정보를 찾을 수 없습니다."})
    return ok(
        {
            "school": school.model_dump(by_alias=True),
            "calendar": demo_store.list_school_calendar_events(school_code, from_date=from_date, to_date=to_date),
            "timetableSummary": demo_store.list_school_timetable_slots(
                school_code,
                timetable_date=timetable_date,
                grade=grade,
                class_name=class_name,
            ),
            "source": {
                "sourceCode": "neis_open_api",
                "mode": "seed_snapshot",
                "endpoints": ["schoolInfo", "SchoolSchedule", "elsTimetable", "misTimetable"],
            },
        }
    )


@router.get("/schools/{school_code}/timetable")
def get_school_timetable(
    school_code: str,
    timetable_date: str | None = Query(default=None, alias="date"),
    grade: str | None = None,
    class_name: str | None = Query(default=None, alias="className"),
    sync_if_missing: bool = Query(default=True, alias="syncIfMissing"),
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    school = demo_store.get_school(school_code)
    if school is None:
        raise HTTPException(status_code=404, detail={"code": "SCHOOL_NOT_FOUND", "message": "학교 정보를 찾을 수 없습니다."})

    context = demo_store.get_timetable_context(
        school_code,
        timetable_date=timetable_date,
        grade=grade,
        class_name=class_name,
    )
    if context is None:
        raise HTTPException(status_code=404, detail={"code": "SCHOOL_NOT_FOUND", "message": "학교 정보를 찾을 수 없습니다."})
    if context["slots"] or not sync_if_missing:
        return ok(context)

    settings = get_settings()
    if not settings.neis_api_key:
        raise HTTPException(
            status_code=424,
            detail={
                "code": "NEIS_API_KEY_MISSING",
                "message": "저장된 시간표가 없고 NEIS_API_KEY가 없어 시간표를 조회할 수 없습니다.",
                "details": {"reviewRequired": True, "fallbackPolicy": "disabled", "cacheStatus": "empty"},
            },
        )
    if not timetable_date or not grade or not class_name:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TIMETABLE_QUERY_INCOMPLETE",
                "message": "시간표 캐시가 없을 때 NEIS 조회를 실행하려면 date, grade, className이 필요합니다.",
            },
        )

    try:
        counts = demo_store.sync_neis_timetable_cache(
            office_code=school.office_code,
            school_code=school.school_code,
            timetable_date=timetable_date,
            grade=grade,
            class_name=class_name,
            client=NeisClient(settings),
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

    demo_store.record_audit(
        actor_user_id=principal.id,
        action="sync_timetable_cache",
        resource_type="school_timetable",
        resource_id=school.school_code,
        payload_json={"date": timetable_date, "grade": grade, "className": class_name, "counts": counts},
    )
    synced_context = demo_store.get_timetable_context(
        school_code,
        timetable_date=timetable_date,
        grade=grade,
        class_name=class_name,
    )
    return ok(synced_context)


@router.post("/sources/{source_code}/sync")
def sync_public_data_source(
    source_code: str,
    payload: PublicDataSyncRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    if source_code != "neis_open_api":
        raise HTTPException(status_code=404, detail={"code": "PUBLIC_DATA_SOURCE_NOT_SUPPORTED", "message": "지원하지 않는 공공데이터 source입니다."})
    try:
        result = NeisClient(get_settings()).sync_school_context(
            office_code=payload.office_code,
            school_code=payload.school_code,
            from_date=payload.from_date,
            to_date=payload.to_date,
            timetable_date=payload.timetable_date,
            grade=payload.grade,
            class_name=payload.class_name,
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

    counts = demo_store.upsert_public_school_context(**result)
    demo_store.record_audit(
        actor_user_id=principal.id,
        action="sync_public_data",
        resource_type="public_data_source",
        resource_id=source_code,
        payload_json={"request": payload.model_dump(by_alias=True), "counts": counts},
    )
    return ok({"jobId": f"sync_{source_code}", "status": "completed", "sourceCode": source_code, "counts": counts})
