# EduYJ Handoff

확인 기준일: 2026-05-05

기준 브랜치: `dev`

이 문서는 팀원이 바로 이어받기 위한 현재 상태 요약이다. 남은 이슈와 병목은 [ISSUES.md](ISSUES.md), 상세 API는 [API.md](API.md), DB 복원은 [../backend/data/README.md](../backend/data/README.md)를 기준으로 한다.

## 현재 완성된 흐름

- 데모 학생 3명 seed가 교사 대시보드, 학생 홈, 학생 미션 화면에서 같은 데이터로 연결된다.
- 학생 이름은 `김지우`, `이민준`, `박수민`처럼 성까지 포함한다.
- 학생 홈과 대시보드의 학년/유형 표기는 `초3 · 저연령 학습지원형`처럼 한국어 label을 사용한다.
- 교사 대시보드는 학생별 `dashboardStage`를 기준으로 자료 생성, 자료 검토, 학습, 학습 피드백 상태를 표시한다.
- 학생 정보 탭은 학생에게 필요한 수업 방향을 제안형 한국어 문장으로 보여준다.
- 자료 생성·검토 탭은 생성 결과, 검토 모달, 승인/반려/배포 API 흐름에 연결되어 있다.
- 교사 화면에서는 내부 AI 참고 맥락을 그대로 노출하지 않는다. 학생 맥락은 서버에서 오케스트레이터 입력으로만 사용한다.
- 학생 홈에서 학생 카드를 누르면 해당 학생의 최신 published 콘텐츠로 바로 이동한다.
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
- 이미지 프롬프트 생성은 별도 LLM 호출 없이 `briefJson.stageVisualSpecs`와 `templateJson` 기반 deterministic builder를 사용한다.
- 이미지 5장은 `gpt-image-2`로 병렬 생성한다. 프론트는 `POST /api/contents/{contentId}/assets/generation-jobs`로 background job을 만들고 `GET /api/contents/{contentId}/assets/generation-jobs/{jobId}`를 polling한다.
- asset generation job 상태와 asset별 성공/실패는 `MissionContent.briefJson.assetGenerationJobs`에 저장된다. 일부 asset 실패 시 성공 asset은 유지되고 실패 asset만 새 job에서 다시 생성된다.

## 데모 학생

| 학생 | 학교/학년 | 유형 | access code | 최신 콘텐츠 |
| --- | --- | --- | --- | --- |
| 김지우 | 영주중앙초등학교 초3 | 저연령 학습지원형 | `STAR-003` | `content_clock_001` |
| 이민준 | 영주중학교 중2 | 고연령 학습지원형 | `STAR-001` | `content_fraction_001` |
| 박수민 | 영주가흥초등학교 초6 | 일상생활 지원형 | `STAR-002` | `content_bus_001` |

## 콘텐츠 계약

공통:

- 콘텐츠는 `MissionContent` 1개와 `ContentStage` 4개로 구성한다.
- 1~3단계는 승인된 정적 템플릿 JSON만 사용한다.
- 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 발화 연습이다.
- 대표 이미지 1장, 단계별 이미지 4장, 대표/단계별 안내 음성 5개를 asset으로 가진다.
- 생성된 콘텐츠는 `teacher_review`로 저장되고, 교사 승인 후 `approved`, 배포 후 `published`가 된다.
- provider key가 없거나 생성/검증에 실패하면 대체 seed 콘텐츠를 저장하지 않고 실패 run과 검수 필요 상태를 남긴다.
- 콘텐츠 생성은 `mission_content_package` 출력 뒤 schema/계약 검증을 통과해야 저장된다. LLM 기반 `content_quality_critique`는 선택 설정이며 기본 병목을 줄이기 위해 현재 기본값은 비활성화다.
- 콘텐츠 생성 입력은 `generationPlan.scenarioPlan`, `stagePlans`, `visualSpecDrafts`로 분리되고, 저장된 콘텐츠는 `briefJson.generationUnits.stageContentDrafts`에 단계별 template/realtime/asset/visual draft를 남긴다.
- 콘텐츠 품질/schema retry는 `qualityRepair.stageRepairTargets`와 이전 `stageContentDrafts`를 함께 전달해 실패 stage/visual unit 중심으로 고친다.
- 오케스트레이터 plan은 작성 전 설계 기준을 포함해야 한다. `scenarioSpine`에는 `whyThisMatters`, `studentLikelyImpulseOrMisconception`, `stage2FirstSuccess`, `stage3Transfer`, `stage4Reuse`가 필요하고, `stagePlan[*].templateRationale`과 `stageVisualSpecs[*].evidenceLocation`도 검증한다.
- 이미지 생성 전에는 별도 LLM을 다시 호출하지 않고, 완성된 `MissionContent`의 `briefJson.stageVisualSpecs`와 단계별 `templateJson`을 조합해 5개 이미지 prompt를 만든다. `gpt-image-2`에는 이 장면 prompt만 전달한다.
- 이미지 prompt는 장면만 설명해야 하며 빈 카드, 말풍선, UI 패널, 선택지 영역, 버튼 같은 학습지형 구성을 요청하면 실패 처리한다.
- OpenAI Realtime 음성은 ElevenLabs 안내 음성과 별도다. 기본값은 `OPENAI_REALTIME_VOICE=marin`, `OPENAI_REALTIME_VOICE_SPEED=0.92`다.
- ElevenLabs 안내 음성은 선생님이 옆에서 또렷하게 말해주는 톤을 목표로 한다. 기본값은 `ELEVENLABS_MODEL_ID=eleven_v3`, `ELEVENLABS_SPEED=1.08`, `ELEVENLABS_ENABLE_AUDIO_TAGS=false`다. v3 오디오 태그는 한국어 말끝이 늘어지는 현상이 있어 기본 비활성화한다.

일상생활 지원형 단계명:

1. 상황 만나기
2. 단서 찾기
3. 행동 고르기
4. 한 번 해보기

학습집중형 단계명:

1. 개념 열기
2. 문제 1
3. 문제 2
4. 설명해보기

템플릿 선택:

- 완전 랜덤이 아니라 학생 메모리, 난이도, 최근 실패/성공 기록을 바탕으로 고른다.
- 화면 문장은 모두 한국어로 만든다.
- 계약상 JSON key는 영문을 유지할 수 있지만, label/choice/feedback/teacher summary 등 사용자-facing 문장은 한국어여야 한다.
- `teach-back`, `realtime` 같은 내부 표현은 교사 화면에서 `설명해보기`, `실시간 발화 연습`처럼 한국어로 설명한다.

## AI가 쓰는 학생 맥락

`GET /api/teacher/students/{studentId}/context-bundle`이 AI 생성 전 맥락의 기준이다.

포함 내용:

- 학생 이름, 학년 label, 학생 유형 label
- 현재 학습 상태와 대시보드 단계
- 교사가 저장한 최근 사례 메모
- 이전 학습 시도와 리뷰 요약
- 장기 반응 패턴과 설명 방식
- NEIS snapshot 기반 학교 일정/시간표 맥락

이 맥락은 콘텐츠를 미리 정해두는 용도가 아니다. 교사가 입력한 수업 주제와 충돌하지 않도록, 학생에게 어떤 수업 방식이 필요한지 판단하는 보조 입력이다.

## DB 인수인계

추적 파일:

```text
backend/data/eduyj_demo_dump.sql
backend/data/eduyj_demo.db
backend/data/README.md
backend/generated/assets/
```

현재 MVP 확인 단계에서는 실제 생성 이미지/음성과 승인된 SQLite 상태를 팀원이 바로 확인할 수 있도록 `backend/data/eduyj_demo.db`와 `backend/generated/assets/`를 추적한다.

주의: 로컬에서 자료 생성/승인/학생 완료 테스트를 하면 `eduyj_demo.db`는 추적 dump와 달라진다. 깨끗한 seed 기준이 필요하면 아래 dump 복원 명령으로 먼저 맞춘다.

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

## 남은 개선사항

자세한 우선순위와 병목은 [ISSUES.md](ISSUES.md)를 기준으로 한다.

최우선:

1. 검토 preview와 realtime preview/runtime 안정화
2. 교사 승인부터 학생 완료, 교사 리포트 확인까지 E2E 회귀 테스트 추가
