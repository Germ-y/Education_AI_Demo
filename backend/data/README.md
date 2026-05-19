# Demo DB Data

이 폴더는 팀원이 현재 배포 상태를 같은 화면으로 재현하기 위한 SQLite DB와 dump를 둡니다.

## 현재 공유 기준

- 기준 DB: `eduyj_demo.db`
- 복원 dump: `eduyj_demo_dump.sql`
- asset 폴더: `../generated/assets/students/**`
- 기준 날짜: 2026-05-12
- 현재 DB는 PostgreSQL이 아니라 SQLite입니다.

현재 DB 내용:

```text
organizations: 1
users: 1
students: 2
supportCases: 2
memoryCards: 2
studentContextBriefs: 2
studentSupportProfiles: 3
missionContents: 7
contentStages: 28
contentAssets: 70
contentAttempts: 33
teacherReports: 1
```

콘텐츠 상태:

```text
published: 2
teacher_review: 5
```

학생:

```text
김진수 / elementary_3 / learning_focus
최하늘 / elementary_3 / learning_focus
```

현재 asset은 모두 존재해야 합니다.

```bash
find backend/generated/assets/students -type f | wc -l
# 70
```

## 복원

```bash
cd backend
rm -f data/eduyj_demo.db
sqlite3 data/eduyj_demo.db < data/eduyj_demo_dump.sql
```

## 공유 기준 갱신

현재 배포 상태를 새 기준으로 확정할 때만 아래 순서를 사용합니다.

1. 학생등록, 콘텐츠 생성, 검토, 승인, 학생 화면 확인을 끝냅니다.
2. DB가 참조하는 asset 파일이 모두 있는지 확인합니다.
3. dump를 현재 DB에서 다시 만듭니다.
4. DB, dump, generated asset을 같은 커밋에 넣습니다.

```bash
cd backend
sqlite3 data/eduyj_demo.db .dump > data/eduyj_demo_dump.sql
cd ..
git add backend/data/eduyj_demo.db backend/data/eduyj_demo_dump.sql
git add -f backend/generated/assets/students
```

## 정합성 체크

```bash
sqlite3 backend/data/eduyj_demo.db "pragma integrity_check;"
sqlite3 backend/data/eduyj_demo.db \
  "select status, count(*) from mission_contents group by status;"
```

DB가 참조하는 `/generated/...` 파일 누락은 허용하지 않습니다.

## PostgreSQL 이관 상태

PostgreSQL은 목표 운영 DB입니다. 현재 main 기준으로는 `DATABASE_URL=postgresql+psycopg://...` 설정 시 SQLAlchemy 모델 기반 schema 생성이 가능하고, `generation_jobs`를 포함한 신규 테이블도 `create_schema()`에서 생성됩니다. SQLite dump를 PostgreSQL에 바로 넣는 방식은 지원하지 않습니다.

남은 작업:

1. PostgreSQL role/database 생성 스크립트
2. SQLite DB를 앱 모델로 읽어 PostgreSQL에 삽입하는 migration script
3. generated asset 배포/동기화 방식 결정
