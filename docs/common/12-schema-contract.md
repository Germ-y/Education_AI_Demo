# 도메인 온보딩 및 단계별 스키마 계약

이 문서는 프론트/백엔드가 기능을 시작하기 전에 먼저 맞춰야 하는 공통 계약이다.
REST API endpoint를 먼저 외우는 문서가 아니라, 전체 도메인과 학생 미션 단계가 각각 어떤 기능을 가져야 하는지 온보딩하면서 합의하기 위한 기준이다.

endpoint 상세는 [08-rest-api-spec.md](08-rest-api-spec.md)를 보되, field와 단계 의미는 이 문서를 우선 기준으로 한다.

## 1. 먼저 고정할 MVP 범위

이번 공모전 MVP는 회원가입/일반 로그인부터 만들지 않는다.

우선순위는 아래다.

```text
1. seed로 센터/사용자/학생/학교/사례/공공데이터 snapshot을 미리 넣는다.
2. 프론트는 seed된 사용자/학생/학교 정보를 조회한다.
3. 교사 대시보드는 학생 케이스 파일과 공공데이터 기반 학교 맥락을 보여준다.
4. 학생 미션은 published 콘텐츠를 조회해 1~4단계로 플레이한다.
5. AI 생성/승인/realtime은 조회성 도메인 계약이 맞은 뒤 붙인다.
```

즉, 지금 먼저 맞출 것은 `가입 플로우`가 아니라 `조회 가능한 도메인 read model`이다.

MVP에서 하지 않는 것:

```text
교사 회원가입
비밀번호 로그인
아이 직접 등록
보호자 가입
프로덕션 권한/초대 플로우
```

MVP에서 하는 것:

```text
seed 사용자 정보 조회
seed 학생 정보 조회
학생별 학교 연결 정보 조회
공공데이터 snapshot 기반 학교/일정/통계 맥락 조회
학생 케이스 파일 조회
학생별 미션 조회
```

## 2. 도메인 온보딩 단계

팀원이 처음 기능을 나눌 때는 아래 순서로 스키마를 고정한다.

| 순서 | 기능 단위 | 목표 | 먼저 합의할 스키마 |
| --- | --- | --- | --- |
| 1 | `seeded-domain-read` | 센터/사용자/학생/학교 데이터가 화면에 조회되는지 확인 | Organization, UserProfile, StudentProfile, SchoolProfile |
| 2 | `school-public-context` | 학생과 학교/공공데이터 맥락을 연결 | PublicContextBundle, SchoolCalendarItem, EducationStat |
| 3 | `teacher-case-read` | 교사 대시보드에서 학생 케이스 파일 조회 | StudentListItem, StudentCaseFile, MemoryCard |
| 4 | `student-mission-read` | 학생이 published 미션을 조회 | StudentMissionSummary, MissionContent |
| 5 | `student-mission-runtime` | 1~3단계 제출과 회고 저장 | ContentAttempt, StageSubmit, Reflection |
| 6 | `content-review` | 교사가 AI 생성 콘텐츠를 검토/승인 | ReviewableContent, ApprovalRequest |
| 7 | `realtime-practice` | 4단계 realtime session 생성 | RealtimePracticeSpec, RealtimeSession |
| 8 | `ai-generation` | 오케스트레이터/이미지 생성/AgentRun 기록 | AgentRun, ImageAssetJob, ContentBrief |

처음 구현은 1~3번만으로도 프론트/백엔드 계약을 충분히 맞출 수 있어야 한다.

## 3. 공통 도메인 read model

### 3.1 Organization

센터와 학교를 모두 조직으로 볼 수 있다.
MVP에서는 센터 조직 1개와 학생이 속한 학교 정보를 seed 또는 public data snapshot으로 넣는다.

```json
{
  "id": "org_yj_center",
  "externalKey": "demo_org_yeongju_center",
  "name": "영주 기초학력거점지원센터",
  "type": "learning_support_center",
  "regionCode": "47210"
}
```

