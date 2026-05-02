export type UserRole = "case_manager" | "coach" | "student" | "guardian";

export type AppUser = {
  id: string;
  name: string;
  role: UserRole;
  organizationId: string;
  linkedStudentIds?: string[];
};

export type StudentProfile = {
  id: string;
  name: string;
  displayName: string;
  grade: string;
  school: string;
  guardianName: string;
  phone: string;
  level: number;
  rewardTokens: number;
  nextRewardTokens: number;
  attendanceRate: number;
  understandingRate: number;
  interests: string[];
  strengths: string[];
};

export type CaseStatus = "intake" | "structured" | "goal_set" | "scene_review" | "follow_up";

export type SupportCase = {
  id: string;
  studentId: string;
  status: CaseStatus;
  statusLabel: string;
  caseType: string;
  primaryNeed: string;
  sessionGoal: string;
  supportStrategy: string;
  nextAction: string;
  riskNote: string;
  challengeTags: string[];
  planTags: string[];
};

export type SceneVisual = {
  kind: "emotion" | "fraction" | "planner";
  label: string;
  helperLabel: string;
  activeIndex: number;
  segments: Array<{
    label: string;
    caption: string;
    color: string;
  }>;
};

export type StageQuestion = {
  step: number;
  stageId?: string;
  stageRole?: "scenario_intro" | "clue_identification" | "action_selection" | "concept_intro" | "basic_problem" | "applied_problem" | "realtime_practice";
  templateType?:
    | "scenario_intro"
    | "scene_observation"
    | "highlight_clue"
    | "action_choice"
    | "sequence_ordering"
    | "decision_card"
    | "concept_intro"
    | "scene_question"
    | "clue_question"
    | "blank_fill"
    | "partition_picker"
    | "applied_question"
    | "mini_simulation"
    | "card_match"
    | "realtime_roleplay"
    | "realtime_teach_back";
  assetRole?: "hero" | "stage_1" | "stage_2" | "stage_3" | "stage_4_realtime";
  kind: "concept" | "quiz" | "scenario" | "summary" | "ox" | "sequence" | "cardMatching" | "fillBlank" | "realtimeTeachBack";
  prompt: string;
  body?: string;
  choices?: string[];
  correctAnswer?: string;
  hint: string;
  correctFeedback: string;
  wrongFeedback: string;
  completionTitle: string;
  completionMessage: string;
  actionLabel?: string;
  conceptCards?: Array<{
    title: string;
    body: string;
  }>;
  scenarioLines?: Array<{
    speaker: string;
    text: string;
  }>;
  oxStatement?: string;
  oxItems?: Array<{
    statement: string;
    correctAnswer: "O" | "X";
  }>;
  sequenceItems?: Array<{
    id: string;
    label: string;
    caption?: string;
  }>;
  matchingPairs?: Array<{
    leftId: string;
    left: string;
    rightId: string;
    right: string;
  }>;
  fillBlankText?: Array<{
    kind: "text" | "blank";
    value: string;
  }>;
  fillOptions?: Array<{
    id: string;
    label: string;
  }>;
  realtimePracticeSpec?: {
    role: string;
    firstPrompt: string;
    rubric: string[];
    timeLimitSeconds: number;
  };
  visualActiveIndex?: number;
};

export type SceneTheme = {
  accent: string;
  accentStrong: string;
  accentSoft: string;
  accentPale: string;
  border: string;
  highlight: string;
  highlightText: string;
  path: string;
  pathLight: string;
  glow: string;
};

export type CoachingScene = {
  id: string;
  contentId?: string;
  caseId: string;
  contentType?: "life_support" | "learning_focus";
  status?: "published" | "teacher_review";
  title: string;
  subtitle: string;
  pathHeadline: string;
  pathDescription: string;
  stageHeadline: string;
  missionTitle: string;
  missionDescription: string;
  totalSteps: number;
  currentStep: number;
  rewardLabel: string;
  rewardProgress: number;
  assets?: Array<{
    assetId: string;
    assetRole: "hero" | "stage_1" | "stage_2" | "stage_3" | "stage_4_realtime";
    alt: string;
  }>;
  theme: SceneTheme;
  stages: Array<{
    step: number;
    title: string;
    subtitle: string;
    state: "done" | "current" | "locked";
    x: string;
    y: string;
  }>;
  visual: SceneVisual;
  question: {
    prompt: string;
    choices: string[];
    correctAnswer: string;
    hint: string;
    correctFeedback: string;
    wrongFeedback: string;
    nextActionLabel: string;
  };
  stageQuestions?: StageQuestion[];
};

