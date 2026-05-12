# EduYJ Goal Context

확인 기준일: 2026-05-12

이 문서는 새 작업자와 `/goal`이 확인할 단일 인수인계 문서입니다.

## 작업 기준

- 작업 루트: `/Users/gimdonghyeon/Desktop/educationforyeongju-backend`
- 기준 브랜치: `main`
- 로컬 프론트: `http://localhost:3000`
- 로컬 백엔드: `http://localhost:4000`
- 배포 프론트 터널: <https://eduYj.summit1123.co.kr>
- 배포 백엔드 터널: <https://eduYjapp.summit1123.co.kr>
- 교사 로그인 UX는 만들지 않습니다. 데모는 교사 대시보드 진입부터 시작합니다.
- 영상 생성은 범위에서 제외합니다.
- 학생 미션은 4단계입니다. 회고는 단계가 아니라 후속 기록입니다.

## 현재 공유 DB

현재 main은 배포 중인 SQLite DB 상태를 그대로 공유합니다.

- DB: `backend/data/eduyj_demo.db`
- dump: `backend/data/eduyj_demo_dump.sql`
- generated asset: `backend/generated/assets/students/**`
- PostgreSQL: 목표 운영 DB지만, main 기준 migration script는 아직 없습니다.

현재 DB 요약:

```text
students: 2
supportCases: 2
missionContents: 7
contentStages: 28
contentAssets: 70
contentAttempts: 33
teacherReports: 1
memoryCards: 2
studentContextBriefs: 2
```

콘텐츠 상태:

```text
published: 2
teacher_review: 5
```

현재 학생:

```text
김진수 / elementary_3 / learning_focus
최하늘 / elementary_3 / learning_focus
```

DB와 asset은 같이 이동해야 합니다. DB 안의 `/generated/...` 경로가 실제 파일을 가리켜야 학생 화면에서 이미지와 음성이 보입니다.

## 로컬 실행

Backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Frontend:

```bash
cd frontend
npm run dev
```

프로덕션 빌드 실행:

```bash
cd frontend
npm run build
npm run start -- -H 0.0.0.0 -p 3000
```

## 현재 기능 흐름

1. 교사 대시보드에서 학생을 등록하거나 기존 학생을 선택합니다.
2. 학생등록 체크리스트는 현재 프론트 상수입니다. 선택 결과만 `supportIntake` JSON으로 저장됩니다.
3. `지원 초안 생성`은 등록 원자료와 교사 메모를 바탕으로 초기 수업 방식 프로필을 만듭니다.
4. 교사가 프로필을 확인하면 학생정보 탭, memory card, 기억장치 dirty 상태에 반영됩니다.
5. 자료 생성 탭에서 `입력 내용으로 생성` 또는 `AI 추천 생성`을 누릅니다.
6. 오케스트레이터가 수업 시나리오와 4단계 계획을 만듭니다.
7. 콘텐츠 agent가 `MissionContent` JSON을 만듭니다.
8. schema와 deterministic quality check를 통과하면 `teacher_review` 상태로 저장됩니다.
9. asset generation job이 이미지 5장과 음성 5개를 생성합니다.
10. 교사는 `제안 검토하기`에서 학생 화면 iframe과 stage 내용을 확인합니다.
11. 승인 후 `수업에 적용하기`를 누르면 해당 학생의 최신 published 콘텐츠가 됩니다.
12. 학생 화면은 published 콘텐츠만 조회합니다.
13. 학생 완료 후 리뷰 요약, AI 리포트 초안, 교사 리포트 저장, 기억장치 갱신 흐름으로 이어집니다.

## 콘텐츠 생성 구조

```text
POST /api/ai/orchestrator-runs
  -> studentContextBrief, caseFile, requestedGoal, contentType, templateRandomization 입력
  -> scenarioSpine, stagePlan, stageVisualSpecs, imagePackageIntent 생성

POST /api/ai/content-generations
  -> orchestrator output과 generationPlan 입력
  -> MissionContent, 4 stages, 10 assets record 생성
  -> schema/quality 검증 후 DB 저장

POST /api/contents/{contentId}/assets/generation-jobs
  -> 이미지 5장 병렬 생성
  -> 음성 5개 생성
  -> asset별 상태를 briefJson.assetGenerationJobs에 저장
```

