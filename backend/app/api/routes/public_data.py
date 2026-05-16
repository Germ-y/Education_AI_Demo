from datetime import date, datetime, timedelta

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


@router.get("/schools/search")
def search_schools(
    q: str | None = None,
    office_code: str | None = Query(default=None, alias="officeCode"),
    sync_if_missing: bool = Query(default=True, alias="syncIfMissing"),
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    cached = demo_store.list_schools(q=q)
    if cached and not sync_if_missing:
        return ok({"schools": cached, "source": {"provider": "cache", "cacheStatus": "cached"}})

    settings = get_settings()
    if not sync_if_missing:
        return ok({"schools": cached, "source": {"provider": "cache", "cacheStatus": "empty" if not cached else "cached"}})
    if not q:
        return ok({"schools": cached, "source": {"provider": "cache", "cacheStatus": "cached" if cached else "empty"}})
    if not settings.neis_api_key:
        if cached:
            return ok({"schools": cached, "source": {"provider": "cache", "cacheStatus": "cached", "neisStatus": "missing_key"}})
        raise HTTPException(
            status_code=424,
            detail={
                "code": "NEIS_API_KEY_MISSING",
                "message": "학교 검색을 위해 NEIS_API_KEY가 필요합니다.",
                "details": {"reviewRequired": True},
            },
        )

    try:
        schools = NeisClient(settings).search_schools(office_code=office_code, school_name=q)
    except AiProviderError as exc:
        raise HTTPException(
            status_code=424,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": {"reviewRequired": True},
            },
        ) from exc
    counts = demo_store.upsert_public_school_context(schools=schools, calendar=[], timetable=[])
    demo_store.record_audit(
        actor_user_id=principal.id,
        action="search_neis_school",
        resource_type="school_profile",
        payload_json={"q": q, "officeCode": office_code, "counts": counts},
    )
    return ok({"schools": demo_store.list_schools(q=q), "source": {"provider": "NEIS", "cacheStatus": "synced", "counts": counts}})


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
                "details": {"reviewRequired": True, "cacheStatus": "empty"},
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
                "details": {"reviewRequired": True},
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


@router.get("/schools/{school_code}/weekly-timetable")
def get_school_weekly_timetable(
    school_code: str,
    week_start: str | None = Query(default=None, alias="weekStart"),
    grade: str | None = None,
    class_name: str | None = Query(default=None, alias="className"),
    sync_if_missing: bool = Query(default=True, alias="syncIfMissing"),
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    school = demo_store.get_school(school_code)
    if school is None:
        raise HTTPException(status_code=404, detail={"code": "SCHOOL_NOT_FOUND", "message": "학교 정보를 찾을 수 없습니다."})
    if not grade or not class_name:
        raise HTTPException(
            status_code=400,
            detail={"code": "TIMETABLE_QUERY_INCOMPLETE", "message": "주간 시간표 조회에는 grade와 className이 필요합니다."},
        )

    start = _week_start_date(week_start)
    dates = [(start + timedelta(days=index)).isoformat() for index in range(5)]
    synced_counts = {"timetable": 0}
    attempted_sync = False

    if sync_if_missing:
        settings = get_settings()
        if not settings.neis_api_key:
            raise HTTPException(
                status_code=424,
                detail={
                    "code": "NEIS_API_KEY_MISSING",
                    "message": "저장된 주간 시간표가 없고 NEIS_API_KEY가 없어 시간표를 조회할 수 없습니다.",
                    "details": {"reviewRequired": True, "cacheStatus": "empty"},
                },
            )
        client = NeisClient(settings)
        for timetable_date in dates:
            existing = demo_store.list_school_timetable_slots(
                school_code,
                timetable_date=timetable_date,
                grade=grade,
                class_name=class_name,
            )
            if existing:
                continue
            attempted_sync = True
            try:
                timetable = client.fetch_timetable_day(
                    office_code=school.office_code,
                    school_code=school.school_code,
                    school_kind=school.school_kind,
                    timetable_date=timetable_date,
                    grade=grade,
                    class_name=class_name,
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
            counts = demo_store.upsert_public_school_context(schools=[school.model_dump(by_alias=True)], calendar=[], timetable=timetable)
            synced_counts["timetable"] += counts["timetable"]

    week_slots = [
        slot
        for slot in demo_store.list_school_timetable_slots(school_code, grade=grade, class_name=class_name)
        if slot["timetableDate"] in dates
    ]
    response = _weekly_timetable_response(
        school.model_dump(by_alias=True),
        dates,
        week_slots,
        grade=grade,
        class_name=class_name,
        cache_status="synced" if attempted_sync else "cached_snapshot",
        counts=synced_counts if attempted_sync else None,
    )
    demo_store.record_audit(
        actor_user_id=principal.id,
        action="sync_weekly_timetable_cache" if attempted_sync else "read_weekly_timetable_cache",
        resource_type="school_timetable",
        resource_id=school.school_code,
        payload_json={"weekStart": dates[0], "weekEnd": dates[-1], "grade": grade, "className": class_name, "counts": synced_counts},
    )
    return ok(response)


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
                "details": {"reviewRequired": True},
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


def _week_start_date(value: str | None) -> date:
    base = datetime.strptime(value, "%Y-%m-%d").date() if value else date.today()
    return base - timedelta(days=base.weekday())


def _weekly_timetable_response(
    school: dict,
    dates: list[str],
    slots: list[dict],
    *,
    grade: str,
    class_name: str,
    cache_status: str,
    counts: dict[str, int] | None,
) -> dict:
    weekday_labels = ["월", "화", "수", "목", "금"]
    days = []
    for index, timetable_date in enumerate(dates):
        day_slots = [slot for slot in slots if slot["timetableDate"] == timetable_date]
        subjects = [slot["subjectName"] for slot in day_slots if slot.get("subjectName")]
        days.append(
            {
                "date": timetable_date,
                "weekdayLabel": weekday_labels[index],
                "subjects": subjects,
                "slots": day_slots,
                "cacheStatus": "cached_snapshot" if day_slots else "empty",
            }
        )
    return {
        "school": school,
        "weekStart": dates[0],
        "weekEnd": dates[-1],
        "grade": grade,
        "className": class_name,
        "days": days,
        "source": {"provider": "NEIS", "cacheStatus": cache_status, "counts": counts},
        "orchestratorHints": _weekly_timetable_hints(days),
    }


def _weekly_timetable_hints(days: list[dict]) -> list[str]:
    subjects = [subject for day in days for subject in day["subjects"]]
    if not subjects:
        return ["주간 시간표 snapshot이 없어 콘텐츠 생성 맥락에는 사용하지 않습니다."]
    hints = ["주간 시간표는 학생 개인 능력 판단이 아니라 학교 수업 맥락으로만 사용합니다."]
    joined = " ".join(subjects)
    if any(keyword in joined for keyword in ["국어", "독서"]):
        hints.append("읽기 자료가 많은 날에는 지시문을 짧게 나누고 핵심 단서를 먼저 확인합니다.")
    if any(keyword in joined for keyword in ["수학", "수리"]):
        hints.append("수학 흐름이 있는 날에는 개념 확인형 콘텐츠를 학교 수업 맥락과 연결할 수 있습니다.")
    if any(keyword in joined for keyword in ["체육", "동아리", "창의적체험활동"]):
        hints.append("활동량이 있는 날에는 짧은 성공 경험으로 회기를 시작합니다.")
    return hints
