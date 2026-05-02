---
name: eduyj-backend-contracts
description: Use when implementing EduYJ backend APIs, database schema, seed data, public-data sync, AI run logging, or approval/runtime contracts.
---

# EduYJ Backend Contracts

Canonical docs:

- `docs/05-backend-feature-spec.md`
- `docs/10-data-api-requirements.md`
- `docs/11-database-schema-spec.md`
- `docs/12-rest-api-spec.md`
- `docs/13-implementation-backlog.md`

Implementation order:

1. Domain types and schema validation
2. DB migrations
3. Demo seed
4. Teacher dashboard API
5. AI generation workflow
6. Image asset pipeline
7. Teacher approval/publish
8. Student runtime
9. Stage-4 realtime
10. Review/memory update
11. Public data sync

Contract rules:

- `mission_contents.total_steps` is always 4.
- `content_stages.step` is 1~4 only.
- Realtime session creation requires `stage.step == 4` and an approved `realtime_spec_json`.
- Student APIs return only approved/published content.
- AI provider keys never leave the server.
- Public data raw records and normalized records are stored separately.
- Approval, memory updates, and student-data access create audit logs.
