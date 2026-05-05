---
name: eduyj-agent-loop
description: EduYJ 레포에서 장기 작업을 이어갈 때 사용한다. 현재 진행상황, API, DB 복원, 검증 기준을 빠르게 확인하고 작은 한국어 커밋까지 반복하는 기본 작업 루프다.
---

# EduYJ 에이전트 작업 루프

새 세션은 아래 문서만 읽는다.

1. `AGENTS.md`
2. `GOAL.md`
3. `docs/HANDOFF.md`
4. `docs/ISSUES.md`
5. API 작업이면 `docs/API.md`
6. DB/asset 작업이면 `backend/data/README.md`

## 기본 규칙

- 통합 검증은 `dev` 브랜치를 기준으로 한다.
- 프론트 단독 작업은 `frontend`, 백엔드 단독 작업은 `backend`에서 진행한다.
- 커밋은 작게 나눈다.
- 커밋 메시지는 `docs : 내용`, `feat : 내용`, `fix : 내용`, `chore : 내용`처럼 한국어로 쓴다.
- 학생 콘텐츠는 4단계다.
- 4단계가 realtime이다.
- 영상 생성 범위를 다시 넣지 않는다.
- API, DB, 진행상황, 남은 이슈가 바뀌면 `docs/HANDOFF.md`, `docs/ISSUES.md`, `docs/API.md`, `backend/data/README.md` 중 필요한 곳만 갱신한다.

## 반복 순서

```text
git status 확인
HANDOFF/ISSUES에서 현재 상태 확인
작게 수정
검증 실행
필요하면 HANDOFF/API 갱신
작게 커밋
필요하면 push
```

## 최소 검증

```bash
git status --short --branch
git diff --check
```