### 3.2 UserProfile

회원가입 없이 seed로 미리 들어가는 교사/센터 사용자 정보다.
프론트는 이 정보를 로그인 폼 구현보다 먼저 `현재 데모 사용자`로 다룬다.

```json
{
  "id": "user_teacher_demo",
  "organizationId": "org_yj_center",
  "email": "teacher.demo@eduyj.local",
  "displayName": "데모 선생님",
  "role": "teacher",
  "status": "active"
}
```

### 3.3 StudentProfile

학생은 회원가입 대상이 아니라 센터/교사가 관리하는 케이스 대상이다.
학교 연결은 `schoolCode`로 한다.

```json
{
  "id": "student_learning_fraction",
  "organizationId": "org_yj_center",
  "externalKey": "demo-learning-001",
  "displayName": "이민준",
  "grade": "middle_2",
  "schoolCode": "school_demo_001",
  "studentType": "learning_focus",
  "primaryNeed": "분수의 전체-부분 관계를 단계적으로 익히는 개념 보완 수업이 좋겠어요.",
  "profileJson": {
    "interests": ["음식", "탐험"],
    "readingLoad": "low",
    "choiceCountLimit": 3
  },
  "status": "active"
}
```

### 3.4 SchoolProfile

학교 정보는 학생의 학교 맥락을 만들기 위한 조회 모델이다.
NEIS/학교알리미를 붙이기 전에는 seed snapshot으로 시작한다.

```json
{
  "id": "school_demo_001",
  "schoolCode": "school_demo_001",
  "officeCode": "R10",
  "name": "영주 데모중학교",
  "schoolLevel": "middle",
  "regionCode": "47210",
  "address": "경상북도 영주시",
  "source": "seed_snapshot"
}
```

### 3.5 PublicContextBundle

학생 상세 화면이나 오케스트레이터 입력에서 쓰는 공공데이터 요약이다.
원본 공공데이터 전체를 프론트에 그대로 넘기지 않고, 화면과 추천에 필요한 요약만 내려준다.

```json
{
  "studentId": "student_learning_fraction",
  "school": "SchoolProfile",
  "calendar": [
    {
      "date": "2026-05-06",
      "title": "중간고사",
      "source": "NEIS_SCHOOL_SCHEDULE"
    }
  ],
  "timetableSummary": {
    "todaySubjects": ["수학", "국어", "영어"],
    "source": "NEIS_TIMETABLE"
  },
  "educationStats": [
    {
      "label": "다문화 학생 수 변화",
      "value": "2025년 기준 증가 추세",
      "source": "KESS"
    }
  ],
  "lastSyncedAt": "2026-05-02T00:00:00.000Z"
}
```

## 4. 교사 대시보드 read model

### 4.1 StudentListItem

학생 목록은 단순 이름 목록이 아니라 케이스 상태 요약이어야 한다.

```json
{
  "studentId": "student_learning_fraction",
  "displayName": "이민준",
  "grade": "middle_2",
  "schoolName": "영주 데모중학교",
  "studentType": "learning_focus",
  "primaryNeed": "분수의 전체-부분 관계를 단계적으로 익히는 개념 보완 수업이 좋겠어요.",
  "caseStatus": "open",
  "latestContentStatus": "published",
  "nextSessionSuggestion": "분모/분자 위치를 짧게 재확인"
}
```

### 4.2 StudentCaseFile

교사 상세 화면의 기준 read model이다.

```json
{
  "profile": "StudentProfile",
  "schoolContext": "PublicContextBundle",
  "openCase": {
    "id": "case_learning_fraction",
    "studentId": "student_learning_fraction",
    "ownerTeacherId": "user_teacher_demo",
    "caseStatus": "open",
    "currentGoal": "분수의 전체-부분 관계를 단계 카드로 안정화해보면 좋겠어요.",
    "openedAt": "2026-05-02T00:00:00.000Z"
  },
  "memoryCard": "MemoryCard",
  "weeklyRecords": ["CaseNote"],
  "monthlySummary": "MonthlySummary",
  "recentContents": ["MissionContent"],
  "plannerItems": ["PlannerItem"]
}
```

