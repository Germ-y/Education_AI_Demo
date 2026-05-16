# EduYJ 에이전트 시작 안내

새 세션은 이 파일을 먼저 읽고, 아래 문서만 확인합니다.

1. [GOAL.md](GOAL.md)
2. [docs/GOAL_CONTEXT.md](docs/GOAL_CONTEXT.md)
3. DB/asset 작업이면 [backend/data/README.md](backend/data/README.md)

## 저장소 구조

- `frontend/`: Next.js 학생/교사 화면
- `backend/`: FastAPI API 서버, 도메인 스키마, AI workflow, SQLite 공유 DB
- `docs/`: 현재 기능/인수인계/남은 작업을 담은 단일 기준 문서
- `.agents/`: 프로젝트 전용 Codex 스킬

## 현재 작업 기준

- 팀 기준 브랜치는 `main`입니다.
- 새 작업은 `main`에서 `frontend/작업명` 또는 `backend/작업명` 브랜치를 따서 진행합니다.
- 작업 전 `git status --short --branch`로 브랜치와 변경사항을 확인합니다.
- 다른 사람의 변경을 되돌리지 않습니다.
- 커밋 메시지는 `feat : 내용`, `fix : 내용`, `docs : 내용`, `chore : 내용` 형식의 한국어를 씁니다.
- 현재 공유 DB는 SQLite입니다. PostgreSQL migration은 별도 백엔드 작업입니다.
- DB를 공유 기준으로 갱신할 때는 `backend/data/eduyj_demo.db`, `backend/data/eduyj_demo_dump.sql`, `backend/generated/assets/students/**`를 같은 커밋에 넣습니다.

## 제품 규칙

- 학생 미션은 4단계입니다.
- 1~3단계는 승인된 정적 템플릿 JSON만 사용합니다.
- 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 발화 연습입니다.
- 회고는 단계 수에 포함하지 않고 후속 기록으로 저장합니다.
- 학생에게 노출되는 AI 생성 콘텐츠는 자동 검수와 교사 승인 뒤에만 배포합니다.
- 영상 생성 파이프라인은 범위에서 제외합니다.
- 공공데이터는 학생 진단값이 아니라 교육과정, 학사일정, 지역 맥락, 통계 근거로 사용합니다.

## 프론트엔드 규칙

<!-- BEGIN:nextjs-agent-rules -->
# 이 프로젝트의 Next.js는 기존 기억과 다를 수 있음

이 버전은 API, 관례, 파일 구조가 기존 학습 기억과 다를 수 있습니다. 프론트엔드 코드를 수정하기 전 `frontend/node_modules/next/dist/docs/`의 관련 가이드를 확인하고, deprecation 안내를 따릅니다.
<!-- END:nextjs-agent-rules -->

## 검증 기준

문서 작업:

```bash
git diff --check
```

백엔드 작업:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
```

프론트 작업:

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```
