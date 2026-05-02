from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_store, require_teacher
from app.api.response import ok
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
