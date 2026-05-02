# 프론트/백엔드 스키마 계약

이 문서는 프론트가 API 연결과 mock 데이터를 맞출 때 기준으로 삼는 공통 스키마 계약이다.
상세 endpoint는 [08-rest-api-spec.md](08-rest-api-spec.md)를 보고, 데이터 모양은 이 문서를 우선 기준으로 본다.

## 1. 공통 규칙

- JSON field는 `camelCase`를 쓴다.
- 시간 값은 ISO-8601 문자열이다.
- 성공 응답은 항상 `data`와 `meta.requestId`를 가진다.
- 오류 응답은 항상 `error.code`, `error.message`, `error.details`를 가진다.
- 학생에게 노출되는 콘텐츠는 `status = "published"`만 허용한다.
- `MissionContent.totalSteps`는 항상 `4`다.
- `ContentStage.step`은 `1, 2, 3, 4`만 허용한다.
- realtime은 `step = 4`에서만 허용한다.
- 이미지 asset은 `hero`, `stage_1`, `stage_2`, `stage_3`, `stage_4_realtime`을 모두 가져야 한다.

## 2. 응답 envelope

성공:

```json
{
  "data": {},
  "meta": {
    "requestId": "uuid"
  }
}
```

오류:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "로그인이 필요합니다.",
    "details": {}
  }
}
```

프론트는 오류 처리 시 `error.code`를 우선 분기 기준으로 사용한다.

## 3. enum 고정값

### UserRole

```text
center_admin
teacher
content_reviewer
guardian
student
```

### StudentType

```text
life_support
learning_focus
```

### MissionStatus

```text
draft
generating
teacher_review
revision_requested
approved
published
archived
```

### StageRole

```text
scenario_intro
clue_identification
action_selection
concept_intro
basic_problem
applied_problem
realtime_practice
```

### TemplateType

```text
scenario_intro
scene_observation
highlight_clue
card_match
action_choice
sequence_ordering
decision_card
concept_intro
scene_question
clue_question
blank_fill
partition_picker
applied_question
mini_simulation
realtime_roleplay
realtime_teach_back
```

### AssetRole

```text
hero
stage_1
stage_2
stage_3
stage_4_realtime
```

### AssetType

```text
image
audio_optional
```

## 4. Auth 스키마

### DemoLoginRequest

```json
{
  "role": "teacher",
  "email": "teacher.demo@eduyj.local"
}
```

### StudentAccessRequest

```json
{
  "accessCode": "STAR-001"
}
```

### AuthResponse.data

교사 로그인:

```json
{
  "user": {
    "id": "user_teacher_demo",
    "organizationId": "org_yj_center",
    "email": "teacher.demo@eduyj.local",
    "displayName": "데모 선생님",
    "role": "teacher",
    "status": "active"
  },
  "session": {
    "accessToken": "demo.user.uuid",
    "expiresAt": "2026-05-02T12:00:00+00:00"
  }
}
```

학생 로그인:

```json
{
  "student": {
    "id": "student_learning_fraction",
    "organizationId": "org_yj_center",
    "externalKey": "demo-learning-001",
    "displayName": "수민",
    "grade": "middle_2",
    "schoolCode": "school_demo_001",
    "studentType": "learning_focus",
    "primaryNeed": "분수의 전체-부분 관계 이해",
    "profileJson": {},
    "status": "active"
  },
  "session": {
    "accessToken": "demo.student.uuid",
    "expiresAt": "2026-05-02T12:00:00+00:00"
  }
}
```

## 5. 교사 대시보드 스키마

### TeacherStudentListItem

`GET /api/teacher/students`의 `data[]` 항목이다.

```json
{
  "studentId": "student_learning_fraction",
  "displayName": "수민",
  "grade": "middle_2",
  "studentType": "learning_focus",
  "primaryNeed": "분수의 전체-부분 관계 이해",
  "latestContentStatus": "published",
  "nextSessionSuggestion": "분모/분자 위치를 짧게 재확인"
}
```

### StudentCaseFile

`GET /api/teacher/students/:studentId`의 `data`다.

```json
{
  "profile": "Student",
  "openCase": "SupportCase",
  "memoryCard": "MemoryCard | null",
  "weeklyRecords": ["CaseNote"],
  "monthlySummary": {
    "repeatedProblemTypes": ["분모/분자 혼동"],
    "growth": "seed 데모 기준 최근 수행 안정화",
    "stillBlocking": ["첫 문제는 쉬운 성공 경험으로 시작"]
  },
  "recentContents": ["MissionContent"],
  "plannerItems": ["PlannerItem"],
  "publicContextSummary": {
    "schoolCode": "school_demo_001",
    "sources": ["neis_open_api"]
  }
}
```

## 6. 학생 미션 스키마

### StudentMissionSummary

`GET /api/student/missions/today`의 `data[]` 항목이다.

```json
{
  "contentId": "content_fraction_001",
  "title": "분수 탐험: 빛나는 한 조각",
  "contentType": "learning_focus",
  "totalSteps": 4,
  "heroImageUrl": "/examples/generated/fraction-mission/fraction-pizza.png",
  "status": "published"
}
```

### MissionContent

`GET /api/student/missions/:contentId`의 `data`다.

```json
{
  "id": "content_fraction_001",
  "caseId": "case_learning_fraction",
  "studentId": "student_learning_fraction",
  "contentType": "learning_focus",
  "title": "분수 탐험: 빛나는 한 조각",
  "sessionGoal": "전체 4개 중 1개를 1/4로 표현하고 말로 설명한다.",
  "status": "published",
  "totalSteps": 4,
  "stages": ["ContentStage"],
  "assets": ["ContentAsset"],
  "briefJson": {},
  "teacherReviewSummary": "교사용 요약",
  "approvedByUserId": "user_teacher_demo",
  "approvedAt": "2026-05-02T00:00:00.000Z",
  "publishedAt": "2026-05-02T00:00:00.000Z"
}
```

### ContentStage

```json
{
  "id": "stage_fraction_2",
  "missionContentId": "content_fraction_001",
  "step": 2,
  "stageRole": "basic_problem",
  "templateType": "partition_picker",
  "studentTitle": "문제 1",
  "studentInstruction": "전체 조각 수와 고른 조각 수를 차례대로 세어보세요.",
  "templateJson": {},
  "realtimeSpec": null,
  "sortOrder": 2
}
```

4단계만 `realtimeSpec`이 필수다.

```json
{
  "id": "stage_fraction_4",
  "missionContentId": "content_fraction_001",
  "step": 4,
  "stageRole": "realtime_practice",
  "templateType": "realtime_teach_back",
  "studentTitle": "AI에게 말해보기",
  "studentInstruction": "별이에게 왜 1/4인지 말로 설명해보세요.",
  "templateJson": {
    "imageAssetId": "asset_content_fraction_001_stage_4_realtime"
  },
  "realtimeSpec": "RealtimePracticeSpec",
  "sortOrder": 4
}
```

### ContentAsset

```json
{
  "id": "asset_content_fraction_001_stage_2",
  "missionContentId": "content_fraction_001",
  "stageId": "stage_fraction_2",
  "assetRole": "stage_2",
  "assetType": "image",
  "provider": "openai",
  "model": "gpt-image-2",
  "promptJson": {},
  "storageUrl": "/examples/generated/fraction-mission/fraction-pizza.png",
  "previewUrl": "/examples/generated/fraction-mission/fraction-pizza.png",
  "qaStatus": "passed",
  "approvalStatus": "approved"
}
```

## 7. RealtimePracticeSpec

```json
{
  "id": "rt_spec_fraction_001",
  "stageId": "stage_fraction_4",
  "templateType": "realtime_teach_back",
  "imageAssetId": "asset_content_fraction_001_stage_4_realtime",
  "mode": "voice_or_text",
  "practiceTitle": "별이에게 분수 설명하기",
  "situationText": "별이가 빛나는 피자 조각을 보고 왜 1/4인지 궁금해해요.",
  "aiRole": "별이",
  "openingLine": "왜 4/1이 아니라 1/4인지 알려줄래?",
  "studentGoal": "전체 4개 중 고른 것이 1개라서 1/4이라고 설명하기",
  "rubric": [
    {
      "id": "mention_whole",
      "label": "전체가 4개임을 말한다",
      "required": true
    }
  ],
  "allowedFeedback": ["좋아요. 전체가 몇 개인지 말했어요."],
  "forbidden": ["학생에게 진단 라벨 말하지 않기"],
  "maxTurns": 6,
  "maxDurationSec": 120,
  "postPracticeReflection": ["쉬웠어요", "조금 헷갈렸어요", "다시 연습하고 싶어요"]
}
```

프론트는 `realtimeSpec` 원문 전체를 학생에게 노출하지 않는다.
학생 화면에는 `practiceTitle`, `situationText`, `openingLine`, `maxTurns`, `maxDurationSec` 정도만 사용한다.

## 8. 학생 플레이 request/response

### StartMissionResponse.data

```json
{
  "id": "attempt_uuid",
  "missionContentId": "content_fraction_001",
  "studentId": "student_learning_fraction",
  "status": "in_progress",
  "currentStep": 1,
  "startedAt": "2026-05-02T12:00:00+00:00",
  "completedAt": null,
  "scoreJson": null
}
```

### StageSubmitRequest

1~3단계에서만 사용한다.

```json
{
  "attemptId": "attempt_uuid",
  "answer": {
    "choiceId": "b"
  },
  "clientEventId": "evt_client_001"
}
```

### StageSubmitResponse.data

```json
{
  "isRealtimeStage": false,
  "isCorrect": true,
  "feedback": "맞아요. 전체는 4조각이에요.",
  "nextStep": 3
}
```

4단계에 submit하면 오류가 난다.

```json
{
  "error": {
    "code": "REALTIME_STAGE_SUBMIT_BLOCKED",
    "message": "4단계는 realtime-session API를 사용해야 합니다.",
    "details": {}
  }
}
```

### RealtimeSessionRequest

```json
{
  "attemptId": "attempt_uuid"
}
```

### RealtimeSessionResponse.data

```json
{
  "sessionId": "rt_session_uuid",
  "provider": "openai",
  "model": "gpt-realtime",
  "clientSecret": "server-issued-or-demo-secret",
  "expiresAt": "2026-05-02T12:05:00+00:00",
  "webrtcUrl": "https://api.openai.com/v1/realtime/calls",
  "practiceSpec": {
    "practiceTitle": "별이에게 분수 설명하기",
    "imageAssetUrl": "/examples/generated/fraction-mission/fraction-pizza.png",
    "openingLine": "왜 4/1이 아니라 1/4인지 알려줄래?",
    "maxTurns": 6,
    "maxDurationSec": 120
  }
}
```

### ReflectionRequest

```json
{
  "attemptId": "attempt_uuid",
  "reflectionChoice": "조금 헷갈렸어요",
  "shortText": "아래 숫자가 전체인 게 헷갈렸어요"
}
```

## 9. 프론트 mock 점검 기준

프론트 mock 또는 임시 데이터는 아래를 반드시 만족해야 한다.

- `MissionContent.totalSteps`는 `4`
- `stages.length`는 `4`
- `stages[].step`은 `[1, 2, 3, 4]`
- 1~3단계 `templateType`은 realtime 계열이 아님
- 4단계 `templateType`은 `realtime_roleplay` 또는 `realtime_teach_back`
- 4단계 `realtimeSpec`은 null이 아님
- `assets`에는 필수 5개 role이 모두 있음
- `heroImageUrl`은 `assetRole = "hero"`에서 온 값
- secret, provider key, prompt 원문은 프론트 mock에 넣지 않음

## 10. 백엔드 우선 수정 대상

프론트가 계약 점검 중 아래를 발견하면 백엔드 확인 요청으로 넘긴다.

- 문서에는 있는 field가 API 응답에 없음
- API 응답 field가 snake_case로 내려옴
- 오류 응답이 `error` envelope가 아님
- 4단계 외 stage에서 realtime template이 내려옴
- `published`가 아닌 미션이 학생 API에 내려옴
- 이미지 asset role이 부족함
- realtime session 응답에 `clientSecret`이 없음
