# EduYJ AI Education Demo

Integrated workspace for the EduYJ AI education demo.

## Branches

- `frontend`: Next.js student and teacher screens.
- `backend`: FastAPI API, schema, seed data, and collaboration documents.
- `dev`: integration branch for frontend/backend verification.

## Project Structure

```text
frontend/       Next.js frontend
backend/        FastAPI backend
docs/common/    shared frontend/backend contracts
docs/frontend/  frontend working guide
docs/backend/   backend working guide
.agents/        Codex/Ralph working skills
examples/       generated content samples
assets/         source/reference assets
```

## First Documents

1. [AGENTS.md](AGENTS.md)
2. [GOAL.md](GOAL.md)
3. [docs/README.md](docs/README.md)
4. [docs/common/00-agent-navigation.md](docs/common/00-agent-navigation.md)
5. [docs/common/01-collaboration-contract.md](docs/common/01-collaboration-contract.md)
6. [docs/common/02-branch-handoff-contract.md](docs/common/02-branch-handoff-contract.md)
7. [docs/common/13-current-handoff-summary.md](docs/common/13-current-handoff-summary.md)

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`.

Verification:

```bash
cd frontend
npm run lint
```

## Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

The API runs at `http://localhost:4000`.

Verification:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

`app.data.seed_demo` creates the SQLAlchemy schema and writes the demo seed to `DATABASE_URL`.
For the shared demo SQLite path:

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

The local `.db` file is ignored by git. A reproducible SQL dump is tracked at
[backend/data/eduyj_demo_dump.sql](backend/data/eduyj_demo_dump.sql), with restore notes in
[backend/data/README.md](backend/data/README.md).

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

## Contract Notes

- Student missions are 4 stages.
- Reflection is not stage 5.
- Stages 1-3 are approved static content.
- Stage 4 is realtime practice.
- Frontend/backend contract changes should be reflected in `docs/common/`.
