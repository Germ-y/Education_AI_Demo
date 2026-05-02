# 기능 시작 체크리스트

이 문서는 팀원이 모여 첫 기능을 시작할 때 하나씩 맞춰볼 실행 체크리스트다.
목표는 기능을 만들기 전에 프론트, 백엔드, 문서, PR 기준을 같은 눈높이로 맞추는 것이다.

## 1. 시작 전에 정할 것

기능을 시작하기 전에 아래 항목을 먼저 채운다.

```text
기능 이름:
기능 단위:
담당 브랜치: frontend / backend / dev
주 담당:
상대 파트 확인 필요 여부:
오늘 끝낼 최소 범위:
```

기능 단위는 [10-pr-feature-review-contract.md](10-pr-feature-review-contract.md)의 분류를 따른다.

## 2. 기능 단위 선택

처음부터 큰 흐름을 한 번에 구현하지 않는다. 아래 단위 중 하나를 고른다.

```text
teacher-dashboard
student-mission
realtime-practice
content-generation
orchestrator-memory
public-data
seed-auth
seeded-domain-read
school-public-context
teacher-case-read
docs-agent-harness
```

첫 구현은 가능하면 아래 순서를 추천한다.

```text
1. seeded-domain-read
2. school-public-context
3. teacher-case-read
4. student-mission
5. content-generation
6. realtime-practice
7. orchestrator-memory
8. public-data
```

이 순서는 데모를 빨리 보이게 하기 위한 추천이다.
회원가입/일반 로그인은 먼저 만들지 않고, seed된 사용자/학생/학교 데이터를 조회하는 것부터 맞춘다.
회의에서 화면 우선으로 가기로 하면 `teacher-dashboard`부터 시작해도 되지만, 그래도 [12-schema-contract.md](12-schema-contract.md)의 도메인 read model을 먼저 확인한다.

## 3. 작업 전 문서 체크

기능을 시작하기 전에 아래 문서를 체크한다.

| 체크 | 문서 | 확인할 것 |
| --- | --- | --- |
| [ ] | [00-agent-navigation.md](00-agent-navigation.md) | 작업 주제별로 볼 문서가 맞는가 |
| [ ] | [01-collaboration-contract.md](01-collaboration-contract.md) | 수정 영역과 계약 변경 순서가 맞는가 |
| [ ] | [02-branch-handoff-contract.md](02-branch-handoff-contract.md) | 상대 파트 승인 필요 여부가 정해졌는가 |
| [ ] | [12-schema-contract.md](12-schema-contract.md) | 도메인 read model, 단계 기능, field, enum이 맞는가 |
| [ ] | [08-rest-api-spec.md](08-rest-api-spec.md) | API path/request/response가 있는가 |
| [ ] | [10-pr-feature-review-contract.md](10-pr-feature-review-contract.md) | PR 기능 단위와 템플릿이 정해졌는가 |

프론트 작업이면 추가로 [../frontend/00-frontend-team-guide.md](../frontend/00-frontend-team-guide.md)를 본다.
백엔드 작업이면 추가로 [../backend/00-backend-team-guide.md](../backend/00-backend-team-guide.md)를 본다.

## 4. 계약 변경 여부 판단

아래 중 하나라도 바뀌면 계약 변경이다.

```text
API path
request/response field
enum/status
Organization/User/Student/School read model
PublicContextBundle
MissionContent JSON
ContentStage template type
image asset role
RealtimePracticeSpec
seed 계정/학생/access code
프론트 화면 흐름
```

계약 변경이면 코드보다 문서를 먼저 수정한다.

```text
1. docs/common 문서 수정
2. 백엔드 schema/API 수정
3. seed 수정
4. 프론트 소비 코드 수정
5. 검증
6. handoff 승인
7. PR
```

## 5. 구현 중 체크

작업 중에는 아래 기준을 유지한다.

- 커밋은 의미 단위로 작게 남긴다.
- 중간 push는 하지 않는다.
- 1~3단계 학생 콘텐츠는 승인된 정적 JSON을 사용한다.
- 4단계만 realtime으로 연다.
- 학생에게 진단명이나 낙인성 표현을 노출하지 않는다.
- OpenAI key나 provider secret을 프론트에 두지 않는다.
- 이미지 생성 실패를 조용히 대체하지 않는다.

## 6. 기능 완료 체크

기능 하나가 끝났다고 보기 전에 아래를 채운다.

```text
기능 단위:
완료한 범위:
수정한 문서:
수정한 코드:
API/데이터 계약 변경: 있음 / 없음
상대 파트 확인 필요: 있음 / 없음
검증 명령:
남은 위험:
다음 기능:
```

백엔드 변경 검증:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

프론트 변경 검증:

```bash
cd frontend
npm run lint
```

## 7. handoff 체크

상대 파트가 확인해야 하면 [02-branch-handoff-contract.md](02-branch-handoff-contract.md)에 맞춰 아래를 남긴다.

```text
검수자:
검수 범위:
승인 상태: 승인 / 수정 요청 / 보류
수정 요청:
```

승인 기록이 없으면 `dev` 통합으로 넘기지 않는다.

## 8. PR 체크

PR을 만들 때는 [10-pr-feature-review-contract.md](10-pr-feature-review-contract.md)의 템플릿을 사용한다.

PR 전 마지막 확인:

```bash
git status --short --branch
git diff --check
git log --oneline --decorate -n 8
```

PR에는 아래가 보여야 한다.

```text
기능 단위
작업 브랜치
관련 문서
API/데이터 계약 변경 여부
handoff 승인 상태
검증 결과
남은 위험
```
