# 브랜치 간 handoff 계약

이 문서는 `frontend`, `backend`, `dev` 브랜치 사이에서 변경사항을 주고받는 기준이다.

## 1. 기본 흐름

```text
frontend 브랜치에서 프론트 작업
backend 브랜치에서 백엔드 작업
각자 브랜치에서 작은 커밋으로 작업 로그 관리
검증 후 각자 브랜치 push
dev 브랜치에서 pull/merge
dev 브랜치에서 통합 검증
검증 결과를 문서/PR에 남김
각자 브랜치로 돌아가 다음 작업
```

handoff는 단순 알림이 아니라 검수와 승인 흐름이다.
PR을 올릴 때는 이 문서의 승인 상태를 [10-pr-feature-review-contract.md](10-pr-feature-review-contract.md)의 PR 설명에 연결한다.

```text
1. 변경한 작업자가 먼저 이 문서의 체크리스트를 읽고 자체 검수한다.
2. 상대 파트가 확인해야 할 내용을 push/PR 설명에 적는다.
3. 상대 파트 작업자가 문서와 코드를 확인하고 승인 또는 수정 요청을 남긴다.
4. 승인 기록이 있으면 dev 브랜치 통합으로 넘어간다.
```

승인 기록은 길게 쓰지 않는다. 아래 정도면 충분하다.

```text
검수자:
검수 범위:
승인 상태: 승인 / 수정 요청 / 보류
수정 요청:
```

## 2. 백엔드가 push하면 프론트가 확인할 문서

백엔드가 API, seed, 콘텐츠 JSON, 상태값을 바꿨다면 프론트는 아래 문서를 먼저 확인한다.

| 확인 순서 | 문서 | 프론트가 볼 것 |
| --- | --- | --- |
| 1 | [08-rest-api-spec.md](08-rest-api-spec.md) | API path, request/response, status code, 인증 헤더 |
| 2 | [05-ai-content-template-spec.md](05-ai-content-template-spec.md) | 학생 미션 단계, 템플릿 타입, 선택지/정답 구조 |
| 3 | [06-realtime-practice-spec.md](06-realtime-practice-spec.md) | 4단계 realtime 진입 조건, 세션 생성 응답 |
| 4 | [07-image-content-package-spec.md](07-image-content-package-spec.md) | 대표 이미지/단계별 이미지 asset 역할 |
| 5 | [../backend/04-demo-seed-auth-registration-plan.md](../backend/04-demo-seed-auth-registration-plan.md) | 데모 로그인 계정, 학생 access code, seed 데이터 |

프론트에서 같이 확인할 코드:

```text
frontend/lib/demo-data.ts
frontend/app/student/*
frontend/app/dashboard*
```

백엔드 push 메시지나 PR 설명에는 아래를 남긴다.

```text
프론트 확인 필요:
- 변경 API:
- 변경 응답 필드:
- 변경 seed:
- 변경 상태값:
- 프론트에서 확인할 화면:
```

프론트 작업자는 승인 전에 아래를 직접 확인한다.

```text
- 문서에 적힌 API path와 실제 호출 path가 맞는가
- request/response 필드가 프론트 타입이나 mock 데이터와 충돌하지 않는가
- enum/status 값이 화면 분기와 맞는가
- MissionContent 1~4단계 구조가 유지되는가
- 이미지 asset role이 화면에서 필요한 위치와 맞는가
- seed 계정, 학생 access code, 데모 학생 id가 화면 테스트에 충분한가
```

프론트 승인 기준:

```text
승인: 문서와 프론트 연결 지점이 일치하고 화면 수정 범위가 명확함
수정 요청: 응답 필드, 상태값, seed, 이미지 role 중 하나라도 프론트와 맞지 않음
보류: 실제 화면 확인에 필요한 서버 실행이나 seed 실행이 되지 않음
```

## 3. 프론트가 push하면 백엔드가 확인할 문서