export type ReviewItem = {
  id: string;
  caseId: string;
  title: string;
  type: string;
  state: string;
};

export type SessionRecord = {
  id: string;
  caseId: string;
  session: string;
  date: string;
  durationMinutes: number;
  understanding: "상" | "중" | "하";
  focus: "상" | "중" | "하";
  note: string;
};

export type StudentContext = {
  student: StudentProfile;
  supportCase: SupportCase;
  scene: CoachingScene;
};

export const PRIMARY_STUDENT_CASE_ID = "case-foundation-001";

export const users: AppUser[] = [
  {
    id: "user-center-001",
    name: "김선생",
    role: "case_manager",
    organizationId: "yeongju-basic-center",
  },
  {
    id: "user-student-001",
    name: "이수민",
    role: "student",
    organizationId: "yeongju-basic-center",
    linkedStudentIds: ["student-foundation-001"],
  },
];

export const students: StudentProfile[] = [
  {
    id: "student-emotion-001",
    name: "박하윤",
    displayName: "하윤",
    grade: "초2",
    school: "새봄초등학교",
    guardianName: "박지현",
    phone: "010-1234-5678",
    level: 3,
    rewardTokens: 58,
    nextRewardTokens: 12,
    attendanceRate: 91,
    understandingRate: 48,
    interests: ["색칠하기", "인형 놀이"],
    strengths: ["그림으로 표현하기", "칭찬에 빠르게 반응"],
  },
  {
    id: "student-foundation-001",
    name: "이수민",
    displayName: "수민",
    grade: "초4",
    school: "영주초등학교",
    guardianName: "이영희",
    phone: "010-2234-9081",
    level: 5,
    rewardTokens: 120,
    nextRewardTokens: 30,
    attendanceRate: 95,
    understandingRate: 35,
    interests: ["그림 그리기", "요리"],
    strengths: ["시각적 학습 능력", "꾸준한 노력"],
  },
  {
    id: "student-older-001",
    name: "김도윤",
    displayName: "도윤",
    grade: "중2",
    school: "봉화중학교",
    guardianName: "김정아",
    phone: "010-3345-7120",
    level: 8,
    rewardTokens: 180,
    nextRewardTokens: 45,
    attendanceRate: 88,
    understandingRate: 64,
    interests: ["축구", "영상 만들기"],
    strengths: ["구체적 예시 기억", "목표가 보일 때 집중"],
  },
];

export const supportCases: SupportCase[] = [
  {
    id: "case-emotion-001",
    studentId: "student-emotion-001",
    status: "structured",
    statusLabel: "기초 확인",
    caseType: "정서 표현 지원",
    primaryNeed: "감정을 말로 표현하기 어려워 활동 시작 전 위축됨",
    sessionGoal: "오늘의 감정을 그림 카드에서 고르고 쉬운 문장으로 말한다.",
    supportStrategy: "감정 카드, 짧은 선택 질문, 즉시 안정 피드백",
    nextAction: "감정 카드 미션을 먼저 열고 학습 진입을 돕기",
    riskNote: "오답보다 선택을 시도한 행동을 먼저 인정해야 함",
    challengeTags: ["감정 어휘 부족", "낯선 상황 위축", "선택 지연"],
    planTags: ["감정 카드", "짧은 문장", "안정 피드백"],
  },
  {
    id: "case-foundation-001",
    studentId: "student-foundation-001",
    status: "scene_review",
    statusLabel: "검토 필요",
    caseType: "기초 개념 지원",
    primaryNeed: "전체와 부분 구분에서 반복 오류",
    sessionGoal: "분수의 전체-부분 관계를 시각 자료로 설명하고 1/4을 표현한다.",
    supportStrategy: "피자 지도 학습 장면, 단계별 질문, 10분 단위 확인 문제",
    nextAction: "학습 자료 검토 후 오늘 수업 자료로 승인",
    riskNote: "시각 자료 필수, 추가 시간 필요",
    challengeTags: ["분수 개념 이해의 어려움", "아이디어 연결하기", "패턴 일반화하기"],
    planTags: ["시각 자료 제공", "1:1 설명", "단계별 체크리스트"],
  },
  {
    id: "case-older-001",
    studentId: "student-older-001",
    status: "goal_set",
    statusLabel: "진행 중",
    caseType: "학습 계획 지원",
    primaryNeed: "과제가 길어지면 조건을 놓치고 시작을 미룸",
    sessionGoal: "긴 과제를 세 단계로 나누고 첫 행동을 선택한다.",
    supportStrategy: "과제 분해, 우선순위 카드, 선택형 실행 질문",
    nextAction: "오늘 과제의 첫 행동을 정하고 10분 타이머로 시작",
    riskNote: "설명을 길게 하기보다 선택지를 줄이고 바로 시작하게 돕기",
    challengeTags: ["시작 지연", "조건 누락", "긴 글 부담"],
    planTags: ["과제 분해", "첫 행동 선택", "짧은 실행"],
  },
];

