# Remaining Issues

확인 기준일: 2026-05-05

이 문서는 다음 작업자가 바로 이어받기 위한 남은 이슈 목록이다. 진행상황 요약은 [HANDOFF.md](HANDOFF.md), API 계약은 [API.md](API.md), DB/asset 복원은 [../backend/data/README.md](../backend/data/README.md)를 본다.

## 현재 완성도

전체 완성도는 약 72%로 본다.

| 영역 | 완성도 | 판단 |
| --- | ---: | --- |
| 교사 대시보드 데이터 연결 | 75% | seed 학생, context bundle, 리포트, 콘텐츠 상태는 연결됨. 학생등록 UI와 생성 job 상태 UX가 남음. |
| 백엔드 API 기반 | 82% | 교사/학생/콘텐츠/공공데이터/NEIS 학교검색/학생등록 백엔드가 있음. 운영 migration과 job queue는 미완성. |
| 콘텐츠 생성 품질 | 76% | scenario/stage/visual unit과 작성 전 설계 필드가 검증됨. 실제 생성 샘플 반복 품질 확인은 E2E에서 남음. |
| 이미지/음성 asset 파이프라인 | 82% | background job 생성/polling과 asset별 성공·실패 상태 저장이 연결됨. provider 실패 UX와 운영 queue 전환이 남음. |
| 학생 런타임/realtime | 82% | published 미션, 제출, 회고, 완료 기록은 됨. preview/runtime 경계와 WebRTC 취소/재시작 방어가 연결됨. provider 실연결 E2E가 남음. |
| 학생등록 UX | 88% | 교사 대시보드 모달에서 학교검색, 학교 선택, 강점/약점/지원 입력, 등록 후 목록/상세 갱신과 access code 확인까지 연결됨. 브라우저 통합 회귀만 남음. |
| 문서/인수인계 | 78% | DB dump와 generated asset 공유 기준이 정리됨. E2E 결과와 최종 push 전 상태만 갱신하면 됨. |

## 우선순위

### 완료. 생성 작업을 background job으로 분리

현재 상태:

- 프론트는 `POST /api/contents/{contentId}/assets/generation-jobs`로 job을 만들고 `GET /api/contents/{contentId}/assets/generation-jobs/{jobId}`를 polling한다.
- job 상태는 `queued`, `running`, `partial_failed`, `succeeded`, `failed`다.
- job과 asset별 상태는 `MissionContent.briefJson.assetGenerationJobs`에 저장되어 브라우저를 닫아도 조회할 수 있다.
- 이미지 일부 실패 시 성공 asset은 유지되고 실패 asset만 새 job에서 재시도한다.
- 기존 `generate-package` endpoint는 백엔드 호환용 동기 endpoint로 남겼고 프론트는 사용하지 않는다.

남은 운영 전환:

- 지금 job 실행은 FastAPI background task 기반이다. 운영에서는 별도 durable worker/queue로 승격할 수 있다.

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

### 완료. 콘텐츠 생성 구조를 작은 단위로 분리

현재 상태:

- 콘텐츠 생성 입력은 `generationPlan.scenarioPlan`, `stagePlans`, `visualSpecDrafts`로 분리된다.
- 저장된 콘텐츠는 `briefJson.generationUnits.stageContentDrafts`에 단계별 template/realtime/asset/visual draft를 남긴다.
- schema/quality retry는 `qualityRepair.stageRepairTargets`와 이전 `stageContentDrafts`를 함께 보내 실패 stage/visual unit 중심으로 고친다.
- content id, stage id, asset id는 백엔드가 계속 결정적으로 재작성한다.

남은 확장:

- 지금은 단일 content agent 호출 안에서 unit을 분리하고 targeted repair snapshot을 보내는 구조다. 운영 최적화가 필요하면 stage별 agent run을 별도 durable job으로 승격한다.

### 완료. 콘텐츠 품질 기준을 검수 탈락이 아니라 작성 기준으로 전환

현재 상태:

- `content_quality.py`는 스키마, 단계명, 템플릿, 이미지 prompt 금지어, 유형 혼선을 잡는다.
- 오케스트레이터 prompt는 작성 전 설계 체크리스트를 앞쪽에 둔다.
- `scenarioSpine`은 `whyThisMatters`, `studentLikelyImpulseOrMisconception`, `stage2FirstSuccess`, `stage3Transfer`, `stage4Reuse`를 필수로 가진다.
- `stageVisualSpecs[*].evidenceLocation`은 문제 판단 근거가 장면 어디에 보이는지 설명한다.
- `stagePlan[*].templateRationale`은 템플릿 선택 이유를 남긴다.
- 위 필드는 `validate_orchestrator_plan_quality`에서 검증한다.

남은 확인:

- 같은 요청을 3회 생성해도 주제, 학생 유형, 단계 흐름이 크게 흔들리지 않는다.
- 교사가 봤을 때 "문제는 맞지만 너무 유치함" 케이스가 줄어든다.

### 완료. 검토 화면과 학생 화면 preview 안정화

현재 상태:

- iframe preview 기준은 실제 학생 캔버스를 담는 `1125x852` viewport로 맞췄다.
- 카드매칭, 순서배열, blank fill 템플릿은 고정 stage board 안에서 자체 높이와 내부 스크롤을 갖는다.
- blank fill은 좁은 우측 패널이 아니라 전체 stage board에서 visual과 입력 UI를 함께 보여준다.
- 교사 대시보드는 `교사용 미리보기`와 `학생 배포 화면` URL을 분리한다.
- unpublished 콘텐츠를 학생 runtime URL로 열면 학생 화면을 실행하지 않고 교사용 preview 안내 화면으로 이동시킨다.
- 2026-05-05 브라우저 확인: choice, blank fill, sequence, card match direct preview는 desktop/mobile에서 document overflow 없이 렌더링됐다.

