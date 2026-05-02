# 프론트 API 계약 준비 점검

기준 브랜치: `frontend-dev`

참고 문서: `origin/backend`의 `docs/README.md`, `docs/frontend/00-frontend-team-guide.md`, `docs/common/11-feature-start-checklist.md`, `docs/common/08-rest-api-spec.md`, `docs/common/02-branch-handoff-contract.md`, `docs/common/10-pr-feature-review-contract.md`

## 먼저 고정할 스키마 계약

현재 프론트는 `frontend/lib/demo-data.ts`의 `CoachingScene`, `StageQuestion`, `ReviewItem`, `SessionRecord` mock을 직접 화면에 넣는다. 백엔드 API 계약은 `MissionContent`, `content_stages`, `attempt`, `content_assets`, `realtime-session` 중심이므로 화면/API 연결 전에 아래 매핑을 먼저 고정한다.

### 학생 미션 공통

- 학생 미션은 화면과 API 모두 `totalSteps: 4`를 유지한다.
- 회고는 5단계가 아니며, 4단계 realtime 이후의 별도 제출 흐름이다.
- 1~3단계는 승인된 정적 콘텐츠만 사용한다.
- 4단계만 realtime 진입을 허용한다.
- 학생 화면은 OpenAI API key, provider secret, 영상 파이프라인 정보를 받지 않는다.

### MissionContent 응답 기대값

`GET /api/student/missions/:contentId`는 프론트에서 아래 덩어리로 소비할 수 있어야 한다.

```ts
type StudentMissionContent = {
  contentId: string;
  title: string;
  totalSteps: 4;
  status: "published";
  currentStep: 1 | 2 | 3 | 4;
  attempt?: {
    attemptId: string;
    status: "not_started" | "in_progress" | "completed";
    completedStageIds: string[];
  };
  stages: StudentMissionStage[];
  assets: StudentMissionAsset[];
};
```

### Stage union

프론트 템플릿 이름은 백엔드 계약의 `templateType`으로 맞춘다.

```ts
type StudentMissionStage =
  | ConceptIntroStage
  | SequenceOrderingStage
  | CardMatchStage
  | BlankFillStage
  | RealtimeTeachBackStage;

type StageBase = {
  stageId: string;
  step: 1 | 2 | 3 | 4;
  title: string;
  instruction: string;
  assetRole?: string;
};
```

단계별 원칙:

- `step: 1`은 개념 확인 고정이다. 현재 UI 요구상 OX 확인 2개를 포함해야 하므로 `concept_intro` 안에 `checks`가 필요하다.
- `step: 2`, `step: 3`은 서버가 내려주는 유형에 따라 `sequence_ordering`, `card_match`, `blank_fill` 중 하나를 렌더링한다.
- `step: 4`는 `realtime_teach_back`만 허용한다.

백엔드 확인 필요:

- `concept_intro`에 OX 확인 문항을 포함할지, 아니면 `ox_check` 같은 별도 `templateType`을 둘지 정해야 한다.
- `card_match`는 현재 UI처럼 하나씩 즉시 채점하고 오답은 연결하지 않는 흐름을 지원해야 한다. 응답에 `accepted`, `correctPair`, `stageCompleted`가 필요하다.
- `blank_fill`의 다시 채우기 버튼은 프론트 상태 초기화이므로 API 재호출 대상이 아니다. 단, 제출 후 오답 피드백 문구 형식은 응답 계약이 필요하다.

### Submit payload

정적 단계 제출은 공통 엔드포인트를 유지한다.

`POST /api/student/missions/:contentId/stages/:stageId/submit`

```ts
type StageSubmitRequest =
  | { templateType: "concept_intro"; answer: { checks: Record<string, "O" | "X"> } }
  | { templateType: "sequence_ordering"; answer: { orderedItemIds: string[] } }
  | { templateType: "card_match"; answer: { leftId: string; rightId: string } }
  | { templateType: "blank_fill"; answer: { blanks: Record<string, string> } };

type StageSubmitResponse = {
  correct: boolean;
  stageCompleted: boolean;
  feedback: {
    title: string;
    message: string;
  };
  acceptedAnswer?: {
    leftId?: string;
    rightId?: string;
  };
};
```

