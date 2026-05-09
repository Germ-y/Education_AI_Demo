from datetime import UTC, datetime
from typing import Any

import httpx

from app.ai.provider_errors import ProviderConfigurationError, ProviderOutputError, ProviderRequestError
from app.core.config import Settings


class NeisClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def search_schools(self, *, office_code: str | None = None, school_name: str | None = None, school_code: str | None = None) -> list[dict[str, Any]]:
        if not self.settings.neis_api_key:
            raise ProviderConfigurationError("NEIS_API_KEY_MISSING", "NEIS_API_KEY가 없어 NEIS 학교 조회를 실행할 수 없습니다.")

        rows = self._fetch_rows(
            "schoolInfo",
            {
                "ATPT_OFCDC_SC_CODE": office_code,
                "SCHUL_NM": school_name,
                "SD_SCHUL_CODE": school_code,
            },
        )
        if school_code:
            rows = [row for row in rows if row.get("SD_SCHUL_CODE") == school_code]
        if school_name:
            exact = [row for row in rows if row.get("SCHUL_NM") == school_name]
            rows = exact or [row for row in rows if school_name in str(row.get("SCHUL_NM") or "")]
        return [_normalize_school(row) for row in rows]

    def sync_school_context(
        self,
        *,
        office_code: str,
        school_code: str | None,
        from_date: str | None,
        to_date: str | None,
        timetable_date: str | None,
        grade: str | None,
        class_name: str | None,
    ) -> dict[str, list[dict[str, Any]]]:
        if not self.settings.neis_api_key:
            raise ProviderConfigurationError("NEIS_API_KEY_MISSING", "NEIS_API_KEY가 없어 NEIS 동기화를 실행할 수 없습니다.")

        school_rows = self._fetch_rows("schoolInfo", {"ATPT_OFCDC_SC_CODE": office_code})
        if school_code:
            school_rows = [row for row in school_rows if row.get("SD_SCHUL_CODE") == school_code]
        schools = [_normalize_school(row) for row in school_rows]

        calendar = []
        timetable = []
        if school_code and schools:
            calendar = [
                _normalize_schedule(row, office_code=office_code, school_code=school_code)
                for row in self._fetch_rows(
                    "SchoolSchedule",
                    {
                        "ATPT_OFCDC_SC_CODE": office_code,
                        "SD_SCHUL_CODE": school_code,
                        "AA_FROM_YMD": _compact_date(from_date),
                        "AA_TO_YMD": _compact_date(to_date),
                    },
                )
            ]
            endpoint = _timetable_endpoint(schools[0]["schoolKind"])
            if endpoint and timetable_date and grade and class_name:
                timetable = [
                    _normalize_timetable(row, office_code=office_code, school_code=school_code, endpoint=endpoint)
                    for row in self._fetch_rows(
                        endpoint,
                        {
                            "ATPT_OFCDC_SC_CODE": office_code,
                            "SD_SCHUL_CODE": school_code,
                            "AY": (timetable_date or "")[:4],
                            "SEM": "1",
                            "ALL_TI_YMD": _compact_date(timetable_date),
                            "GRADE": grade,
                            "CLASS_NM": class_name,
                        },
                    )
                ]
        return {"schools": schools, "calendar": calendar, "timetable": timetable}

    def fetch_timetable_day(
        self,
        *,
        office_code: str,
        school_code: str,
        school_kind: str,
        timetable_date: str,
        grade: str,
        class_name: str,
    ) -> list[dict[str, Any]]:
        if not self.settings.neis_api_key:
            raise ProviderConfigurationError("NEIS_API_KEY_MISSING", "NEIS_API_KEY가 없어 NEIS 시간표 조회를 실행할 수 없습니다.")
        endpoint = _timetable_endpoint(school_kind)
        if not endpoint:
            return []
        return [
            _normalize_timetable(row, office_code=office_code, school_code=school_code, endpoint=endpoint)
            for row in self._fetch_rows(
                endpoint,
                {
                    "ATPT_OFCDC_SC_CODE": office_code,
                    "SD_SCHUL_CODE": school_code,
                    "AY": (timetable_date or "")[:4],
                    "SEM": "1",
                    "ALL_TI_YMD": _compact_date(timetable_date),
                    "GRADE": grade,
                    "CLASS_NM": class_name,
                },
            )
        ]

    def _fetch_rows(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        clean_params = {
            "KEY": self.settings.neis_api_key,
            "Type": "json",
            "pIndex": 1,
            "pSize": 1000,
            **{key: value for key, value in params.items() if value},
        }
        try:
            with httpx.Client(timeout=20) as client:
                response = client.get(f"https://open.neis.go.kr/hub/{endpoint}", params=clean_params)
        except httpx.HTTPError as exc:
            raise ProviderRequestError("NEIS_REQUEST_FAILED", f"NEIS 요청 실패: {exc}") from exc
        if response.status_code >= 400:
            raise ProviderRequestError("NEIS_HTTP_ERROR", f"NEIS HTTP {response.status_code}: {response.text[:500]}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderOutputError("NEIS_RESPONSE_JSON_PARSE_FAILED", "NEIS 응답을 JSON으로 파싱할 수 없습니다.") from exc
        rows = payload.get(endpoint, [{}, {"row": []}])
        if not isinstance(rows, list) or len(rows) < 2:
            return []
        result = rows[1].get("row", [])
        return result if isinstance(result, list) else []


def _normalize_school(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"school_{row.get('SD_SCHUL_CODE')}",
        "officeCode": row.get("ATPT_OFCDC_SC_CODE") or "",
        "schoolCode": row.get("SD_SCHUL_CODE") or "",
        "schoolName": row.get("SCHUL_NM") or "",
        "schoolKind": row.get("SCHUL_KND_SC_NM") or "",
        "regionName": row.get("LCTN_SC_NM") or "경상북도",
        "roadAddress": row.get("ORG_RDNMA") or "",
        "sourceCode": "neis_open_api",
    }


def _normalize_schedule(row: dict[str, Any], *, office_code: str, school_code: str) -> dict[str, Any]:
    event_date = _display_date(row.get("AA_YMD") or "")
    return {
        "id": f"schedule_{school_code}_{row.get('AA_YMD')}_{row.get('EVENT_NM')}",
        "schoolCode": school_code,
        "officeCode": office_code,
        "academicYear": (row.get("AA_YMD") or "")[:4],
        "eventDate": event_date,
        "eventName": row.get("EVENT_NM") or "",
        "eventContent": row.get("EVENT_CNTNT"),
        "scheduleType": row.get("SBTR_DD_SC_NM"),
        "appliesToGrades": _grades_from_schedule(row),
        "sourceCode": "neis_school_schedule",
        "retrievedAt": _now(),
    }


def _normalize_timetable(row: dict[str, Any], *, office_code: str, school_code: str, endpoint: str) -> dict[str, Any]:
    timetable_date = _display_date(row.get("ALL_TI_YMD") or "")
    return {
        "id": f"timetable_{school_code}_{row.get('ALL_TI_YMD')}_{row.get('GRADE')}_{row.get('CLASS_NM')}_{row.get('PERIO')}",
        "schoolCode": school_code,
        "officeCode": office_code,
        "academicYear": (row.get("ALL_TI_YMD") or "")[:4],
        "semester": row.get("SEM") or "1",
        "timetableDate": timetable_date,
        "grade": row.get("GRADE") or "",
        "className": row.get("CLASS_NM") or "",
        "period": int(row.get("PERIO") or 0),
        "subjectName": row.get("ITRT_CNTNT"),
        "sourceCode": f"neis_{endpoint}",
        "retrievedAt": _now(),
    }


def _grades_from_schedule(row: dict[str, Any]) -> list[str]:
    mapping = [("ONE_GRADE_EVENT_YN", "1"), ("TW_GRADE_EVENT_YN", "2"), ("THREE_GRADE_EVENT_YN", "3")]
    return [grade for key, grade in mapping if row.get(key) == "Y"]


def _timetable_endpoint(school_kind: str) -> str | None:
    if "초등" in school_kind:
        return "elsTimetable"
    if "중학교" in school_kind:
        return "misTimetable"
    if "고등" in school_kind:
        return "hisTimetable"
    return None


def _compact_date(value: str | None) -> str | None:
    return value.replace("-", "") if value else None


def _display_date(value: str) -> str:
    if len(value) != 8:
        return value
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def _now() -> str:
    return datetime.now(UTC).isoformat()
