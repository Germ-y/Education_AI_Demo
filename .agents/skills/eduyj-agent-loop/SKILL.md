---
name: eduyj-agent-loop
description: EduYJ 레포에서 Codex/Ralph식 장기 작업을 이어갈 때 사용한다. 다음 마일스톤 선택, 문서 링크 확인, 검증, 작은 한국어 커밋까지 반복하는 기본 작업 루프다.
---

# EduYJ 에이전트 작업 루프

새 세션은 항상 아래 순서로 읽는다.

1. `AGENTS.md`
2. `GOAL.md`
3. `docs/00-agent-navigation.md`
4. `docs/13-implementation-backlog.md`

## 기본 규칙

- 프론트 작업은 `frontend`, 백엔드 작업은 `backend`, 통합 검증은 `dev` 브랜치를 기준으로 한다.
- 커밋은 작게 나눈다.
- 커밋 메시지는 `docs : 내용`, `feat : 내용`, `fix : 내용`, `chore : 내용`처럼 한국어로 쓴다.
- 학생 콘텐츠는 4단계다.
- 4단계가 realtime이다.
- 영상 생성 범위를 다시 넣지 않는다.
- 새 문서를 만들면 `README.md`와 `docs/00-agent-navigation.md`에 링크를 추가한다.

## 반복 순서

```text
git status 확인
백로그에서 가장 앞의 미완료 작업 선택
관련 문서 읽기
작게 수정
검증 실행
필요하면 백로그 갱신
작게 커밋
```

## 최소 검증

```bash
git status --short --branch
rg -n "5[단]계|마지막[ ]실시간|마지막[ ]realtime|R[e]motion|f[f]mpeg" README.md AGENTS.md GOAL.md docs .agents
git diff --check
```
