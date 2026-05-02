# AI 콘텐츠 템플릿 명세

## 1. 핵심 원칙

AI는 학생에게 보여줄 콘텐츠를 자유 HTML/JS로 만들지 않는다.

AI는 아래와 같은 구조화된 템플릿 스펙을 생성하고, 프론트는 허용된 템플릿만 렌더링한다.

```text
AI 생성 JSON
→ 템플릿 스키마 검증
→ 교사 검토
→ 학생 화면 렌더링
```

학생이 플레이하는 동안 1~3단계는 AI가 새로 분석하거나 후처리로 스테이지를 바꾸지 않는다.

단, 4단계는 `Realtime Practice`로 분리한다. 이 단계는 자유 생성 콘텐츠가 아니라 교사가 승인한 `RealtimePracticeSpec` 안에서만 AI가 대화와 짧은 피드백을 제공한다.

## 1.1 사전 TTS 원칙

ElevenLabs는 4단계 realtime 대화에 붙이지 않는다.

ElevenLabs는 교사가 승인한 정적 콘텐츠의 안내 음성을 **사전 생성**하는 선택 provider다.

```text
AI 콘텐츠 JSON 생성
→ 이미지 생성
→ hero + 1~3단계 narrationText 확정
→ ElevenLabs TTS MP3 사전 생성
→ 교사 검토/승인
→ 학생 화면에서 audio asset 로드
```

적용 범위:

| 위치 | 용도 | provider |
| --- | --- | --- |
| `hero` | 대표 시나리오/오늘 미션 도입 음성 | ElevenLabs optional |
| `stage_1` | 상황/개념 설명 음성 | ElevenLabs optional |
| `stage_2` | 문제 안내 음성 | ElevenLabs optional |
| `stage_3` | 응용/심화 안내 음성 | ElevenLabs optional |
| `stage_4_realtime` | 실시간 대화 | ElevenLabs 사용 안 함 |

프론트는 `assetType: audio_optional` asset이 있으면 재생 버튼을 보여주고, 없으면 텍스트만 보여준다. 오디오가 없다고 seed 이미지나 다른 음성으로 조용히 대체하지 않는다.

## 2. 공통 MissionContent 스키마

```json
{
  "id": "content_001",
  "studentId": "student_001",
  "caseId": "case_001",
  "contentType": "learning_focus",
  "title": "분수 탐험: 빛나는 한 조각",
  "status": "teacher_review",
  "totalSteps": 4,
  "rewardLabel": "분수 탐험 토큰",
  "theme": {
    "accent": "#27ae60",
    "accentSoft": "#e8f8ee",
    "highlight": "#fff3c4"
  },
  "stages": []
}
```

오디오 asset은 이미지 asset과 같은 `assetRole`을 공유한다. 구분은 `assetType`으로 한다.

```json
{
  "id": "asset_content_001_stage_1_audio",
  "missionContentId": "content_001",
  "stageId": "stage_001",
  "assetRole": "stage_1",
  "assetType": "audio_optional",
  "provider": "elevenlabs",
  "model": "elevenlabs-tts",
  "sourceText": "피자 지도를 보며 전체와 부분을 확인해요.",
  "storageUrl": "/generated/audio/content_001/stage_1.mp3",
  "previewUrl": "/generated/audio/content_001/stage_1.mp3",
  "qaStatus": "passed",
  "approvalStatus": "approved"
}
```

## 3. 생활지원형 단계

| 단계 | 이름 | stageRole | 허용 템플릿 |
| --- | --- | --- | --- |
| 1 | 상황 만나기 | `scenario_intro` | `scenario_intro` |
| 2 | 단서 찾기 | `clue_identification` | `scene_observation`, `highlight_clue`, `image_quiz`, `card_match` |
| 3 | 행동 고르기 | `action_selection` | `image_quiz`, `card_match`, `sequence_ordering`, `action_choice`, `decision_card` |
| 4 | AI와 연습하기 | `realtime_practice` | `realtime_roleplay` |

## 4. 학습집중형 단계

