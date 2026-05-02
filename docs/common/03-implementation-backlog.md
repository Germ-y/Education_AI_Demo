# 구현 백로그

확인 기준일: 2026-05-02

이 파일은 `/goal` 또는 장기 에이전트 작업에서 다음 행동을 고르는 실행 목록이다.

## 현재 상태

- [x] 콘텐츠 방향: 4단계, 4단계 realtime, 영상 제외
- [x] 교사 승인 구조: AI 생성 후 검수/승인/배포
- [x] 공공데이터 방향: 교육과정/학사일정/통계/지역 맥락
- [x] 문서 하네스: AGENTS/GOAL/문서 지도/상세 명세
- [x] 실제 백엔드 프로젝트 구조 확인
- [x] DB 스키마 구현
- [x] seed 데이터 구현
- [x] 기본 API 구현
- [x] 프론트/백엔드 협업 계약 문서와 모노레포 스킬 추가
- [x] docs를 `common`, `frontend`, `backend` 폴더로 분리
- [x] 프론트 팀원 시작 가이드와 브랜치 handoff 계약 추가
- [x] 기능 단위 PR 검수 계약 추가
- [x] 기능 시작 체크리스트 추가
- [x] 프론트/백엔드 공통 스키마 계약 추가
- [x] MVP를 회원가입보다 seed 도메인 조회 우선으로 정리
- [x] AI provider 연동 기반: AgentRun 저장, OpenAI/ElevenLabs adapter, fallback 금지 실패 기록
- [ ] AI provider 실제 생성 workflow 완성
- [ ] 학생 플레이 런타임 구현

## 협업 기준

프론트와 백엔드가 함께 바뀌는 작업은 먼저 [11-feature-start-checklist.md](11-feature-start-checklist.md), [01-collaboration-contract.md](01-collaboration-contract.md), [02-branch-handoff-contract.md](02-branch-handoff-contract.md), [10-pr-feature-review-contract.md](10-pr-feature-review-contract.md)를 따른다.

첫 기능 분담은 가입/로그인이 아니라 아래 조회성 도메인 순서로 잡는다.

```text
1. seeded-domain-read
2. school-public-context
3. teacher-case-read
4. student-mission
```

계약 변경 순서:

```text
문서 스펙 -> 백엔드 스키마/API -> seed -> 프론트 소비 코드 -> 검증 -> backlog 갱신
```

## 마일스톤 1. 레포와 앱 구조

목표:

```text
백엔드 앱이 실행 가능한 구조인지 확인하고, 없으면 최소 구조를 만든다.
```

작업:

- `backend/pyproject.toml`, `backend/app` directory, framework를 확인한다.
- 프론트와 공유해야 하는 타입 위치를 정한다.
- `backend/.env.example`에 필요한 API key와 public data key를 정리한다.
- 실행 명령을 README에 연결한다.

완료 기준:

```text
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
```

상태:

```text
완료. FastAPI + Pydantic + SQLAlchemy 모델 기반 첫 서버 구조를 추가했다.
```

## 마일스톤 2. 도메인 타입과 스키마

목표:

```text
MissionContent, ContentStage, RealtimePracticeSpec, MemoryCard를 코드 타입으로 고정한다.
```

작업:

- `StudentType`, `StageRole`, `TemplateType`, `MissionStatus` enum 정의
- 4단계 스키마 검증 추가
- `totalSteps=4` 제약 추가
- 이미지 asset 역할 enum 추가

완료 기준:

```text
1~3단계 템플릿과 4단계 realtime 스펙이 스키마 검증을 통과한다.
step=5 또는 video asset 역할은 검증에서 실패한다.
```

상태:

```text
완료. backend/tests/test_domain_schemas.py에서 4단계/asset 역할/realtime 단계 제약을 검증한다.
```

## 마일스톤 3. 데이터베이스 마이그레이션

참조:

- [../backend/06-database-schema-spec.md](../backend/06-database-schema-spec.md)

작업:

- 조직/사용자/학생/지원 사례
- 메모리 카드/사례 메모
- 미션 콘텐츠/콘텐츠 단계/콘텐츠 asset
- 콘텐츠 시도/활동 이벤트
- realtime 세션/이벤트
- 리뷰 요약/플래너
- 공공데이터 출처/수집/원본/정규화 데이터
- 에이전트 실행/감사 로그/동의

완료 기준:

```text
마이그레이션 적용
DB reset 후 스키마 생성
기본 관계 조회 통과
```

상태:

```text
부분 완료. SQLAlchemy 모델과 DB repository를 추가했고, seed upsert/load 및 API repository 연결은 완료했다.
Alembic 기반 운영 마이그레이션은 이후 PostgreSQL 고정 단계에서 진행한다.
```

## 마일스톤 4. 데모 seed

참조:

- [../backend/04-demo-seed-auth-registration-plan.md](../backend/04-demo-seed-auth-registration-plan.md)

작업:

- 영주 기초학력거점지원센터 seed
- 데모 교사 1명 seed
- 학생 3명 seed: 저연령 `learning_focus`, 고연령 `learning_focus`, `life_support`
- 메모리 카드, 사례 메모, 주차/월별 기록 seed
- 공공데이터 snapshot seed
- 샘플 콘텐츠 2개 seed

완료 기준:

```text
seed 여러 번 실행해도 중복 생성 없음
교사 데모 로그인 가능
학생 access code 로그인 가능
```

상태:

```text
부분 완료. 데모 seed를 DB repository에 적재하고 다시 load하는 smoke 명령을 추가했다.
학생 3명/교사 1명/학교 snapshot/샘플 콘텐츠 2개가 DATABASE_URL 기준 DB에 저장된다.
```

## 마일스톤 5. 교사 대시보드 API

참조:

- [08-rest-api-spec.md](08-rest-api-spec.md)

작업:

- `GET /api/teacher/students`
- `GET /api/teacher/students/:studentId`
- 메모리 카드 수정
- 사례 메모 CRUD
- planner 조회/수정

완료 기준:

```text
교사 계정으로 학생 목록과 학생별 케이스 파일 조회 가능
권한 없는 학생 접근 차단
감사 로그 저장
```

상태:

```text
부분 완료. demo token 기반 학생 목록/상세/memory patch API를 추가했다.
학생 상세/히스토리 조회 감사 로그를 저장한다.
```

## 마일스톤 6. AI 콘텐츠 생성

참조:

- [../backend/01-orchestrator-memory.md](../backend/01-orchestrator-memory.md)
- [../backend/02-ai-backend-system-design.md](../backend/02-ai-backend-system-design.md)
- [07-image-content-package-spec.md](07-image-content-package-spec.md)

작업:

- 오케스트레이터 컨텍스트 생성
- prompt registry 및 prompt version 파일 관리
- 콘텐츠 브리프 생성
- 4단계 ContentStage JSON 생성
- RealtimePracticeSpec 생성
- ImageBrief 5개 생성
- AgentRun 저장

완료 기준:

```text
학생 1명 기준으로 teacher_review 상태의 MissionContent가 생성된다.
대표 이미지 + stage_1~stage_4_realtime asset record가 생성된다.
hero + stage_1~stage_4_realtime에는 TTS audio asset record를 붙인다.
4단계 오디오는 realtime 대화 대체가 아니라 realtime 진입 전 상황 안내용이다.
이미지 생성 실패 시 asset status와 job error가 남는다.
```

상태:

```text
부분 완료. prompt registry와 v1 prompt 파일을 추가했고, MVP 프레임워크는 자체 workflow + OpenAI Responses API adapter로 정했다.
AgentRun repository, OpenAI Responses/Realtime adapter, ElevenLabs TTS adapter 골격을 추가했다.
`POST /api/ai/orchestrator-runs`, `POST /api/ai/content-generations`, `GET /api/ai/agent-runs/:id`를 추가했다.
OPENAI_API_KEY/ELEVENLABS_*가 없거나 provider 요청이 실패하면 대체 seed asset을 만들지 않고 failed + reviewRequired 상태로 남긴다.
다음 단계는 image/TTS job record를 MissionContent teacher_review 생성 흐름에 연결하는 것이다.
```

ElevenLabs TTS는 4단계 realtime이 아니라 정적 콘텐츠 안내 음성 사전 생성에만 사용한다.

## 마일스톤 7. gpt-image-2 이미지 asset 파이프라인

작업:

- OpenAI 이미지 생성 adapter
- 프롬프트 안전성 검사
- OCR 필요 여부 flag
- 생성 파일 저장
- QA result 저장
- teacher preview URL 연결

완료 기준:

```text
OPENAI_API_KEY가 있으면 실제 이미지 생성 가능
OPENAI_API_KEY가 없거나 생성 실패 시 job failed 상태와 error reason 저장
QA 실패 시 재생성 요청 가능
fallback seed asset 대체 없음
```

## 마일스톤 8. 승인과 배포

작업:

- 교사 검토 상세 API
- 승인/반려/재생성 API
- 배포 API
- approved content immutability 정책

완료 기준:

