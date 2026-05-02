# 최신 인수인계 요약

확인 기준일: 2026-05-03

기준 브랜치:

```text
backend: 21955e5 fix : 학생 학습 완료 및 검토 흐름 연결 이후 문서/DB 덤프 정리
dev: backend 최신 작업 통합 예정
```

이 문서는 새 팀원이 현재 데모 상태를 빠르게 이해하고 바로 작업을 이어가기 위한 요약이다.
상세 계약은 [08-rest-api-spec.md](08-rest-api-spec.md), [12-schema-contract.md](12-schema-contract.md), [../backend/08-ai-orchestrator-workflow.md](../backend/08-ai-orchestrator-workflow.md)를 기준으로 한다.

## 현재 완성된 흐름

- 데모 학생 3명 seed가 교사 대시보드, 학생 홈, 학생 미션 화면에서 같은 데이터로 연결된다.
- 학생 이름은 성까지 포함한 `김지우`, `이민준`, `박수민` 기준이다.
- 학생 홈의 학년/유형 표기는 `초3 · 저연령 학습지원형`처럼 한국어 label을 사용한다.
- 교사 대시보드는 학생별 `dashboardStage`를 기준으로 자료 생성, 자료 검토, 학습, 학습 피드백 상태를 표시한다.
- 교사 대시보드의 학생 정보 탭은 학생에게 필요한 수업 방향을 제안형 한국어 문장으로 보여준다.
- 교사 메모 영역은 선생님이 추가 관찰 내용을 적어 메모리 맥락에 남긴다는 UX 의미로 정리했다.
- 자료 생성·검토 탭은 학생 컨텍스트 bundle, AI 생성 결과, 검토 iframe, 승인/반려/배포 API 흐름에 맞춰 연결됐다.
- 학생 홈에서 학생 카드를 누르면 해당 학생의 최신 published 콘텐츠로 바로 이동한다.
- 학생 미션은 published 콘텐츠만 조회하고, 시작/제출/회고/완료 이벤트를 API에 저장한다.
- 학생이 완료하면 최신 attempt 기반 리뷰 요약이 자동 생성되고, 교사 대시보드 단계가 학습 피드백으로 이동한다.

## 데모 학생과 접속 코드

| 학생 | 학교/학년 | 유형 | access code | 최신 콘텐츠 |
| --- | --- | --- | --- | --- |
| 김지우 | 영주중앙초등학교 초3 | 저연령 학습지원형 | `STAR-003` | `content_clock_001` |
| 이민준 | 영주중학교 중2 | 고연령 학습지원형 | `STAR-001` | `content_fraction_001` |
| 박수민 | 영주가흥초등학교 초6 | 일상생활 지원형 | `STAR-002` | `content_bus_001` |

## 오케스트레이터에 전달되는 맥락

`GET /api/teacher/students/{studentId}/context-bundle`이 AI 생성 전 맥락의 기준이다.

구성:

- `student`: 이름, 학년 label, 학생 유형 label
- `caseSummary`: 현재 목표, 학생에게 필요한 수업 방향, 지원 전략, 대시보드 단계
- `teacherInputs`: 교사가 저장한 최근 사례 메모
- `previousLessons`: 최근 학습 시도와 리뷰 요약
- `memoryCard`: 장기 반응 패턴, 설명 방식, 주의점
- `schoolContext`: NEIS snapshot 기반 학교 일정/시간표 맥락
- `autoContext`: 교사 화면에 보여줄 학생 기록, 이전 수업, 학교 시간표, 다음 목표
- `aiReadyContext`: 오케스트레이터가 반드시 반영할 요약, 사용할 요소, 피해야 할 요소, 근거 출처

이 맥락은 정답을 미리 짜놓는 용도가 아니라, 학생에게 어떤 수업이 필요한지 판단하고 질 좋은 콘텐츠를 만들기 위한 입력이다.

## 콘텐츠 생성과 품질 관리

현재 계약:

- 콘텐츠는 `MissionContent` 1개와 `ContentStage` 4개로 구성한다.
- 1~3단계는 승인된 정적 템플릿 JSON만 사용한다.
- 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 발화 연습이다.
- 대표 이미지 1장, 단계별 이미지 4장, 대표/단계별 안내 음성 5개를 asset으로 가진다.
- 영상 생성은 범위에 없다.
- provider key가 없거나 생성/검증에 실패하면 대체 seed 콘텐츠를 저장하지 않고 실패 run과 검수 필요 상태를 남긴다.
- 생성된 콘텐츠는 `teacher_review`로 저장되고, 교사 승인 후 `approved`, 배포 후 `published`가 된다.

품질 검증 기준:

- 화면에 노출되는 텍스트는 한국어로 반환되어야 한다.
- 템플릿 필드명은 계약상 영문 key를 유지하되, label/choice/feedback/teacher summary 등 사용자-facing 문장은 한국어여야 한다.
- 학생 정보 카드처럼 수업 방향을 설명하는 영역은 "이런 수업이 필요해 보입니다"에 가까운 제안형 문장이어야 한다.
- 학생 홈처럼 학생이 바로 콘텐츠에 들어가는 영역은 "수업이 좋겠어요" 같은 교사용 제안 문구를 쓰지 않는다.
- 4단계 realtime은 `teach-back` 같은 내부 용어 대신 "실시간 발화 연습"처럼 교사가 이해할 수 있는 한국어 표현을 우선 사용한다.

## 최신 API 요약

공통:

