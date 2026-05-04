# Demo DB Data

이 폴더는 데모 DB를 팀원이 같은 상태로 재현하기 위한 파일을 둔다.

로컬 실행 중 생성/승인/학생 완료를 테스트하면 `eduyj_demo.db`는 바로 달라진다. 현재 MVP 확인 단계에서는 실제 생성 콘텐츠와 승인 상태를 팀원이 바로 볼 수 있어야 하므로 `eduyj_demo.db`도 추적한다. DB가 이상해 보이면 dump로 복원한다.

## 파일

```text
eduyj_demo_dump.sql  추적되는 SQLite SQL dump
eduyj_demo.db        실제 생성/승인 상태가 포함된 로컬 실행용 SQLite DB
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
students: 3
schools: 3
schoolCalendarEvents: 7
schoolTimetableSlots: 16
supportCases: 3
memoryCards: 3
missionContents: 6
contentStages: 24
contentAssets: 60
contentAttempts: 20
realtimePracticeSessions: 8
reviewSummaries: 3
caseNotes: 3
publicDataSources: 2
```
