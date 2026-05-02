# REST API Spec

확인 기준일: 2026-05-02

## 1. 공통 규칙

프론트/백엔드가 공유하는 단계별 기능, field, enum, MissionContent 구조는 [12-schema-contract.md](12-schema-contract.md)를 우선 기준으로 한다.
이 문서는 endpoint별 request/response 흐름 초안이다.
단계 기능이 바뀌면 이 문서보다 [12-schema-contract.md](12-schema-contract.md)를 먼저 고친다.

Base path:

```text
/api
```

응답 envelope:

```json
{
  "data": {},
  "meta": {
    "requestId": "req_001"
  }
}
```

오류 envelope:

```json
{
  "error": {
    "code": "CONTENT_NOT_APPROVED",
    "message": "승인된 콘텐츠만 학생에게 노출할 수 있습니다.",
    "details": {}
  }
}
```

권한:

```text
teacher/admin API: session 또는 bearer token
student API: student session 또는 access code session
AI provider key: 서버에만 보관
Realtime client secret: 짧은 TTL로 발급
```

## 2. Context And Demo Auth APIs

MVP에서는 회원가입/일반 로그인보다 seed된 사용자/학생/학교 데이터를 조회하는 것이 먼저다.
`demo-login`과 `student-access`는 개발/공모전 데모용이다.

### GET /api/context/me

현재 데모 사용자와 조직 정보를 조회한다.

```json
{
  "data": {
    "user": "UserProfile",
    "organization": "Organization",
    "mode": "demo_seed"
  },
  "meta": {
    "requestId": "req_001"
  }
}
```

### POST /api/auth/demo-login

데모 계정으로 로그인한다.

```json
{
  "role": "teacher",
  "email": "teacher.demo@eduyj.local"
}
```

응답:

```json
{
  "user": {
    "id": "user_teacher_001",
    "role": "teacher",
    "displayName": "데모 선생님"
  },
  "session": {
    "accessToken": "demo.jwt",
    "expiresAt": "2026-05-02T12:00:00.000Z"
  }
}
```

### POST /api/auth/student-access

학생 간편 코드 로그인.

```json
{
  "accessCode": "STAR-001"
}
```

## 3. Teacher Student APIs

### GET /api/teacher/students

학생 목록과 현재 상태 요약.

Query:

```text
studentType=life_support|learning_focus
q=검색어
caseStatus=open
```

응답:

```json
{
  "data": [
    {
      "studentId": "student_001",
      "displayName": "민준",
      "grade": "middle_2",
      "studentType": "learning_focus",
      "primaryNeed": "분수의 전체-부분 관계 이해",
      "latestContentStatus": "completed",
      "nextSessionSuggestion": "분모/분자 위치를 짧게 재확인"
    }
  ]
}
```

### GET /api/teacher/students/:studentId

학생 케이스 파일 상세.

포함:

```text
profile
openCase
memoryCard
weeklyRecords
monthlySummary
recentContents
plannerItems
publicContextSummary
```

### PATCH /api/teacher/students/:studentId/memory-card

교사가 메모리 카드 일부를 수정한다.

```json
{
  "effectiveExplanationStyles": ["visual_example", "short_steps"],
  "nextSessionCautions": ["첫 문제는 쉬운 성공 경험으로 시작"]
}
```

## 4. Case APIs

### GET /api/cases/:caseId/notes

회기 기록과 상담 메모 조회.

### POST /api/cases/:caseId/notes

```json
{
  "noteType": "session",
  "body": "분수 그림에는 집중했지만 4/1을 골랐음",
  "visibility": "teacher_only"
}
```

### GET /api/cases/:caseId/planner

주차별/월별 계획 조회.

### PATCH /api/cases/:caseId/planner/:plannerItemId

계획 항목 수정.

## 5. AI Generation APIs

### POST /api/ai/orchestrator-runs

학생 맥락을 읽고 콘텐츠 생성 계획을 만든다.

