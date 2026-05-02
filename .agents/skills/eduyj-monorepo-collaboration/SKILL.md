---
name: eduyj-monorepo-collaboration
description: EduYJ 레포에서 프론트엔드와 백엔드가 함께 바뀌는 작업을 할 때 사용한다. API 계약, 문서, 브랜치 기준, 파일 소유권, 작업 인수인계, Next.js/FastAPI/AI 콘텐츠/공공데이터 협업 순서를 맞춘다.
---

# EduYJ 모노레포 협업 스킬

먼저 읽을 문서:

1. `AGENTS.md`
2. `docs/common/01-collaboration-contract.md`
3. `docs/common/02-branch-handoff-contract.md`
4. `docs/common/00-agent-navigation.md`
5. 지금 작업과 관련된 상세 문서

## 1. 작업 영역 먼저 정하기

작업 시작 전에 어느 영역을 고칠지 정한다.

- 프론트 작업: `frontend/`
- 백엔드 작업: `backend/`
- API 계약 작업: `docs/common/08-rest-api-spec.md`, `backend/app/domain/schemas.py`, `frontend/lib/demo-data.ts`
- AI 콘텐츠 작업: `docs/common/05-*`, `docs/common/06-*`, `docs/common/07-*`, `backend/scripts/`
- 작업 규칙/문서 작업: `AGENTS.md`, `GOAL.md`, `.agents/skills/`, `docs/common/00-*`, `docs/common/03-*`

프론트와 백엔드가 같이 바뀌면 코드보다 문서를 먼저 고친다.

## 2. 계약 변경 순서

API 응답, 콘텐츠 JSON, seed 데이터, 프론트 mock 데이터가 같이 바뀌면 아래 순서로 작업한다.

```text
문서 스펙 수정
백엔드 스키마/API 수정
백엔드 seed 수정
프론트 소비 코드 수정
테스트/lint 실행
백로그 상태 갱신
handoff 문서 확인
커밋
```

## 3. 지켜야 할 것

- 프론트 작업은 `frontend` 브랜치에서 push한다.
- 백엔드 작업은 `backend` 브랜치에서 push한다.
- 통합 검증은 `dev` 브랜치에서 한다.
- provider key는 `frontend/`에 노출하지 않는다.
- 학생 미션은 4단계다. 회고는 5단계가 아니다.
- 4단계가 realtime이다. 1~3단계는 승인된 정적 템플릿이다.
- 영상 파이프라인을 추가하지 않는다.
- 이미지 생성 실패를 seed asset으로 대체하지 않는다.
- `.env`, `.venv`, `node_modules`, cache는 커밋하지 않는다.

## 4. 검증

문서/스킬만 바꾼 경우:

```bash
git diff --check
```

백엔드를 바꾼 경우:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

프론트를 바꾼 경우:

```bash
cd frontend
npm run lint
```

## 5. 작업 끝날 때 남길 내용

```text
목표:
수정한 경로:
API/데이터 계약 변경 여부:
검증:
남은 위험:
다음 작업:
커밋:
```
