export type StudentSceneProfile = {
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
  accessCode?: string | null;
};

export type StudentSceneCase = {
  id: string;
  studentId: string;
  status: "intake" | "structured" | "goal_set" | "scene_review" | "follow_up";
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
  kind: "emotion" | "fraction" | "planner" | "clock" | "transit";
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
    | "image_quiz"
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
    | "explanation_choice"
    | "wrong_explanation_fix"
    | "card_match"
    | "realtime_roleplay"
    | "realtime_teach_back";
  assetRole?: "hero" | "stage_1" | "stage_2" | "stage_3" | "stage_4_realtime";
  imageUrl?: string | null;
  audioUrl?: string | null;
  audioSourceText?: string | null;
  kind: "concept" | "quiz" | "scenario" | "summary" | "ox" | "sequence" | "cardMatching" | "fillBlank" | "realtimeTeachBack";
  prompt: string;
  body?: string;
  choices?: string[];
  correctAnswer?: string;
  runtimeCorrectAnswer?: Record<string, unknown>;
  runtimeChoiceAnswers?: Record<string, Record<string, unknown>>;
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
  isCompleted?: boolean;
  rewardLabel: string;
  rewardProgress: number;
  assets?: Array<{
    assetId: string;
    assetRole: "hero" | "stage_1" | "stage_2" | "stage_3" | "stage_4_realtime";
    assetType?: "image" | "audio";
    alt: string;
    url?: string | null;
    sourceText?: string | null;
  }>;
  theme: SceneTheme;
  stages: Array<{
    step: number;
    title: string;
    subtitle: string;
    state: "done" | "current" | "locked";
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

export type StudentContext = {
  student: StudentSceneProfile;
  supportCase: StudentSceneCase;
  scene: CoachingScene;
};
