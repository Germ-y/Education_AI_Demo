# EduYJ AI Education Demo

영주 공공데이터 공모전용 AI 교육 지원 데모입니다.

## 기준 브랜치

- `dev`: 프론트/백엔드 통합 검증 기준
- `frontend`: 프론트 단독 작업 기준
- `backend`: 백엔드 단독 작업 기준

팀원이 이어받을 때는 먼저 현재 브랜치와 변경사항을 확인합니다.

```bash
git status --short --branch
```

## 핵심 문서

- [AGENTS.md](AGENTS.md): 새 작업자가 먼저 읽는 실행 규칙
- [GOAL.md](GOAL.md): 현재 데모 목표와 남은 일
- [docs/HANDOFF.md](docs/HANDOFF.md): 진행상황, 설정, DB 복원, 검증, 다음 작업
- [docs/API.md](docs/API.md): 최신 REST API 요약
- [backend/data/README.md](backend/data/README.md): 데모 DB dump/seed 복원 방법

## 실행

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

- 프론트: `http://localhost:3000`
- 백엔드: `http://localhost:4000`

## 데모 DB

로컬 DB는 git에 올리지 않고, 재현 가능한 SQL dump만 추적합니다.

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

seed로 다시 만들 때:

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

## 검증

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
```

문서만 바꾼 경우:

```bash
git diff --check
```
