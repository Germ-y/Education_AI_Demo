# 백엔드 팀원 시작 가이드

이 문서는 백엔드 작업자가 무엇을 보고 어떤 순서로 구현하면 되는지 정리한 문서다.

## 1. 먼저 읽을 문서

1. [../common/03-implementation-backlog.md](../common/03-implementation-backlog.md)
2. [03-backend-feature-spec.md](03-backend-feature-spec.md)
3. [06-database-schema-spec.md](06-database-schema-spec.md)
4. [../common/08-rest-api-spec.md](../common/08-rest-api-spec.md)
5. [../common/02-branch-handoff-contract.md](../common/02-branch-handoff-contract.md)

## 2. 백엔드가 담당하는 것

- FastAPI API
- Pydantic 도메인 스키마
- SQLAlchemy DB 모델
- seed 데이터
- AI 오케스트레이터와 AgentRun 기록
- `gpt-image-2` 이미지 생성 job
- 4단계 realtime session 생성
- 공공데이터 source/sync

## 3. 프론트와 맞춰야 하는 것

아래가 바뀌면 반드시 `docs/common` 문서를 먼저 수정한다.

- API path
- request/response 필드
- enum/status 값
- MissionContent JSON
- ContentStage template 타입
- 이미지 asset role
- seed 학생/교사/access code
- realtime session 생성 응답

## 4. 검증

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

프론트 확인이 필요한 변경이면 [../common/02-branch-handoff-contract.md](../common/02-branch-handoff-contract.md)에 있는 handoff 포맷을 사용한다.