### 4.3 MemoryCard

```json
{
  "id": "memory_learning_fraction_v1",
  "studentId": "student_learning_fraction",
  "caseId": "case_learning_fraction",
  "version": 1,
  "learningProblemTypes": ["개념 미이해", "분모/분자 혼동"],
  "recent4wResponseJson": {
    "summary": "시각 자료에는 잘 반응하지만 문장제 조건을 놓침"
  },
  "emotionalStateNote": "틀리면 금방 자신감이 낮아짐",
  "effectiveExplanationStyles": ["visual_example", "short_steps"],
  "frequentBlockingUnits": ["분수", "문장제"],
  "guardianCooperationStatus": "보통",
  "nextSessionCautions": ["첫 문제는 쉬운 성공 경험으로 시작"],
  "teacherVerifiedAt": null,
  "status": "active"
}
```

## 5. 조회성 API 우선순위

프론트/백엔드가 먼저 맞출 API는 아래다.

```text
GET /api/context/me
GET /api/teacher/students
GET /api/teacher/students/:studentId
GET /api/public-data/schools/:schoolId/context
GET /api/student/missions/today
GET /api/student/missions/:contentId
```

`/api/context/me`는 실제 로그인 구현이 아니라 데모 seed 사용자를 확인하는 조회성 endpoint다.
초기에는 `DEMO_TEACHER_EMAIL` 또는 demo token 기준으로 현재 사용자/조직을 반환하면 된다.

예시:

```json
{
  "user": "UserProfile",
  "organization": "Organization",
  "mode": "demo_seed"
}
```

## 6. 학생 미션 제품 규칙

- 학생 미션은 화면 기준 4단계다.
- 회고는 5단계가 아니라 4단계 이후 후속 활동이다.
- 1~3단계는 교사가 승인한 정적 템플릿 JSON을 렌더링한다.
- 4단계만 realtime 연습이다.
- 학생 플레이 중 1~3단계에서 AI가 새 분석이나 새 생성을 하면 안 된다.
- 학생에게 보이는 콘텐츠는 `published` 상태만 허용한다.
- 한 미션은 대표 이미지 1장과 단계별 이미지 4장을 가진다.
- 한 미션은 대표 오디오 1개와 단계별 오디오 4개를 가진다.
- 프론트는 각 단계 화면 진입 시 이미지와 오디오를 먼저 resolve/load한다.
- 질문, 선택지, 피드백은 이미지 안 텍스트가 아니라 UI 텍스트로 보여준다.
- 이미지는 상황 설명, 관계, 대상, 감정, 마스코트 반응을 보여주는 장면 asset이다.
- 문제 문항, 선택지, 카드 텍스트, 빈칸 문장, 힌트, 정답 피드백은 AI가 `templateJson` 필드로 반환한다.
- OpenAI key, realtime provider secret, prompt 원문은 프론트로 내려보내지 않는다.

## 7. 두 가지 콘텐츠 트랙

학생 유형에 따라 같은 4단계 구조를 다른 화면 이름과 기능으로 사용한다.

| contentType | 대상 | 목적 |
| --- | --- | --- |
| `life_support` | 일상생활 도움이 더 필요한 학생 | 실제 생활 상황에서 단서 찾기, 행동 선택, 도움 요청을 연습 |
| `learning_focus` | 학습 보완이 주된 학생 | 개념 이미지, 기본 문제, 응용 문제, 말로 설명하기를 연습 |

프론트는 두 트랙을 완전히 다른 앱처럼 만들지 않는다.
같은 stage shell을 쓰되 `stageRole`, `templateType`, `studentTitle`, `templateJson`으로 화면을 다르게 렌더링한다.

