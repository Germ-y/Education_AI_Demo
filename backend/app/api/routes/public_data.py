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