export const coachingScenes: CoachingScene[] = [
  {
    id: "scene-emotion-001",
    caseId: "case-emotion-001",
    title: "마음 탐험: 오늘 마음 고르기",
    subtitle: "마음 카드에서 지금 느낌을 찾아서 첫 문을 열어보자.",
    pathHeadline: "오늘은 마음 이름을 찾아요",
    pathDescription: "표정 카드를 보고 지금 마음과 가장 가까운 카드를 골라요.",
    stageHeadline: "지금 마음과 닮은 카드를 찾아요",
    missionTitle: "마음 카드 고르기",
    missionDescription: "네 가지 표정 카드 중 오늘 마음과 가장 가까운 카드를 선택해요.",
    totalSteps: 4,
    currentStep: 1,
    rewardLabel: "마음 별 토큰",
    rewardProgress: 46,
    theme: {
      accent: "#f08a7a",
      accentStrong: "#b84232",
      accentSoft: "#fff0ed",
      accentPale: "#fff7f4",
      border: "#f7c7bd",
      highlight: "#ffd6cf",
      highlightText: "#8f3328",
      path: "#ead0dc",
      pathLight: "#fbedf2",
      glow: "#ffd8d1",
    },
    stages: [
      {
        step: 1,
        title: "마음 카드 보기",
        subtitle: "표정을 천천히 살펴봐요",
        state: "current",
        x: "25%",
        y: "24%",
      },
      {
        step: 2,
        title: "마음 이름 말하기",
        subtitle: "한 단어로 표현해요",
        state: "locked",
        x: "53%",
        y: "38%",
      },
      {
        step: 3,
        title: "도움 카드 고르기",
        subtitle: "필요한 도움을 골라요",
        state: "locked",
        x: "30%",
        y: "57%",
      },
      {
        step: 4,
        title: "작은 시작",
        subtitle: "편한 활동부터 시작해요",
        state: "locked",
        x: "55%",
        y: "72%",
      },
    ],
    visual: {
      kind: "emotion",
      label: "마음 카드",
      helperLabel: "편안한 표정",
      activeIndex: 1,
      segments: [
        { label: "신나요", caption: "웃는 얼굴", color: "#ffd36b" },
        { label: "편안해요", caption: "차분한 얼굴", color: "#94d86a" },
        { label: "걱정돼요", caption: "작은 구름", color: "#8fb8ff" },
        { label: "속상해요", caption: "눈물 한 방울", color: "#f08a7a" },
      ],
    },
    question: {
      prompt: "차분하고 괜찮은 마음은 어떤 카드인가요?",
      choices: ["신나요", "편안해요", "속상해요"],
      correctAnswer: "편안해요",
      hint: "초록색 카드처럼 숨이 천천히 쉬어지는 마음을 찾아보세요.",
      correctFeedback: "좋아요. 편안한 마음을 잘 찾았어요. 이제 한 문장으로 말해볼 수 있어요.",
      wrongFeedback: "괜찮아요. 표정이 가장 차분한 카드를 다시 찾아볼까요?",
      nextActionLabel: "학습 길로 돌아가기 →",
    },
  },
  {
    id: "scene-foundation-001",
    contentId: "content-foundation-001",
    caseId: "case-foundation-001",
    contentType: "learning_focus",
    status: "published",
    title: "분수 탐험: 빛나는 한 조각",
    subtitle: "빛나는 한 조각을 찾아서 다음 문을 열어보자.",
    pathHeadline: "오늘은 분수의 문을 열어요",
    pathDescription: "빛나는 한 조각을 찾아서 다음 단계로 이동해요.",
    stageHeadline: "반짝이는 구역을 찾아요",
    missionTitle: "빛나는 구역 찾기",
    missionDescription: "4조각으로 나뉜 피자 지도에서 빛나는 한 조각을 찾아요.",
    totalSteps: 4,
    currentStep: 2,
    rewardLabel: "분수 탐험 토큰",
    rewardProgress: 72,
    assets: [
      { assetId: "asset-foundation-hero", assetRole: "hero", alt: "Mission hero image" },
      { assetId: "asset-foundation-stage-1", assetRole: "stage_1", alt: "Stage 1 concept image" },
      { assetId: "asset-foundation-stage-2", assetRole: "stage_2", alt: "Stage 2 activity image" },
      { assetId: "asset-foundation-stage-3", assetRole: "stage_3", alt: "Stage 3 activity image" },
      { assetId: "asset-foundation-stage-4", assetRole: "stage_4_realtime", alt: "Stage 4 realtime practice image" },
    ],
    theme: {
      accent: "#27ae60",
      accentStrong: "#16803c",
      accentSoft: "#e8f8ee",
      accentPale: "#f4fbef",
      border: "#d9ebc9",
      highlight: "#fff3c4",
      highlightText: "#8a5a00",
      path: "#efe1c1",
      pathLight: "#f8efd8",
      glow: "#dff2de",
    },
    stages: [
      {
        step: 1,
        title: "전체 구역 세기",
        subtitle: "피자 지도의 전체를 먼저 확인해요",
        state: "done",
        x: "18%",
        y: "12%",
      },
      {
        step: 2,
        title: "빛나는 구역 찾기",
        subtitle: "반짝이는 한 조각만 세어봐요",
        state: "current",
        x: "58%",
        y: "32%",
      },
      {
        step: 3,
        title: "분수로 문 열기",
        subtitle: "전체 중 일부를 분수로 표현해요",
        state: "locked",
        x: "30%",
        y: "58%",
      },
      {
        step: 4,
        title: "생활 속 분수",
        subtitle: "오늘 배운 내용을 주변에서 찾아요",
        state: "locked",
        x: "66%",
        y: "78%",
      },
    ],
    visual: {
      kind: "fraction",
      label: "피자 지도",
      helperLabel: "빛나는 한 조각",
      activeIndex: 3,
      segments: [
        { label: "1", caption: "한 조각", color: "#ffd36b" },
        { label: "2", caption: "한 조각", color: "#ffd36b" },
        { label: "3", caption: "한 조각", color: "#ffd36b" },
        { label: "4", caption: "빛나는 조각", color: "#ffe16a" },
      ],
    },
    question: {
      prompt: "빛나는 구역은 몇 개인가요?",
      choices: ["1구역", "2구역", "4구역"],
      correctAnswer: "1구역",
      hint: "노란 빛이 감싸고 있는 구역만 세어보세요.",
      correctFeedback: "맞아요. 전체 4구역 중 빛나는 곳은 1구역이에요.",
      wrongFeedback: "전체 구역이 아니라 빛나는 구역만 다시 세어볼까요?",
      nextActionLabel: "학습 길로 돌아가기 →",
    },
    stageQuestions: [
      {
        step: 1,
        stageId: "stage-foundation-1",
        stageRole: "concept_intro",
        templateType: "concept_intro",
        assetRole: "stage_1",
        kind: "ox",
        prompt: "그림을 보고 전체와 부분을 먼저 알아봐요",
        body: "분수는 전체를 몇 조각으로 나누었는지, 그중 몇 조각을 보았는지 함께 생각하는 방법이에요.",
        oxStatement: "피자 한 판을 똑같이 4조각으로 나누면, 한 조각은 전체의 부분이에요.",
        oxItems: [
          {
            statement: "피자 한 판을 똑같이 4조각으로 나누면, 한 조각은 전체의 부분이에요.",
            correctAnswer: "O",
          },
          {
            statement: "분수에서 아래 숫자는 지금 고른 조각 수를 뜻해요.",
            correctAnswer: "X",
          },
        ],
        choices: ["O", "X"],
        correctAnswer: "O|X",
        hint: "왼쪽 피자 지도에서 큰 조각이 몇 개인지 천천히 살펴보세요.",
        correctFeedback: "맞아요. 한 조각은 전체 피자에서 나뉜 부분이에요.",
        wrongFeedback: "전체는 피자 한 판, 부분은 그중 한 조각이라는 점을 다시 떠올려봐요.",
        completionTitle: "전체 확인 완료",
        completionMessage: "전체가 4조각이고 한 조각은 부분이라는 것을 확인했어요.",
        conceptCards: [
          {
            title: "전체",
            body: "피자 한 판처럼 기준이 되는 큰 하나예요.",
          },
          {
            title: "부분",
            body: "전체를 나눈 조각 중에서 지금 보고 있는 조각이에요.",
          },
          {
            title: "분수",
            body: "전체 중 일부를 숫자로 나타내는 표현이에요.",
          },
        ],
        visualActiveIndex: 0,
      },
      {
        step: 2,
        stageId: "stage-foundation-2",
        stageRole: "basic_problem",
        templateType: "sequence_ordering",
        assetRole: "stage_2",
        kind: "sequence",
        prompt: "분수를 알아보는 순서를 맞춰보세요",
        body: "카드를 눌러 올바른 순서대로 놓아보세요.",
        correctAnswer: "whole>part>fraction",
        hint: "먼저 전체를 보고, 그다음 고른 부분을 세고, 마지막에 분수로 써요.",
        correctFeedback: "좋아요. 전체부터 보고 부분을 찾아 분수로 표현했어요.",
        wrongFeedback: "순서를 다시 생각해볼까요? 전체를 먼저 확인하면 쉬워요.",
        completionTitle: "순서 배열 완료",
        completionMessage: "분수를 확인하는 순서를 잘 정리했어요.",
        sequenceItems: [
          { id: "part", label: "부분 세기", caption: "고른 조각을 세요" },
          { id: "fraction", label: "분수로 쓰기", caption: "1/4처럼 표현해요" },
          { id: "whole", label: "전체 보기", caption: "피자 한 판을 봐요" },
        ],
        visualActiveIndex: 3,
      },
      {
        step: 3,
        stageId: "stage-foundation-3",
        stageRole: "applied_problem",
        templateType: "card_match",
        assetRole: "stage_3",
        kind: "cardMatching",
        prompt: "서로 맞는 카드를 연결해보세요",
        body: "왼쪽 카드와 오른쪽 카드를 하나씩 눌러 연결해요.",
        correctAnswer: "numerator:selected|denominator:whole|fraction:expression|whole:one",
        hint: "위 숫자는 고른 조각, 아래 숫자는 전체 조각 수와 연결돼요.",
        correctFeedback: "맞아요. 분자와 분모의 뜻을 잘 연결했어요.",
        wrongFeedback: "분자와 분모가 각각 무엇을 세는지 다시 살펴봐요.",
        completionTitle: "카드 매칭 완료",
        completionMessage: "분수의 숫자와 뜻을 올바르게 연결했어요.",
        matchingPairs: [
          {
            leftId: "numerator",
            left: "위 숫자 1",
            rightId: "selected",
            right: "고른 조각 수",
          },
          {
            leftId: "denominator",
            left: "아래 숫자 4",
            rightId: "whole",
            right: "전체 조각 수",
          },
          {
            leftId: "fraction",
            left: "1/4",
            rightId: "expression",
            right: "분수 표현",
          },
          {
            leftId: "whole",
            left: "피자 한 판",
            rightId: "one",
            right: "기준이 되는 전체",
          },
        ],
        visualActiveIndex: 3,
      },
      {
        step: 4,
        stageId: "stage-foundation-4",
        stageRole: "realtime_practice",
        templateType: "realtime_teach_back",
        assetRole: "stage_4_realtime",
        kind: "realtimeTeachBack",
        prompt: "빈칸에 알맞은 숫자를 채워보세요",
        body: "아래 숫자 카드를 눌러 빈칸에 넣어요.",
        correctAnswer: "1|4",
        hint: "위에는 고른 조각 수, 아래에는 전체 조각 수를 넣어요.",
        correctFeedback: "정확해요. 전체 4조각 중 1조각은 1/4이에요.",
        wrongFeedback: "위와 아래 숫자의 위치를 다시 확인해봐요.",
        completionTitle: "오늘 학습 완료",
        completionMessage: "전체, 부분, 분수 표현까지 모두 해냈어요.",
        fillBlankText: [
          { kind: "text", value: "전체 4조각 중 1조각은 " },
          { kind: "blank", value: "top" },
          { kind: "text", value: " / " },
          { kind: "blank", value: "bottom" },
          { kind: "text", value: " 이에요." },
        ],
        fillOptions: [
          { id: "1", label: "1" },
          { id: "2", label: "2" },
          { id: "4", label: "4" },
        ],
        actionLabel: "실시간 연습 시작하기",
        realtimePracticeSpec: {
          role: "student_teaches_fraction",
          firstPrompt: "피자 4조각 중 1조각이 왜 1/4인지 설명해볼래요?",
          rubric: ["전체 조각 수를 말한다", "선택한 조각 수를 말한다", "1/4 표현과 연결한다"],
          timeLimitSeconds: 180,
        },
        visualActiveIndex: 3,
      },
    ],
  },
  {
    id: "scene-older-001",
    caseId: "case-older-001",
    title: "미션 정리: 첫 행동 고르기",
    subtitle: "긴 과제를 작게 나누고 바로 시작할 행동을 정해보자.",
    pathHeadline: "오늘은 과제를 작게 나눠요",
    pathDescription: "해야 할 일을 세 칸으로 나누고 첫 행동을 골라요.",
    stageHeadline: "가장 먼저 할 행동을 골라요",
    missionTitle: "첫 행동 선택하기",
    missionDescription: "읽기, 표시하기, 풀기 중 지금 바로 시작할 첫 행동을 선택해요.",
    totalSteps: 4,
    currentStep: 3,
    rewardLabel: "집중 미션 토큰",
    rewardProgress: 64,
    theme: {
      accent: "#2563eb",
      accentStrong: "#1d4ed8",
      accentSoft: "#eef5ff",
      accentPale: "#f5f8ff",
      border: "#c7d8ff",
      highlight: "#dbeafe",
      highlightText: "#1e3a8a",
      path: "#d9e4f7",
      pathLight: "#eef5ff",
      glow: "#dbeafe",
    },
    stages: [
      {
        step: 1,
        title: "과제 보기",
        subtitle: "전체 양을 확인해요",
        state: "done",
        x: "22%",
        y: "18%",
      },
      {
        step: 2,
        title: "조건 표시",
        subtitle: "중요한 말을 밑줄쳐요",
        state: "done",
        x: "52%",
        y: "36%",
      },
      {
        step: 3,
        title: "첫 행동 선택",
        subtitle: "바로 할 일을 고르세요",
        state: "current",
        x: "30%",
        y: "57%",
      },
      {
        step: 4,
        title: "10분 실행",
        subtitle: "짧게 시작하고 확인해요",
        state: "locked",
        x: "57%",
        y: "74%",
      },
    ],
    visual: {
      kind: "planner",
      label: "과제 분해 보드",
      helperLabel: "첫 행동",
      activeIndex: 0,
      segments: [
        { label: "문제 1번 읽기", caption: "30초", color: "#94d86a" },
        { label: "조건 밑줄", caption: "2분", color: "#ffd36b" },
        { label: "풀이 시작", caption: "7분", color: "#8fb8ff" },
        { label: "답 확인", caption: "1분", color: "#f08a7a" },
      ],
    },
    question: {
      prompt: "지금 바로 시작하기 가장 쉬운 첫 행동은 무엇인가요?",
      choices: ["문제 1번 읽기", "전체를 한 번에 끝내기", "나중에 하기"],
      correctAnswer: "문제 1번 읽기",
      hint: "부담이 가장 작은 행동부터 고르면 시작하기 쉬워요.",
      correctFeedback: "좋아요. 첫 행동이 작을수록 시작하기 쉬워요. 이제 10분 실행으로 넘어갈 수 있어요.",
      wrongFeedback: "조금 더 작게 나눠볼까요? 지금 바로 할 수 있는 한 가지를 찾아요.",
      nextActionLabel: "학습 길로 돌아가기 →",
    },
  },
];