```json
{
  "studentId": "student_001",
  "caseId": "case_001",
  "requestedGoal": "분수에서 전체와 부분의 관계를 이해한다",
  "contentType": "learning_focus"
}
```

응답:

```json
{
  "orchestratorRunId": "agent_run_orch_001",
  "sessionGoal": "전체 4개 중 1개를 1/4로 표현한다",
  "selectedFlow": [
    "concept_intro",
    "basic_problem",
    "applied_problem",
    "realtime_teach_back"
  ],
  "teacherSummary": "최근 분모/분자 위치 혼동이 있어 시각 자료와 말로 설명하기를 사용합니다."
}
```

### POST /api/ai/content-generations

콘텐츠 패키지 생성을 요청한다.

```json
{
  "orchestratorRunId": "agent_run_orch_001",
  "studentId": "student_001",
  "caseId": "case_001"
}
```

응답:

```json
{
  "contentId": "content_001",
  "status": "generating",
  "jobs": [
    { "type": "content_json", "status": "queued" },
    { "type": "image_package", "status": "queued" },
    { "type": "auto_validation", "status": "queued" }
  ]
}
```

### GET /api/ai/agent-runs/:agentRunId

AI 실행 상태/결과 조회.

## 6. Content Review APIs

### GET /api/contents/:contentId

교사용 콘텐츠 상세. `teacher_review` 상태도 볼 수 있다.

### POST /api/contents/:contentId/request-image-regeneration

특정 이미지 재생성 요청.

```json
{
  "assetRole": "stage_2",
  "reason": "강조 조각이 2개처럼 보임",
  "teacherInstruction": "한 조각만 더 명확히 빛나게 해주세요."
}
```

### POST /api/contents/:contentId/approve

교사 승인.

```json
{
  "approvedStageIds": ["stage_001", "stage_002", "stage_003", "stage_004"],
  "approvedAssetIds": ["asset_hero", "asset_s1", "asset_s2", "asset_s3", "asset_s4"],
  "reviewNote": "학생 수준에 적합함"
}
```

### POST /api/contents/:contentId/reject

반려/수정 요청.

```json
{
  "reason": "문제 2 난이도가 높음",
  "requestedChanges": ["난이도 낮추기", "힌트 문장 추가"]
}
```

### POST /api/contents/:contentId/publish

승인된 콘텐츠를 학생에게 배포한다.

## 7. Student Mission APIs

### GET /api/student/missions/today

학생의 오늘 미션 목록.

응답:

```json
{
  "data": [
    {
      "contentId": "content_001",
      "title": "분수 탐험: 빛나는 한 조각",
      "contentType": "learning_focus",
      "totalSteps": 4,
      "heroImageUrl": "https://cdn.example.com/hero.png",
      "status": "published"
    }
  ]
}
```

### GET /api/student/missions/:contentId

승인/배포된 미션만 반환한다.

### POST /api/student/missions/:contentId/start

`content_attempts`를 생성한다.

### POST /api/student/missions/:contentId/stages/:stageId/submit

1~3단계 제출. 4단계는 submit이 아니라 realtime session을 사용한다.

```json
{
  "attemptId": "attempt_001",
  "answer": {
    "choiceId": "a"
  },
  "clientEventId": "evt_client_001"
}
```

응답:

```json
{
  "isCorrect": true,
  "feedback": "좋아요. 전체 4조각 중 1조각이니까 1/4이에요.",
  "nextStep": 3
}
```

### POST /api/student/missions/:contentId/events

힌트 사용, 화면 진입, 체류시간 등 이벤트 저장.

## 8. Realtime Stage APIs

### POST /api/student/missions/:contentId/stages/:stageId/realtime-session

4단계 realtime 세션 생성.

서버 검증:

```text
content.status == published
stage.step == 4
stage.realtime_spec_json exists
student has access
no active duplicate session
```

응답:

