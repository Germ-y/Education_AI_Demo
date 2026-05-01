# AI 백엔드 전체 설계

## 1. 설계 전제

프론트엔드는 현재 `학생 학습 길`, `스테이지 플레이`, `교사용 자료 생성/검토`, `학습 기록` 화면을 가지고 있다.

백엔드는 이 UI에 맞춰 다음 역할을 담당한다.

```text
학생/사례 데이터 수집
→ 학생 맥락 압축
→ AI 콘텐츠 전체 생성
→ 교사 검토/승인
→ 학생 플레이
→ 활동 이벤트 저장
→ 기록/메모리 업데이트
```

중요한 원칙:

```text
1~4단계에서는 AI가 새로 분석하거나 새 콘텐츠를 즉석 생성하지 않는다.
AI는 수업 전 콘텐츠 패키지와 마지막 실시간 연습 스펙을 생성한다.
학생 화면은 승인된 콘텐츠 JSON과 승인된 RealtimePracticeSpec만 실행한다.
```

즉, 기본 인터랙션은 **사전에 생성되고 승인된 미션 콘텐츠**를 플레이하는 구조다. 다만 각 유형의 마지막 단계는 예외적으로 `Realtime Practice`를 붙여 학생이 상황 이미지 안에서 AI와 짧게 대화하고 실시간 피드백을 받는다. 이때도 AI가 새 문제를 즉석 생성하는 것이 아니라, 교사가 승인한 상황/역할/루브릭 안에서만 대화한다.

## 2. 현재 프론트 기준 계약

프론트가 현재 기대하는 핵심 데이터는 아래와 같다.

```text
StudentProfile
SupportCase
CoachingScene
StageQuestion
ReviewItem
SessionRecord
```

백엔드는 이 구조를 실제 DB/API로 제공해야 한다.

### 2.1 학생 홈

학생 홈은 `CoachingScene`을 기반으로 학습 길을 렌더링한다.

필요 데이터:

```text
학생 표시 이름
학년
오늘 미션 제목
미션 설명
스테이지 목록
현재 진행 단계
보상 토큰
테마 색상
마스코트/비주얼 정보
```

### 2.2 학생 스테이지 화면

스테이지 화면은 `StageQuestion`을 기반으로 렌더링한다.

필요 데이터:

```text
step
kind
prompt
body
choices
correctAnswer
hint
correctFeedback
wrongFeedback
completionTitle
completionMessage
conceptCards
scenarioLines
visualActiveIndex
templateType
```

현재 프론트는 `concept`, `quiz`, `scenario`, `summary` 정도를 지원한다. 백엔드 설계에서는 이를 확장해 템플릿 기반 콘텐츠를 제공한다.

### 2.3 교사용 화면

교사용 화면은 학생 목록, 현재 사례, AI 자료 검토, 학습 기록을 본다.

필요 데이터:

```text
학생 목록
사례 상태
학생 메모리 카드
AI 생성 자료 목록
자료 검토 상태
스테이지별 미리보기
이미지 프롬프트
교사 승인/수정/반려 이력
수행 기록
AI 리뷰 요약
```

## 3. 학생 유형

기초학력거점지원센터 대상 학생은 일반적인 학습자보다 지원 요구가 넓다. 따라서 콘텐츠 생성은 두 유형으로 나눈다.

### 3.1 생활지원형

대상:

```text
경계선 지능
생활 상황 판단 어려움
실행 기능 어려움
정서 표현 어려움
도움 요청/순서 이해가 필요한 학생
```

목표:

```text
상황 이해
중요 단서 찾기
적절한 행동 선택
실제 상황 리허설
AI와 실시간 상황 연습
```

### 3.2 학습집중형

대상:

```text
기초 개념 부족
오답 패턴 반복
문장제/조건 해석 어려움
특정 단원 보완이 필요한 학생
```

목표:

```text
개념 진입
기본 문제 확인
응용/심화 문제 수행
가상 친구에게 설명하며 이해 확인
AI와 실시간 설명 연습
```

## 4. 콘텐츠 단계

### 4.1 생활지원형 5단계

| 단계 | 학생 화면 이름 | 기능 | 대표 템플릿 |
| --- | --- | --- | --- |
| 1 | 상황 만나기 | 일상 시나리오 이미지/짧은 이야기 | `scenario_intro` |
| 2 | 단서 찾기 | 상황 속 중요한 정보 고르기 | `scene_observation`, `highlight_clue`, `card_match` |
| 3 | 행동 고르기 | 지금 해야 할 행동 선택 | `action_choice`, `sequence_ordering`, `decision_card` |
| 4 | 한 번 해보기 | 실제 상황 재현, 롤플레잉 | `roleplay_simulation`, `dialogue_choice`, `mini_simulation` |
| 5 | AI와 연습하기 | 상황 이미지 기반 실시간 대화/피드백 | `realtime_roleplay` |

회고는 마지막 실시간 연습 종료 후 1~2개 버튼으로 수집한다. 콘텐츠 단계로는 카운트하지 않고 `post_practice_reflection` 이벤트로 저장한다.

예시:

```text
상황: 버스를 타고 센터에 가야 함
1. 정류장 장면을 보여줌
2. 버스 번호/도착 시간/목적지를 찾음
3. 지금 해야 할 행동을 고름
4. 선택형 롤플레잉으로 말/행동을 한번 연습
5. AI가 정류장 직원 역할을 하고 학생이 직접 말로 도움을 요청함
```

### 4.2 학습집중형 5단계

| 단계 | 학생 화면 이름 | 기능 | 대표 템플릿 |
| --- | --- | --- | --- |
| 1 | 개념 열기 | 개념 설명 + 시나리오 이미지 | `concept_intro` |
| 2 | 문제 1 | 시나리오 기반 기본 문제 | `scene_question`, `clue_question`, `blank_fill` |
| 3 | 문제 2 | 문제 1 응용 및 심화 문제 | `applied_question`, `mini_simulation`, `card_match` |
| 4 | 별이에게 설명하기 | 가상 시나리오 속 친구/마스코트에게 이유를 설명하기 | `help_friend`, `explanation_choice`, `wrong_explanation_fix` |
| 5 | AI에게 말해보기 | 상황 이미지 기반 실시간 설명/피드백 | `realtime_teach_back` |

4단계는 `생활에 적용`이나 `개념 정리`가 아니다. 학습집중형 4단계는 반복감을 줄이기 위해 **학생이 개념을 자기 말로 적용해보는 설명 단계**로 둔다. 단, 학생 플레이 중 AI가 새 분석을 하는 것이 아니라, AI가 사전에 생성한 설명 선택지/빈칸/오답 수정 템플릿을 학생이 수행한다.

5단계는 별도 예외다. 학생이 상황 이미지와 별이의 질문을 보고, AI에게 직접 말하거나 짧게 입력하며 설명을 연습한다. AI는 실시간으로 "좋아요", "전체가 몇 조각인지도 말해볼까요?"처럼 피드백하지만, 교사가 승인한 루브릭 밖의 새 문제를 만들지 않는다.

예시:

```text
1. 피자 지도와 분수 개념을 봄
2. 전체 4구역 중 빛나는 구역 수를 찾음
3. 4구역 중 1구역을 1/4로 표현함
4. 별이가 "왜 4/1이 아니라 1/4이야?"라고 묻고, 학생이 맞는 설명을 고름
5. 별이가 다시 묻고, 학생이 마이크/텍스트로 "전체 4개 중 1개라서 1/4이야"라고 설명함
```

## 5. AI 기능 범위

### 5.1 오케스트레이터

역할:

```text
학생 맥락을 읽고 오늘 콘텐츠 생성 계획을 결정한다.
```

입력:

```text
학생 프로필
학생 유형
사례 기록
메모리 카드
최근 회기 요약
최근 수행 결과
교사 코멘트
교육과정/공공데이터
```

출력:

```text
오늘 콘텐츠 유형
5단계 시나리오
단계별 템플릿 선택
마지막 실시간 연습 스펙
난이도
교사 검토 포인트
이미지/음성 생성 필요 여부
```

### 5.2 메모리 압축

역할:

```text
원본 기록을 다음 콘텐츠 생성에 필요한 학생 맥락으로 압축한다.
```

압축 결과:

```text
잘 반응한 설명 방식
반복 오답 패턴
생활 지원 필요 포인트
정서/자신감 상태
보호자 협조 상태
교사 검증 메모
```

### 5.3 콘텐츠 플래너

역할:

```text
생활지원형 또는 학습집중형 5단계 콘텐츠 골격을 만든다.
1~4단계는 정적 템플릿, 5단계는 승인형 RealtimePracticeSpec으로 만든다.
```

출력:

```text
MissionContent
StagePlan[]
TemplateSpec[]
TeacherReviewSummary
```

### 5.4 템플릿 선택기

역할:

```text
단계별로 허용된 템플릿 중 하나를 선택한다.
```

중요:

```text
랜덤처럼 보일 수 있지만 완전 랜덤이면 안 된다.
학생 유형, 문제 유형, 최근 반응에 따라 선택하되,
같은 조건에서 재현 가능한 seeded random을 사용한다.
```

예:

```text
생활지원형 2단계: scene_observation, highlight_clue, card_match 중 선택
학습집중형 4단계: help_friend, explanation_choice, wrong_explanation_fix 중 선택
각 유형 5단계: realtime_roleplay 또는 realtime_teach_back 고정
```

### 5.5 실시간 연습 세션

역할:

```text
마지막 단계에서 학생이 상황 이미지와 AI 대화로 실제 말하기/설명하기를 연습한다.
```

원칙:

```text
실시간 AI는 마지막 단계에서만 열린다.
교사가 승인한 RealtimePracticeSpec이 있어야 세션을 만들 수 있다.
AI는 승인된 역할, 첫 질문, 허용 피드백, 루브릭 안에서만 응답한다.
대화 결과는 즉시 다음 문제 생성에 쓰지 않고, 종료 후 리뷰 요약과 메모리 업데이트 후보로만 저장한다.
```

생활지원형:

```text
AI 역할: 정류장 직원, 센터 선생님, 또래 친구, 도서관 사서 등
학생 행동: 도움 요청하기, 순서 말하기, 감정 표현하기, 안전한 선택 말하기
피드백: 말문 열기, 핵심 단서 확인, 다음 행동 안내
```

학습집중형:

```text
AI 역할: 별이 또는 친구
학생 행동: 개념을 자기 말로 설명하기, 이유 말하기, 헷갈린 부분 다시 말하기
피드백: 핵심 단어 누락 확인, 오개념 짧게 바로잡기, 성공 표현 강화
```

### 5.6 이미지 생성

역할:

```text
각 미션의 시나리오 이미지, 개념 이미지, 역할극 이미지를 생성한다.
```

원칙:

```text
이미지 안에 긴 한글/숫자를 넣지 않는다.
이미지는 장면과 개념 앵커를 담당한다.
정답/선택지/설명은 UI 텍스트가 담당한다.
```

### 5.7 음성/마이크로 영상

MVP에서는 선택 기능이다.

권장 구조:

```text
image-2 장면 이미지
→ ElevenLabs 내레이션
→ Remotion/ffmpeg 기반 20~40초 마이크로 영상
→ 단계별 문제는 앱 UI에서 진행
```

영상 안에 문제를 모두 박지 않는다. 영상은 몰입을 담당하고, 문제/피드백은 앱이 담당한다.

### 5.8 자동 검수

교사 검토 전 시스템이 확인한다.