export const reviewItems: ReviewItem[] = [
  {
    id: "review-emotion-001",
    caseId: "case-emotion-001",
    title: "감정 카드 4종 미션",
    type: "정서 표현 자료 · 선택 질문 포함",
    state: "초안",
  },
  {
    id: "review-foundation-001",
    caseId: "case-foundation-001",
    title: "피자 지도 1/4 학습 자료",
    type: "시각 자료 · 확인 문제 포함",
    state: "검토 필요",
  },
  {
    id: "review-foundation-002",
    caseId: "case-foundation-001",
    title: "학부모용 결과 설명",
    type: "쉬운 표현으로 자동 변환",
    state: "초안",
  },
  {
    id: "review-older-001",
    caseId: "case-older-001",
    title: "과제 분해 체크리스트",
    type: "실행 계획 · 10분 타이머 포함",
    state: "생성 완료",
  },
];

export const sessionRecords: SessionRecord[] = [
  {
    id: "record-emotion-001",
    caseId: "case-emotion-001",
    session: "1차시",
    date: "2026. 4. 22.",
    durationMinutes: 25,
    understanding: "중",
    focus: "중",
    note: "그림 카드를 먼저 보여주자 선택 반응이 빨라졌고, 한 단어 표현을 시도했습니다.",
  },
  {
    id: "record-foundation-001",
    caseId: "case-foundation-001",
    session: "3차시",
    date: "2026. 4. 28.",
    durationMinutes: 45,
    understanding: "중",
    focus: "상",
    note: "피자 모형을 활용했을 때 전체와 부분을 구분하는 반응이 빨라졌습니다.",
  },
  {
    id: "record-older-001",
    caseId: "case-older-001",
    session: "2차시",
    date: "2026. 4. 29.",
    durationMinutes: 40,
    understanding: "상",
    focus: "중",
    note: "과제를 세 단계로 나누자 시작 지연이 줄었고, 첫 문제 풀이까지 이어졌습니다.",
  },
];