### 이미지 asset role

현재 프론트는 CSS/inline visual 중심이라 `content_assets`와 연결되지 않았다. API 연결 시 아래 role 기준으로 화면 배치를 고정한다.

- `mission_hero`: 학생 시작/경로 화면 대표 이미지
- `stage_1_concept`: 1단계 개념 확인 이미지
- `stage_2_activity`: 2단계 정적 활동 이미지
- `stage_3_activity`: 3단계 정적 활동 이미지
- `stage_4_realtime`: 4단계 realtime 진입 안내 이미지
- `teacher_preview`: 교사용 자료 검토/미리보기 썸네일

이미지 생성 실패 fallback UI는 seed asset 대체처럼 보이면 안 된다. 실패 상태는 “이미지 생성 실패/재요청 가능”으로 분리하고, 승인된 seed asset인 것처럼 렌더링하지 않는다.

## 기능 단위 점검

### teacher-dashboard

기능 단위: `teacher-dashboard`

현재 프론트 상태: `frontend/app/dashboard/page.tsx`가 교사 대시보드, 학생 목록, 자료 검토, 피드백, 미리보기 iframe을 한 파일에서 mock 상태로 처리한다.

백엔드 계약과 맞는 부분: 학생 목록, 학생 상세, 메모 수정, 자료 검토/승인/반려/이미지 재생성 같은 화면 흐름은 REST API 범위와 대체로 맞다.

백엔드 계약과 안 맞는 부분: 역할 이름이 `case_manager`, `coach` 등으로 되어 있고 API 계약의 교사/센터 관리자 흐름과 다르다. 검토 상태와 승인 상태가 로컬 배열 상태이며 `contents/:contentId/approve`, `reject`, `publish` 응답 구조와 연결되어 있지 않다.

필요한 수정 파일: `frontend/lib/demo-data.ts`, `frontend/app/dashboard/page.tsx`, API 클라이언트 추가 파일.

백엔드 확인 필요 여부: 필요. `ReviewItem`을 `ContentReviewSummary`로 매핑할 필드, 승인/반려 후 상태 enum, 메모 저장 응답을 확인해야 한다.

우선순위: P1

### student-mission

기능 단위: `student-mission`

현재 프론트 상태: `frontend/app/student/page.tsx`, `frontend/app/student/path/page.tsx`, `frontend/app/student/stage/page.tsx`, `frontend/app/student/stage/StudentStageExperience.tsx`가 `getPrimaryStudentContext()` mock으로 4단계 미션을 렌더링한다.

백엔드 계약과 맞는 부분: 학생 미션은 4단계로 보이고, 1~3단계 템플릿 인터랙션은 정적 콘텐츠 기반으로 동작한다.

백엔드 계약과 안 맞는 부분: 4단계가 realtime이 아니라 `fillBlank` 정적 템플릿이다. `scene.stageQuestions.kind`가 `ox`, `sequence`, `cardMatching`, `fillBlank`로 되어 있어 API의 `templateType`과 다르다. `contentId`, `stageId`, `attemptId`, `submit` 응답의 `feedback`을 소비하지 않는다.

필요한 수정 파일: `frontend/lib/demo-data.ts`, `frontend/app/student/stage/StudentStageExperience.tsx`, `frontend/app/student/stage/page.tsx`, API 클라이언트 추가 파일.

백엔드 확인 필요 여부: 필요. 1단계 OX를 `concept_intro` 내부 check로 둘지, 별도 타입으로 둘지 먼저 정해야 한다.

우선순위: P0

### content-generation

기능 단위: `content-generation`

현재 프론트 상태: 자료 생성/검토 화면은 mock `reviewStagePreviews`를 직접 사용하고 iframe으로 `/student/stage?step=...&preview=1`을 띄운다.

