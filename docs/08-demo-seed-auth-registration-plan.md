# 데모 Seed 데이터 및 회원가입/아이등록 확장 계획

## 1. 결론

공모전 MVP는 회원가입부터 만들지 않는다.

우선순위는 아래다.

```text
1. 선생님/학생/센터 데이터 seed 적재
2. seed 계정 로그인
3. 교사 대시보드에서 학생 케이스 확인
4. AI 콘텐츠 생성/검토/승인
5. 학생 플레이와 4단계 realtime 연습
6. 시간이 남으면 회원가입/아이등록 확장
```

이유:

```text
공모전 데모의 핵심은 가입 플로우가 아니라 학생별 맥락 기반 AI 콘텐츠와 교사 승인 구조다.
따라서 데모 데이터가 풍부해야 서비스 가치가 바로 보인다.
```

## 2. 운영 모드

### 2.1 Demo Seed Mode

환경 변수:

```text
DEMO_SEED_MODE=true
DEMO_SEED_RESET=false
DEMO_TEACHER_EMAIL=teacher.demo@eduyj.local
DEMO_STUDENT_CODE=STAR-001
```

동작:

```text
서버 시작 또는 seed 명령 실행 시 샘플 조직/교사/학생/사례/콘텐츠를 적재한다.
같은 seed를 여러 번 실행해도 중복 생성되지 않게 external_key를 둔다.
운영 환경에서는 DEMO_SEED_MODE를 끈다.
```

명령 예:

```text
python -m app.data.seed_demo
python -m app.data.seed_public_data
```

### 2.2 Production Mode

동작:

```text
seed 계정 자동 생성 없음
관리자 초대 또는 승인된 교사 회원가입만 허용
학생은 교사/센터가 등록
개인정보/동의/감사 로그 필수
```

## 3. Seed 데이터 구성

### 3.1 조직

```json
{
  "externalKey": "demo_org_yeongju_center",
  "name": "영주 기초학력거점지원센터",
  "type": "learning_support_center",
  "region": "경북 영주"
}
```

### 3.2 사용자/계정

| 역할 | 계정 | 목적 |
| --- | --- | --- |
| 센터 관리자 | `admin.demo@eduyj.local` | 전체 학생/교사/공공데이터 확인 |
| 교사 | `teacher.demo@eduyj.local` | 학생 케이스 관리, 콘텐츠 승인 |
| 콘텐츠 검수자 | `reviewer.demo@eduyj.local` | AI 생성물 검토 |
| 학생 1 | `STAR-001` | 학습집중형 분수 미션 플레이 |
| 학생 2 | `STAR-002` | 생활지원형 버스/센터 시나리오 플레이 |

데모 비밀번호는 코드에 하드코딩하지 않고 환경 변수 또는 로컬 seed 설정에서만 관리한다.

### 3.3 학생 샘플

학습집중형 학생:

```json
{
  "externalKey": "demo_student_learning_fraction",
  "displayName": "민준",
  "grade": "중2",
  "studentType": "learning_focus",
  "primaryNeed": "분수의 전체-부분 관계 이해",
  "effectiveStyles": ["시각 자료", "단계 카드", "짧은 문장"],
  "frequentBlockingUnits": ["분수", "문장제 조건 찾기"]
}
```

생활지원형 학생:

```json
{
  "externalKey": "demo_student_life_bus",
  "displayName": "수민",
  "grade": "초6",
  "studentType": "life_support",
  "primaryNeed": "센터 이동 순서와 도움 요청 연습",
  "effectiveStyles": ["상황 그림", "선택지 2개", "역할극"],
  "lifeSupportNeeds": ["순서 이해", "도움 요청", "감정 표현"]
}
```

### 3.4 사전 적재 콘텐츠

```text
학습집중형: 분수 탐험 - 빛나는 한 조각
생활지원형: 센터 가는 길 - 버스 정류장 도움 요청
```

각 콘텐츠는 아래 상태까지 seed 가능하다.

```text
teacher_review
approved
published
```

데모에서는 최소 1개 콘텐츠를 `published` 상태로 둬서 학생 화면이 바로 열린다. 교사 승인 흐름을 보여주기 위해 다른 1개는 `teacher_review` 상태로 둔다.

## 4. Seed 적재 순서

```text
1. Organization
2. Users
3. TeacherProfile / StudentAccount
4. Students
5. SupportCases
6. CaseNotes
7. MemoryCards
8. PublicData seed
9. MissionContents
10. ContentStages
11. Assets
12. RealtimePracticeSpec
13. SessionRecords / ActivityEvents sample
```

idempotency 규칙:

