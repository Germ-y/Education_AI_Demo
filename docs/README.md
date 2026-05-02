# 문서 구조

문서는 세 폴더로 관리한다.

```text
docs/common/    프론트와 백엔드가 함께 보는 공통 계약
docs/frontend/  프론트 팀원이 작업 전에 보는 문서
docs/backend/   백엔드 팀원이 작업 전에 보는 문서
```

## 먼저 볼 문서

- 전체 문서 지도: [common/00-agent-navigation.md](common/00-agent-navigation.md)
- 협업 계약: [common/01-collaboration-contract.md](common/01-collaboration-contract.md)
- 브랜치 handoff 계약: [common/02-branch-handoff-contract.md](common/02-branch-handoff-contract.md)
- PR 기능 단위 검수 계약: [common/10-pr-feature-review-contract.md](common/10-pr-feature-review-contract.md)
- 기능 시작 체크리스트: [common/11-feature-start-checklist.md](common/11-feature-start-checklist.md)
- 프론트/백엔드 스키마 계약: [common/12-schema-contract.md](common/12-schema-contract.md)
- 프론트 팀원 가이드: [frontend/00-frontend-team-guide.md](frontend/00-frontend-team-guide.md)
- 백엔드 팀원 가이드: [backend/00-backend-team-guide.md](backend/00-backend-team-guide.md)
- NEIS 데이터 수집/조회 계획: [backend/07-neis-data-collection-plan.md](backend/07-neis-data-collection-plan.md)
- AI 오케스트레이터 workflow: [backend/08-ai-orchestrator-workflow.md](backend/08-ai-orchestrator-workflow.md)
- 최신 인수인계 요약: [common/13-current-handoff-summary.md](common/13-current-handoff-summary.md)

## 문서 수정 기준

- 프론트 화면만 바뀌면 `docs/frontend/`를 우선 수정한다.
- 백엔드 API/DB/AI workflow만 바뀌면 `docs/backend/`를 우선 수정한다.
- API 응답, 콘텐츠 JSON, seed, 상태값처럼 양쪽이 같이 맞춰야 하는 내용은 `docs/common/`을 수정한다.
- 한쪽 브랜치에서 push한 변경을 다른 팀이 확인해야 하면 [common/02-branch-handoff-contract.md](common/02-branch-handoff-contract.md)에 자체 검수와 상대 파트 승인 상태를 남긴다.
- PR을 올릴 때는 [common/10-pr-feature-review-contract.md](common/10-pr-feature-review-contract.md)에 맞춰 기능 단위와 검수 범위를 적는다.
- 새 기능을 시작할 때는 [common/11-feature-start-checklist.md](common/11-feature-start-checklist.md)를 먼저 채운다.
- API field, enum, MissionContent 구조가 바뀌면 [common/12-schema-contract.md](common/12-schema-contract.md)를 먼저 갱신한다.
- dev 통합 전후의 최신 구현 상태와 DB 복원 방법은 [common/13-current-handoff-summary.md](common/13-current-handoff-summary.md)에 남긴다.
