# EduYJ Goal Context

확인 기준일: 2026-05-06

이 문서는 Codex `/goal` 또는 새 작업자가 반드시 확인할 단일 기준 문서다. 이전에 나뉘어 있던 `HANDOFF.md`, `ISSUES.md`, `API.md`의 내용을 합쳤다.

## 작업 기준

- 작업 루트: `/Users/gimdonghyeon/Desktop/educationforyeongju-backend`
- 기준 브랜치: `dev`
- 프론트: `http://localhost:3000`
- 백엔드: `http://localhost:4000`
- 백엔드 포트: `4000`
- 프론트 포트: `3000`
- 교사 로그인 UX는 만들지 않는다. 데모 플로우는 교사 대시보드 진입부터 시작한다.
- 영상 생성은 범위에서 제외한다.
- 학생 미션은 4단계다. 회고는 단계가 아니라 후속 기록이다.

## 시작 절차

1. `git status --short --branch`로 브랜치와 변경사항을 확인한다.
2. `GOAL.md`와 이 문서를 읽는다.
3. DB/asset 작업이면 `backend/data/README.md`도 읽는다.
4. 기존 변경사항을 되돌리지 않는다.
5. 작은 단위로 구현하고, 가능한 검증을 실행한 뒤 한국어 커밋을 만든다.

## 현재 완성도

전체 완성도는 약 94%다.

| 영역 | 완성도 | 판단 |
| --- | ---: | --- |
| 교사 대시보드 데이터 연결 | 90% | seed/등록 학생, context bundle, 리포트, 콘텐츠 상태가 연결됨. 운영 회원/권한 확장만 남음. |
| 백엔드 API 기반 | 88% | 교사/학생/콘텐츠/공공데이터/NEIS 학교검색/학생등록/지원 프로필/AI 리포트/ContextBrief API가 연결됨. 운영 migration과 durable job queue는 미완성. |
| 콘텐츠 생성 품질 | 76% | scenario/stage/visual unit과 작성 전 설계 필드가 검증됨. 실제 provider 반복 샘플 품질 확인은 남음. |
| 이미지/음성 asset 파이프라인 | 82% | background job 생성/polling과 asset별 성공·실패 상태 저장이 연결됨. provider 실패 UX와 운영 queue 전환이 남음. |
| 학생 런타임/realtime | 88% | published 미션, 제출, 회고, 완료, realtime preview/runtime API 성공 경로가 E2E로 고정됨. 실제 provider 음성 송수신 확인은 남음. |
| 학생등록 UX | 90% | 학교검색/기본 등록/access code와 지원 intake 보존, AI 초기 지원 프로필 초안, 교사 확정, 학생정보 탭 반영이 연결됨. 센터 원자료 파일 업로드/버전 UI는 남음. |
| AI 리포트/메모리 폐루프 | 78% | 학생 완료 뒤 자동 요약, AI 리포트 SSE 초안, 교사 확정 리포트 저장, memory candidate 반영, ContextBrief dirty/refresh가 E2E로 연결됨. 실제 provider 리포트 품질 검증은 남음. |
| 문서/인수인계 | 90% | DB dump와 generated asset 공유 기준, API/프론트 계약, E2E 범위, 검증 결과가 정리됨. |

## 현재 완성된 흐름

- 데모 학생 3명 seed가 교사 대시보드, 학생 홈, 학생 미션 화면에서 같은 데이터로 연결된다.
- 학생 이름은 `김지우`, `이민준`, `박수민`처럼 성까지 포함한다.
- 학생 홈과 대시보드의 학년/유형 표기는 `초3 · 저연령 학습지원형`처럼 한국어 label을 사용한다.
- 교사 대시보드는 학생별 `dashboardStage`를 기준으로 자료 생성, 자료 검토, 학습, 학습 피드백 상태를 표시한다.
- 학생 홈에서 학생 카드를 누르면 해당 학생의 최신 published 콘텐츠로 바로 이동한다.
- 자료 생성·검토 탭은 생성 결과, 검토 모달, 승인/반려/배포 API 흐름에 연결되어 있다.
- 교사 화면에서는 내부 AI 참고 맥락을 그대로 노출하지 않는다. 학생 맥락은 서버에서 오케스트레이터 입력으로만 사용한다.
- 학생 미션은 published 콘텐츠만 조회하고, 시작/제출/회고/완료 이벤트를 API에 저장한다.
- 학생이 완료하면 최신 attempt 기반 리뷰 요약이 자동 생성되고, 교사 대시보드 단계가 학습 피드백으로 이동한다.
- 검토 모달의 학생 화면 미리보기 iframe 높이는 잘림이 없도록 보정했다.
- 교사용 미리보기 URL은 `preview=1`을 붙여 unpublished 콘텐츠도 열 수 있고, 학생 배포 URL은 published 콘텐츠에만 노출한다.
- 미배포 콘텐츠를 학생 런타임 URL로 열면 배포 전 안내 화면에서 교사용 미리보기로 이동하도록 막는다.
- 학생 preview의 카드매칭, 순서배열, blank fill 템플릿은 고정 캔버스 안에서 자체 높이/스크롤을 갖는다.
- 검토 모달에서 이미지/음성 asset이 준비되지 않은 자료는 `사용 승인`과 `수업에 적용하기`가 막힌다.
- 학생 화면에서 다음 단계로 이동하면 URL의 `step` query가 함께 갱신된다.
- 교사 메모는 `POST /api/teacher/students/{studentId}/notes`로 저장되고, 새로고침 후에도 최근 메모가 복원된다.
- 교사 학습 기록 리포트는 `session` note로 저장되고, `POST /api/review-summaries/{reviewId}/apply-to-memory`로 메모리에 반영된다.
- `GET /api/public-data/schools/search`는 실제 NEIS `schoolInfo` 조회로 학교를 검색하고 캐시에 저장한다.
- `POST /api/teacher/students`는 학교검색 결과를 기반으로 학생, 케이스, 메모리카드, 다음 목표, 학생 access code를 만든다.
- 교사 대시보드의 `학생 등록` 버튼은 학교검색, 학교 선택, 학생 강점/약점/지원 입력, 등록 후 access code 확인과 자료 생성 탭 이동까지 연결되어 있다.
- 학생등록 원자료는 `student_support_intake_sources`에 보존되고, `POST /api/teacher/students/{studentId}/support-profile-drafts`로 초기 지원 프로필 초안을 만든다.
- 교사가 `POST /api/teacher/students/{studentId}/support-profiles`로 초안을 확인/저장하면 학생정보 탭, memory card, ContextBrief dirty source에 반영된다.
- `GET /api/teacher/students/{studentId}/context-brief`와 `POST /api/teacher/students/{studentId}/context-brief/refresh`가 최신 생성용 압축 맥락을 조회/갱신한다.
- 콘텐츠 생성 오케스트레이터 입력에는 `studentContextBrief`와 `generationContext.contextBriefPriority`가 함께 들어가며, 교사 요청 주제를 우선하고 ContextBrief는 scaffold 조정에만 쓴다.
- 학생 완료 뒤 `POST /api/review-summaries/{reviewId}/report-drafts/stream`이 AI 리포트 초안을 SSE로 반환한다.
- `POST /api/teacher-reports`는 교사가 확정한 리포트와 memory candidate를 저장하고, memory card와 ContextBrief dirty 상태를 갱신한다.
- 이미지 프롬프트 생성은 별도 LLM 호출 없이 `briefJson.stageVisualSpecs`와 `templateJson` 기반 deterministic builder를 사용한다.
- 이미지 5장은 `gpt-image-2`로 병렬 생성한다.
- 프론트는 `POST /api/contents/{contentId}/assets/generation-jobs`로 background job을 만들고 `GET /api/contents/{contentId}/assets/generation-jobs/{jobId}`를 polling한다.
- asset generation job 상태와 asset별 성공/실패는 `MissionContent.briefJson.assetGenerationJobs`에 저장된다.
- 일부 asset 실패 시 성공 asset은 유지되고 실패 asset만 새 job에서 다시 생성된다.

