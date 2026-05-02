import { backendAdapter } from "@/lib/api/backend-adapter";
import type {
  AssetRole,
  Choice as ApiChoice,
  ContentAsset,
  ContentStage,
  MissionContent,
  StudentCaseFile,
  StudentListItem,
  StudentProfile as ApiStudentProfile,
  TemplateType,
} from "@/lib/api/contracts";
import type {
  CoachingScene,
  SceneTheme,
  SceneVisual,
  StageQuestion,
  StudentContext,
  StudentProfile,
  SupportCase,
} from "@/lib/demo-data";

const DEMO_STUDENT_ACCESS_CODES: Record<string, string> = {
  student_learning_fraction: "STAR-001",
  student_life_bus: "STAR-002",
  student_learning_clock: "STAR-003",
};

const DEFAULT_STUDENT_ID = "student_learning_fraction";

export type StudentScenarioCard = {
  studentId: string;
  studentName: string;
  displayName: string;
  grade: string;
  schoolName: string;
  label: string;
  contentStatus: string;
};

export type StudentScenarioResult =
  | {
      kind: "ready";
      context: StudentContext;
      studentId: string;
      contentId: string;
    }
  | {
      kind: "empty";
      student: StudentProfile;
      supportCase: SupportCase;
      studentId: string;
      message: string;
    };

export async function getBackendStudentCaseSummaries(): Promise<StudentScenarioCard[]> {
  const students = await backendAdapter.getTeacherStudents();

  return students.map((student) => ({
    studentId: student.studentId,
    studentName: student.displayName,
    displayName: student.displayName,
    grade: formatGrade(student.grade),
    schoolName: student.schoolName ?? "학교 정보 확인 중",
    label: contentTypeLabel(student.studentType),
    contentStatus: student.latestContentStatus,
  }));
}

export async function getBackendStudentScenario(studentId?: string, contentId?: string): Promise<StudentScenarioResult> {
  const resolvedStudentId = resolveStudentId(studentId);

  if (contentId) {
    const caseFile = await backendAdapter.getTeacherStudent(resolvedStudentId);
    const mission = await backendAdapter.getReviewableContent(contentId);
    if (mission.studentId !== resolvedStudentId) {
      throw new Error(`요청한 학생과 콘텐츠 학생이 다릅니다: ${resolvedStudentId} / ${mission.studentId}`);
    }

    return {
      kind: "ready",
      studentId: resolvedStudentId,
      contentId: mission.id,
      context: {
        student: mapStudentProfile(caseFile),
        supportCase: mapSupportCase(caseFile, mission),
        scene: mapMissionScene(caseFile, mission),
      },
    };
  }

  const studentToken = await getStudentAccessToken(resolvedStudentId);

  const caseFile = await backendAdapter.getTeacherStudent(resolvedStudentId);
  const missions = await backendAdapter.getTodayStudentMissions({ token: studentToken });

  if (missions.length === 0) {
    return {
      kind: "empty",
      studentId: resolvedStudentId,
      student: mapStudentProfile(caseFile),
      supportCase: mapSupportCase(caseFile, null),
      message: "아직 학생에게 배포된 오늘의 미션이 없습니다. 교사용 화면에서 자료를 생성하고 승인한 뒤 다시 확인해 주세요.",
    };
  }

  const mission = await backendAdapter.getStudentMission(missions[0].contentId, {
    token: studentToken,
  });

  return {
    kind: "ready",
    studentId: resolvedStudentId,
    contentId: mission.id,
    context: {
      student: mapStudentProfile(caseFile),
      supportCase: mapSupportCase(caseFile, mission),
      scene: mapMissionScene(caseFile, mission),
    },
  };
}

async function getStudentAccessToken(studentId: string): Promise<string> {
  const accessCode = DEMO_STUDENT_ACCESS_CODES[studentId];
  if (!accessCode) {
    throw new Error(`데모 학생 접근 코드가 없습니다: ${studentId}`);
  }

  const login = await backendAdapter.studentAccess({ accessCode });
  return login.session.accessToken;
}

function resolveStudentId(studentId: string | undefined): string {
  if (studentId && DEMO_STUDENT_ACCESS_CODES[studentId]) return studentId;
  return DEFAULT_STUDENT_ID;
}