- `GET /api/context/seed`: 교사, 학생 3명, assignment, mission mapping을 반환한다.
- `GET /api/context/me`: 데모 사용자/조직 정보를 반환한다.
- `POST /api/auth/demo-login`: 데모 교사 세션 생성.
- `POST /api/auth/student-access`: 학생 access code 세션 생성.

교사:

- `GET /api/teacher/students`: 한국어 label, `dashboardStage`, 최신 콘텐츠 상태를 포함한 학생 목록.
- `GET /api/teacher/students/{studentId}`: 학생 상세, 대시보드 프로필, 학교 맥락, context bundle.
- `GET /api/teacher/students/{studentId}/context-bundle`: AI 생성 전 학생 맥락 bundle.
- `GET /api/teacher/students/{studentId}/history`: 사례 메모, 콘텐츠, 시도, 이벤트, realtime 세션 이력.
- `GET /api/teacher/students/{studentId}/report`: 리뷰 요약 기반 학습 기록.
- `POST /api/teacher/students/{studentId}/notes`: 교사 메모 저장.
- `PATCH /api/teacher/students/{studentId}/memory-card`: 메모리 카드 부분 수정.

공공데이터:

- `GET /api/public-data/schools/{schoolCode}/timetable`: 저장된 시간표 snapshot 조회.
- `syncIfMissing=true`일 때 필수 query와 `NEIS_API_KEY`가 있으면 NEIS 시간표 cache 동기화를 시도한다.

AI/콘텐츠:

- `POST /api/ai/orchestrator-runs`: 학생 맥락 기반 생성 계획.
- `POST /api/ai/content-generations`: 4단계 미션 콘텐츠 생성.
- `GET /api/ai/agent-runs/{agentRunId}`: AI 실행 기록 조회.
- `GET /api/contents/{contentId}`: 교사용 콘텐츠 상세.
- `POST /api/contents/{contentId}/approve`: 모든 stage/asset 검수 후 승인.
- `POST /api/contents/{contentId}/reject`: 반려 및 수정 요청.
- `POST /api/contents/{contentId}/publish`: 학생에게 배포하고 대시보드 단계를 `learning`으로 이동.
- `POST /api/contents/{contentId}/assets/{assetId}/generate`: 단일 asset 생성.
- `POST /api/contents/{contentId}/assets/generate-package`: 이미지 5개와 오디오 5개 batch 생성.
- `GET|POST /api/contents/{contentId}/review-summary`: 최신 attempt 기반 리뷰 요약 조회/생성.

학생:

- `GET /api/student/missions/today`: 로그인 학생의 published 미션 목록.
- `GET /api/student/missions/{contentId}`: published 미션 상세.
- `POST /api/student/missions/{contentId}/start`: attempt 생성.
- `POST /api/student/missions/{contentId}/stages/{stageId}/submit`: 1~3단계 제출.
- `POST /api/student/missions/{contentId}/events`: 학생 활동 이벤트 저장.
- `POST /api/student/missions/{contentId}/stages/{stageId}/realtime-session`: 4단계 realtime 세션 생성.
- `POST /api/student/realtime-sessions/{sessionId}/events`: realtime 이벤트 저장.
- `POST /api/student/realtime-sessions/{sessionId}/complete`: realtime 결과 저장.
- `POST /api/student/missions/{contentId}/post-practice-reflection`: 학생 회고 저장.
- `POST /api/student/missions/{contentId}/complete`: attempt 완료, 리뷰 요약 자동 생성, 대시보드 단계를 `feedback`으로 이동.

## DB와 seed 인수인계

추적 파일:

```text
backend/data/eduyj_demo_dump.sql
backend/data/README.md
```

로컬 SQLite 원본인 `backend/data/eduyj_demo.db`는 `.gitignore` 대상이다.
다른 팀원은 SQL 덤프를 복원하거나 seed 명령을 다시 실행하면 된다.

seed 재생성:

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

SQL 덤프 복원:

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

PostgreSQL 같은 다른 DB는 `DATABASE_URL`을 바꾼 뒤 `app.data.seed_demo`를 실행하는 방식을 우선 사용한다.

## 최근 검증 기준

backend:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

frontend:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

문서/통합:

```bash
git diff --check
rg -n "5[단]계|마지막[ ]실시간|마지막[ ]realtime|R[e]motion|f[f]mpeg|f[a]llbackUsed|candidate[M]odels" README.md AGENTS.md GOAL.md docs .agents backend examples
```

## 남은 개선사항

- 실제 운영 key 기준 OpenAI 이미지/TTS asset 생성을 모든 신규 콘텐츠에서 반복 검증한다.
- 학생 UI의 4단계 실시간 발화 연습을 실제 WebRTC Realtime 연결로 완성한다.
- 교사 메모 저장 UI를 `POST /api/teacher/students/{studentId}/notes`와 완전히 연결한다.
- 교사 피드백을 `POST /api/review-summaries/{reviewId}/apply-to-memory`로 반영하는 화면 흐름을 붙인다.
- 학생 3명 각각에 대해 콘텐츠를 새로 생성하고, 한 번 더 생성해 메모리/이전 수업 맥락 활용 품질을 비교한다.
- 교사 승인부터 학생 완료, 교사 리포트 확인까지 E2E 회귀 테스트를 추가한다.
- 운영 PostgreSQL/Alembic 마이그레이션을 확정한다.
- 공모전 MVP 이후 회원가입, 학생 등록, 보호자 동의 흐름을 확장한다.
