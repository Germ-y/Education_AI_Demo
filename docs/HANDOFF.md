# EduYJ Handoff

확인 기준일: 2026-05-04

기준 브랜치: `dev`

이 문서는 팀원이 바로 이어받기 위한 단일 인수인계 문서다. 상세 API는 [API.md](API.md), DB 복원은 [../backend/data/README.md](../backend/data/README.md)를 기준으로 한다.

## 현재 완성된 흐름

- 데모 학생 3명 seed가 교사 대시보드, 학생 홈, 학생 미션 화면에서 같은 데이터로 연결된다.
- 학생 이름은 `김지우`, `이민준`, `박수민`처럼 성까지 포함한다.
- 학생 홈과 대시보드의 학년/유형 표기는 `초3 · 저연령 학습지원형`처럼 한국어 label을 사용한다.
- 교사 대시보드는 학생별 `dashboardStage`를 기준으로 자료 생성, 자료 검토, 학습, 학습 피드백 상태를 표시한다.
- 학생 정보 탭은 학생에게 필요한 수업 방향을 제안형 한국어 문장으로 보여준다.
- 자료 생성·검토 탭은 생성 결과, 검토 모달, 승인/반려/배포 API 흐름에 연결되어 있다.
- 교사 화면에서는 내부 AI 참고 맥락을 그대로 노출하지 않는다. 학생 맥락은 서버에서 오케스트레이터 입력으로만 사용한다.
- 학생 홈에서 학생 카드를 누르면 해당 학생의 최신 published 콘텐츠로 바로 이동한다.
- 학생 미션은 published 콘텐츠만 조회하고, 시작/제출/회고/완료 이벤트를 API에 저장한다.
- 학생이 완료하면 최신 attempt 기반 리뷰 요약이 자동 생성되고, 교사 대시보드 단계가 학습 피드백으로 이동한다.
- 검토 모달의 학생 화면 미리보기 iframe 높이는 잘림이 없도록 보정했다.
- 검토 모달에서 이미지/음성 asset이 준비되지 않은 자료는 `사용 승인`과 `수업에 적용하기`가 막힌다.
- 학생 화면에서 다음 단계로 이동하면 URL의 `step` query가 함께 갱신된다.
- 교사 메모는 `POST /api/teacher/students/{studentId}/notes`로 저장되고, 새로고침 후에도 최근 메모가 복원된다.
- 교사 학습 기록 리포트는 `session` note로 저장되고, `POST /api/review-summaries/{reviewId}/apply-to-memory`로 메모리에 반영된다.

## 데모 학생

| 학생 | 학교/학년 | 유형 | access code | 최신 콘텐츠 |
| --- | --- | --- | --- | --- |
| 김지우 | 영주중앙초등학교 초3 | 저연령 학습지원형 | `STAR-003` | `content_clock_001` |
| 이민준 | 영주중학교 중2 | 고연령 학습지원형 | `STAR-001` | `content_fraction_001` |
| 박수민 | 영주가흥초등학교 초6 | 일상생활 지원형 | `STAR-002` | `content_bus_001` |

## 콘텐츠 계약

공통:

- 콘텐츠는 `MissionContent` 1개와 `ContentStage` 4개로 구성한다.
- 1~3단계는 승인된 정적 템플릿 JSON만 사용한다.
- 4단계는 승인된 `RealtimePracticeSpec` 기반 실시간 발화 연습이다.
- 대표 이미지 1장, 단계별 이미지 4장, 대표/단계별 안내 음성 5개를 asset으로 가진다.
- 생성된 콘텐츠는 `teacher_review`로 저장되고, 교사 승인 후 `approved`, 배포 후 `published`가 된다.
- provider key가 없거나 생성/검증에 실패하면 대체 seed 콘텐츠를 저장하지 않고 실패 run과 검수 필요 상태를 남긴다.
- 콘텐츠 생성은 작성자와 검수자를 분리한다. `mission_content_package` 출력은 schema/계약 검증 뒤 `content_quality_critique`가 한 번 더 보고, `repair` 판정이면 저장하지 않고 재생성한다.
- 이미지 생성 전에는 `image_brief`가 5개 이미지 prompt를 다시 작성한다. `gpt-image-2`에는 이 재작성된 장면 prompt만 전달한다.
- 이미지 prompt는 장면만 설명해야 하며 빈 카드, 말풍선, UI 패널, 선택지 영역, 버튼 같은 학습지형 구성을 요청하면 실패 처리한다.
- OpenAI Realtime 음성은 ElevenLabs 안내 음성과 별도다. 기본값은 `OPENAI_REALTIME_VOICE=marin`, `OPENAI_REALTIME_VOICE_SPEED=0.92`다.

일상생활 지원형 단계명:

1. 상황 만나기
2. 단서 찾기
3. 행동 고르기
4. 한 번 해보기

학습집중형 단계명:

1. 개념 열기
2. 문제 1
3. 문제 2
4. 설명해보기

템플릿 선택:

- 완전 랜덤이 아니라 학생 메모리, 난이도, 최근 실패/성공 기록을 바탕으로 고른다.
- 화면 문장은 모두 한국어로 만든다.
- 계약상 JSON key는 영문을 유지할 수 있지만, label/choice/feedback/teacher summary 등 사용자-facing 문장은 한국어여야 한다.
- `teach-back`, `realtime` 같은 내부 표현은 교사 화면에서 `설명해보기`, `실시간 발화 연습`처럼 한국어로 설명한다.

## AI가 쓰는 학생 맥락

`GET /api/teacher/students/{studentId}/context-bundle`이 AI 생성 전 맥락의 기준이다.

포함 내용:

- 학생 이름, 학년 label, 학생 유형 label
- 현재 학습 상태와 대시보드 단계
- 교사가 저장한 최근 사례 메모
- 이전 학습 시도와 리뷰 요약
- 장기 반응 패턴과 설명 방식
- NEIS snapshot 기반 학교 일정/시간표 맥락

이 맥락은 콘텐츠를 미리 정해두는 용도가 아니다. 교사가 입력한 수업 주제와 충돌하지 않도록, 학생에게 어떤 수업 방식이 필요한지 판단하는 보조 입력이다.

## DB 인수인계

추적 파일:

```text
backend/data/eduyj_demo_dump.sql
backend/data/README.md
```

로컬 SQLite 원본인 `backend/data/eduyj_demo.db`는 `.gitignore` 대상이다.

주의: 로컬에서 자료 생성/승인/학생 완료 테스트를 하면 `eduyj_demo.db`는 추적 dump와 달라진다. 팀원이 같은 기준에서 시작해야 하면 아래 dump 복원 명령으로 먼저 맞춘다.

SQL dump 복원:

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

seed 재생성:

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

## 실행

Backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

Frontend:

```bash
cd frontend
npm run dev
```

## 검증

Backend:

```bash
cd backend
.venv/bin/ruff check app tests
.venv/bin/python -m pytest
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

Frontend:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

문서/통합:

```bash
git diff --check
```

## 남은 개선사항

- 실제 OpenAI 이미지/TTS 생성 환경에서 학생 3명 각각 콘텐츠를 새로 만들고 품질을 비교한다.
- 학생별로 한 번씩 더 생성해 메모리/이전 수업 맥락 활용이 잘 되는지 확인한다.
- 학생 UI의 4단계 실시간 발화 연습을 실제 WebRTC Realtime 연결로 완성한다.
- 교사 승인부터 학생 완료, 교사 리포트 확인까지 E2E 회귀 테스트를 추가한다.
- 운영 PostgreSQL/Alembic 마이그레이션을 확정한다.
- 공모전 MVP 이후 회원가입, 학생 등록, 보호자 동의 흐름을 확장한다.
