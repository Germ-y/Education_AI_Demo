import json
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    if not settings.neis_api_key:
        raise SystemExit("NEIS_API_KEY is missing.")

    params = {
        "KEY": settings.neis_api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,
        "ATPT_OFCDC_SC_CODE": "R10",
    }
    url = "https://open.neis.go.kr/hub/schoolInfo?" + urlencode(params)
    with urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rows = payload.get("schoolInfo", [{}, {"row": []}])[1].get("row", [])
    yeongju_rows = [
        row
        for row in rows
        if "영주시" in (row.get("ORG_RDNMA") or "") or "영주" in (row.get("SCHUL_NM") or "")
    ]
    result = [
        {
            "schoolName": row.get("SCHUL_NM"),
            "schoolCode": row.get("SD_SCHUL_CODE"),
            "schoolKind": row.get("SCHUL_KND_SC_NM"),
            "officeCode": row.get("ATPT_OFCDC_SC_CODE"),
            "roadAddress": row.get("ORG_RDNMA"),
        }
        for row in yeongju_rows
    ]
    print(json.dumps({"count": len(result), "schools": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