백엔드 계약과 맞는 부분: 교사가 생성된 자료를 검토하고 승인/수정/반려하는 UX 방향은 계약과 맞다.

백엔드 계약과 안 맞는 부분: `MissionContent` 1~4단계 구조, `content_assets.assetRole`, 이미지 재생성 요청/상태가 mock 문자열과 로컬 편집 상태로만 존재한다. 학생 preview iframe도 실제 `contentId/stageId`가 아니라 `step` query만 받는다.

필요한 수정 파일: `frontend/app/dashboard/page.tsx`, `frontend/app/student/stage/page.tsx`, `frontend/app/student/stage/StudentStageExperience.tsx`, API 클라이언트 추가 파일.

백엔드 확인 필요 여부: 필요. 교사용 preview가 `published` 전 콘텐츠를 볼 수 있는 접근 방식과 preview token 또는 teacher auth 조건이 필요하다.

우선순위: P1

### realtime-practice

기능 단위: `realtime-practice`

현재 프론트 상태: realtime 화면/세션 생성 호출이 없다. 학생 미션 완료는 정적 4단계 이후 `/student/path?complete=1`로 이동한다.

백엔드 계약과 맞는 부분: 없음. 아직 연결 준비 전 상태다.

백엔드 계약과 안 맞는 부분: 4단계 진입 조건, `POST /realtime-session`, `clientSecret`, `practiceSpec`, realtime 후 회고 제출과 attempt complete 흐름이 없다.

필요한 수정 파일: `frontend/lib/demo-data.ts`, `frontend/app/student/stage/StudentStageExperience.tsx`, realtime practice 화면/클라이언트 파일.

백엔드 확인 필요 여부: 필요. 프론트에 내려줄 `practiceSpec`의 최소 필드, 세션 만료/재시도, 회고 제출 위치를 확인해야 한다.

우선순위: P0

### seed-auth

기능 단위: `seed-auth`

현재 프론트 상태: 로그인/접근 코드 없이 `/dashboard`, `/student`로 직접 진입한다.

백엔드 계약과 맞는 부분: 데모 화면으로 역할별 진입점이 나뉘어 있는 점만 맞다.

백엔드 계약과 안 맞는 부분: `POST /api/auth/demo-login`, `POST /api/auth/student-access` 호출이 없다. seed 사용자/학생 access code를 화면 상태와 연결하지 않는다.

필요한 수정 파일: `frontend/app/page.tsx`, 로그인/접근 코드 화면 파일, API 클라이언트 추가 파일.

백엔드 확인 필요 여부: 필요. 데모 로그인 응답의 쿠키/토큰 방식, 학생 access code 실패 응답, seed 사용자 목록 노출 정책을 확인해야 한다.

우선순위: P2

## 바로 코드 수정하지 않는 항목

아래 항목은 API 계약 자체가 확정되어야 하므로 프론트 코드 수정 전에 백엔드 확인이 먼저 필요하다.

- `concept_intro` 안의 OX 확인 문항 구조
- `card_match` 즉시 채점 응답 구조
- `realtime_teach_back`의 `practiceSpec` 최소 필드
- preview iframe이 draft content를 조회하는 인증/권한 방식
- `content_assets.assetRole` enum
- seed auth 쿠키/토큰 처리 방식

## 다음 추천 작업

1. 백엔드와 위 스키마 계약 확인 항목을 먼저 잠근다.
2. `frontend/lib/demo-data.ts`를 백엔드 계약 이름에 맞춘 mock adapter로 쪼갠다.
3. 학생 미션 4단계 mock을 `realtime_teach_back`으로 바꾸고, 회고를 stage count 밖으로 분리한다.
4. `dashboard/page.tsx`의 자료 검토 mock을 `ContentReviewSummary`/`MissionContent` 형태로 분리한다.
5. API 클라이언트는 기능 단위별로 작은 파일부터 만든다.