## 데모 학생

| 학생 | 학교/학년 | 유형 | access code | 최신 콘텐츠 |
| --- | --- | --- | --- | --- |
| 김지우 | 영주중앙초등학교 초3 | 저연령 학습지원형 | `STAR-003` | `content_clock_001` |
| 이민준 | 영주중학교 중2 | 고연령 학습지원형 | `STAR-001` | `content_fraction_001` |
| 박수민 | 영주가흥초등학교 초6 | 일상생활 지원형 | `STAR-002` | `content_bus_001` |

## 제품 규칙

- 콘텐츠는 `MissionContent` 1개와 `ContentStage` 4개로 구성한다.
- 1~3단계는 승인된 정적 템플릿 JSON만 사용한다.
- 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 발화 연습이다.
- 대표 이미지 1장, 단계별 이미지 4장, 대표/단계별 안내 음성 5개를 asset으로 가진다.
- 생성된 콘텐츠는 `teacher_review`로 저장되고, 교사 승인 후 `approved`, 배포 후 `published`가 된다.
- provider key가 없거나 생성/검증에 실패하면 대체 seed 콘텐츠를 저장하지 않고 실패 run과 검수 필요 상태를 남긴다.
- 학생에게 노출되는 모든 AI 생성 콘텐츠는 자동 검수와 교사 승인 뒤에만 배포한다.
- 학생 플레이 중 1~3단계에서 AI가 새 분석/새 생성/후처리로 콘텐츠를 바꾸면 안 된다.
- 학생 화면에는 진단명, 내부 라벨, 영어 단계명, provider 오류를 노출하지 않는다.
- 화면 문장은 모두 한국어로 만든다.
- 계약상 JSON key는 영문을 유지할 수 있지만, label/choice/feedback/teacher summary 등 사용자-facing 문장은 한국어여야 한다.
- `teach-back`, `realtime` 같은 내부 표현은 교사 화면에서 `설명해보기`, `실시간 발화 연습`처럼 한국어로 설명한다.
- 공공데이터는 학생 개인 진단값이 아니라 교육과정, 학사일정, 지역 맥락, 통계 근거로 사용한다.

## 단계 계약

일상생활 지원형:

1. 상황 만나기: 일상 시나리오 이미지와 짧은 이야기
2. 단서 찾기: 상황 속 중요한 정보 고르기
3. 행동 고르기: 지금 해야 할 행동 선택
4. 한 번 해보기: 실제 상황을 재현하는 롤플레잉형 실시간 발화 연습

학습집중형:

1. 개념 열기: 개념 설명과 시나리오 이미지
2. 문제 1: 시나리오 기반 기본 문제
3. 문제 2: 1번 응용 및 심화 문제
4. 설명해보기: 가상 시나리오를 보고 직접 설명하는 실시간 발화 연습

템플릿 선택은 완전 랜덤이 아니다. 학생 메모리, 난이도, 최근 실패/성공 기록을 바탕으로 고른다.

## 이미지와 음성 기준

- 이미지 생성 모델은 `gpt-image-2` 기준이다.
- 한 미션의 이미지 5장은 병렬 생성한다.
- 이미지 안에는 문제/정답/선택지/피드백 UI 텍스트를 넣지 않는다.
- 단, 포스터/안내문/표지판처럼 장면 자체의 읽기 근거인 짧은 텍스트는 허용한다.
- 이미지 prompt는 장면만 설명해야 하며 빈 카드, 말풍선, UI 패널, 선택지 영역, 버튼 같은 학습지형 구성을 요청하면 실패 처리한다.
- 이미지 생성 실패를 seed asset으로 조용히 대체하지 않는다.
- OpenAI Realtime 음성은 ElevenLabs 안내 음성과 별도다.
- OpenAI realtime 기본값은 `OPENAI_REALTIME_VOICE=marin`, `OPENAI_REALTIME_VOICE_SPEED=0.92`다.
- ElevenLabs 안내 음성은 선생님이 옆에서 또렷하게 말해주는 톤을 목표로 한다.
- ElevenLabs 기본값은 `ELEVENLABS_MODEL_ID=eleven_v3`, `ELEVENLABS_SPEED=1.08`, `ELEVENLABS_ENABLE_AUDIO_TAGS=false`다.
- v3 오디오 태그는 한국어 말끝이 늘어지는 현상이 있어 기본 비활성화한다.

