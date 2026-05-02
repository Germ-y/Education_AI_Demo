# NEIS 데이터 수집 및 조회 API 계획

확인 기준일: 2026-05-02

## 1. 결론

콘텐츠 생성 전에 먼저 NEIS 데이터를 아래 순서로 고정한다.

```text
1. 학교기본정보 schoolInfo
2. 학사일정 SchoolSchedule
3. 시간표 elsTimetable / misTimetable / hisTimetable
4. seed snapshot 저장
5. 교사/프론트 조회 API 제공
6. 오케스트레이터 입력에는 요약본만 전달
```

MVP에서는 실시간 호출보다 **사전 수집 snapshot + 조회 API**를 우선한다.

이유:

```text
공공데이터 API 장애/속도/쿼터와 관계없이 데모 화면이 안정적으로 떠야 한다.
오케스트레이터가 매번 NEIS를 직접 호출하면 콘텐츠 생성 속도와 재현성이 흔들린다.
```

## 2. 현재 확인된 영주시 학교

NEIS `schoolInfo`에서 경상북도교육청 코드 `R10`으로 조회했고, 영주시 학교 39개가 확인됐다.

현재 seed 학생 3명에는 아래 학교를 먼저 연결한다.

| 학생 | 학교급 | NEIS 학교코드 | 학교명 | 주소 |
| --- | --- | --- | --- | --- |
| 지우 | 초등학교 | `8811046` | 영주중앙초등학교 | 경상북도 영주시 중앙로 126 |
| 민준 | 중학교 | `8811058` | 영주중학교 | 경상북도 영주시 남간로 29 |
| 수민 | 초등학교 | `8811067` | 영주가흥초등학교 | 경상북도 영주시 대동로70번길 8-9 |

## 3. NEIS Endpoint Shape

### 3.1 학교기본정보

Endpoint:

```text
GET https://open.neis.go.kr/hub/schoolInfo
```

주요 요청값:

```text
KEY
Type=json
ATPT_OFCDC_SC_CODE=R10
```

정규화 필드:

```json
{
  "officeCode": "R10",
  "schoolCode": "8811058",
  "schoolName": "영주중학교",
  "schoolKind": "중학교",
  "regionName": "경상북도 영주시",
  "roadAddress": "경상북도 영주시 남간로 29",
  "sourceCode": "neis_open_api"
}
```

### 3.2 학사일정

Endpoint:

```text
GET https://open.neis.go.kr/hub/SchoolSchedule
```

주요 요청값:

```text
KEY
Type=json
ATPT_OFCDC_SC_CODE=R10
SD_SCHUL_CODE=8811058
AA_FROM_YMD=20260501
AA_TO_YMD=20260515
```

확인된 응답 필드:

```json
{
  "AA_YMD": "20260501",
  "EVENT_NM": "노동절",
  "EVENT_CNTNT": "",
  "SBTR_DD_SC_NM": "공휴일",
  "ONE_GRADE_EVENT_YN": "Y",
  "TW_GRADE_EVENT_YN": "Y",
  "THREE_GRADE_EVENT_YN": "Y",
  "LOAD_DTM": "20260502"
}
```

정규화 필드:

```json
{
  "schoolCode": "8811058",
  "officeCode": "R10",
  "academicYear": "2026",
  "eventDate": "2026-05-01",
  "eventName": "노동절",
  "eventContent": "",
  "scheduleType": "공휴일",
  "appliesToGrades": ["1", "2", "3"],
  "sourceCode": "neis_school_schedule",
  "retrievedAt": "2026-05-02T00:00:00.000Z"
}
```

### 3.3 시간표

학교급별 endpoint:

| 학교급 | endpoint |
| --- | --- |
| 초등학교 | `elsTimetable` |
| 중학교 | `misTimetable` |
| 고등학교 | `hisTimetable` |

주요 요청값:

```text
KEY
Type=json
ATPT_OFCDC_SC_CODE=R10
SD_SCHUL_CODE=8811058
AY=2026
SEM=1
ALL_TI_YMD=20260501
GRADE=2
CLASS_NM=1
```

확인된 중학교 응답 필드:

```json
{
  "ALL_TI_YMD": "20260501",
  "GRADE": "2",
  "CLASS_NM": "1",
  "PERIO": "1",
  "ITRT_CNTNT": "역사",
  "LOAD_DTM": "20260502"
}
```

정규화 필드:

```json
{
  "schoolCode": "8811058",
  "officeCode": "R10",
  "academicYear": "2026",
  "semester": "1",
  "timetableDate": "2026-05-01",
  "grade": "2",
  "className": "1",
  "period": 1,
  "subjectName": "역사",
  "sourceCode": "neis_mis_timetable",
  "retrievedAt": "2026-05-02T00:00:00.000Z"
}
```

초등학교 시간표는 응답 row가 내려와도 `ITRT_CNTNT`가 `null`일 수 있다. 이 경우 `subjectName=null`로 저장하고, 콘텐츠 추천에는 과목 라우팅 근거로 쓰지 않는다.

## 4. 조회 API

MVP에서 먼저 제공하는 조회 API:

```text
GET /api/public-data/schools
GET /api/public-data/schools/{schoolCode}/context
```

`context` query:

```text
fromDate=2026-05-01
toDate=2026-05-15
timetableDate=2026-05-01
grade=2
className=1
```

응답 shape:

```json
{
  "school": {},
  "calendar": [],
  "timetableSummary": [],
  "source": {
    "sourceCode": "neis_open_api",
    "mode": "seed_snapshot",
    "endpoints": ["schoolInfo", "SchoolSchedule", "elsTimetable", "misTimetable"]
  }
}
```

## 5. 학생 Seed 연결

학생 seed에는 최소 아래 정보가 있어야 한다.

```json
{
  "schoolCode": "8811058",
  "grade": "middle_2",
  "profileJson": {
    "className": "1"
  }
}
```

현재는 학년/학교코드 중심으로 연결하고, 반 정보는 시간표 조회를 붙일 때 `profileJson.className`으로 확장한다.

## 6. 오케스트레이터 입력 규칙

오케스트레이터에는 NEIS 원본 row 전체를 넣지 않는다.

넣는 값:

```json
{
  "schoolContext": {
    "schoolName": "영주중학교",
    "upcomingEvents": ["2026-05-04 재량휴업일"],
    "todaySubjects": ["역사", "동아리활동", "진로와 직업", "국어", "과학", "도덕"]
  }
}
```

사용 방식:

```text
휴업/시험/행사 전후 → 새 개념보다 짧은 복습 또는 성공 경험 우선
오늘 수학/국어 등 관련 과목 있음 → 해당 과목 콘텐츠 우선순위 상승
시간표 subjectName 없음 → 시간표 기반 추천 근거로 사용하지 않음
```

## 7. 지금 구현 상태

```text
학교기본정보 seed snapshot: 완료
학사일정 seed snapshot: 완료
중학교 시간표 seed snapshot: 완료
조회 API: 완료
실제 DB import job: 이후 단계
프론트 fetching 연결: 이후 단계
```