프론트가 화면 흐름, 필요한 데이터, 새 API 요구사항을 바꿨다면 백엔드는 아래 문서를 먼저 확인한다.

| 확인 순서 | 문서 | 백엔드가 볼 것 |
| --- | --- | --- |
| 1 | [../frontend/00-frontend-team-guide.md](../frontend/00-frontend-team-guide.md) | 화면 구조, 프론트가 기대하는 데이터 흐름 |
| 2 | [08-rest-api-spec.md](08-rest-api-spec.md) | 새로 필요한 API, 기존 API와의 차이 |
| 3 | [04-child-content-experience.md](04-child-content-experience.md) | 학생 화면 단계와 UX 요구 |
| 4 | [01-collaboration-contract.md](01-collaboration-contract.md) | 계약 변경 순서와 검증 기준 |

백엔드에서 같이 확인할 코드:

```text
backend/app/domain/schemas.py
backend/app/api/routes/*
backend/app/data/demo_data.py
backend/tests/*
```

프론트 push 메시지나 PR 설명에는 아래를 남긴다.

```text
백엔드 확인 필요:
- 새로 필요한 API:
- 화면에서 기대하는 응답 필드:
- 새 상태값/enum:
- seed에 필요한 데이터:
- 백엔드에서 확인할 사용자 흐름:
```

백엔드 작업자는 승인 전에 아래를 직접 확인한다.

```text
- 프론트가 요구한 API가 기존 REST 계약으로 해결 가능한가
- 새 API가 필요하다면 path, request, response가 문서에 먼저 적혔는가
- 새 응답 필드가 Pydantic schema와 DB 모델에 반영 가능한가
- seed 데이터만으로 프론트 화면 시나리오를 재현할 수 있는가
- 학생 미션 4단계와 realtime 진입 조건을 깨지 않는가
- provider secret이나 AI 생성 로직을 프론트로 넘기지 않는가
```

백엔드 승인 기준:

```text
승인: 프론트 요구사항이 API/DB/seed 설계와 충돌하지 않고 구현 범위가 명확함
수정 요청: 필요한 응답 필드, 상태값, seed 조건, realtime 조건이 문서에 없음
보류: 요구 화면 흐름이 현재 4단계 콘텐츠 계약과 충돌함
```

## 4. dev 브랜치 통합 체크리스트

`dev` 브랜치에서 통합하기 전에 상대 파트 승인 기록이 있어야 한다.

승인 기록이 없는 경우에는 dev 통합으로 넘어가지 않고, 이 문서의 handoff 항목을 먼저 채운다.

승인 후 아래 순서로 확인한다.

```bash
git status --short --branch
git pull origin dev
git merge origin/frontend
git merge origin/backend
```

충돌이 없거나 충돌 해결 후 검증한다.

백엔드:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

프론트:

```bash
cd frontend
npm run lint
```

통합 smoke:

```text
1. 백엔드 서버 실행
2. 프론트 서버 실행
3. 교사 대시보드 진입
4. 학생 미션 진입
5. 1~3단계 진행
6. 4단계 realtime session 생성
```

## 5. 문서 수정 의무

다음 중 하나라도 바뀌면 반드시 문서를 같이 수정한다.

- API path, request, response
- enum 또는 status 값
- 학생 미션 단계 구조
- 이미지 asset 역할
- seed 계정/학생/access code
- 프론트 화면 흐름
- realtime session 생성 조건

수정 위치:

```text
공통 계약: docs/common/*
프론트 전용 설명: docs/frontend/*
백엔드 전용 설명: docs/backend/*
```

## 6. push 전 확인

작업 중간에는 커밋만 남기고, push는 handoff 가능한 상태에서 마지막에 한다.

```bash
git status --short --branch
git diff --check
git log --oneline --decorate -n 8
```

push 메시지나 PR 설명에는 다음을 남긴다.

```text
이번 push 목적:
주요 커밋:
프론트 확인 필요:
백엔드 확인 필요:
실행한 검증:
```
