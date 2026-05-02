---
name: eduyj-monorepo-collaboration
description: Use when working across the EduYJ frontend/backend monorepo, coordinating API contracts, shared docs, branch ownership, handoffs, or multi-agent collaboration between Next.js, FastAPI, AI content, and public-data work.
---

# EduYJ Monorepo Collaboration

Read first:

1. `AGENTS.md`
2. `docs/14-collaboration-contract.md`
3. `docs/00-agent-navigation.md`
4. The task-specific spec selected from the navigation table

## Decide Ownership

Before editing, classify the task:

- Frontend: `frontend/`
- Backend: `backend/`
- Contract: `docs/12-rest-api-spec.md`, `backend/app/domain/schemas.py`, `frontend/lib/demo-data.ts`
- AI Content: `docs/04-*`, `docs/07-*`, `docs/09-*`, `backend/scripts/`
- Harness: `AGENTS.md`, `GOAL.md`, `.agents/skills/`, `docs/00-*`, `docs/13-*`

If a task crosses areas, update the contract docs before code.

## Contract Change Order

```text
docs spec
backend schema/API
backend seed
frontend consumer/mock
tests/lint
backlog update
commit
```

## Guardrails

- Do not expose provider keys in `frontend/`.
- Keep mission stages at 4; reflection is not stage 5.
- Stage 4 is realtime; stages 1~3 stay approved static templates.
- Do not add video pipelines.
- Do not replace failed image generation with seed assets; `gpt-image-2` generation failure should fail visibly.
- Do not commit `.env`, `.venv`, `node_modules`, or caches.

## Validation

For docs/harness:

```bash
git diff --check
```

For backend:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

For frontend:

```bash
cd frontend
npm run lint
```

## Handoff

End with:

```text
목표:
수정 경로:
계약 변경:
검증:
남은 위험:
다음 작업:
커밋:
```
