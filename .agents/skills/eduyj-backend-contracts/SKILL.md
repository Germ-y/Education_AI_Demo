---
name: eduyj-backend-contracts
description: EduYJ 백엔드 API, DB 스키마, seed 데이터, 공공데이터 동기화, AI 실행 로그, 승인/학생 플레이 계약을 구현할 때 사용한다.
---

# EduYJ 백엔드 계약 스킬

먼저 볼 문서:

- `docs/HANDOFF.md`
- `docs/ISSUES.md`
- `docs/API.md`
- `backend/data/README.md`

## 구현 순서

1. 도메인 타입과 스키마 검증
2. DB migration 또는 seed 수정
3. 교사 대시보드 API
4. AI 생성 workflow
5. 이미지/음성 asset pipeline
6. 교사 승인/배포
7. 학생 플레이 runtime
8. 4단계 realtime
9. 리뷰/메모리 업데이트
10. 공공데이터 sync

## 계약 규칙

- `mission_contents.total_steps`는 항상 4다.
- API JSON field는 `camelCase`를 기준으로 한다.
- `content_stages.step`은 1~4만 허용한다.
- realtime session 생성은 `stage.step == 4`이고 승인된 `realtime_spec_json`이 있을 때만 가능하다.
- 학생 API는 승인/배포된 콘텐츠만 반환한다.
- AI provider key는 서버 밖으로 나가지 않는다.
- 공공데이터 원본 record와 정규화 record는 따로 저장한다.
- 승인, 메모리 업데이트, 학생 데이터 접근은 audit log로 남긴다.
- 계약이 바뀌면 `docs/API.md`와 `frontend/lib/api/contracts.ts`를 같이 확인한다.