## AI 생성 구조

현재 구조:

- `POST /api/ai/orchestrator-runs`가 학생 맥락과 교사 요청을 보고 생성 계획을 만든다.
- `POST /api/ai/content-generations`가 4단계 미션 콘텐츠를 만든다.
- 콘텐츠 생성 입력은 `generationPlan.scenarioPlan`, `stagePlans`, `visualSpecDrafts`로 분리된다.
- 저장된 콘텐츠는 `briefJson.generationUnits.stageContentDrafts`에 단계별 draft를 남긴다.
- content id, stage id, asset id는 백엔드가 결정적으로 재작성한다.
- schema/quality retry는 `qualityRepair.stageRepairTargets`와 이전 `stageContentDrafts`를 함께 보내 실패 stage/visual unit 중심으로 고친다.
- 이미지 생성 전에는 별도 LLM을 다시 호출하지 않고, 완성된 `MissionContent`의 `briefJson.stageVisualSpecs`와 단계별 `templateJson`을 조합해 5개 이미지 prompt를 만든다.

품질 기준:

- 콘텐츠 생성은 `MissionContent` schema와 계약 검증을 통과해야 저장된다.
- LLM 기반 `content_quality_critique`는 선택 설정이며, 기본 병목을 줄이기 위해 현재 기본값은 비활성화다.
- 오케스트레이터 plan은 작성 전 설계 기준을 포함해야 한다.
- `scenarioSpine`에는 `whyThisMatters`, `studentLikelyImpulseOrMisconception`, `stage2FirstSuccess`, `stage3Transfer`, `stage4Reuse`가 필요하다.
- `stagePlan[*].templateRationale`은 템플릿 선택 이유를 남긴다.
- `stageVisualSpecs[*].evidenceLocation`은 문제 판단 근거가 장면 어디에 보이는지 설명한다.

최근 안정화:

- GPT 모델 기본값은 `gpt-5.1`로 올리고 reasoning effort는 `none`으로 둔다.
- generation timeout은 180초 기준으로 본다.
- `realtimeSpec.postPracticeReflection`이 object로 올 때 list로 정규화한다.
- `realtimeSpec.rubric[*].description`만 있고 `label`이 없을 때 label로 정규화한다.

## AI가 쓰는 학생 맥락

현재 `GET /api/teacher/students/{studentId}/context-bundle`이 AI 생성 전 맥락의 기준이다.

포함 내용:

- 학생 이름, 학년 label, 학생 유형 label
- 현재 학습 상태와 대시보드 단계
- 교사가 저장한 최근 사례 메모
- 이전 학습 시도와 리뷰 요약
- 장기 반응 패턴과 설명 방식
- NEIS snapshot 기반 학교 일정/시간표 맥락

이 맥락은 콘텐츠를 미리 정해두는 용도가 아니다. 교사가 입력한 수업 주제와 충돌하지 않도록, 학생에게 어떤 수업 방식이 필요한지 판단하는 보조 입력이다.

현재 구현은 `context-bundle` 전체와 별도로 학생별 `ContextBrief`를 오케스트레이터 입력에 전달한다. `ContextBrief`는 선생님 요청 주제와 합쳐질 1~2KB 생성용 요약이며, 학생 유형, 읽기 부담, 선택지 수, 최근 성공/실패 패턴, 쓰면 좋은 scaffold, 피해야 할 과거 주제 회귀를 담는다.

## 다음 큰 작업 1. 학생등록과 초기 지원 프로필

현재 상태:

- 학생등록은 기본정보, 학교검색, 현재 목표, 관찰 메모, 강점, 약점, 선호 지원을 받는다.
- 등록 payload의 `supportIntake`는 `student_support_intake_sources`에 원자료로 보존한다.
- 저장 시 `profileJson.dashboard`, `memoryCard`, 초기 dirty `student_context_briefs`를 만든다.
- `POST /api/teacher/students/{studentId}/support-profile-drafts`가 등록 원자료를 바탕으로 `수업 설계 초안`을 만든다.
- `POST /api/teacher/students/{studentId}/support-profiles`가 교사 확정 프로필을 저장하고 학생정보 탭, memory card, ContextBrief dirty 상태에 반영한다.
- 학생정보 탭은 현재 목표, 학습 반응 패턴, 지원 유의점, 강점/어려움, 교사 메모 중심으로 재구성했다.
- 대시보드 왼쪽 목록의 긴 `~수업이 좋겠어요` 문장은 프론트에서 짧은 현재 목표로 압축한다.

남은 확장:

- 센터에서 받는 기능평가/PBS 자료를 그대로 화면에 옮기지 않는다.
- 제품용 간단 체크리스트와 AI 초기 지원 프로필로 바꾼다.
- 센터 양식 파일 업로드와 원자료 버전 관리 UI를 추가한다.
- 현재 초안 생성은 데모 안정성을 위해 local demo AI builder를 사용한다. 실제 provider 기반 문장 품질 검증은 남아 있다.

등록 화면 추가 후보:

- 학습 반응: 그림 단서, 짧은 문장, 선택지 수, 따라 말하기, 역할놀이
- 부담 요인: 긴 설명, 실패 후 재시도, 전환, 기다림, 소음, 과제 시작
- 행동지원 정보: 우선 지원 행동, 발생 맥락, 기능 가설
- 대체기술: 도움 요청하기, 쉬기 요청하기, 다시 말해달라고 하기, 순서 확인하기

학생정보 탭 목표 구성:

- 기본 프로필: 학교, 학년, 학생 유형, 현재 목표
- 수업 설계 힌트: 등록 정보와 이후 기록을 수업 설계 언어로 번역한 AI 초안/교사 확정 문장
- 학습 반응 패턴: 잘 반응하는 단서, 부담되는 방식, 적정 선택지 수, 읽기 부담
- 행동지원 프로필: 우선 지원 행동, 발생 맥락, 기능 가설, 대체기술
- 강점/어려움: 교사용 문장형 chip
- 교사 메모: 저장 시 메모리 source로 남는 자유 기록

대시보드 수정 기준:

- 왼쪽 학생 목록의 긴 `~수업이 좋겠어요` 문장은 제거하거나 아주 짧은 현재 목표로 바꾼다.
- 학생정보 탭의 `수업 제안`, `콘텐츠 방향 제안`, `수업 유의점`은 하드코딩/규칙 제안처럼 보이면 안 된다.
- 학생정보 탭은 `현재 목표`, `학습 반응 패턴`, `지원 유의점`, `강점`, `어려움`, `교사 메모` 중심으로 재구성한다.
- AI 초기 지원 프로필이 도입되면 `AI 초안`과 `교사 확인 완료` 상태를 구분한다.

권장 DB:

- `student_support_intake_sources`: 등록 당시 원자료, 센터 양식 요약, 체크리스트 응답, 파일 출처를 보존
- `student_support_profiles`: AI 초안과 교사 확정 지원 프로필을 버전 관리
- `student_context_briefs`: 콘텐츠 생성용 1~2KB 압축 맥락. 등록 확정 뒤 dirty 또는 refreshed 상태로 관리

지원 프로필 필드 후보:

- `learningResponse`: 잘 반응하는 단서, 읽기 부담, 선택지 수, 설명 방식
- `challengeBehaviorPriorities`: 우선 지원 행동, 위험도, 빈도, 지속시간, 독립기술 관련성
- `behaviorFunctionHypotheses`: 관심, 회피, 감각/자동강화, 신체 불편, 원하는 물건/활동
- `replacementSkills`: 도움 요청, 쉬기 요청, 다시 말해달라고 하기, 순서 확인하기
- `recommendedScaffolds`: 먼저-그다음, 시각 일정, 짧은 성공 경험, 선택권 제공
- `avoidGuidance`: 피해야 할 자극, 지시 방식, 과거 주제 회귀

현재 수용 기준:

- AI 문구는 진단명이 아니라 `수업 설계 초안`으로 표시한다.
- 원자료와 AI 초안, 교사 확정값을 분리한다.
- 학생정보 탭은 선생님이 다음 수업을 바로 설계할 수 있는 문장으로 보인다.
- 학생등록 직후 AI 초기 지원 프로필 초안을 만들 수 있다. E2E 테스트가 검증한다.
- 교사가 초안을 확인/수정/저장하면 메모리 seed와 ContextBrief source로 이어진다. E2E 테스트가 검증한다.

## 다음 큰 작업 2. AI 리포트와 메모리 폐루프

현재 상태:

- 학생이 미션을 완료하면 `review_summaries`가 생성된다.
- 현재 자동 기록 요약은 정답률, 회고, realtime 이벤트를 모은 규칙 기반 요약이다.
- `POST /api/review-summaries/{reviewId}/apply-to-memory`로 교사가 수동 반영하면 `memory_cards`가 갱신된다.
- `POST /api/review-summaries/{reviewId}/report-drafts/stream`이 마크다운 AI 리포트 초안을 SSE로 반환한다.
- `POST /api/teacher-reports`가 교사 확정 리포트와 선택한 memory candidate를 저장한다.
- 확정 리포트 저장 시 `memory_cards.recent4wResponseJson`, `nextSessionCautions`가 갱신되고 ContextBrief가 dirty 상태가 된다.
- 교사 대시보드 학습 기록 탭에서 AI 리포트 초안 생성, 수정, 최근 기록 저장까지 연결된다.

현재 UX:

- 학습 기록 탭의 `자동 기록 요약`은 접을 수 있는 원자료 요약으로 둔다.
- 그 아래 `AI 리포트 초안` 영역을 추가한다.
- 교사가 `생성하기`를 누르면 수업 반응, 이해 변화, 다음 수업 제안, 메모리 반영 후보가 마크다운 초안으로 채워진다.
- 교사는 초안을 수정하고 `최근 기록으로 저장`한다.
- 저장된 교사 리포트와 선택된 메모리 후보가 다음 ContextBrief 갱신 source가 된다.

AI 리포트 입력:

- `review_summary`: 완료율, 정답률, 오답 패턴, 학생 회고, realtime 요약
- `attempt_result`: stage별 제출 결과와 시도 횟수
- `content_snapshot`: 콘텐츠 제목, 수업 의도, stage 요약, realtime 목표
- `student_context_brief`: 최신 학생 생성용 압축 맥락
- `teacher_notes`: 최근 교사 메모와 이번 회기 입력
- `school_context`: 필요한 경우 NEIS 시간표/학교 맥락

권장 DB:

- `teacher_report_drafts`: AI 리포트 초안, 입력 snapshot, 스트리밍 결과, 다음 학습 제안, 메모리 후보, 모델, 상태 저장
- `teacher_reports`: 교사가 확정 저장한 공식 리포트와 선택된 메모리 후보 저장
- `student_context_briefs`: 학생별 최신 생성용 요약, source watermark, dirty 상태, 갱신 시간, 모델 저장
- 필요하면 `student_memory_sources`: 회고, 교사 리포트, 메모리 카드, 리뷰 요약을 한곳에서 추적하는 source ledger

현재 수용 기준:

- 리포트 초안은 SSE 이벤트로 즉시 반환된다.
- 최종 저장 전까지 memory card를 자동 overwrite하지 않는다.
- 저장된 원문 기록은 보존하고, ContextBrief는 캐시처럼 재생성 가능하다.
- 콘텐츠 생성에는 `studentContextBrief`와 현재 교사 요청이 함께 전달된다.
- 콘텐츠 fallback은 기존처럼 최대 1회 targeted repair만 허용한다.

