# PR 기능 단위 검수 계약

이 문서는 PR을 기능 단위로 이해하고 검수하기 위한 공통 기준이다.
목표는 PR을 봤을 때 “무슨 기능이 어느 화면/API/DB/AI 흐름까지 바뀌었는지” 바로 파악되게 만드는 것이다.

## 1. PR 기본 원칙

- PR 하나는 가능하면 기능 하나만 담는다.
- 기능 하나가 프론트와 백엔드를 모두 건드리면 PR 설명에서 계약 변경 범위를 먼저 밝힌다.
- 문서만 바꾸는 PR, API만 바꾸는 PR, 화면만 바꾸는 PR은 목적을 분리해서 작성한다.
- 기능 단위가 크면 `문서 계약 PR → 백엔드 구현 PR → 프론트 연결 PR → dev 통합 PR`로 쪼갠다.
- handoff 승인이 필요한 PR은 [02-branch-handoff-contract.md](02-branch-handoff-contract.md)의 승인 상태를 먼저 채운다.

## 2. 기능 단위 분류

PR 설명에는 아래 중 하나 이상의 기능 단위를 표시한다.

| 기능 단위 | 범위 | 주로 보는 문서 |
| --- | --- | --- |
| `seeded-domain-read` | seed된 센터/사용자/학생/학교 기본 정보 조회 | [11-feature-start-checklist.md](11-feature-start-checklist.md), [12-schema-contract.md](12-schema-contract.md) |
| `school-public-context` | 학생 학교 연결, 공공데이터 snapshot, 학교 맥락 조회 | [12-schema-contract.md](12-schema-contract.md), [09-public-data-strategy.md](09-public-data-strategy.md) |
| `teacher-case-read` | 학생 케이스 파일, 메모리 카드, 주차/월별 기록 조회 | [12-schema-contract.md](12-schema-contract.md), [../backend/06-database-schema-spec.md](../backend/06-database-schema-spec.md) |
| `teacher-dashboard` | 교사 대시보드, 학생 목록, 학생 메모리 카드 | [../frontend/00-frontend-team-guide.md](../frontend/00-frontend-team-guide.md), [08-rest-api-spec.md](08-rest-api-spec.md) |
| `student-mission` | 학생 오늘 미션, 1~3단계 정적 플레이 | [04-child-content-experience.md](04-child-content-experience.md), [05-ai-content-template-spec.md](05-ai-content-template-spec.md) |
| `realtime-practice` | 4단계 realtime session, 피드백, 종료 결과 | [06-realtime-practice-spec.md](06-realtime-practice-spec.md), [08-rest-api-spec.md](08-rest-api-spec.md) |
| `content-generation` | MissionContent 생성, 이미지 패키지, 교사 승인 | [05-ai-content-template-spec.md](05-ai-content-template-spec.md), [07-image-content-package-spec.md](07-image-content-package-spec.md) |
| `orchestrator-memory` | 오케스트레이터, 메모리 카드, AgentRun | [../backend/01-orchestrator-memory.md](../backend/01-orchestrator-memory.md), [../backend/02-ai-backend-system-design.md](../backend/02-ai-backend-system-design.md) |
| `public-data` | 공공데이터 source, sync, snapshot | [09-public-data-strategy.md](09-public-data-strategy.md), [../backend/05-data-api-requirements.md](../backend/05-data-api-requirements.md) |
| `seed-auth` | seed 사용자 식별, 학생 access code, 데모 세션. 일반 회원가입은 제외 | [../backend/04-demo-seed-auth-registration-plan.md](../backend/04-demo-seed-auth-registration-plan.md), [08-rest-api-spec.md](08-rest-api-spec.md) |
| `docs-agent-harness` | AGENTS, skills, 문서 구조, 작업 규칙 | [00-agent-navigation.md](00-agent-navigation.md), [01-collaboration-contract.md](01-collaboration-contract.md) |

## 3. PR 제목 기준

PR 제목은 기능 단위가 보이게 쓴다.

```text
[backend][student-mission] 학생 오늘 미션 조회 API 추가
[backend][seeded-domain-read] seed 도메인 조회 API 추가
[frontend][teacher-dashboard] 학생 메모리 카드 화면 연결
[common][content-generation] 콘텐츠 템플릿 계약 갱신
[dev][realtime-practice] 4단계 realtime 통합 검증
```

커밋 메시지는 기존 규칙을 따른다.

```text
feat : 학생 미션 조회 API 추가
docs : 콘텐츠 템플릿 계약 갱신
fix : realtime 세션 상태값 수정
```

## 4. PR 설명 템플릿

PR 설명에는 아래 항목을 채운다.

```text
기능 단위:
작업 브랜치:
관련 문서:

무엇을 바꿨나:
- 

API/데이터 계약 변경:
- 없음 / 있음
- 변경 path:
- 변경 request:
- 변경 response:
- 변경 enum/status:

프론트 확인 필요:
- 없음 / 있음
- 확인 화면:
- 확인 필드:

백엔드 확인 필요:
- 없음 / 있음
- 확인 API:
- 확인 seed:
- 확인 DB/스키마:

handoff 승인:
- 대상 파트:
- 승인 상태: 승인 / 수정 요청 / 보류 / 해당 없음
- 승인 기록 위치:

검증:
- 실행한 명령:
- 통과 여부:

남은 위험:
- 
```

## 5. 리뷰어가 먼저 볼 순서

리뷰어는 코드부터 보지 않는다. 아래 순서로 본다.

```text
1. PR 제목의 기능 단위가 실제 변경 범위와 맞는지 확인
2. 관련 문서가 같이 수정됐는지 확인
3. API/데이터 계약 변경 여부 확인
4. handoff 승인 필요 여부 확인
5. 테스트/lint/seed 검증 결과 확인
6. 코드 diff 확인
```

기능 단위가 섞여 있으면 리뷰어는 분리를 요청한다.

## 6. dev 통합 PR 기준

`dev` 브랜치로 통합하는 PR은 기능 구현 PR과 성격이 다르다.

반드시 포함할 것:

```text
통합 대상:
- origin/frontend 커밋:
- origin/backend 커밋:

통합 기능 단위:
- 

승인 상태:
- frontend 확인:
- backend 확인:

통합 검증:
- backend ruff:
- backend pytest:
- backend seed:
- frontend lint:
- smoke:
```

dev 통합 PR은 새 기능을 임의로 추가하지 않는다. 충돌 해결, 연결 검증, 문서 정합성 보강만 한다.
