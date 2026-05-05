# REST API

기준 서버: `http://localhost:4000`

모든 성공 응답은 기본적으로 `ok(...)` 래퍼를 사용한다. 프론트 계약은 `frontend/lib/api/contracts.ts`, 백엔드 스키마는 `backend/app/domain/schemas.py`를 함께 확인한다.

## Health

- `GET /health`: 서버 상태 확인

## Context/Auth

- `GET /api/context/seed`: 데모 교사, 학생 3명, assignment, mission mapping 조회
- `GET /api/context/me`: 데모 사용자/조직 정보 조회
- `POST /api/auth/demo-login`: 데모 교사 세션 생성
- `POST /api/auth/student-access`: 학생 access code 세션 생성

## Teacher

- `GET /api/teacher/students`: 학생 목록, 한국어 label, `dashboardStage`, 최신 콘텐츠 상태 조회
- `POST /api/teacher/students`: 신규 학생 등록. 학교는 `schoolCode` 또는 `schoolName`으로 확인하고, 캐시에 없으면 NEIS 학교검색을 수행한다.
- `GET /api/teacher/students/{studentId}`: 학생 상세, 대시보드 프로필, 학교 맥락, context bundle 조회
- `GET /api/teacher/students/{studentId}/history`: 사례 메모, 콘텐츠, 시도, 이벤트, realtime 세션 이력 조회
- `GET /api/teacher/students/{studentId}/context-bundle`: AI 생성 전 학생 맥락 bundle 조회
- `GET /api/teacher/students/{studentId}/report`: 리뷰 요약 기반 학습 기록 조회
- `POST /api/teacher/students/{studentId}/notes`: 교사 메모 저장
- `PATCH /api/teacher/students/{studentId}/memory-card`: 메모리 카드 부분 수정

## Public Data

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

## AI/Content

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

## Student

- `GET /api/student/missions/today`: 로그인 학생의 published 미션 목록 조회
- `GET /api/student/missions/{contentId}`: published 미션 상세 조회
- `POST /api/student/missions/{contentId}/start`: attempt 생성
- `POST /api/student/missions/{contentId}/stages/{stageId}/submit`: 1~3단계 제출
- `POST /api/student/missions/{contentId}/stages/{stageId}/realtime-session`: 4단계 realtime 세션 생성
- `POST /api/student/missions/{contentId}/post-practice-reflection`: 학생 회고 저장
- `POST /api/student/missions/{contentId}/events`: 학생 활동 이벤트 저장
- `POST /api/student/missions/{contentId}/complete`: attempt 완료, 리뷰 요약 자동 생성, 대시보드 단계를 `feedback`으로 이동
- `POST /api/student/realtime-sessions/{sessionId}/events`: realtime 이벤트 저장
- `POST /api/student/realtime-sessions/{sessionId}/complete`: realtime 결과 저장

## Audit

- `GET /api/audit-logs`: 감사 로그 조회

## Generation Logs

- 기본 파일: `backend/logs/generation.log`
- 환경변수: `GENERATION_LOG_FILE`
- 대상: AI/content route, OpenAI provider, ElevenLabs provider
- 형식 예시: `[04:12:03] INFO contents.assets.generating content_id=... progress=1/10 asset_id=...`
- 로컬 로그 파일은 `.gitignore` 대상이다. `backend/logs/`, `backend/*.log`, `backend/*.err`는 커밋하지 않는다.

## 주요 상태값

콘텐츠 상태:

- `draft`
- `generating`
- `teacher_review`
- `revision_requested`
- `approved`
- `published`
- `archived`

교사 대시보드 단계:

- `material_generation`
- `material_review`
- `learning`
- `feedback`

학생 미션 원칙:

- 학생 API는 `published` 콘텐츠만 반환한다.
- 학생 플레이 중 1~3단계 콘텐츠는 AI가 새로 생성하거나 바꾸지 않는다.
- 4단계 realtime 세션은 승인된 `RealtimePracticeSpec`이 있는 stage에서만 만든다.

Asset generation job 응답 예시:

```json
{
  "jobId": "asset_job_abc123",
  "contentId": "content_student_learning_fraction_001",
  "status": "running",
  "queuedAt": "2026-05-05T12:00:00+00:00",
  "startedAt": "2026-05-05T12:00:01+00:00",
  "completedAt": null,
  "totalCount": 10,
  "completedCount": 4,
  "failedCount": 0,
  "generatedCount": 4,
  "assets": [
    {
      "assetId": "asset_content_001_stage_2",
      "assetRole": "stage_2",
      "assetType": "image",
      "status": "running",
      "qaStatus": "pending",
      "approvalStatus": "pending"
    }
  ]
}
```