관련 주요 파일:

- `backend/app/api/routes/ai.py`
- `backend/app/api/routes/contents.py`
- `backend/app/services/content_quality.py`
- `backend/app/services/store.py`
- `frontend/app/dashboard/page.tsx`
- `frontend/app/dashboard/StudentRegistrationModal.tsx`
- `frontend/lib/api/contracts.ts`

## 단계 계약

학습지원형:

1. 개념 열기
2. 문제 1
3. 문제 2
4. 설명해보기

일상생활 지원형:

1. 상황 만나기
2. 단서 찾기
3. 행동 고르기
4. 한 번 해보기

1~3단계는 정적 템플릿이고, 4단계는 realtime 연습입니다.

## 현재 중요한 계약

- 학생에게 노출되는 AI 콘텐츠는 교사 승인 전에는 published로 열리지 않습니다.
- 교사 검토는 `제안 검토하기` 모달에서 합니다. 별도 `교사용 미리보기` 버튼은 제거했습니다.
- `학생 화면 열기`는 published 콘텐츠에서만 사용합니다.
- 이미지에는 문제 UI, 선택지, 정답, 피드백을 넣지 않습니다.
- 포스터, 알림장, 안내문처럼 장면 자체의 읽기 근거인 짧은 텍스트는 이미지에 들어갈 수 있습니다.
- 기억장치는 주제를 정하는 값이 아니라 제시 방식, 읽기 부담, 선택지 수, 스캐폴딩 조정용입니다.
- 체크리스트 항목은 아직 DB catalog가 아니라 프론트 상수입니다.

## 남은 작업

우선순위가 높은 작업:

1. 체크리스트 catalog API화
   - 현재: 프론트 상수
   - 목표: `GET /api/teacher/support-checklists?studentType=...`
   - 저장 시 `itemId`, `groupId`, `label`, `version` 보존

2. PostgreSQL migration 준비
   - 현재: SQLite 공유 DB
   - 목표: PostgreSQL role/database 생성 스크립트와 SQLite to PostgreSQL migration script
   - 현재 dry-run에서 FK insert 순서 보정이 필요함

3. 학생정보 탭 UX 정리
   - 텍스트 과밀 축소
   - 수업 방식 프로필과 기억장치의 역할 구분
   - 학습지원형/일상생활지원형 intake 문항 분리 강화

4. 콘텐츠 품질 반복 샘플 검증
   - 학습지원형이 일상생활형 문제처럼 흐르지 않는지 확인
   - 이미지 근거와 templateJson 문제의 연결성 확인
   - 템플릿 다양성 확인

5. 운영 job queue
   - 현재: FastAPI background task
   - 목표: durable worker/queue

## 팀 작업 방식

`main`에서 브랜치를 따서 작업합니다.

```bash
git checkout main
git pull origin main
git checkout -b frontend/작업명
# 또는
git checkout -b backend/작업명
```

프론트 작업자는 SQLite 공유 DB로 UI/API 연결을 먼저 확인합니다.

백엔드 작업자는 SQLite로 빠르게 개발하되, DB 구조 변경이나 migration 작업은 PostgreSQL dry-run까지 확인해야 합니다.

## 검증

기본:

```bash
git status --short --branch
git diff --check
```

DB:

```bash
sqlite3 backend/data/eduyj_demo.db "pragma integrity_check;"
```

Backend:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
```

Frontend:

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

## `/goal`에 넣을 짧은 프롬프트

```text
/goal EduYJ main 브랜치에서 docs/GOAL_CONTEXT.md 기준으로 학생등록, 체크리스트 계약, 콘텐츠 생성, 검토/배포, 학생 플레이, AI 리포트, 기억장치 흐름을 깨지 않게 개선한다. 현재 공유 DB는 SQLite이며 DB/asset 변경 시 backend/data/README.md 기준으로 dump와 generated asset을 함께 갱신한다. 교사 로그인과 영상 생성은 범위에서 제외한다.
```
