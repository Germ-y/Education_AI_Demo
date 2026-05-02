# EduYJ 에이전트 시작점

이 파일은 레포에 들어온 에이전트가 처음 보는 입구다. 자세한 설명은 아래 문서로 분리되어 있으므로, 작업 유형에 맞는 문서를 반드시 따라간다.

## 1. 먼저 확인

```bash
git status --short --branch
```

현재 브랜치와 변경사항을 먼저 확인한다.

- 프론트 작업은 `frontend` 브랜치에서 진행한다.
- 백엔드 작업은 `backend` 브랜치에서 진행한다.
- 통합 검증은 `dev` 브랜치에서 진행한다.
- 이미 수정된 파일이 있으면 사용자 또는 다른 작업자의 변경으로 보고 함부로 되돌리지 않는다.

## 2. 공통으로 읽을 문서

1. [GOAL.md](GOAL.md) - 전체 목표
2. [docs/README.md](docs/README.md) - 문서 폴더 구조
3. [docs/common/00-agent-navigation.md](docs/common/00-agent-navigation.md) - 작업별 문서 지도
4. [docs/common/01-collaboration-contract.md](docs/common/01-collaboration-contract.md) - 프론트/백엔드 협업 계약
5. [docs/common/02-branch-handoff-contract.md](docs/common/02-branch-handoff-contract.md) - 브랜치 간 handoff 기준
6. [docs/common/03-implementation-backlog.md](docs/common/03-implementation-backlog.md) - 현재 백로그

## 3. 작업 유형별 시작 문서

| 작업 유형 | 먼저 볼 문서 | 사용할 스킬 |
| --- | --- | --- |
| 프론트 화면/UX | [docs/frontend/00-frontend-team-guide.md](docs/frontend/00-frontend-team-guide.md) | [eduyj-monorepo-collaboration](.agents/skills/eduyj-monorepo-collaboration/SKILL.md) |
| 백엔드 API/DB/seed | [docs/backend/00-backend-team-guide.md](docs/backend/00-backend-team-guide.md) | [eduyj-backend-contracts](.agents/skills/eduyj-backend-contracts/SKILL.md) |
| 콘텐츠/이미지/realtime | [docs/common/05-ai-content-template-spec.md](docs/common/05-ai-content-template-spec.md) | [eduyj-content-package](.agents/skills/eduyj-content-package/SKILL.md) |
| 프론트/백엔드 동시 변경 | [docs/common/02-branch-handoff-contract.md](docs/common/02-branch-handoff-contract.md) | [eduyj-monorepo-collaboration](.agents/skills/eduyj-monorepo-collaboration/SKILL.md) |
| 장기 목표 이어가기 | [docs/common/03-implementation-backlog.md](docs/common/03-implementation-backlog.md) | [eduyj-agent-loop](.agents/skills/eduyj-agent-loop/SKILL.md) |

## 4. 폴더 기준

```text
frontend/       프론트 구현
backend/        백엔드 구현
docs/common/    프론트와 백엔드가 함께 지키는 계약
docs/frontend/  프론트 팀원이 보는 문서
docs/backend/   백엔드 팀원이 보는 문서
.agents/skills/ 에이전트 작업 스킬
examples/       생성 콘텐츠 샘플
assets/         OCR/공공데이터 시각 자료
```

## 5. 반드시 지킬 것

- 커밋은 작게 나누고 메시지는 `feat : 내용`, `docs : 내용`, `fix : 내용`, `chore : 내용`처럼 한국어로 쓴다.
- 학생 미션은 4단계다. 회고는 5단계가 아니다.
- 4단계가 realtime이다. 1~3단계는 승인된 정적 템플릿이다.
- 영상 생성, ffmpeg, Remotion 파이프라인을 핵심 범위에 넣지 않는다.
- 이미지는 `gpt-image-2`로 실제 생성한다. 실패를 seed asset으로 조용히 대체하지 않는다.
- provider key는 `frontend/`에 노출하지 않는다.
- 학생에게 진단명이나 낙인성 표현을 노출하지 않는다.
- 실제 `.env`, `.venv`, `node_modules`, cache는 커밋하지 않는다.

## 6. Next.js 주의

<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

이 프로젝트의 Next.js 버전은 일반적으로 알고 있는 구조와 다를 수 있다. 프론트 코드를 수정하기 전에는 `frontend/node_modules/next/dist/docs/`의 관련 문서를 먼저 확인한다.
<!-- END:nextjs-agent-rules -->

## 7. 검증 기준

문서만 바꾼 경우:

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

프론트와 백엔드를 같이 바꾼 경우에는 [docs/common/02-branch-handoff-contract.md](docs/common/02-branch-handoff-contract.md)의 `dev` 통합 검증 흐름을 따른다.

## 8. 작업 종료 보고

작업을 끝낼 때는 아래 형식으로 남긴다.

```text
목표:
수정한 경로:
API/데이터 계약 변경 여부:
검증:
남은 위험:
다음 작업:
커밋:
```