function mapStudentProfile(caseFile: StudentCaseFile): StudentProfile {
  const profile = caseFile.profile;
  const profileJson = profile.profileJson;
  const interests = stringArray(profileJson.interests);
  const strengths = profile.studentType === "life_support" ? ["시각 순서", "역할극 반응"] : ["그림 단서", "짧은 단계"];

  return {
    id: profile.id,
    name: profile.displayName,
    displayName: profile.displayName,
    grade: formatGrade(profile.grade),
    school: caseFile.schoolContext?.school.name ?? schoolNameFromProfile(profile),
    guardianName: "보호자",
    phone: "-",
    level: profile.studentType === "life_support" ? 2 : 3,
    rewardTokens: profile.studentType === "life_support" ? 96 : 120,
    nextRewardTokens: 30,
    attendanceRate: 92,
    understandingRate: profile.studentType === "life_support" ? 68 : 76,
    interests,
    strengths,
  };
}

function mapSupportCase(caseFile: StudentCaseFile, mission: MissionContent | null): SupportCase {
  const memory = caseFile.memoryCard;
  const challengeTags = memory?.learningProblemTypes ?? [caseFile.profile.primaryNeed];
  const planTags = caseFile.plannerItems.map((item) => item.goalText).slice(0, 3);

  return {
    id: caseFile.openCase.id,
    studentId: caseFile.profile.id,
    status: mission ? "scene_review" : "structured",
    statusLabel: mission ? "배포 자료 확인" : "자료 생성 필요",
    caseType: contentTypeLabel(caseFile.profile.studentType),
    primaryNeed: caseFile.profile.primaryNeed,
    sessionGoal: mission?.sessionGoal ?? caseFile.openCase.currentGoal,
    supportStrategy: memory?.effectiveExplanationStyles.join(", ") ?? "학생 반응을 보고 짧은 단계로 진행",
    nextAction: mission ? "학생 미션 수행 후 결과 확인" : "교사용 화면에서 오늘의 미션 생성",
    riskNote: memory?.emotionalStateNote ?? "초기 데이터 수집 중입니다.",
    challengeTags,
    planTags: planTags.length > 0 ? planTags : ["다음 회기 목표 확인"],
  };
}

function mapMissionScene(caseFile: StudentCaseFile, mission: MissionContent): CoachingScene {
  const theme = themeForContentType(mission.contentType);
  const stages = [...mission.stages].sort((a, b) => a.step - b.step);
  const firstQuestion = mapStageQuestion(stages[0], mission, 0);

  return {
    id: mission.id,
    contentId: mission.id,
    caseId: mission.caseId,
    contentType: mission.contentType,
    status: mission.status === "published" ? "published" : "teacher_review",
    title: mission.title,
    subtitle: mission.sessionGoal,
    pathHeadline: mission.contentType === "life_support" ? "오늘의 생활 미션 길을 따라가요" : "오늘의 학습 미션 길을 따라가요",
    pathDescription: mission.sessionGoal,
    stageHeadline: mission.contentType === "life_support" ? "상황을 보고 차근차근 연습해요" : "개념을 보고 직접 풀어봐요",
    missionTitle: mission.title,
    missionDescription: mission.sessionGoal,
    totalSteps: mission.totalSteps,
    currentStep: 1,
    rewardLabel: "별 토큰",
    rewardProgress: caseFile.profile.studentType === "life_support" ? 64 : 78,
    assets: mission.assets.map((asset) => ({
      assetId: asset.id,
      assetRole: asset.assetRole,
      assetType: asset.assetType,
      alt: `${mission.title} ${asset.assetRole}`,
      url: normalizeAssetUrl(asset.previewUrl ?? asset.storageUrl),
      sourceText: asset.sourceText,
    })),
    theme,
    stages: stages.map((stage) => ({
      step: stage.step,
      title: stage.studentTitle,
      subtitle: stage.studentInstruction,
      state: stage.step === 1 ? "current" : "locked",
    })),
    visual: visualForMission(mission),
    question: {
      prompt: firstQuestion.prompt,
      choices: firstQuestion.choices ?? [],
      correctAnswer: firstQuestion.correctAnswer ?? "",
      hint: firstQuestion.hint,
      correctFeedback: firstQuestion.correctFeedback,
      wrongFeedback: firstQuestion.wrongFeedback,
      nextActionLabel: firstQuestion.actionLabel ?? "다음 단계로",
    },
    stageQuestions: stages.map((stage, index) => mapStageQuestion(stage, mission, index)),
  };
}