## 다음 큰 작업 3. ContextBrief

현재 상태:

- 학생별 `student_context_briefs`를 저장한다.
- `GET /api/teacher/students/{studentId}/context-brief`와 `POST /api/teacher/students/{studentId}/context-brief/refresh`로 조회/갱신한다.
- 등록 시 dirty brief를 만들고, 지원 프로필 확정/리포트 저장/메모리 반영 뒤 dirty 처리한다.
- refresh는 학생 유형, 읽기 부담, 선택지 수, 최근 성공/어려움 패턴, 추천 scaffold, 피해야 할 주제 회귀를 1~2KB 요약으로 다시 만든다.
- 오케스트레이터 입력에는 ContextBrief가 별도 필드로 전달된다.

남은 확장:

- 현재 refresh는 요청 즉시 실행된다. 운영에서는 durable background job으로 승격한다.
- 실제 provider 기반 ContextBrief 압축 품질과 watermark 정책을 검증한다.

필수 필드 후보:

```json
{
  "studentId": "student_001",
  "briefText": "짧은 그림 단서와 2개 선택지에서 안정적으로 시작합니다...",
  "studentType": "저연령 학습지원형",
  "readingLoad": "짧은 한 문장 지시가 적합",
  "choiceCount": 2,
  "recentSuccessPatterns": ["그림 단서를 먼저 볼 때 시작이 빠름"],
  "recentDifficultyPatterns": ["긴 설명 뒤 첫 행동 시작이 느림"],
  "recommendedScaffolds": ["그림 먼저 보기", "2개 선택지", "따라 말하기"],
  "avoidTopicRegression": ["이미 충분히 반복한 시계 읽기만 재사용하지 않기"],
  "sourceWatermark": "2026-05-05T12:00:00+09:00",
  "dirty": false
}
```

## 다음 큰 작업 4. 콘텐츠 생성 안정화와 E2E

현재 문제:

- 콘텐츠 생성이 timeout만의 문제가 아니라 schema mismatch, template 계약 불일치, realtimeSpec shape 불일치 때문에 자주 실패한다.
- 최근 실패 예:
  - `realtimeSpec.postPracticeReflection`이 list여야 하는데 object로 반환됨
  - `realtimeSpec.rubric` 항목이 `label` 대신 `description`으로 반환됨
  - `orchestrator.stagePlan[3].templateType`이 허용 범위를 벗어남
  - 품질검수가 실제 학습 흐름보다 형식 제약에 과하게 반응함

해야 할 일:

- schema mismatch는 normalizer와 prompt 계약으로 흡수한다.
- 품질검수 실패는 실제 교육 품질 문제인지, 과도한 형식 제약인지 분리한다.
- 실패한 `agent_run`의 input/output/error를 근거로 수정한다.
- `완전 실패`와 `부분 실패`를 UI에서 구분한다.
- asset 일부 실패 시 구조 콘텐츠는 보존하고 asset 재시도 경로를 제공한다.

E2E 검증 흐름:

1. 교사 대시보드 진입
2. 학생 등록
3. 등록 정보 기반 AI 초기 지원 프로필 생성
4. 교사 확인/수정/저장
5. 학생정보 탭 반영 확인
6. 콘텐츠 생성 요청
7. 생성된 콘텐츠 schema/quality/asset 상태 확인
8. 교사 검토 화면에서 미리보기 확인
9. 교사가 직접 수정
10. 이미지/음성 asset 생성 확인
11. 승인/배포
12. 학생 화면에서 플레이
13. 1~3단계 제출
14. 4단계 realtime 또는 preview 경로 확인
15. 학생 회고 작성
16. 수업 완료
17. 교사 학습 기록 탭 반영
18. AI 리포트 초안 생성
19. 교사 리포트 수정/저장
20. memory candidate 선택 저장
21. ContextBrief dirty/refresh 확인
22. 같은 학생으로 두 번째 콘텐츠 생성
23. 이전 리포트/메모리가 새 콘텐츠 생성에 반영되는지 확인

반복 생성 검증 케이스:

- 저연령 학습지원형
- 고연령 학습지원형
- 일상생활 지원형
- 신규 등록 학생

각 케이스에서 최소 1회 성공 콘텐츠를 만든다.

실패 분류:

- `OPENAI_REQUEST_FAILED`
- `MISSION_CONTENT_SCHEMA_INVALID`
- `MISSION_CONTENT_QUALITY_INVALID`
- `ORCHESTRATOR_PLAN_QUALITY_INVALID`
- `ASSET_GENERATION_FAILED`
- `REALTIME_SESSION_FAILED`

완료 기준:

- 신규 학생 등록부터 두 번째 콘텐츠 생성까지 실제로 이어진다.
- schema mismatch가 반복해서 같은 형태로 터지지 않는다.
- 실패 시 UI와 `agent_runs`에서 원인이 명확히 보인다.
- `teacher_review` 콘텐츠가 검토 화면에서 깨지지 않는다.
- 승인/배포 후 학생 화면에서 정상 플레이된다.
- 학생 완료 후 교사 기록과 AI 리포트, 메모리 업데이트가 이어진다.
- 전체 플로우를 통과한 테스트 또는 명확한 수동 검증 기록이 이 문서에 남는다.

## API 계약

기준 서버: `http://localhost:4000`

모든 성공 응답은 기본적으로 `ok(...)` 래퍼를 사용한다. 프론트 계약은 `frontend/lib/api/contracts.ts`, 백엔드 스키마는 `backend/app/domain/schemas.py`를 함께 확인한다.

### 계약 기준표

