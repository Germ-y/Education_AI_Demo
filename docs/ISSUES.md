# Remaining Issues

확인 기준일: 2026-05-05

이 문서는 다음 작업자가 바로 이어받기 위한 남은 이슈 목록이다. 진행상황 요약은 [HANDOFF.md](HANDOFF.md), API 계약은 [API.md](API.md), DB/asset 복원은 [../backend/data/README.md](../backend/data/README.md)를 본다.

## 현재 완성도

전체 완성도는 약 72%로 본다.

| 영역 | 완성도 | 판단 |
| --- | ---: | --- |
| 교사 대시보드 데이터 연결 | 75% | seed 학생, context bundle, 리포트, 콘텐츠 상태는 연결됨. 학생등록 UI와 생성 job 상태 UX가 남음. |
| 백엔드 API 기반 | 82% | 교사/학생/콘텐츠/공공데이터/NEIS 학교검색/학생등록 백엔드가 있음. 운영 migration과 job queue는 미완성. |
| 콘텐츠 생성 품질 | 60% | 4단계 생성은 되지만 시나리오 깊이, 문제-이미지 정합성, retry 구조가 아직 불안정함. |
| 이미지/음성 asset 파이프라인 | 68% | gpt-image-2 5장 병렬과 ElevenLabs TTS 연결됨. HTTP 동기 요청과 상태 job 분리가 필요함. |
| 학생 런타임/realtime | 70% | published 미션, 제출, 회고, 완료 기록은 됨. preview/runtime 경계와 WebRTC 안정화가 남음. |
| 학생등록 UX | 88% | 교사 대시보드 모달에서 학교검색, 학교 선택, 강점/약점/지원 입력, 등록 후 목록/상세 갱신과 access code 확인까지 연결됨. 브라우저 통합 회귀만 남음. |
| 문서/인수인계 | 70% | 문서는 축소됨. DB dump와 generated asset 정책을 최신 상태로 반복 관리해야 함. |

## 우선순위

### P0. 생성 작업을 background job으로 분리

현재 병목:

- `POST /api/contents/{contentId}/assets/generate-package`가 이미지 5장과 음성 5개를 한 HTTP 요청에서 끝까지 수행한다.
- 실제 로그 기준 asset package는 보통 168~193초, 과거에는 764초까지 걸렸다.
- 프론트는 이 요청을 `await`하기 때문에 로딩이 사라지거나 502/timeout처럼 보일 수 있다.

해야 할 일:

- `POST /api/contents/{contentId}/assets/generation-jobs` 형태로 job 생성.
- `GET /api/contents/{contentId}/assets/generation-jobs/{jobId}`로 상태 조회.
- job 상태: `queued`, `running`, `partial_failed`, `succeeded`, `failed`.
- asset별 진행률과 오류를 저장.
- 프론트는 polling만 하고 긴 생성 요청을 직접 기다리지 않는다.

완료 기준:

- 브라우저가 닫혀도 job 상태가 남는다.
- 이미지 일부 실패 시 성공 asset은 유지되고 실패 asset만 재시도할 수 있다.
- 생성 완료 후 교사 검토 모달이 자동으로 최신 콘텐츠를 다시 읽는다.

### 완료. 학생등록 프론트 연결

현재 상태:

- 백엔드 `GET /api/public-data/schools/search`와 `POST /api/teacher/students`는 구현됨.
- 실제 NEIS `schoolInfo` 검색으로 `풍기초등학교 / 8811053 / R10` 조회 확인됨.
- 프론트 `학생 등록` 버튼은 `StudentRegistrationModal`로 연결된다.
- 학교명 입력 시 학교검색 API를 호출하고 검색 결과에서 학교를 선택한다.
- 이름, 학년, 반, 학생 유형, 현재 목표, 관찰 메모, 강점, 약점, 선호 지원을 입력한다.
- 등록 성공 후 학생 목록/상세/자료 생성 탭을 갱신한다.
- 새 학생에게 발급된 access code를 교사가 확인할 수 있다.

남은 확인:

- 최종 E2E에서 대시보드 진입부터 실제 등록, context-bundle, 자료 생성 시작까지 브라우저로 다시 확인한다.

### P0. 콘텐츠 생성 구조를 작은 단위로 분리

현재 병목:

- 오케스트레이터가 `scenarioSpine`, `stagePlan`, `stageVisualSpecs`, `imagePackageIntent`, `ttsNarrationIntent`를 한 번에 만든다.
- 콘텐츠 agent가 `MissionContent` 전체 JSON, 4개 stage, 10개 asset record, realtime spec을 한 번에 만든다.
- 품질 실패 시 작은 부분만 고치지 않고 전체 MissionContent를 다시 생성한다.
- 실제 agent run 로그에서 content 생성은 80초대가 흔하고, 실패 retry 포함 396초까지 확인됨.

해야 할 구조:

```text
teacher request
-> scenario planner
-> stage planner
-> stage content builder
-> visual spec builder
-> deterministic image prompt builder
-> image/audio generation job
-> final package validator
-> teacher review
```

권장 구현 순서:

1. `ScenarioPlan` 스키마를 별도 저장 가능한 중간 산출물로 분리.
2. stage 1~4를 각각 생성하거나 최소한 `stageContentDrafts` 배열로 나눠 검증.
3. 실패 시 해당 stage 또는 visual spec만 repair.
4. `MissionContent` 조립은 백엔드가 결정적으로 수행.
5. content id, stage id, asset id는 계속 백엔드가 생성.

완료 기준:

- 한 stage 검증 실패가 전체 4단계 재생성으로 이어지지 않는다.
- 생성 결과가 너무 유치하거나 얕을 때 교사 검토 전에 구조화된 이유가 남는다.
- 학습지원형/일상생활 지원형이 요청 주제와 섞이지 않는다.

### P1. 콘텐츠 품질 기준을 검수 탈락이 아니라 작성 기준으로 전환

현재 상태:

- `content_quality.py`는 스키마, 단계명, 템플릿, 이미지 prompt 금지어, 유형 혼선을 잡는다.
- 이 검수는 "저장해도 되는가"에는 유용하지만, "처음부터 좋은 수업인가"를 충분히 보장하지 못한다.

주요 품질 이슈:

- 학생 메모리가 scaffolding이 아니라 과거 주제 고정처럼 작동할 때가 있다.
- 학습지원형에서 생활안전/도움요청 문제처럼 흐를 수 있다.
- 카드매칭/순서배열이 교육적 이유 없이 UI 계약 때문에 들어가면 잘리거나 억지스럽다.
- 이미지가 예뻐도 문제의 근거가 장면 안에 약하게 드러날 수 있다.
- 안내문/포스터/표지판처럼 읽기 자료가 필요한 경우, 장면 텍스트를 허용해야 하는데 문제/정답/선택지와 구분해야 한다.

해야 할 일:

- 프롬프트에 "잘못 만들면 재시도"보다 "작성 전 설계 체크리스트"를 앞쪽에 둔다.
- `scenarioSpine`에 아래 필드를 강제한다.
  - `whyThisMatters`
  - `studentLikelyImpulseOrMisconception`
  - `stage2FirstSuccess`
  - `stage3Transfer`
  - `stage4Reuse`
- `stageVisualSpecs`는 "무엇을 보여줄지"뿐 아니라 "문제 판단 근거가 어디에 보이는지"를 포함한다.
- template 선택은 이유를 남긴다.

완료 기준:

- 같은 요청을 3회 생성해도 주제, 학생 유형, 단계 흐름이 크게 흔들리지 않는다.
- 교사가 봤을 때 "문제는 맞지만 너무 유치함" 케이스가 줄어든다.

### P1. 검토 화면과 학생 화면 preview 안정화

현재 상태:

- iframe 높이/일부 카드매칭 잘림은 한 차례 보정됨.
- 그래도 템플릿별 aspect/frame 검증은 부족하다.

해야 할 일:

- 템플릿별 visual regression 체크 추가.
- 카드매칭, 순서배열, 선택형, blank fill의 모바일/desktop preview 기준 높이 고정.
- 교사용 preview URL과 학생 published runtime URL을 UI에서 명확히 분리.
- unpublished 콘텐츠를 학생 runtime으로 열면 교사 preview로 안내한다.

완료 기준:

- 검토 모달에서 4개 stage가 스크롤/잘림 없이 확인된다.
- 교사 preview realtime은 unpublished에서도 가능하고, 학생 runtime은 published만 가능하다.

### P1. Realtime 안정화

현재 상태:

