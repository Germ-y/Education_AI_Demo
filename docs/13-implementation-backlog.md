# Implementation Backlog

확인 기준일: 2026-05-02

이 파일은 `/goal` 또는 장기 에이전트 작업에서 다음 행동을 고르는 실행 목록이다.

## Current Status

- [x] 콘텐츠 방향: 4단계, 4단계 realtime, 영상 제외
- [x] 교사 승인 구조: AI 생성 후 검수/승인/배포
- [x] 공공데이터 방향: 교육과정/학사일정/통계/지역 맥락
- [x] 문서 하네스: AGENTS/GOAL/navigation/spec docs
- [x] 실제 백엔드 프로젝트 구조 확인
- [x] DB schema 구현
- [x] seed 데이터 구현
- [x] 기본 API 구현
- [ ] AI provider 연동
- [ ] 학생 플레이 runtime 구현

## Milestone 1. Repo And App Structure

목표:

```text
백엔드 앱이 실행 가능한 구조인지 확인하고, 없으면 최소 구조를 만든다.
```

작업:

- `package.json`, app directory, framework를 확인한다.
- 프론트와 공유해야 하는 타입 위치를 정한다.
- `.env.example`에 필요한 API key와 public data key를 정리한다.
- 실행 명령을 README에 연결한다.

완료 기준:

```text
npm install 또는 pnpm install
npm run dev
npm run lint/typecheck
```

상태:

```text
완료. Fastify + TypeScript + Zod + Prisma 스키마 기반 첫 서버 구조를 추가했다.
```

## Milestone 2. Domain Types And Schemas

목표:

```text
MissionContent, ContentStage, RealtimePracticeSpec, MemoryCard를 코드 타입으로 고정한다.
```

작업:

- `StudentType`, `StageRole`, `TemplateType`, `MissionStatus` enum 정의
- 4단계 스키마 검증 추가
- `totalSteps=4` 제약 추가
- image asset role enum 추가

완료 기준:

```text
1~3단계 템플릿과 4단계 realtime spec이 schema validation을 통과한다.
step=5 또는 video asset role은 validation에서 실패한다.
```

상태:

```text
완료. tests/domain-schemas.test.ts에서 4단계/asset role/realtime stage 제약을 검증한다.
```

## Milestone 3. Database Migration

참조:

- [11-database-schema-spec.md](11-database-schema-spec.md)

작업:

- organization/user/student/support case
- memory card/case note
- mission content/content stage/content asset
- content attempt/activity event
- realtime session/event
- review summary/planner
- public data source/import/raw/normalized
- agent run/audit/consent

완료 기준:

```text
migration 적용
DB reset 후 schema 생성
기본 relation query 통과
```

상태:

```text
부분 완료. prisma/schema.prisma 계약과 prisma validate는 완료했다. 실제 PostgreSQL migration 적용은 다음 DB 연결 슬라이스에서 진행한다.
```

## Milestone 4. Demo Seed

참조:

- [08-demo-seed-auth-registration-plan.md](08-demo-seed-auth-registration-plan.md)

작업:

- 영주 기초학력거점지원센터 seed
- 데모 교사/리뷰어/admin seed
- 학생 2명 seed: `learning_focus`, `life_support`
- 메모리 카드, 사례 메모, 주차/월별 기록 seed
- 공공데이터 snapshot seed
- 샘플 콘텐츠 2개 seed

완료 기준:

```text
seed 여러 번 실행해도 중복 생성 없음
teacher demo login 가능
student access code login 가능
```

상태:

```text
부분 완료. in-memory demo seed와 seed smoke 명령을 추가했다. DB upsert seed는 PostgreSQL 연결 뒤 진행한다.
```

## Milestone 5. Teacher Dashboard API

참조:

- [12-rest-api-spec.md](12-rest-api-spec.md)

작업:

- `GET /api/teacher/students`
- `GET /api/teacher/students/:studentId`
- memory card patch
- case notes CRUD
- planner 조회/수정

완료 기준:

```text
교사 계정으로 학생 목록과 학생별 케이스 파일 조회 가능
권한 없는 학생 접근 차단
감사 로그 저장
```

상태:

```text
부분 완료. demo token 기반 학생 목록/상세/memory patch API를 추가했다. 감사 로그 영속화는 DB 연결 뒤 진행한다.
```

