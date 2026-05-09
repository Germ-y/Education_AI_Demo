# Demo DB Data

이 폴더는 데모 DB를 팀원이 같은 상태로 재현하기 위한 파일을 둔다.

로컬 실행 중 학생등록, 생성, 승인, 학생 완료를 테스트하면 `eduyj_demo.db`는 바로 달라진다. 현재 공유 기준 DB는 학생등록부터 새로 시작할 수 있도록 학생/콘텐츠/학습기록을 비운 상태다.

기본 규칙:

- 현재 git에 추적된 DB와 dump만 공유 기준이다.
- 새로 생긴 `backend/generated/assets/**`는 `.gitignore`로 기본 무시한다.
- 개인 테스트 결과는 공유 기준으로 확정할 때만 DB, dump, asset 폴더를 한 커밋에 함께 넣는다.
- 공유 기준 갱신이 아니라면 `backend/data/eduyj_demo.db` 변경은 커밋하지 않는다.
- DB가 이상해 보이면 dump로 복원하거나 seed로 빈 데모 상태를 다시 만든다.

## 파일

```text
eduyj_demo_dump.sql  추적되는 SQLite SQL dump
eduyj_demo.db        실제 생성/승인 상태가 포함된 로컬 실행용 SQLite DB
../generated/assets  학생별/콘텐츠별 생성 이미지와 안내 음성
```

asset 경로 규칙:

```text
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.png
backend/generated/assets/students/{studentId}/{contentId}/{assetId}.mp3
```

현재 로컬에서 새 콘텐츠 생성을 테스트하면 위 경로에 새 폴더가 생긴다. 팀원에게 공유할 데모 콘텐츠로 확정하기 전까지는 DB와 asset을 같이 커밋하지 않는다.

## 공유 기준 갱신 절차

새 콘텐츠/asset을 팀 기준으로 확정할 때만 아래 순서를 사용한다.

1. 생성, 검토, 승인, 학생 화면 확인까지 끝낸다.
2. DB asset URL이 실제 파일을 가리키는지 확인한다.
3. dump를 현재 DB에서 다시 만든다.
4. 관련 asset 폴더는 `.gitignore` 대상이므로 `git add -f`로 명시 추가한다.
5. DB, dump, asset 폴더를 같은 커밋에 넣는다.

예시:

```bash
cd backend
sqlite3 data/eduyj_demo.db .dump > data/eduyj_demo_dump.sql
cd ..
git add backend/data/eduyj_demo.db backend/data/eduyj_demo_dump.sql
git add -f backend/generated/assets/students/{studentId}/{contentId}
```

공유 기준 갱신 전 확인:

```bash
git status --short backend/data backend/generated/assets
git ls-files backend/generated/assets/students/{studentId}/{contentId}
```

## seed로 재생성

```bash
cd backend
DATABASE_URL=sqlite+pysqlite:///./data/eduyj_demo.db .venv/bin/python -m app.data.seed_demo
```

## dump로 복원

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

## 현재 dump 기준

```text
organizations: 1
users: 1
students: 0
schools: 3
schoolCalendarEvents: 7
schoolTimetableSlots: 16
supportCases: 0
memoryCards: 0
missionContents: 0
contentStages: 0
contentAssets: 0
contentAttempts: 0
realtimePracticeSessions: 0
reviewSummaries: 0
caseNotes: 0
publicDataSources: 2
studentSupportIntakeSources: schema ready, seed 기본값 0
studentSupportProfiles: schema ready, seed 기본값 0
studentContextBriefs: schema ready, seed 기본값 0, 교사 화면 명칭은 기억장치
teacherReportDrafts: schema ready, seed 기본값 0
teacherReports: schema ready, seed 기본값 0
```

2026-05-06 코드 기준으로 지원 프로필, AI 리포트, 기억장치(ContextBrief) table이 추가됐다. 기존 dump를 복원해도 앱 시작 시 `create_schema()`가 누락 table을 만들며, 공유 기준 DB/dump를 새로 확정할 때 위 table 데이터까지 함께 갱신한다.