```text
teacher_review 콘텐츠는 학생 API에서 보이지 않는다.
published 콘텐츠만 학생 API에서 조회된다.
승인/반려/배포가 audit log에 남는다.
```

상태:

```text
부분 완료. GET /api/contents/:id, approve, reject, publish API를 추가했다.
POST /api/contents/:id/assets/:assetId/generate로 단일 이미지/TTS asset 실제 생성을 연결했다.
POST /api/contents/:id/assets/generate-package로 5개 이미지 + 5개 오디오 batch 생성을 연결했다.
학생 API는 published 콘텐츠만 반환한다.
승인/반려/배포/asset 생성 audit log를 저장한다.
재생성 API는 단일 asset generate API를 재사용하며, 교사용 별도 요청 문구 저장은 다음 슬라이스에서 진행한다.
```

## 마일스톤 9. 학생 플레이 런타임

작업:

- 오늘의 미션 조회
- 콘텐츠 시작/진행
- 1~3단계 submit
- 힌트/이벤트 저장
- 연습 후 회고 저장
- 완료 처리

완료 기준:

```text
학생 access code로 로그인해 published 콘텐츠를 1~3단계까지 완료한다.
정답 판정은 서버에서 승인된 JSON 기준으로 수행한다.
```

상태:

```text
부분 완료. 오늘의 미션 조회, 콘텐츠 시작, 1~3단계 submit, 학생 활동 이벤트 저장, 회고, 완료 API를 추가했다.
```

## 마일스톤 10. 4단계 realtime

참조:

- [06-realtime-practice-spec.md](06-realtime-practice-spec.md)

작업:

- realtime session 생성 API
- 승인된 스펙 검증
- OpenAI Realtime client secret 발급
- WebRTC 연결용 응답
- realtime 이벤트 저장
- 완료 후 루브릭 결과 저장

완료 기준:

```text
4단계에서만 realtime session이 열린다.
stage.step != 4이면 session 생성 실패.
세션 종료 후 review input으로 사용할 summary가 저장된다.
```

상태:

```text
부분 완료. OpenAI realtime client secret 발급 adapter, realtime session 생성 계약, realtime 이벤트 저장, realtime 완료 저장 API를 추가했다.
OPENAI_API_KEY가 없으면 가짜 secret을 반환하지 않고 424 + 검수 필요 오류를 반환한다.
```

## 마일스톤 11. 리뷰와 메모리 업데이트

작업:

- ReviewAgent 요약
- 메모리 업데이트 후보
- 플래너 업데이트 후보
- 교사 반영 API

완료 기준:

```text
학생 플레이 완료 후 리뷰 요약 생성.
교사가 승인하면 memory_cards 새 버전 또는 업데이트 후보가 저장된다.
```

상태:

```text
부분 완료. 저장된 attempt/activity/realtime 데이터를 기준으로 deterministic review summary 생성/조회 API를 추가했다.
POST /api/review-summaries/:id/apply-to-memory로 active memory card에 요약을 반영한다.
AI ReviewAgent provider 실행과 메모리 새 버전 생성은 다음 고도화 단계에서 진행한다.
```

## 마일스톤 12. 공공데이터 동기화

참조:

- [../backend/05-data-api-requirements.md](../backend/05-data-api-requirements.md)

작업:

- 출처 registry
- seed snapshot loader
- NEIS adapter skeleton
- 학교/교육과정/통계 조회 API
- sync job 상태 API

완료 기준:

```text
API key 없이도 snapshot으로 데모 가능.
API key가 있으면 수동 sync job 실행 가능.
```

상태:

```text
부분 완료. seed snapshot 조회 API와 NEIS 수동 sync endpoint를 추가했다.
NEIS_API_KEY가 없으면 snapshot fallback sync를 하지 않고 424 오류를 반환한다.
키가 있으면 schoolInfo, SchoolSchedule, timetable endpoint를 호출해 정규화 snapshot을 upsert한다.
sync job 이력 테이블은 이후 운영 고도화 단계에서 진행한다.
```

## 마일스톤 13. 선택 기능: 회원가입과 아이 등록

작업:

- 교사 초대/회원가입
- 아이 등록
- 보호자 동의 입력
- 학생 access code 발급

완료 기준:

```text
seed 없이도 신규 학생 케이스를 생성할 수 있다.
단, 공모전 핵심 데모 완료 이후 진행한다.
```

## 검증 명령

구현 후 실제 명령은 프로젝트 스택에 맞춰 조정한다.

```bash
git status --short --branch
git diff --check
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
.venv/bin/python -m app.data.seed_demo
```

## 커밋 계획

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