## Milestone 6. AI Content Generation

참조:

- [02-orchestrator-memory.md](02-orchestrator-memory.md)
- [03-ai-backend-system-design.md](03-ai-backend-system-design.md)
- [09-image-content-package-spec.md](09-image-content-package-spec.md)

작업:

- OrchestratorContext 생성
- ContentBrief 생성
- 4단계 ContentStage JSON 생성
- RealtimePracticeSpec 생성
- ImageBrief 5개 생성
- AgentRun 저장

완료 기준:

```text
학생 1명 기준으로 teacher_review 상태의 MissionContent가 생성된다.
대표 이미지 + stage_1~stage_4_realtime asset record가 생성된다.
이미지 생성 실패 시 asset status와 job error가 남는다.
```

## Milestone 7. gpt-image-2 Asset Pipeline

작업:

- OpenAI image generation adapter
- prompt safety check
- OCR required flag
- generated file storage
- QA result 저장
- teacher preview URL 연결

완료 기준:

```text
OPENAI_API_KEY가 있으면 실제 이미지 생성 가능
키가 없으면 demo fallback asset 사용
QA 실패 시 재생성 요청 가능
```

## Milestone 8. Approval And Publish

작업:

- teacher review detail API
- approve/reject/regenerate API
- publish API
- approved content immutability 정책

완료 기준:

```text
teacher_review 콘텐츠는 학생 API에서 보이지 않는다.
published 콘텐츠만 학생 API에서 조회된다.
승인/반려/배포가 audit log에 남는다.
```

## Milestone 9. Student Runtime

작업:

- 오늘의 미션 조회
- 콘텐츠 시작/진행
- 1~3단계 submit
- hint/event 저장
- post-practice reflection 저장
- complete 처리

완료 기준:

```text
학생 access code로 로그인해 published 콘텐츠를 1~3단계까지 완료한다.
정답 판정은 서버에서 승인된 JSON 기준으로 수행한다.
```

## Milestone 10. Realtime Stage 4

참조:

- [07-realtime-practice-spec.md](07-realtime-practice-spec.md)

작업:

- realtime session 생성 API
- 승인된 spec validation
- OpenAI Realtime client secret 발급
- WebRTC 연결용 응답
- realtime events 저장
- complete 후 루브릭 결과 저장

완료 기준:

```text
4단계에서만 realtime session이 열린다.
stage.step != 4이면 session 생성 실패.
세션 종료 후 review input으로 사용할 summary가 저장된다.
```

## Milestone 11. Review And Memory Update

작업:

- ReviewAgent summary
- Memory update candidate
- Planner update candidate
- 교사 반영 API

완료 기준:

```text
학생 플레이 완료 후 리뷰 요약 생성.
교사가 승인하면 memory_cards 새 버전 또는 업데이트 후보가 저장된다.
```

## Milestone 12. Public Data Sync

참조:

- [10-data-api-requirements.md](10-data-api-requirements.md)

작업:

- source registry
- seed snapshot loader
- NEIS adapter skeleton
- school/curriculum/stats query API
- sync job status API

완료 기준:

```text
API key 없이도 snapshot으로 데모 가능.
API key가 있으면 수동 sync job 실행 가능.
```

## Milestone 13. Optional Signup And Child Registration

작업:

- teacher invite/signup
- child registration
- guardian consent input
- student access code issue

완료 기준:

```text
seed 없이도 신규 학생 케이스를 생성할 수 있다.
단, 공모전 핵심 데모 완료 이후 진행한다.
```

## Validation Commands

구현 후 실제 명령은 프로젝트 스택에 맞춰 조정한다.

```bash
git status --short --branch
git diff --check
npm run lint
npm run typecheck
npm run test
npm run db:seed:demo
```

## Commit Plan

커밋은 아래 단위보다 크게 묶지 않는다.

```text
docs : agent 목표와 네비게이션 추가
docs : 이미지 패키지 명세 추가
docs : 공공데이터 요구사항 정리
docs : DB 및 API 명세 추가
feat : 도메인 스키마 타입 추가
feat : 데모 seed 데이터 추가
feat : 교사 학생 조회 API 추가
feat : AI 콘텐츠 생성 워크플로우 추가
feat : 4단계 realtime 세션 API 추가
```
