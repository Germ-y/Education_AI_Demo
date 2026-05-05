# EduYJ Agent Start Guide

새 세션은 이 파일을 먼저 읽고, 아래 문서만 확인합니다.

1. [GOAL.md](GOAL.md)
2. [docs/HANDOFF.md](docs/HANDOFF.md)
3. [docs/ISSUES.md](docs/ISSUES.md)
4. API 작업이면 [docs/API.md](docs/API.md)
5. DB/asset 작업이면 [backend/data/README.md](backend/data/README.md)

## Repository Layout

- `frontend/`: Next.js 학생/교사 화면
- `backend/`: FastAPI API 서버, 도메인 스키마, seed, AI workflow
- `docs/`: 인수인계, 남은 이슈, API 요약만 유지
- `.agents/`: 프로젝트 전용 Codex 스킬

## Current Working Rule

- 통합 기준은 `dev` 브랜치다.
- 프론트 단독 작업은 `frontend`, 백엔드 단독 작업은 `backend`에서 진행한다.
- 작업 전 `git status --short --branch`로 브랜치와 변경사항을 확인한다.
- 다른 사람의 변경을 되돌리지 않는다.
- 커밋 메시지는 `feat : 내용`, `fix : 내용`, `docs : 내용`, `chore : 내용` 형식의 한국어를 쓴다.

## Product Rules

- 학생 미션은 4단계다.
- 1~3단계는 승인된 정적 템플릿 JSON만 사용한다.
- 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 발화 연습이다.
- 회고는 단계 수에 포함하지 않고 후속 기록으로 저장한다.
- 학생에게 노출되는 AI 생성 콘텐츠는 자동 검수와 교사 승인 뒤에만 배포한다.
- 영상 생성 파이프라인은 범위에서 제외한다.
- 데모 MVP는 seed 학생/교사/센터 데이터로 먼저 완성한다.
- 공공데이터는 학생 진단값이 아니라 교육과정, 학사일정, 지역 맥락, 통계 근거로 사용한다.

## Frontend Rule

<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes. APIs, conventions, and file structure may differ from your training data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing frontend code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Verification Gate

문서 작업:

```bash
git diff --check
```

백엔드 작업:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
```

프론트 작업:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```
