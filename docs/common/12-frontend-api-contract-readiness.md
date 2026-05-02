# 프론트 API 계약 준비 점검

이 문서는 프론트가 API fetching 구조를 선구현할 때 확인할 체크리스트다.
스키마의 source of truth는 [12-schema-contract.md](12-schema-contract.md)다.

기존 프론트 mock이나 화면 구조가 이 문서와 다르면, 바로 API를 붙이지 말고 먼저 `dev adapter`와 계약 타입을 분리한다.

## 1. 먼저 볼 기준 문서

```text
1. docs/common/12-schema-contract.md
2. docs/common/08-rest-api-spec.md
3. docs/common/11-feature-start-checklist.md
4. docs/common/02-branch-handoff-contract.md
5. docs/common/10-pr-feature-review-contract.md
```

주의:

- endpoint 흐름은 `08-rest-api-spec.md`를 참고한다.
- field, enum, 도메인 read model, 학생 미션 단계 의미는 `12-schema-contract.md`를 우선한다.
- 일반 회원가입/비밀번호 로그인 UI는 MVP 선작업 대상이 아니다.

## 2. 프론트 선구현 범위

프론트가 먼저 구현할 수 있는 것은 화면 완성이 아니라 fetching 구조다.

```text
api contract types
apiFetch 공통 함수
dev adapter
backend adapter
feature별 query/fetch 함수
화면 컴포넌트와 데이터 소스 분리
```

`mock fallback`처럼 만들지 않는다.
임시 데이터는 `dev adapter`로 명확히 분리하고, 실패를 seed asset으로 조용히 대체하지 않는다.

## 3. 첫 기능 단위

프론트/백엔드는 아래 순서로 맞춘다.

```text
1. seeded-domain-read
2. school-public-context
3. teacher-case-read
4. student-mission
5. student-mission-runtime
6. content-review
7. realtime-practice
8. ai-generation
```

프론트가 처음부터 학생 미션 화면만 API에 붙이면 안 된다.
먼저 seed된 사용자/조직/학생/학교/공공데이터 read model이 화면에 들어갈 수 있는지 본다.

## 4. 공통 API envelope

```ts
export type ApiSuccess<T> = {
  data: T;
  meta: {
    requestId: string;
  };
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};
```

프론트는 오류 분기에서 `error.code`를 우선 사용한다.

## 5. 먼저 만들 fetch 함수

```text
GET /api/context/me
GET /api/teacher/students
GET /api/teacher/students/:studentId
GET /api/public-data/schools/:schoolId/context
GET /api/student/missions/today
GET /api/student/missions/:contentId
```

아직 백엔드 endpoint가 없는 경우:

```text
계약 타입은 먼저 만든다.
backend adapter 함수도 path 기준으로 만든다.
dev adapter는 같은 return type을 맞춘다.
컴포넌트는 adapter 결과만 받는다.
```

## 6. 기능 단위별 점검

### seeded-domain-read

확인할 것:

- `Organization`, `UserProfile`, `StudentProfile`, `SchoolProfile` 타입이 있는가
- `GET /api/context/me`에 맞는 fetch 함수가 있는가
- 화면이 seed 사용자/조직 값을 직접 하드코딩하지 않는가

백엔드 확인 필요:

- 현재 demo token 없이 `/api/context/me`를 허용할지
- demo teacher 기본값을 env 기반으로 줄지

### school-public-context

확인할 것:

- 학생의 `schoolCode`를 화면 데이터에서 보존하는가
- `PublicContextBundle` 타입이 있는가
- 학교 일정/시간표/통계가 한 번에 내려와도 화면에서 필요한 것만 쓰는가

백엔드 확인 필요:

- `GET /api/public-data/schools/:schoolId/context` 응답 shape
- `calendar`, `timetableSummary`, `educationStats` 최소 필드

### teacher-case-read

확인할 것:

- 학생 목록은 `StudentListItem`으로 받는가
- 학생 상세는 `StudentCaseFile`로 받는가
- 메모리 카드, 최근 기록, 월간 요약, 최근 콘텐츠가 한 화면에서 분리되어 렌더링 가능한가

백엔드 확인 필요:

- 학생 목록에 `schoolName`을 줄지
- `monthlySummary`를 문자열/객체 중 어떤 형태로 줄지

### student-mission

확인할 것:

- 학생 미션은 `totalSteps: 4`를 기준으로 렌더링되는가
- 회고가 5단계처럼 보이지 않는가
- `ContentStage.step`과 `templateType` 기준으로 템플릿을 분기하는가
- `hero`, `stage_1`, `stage_2`, `stage_3`, `stage_4_realtime` asset role을 사용 가능한가

백엔드 확인 필요:

- 1단계 개념 확인에서 OX/check 문항이 필요한 경우 `templateJson`에 어떻게 담을지
- `card_match`, `blank_fill`, `sequence_ordering` 제출 응답 shape

### realtime-practice

확인할 것:

- 4단계에서만 realtime 진입 버튼이 보이는가
- `realtime-session` fetch 함수가 별도 분리되어 있는가
- `clientSecret`은 화면 상태에 오래 저장하지 않는가

백엔드 확인 필요:

- `practiceSpec` 최소 노출 필드
- 세션 만료/재시도 오류 code

## 7. 프론트 작업 결과 보고 형식

```text
기능 단위:
수정한 파일:
API/데이터 계약 변경 필요 여부:
백엔드 확인 필요:
검증:
남은 위험:
다음 추천 작업:
```

검증:

```bash
cd frontend
npm run lint
```