```text
정답/선택지 일치
금지 표현/민감 정보 노출 여부
학생 수준 대비 문장 길이
템플릿 스키마 유효성
이미지 프롬프트 안전성
교육과정 연결 여부
RealtimePracticeSpec의 역할/루브릭/시간 제한 유효성
```

### 5.9 리뷰 요약

학생 플레이 후 AI가 수행 결과를 요약한다.

단, 새 콘텐츠를 즉시 생성하지 않는다. 마지막 실시간 연습의 대화 기록은 루브릭 결과와 짧은 요약으로 압축해 다음 회기 근거로만 사용한다.

출력:

```text
완료 여부
오답 패턴
힌트 사용
체류시간
자기평가
다음 회기 생성에 반영할 메모리 업데이트
```

## 6. 백엔드 모듈

권장 초기 구조는 Node.js/TypeScript 기반이다. 프론트가 Next.js이므로 타입 공유와 JSON 스키마 관리가 쉽다.

```text
apps/api
packages/shared
packages/ai
packages/content-runtime
```

MVP에서는 단일 API 서버로 시작해도 된다.

### 6.1 도메인 모듈

```text
AuthModule
OrganizationModule
UserModule
StudentModule
CaseModule
MemoryModule
SessionRecordModule
ContentModule
TemplateModule
AssetModule
ApprovalModule
ActivityModule
ReviewModule
OrchestratorModule
AgentRunModule
PublicEducationDataModule
AuditModule
ConsentModule
```

### 6.2 인프라

권장:

```text
PostgreSQL: 핵심 데이터
Prisma: ORM
Redis + BullMQ: AI 생성/이미지 생성 작업 큐
S3 호환 스토리지: 생성 이미지/음성/영상
OpenAI: reasoning, content JSON, image-2
ElevenLabs: 음성 생성
Remotion/ffmpeg: 마이크로 영상 렌더링
```

## 7. 주요 데이터 모델

### 7.1 Student

```text
id
organization_id
name
display_name
grade
school
student_type: life_support | learning_focus
interests
strengths
created_at
updated_at
```

### 7.2 SupportCase

```text
id
student_id
case_type
primary_need
session_goal
support_strategy
risk_note
status
challenge_tags
plan_tags
```

### 7.3 MemoryCard

```text
id
student_id
effective_styles
avoid_styles
frequent_blocking_types
life_support_needs
emotional_profile
teacher_verified_notes
updated_by
updated_at
```

### 7.4 MissionContent

```text
id
student_id
case_id
orchestrator_run_id
content_type: life_support | learning_focus
title
description
status: draft | ai_checked | teacher_review | revision_requested | approved | published | completed | reviewed
total_steps
current_step
reward_label
reward_progress
theme_json
teacher_review_summary
created_at
updated_at
```

### 7.5 ContentStage

```text
id
mission_content_id
step
student_label
stage_role
template_type
kind
prompt
body
choices_json
correct_answer
hint
correct_feedback
wrong_feedback
completion_title
completion_message
scenario_lines_json
concept_cards_json
visual_spec_json
```

### 7.6 Asset

```text
id
mission_content_id
stage_id
asset_type: image | audio | video
purpose
prompt
model
status
storage_url
safety_checked
created_at
```

### 7.7 ActivityEvent

```text
id
student_id
mission_content_id
stage_id
event_type
payload_json
duration_ms
created_at
```

### 7.8 AgentRun

```text
id
orchestrator_run_id
agent_type
input_snapshot_json
output_json
model_name
status
error_message
created_at
```

## 8. API 설계

### 8.1 학생 화면

```text
GET  /api/student/me
GET  /api/student/me/today-content
GET  /api/student/contents/:contentId
POST /api/student/contents/:contentId/start
POST /api/student/contents/:contentId/events
POST /api/student/contents/:contentId/stages/:stageId/answer
POST /api/student/contents/:contentId/stages/:stageId/realtime-session
POST /api/student/realtime-sessions/:sessionId/events
POST /api/student/realtime-sessions/:sessionId/complete
POST /api/student/contents/:contentId/post-practice-reflection
POST /api/student/contents/:contentId/complete
```

