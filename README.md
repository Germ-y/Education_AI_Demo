# EduYJ AI Education Demo

영주 공공데이터 공모전용 AI 맞춤형 교육 지원 서비스의 통합 작업 폴더입니다.

## Structure

```text
frontend/   Next.js 학생/교사 화면
backend/    FastAPI API 서버와 AI workflow 계약
docs/       기획, 오케스트레이터, DB, API, 공공데이터 명세
.agents/    Codex/Ralph식 장기 작업용 프로젝트 스킬
examples/   생성 콘텐츠 샘플
assets/     OCR/공공데이터 시각 자료
```

## Start Here

1. [AGENTS.md](AGENTS.md) - 레포 작업 규칙과 프론트/백엔드 주의사항
2. [GOAL.md](GOAL.md) - `/goal` 장기 실행 기준
3. [문서 내비게이션](docs/00-agent-navigation.md) - 기능별 참조 문서 라우팅
4. [구현 백로그](docs/13-implementation-backlog.md) - 다음 구현 순서
5. [협업 계약](docs/14-collaboration-contract.md) - 프론트/백엔드 동시 작업 기준

## Core Decisions

- 학생 콘텐츠는 `생활지원형`과 `학습집중형` 두 유형으로 나눈다.
- 학생 화면은 4단계 미션이다. 1~3단계는 승인된 템플릿 JSON, 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 연습이다.
- 영상 생성은 범위에서 제외한다. AI는 `gpt-image-2`로 대표 이미지 1장과 단계별 이미지 4장을 실제 생성한다.
- AI 생성물은 자동 검수 후 교사가 승인해야 학생에게 배포된다.
- 공공데이터는 학생 개인 진단이 아니라 교육과정, 학사일정, 통계, 지역 맥락 연결 근거로 사용한다.
- 프론트/백엔드 계약 변경은 문서, 백엔드 스키마/API, seed, 프론트 소비 코드 순서로 맞춘다.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

기본 화면은 `http://localhost:3000`에서 실행됩니다.

## Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

기본 API는 `http://localhost:4000`에서 실행됩니다.

검증 명령:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

데모 로그인:

```bash
curl -s -X POST http://localhost:4000/api/auth/demo-login \
  -H 'content-type: application/json' \
  -d '{"role":"teacher","email":"teacher.demo@eduyj.local"}'

curl -s -X POST http://localhost:4000/api/auth/student-access \
  -H 'content-type: application/json' \
  -d '{"accessCode":"STAR-001"}'
```

## Collaboration

- 협업 기준: [docs/14-collaboration-contract.md](docs/14-collaboration-contract.md)
- 에이전트 스킬: [.agents/skills/eduyj-monorepo-collaboration/SKILL.md](.agents/skills/eduyj-monorepo-collaboration/SKILL.md)