| 흐름 | Backend schema/route | Frontend contract/helper |
| --- | --- | --- |
| 학교검색 | `GET /api/public-data/schools/search` | `SchoolSearchRequest`, `SchoolSearchResponse`, `searchSchools` |
| 학생등록 | `StudentRegistrationRequest`, `POST /api/teacher/students` | `StudentRegistrationRequest`, `StudentRegistrationResponse`, `createTeacherStudent` |
| 학생 초기 지원 프로필 | `StudentSupportIntakeSource`, `StudentSupportProfile`, support profile routes | `createSupportProfileDraft`, `confirmSupportProfile` |
| 콘텐츠 검토 수정 | `ContentReviewUpdateRequest`, `PATCH /api/contents/{contentId}/review` | `ContentReviewUpdateRequest`, `updateContentReview` |
| 승인/반려/배포 | `ContentApprovalRequest`, `ContentRejectRequest`, content routes | `ContentApprovalRequest`, `ContentRejectRequest`, `approveContent`, `rejectContent`, `publishContent` |
| asset generation job | content asset job routes | `AssetGenerationJob`, `createContentAssetGenerationJob`, `getContentAssetGenerationJob` |
| student runtime | `AttemptRequest`, `StageSubmitRequest`, `RealtimeSession*Request` | matching request/response types in `contracts.ts` |
| AI 리포트/ContextBrief | `TeacherReportDraft`, `TeacherReport`, `StudentContextBrief`, report/context routes | `createTeacherReportDraft`, `saveTeacherReport`, `getStudentContextBrief`, `refreshStudentContextBrief` |

### Health

- `GET /health`: 서버 상태 확인

### Context/Auth

- `GET /api/context/seed`: 데모 교사, 학생 3명, assignment, mission mapping 조회
- `GET /api/context/me`: 데모 사용자/조직 정보 조회
- `POST /api/auth/demo-login`: 데모 교사 세션 생성. 실제 로그인 UX는 만들지 않는다.
- `POST /api/auth/student-access`: 학생 access code 세션 생성

### Teacher

- `GET /api/teacher/students`: 학생 목록, 한국어 label, `dashboardStage`, 최신 콘텐츠 상태 조회
- `POST /api/teacher/students`: 신규 학생 등록. 학교는 `schoolCode` 또는 `schoolName`으로 확인하고, 캐시에 없으면 NEIS 학교검색을 수행한다.
- `GET /api/teacher/students/{studentId}`: 학생 상세, 대시보드 프로필, 학교 맥락, context bundle 조회
- `GET /api/teacher/students/{studentId}/history`: 사례 메모, 콘텐츠, 시도, 이벤트, realtime 세션 이력 조회
- `GET /api/teacher/students/{studentId}/context-bundle`: AI 생성 전 학생 맥락 bundle 조회
- `GET /api/teacher/students/{studentId}/context-brief`: 최신 AI 생성용 압축 맥락 조회. 없으면 즉시 생성을 시도한다.
- `POST /api/teacher/students/{studentId}/context-brief/refresh`: 학생별 ContextBrief 즉시 갱신 요청
- `GET /api/teacher/students/{studentId}/report`: 리뷰 요약 기반 학습 기록 조회
- `POST /api/teacher/students/{studentId}/notes`: 교사 메모 저장
- `PATCH /api/teacher/students/{studentId}/memory-card`: 메모리 카드 부분 수정

### Public Data

- `GET /api/public-data/sources`: 공공데이터 source registry 조회
- `GET /api/public-data/schools`: seed 학교 목록 조회
- `GET /api/public-data/schools/search`: 학교명 검색. `q`, `officeCode`, `syncIfMissing`를 받으며, 캐시에 없고 `NEIS_API_KEY`가 있으면 NEIS `schoolInfo`를 조회해 학교 캐시에 저장한다.
- `GET /api/public-data/schools/{schoolCode}/context`: 학교 일정/시간표 맥락 조회
- `GET /api/public-data/schools/{schoolCode}/timetable`: 저장된 시간표 snapshot 조회
- `POST /api/public-data/sources/{sourceCode}/sync`: source 동기화 시도

시간표 query:

- `date`: `YYYY-MM-DD`
- `grade`: 학년
- `className`: 반
- `syncIfMissing`: 저장 snapshot이 없을 때 NEIS 동기화 시도 여부

`syncIfMissing=true`는 필수 query와 `NEIS_API_KEY`가 있을 때만 실제 동기화를 시도한다.

학생등록 payload 예시:

```json
{
  "displayName": "최하늘",
  "schoolName": "풍기초등학교",
  "officeCode": "R10",
  "grade": "초4",
  "gradeNumber": "4",
  "className": "1",
  "studentType": "learning_focus",
  "currentGoal": "영어 단어를 그림 카드와 연결하기",
  "observationNote": "그림 단서가 있으면 먼저 손으로 가리키며 반응합니다.",
  "strengths": ["그림 단서를 잘 찾음"],
  "weaknesses": ["긴 문장 지시가 부담됨"],
  "preferredSupports": ["그림 카드", "2개 선택지"]
}
```

학생등록 확장 예정 payload 후보:

```json
{
  "displayName": "최하늘",
  "schoolCode": "8811053",
  "grade": "초4",
  "className": "1",
  "studentType": "life_support",
  "currentGoal": "쉬는 시간에 친구에게 도움을 요청하는 연습",
  "observationNote": "긴 설명보다 그림과 짧은 선택지에 먼저 반응합니다.",
  "supportIntake": {
    "learningResponse": {
      "preferredCues": ["그림 단서", "짧은 문장"],
      "readingLoad": "low",
      "choiceCountLimit": 2
    },
    "challengeBehaviorPriorities": [
      {
        "label": "자리 이탈",
        "risk": 2,
        "frequency": 3,
        "duration": 2,
        "independenceImpact": 3
      }
    ],
    "behaviorFunctionHypotheses": ["과제 회피", "관심 요청"],
    "replacementSkills": ["도움 요청하기", "쉬기 요청하기"],
    "recommendedScaffolds": ["먼저-그다음 안내", "짧은 성공 경험"]
  }
}
```

### AI/Content