function mapStageQuestion(stage: ContentStage, mission: MissionContent, index: number): StageQuestion {
  const template = stage.templateJson;
  const assetRole = assetRoleForStage(stage.step);
  const imageAsset = findAsset(mission.assets, assetRole, "image");
  const audioAsset = findAsset(mission.assets, assetRole, "audio");
  const questionText = asString(template.question) ?? asString(template.missionText) ?? stage.studentInstruction;
  const choices = parseChoices(template.choices);
  const answer = asString(template.answer);
  const correctAnswer = answer ? (choices.find((choice) => choice.id === answer)?.text ?? answer) : undefined;
  const common = {
    step: stage.step,
    stageId: stage.id,
    stageRole: stage.stageRole,
    templateType: stage.templateType,
    assetRole,
    imageUrl: imageAsset?.previewUrl ?? imageAsset?.storageUrl ?? null,
    audioUrl: audioAsset?.previewUrl ?? audioAsset?.storageUrl ?? null,
    audioSourceText: audioAsset?.sourceText ?? null,
    prompt: questionText,
    hint: hintForTemplate(stage.templateType),
    correctFeedback: asString(template.correctFeedback) ?? "좋아요. 다음 단계로 이어가요.",
    wrongFeedback: asString(template.wrongFeedback) ?? "한 번 더 살펴보고 다시 골라볼까요?",
    completionTitle: "좋아요!",
    completionMessage: stage.step === 4 ? "실시간 연습까지 마쳤어요." : "이번 단계를 완료했어요.",
    actionLabel: stage.step === 4 ? "실시간 연습 시작하기" : "확인했어요",
    visualActiveIndex: Math.min(index, 3),
  } satisfies Partial<StageQuestion>;

  if (stage.templateType === "sequence_ordering") {
    const cards = parseCards(template.cards);
    const answerOrder = stringArray(template.answerOrder);
    return {
      ...common,
      kind: "sequence",
      body: asString(template.question) ?? stage.studentInstruction,
      sequenceItems: cards,
      correctAnswer: answerOrder.join(">"),
    };
  }

  if (stage.templateType === "card_match") {
    const pairs = parseMatchingPairs(template);
    return {
      ...common,
      kind: "cardMatching",
      body: asString(template.question) ?? stage.studentInstruction,
      matchingPairs: pairs,
      correctAnswer: pairs.map((pair) => `${pair.leftId}:${pair.rightId}`).join("|"),
    };
  }

  if (stage.templateType === "blank_fill") {
    const accepted = firstAcceptedAnswer(template.acceptedAnswers);
    const fillOptions = uniqueStrings([...stringArray(template.tiles), accepted.numerator, accepted.denominator, "2", "3", "4"])
      .slice(0, 4)
      .map((value) => ({ id: value, label: value }));

    return {
      ...common,
      kind: "fillBlank",
      body: stage.studentInstruction,
      fillBlankText: fillBlankText(asString(template.question) ?? "__ / __"),
      fillOptions,
      correctAnswer: `${accepted.numerator}|${accepted.denominator}`,
    };
  }

  if (stage.templateType === "image_quiz") {
    return {
      ...common,
      kind: mission.contentType === "life_support" ? "scenario" : "quiz",
      body: asString(template.question) ?? stage.studentInstruction,
      choices: choices.map((choice) => choice.text),
      correctAnswer,
      actionLabel: "정답 확인",
    };
  }

  if (stage.templateType === "realtime_roleplay" || stage.templateType === "realtime_teach_back") {
    const spec = stage.realtimeSpec;
    return {
      ...common,
      kind: "realtimeTeachBack",
      prompt: spec?.practiceTitle ?? stage.studentTitle,
      body: spec?.situationText ?? stage.studentInstruction,
      hint: spec?.studentGoal ?? "AI와 한 번씩 말하며 연습해요.",
      correctAnswer: "realtime-started",
      realtimePracticeSpec: spec
        ? {
            role: spec.aiRole,
            firstPrompt: spec.openingLine,
            rubric: spec.rubric.map((item) => item.label),
            timeLimitSeconds: spec.maxDurationSec,
          }
        : undefined,
    };
  }

  if (stage.templateType === "scenario_intro" || stage.templateType === "concept_intro") {
    return {
      ...common,
      kind: "concept",
      body: asString(template.storyText) ?? stage.studentInstruction,
      conceptCards: [
        { title: stage.studentTitle, body: asString(template.missionText) ?? stage.studentInstruction },
        { title: "오늘 목표", body: mission.sessionGoal },
      ],
      scenarioLines: asString(template.storyText)
        ? [{ speaker: mission.contentType === "life_support" ? "상황" : "별이", text: asString(template.storyText) as string }]
        : undefined,
    };
  }

  return {
    ...common,
    kind: mission.contentType === "life_support" ? "scenario" : "quiz",
    body: stage.studentInstruction,
    choices: choices.map((choice) => choice.text),
    correctAnswer,
    scenarioLines:
      mission.contentType === "life_support"
        ? [{ speaker: "상황", text: stage.studentInstruction }]
        : undefined,
  };
}

