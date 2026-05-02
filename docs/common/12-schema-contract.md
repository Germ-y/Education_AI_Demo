# 단계별 기능 및 스키마 계약

이 문서는 프론트/백엔드가 기능을 시작하기 전에 먼저 맞춰야 하는 공통 계약이다.
REST API endpoint를 먼저 외우는 문서가 아니라, 학생 미션 1~4단계가 각각 어떤 기능을 가져야 하는지 온보딩하면서 합의하기 위한 기준이다.

endpoint 상세는 [08-rest-api-spec.md](08-rest-api-spec.md)를 보되, field와 단계 의미는 이 문서를 우선 기준으로 한다.

## 1. 먼저 고정할 제품 규칙

- 학생 미션은 화면 기준 4단계다.
- 회고는 5단계가 아니라 4단계 이후 후속 활동이다.
- 1~3단계는 교사가 승인한 정적 템플릿 JSON을 렌더링한다.
- 4단계만 realtime 연습이다.
- 학생 플레이 중 1~3단계에서 AI가 새 분석이나 새 생성을 하면 안 된다.
- 학생에게 보이는 콘텐츠는 `published` 상태만 허용한다.
- 한 미션은 대표 이미지 1장과 단계별 이미지 4장을 가진다.
- 질문, 선택지, 피드백은 이미지 안 텍스트가 아니라 UI 텍스트로 보여준다.
- OpenAI key, realtime provider secret, prompt 원문은 프론트로 내려보내지 않는다.

## 2. 두 가지 콘텐츠 트랙

학생 유형에 따라 같은 4단계 구조를 다른 화면 이름과 기능으로 사용한다.

| contentType | 대상 | 목적 |
| --- | --- | --- |
| `life_support` | 일상생활 도움이 더 필요한 학생 | 실제 생활 상황에서 단서 찾기, 행동 선택, 도움 요청을 연습 |
| `learning_focus` | 학습 보완이 주된 학생 | 개념 이미지, 기본 문제, 응용 문제, 말로 설명하기를 연습 |

프론트는 두 트랙을 완전히 다른 앱처럼 만들지 않는다.
같은 stage shell을 쓰되 `stageRole`, `templateType`, `studentTitle`, `templateJson`으로 화면을 다르게 렌더링한다.

## 3. 4단계 기능 정의

### 3.1 생활지원형

| step | 학생 화면 이름 | stageRole | 기능 목표 | 결과 데이터 |
| --- | --- | --- | --- | --- |
| 1 | 상황 만나기 | `scenario_intro` | 상황 이미지와 짧은 이야기로 오늘 미션을 이해 | 시작/조회 이벤트 |
| 2 | 단서 찾기 | `clue_identification` | 상황 속 중요한 정보, 위치, 조건을 고름 | 선택/핫스팟/매칭 결과 |
| 3 | 행동 고르기 | `action_selection` | 지금 해야 할 행동이나 순서를 선택 | 정답 여부, 다음 행동 이해 |
| 4 | 한 번 해보기 | `realtime_practice` | AI 역할과 실제 상황을 짧게 연습 | realtime session, 루브릭 요약 |

### 3.2 학습집중형

| step | 학생 화면 이름 | stageRole | 기능 목표 | 결과 데이터 |
| --- | --- | --- | --- | --- |
| 1 | 개념 열기 | `concept_intro` | 이미지와 짧은 설명으로 개념 앵커를 잡음 | 시작/조회 이벤트 |
| 2 | 문제 1 | `basic_problem` | 성공 가능한 기본 문제로 핵심 개념을 확인 | 정답 여부, 피드백 |
| 3 | 문제 2 | `applied_problem` | 헷갈리는 답, 응용 상황, 빈칸 등으로 한 번 더 적용 | 오답 패턴, 교정 포인트 |
| 4 | AI에게 말해보기 | `realtime_practice` | 상황 이미지와 AI 질문을 보고 말/텍스트로 설명 | realtime session, 루브릭 요약 |

## 4. 단계별 기능 요구사항

### 4.1 Step 1: 상황/개념 열기

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

### 4.2 Step 2: 핵심 확인

프론트 기능:

- 단서 선택, 카드 매칭, 기본 선택형, 빈칸 등 하나의 짧은 상호작용을 제공한다.
- 선택지는 2~3개를 기본으로 한다.
- 제출 후 즉시 피드백을 보여준다.
- 정답/오답 이벤트를 서버에 보낸다.

백엔드 제공:

- `templateType`
- `templateJson.question`
- `templateJson.choices` 또는 `templateJson.hotspots` 또는 `templateJson.tiles`
- `templateJson.answer` 또는 `templateJson.acceptedAnswers`
- `templateJson.correctFeedback`
- `templateJson.wrongFeedback`

허용 템플릿:

```text
life_support: scene_observation, highlight_clue, card_match
learning_focus: scene_question, clue_question, blank_fill, partition_picker
```

### 4.3 Step 3: 적용/결정

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
life_support: action_choice, sequence_ordering, decision_card
learning_focus: applied_question, mini_simulation, card_match, sequence_ordering, explanation_choice, wrong_explanation_fix
```

### 4.4 Step 4: realtime 연습

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

## 5. 회고는 stage가 아니다

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

## 6. MissionContent 최소 스키마

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

## 7. ContentStage 최소 스키마

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

## 8. ContentAsset 최소 스키마

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

asset role:

```text
hero
stage_1
stage_2
stage_3
stage_4_realtime
```

## 9. RealtimePracticeSpec 최소 스키마

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

## 10. 공통 enum

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

## 11. API envelope

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

## 12. 프론트 agent가 먼저 확인할 질문

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
