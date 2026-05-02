# 프론트 팀원 시작 가이드

이 문서는 프론트 팀원이 레포를 처음 열었을 때 무엇을 보고, 어떤 순서로 작업하면 되는지 정리한 문서다.

## 1. 현재 목표

이 서비스는 기초학력거점지원센터의 학생에게 맞춤형 AI 학습/생활 미션을 제공하는 데모다.

큰 흐름은 아래와 같다.

```text
교사 대시보드
-> 학생 선택
-> 학생 메모리/최근 기록 확인
-> AI 생성 콘텐츠 교사 검토
-> 학생에게 배포
-> 학생 4단계 미션 플레이
-> 4단계 realtime 연습
-> 회고/리뷰/메모리 업데이트
```

프론트의 핵심 화면은 두 갈래다.

- 교사용 화면: 학생 케이스 파일을 보고 콘텐츠를 승인한다.
- 학생용 화면: 오늘의 미션을 4단계로 플레이한다.

## 2. 먼저 읽을 문서

작업 전 아래 순서로 읽는다.

1. [../common/04-child-content-experience.md](../common/04-child-content-experience.md)
2. [../common/05-ai-content-template-spec.md](../common/05-ai-content-template-spec.md)
3. [../common/08-rest-api-spec.md](../common/08-rest-api-spec.md)
4. [../common/02-branch-handoff-contract.md](../common/02-branch-handoff-contract.md)
5. [../../AGENTS.md](../../AGENTS.md)

API나 데이터가 헷갈리면 [../common/08-rest-api-spec.md](../common/08-rest-api-spec.md)를 기준으로 본다.

## 3. 프론트 폴더 구조

```text
frontend/app/page.tsx
홈 또는 진입 화면

frontend/app/dashboard*
교사 대시보드 관련 화면

frontend/app/student*
학생 미션 관련 화면

frontend/app/student/stage/*
학생 단계별 플레이 화면

frontend/lib/demo-data.ts
프론트 데모 데이터 또는 API 연결 전 임시 데이터
```

## 4. 반드시 지킬 UX 기준

- 학생 화면은 학습 관리 툴처럼 보이면 안 된다.
- 학생 화면은 짧은 미션형 플레이 흐름이어야 한다.
- 학생 미션은 4단계다.
- 회고는 4단계 이후 활동이며 5단계가 아니다.
- 1~3단계는 이미 승인된 정적 콘텐츠를 보여준다.
- 4단계는 realtime 대화/연습 화면이다.
- 학생에게 진단명이나 낙인성 표현을 노출하지 않는다.
- 이미지 안에 긴 텍스트를 넣지 않는다. 텍스트는 UI가 담당한다.

## 5. 학생 미션 4단계

생활지원형:

```text
1. 상황 만나기
2. 단서 찾기
3. 행동 고르기
4. 한 번 해보기: realtime 역할 연습
```

학습집중형:

```text
1. 개념 열기
2. 문제 1
3. 문제 2
4. 직접 설명해보기: realtime 설명 연습
```

## 6. 백엔드 변경 후 프론트가 확인할 것

백엔드가 push한 뒤에는 [../common/02-branch-handoff-contract.md](../common/02-branch-handoff-contract.md)의 “백엔드가 push하면 프론트가 확인할 문서”를 먼저 본다.

특히 확인할 것:

```text
API path가 바뀌었는가
응답 필드명이 바뀌었는가
status 값이 바뀌었는가
MissionContent 단계 구조가 바뀌었는가
이미지 asset role이 바뀌었는가
학생 access code나 seed 데이터가 바뀌었는가
```

## 7. 프론트가 새 API를 요구할 때

화면에서 새 API가 필요하면 먼저 문서에 적는다.

수정 위치:

```text
docs/common/08-rest-api-spec.md
docs/common/02-branch-handoff-contract.md
필요하면 docs/common/04-child-content-experience.md
```

PR이나 커밋 설명에는 아래를 남긴다.

```text
백엔드 확인 필요:
- 새 API:
- 필요한 응답 필드:
- 필요한 seed 데이터:
- 연결할 화면:
```

## 8. 실행과 검증

프론트 실행:

```bash
cd frontend
npm install
npm run dev
```

프론트 검증:

```bash
cd frontend
npm run lint
```

백엔드와 같이 볼 때:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

## 9. 작업 종료 전 체크리스트

- [ ] `npm run lint` 통과
- [ ] 화면에서 텍스트가 넘치거나 겹치지 않음
- [ ] 학생 미션이 4단계로 유지됨
- [ ] 4단계 realtime 흐름이 5단계로 보이지 않음
- [ ] 백엔드 계약 변경이 있으면 `docs/common/08-rest-api-spec.md` 수정
- [ ] 백엔드가 확인할 내용이 있으면 handoff 문구 작성