- `POST /api/ai/orchestrator-runs`: 학생 맥락 기반 생성 계획 생성
- `POST /api/ai/content-generations`: 4단계 미션 콘텐츠 생성
- `GET /api/ai/agent-runs/{agentRunId}`: AI 실행 기록 조회
- `GET /api/contents/{contentId}`: 교사용 콘텐츠 상세 조회
- `PATCH /api/contents/{contentId}/review`: 교사가 stage instruction/question/choice/realtime goal을 직접 수정
- `POST /api/contents/{contentId}/approve`: 모든 stage/asset 검수 후 승인. asset은 URL이 있고 `qaStatus=passed`여야 한다.
- `POST /api/contents/{contentId}/reject`: 반려 및 수정 요청 저장
- `POST /api/contents/{contentId}/publish`: 준비·승인된 asset만 학생에게 배포하고 대시보드 단계를 `learning`으로 이동
- `POST /api/contents/{contentId}/assets/{assetId}/generate`: 단일 asset 생성
- `POST /api/contents/{contentId}/assets/generation-jobs`: 이미지/오디오 asset package background job 생성. 응답은 `jobId`, `status`, `totalCount`, `completedCount`, `failedCount`, asset별 상태를 포함한다.
- `GET /api/contents/{contentId}/assets/generation-jobs/{jobId}`: asset generation job 상태 조회. job 상태는 `queued`, `running`, `partial_failed`, `succeeded`, `failed`다.
- `POST /api/contents/{contentId}/assets/generate-package`: 기존 호환용 동기 batch 생성 endpoint. 프론트는 사용하지 않으며 새 작업은 `generation-jobs`와 polling을 사용한다.
- `GET /api/contents/{contentId}/review-summary`: 최신 attempt 기반 리뷰 요약 조회
- `POST /api/contents/{contentId}/review-summary`: 최신 attempt 기반 리뷰 요약 생성
- `POST /api/review-summaries/{reviewId}/apply-to-memory`: 교사 확인 후 리뷰 요약을 메모리에 반영

### Student

- 학생 runtime API는 published 콘텐츠만 반환해야 한다.
- teacher review 상태 콘텐츠는 교사용 preview 경로로만 본다.
- 학생 화면에서 1~3단계는 정적 template JSON을 실행한다.
- 4단계는 realtime session을 시작하고 event/complete를 저장한다.
- 학생 완료 후 review summary가 생성되고 교사 대시보드가 학습 피드백 상태로 이동한다.

## 신규 API 계약

### 등록 정보 기반 초기 지원 프로필

- `POST /api/teacher/students/{studentId}/support-profile-drafts`
- 목적: 학생등록 원자료와 체크리스트를 바탕으로 AI 초기 지원 프로필 초안을 만든다.

응답 예시:

```json
{
  "draftId": "support_profile_draft_001",
  "studentId": "student_001",
  "status": "completed",
  "profileDraft": {
    "lessonDesignHints": [
      "그림 단서를 먼저 보여주고 선택지는 2개부터 시작하는 편이 좋습니다."
    ],
    "learningResponsePattern": {
      "worksWell": ["그림 단서", "짧은 문장"],
      "canBeHard": ["긴 설명 뒤 바로 시작하기"],
      "choiceCountLimit": 2
    },
    "behaviorSupportProfile": {
      "priorityBehaviors": ["자리 이탈"],
      "functionHypotheses": ["과제 회피"],
      "replacementSkills": ["도움 요청하기", "쉬기 요청하기"]
    },
    "strengths": ["그림 단서를 빠르게 찾습니다."],
    "supportCautions": ["과제 시작 전 긴 설명은 줄이는 편이 좋습니다."]
  }
}
```

- `POST /api/teacher/students/{studentId}/support-profiles`
- 목적: 교사가 확인/수정한 지원 프로필을 확정 저장한다.
- 저장 효과: `memory_cards` seed 갱신, `student_context_briefs` dirty 처리, 학생정보 탭 표시값 갱신.

### AI 리포트 초안 스트리밍

- `POST /api/review-summaries/{reviewId}/report-drafts/stream`
- 응답: `text/event-stream`
- 목적: 학생 학습 완료 뒤 교사용 마크다운 리포트 초안을 실시간으로 보여준다.

SSE event:

```text
event: draft_delta
data: {"text":"## 수업 반응\n"}

event: draft_metadata
data: {"nextLearningSuggestions":["..."],"memoryCandidates":["..."]}

event: done
data: {"draftId":"report_draft_...","status":"completed"}

event: error
data: {"message":"..."}
```

### 교사 리포트 저장

- `POST /api/teacher-reports`
- 목적: AI 초안을 교사가 수정한 뒤 공식 학습 기록으로 저장한다.

Payload 예시:

```json
{
  "draftId": "report_draft_001",
  "reviewSummaryId": "review_summary_001",
  "studentId": "student_001",
  "contentId": "content_001",
  "teacherBody": "## 수업 반응\n그림 단서를 먼저 볼 때 안정적으로 참여했습니다.",
  "selectedMemoryCandidates": [
    "그림 단서를 먼저 확인하면 과제 시작이 빨라집니다."
  ]
}
```

저장 효과:

- `teacher_reports`에 확정 리포트를 남긴다.
- 선택된 memory candidate는 장기 메모리 source로 기록한다.
- 해당 학생의 `student_context_briefs`를 dirty 상태로 만든다.
- 다음 콘텐츠 생성 전 최신 ContextBrief가 없거나 dirty면 프론트/운영자가 refresh 요청을 먼저 보낼 수 있다.

### 학생 ContextBrief

- `GET /api/teacher/students/{studentId}/context-brief`
- `POST /api/teacher/students/{studentId}/context-brief/refresh`

## DB와 asset 인수인계

추적 파일:

```text
backend/data/eduyj_demo_dump.sql
backend/data/eduyj_demo.db
backend/data/README.md
backend/generated/assets/
```

현재 MVP 확인 단계에서는 실제 생성 이미지/음성과 승인된 SQLite 상태를 팀원이 바로 확인할 수 있도록 `backend/data/eduyj_demo.db`와 공유 기준 `backend/generated/assets/`를 추적한다.

