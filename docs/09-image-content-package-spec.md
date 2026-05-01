# Image Content Package Spec

확인 기준일: 2026-05-02

## 1. 결론

AI가 만드는 것은 이미지 한 장이 아니라 `MissionContent`에 연결되는 이미지 패키지다.

한 미션에는 아래 5개 이미지 슬롯이 있다.

| 슬롯 | 용도 | 학생 화면 |
| --- | --- | --- |
| `hero` | 미션 대표 이미지 | 오늘의 미션 카드, 교사 검토 썸네일 |
| `stage_1` | 상황/개념 진입 | 1단계 |
| `stage_2` | 단서 찾기/기본 문제 | 2단계 |
| `stage_3` | 행동 선택/응용 문제 | 3단계 |
| `stage_4_realtime` | 실시간 연습 상황 이미지 | 4단계 realtime |

영상은 만들지 않는다. 이미지, UI 텍스트, 템플릿 인터랙션, realtime 대화만으로 콘텐츠 경험을 만든다.

## 2. 모델 정책

```text
provider: openai
model: gpt-image-2
usage: server-side generation job
storage: object storage + content_assets table
teacher exposure: preview only after safety/OCR QA
student exposure: approved content only
```

이미지에는 긴 문장, 정답 문장, 복잡한 수식을 넣지 않는다. 텍스트와 선택지는 앱 UI가 렌더링한다.

## 3. 이미지 브리프 스키마

```json
{
  "assetRole": "stage_2",
  "contentType": "learning_focus",
  "studentFit": {
    "readingLoad": "low",
    "visualStyle": "friendly_illustration",
    "avoid": ["dark_mood", "busy_background", "tiny_text"]
  },
  "learningTarget": {
    "subject": "math",
    "unit": "fractions",
    "skill": "전체와 부분 관계를 분수로 표현"
  },
  "visualGoal": "전체 4조각 중 빛나는 1조각을 한눈에 구분하게 한다.",
  "sceneDescription": "탐험 지도 위에 같은 크기로 4등분된 피자가 있고, 한 조각만 따뜻한 빛으로 강조된다.",
  "composition": "main object centered, clear 4 equal sections, one highlighted section, no text labels",
  "mustShow": ["4 equal parts", "1 highlighted part", "friendly star mascot nearby"],
  "mustAvoid": ["written fraction", "Korean text inside image", "unequal slices", "extra highlighted parts"],
  "ocrRequired": false,
  "prompt": "",
  "negativePrompt": ""
}
```

## 4. 프롬프트 생성 원칙

프롬프트는 바로 이미지 모델에 던지는 문장이 아니라 아래 절차로 만든다.

```text
ContentBrief
→ ImageBrief
→ PromptSafetyCheck
→ PromptBuilder
→ gpt-image-2 generation
→ Visual/OCR QA
→ Teacher Preview
```

PromptBuilder는 아래 구조를 따른다.

```text
1. visual style
2. subject and scene
3. educational focus
4. composition constraints
5. student accessibility constraints
6. text/OCR constraints
7. quality bar
8. avoid list
```

## 5. 고품질 프롬프트 템플릿

### 5.1 학습집중형 분수 예시

```text
Create a polished educational illustration for a Korean middle-school learning app.
Scene: a warm adventure-map tabletop with a round pizza divided into exactly four equal slices.
One slice is softly glowing, clearly separated as the chosen part, while the full pizza remains visible.
Add a small cheerful star mascot near the corner, reacting with curiosity, not blocking the pizza.
Educational focus: make the relationship "one selected part out of four equal whole parts" visually obvious without writing any fraction.
Composition: clean 16:9 card layout, centered pizza, high contrast between the selected slice and the rest, enough empty space for UI text overlay outside the image.
Accessibility: simple shapes, low visual clutter, friendly colors, no scary mood, no tiny details required to understand the answer.
Do not include Korean text, English text, numbers, equations, labels, watermarks, hands, or extra highlighted slices.
High-quality app illustration, crisp edges, soft lighting, consistent perspective.
```

### 5.2 생활지원형 버스 예시

```text
Create a friendly scenario illustration for a life-skills learning mission.
Scene: a student standing safely at a neighborhood bus stop, looking at a blue bus approaching on a clear street.
Show three important visual clues: the bus stop sign, the bus front display area, and the destination direction toward a small community learning center in the distance.
Educational focus: the student should be able to notice where to check route information and what to do next.
Composition: wide 16:9 layout, bus and stop sign visible, student in foreground, learning center in background, uncluttered environment.
Accessibility: calm daytime colors, clear landmarks, no crowded traffic, no unsafe situation, no confusing extra buses.
Do not include readable Korean text, real route numbers, personal names, brand logos, or dense signage.
High-quality app illustration, clear shapes, warm and reassuring mood.
```

## 6. OCR/Visual QA

OCR QA가 필요한 경우:

- 버스 번호, 시간, 표지판, 숫자 카드가 이미지 안에 들어간다.
- 교사가 이미지 자체에서 특정 숫자/라벨을 확인해야 한다.
- 이미지가 문제의 단서 역할을 하고, 그 단서가 문자/숫자로 표현된다.

OCR QA가 필요 없는 경우:

- 정답, 숫자, 선택지, 설명이 모두 UI 텍스트로 분리된다.
- 이미지는 장면/관계/행동 맥락만 제공한다.

검수 결과 예:

```json
{
  "assetId": "asset_001",
  "ocrRequired": true,
  "ocrPassed": false,
  "detectedText": ["38", "B8"],
  "expectedText": ["3"],
  "visualIssues": ["bus number not readable"],
  "action": "regenerate"
}
```

## 7. Asset 상태

| 상태 | 의미 |
| --- | --- |
| `draft` | 생성 요청 전 또는 브리프만 있는 상태 |
| `generating` | 이미지 생성 중 |
| `generated` | 이미지 생성 완료 |
| `qa_passed` | 자동 검수 통과 |
| `qa_failed` | 자동 검수 실패 |
| `teacher_review` | 교사 미리보기 대기 |
| `approved` | 콘텐츠 배포 가능 |
| `rejected` | 재생성 또는 삭제 필요 |

## 8. 저장 필드

```json
{
  "id": "asset_001",
  "missionContentId": "content_001",
  "stageId": "stage_002",
  "assetRole": "stage_2",
  "provider": "openai",
  "model": "gpt-image-2",
  "promptVersion": "image_prompt_v1",
  "promptJson": {},
  "storageUrl": "s3://eduyj-assets/content_001/stage_2.png",
  "publicPreviewUrl": "https://cdn.example.com/content_001/stage_2.png",
  "ocrRequired": false,
  "qaStatus": "qa_passed",
  "teacherApprovalStatus": "pending"
}
```

## 9. Realtime Stage Image

4단계 이미지는 정답을 맞히기 위한 그림이 아니라 대화를 열기 위한 상황 이미지다.

생활지원형:

```text
학생이 실제로 말해야 하는 상황을 보여준다.
예: 정류장에서 도움 요청하기, 센터 입구에서 인사하기, 준비물 확인하기.
```

학습집중형:

```text
학생이 개념을 자기 말로 설명할 장면을 보여준다.
예: 별이가 피자 조각을 보고 "왜 1/4이야?"라고 궁금해하는 상황.
```

이미지는 대화 맥락만 제공하고, realtime의 질문/피드백은 `RealtimePracticeSpec`이 담당한다.