- 학생 runtime은 published 콘텐츠에서만 realtime 세션을 만들 수 있다.
- 교사 preview realtime endpoint는 별도 존재한다.
- 프론트 WebRTC 연결 중 빠른 이탈/재시작 시 `RTCPeerConnection` closed 관련 오류가 날 수 있다.

해야 할 일:

- 연결 attempt id 방어를 더 촘촘히 유지.
- 연결 실패 원인을 교사용 메시지와 학생용 메시지로 분리.
- preview에서 opening audio, image, realtime 연결 상태를 단계별로 표시.
- OpenAI realtime voice/speed 설정을 테스트해 기본값 확정.

완료 기준:

- 검토 모달에서 4단계 realtime preview를 시작/중단/재시작해도 콘솔 오류가 없다.
- 학생이 published 미션에서 realtime을 완료하면 이벤트와 리포트에 반영된다.

### P1. DB dump와 generated asset 정책 정리

현재 상태:

- `backend/data/eduyj_demo.db`, `backend/data/eduyj_demo_dump.sql`, `backend/generated/assets/`가 추적 대상이다.
- 실제 생성 테스트를 하면 로컬 DB와 generated asset이 계속 변한다.
- 지금 로컬에는 커밋하지 않은 실제 생성 테스트 결과가 남아 있다.

해야 할 일:

- "공유 기준 DB"와 "개인 테스트 결과"를 구분한다.
- 팀원 공유용 DB를 만들 때만 dump와 asset을 함께 갱신한다.
- generated asset은 학생별/콘텐츠별 폴더 구조를 유지한다.

권장 규칙:

```text
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.png
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.mp3
```

완료 기준:

- 팀원이 dump 복원 후 같은 콘텐츠와 asset을 볼 수 있다.
- 개인 테스트 산출물이 실수로 공유 기준 DB에 섞이지 않는다.

### P2. API/프론트 계약 정리

해야 할 일:

- `frontend/lib/api/contracts.ts`와 `backend/app/domain/schemas.py`의 신규 학생등록 계약 동기화.
- `docs/API.md`에 학생등록 payload 예시 추가.
- asset generation job 전환 후 기존 `generate-package` API는 deprecated 또는 내부 호환 endpoint로 정리.

### P2. E2E 회귀 테스트

필수 시나리오:

1. 교사 대시보드 진입.
2. NEIS 학교검색.
3. 학생등록.
4. 등록 학생으로 콘텐츠 생성.
5. asset generation job 완료.
6. 교사 검토/승인/배포.
7. 학생 홈에서 최신 콘텐츠 진입.
8. 1~3단계 제출.
9. 4단계 realtime preview/runtime 확인.
10. 회고/완료.
11. 교사 대시보드 학습 기록/리포트 반영 확인.

## 생성 파이프라인 병목 위치

| 단계 | 코드 위치 | 현재 병목 | 다음 조치 |
| --- | --- | --- | --- |
| 오케스트레이터 | `backend/app/api/routes/ai.py` | 큰 JSON 계획을 한 번에 생성 | scenario/stage/visual plan 분리 |
| 콘텐츠 agent | `backend/app/api/routes/ai.py` | MissionContent 전체 생성과 전체 retry | stage별 draft와 부분 repair |
| 품질 검수 | `backend/app/services/content_quality.py` | 탈락 조건 중심 | 작성 전 품질 기준으로 이동 |
| 이미지 prompt | `backend/app/api/routes/contents.py` | deterministic으로 개선됨 | 앞단 visual spec 품질 강화 |
| 이미지 생성 | `backend/app/api/routes/contents.py` | 5장 병렬이어도 가장 느린 이미지에 묶임 | background job과 partial retry |
| 음성 생성 | `backend/app/ai/elevenlabs_provider.py` | 속도 병목은 작음 | sourceText 품질과 speed 테스트 |
| 검토/승인 | `backend/app/services/store.py` | asset 실패 시 상태 설명이 거칠다 | asset job 상태 UI 추가 |
| 학생 runtime | `backend/app/api/routes/student.py` | preview/published 경계 혼동 가능 | URL/상태 분리 |

## 다음 커밋 추천 순서

1. `feat : asset 생성 job 상태 분리`
2. `fix : 콘텐츠 생성 stage draft 구조화`
3. `fix : 검토 preview 템플릿별 프레임 안정화`
4. `test : 교사 생성부터 학생 완료까지 e2e 추가`
5. `docs : 공유 DB와 asset 기준 갱신`
