# EduYJ Agent Guide

이 문서는 Codex/Ralph식 장기 작업을 이어받는 에이전트의 시작점이다. 새 세션은 항상 이 파일을 먼저 읽고, 다음 파일을 순서대로 연다.

1. [GOAL.md](GOAL.md)
2. [docs/00-agent-navigation.md](docs/00-agent-navigation.md)
3. [docs/13-implementation-backlog.md](docs/13-implementation-backlog.md)
4. 프론트/백엔드가 함께 바뀌는 작업이면 [docs/14-collaboration-contract.md](docs/14-collaboration-contract.md)

## Repository Layout

- `frontend/`: Next.js 학생/교사 화면
- `backend/`: FastAPI API 서버, 도메인 스키마, seed, AI workflow 계약
- `docs/`: 공통 기획/DB/API/공공데이터/오케스트레이터 문서
- `.agents/`: 프로젝트 전용 Codex 스킬
- `examples/`, `assets/`: 생성 콘텐츠 예시와 시각 자료

## Frontend Rule

<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Non-Negotiables

- 커밋은 작게 쪼갠다. 메시지는 `feat : 내용`, `docs : 내용`, `fix : 내용`, `chore : 내용` 형식의 한국어를 쓴다.
- 백엔드 구현은 `backend/`, 프론트엔드 구현은 `frontend/`, 공통 기획 문서는 `docs/`에 둔다.
- 영상 생성은 범위에서 제외한다. 영상 렌더링/믹싱 파이프라인을 핵심 설계에 넣지 않는다.
- 콘텐츠는 4단계다. 1~3단계는 승인된 템플릿 JSON, 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 연습이다.
- 이미지 생성은 `gpt-image-2` 기준이다. 한 미션은 대표 이미지 1장과 단계별 이미지 4장을 가진다.
- 데모 이미지도 API로 실제 생성한다. 비용/속도 문제 때문에 seed asset으로 대체하지 않는다.
- 학생 플레이 중 1~3단계에서 AI가 새 분석/새 생성/후처리로 콘텐츠를 바꾸면 안 된다.
- 학생에게 노출되는 모든 AI 생성 콘텐츠는 자동 검수와 교사 승인 뒤에만 배포한다.
- 공공데이터는 학생 개인 진단값이 아니라 교육과정, 학사일정, 지역 맥락, 통계 근거로 사용한다.
- 데모 MVP는 seed 학생/교사/센터 데이터로 먼저 완성한다. 회원가입/아이등록은 시간이 남을 때 확장한다.
- 프론트/백엔드 계약 변경은 문서 → 백엔드 스키마/API → seed → 프론트 소비 코드 → 검증 순서로 진행한다.

## Agent Loop

1. `git status --short --branch`로 현재 브랜치와 변경사항을 확인한다.
2. [GOAL.md](GOAL.md)의 마일스톤 중 완료되지 않은 가장 앞 작업을 고른다.
3. 관련 문서를 [docs/00-agent-navigation.md](docs/00-agent-navigation.md)에서 찾아 읽는다.
4. 작은 단위로 구현하거나 문서를 수정한다.
5. 링크, 용어, 단계 수, API/DB 연결점 정합성을 검증한다.
6. 테스트 또는 문서 검증 명령을 실행하고 결과를 기록한다.
7. 변경 범위별로 작은 커밋을 만든다.
8. [docs/13-implementation-backlog.md](docs/13-implementation-backlog.md)를 필요하면 갱신한다.

## Verification Gate

문서 작업이라도 아래는 확인한다.

```bash
rg -n "5[단]계|마지막[ ]실시간|마지막[ ]realtime|R[e]motion|f[f]mpeg" README.md AGENTS.md GOAL.md docs .agents backend
rg -n "\\]\\(([^)#]+\\.md)" README.md AGENTS.md GOAL.md docs .agents
git diff --check
```

구현 작업이라면 추가로 타입체크, 테스트, seed 실행, API smoke test를 수행한다.

FastAPI 백엔드 검증은 루트에서 `cd backend` 후 실행한다.

## Project Skills

- [.agents/skills/eduyj-agent-loop/SKILL.md](.agents/skills/eduyj-agent-loop/SKILL.md)
- [.agents/skills/eduyj-monorepo-collaboration/SKILL.md](.agents/skills/eduyj-monorepo-collaboration/SKILL.md)
- [.agents/skills/eduyj-backend-contracts/SKILL.md](.agents/skills/eduyj-backend-contracts/SKILL.md)
- [.agents/skills/eduyj-content-package/SKILL.md](.agents/skills/eduyj-content-package/SKILL.md)