export const caseSteps: Array<{ key: CaseStatus; label: string }> = [
  { key: "intake", label: "신청 접수" },
  { key: "structured", label: "사례 구조화" },
  { key: "goal_set", label: "수업 목표 설정" },
  { key: "scene_review", label: "학습 자료 검토" },
  { key: "follow_up", label: "후속관리" },
];

export function getStudentContext(caseId?: string): StudentContext {
  const supportCase = supportCases.find((item) => item.id === caseId) ?? supportCases[0];
  const student = students.find((item) => item.id === supportCase.studentId);
  const scene = coachingScenes.find((item) => item.caseId === supportCase.id);

  if (!student || !scene) {
    throw new Error("Student demo context is incomplete.");
  }

  return { student, supportCase, scene };
}

export function getPrimaryStudentContext() {
  return getStudentContext(PRIMARY_STUDENT_CASE_ID);
}

export function getNextCaseId(caseId: string) {
  const index = supportCases.findIndex((item) => item.id === caseId);
  const nextIndex = index >= 0 ? (index + 1) % supportCases.length : 0;
  return supportCases[nextIndex].id;
}

export function getStudentCaseSummaries() {
  return supportCases.map((supportCase) => {
    const { student, scene } = getStudentContext(supportCase.id);

    return {
      caseId: supportCase.id,
      studentName: student.name,
      grade: student.grade,
      label: supportCase.caseType,
      title: scene.title,
      description: supportCase.primaryNeed,
    };
  });
}