### 8.2 교사 화면

```text
GET  /api/teacher/students
GET  /api/teacher/students/:studentId
GET  /api/teacher/students/:studentId/memory-card
GET  /api/teacher/students/:studentId/contents
POST /api/teacher/students/:studentId/contents/generate
GET  /api/teacher/contents/:contentId
PATCH /api/teacher/contents/:contentId/stages/:stageId
POST /api/teacher/contents/:contentId/request-revision
POST /api/teacher/contents/:contentId/approve
POST /api/teacher/contents/:contentId/publish
GET  /api/teacher/students/:studentId/session-records
POST /api/teacher/students/:studentId/session-records
```

### 8.3 AI 작업

외부에 직접 열지 않는 내부 API 또는 worker job으로 둔다.

```text
POST /internal/ai/orchestrate
POST /internal/ai/generate-content-plan
POST /internal/ai/generate-stage
POST /internal/ai/generate-image
POST /internal/ai/validate-content
POST /internal/ai/summarize-review
POST /internal/ai/update-memory
```

## 9. 콘텐츠 생성 작업 흐름

```text
1. 교사가 학생 선택 후 "AI 자료 생성" 클릭
2. OrchestratorRun 생성
3. Working Context 생성
4. 콘텐츠 유형 결정
5. 5단계 StagePlan 생성
6. 1~4단계 템플릿 선택 및 5단계 RealtimePracticeSpec 생성
7. StageQuestion/TemplateSpec 생성
8. 이미지/음성/영상 Asset job 생성
9. 자동 검수
10. teacher_review 상태 저장
11. 교사가 승인
12. published 상태로 학생에게 노출
```

## 10. 학생 플레이 작업 흐름

```text
1. 학생이 오늘의 학습 길 진입
2. published 콘텐츠 조회
3. 각 스테이지 플레이
4. 선택/클릭/힌트/체류시간 이벤트 저장
5. 마지막 단계에서 승인된 realtime session 생성
6. 상황 이미지 기반 AI 대화/실시간 피드백 수행
7. post-practice 회고 저장
8. 완료 시 content_attempt 종료
9. 리뷰 요약 job 실행
10. 메모리 업데이트 후보 생성
11. 교사 화면 기록/분석에 노출
```

## 11. 안전 원칙

```text
AI 생성물은 교사 승인 전 학생에게 노출하지 않는다.
학생 플레이 중 임의 JS 코드를 실행하지 않는다.
인터랙션은 허용된 템플릿 스키마만 렌더링한다.
마지막 realtime은 승인된 역할/루브릭/시간 제한 안에서만 실행한다.
민감 정보는 콘텐츠 텍스트와 이미지 프롬프트에 넣지 않는다.
AgentRun과 콘텐츠 버전은 모두 저장한다.
승인된 콘텐츠는 학생 수행 후 수정하지 않고 새 버전을 만든다.
```

## 12. MVP 범위

### 1차

```text
학생/사례 CRUD
메모리 카드 조회/수정
교사 회기 기록
AI 콘텐츠 생성
5단계 콘텐츠 JSON 저장
image-2 시나리오 이미지 생성
교사 승인/배포
학생 플레이 이벤트 저장
리뷰 요약
메모리 업데이트 후보 생성
```

### 2차

```text
ElevenLabs 음성 생성
마이크로 영상 렌더링
공공 교육데이터/학교 일정 연계
보호자 요약 카드
주간/월간 리포트
```

### 3차

```text
템플릿 고도화
시뮬레이션 위젯
개인별 반응 기반 템플릿 선택 최적화
센터별 대시보드
감사 로그/동의 관리 강화
```
