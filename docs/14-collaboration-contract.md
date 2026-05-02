# Collaboration Contract

이 문서는 `frontend/`와 `backend/`가 같은 레포를 바라볼 때 작업자가 서로의 변경을 덜 밟도록 만든 협업 계약이다.

## 1. 기본 원칙

- 한 작업은 가능한 한 하나의 목적과 하나의 소유 영역을 가진다.
- API, 스키마, seed, 화면이 함께 바뀌는 작업은 계약 변경으로 취급한다.
- 계약 변경은 문서 → 백엔드 스키마/API → seed → 프론트 소비 코드 → 검증 순서로 진행한다.
- 프론트와 백엔드가 동시에 같은 파일을 고치지 않도록 작업 시작 전에 소유 파일을 명시한다.
- `node_modules`, `.venv`, cache, 실제 `.env`는 커밋하지 않는다.

## 2. 소유 영역

| 영역 | 주요 경로 | 소유 기준 |
| --- | --- | --- |
| Frontend | `frontend/` | Next.js 화면, 라우팅, UI 상태, 프론트 데모 데이터 |
| Backend | `backend/` | FastAPI API, Pydantic/SQLAlchemy 스키마, seed, AI provider adapter |
| Contracts | `docs/12-rest-api-spec.md`, `backend/app/domain/schemas.py`, `frontend/lib/demo-data.ts` | API 응답 형태, enum, stage/template 데이터 모양 |
| AI Content | `docs/04-ai-content-template-spec.md`, `docs/07-realtime-practice-spec.md`, `docs/09-image-content-package-spec.md`, `backend/scripts/` | 4단계 콘텐츠, 이미지 패키지, realtime spec |
| Public Data | `docs/06-public-data-strategy.md`, `docs/10-data-api-requirements.md`, backend public-data routes/services | 공공데이터 source registry, sync, snapshot |
| Agent Harness | `AGENTS.md`, `GOAL.md`, `.agents/skills/`, `docs/00-agent-navigation.md`, `docs/13-implementation-backlog.md` | 장기 작업 루프, 스킬, 링크 지도, backlog |

## 3. 계약 변경 순서

API나 데이터 모양을 바꿀 때는 아래 순서를 따른다.

```text
1. docs/12-rest-api-spec.md 또는 관련 spec 문서 갱신
2. backend/app/domain/schemas.py 또는 backend route/service 갱신
3. backend/app/data/demo_data.py seed 갱신
4. frontend/lib/demo-data.ts 또는 API client 소비 코드 갱신
5. 백엔드 테스트, 프론트 lint, 필요 시 화면 smoke test 실행
6. docs/13-implementation-backlog.md 상태 갱신
```

예외:

- 순수 UI 배치 변경은 프론트 영역만 수정해도 된다.
- 순수 백엔드 내부 리팩터는 API 응답 형태가 바뀌지 않으면 프론트 변경 없이 진행할 수 있다.
- AI provider prompt만 바꾸는 경우에도 생성 결과 JSON 필드가 바뀌면 계약 변경으로 본다.

## 4. 병렬 작업 규칙

동시에 작업할 때는 파일 단위로 나눈다.

- 프론트 작업자는 `frontend/`만 수정한다. API mock 형태가 필요하면 먼저 contract 문서에 추가한다.
- 백엔드 작업자는 `backend/`와 관련 `docs/`만 수정한다. 프론트 소비 코드 수정이 필요하면 별도 커밋으로 분리한다.
- 문서/스킬 작업자는 `AGENTS.md`, `GOAL.md`, `docs/`, `.agents/`를 수정하고 코드 변경은 하지 않는다.
- 같은 파일을 두 작업자가 수정해야 하면 먼저 한쪽이 계약 문서를 고정하고, 다른 쪽이 그 계약을 따라간다.

## 5. 금지 패턴

- 프론트에서 OpenAI API key나 provider secret을 직접 사용하지 않는다.
- 학생 플레이 중 1~3단계 콘텐츠를 AI가 새로 분석하거나 후처리하게 만들지 않는다.
- 영상 생성, f[f]mpeg, R[e]motion 파이프라인을 핵심 범위에 추가하지 않는다.
- 이미지 생성 실패를 seed asset으로 조용히 대체하지 않는다.
- `frontend/package-lock.json`은 의존성 변경 없이 건드리지 않는다.
- `backend/requirements.txt`는 실제 import 또는 실행에 필요한 경우에만 바꾼다.

## 6. 검증 매트릭스

문서/스킬만 바꾼 경우:

```bash
rg -n "5[단]계|마지막[ ]실시간|마지막[ ]realtime|R[e]motion|f[f]mpeg|f[a]llbackUsed|candidate[M]odels" README.md AGENTS.md GOAL.md docs .agents backend examples
git diff --check
```

백엔드 변경이 있는 경우:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

프론트 변경이 있는 경우:

```bash
cd frontend
npm run lint
```

통합 흐름 변경이 있는 경우:

```text
1. backend 서버 실행: http://localhost:4000
2. frontend 서버 실행: http://localhost:3000
3. 교사 데모 로그인/학생 목록 확인
4. 학생 오늘 미션 조회
5. 1~3단계 static template 진행
6. 4단계 realtime session mock 또는 실제 session 생성
```

## 7. 핸드오프 포맷

작업을 끝낼 때 다음 내용을 남긴다.

```text
목표:
수정 경로:
계약 변경:
실행한 검증:
남은 위험:
다음 추천 작업:
커밋:
```

## 8. 브랜치 기준

- 현재 공모전 데모 기준 통합 작업 브랜치는 `backend`다.
- `frontend` 브랜치는 프론트 전용 변경의 출처로만 취급하고, 통합 변경은 `backend` 브랜치에 반영한다.
- 다른 브랜치의 변경을 가져올 때는 먼저 `git status --short --branch`로 깨끗한지 확인하고, 복사/체리픽 후 통합 검증을 다시 수행한다.
