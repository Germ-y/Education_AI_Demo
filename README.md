# EduYJ AI Education Demo

영주 공공데이터 공모전용 AI 교육 지원 데모입니다.

## 지금 팀 기준

- 기준 브랜치: `main`
- 작업 루트: `/Users/gimdonghyeon/Desktop/educationforyeongju-backend`
- 프론트 배포 터널: <https://eduYj.summit1123.co.kr>
- 백엔드 배포 터널: <https://eduYjapp.summit1123.co.kr>
- 로컬 프론트: `http://localhost:3000`
- 로컬 백엔드: `http://localhost:4000`
- 현재 공유 DB는 SQLite입니다. PostgreSQL은 목표 환경이지만, 운영 migration은 아직 별도 작업입니다.

프론트/백엔드 작업자는 `main`에서 새 브랜치를 따서 작업합니다.

```bash
git checkout main
git pull origin main
git checkout -b frontend/작업명
# 또는
git checkout -b backend/작업명
```

## 먼저 읽을 문서

- [AGENTS.md](AGENTS.md): 작업 규칙
- [docs/GOAL_CONTEXT.md](docs/GOAL_CONTEXT.md): 현재 기능, DB 상태, 남은 작업, API 흐름
- [backend/data/README.md](backend/data/README.md): DB/asset 복원과 공유 기준

## 실행

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## 현재 공유 DB 복원

`backend/data/eduyj_demo.db`와 `backend/generated/assets/students/**`를 함께 추적합니다. 팀원이 `main`을 받으면 현재 배포 화면의 학생, 콘텐츠, 이미지, 음성 파일을 그대로 확인할 수 있어야 합니다.

DB가 꼬이면 dump로 복원합니다.

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
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
npm run build
```

DB/asset:

```bash
sqlite3 backend/data/eduyj_demo.db "pragma integrity_check;"
```