| 단계 | 이름 | stageRole | 허용 템플릿 |
| --- | --- | --- | --- |
| 1 | 개념 열기 | `concept_intro` | `concept_intro` |
| 2 | 문제 1 | `basic_problem` | `image_quiz`, `card_match`, `sequence_ordering`, `blank_fill`, `scene_question`, `clue_question`, `partition_picker` |
| 3 | 문제 2 | `applied_problem` | `image_quiz`, `card_match`, `sequence_ordering`, `blank_fill`, `applied_question`, `mini_simulation`, `explanation_choice`, `wrong_explanation_fix` |
| 4 | AI에게 말해보기 | `realtime_practice` | `realtime_teach_back` |

학습집중형 4단계는 개념 정리가 아니라 **상황 이미지와 AI 대화로 설명을 직접 연습하는 realtime 단계**다. AI는 교사가 승인한 역할/루브릭 안에서만 피드백한다.

회고는 4단계 실시간 연습 종료 후 `post_practice_reflection` 이벤트로 수집한다. 별도 스테이지로 카운트하지 않는다.

2~3단계는 오케스트레이터가 허용 목록 안에서 템플릿을 선택한다.
프론트는 `templateType`별 렌더러를 준비하고, 콘텐츠 fetch 결과의 `templateJson`을 그대로 사용한다.

공통 랜덤 후보:

| templateType | 화면 성격 | 핵심 데이터 |
| --- | --- | --- |
| `image_quiz` | 이미지 + 3지선다 퀴즈 | `imageAssetId`, `choices[3]`, `answer` |
| `card_match` | 카드 매칭 | `leftCards`, `rightCards`, `matches` |
| `sequence_ordering` | 순서 배열 | `cards`, `answerOrder` |
| `blank_fill` | 빈칸 채우기 | `tiles`, `acceptedAnswers` 또는 `answers` |

## 5. 템플릿 목록

### 5.1 `scenario_intro`

목적:

```text
상황 또는 개념에 진입할 수 있도록 이미지와 짧은 이야기를 제시한다.
```

필드:

```json
{
  "templateType": "scenario_intro",
  "imageAssetId": "asset_001",
  "storyText": "수민이가 버스를 타고 센터에 가야 해요.",
  "missionText": "중요한 단서를 찾아서 안전하게 센터에 가요."
}
```

### 5.2 `scene_observation`

목적:

```text
이미지 속 중요한 단서를 찾게 한다.
```

필드:

```json
{
  "templateType": "scene_observation",
  "question": "버스 번호는 어디에 있나요?",
  "hotspots": [
    { "id": "bus_number", "label": "버스 번호", "x": 62, "y": 32, "correct": true },
    { "id": "ad_board", "label": "광고판", "x": 20, "y": 40, "correct": false }
  ],
  "correctFeedback": "좋아요. 버스 번호를 먼저 확인했어요.",
  "wrongFeedback": "광고판보다 버스 번호 표시를 찾아볼까요?"
}
```

### 5.3 `highlight_clue`

목적:

```text
문장, 시간표, 안내문에서 핵심 조건을 고르게 한다.
```

필드:

```json
{
  "templateType": "highlight_clue",
  "sourceText": "3번 버스는 오후 2시 10분에 센터 앞에 도착해요.",
  "targetClues": ["3번 버스", "오후 2시 10분", "센터 앞"],
  "question": "중요한 단서를 눌러보세요."
}
```

### 5.4 `action_choice`

목적:

```text
상황에서 지금 해야 할 행동을 고르게 한다.
```

필드:

```json
{
  "templateType": "action_choice",
  "scenario": "버스가 5분 뒤에 와요.",
  "question": "지금 먼저 해야 할 일은 무엇인가요?",
  "choices": [
    { "id": "check_number", "text": "버스 번호를 확인한다", "isCorrect": true },
    { "id": "any_bus", "text": "아무 버스나 탄다", "isCorrect": false }
  ]
}
```

### 5.5 `image_quiz`

목적:

```text
시나리오/개념 이미지를 보고 3개 선택지 중 하나를 고르게 한다.
```