남은 확인:

- 최종 E2E에서 검토 모달 4개 stage를 다시 확인한다.
- 현재 로컬 DB에는 stale content mapping이 있어 대시보드 진입 시 `content_generated_001`, `content_prepared_notice_magnifier_001` 404가 찍힌다. DB/asset 정책 정리 단계에서 공유 기준 DB와 함께 정리한다.

### 완료. Realtime 안정화

현재 상태:

- 학생 runtime은 published 콘텐츠에서만 realtime 세션을 만들 수 있다.
- 교사 preview realtime endpoint는 별도 존재한다.
- 프론트는 realtime 연결 시도 id를 예약하고, 취소/이탈/재시작 뒤 늦게 도착한 WebRTC 이벤트를 무시한다.
- 연결 중에는 `연결 중단`으로 바로 idle 상태로 돌아갈 수 있고, preview 완료 뒤에는 다시 시작할 수 있다.
- 교사용 preview와 학생 runtime의 시작 실패 메시지를 분리했다.
- preview/runtime 화면은 이미지, 안내 음성, 실시간 연결 상태를 단계별로 표시한다.
- OpenAI realtime 기본값은 `OPENAI_REALTIME_VOICE=marin`, `OPENAI_REALTIME_VOICE_SPEED=0.92`이고 provider 단위 테스트가 있다.

남은 확인:

- 2026-05-05 브라우저 확인: provider 응답 대기 중 preview 시작 후 즉시 `연결 중단`해도 콘솔 오류 없이 대기 상태로 돌아왔다.
- 실제 provider client secret, 마이크 권한, WebRTC 음성 송수신, 완료 저장은 최종 E2E에서 한 번 더 확인한다.

### 완료. DB dump와 generated asset 정책 정리

현재 상태:

- `backend/data/eduyj_demo.db`, `backend/data/eduyj_demo_dump.sql`, `backend/generated/assets/`가 추적 대상이다.
- 실제 생성 테스트를 하면 로컬 DB와 generated asset이 계속 변한다.
- 지금 로컬에는 커밋하지 않은 실제 생성 테스트 결과가 남아 있다.
- 새 generated asset은 `.gitignore`로 기본 무시한다.
- 공유 기준으로 확정한 콘텐츠만 `git add -f backend/generated/assets/students/{studentId}/{contentId}`로 명시 추가한다.
- DB, dump, asset은 같은 커밋에 넣어야 한다.

운영 규칙:

- "공유 기준 DB"와 "개인 테스트 결과"를 구분한다.
- 팀원 공유용 DB를 만들 때만 dump와 asset을 함께 갱신한다.
- generated asset은 학생별/콘텐츠별 폴더 구조를 유지한다.

권장 규칙:

```text
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.png
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.mp3
```

남은 확인:

- 현재 로컬의 `backend/data/eduyj_demo.db` 변경과 untracked generated asset은 공유 기준으로 확정하지 않았다.
- 최종 push 전 공유 기준 DB를 갱신할지, 현 추적 dump/asset 기준으로 둘지 다시 확인한다.

### P2. API/프론트 계약 정리

해야 할 일:

- `frontend/lib/api/contracts.ts`와 `backend/app/domain/schemas.py`의 신규 학생등록 계약 동기화.
- `docs/API.md`에 학생등록 payload 예시 추가.
- asset generation job 계약은 `frontend/lib/api/contracts.ts`와 `docs/API.md`에 반영됨. P2에서는 최종 E2E 기준으로 남은 field/상태명을 다시 정리한다.

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
| 오케스트레이터 | `backend/app/api/routes/ai.py` | scenario/stage/visual plan과 작성 전 기준은 분리됨 | 반복 생성 샘플 품질 확인 |
| 콘텐츠 agent | `backend/app/api/routes/ai.py` | stageContentDrafts와 targeted repair는 연결됨 | stage별 별도 agent run은 운영 최적화로 남김 |
| 품질 검수 | `backend/app/services/content_quality.py` | 작성 전 설계 필드 검증 연결됨 | 반복 생성 샘플 품질 확인 |
| 이미지 prompt | `backend/app/api/routes/contents.py` | deterministic으로 개선됨 | 앞단 visual spec 품질 강화 |
| 이미지 생성 | `backend/app/api/routes/contents.py` | background job과 partial retry는 연결됨 | 운영 queue와 provider 재시도 정책 고도화 |
| 음성 생성 | `backend/app/ai/elevenlabs_provider.py` | 속도 병목은 작음 | sourceText 품질과 speed 테스트 |
| 검토/승인 | `backend/app/services/store.py` | asset 실패 시 상태 설명이 거칠다 | asset job 상태 UI 추가 |
| 학생 runtime | `backend/app/api/routes/student.py` | WebRTC 빠른 이탈/재시작 오류 가능 | Realtime 안정화 |

## 다음 커밋 추천 순서

1. `docs : API 프론트 계약 최종 정리`
2. `test : 교사 생성부터 학생 완료까지 e2e 추가`
3. `docs : 최종 검증 결과 반영`
