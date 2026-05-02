# 협업 계약

이 문서는 프론트엔드와 백엔드를 같은 레포에서 같이 작업할 때의 약속이다.
목표는 단순하다. 누가 어떤 파일을 고쳐야 하는지, API 모양이 바뀔 때 어떤 순서로 맞춰야 하는지, 작업 끝나고 무엇을 검증해야 하는지 헷갈리지 않게 만든다.

## 1. 기본 원칙

- 한 작업은 가능한 한 하나의 목적만 가진다.
- 한 작업은 가능한 한 하나의 소유 영역만 수정한다.
- API 응답, 스키마, seed 데이터, 화면 데이터가 함께 바뀌면 이것은 `계약 변경`이다.
- 계약 변경은 `문서 → 백엔드 → seed → 프론트 → 검증` 순서로 진행한다.
- 작업 시작 전에 내가 건드릴 파일 범위를 먼저 정한다.
- 커밋은 작업 로그이므로 의미 단위마다 작게 남긴다.
- push는 작업 중간이 아니라, 검증과 handoff 준비가 끝난 마지막에 한다.
- `node_modules`, `.venv`, cache, 실제 `.env`는 커밋하지 않는다.

## 2. 폴더별 역할

| 영역 | 경로 | 맡는 일 |
| --- | --- | --- |
| 프론트엔드 | `frontend/` | Next.js 화면, 라우팅, UI 상태, 프론트용 데모 데이터 |
| 백엔드 | `backend/` | FastAPI API, Pydantic/SQLAlchemy 스키마, seed, AI 연동 |
| API 계약 | `docs/common/08-rest-api-spec.md`, `backend/app/domain/schemas.py`, `frontend/lib/demo-data.ts` | API 응답 형태, enum, 단계/템플릿 데이터 모양 |
| AI 콘텐츠 | `docs/common/05-ai-content-template-spec.md`, `docs/common/06-realtime-practice-spec.md`, `docs/common/07-image-content-package-spec.md`, `backend/scripts/` | 4단계 콘텐츠, 이미지 패키지, realtime 스펙 |
| 공공데이터 | `docs/common/09-public-data-strategy.md`, `docs/backend/05-data-api-requirements.md`, `backend/app/api/routes/public_data.py` | 공공데이터 출처, 동기화, snapshot |
| 작업 하네스 | `AGENTS.md`, `GOAL.md`, `.agents/skills/`, `docs/common/00-agent-navigation.md`, `docs/common/03-implementation-backlog.md` | 에이전트 작업 규칙, 스킬, 문서 지도, 백로그 |

## 3. API나 데이터 모양이 바뀔 때

API 응답 필드, 콘텐츠 JSON, 학생/교사 seed 데이터, 프론트 mock 데이터가 바뀌면 아래 순서를 따른다.

```text
1. 관련 문서를 먼저 수정한다.
   예: docs/common/08-rest-api-spec.md, docs/common/05-ai-content-template-spec.md

2. 백엔드 스키마/API를 수정한다.
   예: backend/app/domain/schemas.py, backend/app/api/routes/*

3. seed 데이터를 수정한다.
   예: backend/app/data/demo_data.py

4. 프론트가 읽는 데이터나 화면을 수정한다.
   예: frontend/lib/demo-data.ts, frontend/app/*

5. 백엔드 테스트와 프론트 lint를 돌린다.

6. docs/common/03-implementation-backlog.md에 상태를 남긴다.
```

예외:

- 화면 배치만 바꾸는 작업은 `frontend/`만 수정해도 된다.
- 백엔드 내부 리팩터가 API 응답을 바꾸지 않으면 프론트 수정은 필요 없다.
- 이미지 프롬프트만 바꿔도 생성 결과 JSON 필드가 바뀌면 계약 변경으로 본다.

## 4. 동시에 작업할 때

동시에 여러 명이나 여러 에이전트가 작업한다면 파일 단위로 나눈다.