function findAsset(assets: ContentAsset[], assetRole: AssetRole, assetType: "image" | "audio"): ContentAsset | undefined {
  const asset = assets.find((candidate) => candidate.assetRole === assetRole && candidate.assetType === assetType);
  if (!asset) return undefined;

  return {
    ...asset,
    storageUrl: normalizeAssetUrl(asset.storageUrl) ?? asset.storageUrl,
    previewUrl: normalizeAssetUrl(asset.previewUrl ?? asset.storageUrl),
  };
}

function normalizeAssetUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (/^https?:\/\//.test(url)) return url;

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:4000";
  if (url.startsWith("/examples/generated/")) {
    return `${apiBaseUrl}${url.replace("/examples/generated", "/generated")}`;
  }
  if (url.startsWith("/generated/")) return `${apiBaseUrl}${url}`;
  return url;
}

function assetRoleForStage(step: 1 | 2 | 3 | 4): AssetRole {
  return step === 4 ? "stage_4_realtime" : `stage_${step}`;
}

function parseChoices(value: unknown): ApiChoice[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item, index) => {
      if (typeof item === "string") return { id: String(index + 1), text: item };
      if (!isRecord(item)) return null;
      const id = asString(item.id) ?? String(index + 1);
      const text = asString(item.text) ?? asString(item.label);
      return text ? { id, text } : null;
    })
    .filter((item): item is ApiChoice => item !== null);
}

function parseCards(value: unknown): Array<{ id: string; label: string; caption?: string }> {
  if (!Array.isArray(value)) return [];
  return value
    .map((item, index) => {
      if (typeof item === "string") return { id: String(index + 1), label: item };
      if (!isRecord(item)) return null;
      const id = asString(item.id) ?? String(index + 1);
      const label = asString(item.text) ?? asString(item.label);
      const caption = asString(item.caption);
      return label ? { id, label, caption } : null;
    })
    .filter((item): item is { id: string; label: string; caption?: string } => item !== null);
}

function parseMatchingPairs(template: Record<string, unknown>): Array<{ leftId: string; left: string; rightId: string; right: string }> {
  const legacyPairs = parseLegacyMatchingPairs(template.matchingPairs);
  if (legacyPairs.length > 0) return legacyPairs;

  const leftCards = parseCards(template.leftCards);
  const rightCards = parseCards(template.rightCards);
  const matches = isRecord(template.matches) ? template.matches : {};

  return Object.entries(matches)
    .map(([leftId, rightIdValue]) => {
      const rightId = asString(rightIdValue);
      const left = leftCards.find((card) => card.id === leftId);
      const right = rightCards.find((card) => card.id === rightId);
      return left && right ? { leftId, left: left.label, rightId: right.id, right: right.label } : null;
    })
    .filter((item): item is { leftId: string; left: string; rightId: string; right: string } => item !== null);
}

function parseLegacyMatchingPairs(value: unknown): Array<{ leftId: string; left: string; rightId: string; right: string }> {
  if (!Array.isArray(value)) return [];
  return value
    .map((item, index) => {
      if (!isRecord(item)) return null;
      const leftId = asString(item.leftId) ?? `left_${index + 1}`;
      const rightId = asString(item.rightId) ?? `right_${index + 1}`;
      const left = asString(item.left) ?? asString(item.leftText);
      const right = asString(item.right) ?? asString(item.rightText);
      return left && right ? { leftId, left, rightId, right } : null;
    })
    .filter((item): item is { leftId: string; left: string; rightId: string; right: string } => item !== null);
}

