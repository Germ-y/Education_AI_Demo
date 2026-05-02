# EduYJ FastAPI Backend

이 폴더는 AI 맞춤형 교육 지원 서비스의 FastAPI 백엔드 구현 위치입니다.

## Quick Start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

## Verification

```bash
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

기본 API는 `http://localhost:4000`에서 실행됩니다.

## Demo DB

공유용 SQL dump는 [data/eduyj_demo_dump.sql](data/eduyj_demo_dump.sql)에 둔다.
로컬 SQLite DB인 `data/eduyj_demo.db`는 git 추적 대상이 아니다.

```bash
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

자세한 복원 기준은 [data/README.md](data/README.md)를 본다.