## 8. 4단계 기능 정의

### 8.1 생활지원형

| step | 학생 화면 이름 | stageRole | 기능 목표 | 결과 데이터 |
| --- | --- | --- | --- | --- |
| 1 | 상황 만나기 | `scenario_intro` | 상황 이미지와 짧은 이야기로 오늘 미션을 이해 | 시작/조회 이벤트 |
| 2 | 단서 찾기 | `clue_identification` | 상황 속 중요한 정보, 위치, 조건을 고름 | 선택/핫스팟/매칭 결과 |
| 3 | 행동 고르기 | `action_selection` | 지금 해야 할 행동이나 순서를 선택 | 정답 여부, 다음 행동 이해 |
| 4 | 한 번 해보기 | `realtime_practice` | AI 역할과 실제 상황을 짧게 연습 | realtime session, 루브릭 요약 |

### 8.2 학습집중형

| step | 학생 화면 이름 | stageRole | 기능 목표 | 결과 데이터 |
| --- | --- | --- | --- | --- |
| 1 | 개념 열기 | `concept_intro` | 이미지와 짧은 설명으로 개념 앵커를 잡음 | 시작/조회 이벤트 |
| 2 | 문제 1 | `basic_problem` | 성공 가능한 기본 문제로 핵심 개념을 확인 | 정답 여부, 피드백 |
| 3 | 문제 2 | `applied_problem` | 헷갈리는 답, 응용 상황, 빈칸 등으로 한 번 더 적용 | 오답 패턴, 교정 포인트 |
| 4 | AI에게 말해보기 | `realtime_practice` | 상황 이미지와 AI 질문을 보고 말/텍스트로 설명 | realtime session, 루브릭 요약 |

## 9. 단계별 기능 요구사항

### 9.1 Step 1: 상황/개념 열기

프론트 기능:

- 대표 또는 1단계 이미지를 크게 보여준다.
- 오늘 미션 목표를 한 문장으로 보여준다.
- 학생이 해야 할 첫 행동을 짧게 보여준다.
- 정답 판정은 하지 않는다.

백엔드 제공:

- `studentTitle`
- `studentInstruction`
- `templateJson.imageAssetId`
- `templateJson.storyText` 또는 `templateJson.shortExplanation`
- `templateJson.missionText`

허용 템플릿:

```text
life_support: scenario_intro
learning_focus: concept_intro
```

### 9.2 Step 2: 핵심 확인

프론트 기능:

- 단서 선택, 이미지 3지선다 퀴즈, 카드 매칭, 순서 배열, 빈칸 등 하나의 짧은 상호작용을 제공한다.
- 선택지는 2~3개를 기본으로 한다.
- 제출 후 즉시 피드백을 보여준다.
- 정답/오답 이벤트를 서버에 보낸다.

백엔드 제공:

- `templateType`
- `templateJson.question`
- `templateJson.choices` 또는 `templateJson.hotspots` 또는 `templateJson.leftCards/rightCards` 또는 `templateJson.cards`
- `templateJson.answer` 또는 `templateJson.acceptedAnswers`
- `templateJson.correctFeedback`
- `templateJson.wrongFeedback`

허용 템플릿:

```text
life_support: scene_observation, highlight_clue, image_quiz, card_match
learning_focus: image_quiz, card_match, sequence_ordering, blank_fill, scene_question, clue_question, partition_picker
```

### 9.3 Step 3: 적용/결정

프론트 기능:

- Step 2에서 확인한 것을 상황에 적용하게 한다.
- 생활지원형은 행동 선택 또는 순서 배열이 중심이다.
- 학습집중형은 응용 문제, 오답 비교, 친구 도와주기, 설명 선택이 중심이다.
- 제출 후 교정 피드백을 보여준다.

백엔드 제공:

- `templateType`
- `templateJson.scenario` 또는 `templateJson.question`
- `templateJson.choices`, `templateJson.cards`, `templateJson.answerOrder`
- `templateJson.correctFeedback`
- `templateJson.wrongFeedback`
- 필요 시 `templateJson.repairText`

허용 템플릿:

```text
life_support: image_quiz, card_match, sequence_ordering, action_choice, decision_card
learning_focus: image_quiz, card_match, sequence_ordering, blank_fill, applied_question, mini_simulation, explanation_choice, wrong_explanation_fix
```

2~3단계 랜덤 템플릿 후보의 공통 풀은 아래 4개다.

```text
image_quiz: 이미지 + 3지선다 퀴즈
card_match: 왼쪽/오른쪽 카드 연결
sequence_ordering: 카드 순서 배열
blank_fill: 빈칸 채우기
```

오케스트레이터는 이 후보 중 학생 유형, 최근 반응, 교사 고정 옵션에 따라 하나를 선택한다.
프론트는 `templateType`과 `templateJson`만 보고 해당 렌더러를 fetch/render한다.

### 9.4 Step 4: realtime 연습

프론트 기능:

- 4단계 이미지를 보여준다.
- `realtime-session`을 생성한 뒤 음성 또는 텍스트 연습 UI로 들어간다.
- 학생이 볼 수 있는 정보만 노출한다.
- provider key, system prompt, 전체 루브릭 원문은 노출하지 않는다.
- 완료 후 후속 회고 UI를 보여준다.

백엔드 제공:

- `realtimeSpec.practiceTitle`
- `realtimeSpec.situationText`
- `realtimeSpec.openingLine`
- `realtimeSpec.maxTurns`
- `realtimeSpec.maxDurationSec`
- `practiceSpec.imageAssetUrl`
- session 생성 시 `clientSecret`

허용 템플릿:

```text
life_support: realtime_roleplay
learning_focus: realtime_teach_back
```

서버 검증:

```text
content.status == published
stage.step == 4
stage.realtimeSpec exists
student has access
attempt exists
```

## 10. 회고는 stage가 아니다

회고는 `post_practice_reflection` 이벤트다.
프론트에서는 4단계 완료 후 별도 하단 카드나 완료 화면으로 보여준다.

백엔드 저장:

```json
{
  "attemptId": "attempt_uuid",
  "reflectionChoice": "조금 헷갈렸어요",
  "shortText": "아래 숫자가 전체인 게 헷갈렸어요"
}
```

## 11. MissionContent 최소 스키마

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

프론트 필수 검증:

```text
totalSteps === 4
stages.length === 4
stages step list === [1, 2, 3, 4]
assets has hero, stage_1, stage_2, stage_3, stage_4_realtime
```

## 12. ContentStage 최소 스키마

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

규칙:

- `step`과 `sortOrder`는 1~4다.
- `step === 4`이면 `templateType`은 realtime 계열이어야 한다.
- `step === 4`이면 `realtimeSpec`이 null이면 안 된다.
- `step !== 4`이면 `realtimeSpec`은 null이다.

## 13. ContentAsset 최소 스키마

```json
{
  "id": "asset_content_fraction_001_stage_2",
  "missionContentId": "content_fraction_001",
  "stageId": "stage_fraction_2",
  "assetRole": "stage_2",
  "assetType": "image",
  "provider": "openai",
  "model": "gpt-image-2",
  "promptJson": {
    "visualRole": "stage_2",
    "textRenderingPolicy": "scene_only_no_problem_text",
    "forbiddenInlineText": ["문제 문장", "선택지", "정답", "힌트", "긴 설명"]
  },
  "storageUrl": "/examples/generated/fraction-mission/fraction-pizza.png",
  "previewUrl": "/examples/generated/fraction-mission/fraction-pizza.png",
  "qaStatus": "passed",
  "approvalStatus": "approved"
}
```

오디오 asset 예시:

```json
{
  "id": "asset_content_fraction_001_stage_2_audio",
  "missionContentId": "content_fraction_001",
  "stageId": "stage_fraction_2",
  "assetRole": "stage_2",
  "assetType": "audio",
  "provider": "elevenlabs",
  "model": "elevenlabs-tts",
  "sourceText": "전체 조각 수를 먼저 세어보세요.",
  "storageUrl": "/examples/generated/fraction-mission/audio/stage-2.mp3",
  "previewUrl": "/examples/generated/fraction-mission/audio/stage-2.mp3",
  "qaStatus": "passed",
  "approvalStatus": "approved"
}
```

asset role:

```text
hero
stage_1
stage_2
stage_3
stage_4_realtime
```

각 role은 `image` asset과 `audio` asset을 하나씩 가져야 한다.
`stage_4_realtime`의 audio는 realtime 시작 전 상황 안내용이며, 실시간 대화는 realtime session에서 처리한다.

## 14. RealtimePracticeSpec 최소 스키마

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

프론트 노출 가능:

```text
practiceTitle
situationText
openingLine
maxTurns
maxDurationSec
imageAssetUrl
```

프론트 노출 금지:

```text
provider key
system prompt
전체 forbidden/prompt 원문
학생 진단 라벨
```

## 15. 공통 enum

### contentType

```text
life_support
learning_focus
```

### mission status

```text
draft
generating
teacher_review
revision_requested
approved
published
archived
```

### stageRole

```text
scenario_intro
clue_identification
action_selection
concept_intro
basic_problem
applied_problem
realtime_practice
```

### templateType

```text
scenario_intro
scene_observation
highlight_clue
card_match
action_choice
sequence_ordering
decision_card
image_quiz
concept_intro
scene_question
clue_question
blank_fill
partition_picker
applied_question
mini_simulation
explanation_choice
wrong_explanation_fix
realtime_roleplay
realtime_teach_back
```

## 16. API envelope

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

## 17. 프론트 agent가 먼저 확인할 질문

프론트 agent는 API 연결 전에 아래를 먼저 확인한다.

```text
1. 현재 화면이 4단계 구조를 전제로 되어 있는가?
2. 회고가 5단계처럼 렌더링되고 있지 않은가?
3. life_support와 learning_focus가 같은 stage shell에서 분기 가능한가?
4. stageRole/templateType 조합이 위 표와 맞는가?
5. 1~3단계가 정적 템플릿 JSON만으로 렌더링 가능한가?
6. 4단계 realtime 진입 버튼이 stage.step === 4에서만 보이는가?
7. image asset role 5개를 화면에서 어디에 쓰는지 정해져 있는가?
8. mock 데이터가 이 문서의 최소 스키마를 만족하는가?
```

### Dashboard read-model additions

Teacher dashboard APIs include UI-facing read-model fields so the frontend does not invent student observations.
The source of student observation fields is `students.profile_json.dashboard`; the API may expose the same values on read models for UI convenience.

StudentProfile.profileJson stores:

```json
{
  "dashboard": {
    "attendanceRate": 95,
    "strengths": ["그림이나 조각 모델을 보면 전체와 부분을 더 쉽게 이해해요."],
    "weaknesses": ["문제 설명이 길면 중요한 조건을 놓칠 수 있어요."]
  }
}
```

StudentProfile and StudentListItem may expose:

```json
{
  "attendanceRate": 95,
  "strengths": ["그림이나 조각 모델을 보면 전체와 부분을 더 쉽게 이해해요."],
  "weaknesses": ["문제 설명이 길면 중요한 조건을 놓칠 수 있어요."]
}
```

SupportCaseSummary and StudentListItem may include:

```json
{
  "dashboardStage": "initial_review | material_generation | material_review | learning | feedback",
  "supportStrategy": "그림 자료와 짧은 단계 설명으로 반복 확인"
}
```

`latestContentStatus: "none"` and `dashboardStage: "initial_review"` means the dashboard should show 초기 확인, not 학습 중.
