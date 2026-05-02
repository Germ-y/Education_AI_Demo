# EduYJ Agent Start Guide

This repository uses three long-lived branches:

- `frontend`: frontend implementation work.
- `backend`: backend, API, DB, seed, and collaboration-contract work.
- `dev`: integration and verification branch.

Before changing files, run:

```bash
git status --short --branch
```

Do not revert another person's uncommitted or unrelated work.

## Documents To Read

Start from these documents when the branch contains them:

1. [GOAL.md](GOAL.md) - 전체 목표
2. [docs/README.md](docs/README.md) - 문서 폴더 구조
3. [docs/common/00-agent-navigation.md](docs/common/00-agent-navigation.md) - 작업별 문서 지도
4. [docs/common/01-collaboration-contract.md](docs/common/01-collaboration-contract.md) - 프론트/백엔드 협업 계약
5. [docs/common/02-branch-handoff-contract.md](docs/common/02-branch-handoff-contract.md) - 브랜치 간 handoff 기준
6. [docs/common/10-pr-feature-review-contract.md](docs/common/10-pr-feature-review-contract.md) - 기능 단위 PR 기준
7. [docs/common/11-feature-start-checklist.md](docs/common/11-feature-start-checklist.md) - 기능 시작 체크리스트
8. [docs/common/12-schema-contract.md](docs/common/12-schema-contract.md) - 도메인 온보딩 및 스키마 계약
9. [docs/common/03-implementation-backlog.md](docs/common/03-implementation-backlog.md) - 현재 백로그

Frontend work starts from [docs/frontend/00-frontend-team-guide.md](docs/frontend/00-frontend-team-guide.md).
Backend work starts from [docs/backend/00-backend-team-guide.md](docs/backend/00-backend-team-guide.md).

## Task Router

| 작업 유형 | 먼저 볼 문서 | 사용할 스킬 |
| --- | --- | --- |
| 프론트 화면/UX | [docs/frontend/00-frontend-team-guide.md](docs/frontend/00-frontend-team-guide.md) | [eduyj-monorepo-collaboration](.agents/skills/eduyj-monorepo-collaboration/SKILL.md) |
| 백엔드 API/DB/seed | [docs/backend/00-backend-team-guide.md](docs/backend/00-backend-team-guide.md) | [eduyj-backend-contracts](.agents/skills/eduyj-backend-contracts/SKILL.md) |
| 콘텐츠/이미지/realtime | [docs/common/05-ai-content-template-spec.md](docs/common/05-ai-content-template-spec.md) | [eduyj-content-package](.agents/skills/eduyj-content-package/SKILL.md) |
| 프론트/백엔드 동시 변경 | [docs/common/02-branch-handoff-contract.md](docs/common/02-branch-handoff-contract.md) | [eduyj-monorepo-collaboration](.agents/skills/eduyj-monorepo-collaboration/SKILL.md) |
| PR 작성/리뷰 | [docs/common/10-pr-feature-review-contract.md](docs/common/10-pr-feature-review-contract.md) | [eduyj-monorepo-collaboration](.agents/skills/eduyj-monorepo-collaboration/SKILL.md) |
| 기능 시작 회의 | [docs/common/11-feature-start-checklist.md](docs/common/11-feature-start-checklist.md) | [eduyj-monorepo-collaboration](.agents/skills/eduyj-monorepo-collaboration/SKILL.md) |
| 스키마/API 계약 | [docs/common/12-schema-contract.md](docs/common/12-schema-contract.md) | [eduyj-backend-contracts](.agents/skills/eduyj-backend-contracts/SKILL.md) |
| 장기 목표 이어가기 | [docs/common/03-implementation-backlog.md](docs/common/03-implementation-backlog.md) | [eduyj-agent-loop](.agents/skills/eduyj-agent-loop/SKILL.md) |

## Hard Rules

- Student missions have exactly 4 stages.
- Reflection is not a 5th stage.
- Stages 1-3 use approved static content.
- Stage 4 is the only realtime stage.
- MVP starts from seeded domain read models, not signup or general login.
- Do not add video generation, ffmpeg, or Remotion pipelines.
- Do not expose provider secrets or OpenAI API keys in `frontend/`.
- Do not make image-generation failure UI look like a seed asset replacement.
- Do not show diagnostic labels or stigmatizing wording to students.

## Next.js Warning

<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes. APIs, conventions, and file structure may differ from your training data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing frontend code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Verification

Frontend changes:

```bash
cd frontend
npm run lint
```

Backend changes:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

Integration changes should follow [docs/common/02-branch-handoff-contract.md](docs/common/02-branch-handoff-contract.md).