function firstAcceptedAnswer(value: unknown): { numerator: string; denominator: string } {
  if (Array.isArray(value) && isRecord(value[0])) {
    return {
      numerator: asString(value[0].numerator) ?? "1",
      denominator: asString(value[0].denominator) ?? "4",
    };
  }
  return { numerator: "1", denominator: "4" };
}

function fillBlankText(question: string): StageQuestion["fillBlankText"] {
  const [before, afterFirst = "", afterSecond = ""] = question.split("__");
  return [
    { kind: "text", value: before },
    { kind: "blank", value: "numerator" },
    { kind: "text", value: afterFirst },
    { kind: "blank", value: "denominator" },
    { kind: "text", value: afterSecond },
  ];
}

function visualForMission(mission: MissionContent): SceneVisual {
  if (mission.contentType === "life_support") {
    return {
      kind: "planner",
      label: "생활 미션",
      helperLabel: "순서 확인",
      activeIndex: 0,
      segments: [
        { label: "상황 보기", caption: "어디에 있는지 확인", color: "#b8defa" },
        { label: "단서 찾기", caption: "중요한 정보 고르기", color: "#f7d98b" },
        { label: "행동 고르기", caption: "해야 할 일 정하기", color: "#bddca7" },
        { label: "연습하기", caption: "AI와 말해보기", color: "#f1b7c8" },
      ],
    };
  }

  return {
    kind: "fraction",
    label: "분수 미션",
    helperLabel: "전체와 부분",
    activeIndex: 0,
    segments: [
      { label: "1", caption: "고른 조각", color: "#ffe066" },
      { label: "2", caption: "같은 크기", color: "#ffd08a" },
      { label: "3", caption: "같은 크기", color: "#f5bd63" },
      { label: "4", caption: "같은 크기", color: "#f0a54b" },
    ],
  };
}

function themeForContentType(contentType: MissionContent["contentType"]): SceneTheme {
  if (contentType === "life_support") {
    return {
      accent: "#2563eb",
      accentStrong: "#1d4ed8",
      accentSoft: "#dbeafe",
      accentPale: "#eff6ff",
      border: "#bfdbfe",
      highlight: "#fef3c7",
      highlightText: "#7c4a03",
      path: "#2563eb",
      pathLight: "#bfdbfe",
      glow: "#93c5fd",
    };
  }

  return {
    accent: "#27ae60",
    accentStrong: "#15803d",
    accentSoft: "#dcfce7",
    accentPale: "#f0fdf4",
    border: "#bbf7d0",
    highlight: "#fff0b8",
    highlightText: "#6b4b12",
    path: "#27ae60",
    pathLight: "#d9ebc9",
    glow: "#b6f1c6",
  };
}

function hintForTemplate(templateType: TemplateType): string {
  if (templateType === "blank_fill") return "위에는 고른 것, 아래에는 전체 수를 넣어요.";
  if (templateType === "sequence_ordering") return "먼저 해야 하는 일을 앞으로 놓아보세요.";
  if (templateType === "realtime_roleplay" || templateType === "realtime_teach_back") return "상황 이미지를 보고 AI에게 한 문장씩 말해요.";
  if (templateType === "scenario_intro" || templateType === "concept_intro") return "그림과 짧은 이야기를 먼저 확인해요.";
  return "그림에서 중요한 단서를 찾아보세요.";
}

function formatGrade(grade: string): string {
  const match = /^(elementary|middle|high)_(\d+)$/.exec(grade);
  if (!match) return grade;
  const label = match[1] === "elementary" ? "초" : match[1] === "middle" ? "중" : "고";
  return `${label}${match[2]}`;
}

function contentTypeLabel(contentType: StudentListItem["studentType"]): string {
  return contentType === "life_support" ? "일상생활 지원형" : "학습집중형";
}

function schoolNameFromProfile(profile: ApiStudentProfile): string {
  if (profile.schoolCode === "8811046") return "영주중앙초등학교";
  if (profile.schoolCode === "8811058") return "영주중학교";
  if (profile.schoolCode === "8811067") return "영주가흥초등학교";
  return "학교 정보 확인 중";
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean)));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
