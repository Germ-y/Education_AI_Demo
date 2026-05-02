# Demo DB Data

이 폴더는 데모 DB를 팀원이 같은 상태로 재현하기 위한 파일을 둔다.

## 파일

```text
eduyj_demo_dump.sql  추적되는 SQLite SQL dump
eduyj_demo.db        로컬 실행용 SQLite DB, git 추적 제외
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
missionContents: 3
publicDataSources: 2
```
