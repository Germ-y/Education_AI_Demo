# EduYJ Backend Goal Plan

## Summary

최종 목표는 영주 공공데이터 공모전용 AI 교육 지원 백엔드를 `교사 대시보드 → 학생 메모리 → AI 콘텐츠 생성 → 교사 승인 → 학생 4단계 플레이 → 4단계 realtime 연습 → 리뷰/메모리 업데이트`까지 데모 가능한 상태로 만드는 것이다.

이 레포의 장기 실행 기준은 `/goal`에 입력할 수 있는 이 문서다. Codex goal 기능이 켜져 있으면 이 문서를 목표 원문으로 삼고, 세션이 끊겨도 [docs/13-implementation-backlog.md](docs/13-implementation-backlog.md)의 다음 항목부터 이어간다.

## Key Decisions

- 콘텐츠 유형은 `생활지원형`과 `학습집중형` 두 갈래다.
- 학생 플레이는 4단계다. 4단계가 realtime이다.
- 영상은 제외한다. 이미지는 `gpt-image-2`로 대표 이미지 1장과 단계별 이미지 4장을 만든다.
- 교사 승인이 없으면 학생에게 콘텐츠를 노출하지 않는다.
- 공공데이터는 교육과정, 학교 일정, 통계, 지역 자원 맥락을 연결하는 근거 데이터다.
- MVP는 seed 계정과 seed 학생 데이터로 먼저 돌아가야 한다.

## Milestones

### M0. Harness Foundation

- [AGENTS.md](AGENTS.md), [docs/00-agent-navigation.md](docs/00-agent-navigation.md), [docs/13-implementation-backlog.md](docs/13-implementation-backlog.md)를 정비한다.
- README 링크가 모두 클릭 가능한 상대 링크인지 확인한다.
- Codex `goals = true` 설정 여부를 확인한다.

### M1. Domain Contract

- DB 스키마를 [docs/11-database-schema-spec.md](docs/11-database-schema-spec.md)에 맞춰 SQLAlchemy ORM 모델로 옮긴다.
- 공통 enum, 상태값, JSON 스키마를 `packages/shared` 또는 백엔드 공통 모듈로 정의한다.
- `MissionContent`, `ContentStage`, `RealtimePracticeSpec`, `MemoryCard` 타입을 먼저 고정한다.

### M2. Seed Runtime

- demo organization, teacher, reviewer, students, support cases, memory cards를 seed 한다.
- seed login 또는 demo account selector를 제공한다.
- 학생/교사 데이터는 seed가 여러 번 실행되어도 중복 생성되지 않아야 한다.

### M3. Teacher Case Dashboard API

- 교사 학생 목록, 학생 메모리 카드, 주차별/월별 기록, 최근 콘텐츠 결과 API를 만든다.
- 교사 메모와 다음 회기 목표 수정 API를 만든다.
- 학생 개인정보 접근은 감사 로그에 남긴다.

### M4. AI Content Generation

- 오케스트레이터가 학생 컨텍스트 패킷을 만들고 4단계 콘텐츠 계획을 결정한다.
- 콘텐츠 에이전트가 1~3단계 템플릿 JSON과 4단계 `RealtimePracticeSpec`을 만든다.
- 이미지 프롬프트 빌더가 대표 이미지와 단계별 이미지 4장 브리프를 만든다.
- `gpt-image-2` generation job, OCR/visual QA job, asset 저장 구조를 연결한다.

### M5. Teacher Approval

- AI 생성 콘텐츠는 `teacher_review` 상태로 저장한다.
- 교사는 텍스트, 선택지, 정답, 이미지, realtime 역할/루브릭을 확인하고 승인/반려한다.
- 승인된 콘텐츠만 `published` 상태로 학생 API에 노출한다.

### M6. Student Play

- 학생은 오늘의 미션, 단계 진행률, 보상, 힌트, 회고를 볼 수 있다.
- 1~3단계 제출은 승인된 템플릿 스키마와 서버 판정만 사용한다.
- 학생 플레이 이벤트는 유실 없이 저장한다.

### M7. Realtime Stage 4

- 4단계 진입 시 서버가 승인된 `RealtimePracticeSpec`을 검증한다.
- OpenAI Realtime client secret을 짧은 TTL로 발급한다.
- WebRTC 연결용 session API와 이벤트 저장 API를 제공한다.
- 세션 종료 후 루브릭 결과, 요약, 회고를 저장한다.

### M8. Review And Memory

- ReviewAgent가 활동 이벤트, 오답, 체류시간, realtime 루브릭, 회고를 요약한다.
- MemoryAgent가 메모리 업데이트 후보를 만든다.
- 교사가 메모리 반영 여부를 확인할 수 있어야 한다.

### M9. Public Data

- NEIS, 교육과정, KESS/KOSIS, 학교알리미, 지역 학습자원 후보를 source registry로 관리한다.
- 데모에 필요한 최소 데이터는 seed snapshot으로 제공한다.
- 실제 API 키가 있을 때 sync job으로 갱신할 수 있어야 한다.

### M10. Optional Registration

- 핵심 데모가 돌아간 뒤 교사 회원가입, 초대 코드, 아이등록, 보호자 동의 입력을 추가한다.

## Verification

- `git status --short --branch`가 의도한 브랜치와 변경 범위를 보여야 한다.
- 문서 링크가 깨지지 않아야 한다.
- `stage 5`, `final realtime`, `video generation implementation` 같은 이전 범위 표현이 남아 있으면 안 된다.
- API/DB/AI workflow 문서의 엔티티 이름이 서로 맞아야 한다.
- 구현 단계에서는 타입체크, 테스트, seed 실행, 주요 API smoke test를 통과해야 한다.

## Completion Criteria

- 교사 seed 계정으로 로그인해 학생 케이스를 조회할 수 있다.
- 학생별 메모리 카드와 최근 기록을 볼 수 있다.
- AI 콘텐츠 생성 요청이 4단계 콘텐츠 패키지와 이미지 asset brief를 만든다.
- 교사가 콘텐츠를 승인하면 학생 계정에서 플레이할 수 있다.
- 4단계 realtime 연습을 시작하고 완료 결과가 저장된다.
- 리뷰 요약과 메모리 업데이트 후보가 다음 회기 추천에 반영된다.

## Assumptions

- 실제 운영 보안/개인정보 정책은 공모전 데모 이후 강화한다.
- 데모 이미지도 `gpt-image-2` API로 실제 생성한다. 비용/속도 문제 때문에 seed asset으로 대체하지 않는다.
- 공공데이터 endpoint는 provider portal에서 최종 확인 후 구현한다.
- `gpt-image-2`와 Realtime API는 서버에서만 호출하고, 클라이언트에는 임시 토큰만 전달한다.