새로 생긴 `backend/generated/assets/**`는 `.gitignore`로 기본 무시한다. 팀 기준으로 확정한 콘텐츠만 `git add -f backend/generated/assets/students/{studentId}/{contentId}`로 명시 추가하고, DB/dump/asset을 같은 커밋에 넣는다.

현재 로컬 `backend/data/eduyj_demo.db` 변경은 개인 실행 결과일 수 있으므로 공유 기준으로 확정하기 전까지 커밋하지 않는다.

SQL dump 복원:

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

seed 재생성:

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

권장 asset 경로:

```text
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.png
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.mp3
```

## 실행

Backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

Frontend:

```bash
cd frontend
npm run dev
```

## 검증

Backend:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m pytest tests/test_api_smoke.py::test_registered_student_generation_review_student_completion_e2e
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

Frontend:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

문서/통합:

```bash
git diff --check
```

## 최근 검증 기록

2026-05-06 기준 `dev` 작업트리에서 아래 검증을 완료했다.

- `cd backend && .venv/bin/ruff check app tests`: 통과
- `cd backend && .venv/bin/python -m pytest`: 61 passed
- `cd backend && .venv/bin/python -m pytest tests/test_api_smoke.py::test_registered_student_generation_review_student_completion_e2e`: 통과
- `cd backend && DATABASE_URL=sqlite+pysqlite:///$tmp_db .venv/bin/python -m app.data.seed_demo`: temp DB 기준 통과
- `cd frontend && npm run lint`: 통과
- `cd frontend && npx tsc --noEmit`: 통과

`test_registered_student_generation_review_student_completion_e2e`는 교사 대시보드 진입, NEIS 학교검색, 학생등록, AI 초기 지원 프로필 초안, 교사 확정, ContextBrief refresh, 콘텐츠 생성, asset job, 교사 preview, 승인/배포, 학생 플레이, 1~3단계 제출, 4단계 realtime, 회고/완료, AI 리포트 SSE 초안, 교사 리포트 저장, memory candidate 반영, ContextBrief dirty/refresh, 같은 학생 두 번째 콘텐츠 생성까지 검증한다.

2026-05-05 기준 `dev`에서 아래 검증을 완료했다.

- `cd backend && .venv/bin/ruff check app tests`: 통과
- `cd backend && .venv/bin/python -m pytest`: 57 passed
- `cd frontend && npm run lint`: 통과
- `cd frontend && npx tsc --noEmit`: 통과
- `git diff --check`: 통과
- Chrome headless 브라우저 확인: `localhost:3000`/`localhost:4000`에서 교사 대시보드, 학생등록 모달, published 학생 홈, 3단계 preview, 4단계 realtime preview 렌더링 확인. 가로 overflow와 치명적 콘솔 오류 없음.

브라우저에서는 로컬 `backend/data/eduyj_demo.db` 변경을 더 늘리지 않기 위해 학생등록 최종 제출은 반복하지 않았다. 등록 제출부터 콘텐츠 생성, asset job, 승인/배포, 학생 완료, 교사 리포트 반영은 `backend/tests/test_api_smoke.py::test_registered_student_generation_review_student_completion_e2e`가 temp DB와 mock provider로 검증한다.

## 생성 파이프라인 병목 위치

| 단계 | 코드 위치 | 현재 병목 | 다음 조치 |
| --- | --- | --- | --- |
| 오케스트레이터 | `backend/app/api/routes/ai.py` | scenario/stage/visual plan과 작성 전 기준은 분리됨 | 반복 생성 샘플 품질 확인 |
| 콘텐츠 agent | `backend/app/api/routes/ai.py` | stageContentDrafts와 targeted repair는 연결됨 | stage별 별도 agent run은 운영 최적화로 남김 |
| 품질 검수 | `backend/app/services/content_quality.py` | 작성 전 설계 필드 검증 연결됨 | 반복 생성 샘플 품질 확인 |
| 이미지 prompt | `backend/app/api/routes/contents.py` | deterministic으로 개선됨 | 앞단 visual spec 품질 강화 |
| 이미지 생성 | `backend/app/api/routes/contents.py` | background job과 partial retry는 연결됨 | 운영 queue와 provider 재시도 정책 고도화 |
| 음성 생성 | `backend/app/ai/elevenlabs_provider.py` | 속도 병목은 작음 | sourceText 품질과 speed 테스트 |
| 검토/승인 | `backend/app/services/store.py` | asset 실패 시 상태 설명이 거칠다 | asset job 상태 UI 추가 |
| 학생 runtime | `backend/app/api/routes/student.py` | WebRTC 빠른 이탈/재시작 오류 가능 | Realtime 안정화 |

## 다음 개선 우선순위

1. 실제 provider 기반 지원 프로필/AI 리포트/ContextBrief 문장 품질 샘플 검증
2. ContextBrief refresh와 asset generation job의 durable worker/queue 전환
3. 운영 DB 기준 Alembic/PostgreSQL migration 확정
4. 콘텐츠 생성 안정성 normalizer와 schema mismatch 반복 방지 샘플 확대
5. 실제 provider 반복 생성과 realtime 음성 송수신 확인
6. 센터 원자료 파일 업로드, 버전 관리, 보호자 동의 흐름 확장
7. 공모전 이후 회원가입/권한 흐름 확장

## `/goal`에 넣을 짧은 프롬프트

아래처럼 짧게 넣고, 세부사항은 이 문서를 읽게 한다.

```text
/goal EduYJ dev 브랜치에서 GOAL.md와 docs/GOAL_CONTEXT.md 기준으로 학생등록, AI 초기 지원 프로필, 콘텐츠 생성 안정화, 검토/배포/학생 플레이/AI 리포트/메모리/ContextBrief까지 전체 E2E 플로우를 구현·검증·문서화·커밋·푸시한다. 작업 루트는 /Users/gimdonghyeon/Desktop/educationforyeongju-backend 이며 교사 로그인은 만들지 않는다.
```