필드:

```json
{
  "templateType": "image_quiz",
  "imageAssetId": "asset_content_001_stage_2",
  "question": "빛나는 조각은 전체 중 몇 개인가요?",
  "choices": [
    { "id": "a", "text": "1개" },
    { "id": "b", "text": "2개" },
    { "id": "c", "text": "4개" }
  ],
  "answer": "a",
  "correctFeedback": "좋아요. 빛나는 조각은 1개예요.",
  "wrongFeedback": "빛나는 부분만 다시 세어볼까요?"
}
```

제약:

```text
choices는 정확히 3개다.
answer는 choices의 id 중 하나다.
이미지는 content_assets의 stage_2 또는 stage_3 asset을 참조한다.
```

### 5.6 `card_match`

목적:

```text
왼쪽 카드와 오른쪽 카드를 연결해 개념-예시, 상황-행동, 단서-의미 관계를 확인한다.
```

필드:

```json
{
  "templateType": "card_match",
  "question": "서로 맞는 카드를 연결해보세요.",
  "leftCards": [
    { "id": "left_part", "text": "전체 4개 중 1개" },
    { "id": "left_feeling", "text": "걱정돼요" }
  ],
  "rightCards": [
    { "id": "right_fraction", "text": "1/4" },
    { "id": "right_help", "text": "도움 요청하기" }
  ],
  "matches": {
    "left_part": "right_fraction",
    "left_feeling": "right_help"
  },
  "correctFeedback": "좋아요. 서로 맞게 연결했어요.",
  "wrongFeedback": "왼쪽 카드가 어떤 뜻인지 다시 살펴볼까요?"
}
```

### 5.7 `sequence_ordering`

목적:

```text
행동 또는 풀이 순서를 배열하게 한다.
```

필드:

```json
{
  "templateType": "sequence_ordering",
  "question": "센터에 가는 순서를 맞춰보세요.",
  "cards": [
    { "id": "check_bus", "text": "버스 번호 확인" },
    { "id": "move_stop", "text": "정류장으로 이동" },
    { "id": "take_bus", "text": "버스 타기" }
  ],
  "answerOrder": ["check_bus", "move_stop", "take_bus"]
}
```

### 5.8 `roleplay_simulation`

목적:

```text
실제 상황처럼 말/행동을 선택하게 한다.
```

필드:

```json
{
  "templateType": "roleplay_simulation",
  "scene": "정류장에 왔는데 버스가 아직 안 왔어요.",
  "npcLine": "어떤 버스를 기다리고 있니?",
  "studentChoices": [
    { "id": "answer_route", "text": "3번 버스를 기다려요.", "isCorrect": true },
    { "id": "silent", "text": "아무 말도 하지 않아요.", "isCorrect": false }
  ]
}
```

### 5.9 `concept_intro`

목적:

```text
개념 설명과 시나리오 이미지를 함께 보여준다.
```

필드:

```json
{
  "templateType": "concept_intro",
  "imageAssetId": "asset_101",
  "conceptTitle": "분수",
  "shortExplanation": "분수는 전체 중 일부를 나타내는 방법이에요.",
  "missionText": "피자 지도에서 빛나는 한 조각을 찾아봐요."
}
```

### 5.10 `scene_question`

목적:

```text
시나리오 이미지 기반 기본 문제를 낸다.
```

필드:

```json
{
  "templateType": "scene_question",
  "question": "빛나는 구역은 몇 개인가요?",
  "choices": ["1구역", "2구역", "4구역"],
  "correctAnswer": "1구역"
}
```

### 5.11 `blank_fill`

목적:

```text
핵심 표현의 빈칸을 채우게 한다.
```

필드:

```json
{
  "templateType": "blank_fill",
  "sentence": "전체 4개 중 1개는 [A]/[B]이에요.",
  "blanks": ["A", "B"],
  "tiles": ["1", "2", "4"],
  "answers": {
    "A": "1",
    "B": "4"
  }
}
```

### 5.12 `partition_picker`

목적:

```text
도형/그림의 일부를 직접 선택하게 한다.
```

필드:

```json
{
  "templateType": "partition_picker",
  "visual": {
    "shape": "pizza_map",
    "totalParts": 4,
    "targetParts": 1
  },
  "instruction": "4조각 중 1조각을 눌러보세요.",
  "resultText": "선택한 조각은 1/4이에요."
}
```

### 5.13 `trap_finder`

목적:

```text
일부러 틀린 풀이/그림/친구 답에서 오류를 찾게 한다.
```

필드:

```json
{
  "templateType": "trap_finder",
  "setup": "민준이가 4구역 중 1구역을 보고 4/1이라고 했어요.",
  "question": "어디가 이상할까요?",
  "choices": [
    { "id": "swapped", "text": "전체 수와 고른 수의 자리가 바뀌었어요.", "isCorrect": true },
    { "id": "no_light", "text": "빛나는 구역이 없어요.", "isCorrect": false }
  ]
}
```

### 5.14 `wrong_answer_compare`

목적:

```text
정답과 헷갈리는 답을 나란히 비교한다.
```

필드:

```json
{
  "templateType": "wrong_answer_compare",
  "left": {
    "label": "친구의 답",
    "value": "4/1"
  },
  "right": {
    "label": "올바른 답",
    "value": "1/4"
  },
  "question": "왜 오른쪽이 맞을까요?",
  "choices": ["아래 숫자는 전체 수라서", "큰 숫자가 항상 위라서"]
}
```

### 5.15 `help_friend`

목적:

```text
가상의 친구를 도와주는 방식으로 개념을 설명하게 한다.
```

필드:

```json
{
  "templateType": "help_friend",
  "friendLine": "왜 4/1이 아니라 1/4이야?",
  "question": "친구에게 어떻게 알려줄까요?",
  "choices": [
    { "text": "전체 4개 중 고른 것이 1개라서 1/4이야.", "isCorrect": true },
    { "text": "그냥 외우면 돼.", "isCorrect": false }
  ]
}
```

### 5.16 `explanation_choice`

목적:

```text
가상 친구나 마스코트에게 들려줄 가장 좋은 설명을 고르게 한다.
```

필드:

```json
{
  "templateType": "explanation_choice",
  "friendName": "별이",
  "friendLine": "왜 아래 숫자가 4인지 모르겠어.",
  "question": "별이에게 어떤 설명을 해주면 좋을까요?",
  "choices": [
    {
      "id": "whole_count",
      "text": "아래 숫자는 전체가 몇 조각인지 알려줘. 전체가 4조각이라서 아래에 4를 써.",
      "isCorrect": true
    },
    {
      "id": "large_number",
      "text": "큰 숫자는 항상 아래에 쓰면 돼.",
      "isCorrect": false
    }
  ]
}
```

### 5.17 `wrong_explanation_fix`

목적:

```text
친구의 설명 중 틀린 부분을 고치게 한다.
```

필드:

```json
{
  "templateType": "wrong_explanation_fix",
  "wrongLine": "전체 4개 중 1개니까 4/1이라고 쓰면 돼.",
  "fixOptions": [
    {
      "id": "swap",
      "text": "고른 것은 위에, 전체는 아래에 써야 해.",
      "isCorrect": true
    },
    {
      "id": "same",
      "text": "전체와 고른 것을 같은 숫자로 써야 해.",
      "isCorrect": false
    }
  ],
  "fixedLine": "전체 4개 중 고른 것이 1개라서 1/4이에요."
}
```

### 5.18 `realtime_roleplay`

목적:

```text
생활지원형 학생이 상황 이미지 속 역할극을 AI와 실시간으로 연습하게 한다.
```

필드:

```json
{
  "templateType": "realtime_roleplay",
  "imageAssetId": "asset_bus_stop_001",
  "practiceTitle": "정류장에서 도움 요청하기",
  "situationText": "버스가 아직 오지 않았고, 어떤 버스를 타야 할지 헷갈려요.",
  "aiRole": "정류장 안내 직원",
  "openingLine": "어디로 가려고 하나요? 제가 도와줄게요.",
  "studentGoal": "3번 버스를 타고 센터에 가야 한다고 말하기",
  "rubric": [
    { "id": "state_destination", "label": "목적지를 말한다", "required": true },
    { "id": "ask_help", "label": "도움을 요청한다", "required": true },
    { "id": "confirm_next_action", "label": "다음 행동을 확인한다", "required": false }
  ],
  "allowedFeedback": [
    "좋아요. 어디로 가는지 말했어요.",
    "도움을 요청하는 말을 한 번 더 해볼까요?",
    "이제 어떤 버스를 타면 되는지 확인해봐요."
  ],
  "maxTurns": 6,
  "maxDurationSec": 120
}
```

### 5.19 `realtime_teach_back`

목적:

```text
학습집중형 학생이 상황 이미지와 별이의 질문을 보고 AI에게 말로 설명하며 실시간 피드백을 받는다.
```

필드:

```json
{
  "templateType": "realtime_teach_back",
  "imageAssetId": "asset_fraction_001",
  "practiceTitle": "별이에게 분수 설명하기",
  "situationText": "별이가 빛나는 피자 조각을 보고 왜 1/4인지 궁금해해요.",
  "aiRole": "별이",
  "openingLine": "왜 4/1이 아니라 1/4인지 알려줄래?",
  "studentGoal": "전체 4개 중 고른 것이 1개라서 1/4이라고 설명하기",
  "rubric": [
    { "id": "mention_whole", "label": "전체가 4개임을 말한다", "required": true },
    { "id": "mention_part", "label": "고른 것이 1개임을 말한다", "required": true },
    { "id": "connect_fraction", "label": "1/4로 연결한다", "required": true }
  ],
  "allowedFeedback": [
    "좋아요. 전체가 4개라는 말을 넣었어요.",
    "고른 조각이 몇 개인지도 말해볼까요?",
    "이제 1/4이라는 표현까지 이어서 말해봐요."
  ],
  "maxTurns": 6,
  "maxDurationSec": 120
}
```

### 5.20 `reflection_check`

목적:

```text
학생의 이해도, 감정, 도움 필요도를 수집한다.
```

필드:

```json
{
  "templateType": "reflection_check",
  "question": "오늘 미션은 어땠나요?",
  "choices": ["쉬웠어요", "조금 헷갈렸어요", "다시 보고 싶어요"],
  "freeTextEnabled": false
}
```

`reflection_check`는 이제 마지막 정규 스테이지가 아니라 실시간 연습 종료 후 짧게 붙는 후속 수집용 템플릿이다.

## 6. AI 생성 출력 예시

```json
{
  "contentType": "learning_focus",
  "title": "분수 탐험: 빛나는 한 조각",
  "stages": [
    {
      "step": 1,
      "studentLabel": "개념 열기",
      "stageRole": "concept_intro",
      "templateType": "concept_intro"
    },
    {
      "step": 2,
      "studentLabel": "문제 1",
      "stageRole": "basic_problem",
      "templateType": "scene_question"
    },
    {
      "step": 3,
      "studentLabel": "문제 2",
      "stageRole": "applied_problem",
      "templateType": "partition_picker"
    },
    {
      "step": 4,
      "studentLabel": "AI에게 말해보기",
      "stageRole": "realtime_practice",
      "templateType": "realtime_teach_back"
    }
  ]
}
```

## 7. 검수 규칙

AI가 만든 템플릿은 저장 전 아래를 통과해야 한다.

```text
templateType이 허용 목록에 있는가
단계별 stageRole과 templateType 조합이 맞는가
정답이 choices 안에 있는가
학생 유형에 맞는 문장 길이인가
민감 개인정보가 텍스트/프롬프트에 포함되지 않았는가
이미지 안에 넣을 텍스트를 과도하게 요구하지 않았는가
realtime 템플릿의 역할/첫 질문/루브릭/시간 제한이 승인 가능한가
교사 승인 전 published 상태가 아닌가
```