- 프론트 작업자는 기본적으로 `frontend/`만 수정한다.
- 백엔드 작업자는 기본적으로 `backend/`와 관련 `docs/`만 수정한다.
- 문서/스킬 작업자는 `AGENTS.md`, `GOAL.md`, `docs/`, `.agents/`만 수정한다.
- 같은 파일을 둘 이상이 수정해야 하면, 먼저 문서에서 계약을 확정하고 그 다음 코드가 따라간다.
- 프론트 소비 코드 수정이 필요한 백엔드 작업은 가능하면 별도 커밋으로 분리한다.

## 5. 절대 넣지 말 것

- 프론트에서 OpenAI API key나 provider secret을 직접 쓰면 안 된다.
- 학생 플레이 1~3단계에서 AI가 새로 분석하거나 새 콘텐츠를 만들면 안 된다.
- 영상 생성, f[f]mpeg, R[e]motion 파이프라인을 핵심 범위에 넣지 않는다.
- 이미지 생성 실패를 seed asset으로 조용히 대체하지 않는다.
- 의존성을 바꾸지 않았는데 `frontend/package-lock.json`만 만지지 않는다.
- 실제 import나 실행에 필요하지 않은 패키지를 `backend/requirements.txt`에 넣지 않는다.

## 6. 검증 명령

문서나 스킬만 바꾼 경우:

```bash
rg -n "5[단]계|마지막[ ]실시간|마지막[ ]realtime|R[e]motion|f[f]mpeg|f[a]llbackUsed|candidate[M]odels" README.md AGENTS.md GOAL.md docs .agents backend examples
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

프론트와 백엔드를 같이 바꾼 경우:

```text
1. 백엔드 서버 실행: http://localhost:4000
2. 프론트 서버 실행: http://localhost:3000
3. 교사 데모 로그인 확인
4. 학생 목록/학생 상세 확인
5. 학생 오늘 미션 조회 확인
6. 1~3단계 정적 템플릿 진행 확인
7. 4단계 realtime session 생성 확인
```

## 7. 작업 끝날 때 남길 내용

최종 보고나 PR 설명에는 아래 내용을 남긴다.

```text
목표:
수정한 경로:
API/데이터 계약 변경 여부:
실행한 검증:
남은 위험:
다음 추천 작업:
커밋:
```

## 8. 커밋 로그 기준

커밋은 나중에 프론트/백엔드 팀원이 흐름을 따라갈 수 있는 작업 기록이어야 한다.

- 문서 구조 변경은 `docs : ...` 커밋으로 분리한다.
- API/DB/seed 변경은 기능 단위로 `feat : ...` 또는 `fix : ...` 커밋을 남긴다.
- 검증 스크립트나 테스트만 바꾸면 별도 커밋으로 분리한다.
- 여러 파일을 한 번에 고치더라도 목적이 다르면 커밋을 나눈다.
- push 전에는 최근 커밋 로그를 확인하고, PR/공유 메시지에 핵심 커밋을 적는다.

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

## 9. 브랜치 기준

- `frontend` 브랜치는 프론트 작업자가 작업하고 push하는 브랜치다.
- `backend` 브랜치는 백엔드 작업자가 작업하고 push하는 브랜치다.
- `dev` 브랜치는 프론트와 백엔드 변경을 합쳐 검증하는 통합 브랜치다.
- 각자 브랜치에서 작은 커밋을 쌓고, handoff 가능한 상태에서 마지막에 원격으로 push한다.
- 통합 담당자는 `dev` 브랜치에서 `frontend`, `backend` 변경을 pull/merge한다.
- `dev`에서 프론트 lint, 백엔드 테스트, 필요한 화면/API smoke test를 통과시킨다.
- 검증이 끝나면 각 작업자는 다시 자기 브랜치로 돌아가 다음 작업을 이어간다.
- 다른 브랜치 변경을 가져오기 전에는 `git status --short --branch`로 현재 작업트리가 깨끗한지 먼저 확인한다.

기본 흐름:

```text
frontend 브랜치에서 프론트 작업 -> push
backend 브랜치에서 백엔드 작업 -> push
dev 브랜치에서 두 브랜치 변경 통합
dev 브랜치에서 전체 검증
각자 frontend/backend 브랜치로 돌아가 다음 작업
```
