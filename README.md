# EduYJ Backend Design

영주 공공데이터 공모전용 AI 맞춤형 교육 지원 서비스의 백엔드 설계 저장소입니다.

## Start Here

작업을 이어받는 에이전트는 아래 순서대로 읽습니다.

1. [AGENTS.md](AGENTS.md) - 레포 작업 규칙, 커밋 규칙, 금지 범위
2. [GOAL.md](GOAL.md) - `/goal`로 장기 실행할 운영 목표와 마일스톤
3. [문서 내비게이션](docs/00-agent-navigation.md) - 기능별 참조 문서 라우팅
4. [구현 백로그](docs/13-implementation-backlog.md) - 내일 바로 작업할 순서

## Core Decisions

- 학생 콘텐츠는 `생활지원형`과 `학습집중형` 두 유형으로 나눈다.
- 학생 화면은 4단계 미션이다. 1~3단계는 승인된 템플릿 JSON, 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 연습이다.
- 영상 생성은 범위에서 제외한다. AI는 고품질 대표 이미지 1장과 단계별 이미지 4장을 생성한다.
- AI 생성물은 자동 검수 후 교사가 승인해야 학생에게 배포된다.
- 공공데이터는 학생 개인 진단이 아니라 교육과정, 학사일정, 통계, 지역 맥락 연결 근거로 사용한다.

## Backend Quick Start

백엔드 구현은 루트의 [`backend/`](backend/README.md) 폴더 안에 있습니다. 프론트엔드는 같은 레포의 `frontend/` 폴더와 나란히 두는 모노레포 구조로 맞춥니다.

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

기본 서버는 `http://localhost:4000`에서 실행됩니다.

검증 명령:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

현재 구현된 첫 슬라이스:

- FastAPI + Pydantic API 서버
- Pydantic 기반 4단계 콘텐츠/RealtimePracticeSpec 검증
- SQLAlchemy PostgreSQL 모델 계약
- in-memory demo seed store
- 데모 로그인, 학생 목록/상세, 학생 미션 조회/시작/제출, 4단계 realtime session mock API

데모 흐름:

```bash
curl -s -X POST http://localhost:4000/api/auth/demo-login \
  -H 'content-type: application/json' \
  -d '{"role":"teacher","email":"teacher.demo@eduyj.local"}'

curl -s -X POST http://localhost:4000/api/auth/student-access \
  -H 'content-type: application/json' \
  -d '{"accessCode":"STAR-001"}'
```

## Design Docs

| 문서 | 목적 |
| --- | --- |
| [00-agent-navigation.md](docs/00-agent-navigation.md) | 에이전트용 전체 문서 지도 |
| [01-child-content-experience.md](docs/01-child-content-experience.md) | 학생 콘텐츠 경험과 4단계 플레이 구조 |
| [02-orchestrator-memory.md](docs/02-orchestrator-memory.md) | 오케스트레이터와 메모리 압축 설계 |
| [03-ai-backend-system-design.md](docs/03-ai-backend-system-design.md) | AI 백엔드 전체 구조 |
| [04-ai-content-template-spec.md](docs/04-ai-content-template-spec.md) | 콘텐츠 템플릿 JSON 명세 |
| [05-backend-feature-spec.md](docs/05-backend-feature-spec.md) | 백엔드 기능 명세와 AI 워크플로우 |
| [06-public-data-strategy.md](docs/06-public-data-strategy.md) | 공공데이터 활용 전략 |
| [07-realtime-practice-spec.md](docs/07-realtime-practice-spec.md) | 4단계 실시간 연습 명세 |
| [08-demo-seed-auth-registration-plan.md](docs/08-demo-seed-auth-registration-plan.md) | 데모 seed와 회원가입/아이등록 확장 |
| [09-image-content-package-spec.md](docs/09-image-content-package-spec.md) | gpt-image-2 이미지 패키지 생성 명세 |
| [10-data-api-requirements.md](docs/10-data-api-requirements.md) | 수집할 공공데이터/API 요구사항 |
| [11-database-schema-spec.md](docs/11-database-schema-spec.md) | 데이터베이스 스키마 명세 |
| [12-rest-api-spec.md](docs/12-rest-api-spec.md) | REST API 계약 초안 |
| [13-implementation-backlog.md](docs/13-implementation-backlog.md) | 구현 순서와 검증 기준 |

## Codex Goal Setup

Codex `/goal` 기능을 쓰려면 로컬 `~/.codex/config.toml`의 `[features]`에 아래 설정이 필요합니다.

```toml
[features]
goals = true
```

설정 후 Codex/TUI를 재시작하면 `/goal` 명령을 사용할 수 있습니다. 이 레포의 장기 goal 원문은 [GOAL.md](GOAL.md)에 둡니다.
