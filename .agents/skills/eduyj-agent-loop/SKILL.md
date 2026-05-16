---
name: eduyj-agent-loop
description: EduYJ 레포에서 장기 작업을 이어갈 때 사용한다. 현재 진행상황, API, DB 복원, 검증 기준을 빠르게 확인하고 작은 한국어 커밋까지 반복하는 기본 작업 루프다.
---

# EduYJ 에이전트 작업 루프

새 세션은 아래 문서만 읽는다.

1. `AGENTS.md`
2. `GOAL.md`
3. `docs/GOAL_CONTEXT.md`
4. DB/asset 작업이면 `backend/data/README.md`

## 기본 규칙

- 통합 기준은 `main` 브랜치다.
- 프론트/백엔드 작업은 `main`에서 `frontend/작업명`, `backend/작업명` 브랜치를 따서 진행한다.
- 커밋은 작게 나눈다.
- 커밋 메시지는 `docs : 내용`, `feat : 내용`, `fix : 내용`, `chore : 내용`처럼 한국어로 쓴다.
- 학생 콘텐츠는 4단계다.
- 4단계가 realtime이다.
- 영상 생성 범위를 다시 넣지 않는다.
- API, DB, 진행상황, 남은 이슈가 바뀌면 `docs/GOAL_CONTEXT.md`와 필요한 경우 `backend/data/README.md`만 갱신한다.
- 현재 공유 DB는 SQLite이며, DB 공유 기준을 갱신할 때는 dump와 generated asset을 함께 커밋한다.

## 반복 순서

```text
git status 확인
GOAL_CONTEXT에서 현재 상태 확인
작게 수정
검증 실행
필요하면 GOAL_CONTEXT 갱신
작게 커밋
필요하면 push
```

## 최소 검증

```bash
git status --short --branch
git diff --check
```
