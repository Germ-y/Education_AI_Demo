# Student Stage Handoff - 2026-05-04

기준 브랜치: `dev`

## 이번 작업 요약

- 학생 스테이지 카드 매칭/순서 배열 화면의 큰 화면 레이아웃을 조정했다.
- iframe 미리보기와 실제 학생 메인 화면에서 비율이 다르게 보이던 문제를 줄이기 위해 고정 보드 스케일과 내부 카드 영역 높이를 다시 맞췄다.
- 기본 오디오 컨트롤 바가 사진 영역을 많이 차지해서, 학생 화면에서는 재생 바 대신 둥근 재생 버튼만 보이도록 바꿨다.
- 정답/완료 메시지는 레이아웃을 밀어내는 박스가 아니라 떠 있는 피드백 토스트처럼 보이게 했다.
- 카드 트레이는 최대 3개 선택지 기준으로 공백을 줄이고, 선택된 카드가 올라가는 동작이 보이도록 순서 칸과 트레이 간격을 조정했다.
- `explanation_choice`, `wrong_explanation_fix` 템플릿은 선택지가 떠야 하는 화면이라 `image_quiz` 렌더러로 매핑했다.
- 백엔드 생성 로그 파일을 추가했다. 이미지/TTS 생성 패키지를 돌리면 `progress=1/10` 같은 진행률이 파일에 남는다.
- 리뷰 asset 재생성/쇼케이스 생성에 쓰던 일회성 Python 스크립트 3개는 삭제했다.

## 관련 커밋

- `ec22d4a fix : 생성 진행 로그와 학생 화면 UI 정리`
- `09f3b26 chore : 임시 생성 스크립트 정리`

## 학생 화면에서 바뀐 파일

- `frontend/app/student/stage/StudentStageExperience.tsx`
  - `AudioPlayButton`을 추가해 이미지 위 좌상단에 재생 버튼만 띄운다.
  - `StageMedia`가 기본 브라우저 오디오 바를 직접 노출하지 않는다.
  - 카드 매칭/순서 배열의 이미지 영역과 선택 영역 높이를 다시 배분했다.
  - 완료 피드백은 CTA 위쪽에 뜨도록 배치했다.
- `frontend/lib/mission-content.ts`
  - `explanation_choice`, `wrong_explanation_fix`를 `image_quiz`로 렌더링하도록 매핑했다.

## 생성 로그

- 기본 로그 파일: `backend/logs/generation.log`
- 설정 키: `GENERATION_LOG_FILE`
- 로테이션: 1MB, 백업 5개
- 로그 대상:
  - `app.api.routes.ai`
  - `app.api.routes.contents`
  - `app.ai.openai_provider`
  - `app.ai.elevenlabs_provider`
- 예시:

```text
[04:12:03] INFO contents.assets.package_started content_id=content_fraction_001 student_id=student_learning_fraction asset_count=10
[04:12:03] INFO contents.assets.generating content_id=content_fraction_001 progress=1/10 asset_id=... type=image role=...
[04:12:16] INFO openai.image.returned model=gpt-image-2 output_path=... elapsed_sec=12.4
```

`.gitignore`에는 `backend/logs/`, `backend/*.log`, `backend/*.err`, `*.db-journal`가 들어가 있다. 로컬 생성 로그나 DB journal은 커밋하지 않는다.

## 삭제한 임시 파일

아래 파일은 데모 데이터 보정/쇼케이스 생성용 일회성 스크립트라 삭제했다.

- `backend/scripts/diversify_review_contents.py`
- `backend/scripts/generate_showcase_contents.py`
- `backend/scripts/regenerate_review_assets.py`

제품 코드인 `backend/app/api/routes/review.py`, `frontend/lib/api/features/content-review.ts`는 삭제 대상이 아니다.

## 협업자가 알아야 할 점

- 이번 작업은 DB seed를 수정하지 않았다. 학생 화면에 보이는 선택지나 카드 문구는 현재 published 콘텐츠/seed 데이터에서 온다.
- “조부모님” 같은 카드가 보이는 것은 프론트가 새로 DB에 넣은 값이 아니라, 받아온 콘텐츠 데이터를 렌더링한 결과다.
- 학생 미션 1~3단계는 정적 JSON 템플릿 기반이라, UI가 이상하면 먼저 `templateType`과 렌더러 매핑을 확인한다.
- 카드 매칭/순서 배열은 최대 선택지 수가 작아도 실제 화면 보드가 넓어서 공백이 커질 수 있다. 새 템플릿을 추가할 때는 선택지 개수별 레이아웃을 같이 확인한다.
- 오디오를 숨긴 것이 아니라 HTMLAudioElement를 숨겨 두고 버튼으로 재생/일시정지를 제어한다. 접근성 때문에 버튼 `aria-label`은 유지해야 한다.
- 생성 로그는 운영 디버깅용 파일 로그다. 느려지는 수준의 동기 작업은 아니지만, 매우 많은 생성 작업을 병렬로 돌릴 경우 로그 파일 증가와 로테이션만 확인하면 된다.

## 남은 작업

- 실제 로컬 학생 화면에서 1366x768, 1536x864, iframe 미리보기 981x736 기준 스크린샷을 다시 비교한다.
- 카드 매칭 완료 토스트가 CTA와 겹치지 않는지 stage 2/3 모두 확인한다.
- `explanation_choice`, `wrong_explanation_fix` 콘텐츠가 실제 선택지까지 정상 노출되는지 API 응답과 학생 화면을 함께 확인한다.
- 학생 스테이지에서 오디오 재생 버튼 클릭 후 상태 아이콘이 기대대로 바뀌는지 확인한다.
- 생성 패키지를 실제 provider key가 있는 환경에서 한 번 돌려 `backend/logs/generation.log`에 `progress=1/10`부터 끝까지 남는지 확인한다.
- 삭제한 일회성 스크립트가 다른 작업자 자동화에 쓰이고 있었다면, 제품용 CLI로 다시 설계해서 별도 PR로 복구한다.

## 검증 완료

아래 검증은 `ec22d4a` 커밋 직전에 통과했다.

```bash
cd frontend
npm run lint
npx tsc --noEmit

cd backend
python -m ruff check app tests
python -m pytest

git diff --check
```