```text
모든 seed row는 external_key를 가진다.
이미 존재하면 update 또는 skip한다.
학생 개인정보 샘플은 가명만 사용한다.
실제 학생 데이터를 seed 파일에 넣지 않는다.
```

## 5. 초기 Auth API

MVP 필수:

```http
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/demo-login
```

`demo-login`은 데모 환경에서만 활성화한다.

응답 예:

```json
{
  "user": {
    "id": "user_teacher_demo",
    "role": "teacher",
    "organizationId": "org_yeongju_demo",
    "displayName": "김선생"
  },
  "session": {
    "expiresAt": "2026-05-02T12:00:00.000Z"
  }
}
```

## 6. 아이등록 확장

시간이 남으면 교사 화면에 `아이 등록`을 추가한다.

### 6.1 API

```http
POST /api/teacher/students
GET  /api/teacher/students/:studentId
PATCH /api/teacher/students/:studentId
POST /api/teacher/students/:studentId/cases
POST /api/teacher/students/:studentId/memory-card/bootstrap
POST /api/teacher/students/:studentId/access-code
```

### 6.2 입력 필드

필수:

```text
학생 표시 이름
학년
학교/학교급
학생 유형: life_support | learning_focus
주요 지원 필요
초기 코칭 목표
보호자 동의 상태
```

선택:

```text
관심사
강점
자주 어려워하는 과목/단원
잘 반응한 설명 방식
피해야 할 설명 방식
정서/자신감 메모
보호자 협조 상태
```

등록 후 자동 생성:

```text
SupportCase
MemoryCard 초안
Planner 초안
student_access_code
```

## 7. 교사 회원가입 확장

회원가입은 아무나 열면 안 된다.

권장 방식:

```text
센터 관리자 초대 코드 발급
교사 이메일/이름/소속 입력
초대 코드 검증
관리자 승인 또는 자동 승인
teacher 역할 부여
```

API:

```http
POST /api/auth/teacher-signup
POST /api/auth/invitations
GET  /api/admin/pending-teachers
POST /api/admin/teachers/:teacherId/approve
POST /api/admin/teachers/:teacherId/reject
```

## 8. 데이터 모델 추가/보강

### 8.1 User

```text
id
organization_id
email
password_hash
role: center_admin | teacher | content_reviewer | student | guardian
display_name
status: active | pending | disabled
last_login_at
created_at
updated_at
```

### 8.2 StudentAccount

```text
id
student_id
access_code_hash
login_enabled
expires_at
created_by
created_at
```

### 8.3 Invitation

```text
id
organization_id
email
invite_code_hash
role
status: pending | accepted | expired | revoked
expires_at
created_by
created_at
```

## 9. 화면 흐름

### 9.1 MVP 데모

```text
데모 로그인
→ 교사 대시보드
→ 학생 목록
→ 학생 메모리 카드
→ AI 생성 콘텐츠 검토
→ 승인/배포
→ 학생 화면에서 published 콘텐츠 플레이
```

### 9.2 확장 아이등록

```text
교사 로그인
→ 학생 목록
→ 아이 등록
→ 기본 정보 입력
→ 지원 유형 선택
→ 초기 메모 입력
→ 저장
→ MemoryCard 초안 생성
→ 첫 콘텐츠 생성 요청
```

## 10. 우선순위

반드시:

```text
seed 계정 로그인
seed 학생 2명 이상
teacher_review / published 콘텐츠 각각 1개 이상
학생 플레이 가능한 access_code
```

시간 남으면:

```text
교사 회원가입
관리자 초대 코드
아이 등록
등록 직후 메모리 카드 초안 생성
```

나중에:

```text
보호자 계정
보호자용 요약 카드
학교/반 단위 일괄 등록
CSV 업로드
```

## 11. 보안 주의

```text
데모 계정은 production에서 비활성화한다.
seed 비밀번호를 저장소에 넣지 않는다.
학생 access_code는 hash로 저장한다.
학생 등록 시 보호자 동의 상태를 반드시 기록한다.
실제 학생 데이터는 seed 파일에 넣지 않는다.
```

## 12. 구현 판단

현재 프로젝트에서는 아래 순서가 가장 안전하다.

```text
seed 데이터 완성
→ 로그인/세션 최소 구현
→ 교사/학생 화면 연결
→ AI 생성/승인/플레이 플로우 완성
→ 시간이 남으면 아이등록
→ 시간이 더 남으면 교사 회원가입
```

가입 기능이 없어도 데모는 성립한다. 하지만 seed 데이터가 약하면 서비스 가치가 바로 보이지 않는다. 따라서 초기 개발 리소스는 seed 케이스 품질에 먼저 써야 한다.
