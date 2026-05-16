---
name: eduyj-monorepo-collaboration
description: EduYJ 레포에서 프론트엔드와 백엔드가 함께 바뀌는 작업을 할 때 사용한다. API 계약, DB dump, 브랜치 기준, 작업 인수인계를 맞춘다.
---

# EduYJ 모노레포 협업 스킬

먼저 읽을 문서:

1. `AGENTS.md`
2. `docs/GOAL_CONTEXT.md`
3. `backend/data/README.md`

## 작업 영역

- 프론트 작업: `frontend/`
- 백엔드 작업: `backend/`
- API 계약: `docs/GOAL_CONTEXT.md`, `backend/app/domain/schemas.py`, `frontend/lib/api/contracts.ts`
- DB/seed/asset 인수인계: `backend/data/README.md`, `backend/data/eduyj_demo.db`, `backend/data/eduyj_demo_dump.sql`, `backend/generated/assets/students/**`
- 진행상황/예정사항/병목: `docs/GOAL_CONTEXT.md`
- 작업 규칙: `AGENTS.md`, `GOAL.md`, `.agents/skills/`

프론트와 백엔드가 같이 바뀌면 API 계약과 seed 데이터가 먼저 맞아야 한다.

## 지켜야 할 것

- 통합 기준은 `main` 브랜치다.
- 프론트/백엔드 작업은 `main`에서 `frontend/작업명`, `backend/작업명` 브랜치를 따서 진행한다.
- 작업 중에는 작은 커밋을 쌓고, 검증 후 push한다.
- API field, enum, MissionContent 구조가 바뀌면 `docs/GOAL_CONTEXT.md`를 갱신한다.
- provider key는 `frontend/`에 노출하지 않는다.
- 학생 미션은 4단계다.
- 4단계가 realtime이다.
- 1~3단계는 승인된 정적 템플릿이다.
- 영상 파이프라인을 추가하지 않는다.
- 이미지 생성 실패를 seed asset으로 대체하지 않는다.
- `.env`, `.venv`, `node_modules`, cache는 커밋하지 않는다.
- 현재 공유 DB는 SQLite다. PostgreSQL migration은 별도 백엔드 작업으로 검증한다.
- DB가 참조하는 generated asset은 DB/dump와 같은 커밋에 포함한다.

## 검증

문서/스킬만 바꾼 경우:

```bash
git diff --check
```

백엔드를 바꾼 경우:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
```

프론트를 바꾼 경우:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

## 작업 끝날 때 남길 내용

```text
목표:
수정한 경로:
API/데이터 계약 변경 여부:
검증:
남은 위험:
다음 작업:
커밋:
```