```json
{
  "sessionId": "rt_session_001",
  "provider": "openai",
  "model": "gpt-realtime",
  "clientSecret": "ek_...",
  "expiresAt": "2026-05-02T12:10:00.000Z",
  "webrtcUrl": "https://api.openai.com/v1/realtime/calls",
  "practiceSpec": {
    "practiceTitle": "별이에게 분수 설명하기",
    "imageAssetUrl": "https://cdn.example.com/stage4.png",
    "openingLine": "왜 4/1이 아니라 1/4인지 알려줄래?",
    "maxTurns": 6,
    "maxDurationSec": 120
  }
}
```

### POST /api/student/realtime-sessions/:sessionId/events

Realtime 이벤트 저장. 클라이언트 이벤트, sideband 이벤트, 서버 평가 이벤트를 같은 session에 묶는다.

### POST /api/student/realtime-sessions/:sessionId/complete

세션 종료와 루브릭 요약 저장.

```json
{
  "turnCount": 4,
  "durationSec": 78,
  "rubricResult": {
    "passed": ["mention_whole", "mention_part"],
    "needsSupport": ["connect_fraction"]
  },
  "transcriptSummary": "전체와 고른 조각은 말했지만 분수 표현 연결은 한 번 더 도움이 필요합니다."
}
```

## 9. Reflection And Review APIs

### POST /api/student/missions/:contentId/post-practice-reflection

```json
{
  "attemptId": "attempt_001",
  "reflectionChoice": "조금 헷갈렸어요",
  "shortText": "아래 숫자가 전체인 게 헷갈렸어요"
}
```

### POST /api/student/missions/:contentId/complete

attempt 완료.

### POST /api/contents/:contentId/review-summary

ReviewAgent 실행 요청.

### GET /api/contents/:contentId/review-summary

리뷰 요약 조회.

### POST /api/review-summaries/:reviewId/apply-to-memory

교사가 리뷰 요약을 메모리 카드에 반영한다.

## 10. Public Data APIs

### GET /api/public-data/sources

등록된 source 목록.

### POST /api/public-data/sources/:sourceCode/sync

```json
{
  "regionCode": "47210",
  "schoolCode": "sample_school",
  "fromDate": "2026-05-01",
  "toDate": "2026-05-31"
}
```

### GET /api/public-data/sync-jobs/:jobId

sync job 상태 조회.

### GET /api/public-data/schools/search

학교 검색.

### GET /api/public-data/schools/:schoolId/calendar

학사일정 조회.

### GET /api/public-data/schools/:schoolId/context

학생/교사 화면에서 바로 쓰는 학교 맥락 요약.

응답:

```json
{
  "school": "SchoolProfile",
  "calendar": ["SchoolCalendarItem"],
  "timetableSummary": {
    "todaySubjects": ["수학", "국어", "영어"],
    "source": "NEIS_TIMETABLE"
  },
  "educationStats": ["EducationStat"],
  "lastSyncedAt": "2026-05-02T00:00:00.000Z"
}
```

### GET /api/public-data/schools/:schoolId/timetable

시간표 조회.

### GET /api/public-data/curriculum-standards

성취기준 조회.

### GET /api/public-data/education-stats

교육통계 조회.

## 11. Admin And Seed APIs

### POST /api/admin/seed/demo

개발/공모전 환경에서만 허용.

```json
{
  "reset": false,
  "includePublicDataSnapshot": true,
  "includeSampleContents": true
}
```

### POST /api/admin/users/invite

시간이 남으면 추가하는 교사 초대 기능.

### POST /api/admin/students

시간이 남으면 추가하는 아이등록 기능.

## 12. API Safety Rules

- 학생 API는 `teacher_review`, `generating`, `rejected` 콘텐츠를 반환하지 않는다.
- 학생 API는 AI 생성 endpoint를 호출할 수 없다.
- 4단계 realtime client secret은 서버가 발급하고 TTL을 짧게 둔다.
- AI prompt 원문은 관리자/디버그 권한에서만 조회한다.
- 모든 승인/반려/메모리 반영은 `audit_logs`에 기록한다.
