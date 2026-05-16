# EduYJ FastAPI Backend

FastAPI 백엔드, 도메인 스키마, AI 생성 workflow, 데모 SQLite DB가 있는 폴더입니다.

## 실행

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 4000
```

기본 API는 `http://localhost:4000`에서 실행됩니다.

## DB 기준

- 현재 팀 공유 기준은 `data/eduyj_demo.db` SQLite 파일입니다.
- `data/eduyj_demo_dump.sql`은 같은 상태를 복원하기 위한 SQLite dump입니다.
- PostgreSQL은 목표 운영 DB지만, 현재 main 기준에서는 migration 스크립트가 아직 없습니다.
- DB가 참조하는 이미지/음성은 `generated/assets/students/**`에 있습니다. DB와 asset은 같이 이동해야 합니다.

복원:

```bash
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

자세한 기준은 [data/README.md](data/README.md)를 봅니다.

## 검증

```bash
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
sqlite3 data/eduyj_demo.db "pragma integrity_check;"
```
