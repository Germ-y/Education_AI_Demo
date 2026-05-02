import { getContextSeed, getReviewableContent, getStudentMission, type MissionContent, type TemplateType } from "@/lib/api";
import { getAssetUrl, getTemplateRenderer, resolveStageAssets, validateMissionContent } from "@/lib/mission-content";
import type { SceneTheme, SceneVisual, StageQuestion, StudentContext } from "@/lib/student-scene-types";

type StudentRouteParams = {
  caseId?: string;
  contentId?: string;
  preview?: boolean;
};

const missionTheme: SceneTheme = {
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
};

const defaultStageColors = ["#ffd36b", "#94d86a", "#8fb8ff", "#f08a7a"];

const visualPresets: Record<SceneVisual["kind"], Array<{ label: string; caption: string }>> = {
  emotion: [
    { label: "보기", caption: "그림 단서" },
    { label: "고르기", caption: "짧은 선택" },
    { label: "말하기", caption: "한 문장" },
    { label: "연습", caption: "다시 시도" },
  ],
  fraction: [
    { label: "전체", caption: "전체 조각 보기" },
    { label: "부분", caption: "고른 조각 찾기" },
    { label: "쓰기", caption: "분수로 표현" },
    { label: "말하기", caption: "내 말로 설명" },
  ],
  planner: [
    { label: "상황", caption: "오늘 장면" },
    { label: "단서", caption: "먼저 볼 것" },
    { label: "행동", caption: "짧게 선택" },
    { label: "연습", caption: "직접 말하기" },
  ],
  clock: [
    { label: "짧은 바늘", caption: "먼저 보기" },
    { label: "긴 바늘", caption: "다음 보기" },
    { label: "약속 시간", caption: "2개 중 선택" },
    { label: "말하기", caption: "순서 설명" },
  ],
  transit: [
    { label: "정류장", caption: "상황 보기" },
    { label: "버스 번호", caption: "중요 단서" },
    { label: "도움 요청", caption: "짧게 말하기" },
    { label: "역할 연습", caption: "직접 말하기" },
  ],
};

export async function getStudentContextForRoute({ caseId, contentId, preview = false }: StudentRouteParams): Promise<StudentContext> {
  const seed = await getContextSeed();
  const resolvedContentId = contentId ?? resolveContentIdFromSeed(seed, caseId, { preview });
  if (!resolvedContentId) {
    throw new Error("학생에게 연결된 MissionContent가 없습니다.");
  }

  const mission = await getMissionForRoute(resolvedContentId, { allowReviewable: preview });
  const validation = validateMissionContent(mission);

  if (!validation.ok) {
    throw new Error(`MissionContent contract invalid: ${validation.errors.join(" ")}`);
  }

  const student = seed.students.find((item) => item.id === mission.studentId);
  const supportCase = seed.cases.find((item) => item.id === mission.caseId);
  const school = seed.schools.find((item) => item.schoolCode === student?.schoolCode);

  if (!student || !supportCase) {
    throw new Error("MissionContent와 연결된 학생/케이스 데이터를 찾지 못했습니다.");
  }

  return {
    student: {
      id: student.id,
      name: student.displayName,
      displayName: student.displayName,
      grade: student.gradeLabel ?? student.grade,
      school: school?.name ?? "학교 정보 확인 중",
      guardianName: "",
      phone: "",
      level: 1,
      rewardTokens: 0,
      nextRewardTokens: 10,
      attendanceRate: student.attendanceRate ?? 0,
      understandingRate: 0,
      interests: readStringArray(student.profileJson.interests),
      strengths: student.strengths ?? [],
      accessCode: student.accessCode ?? null,
    },
    supportCase: {
      id: supportCase.id,
      studentId: supportCase.studentId,
      status: "scene_review",
      statusLabel: "학습 준비",
      caseType: student.trackLabel ?? student.studentTypeLabel ?? (student.studentType === "learning_focus" ? "학습지원형" : "일상생활 지원형"),
      primaryNeed: student.primaryNeed,
      sessionGoal: mission.sessionGoal,
      supportStrategy: "승인된 정적 콘텐츠와 4단계 실시간 발화 연습",
      nextAction: "오늘 미션 진행",
      riskNote: "학생에게 진단 표현을 노출하지 않음",
      challengeTags: [],
      planTags: [],
    },
    scene: missionToScene(mission),
  };
}

function missionToScene(mission: MissionContent): StudentContext["scene"] {
  const sortedStages = [...mission.stages].sort((left, right) => left.step - right.step);

  return {
    id: `scene-${mission.id}`,
    contentId: mission.id,
    caseId: mission.caseId,
    contentType: mission.contentType,
    status: mission.status === "published" ? "published" : "teacher_review",
    title: mission.title,
    subtitle: mission.sessionGoal,
    pathHeadline: mission.contentType === "learning_focus" ? "오늘은 개념을 열어봐요" : "오늘은 생활 속 연습을 해요",
    pathDescription: mission.sessionGoal,
    stageHeadline: mission.title,
    missionTitle: mission.title,
    missionDescription: mission.sessionGoal,
    totalSteps: 4,
    currentStep: 1,
    rewardLabel: "미션 토큰",
    rewardProgress: 0,
    assets: mission.assets
      .map((asset) => ({
        assetId: asset.id,
        assetRole: asset.assetRole,
        assetType: asset.assetType,
        alt: asset.assetRole,
        url: getAssetUrl(asset),
        sourceText: asset.sourceText,
      })),
    theme: missionTheme,
    stages: sortedStages.map((stage) => ({
      step: stage.step,
      title: stage.studentTitle,
      subtitle: stage.studentInstruction,
      state: stage.step === 1 ? "current" : "locked",
    })),
    visual: buildMissionVisual(mission),
    question: {
      prompt: sortedStages[0]?.studentInstruction ?? mission.sessionGoal,
      choices: ["좋아요", "다시 볼래요", "넘어갈래요"],
      correctAnswer: "좋아요",
      hint: "오늘 미션을 천천히 시작해봐요.",
      correctFeedback: "좋아요. 다음 단계로 갈 수 있어요.",
      wrongFeedback: "괜찮아요. 다시 천천히 봐요.",
      nextActionLabel: "학습 길로 돌아가기 →",
    },
    stageQuestions: sortedStages.map((stage) => stageToQuestion(mission, stage)),
  };
}

function buildMissionVisual(mission: MissionContent): SceneVisual {
  const missionText = [
    mission.title,
    mission.sessionGoal,
    ...mission.stages.flatMap((stage) => [stage.studentTitle, stage.studentInstruction, JSON.stringify(stage.templateJson)]),
  ].join(" ");
  const visualKind = inferVisualKind(mission, missionText);
  const preset = visualPresets[visualKind];

  return {
    kind: visualKind,
    label: "미션 이미지",
    helperLabel: "오늘의 단계",
    activeIndex: 0,
    segments: preset.map((item, index) => ({
      ...item,
      color: defaultStageColors[index] ?? defaultStageColors[0],
    })),
  };
}

function inferVisualKind(mission: MissionContent, missionText: string): SceneVisual["kind"] {
  if (/시계|시침|분침|짧은 바늘|긴 바늘|약속 시간/.test(missionText)) return "clock";
  if (/버스|정류장|센터|이동|도움 요청|안내 직원/.test(missionText)) return "transit";
  if (/분수|조각|전체|부분|1\/4|사분의/.test(missionText)) return "fraction";
  if (mission.contentType === "life_support") return "planner";
  return "emotion";
}

async function getMissionForRoute(contentId: string, options: { allowReviewable: boolean }) {
  try {
    return await getStudentMission(contentId);
  } catch (error) {
    const content = await getReviewableContent(contentId);
    if (options.allowReviewable || content.status === "published") {
      return content;
    }
    throw error;
  }
}

function resolveContentIdFromSeed(seed: Awaited<ReturnType<typeof getContextSeed>>, caseId?: string, options: { preview: boolean } = { preview: false }) {
  const isAllowed = (mapping: Awaited<ReturnType<typeof getContextSeed>>["mappings"][number]) =>
    options.preview || mapping.status === "published";

  if (caseId) {
    const matched = findLatestMapping(seed.mappings, (mapping) => mapping.caseId === caseId && isAllowed(mapping));
    if (matched) return matched.contentId;
  }

  return findLatestMapping(seed.mappings, isAllowed)?.contentId;
}

function findLatestMapping(
  mappings: Awaited<ReturnType<typeof getContextSeed>>["mappings"],
  predicate: (mapping: Awaited<ReturnType<typeof getContextSeed>>["mappings"][number]) => boolean = () => true,
) {
  return [...mappings]
    .filter(predicate)
    .sort((left, right) => toTimestamp(right.updatedAt) - toTimestamp(left.updatedAt))[0];
}

function toTimestamp(value?: string | null) {
  if (!value) return 0;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function stageToQuestion(mission: MissionContent, stage: MissionContent["stages"][number]): StageQuestion {
  const renderer = getTemplateRenderer(stage.templateType);
  const template = stage.templateJson;
  const question = readString(template.question) ?? readString(template.missionText) ?? stage.studentInstruction;
  const correctAnswer = readAnswer(stage.templateType, template);
  const { image, audio } = resolveStageAssets(mission, stage);

  return {
    step: stage.step,
    stageId: stage.id,
    stageRole: stage.stageRole,
    templateType: stage.templateType,
    assetRole: stage.step === 4 ? "stage_4_realtime" : `stage_${stage.step}`,
    imageUrl: getAssetUrl(image),
    audioUrl: getAssetUrl(audio),
    audioSourceText: audio?.sourceText ?? undefined,
    kind:
      renderer === "sequence_ordering"
        ? "sequence"
        : renderer === "card_match"
          ? "cardMatching"
          : renderer === "blank_fill"
            ? "fillBlank"
            : renderer === "realtime_practice"
              ? "realtimeTeachBack"
              : renderer === "static_intro"
                ? "concept"
                : "quiz",
    prompt: question,
    body: readString(template.storyText) ?? readString(template.shortExplanation) ?? readString(template.scenario),
    choices: readChoices(template),
    correctAnswer,
    runtimeCorrectAnswer: readRuntimeCorrectAnswer(stage.templateType, template),
    runtimeChoiceAnswers: readChoiceAnswerMap(template),
    hint: stage.studentInstruction,
    correctFeedback: readString(template.correctFeedback) ?? "좋아요. 다음 단계로 이동할 수 있어요.",
    wrongFeedback: readString(template.wrongFeedback) ?? "괜찮아요. 다시 한 번 살펴봐요.",
    completionTitle: `${stage.studentTitle} 완료`,
    completionMessage: "이 단계를 잘 마쳤어요.",
    actionLabel: renderer === "static_intro" ? "확인했어요" : undefined,
    conceptCards: renderer === "static_intro" ? [{ title: stage.studentTitle, body: stage.studentInstruction }] : undefined,
    sequenceItems: readSequenceItems(template),
    matchingPairs: readMatchingPairs(template),
    fillBlankText: readFillBlankText(template),
    fillOptions: readFillOptions(template),
    realtimePracticeSpec: stage.realtimeSpec
      ? {
          role: stage.realtimeSpec.aiRole,
          firstPrompt: stage.realtimeSpec.openingLine,
          rubric: stage.realtimeSpec.rubric.map((item) => item.label),
          timeLimitSeconds: stage.realtimeSpec.maxDurationSec,
        }
      : undefined,
    visualActiveIndex: Math.max(0, stage.step - 1),
  };
}

function readString(value: unknown) {
  return typeof value === "string" ? value : undefined;
}

function readStringArray(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function readChoices(template: Record<string, unknown>) {
  const choices = template.choices;
  if (Array.isArray(choices)) {
    return choices
      .map((choice) => {
        if (typeof choice === "string") return choice;
        if (choice && typeof choice === "object" && "text" in choice && typeof choice.text === "string") return choice.text;
        if (choice && typeof choice === "object" && "label" in choice && typeof choice.label === "string") return choice.label;
        return null;
      })
      .filter((choice): choice is string => Boolean(choice));
  }

  const rightCards = template.rightCards;
  if (Array.isArray(rightCards)) {
    return rightCards
      .map((card) => {
        if (typeof card === "string") return card;
        if (card && typeof card === "object" && "text" in card && typeof card.text === "string") return card.text;
        if (card && typeof card === "object" && "label" in card && typeof card.label === "string") return card.label;
        return null;
      })
      .filter((choice): choice is string => Boolean(choice));
  }

  return undefined;
}

function readAnswer(templateType: TemplateType, template: Record<string, unknown>) {
  if (typeof template.answer === "string") return readChoiceTextById(template, template.answer) ?? template.answer;
  if (Array.isArray(template.answerOrder)) return template.answerOrder.map(String).join(">");
  if (templateType === "blank_fill") {
    const answer = readAcceptedFractionAnswer(template);
    if (answer) return `${answer.numerator}|${answer.denominator}`;
  }
  return undefined;
}

function readRuntimeCorrectAnswer(templateType: TemplateType, template: Record<string, unknown>) {
  if (typeof template.answer === "string") return { choiceId: template.answer };
  if (Array.isArray(template.answerOrder)) return { order: template.answerOrder.map(String) };
  if (templateType === "blank_fill") {
    const answer = readAcceptedFractionAnswer(template);
    if (answer) return answer;
  }
  return undefined;
}

function readChoiceAnswerMap(template: Record<string, unknown>) {
  const choices = template.choices;
  if (!Array.isArray(choices)) return undefined;

  const answers: Record<string, Record<string, unknown>> = {};
  for (const choice of choices) {
    if (!choice || typeof choice !== "object" || !("id" in choice)) continue;
    const text =
      "text" in choice && typeof choice.text === "string"
        ? choice.text
        : "label" in choice && typeof choice.label === "string"
          ? choice.label
          : null;
    if (text) answers[text] = { choiceId: String(choice.id) };
  }

  return Object.keys(answers).length > 0 ? answers : undefined;
}

function readChoiceTextById(template: Record<string, unknown>, answerId: string) {
  const choices = template.choices;
  if (!Array.isArray(choices)) return undefined;

  const matchedChoice = choices.find(
    (choice) => choice && typeof choice === "object" && "id" in choice && String(choice.id) === answerId,
  );

  if (!matchedChoice || typeof matchedChoice !== "object" || !("text" in matchedChoice)) return undefined;
  return typeof matchedChoice.text === "string" ? matchedChoice.text : undefined;
}

function readSequenceItems(template: Record<string, unknown>) {
  const cards = template.cards;
  if (!Array.isArray(cards)) return undefined;
  return cards
    .map((card) => {
      if (!card || typeof card !== "object" || !("id" in card) || !("text" in card)) return null;
      return { id: String(card.id), label: String(card.text) };
    })
    .filter((item): item is { id: string; label: string } => Boolean(item));
}

function readMatchingPairs(template: Record<string, unknown>) {
  const pairs = template.pairs;
  if (Array.isArray(pairs)) {
    return pairs
      .map((pair) => {
        if (!pair || typeof pair !== "object") return null;
        if (!("leftId" in pair) || !("left" in pair) || !("rightId" in pair) || !("right" in pair)) return null;
        return {
          leftId: String(pair.leftId),
          left: String(pair.left),
          rightId: String(pair.rightId),
          right: String(pair.right),
        };
      })
      .filter((item): item is { leftId: string; left: string; rightId: string; right: string } => Boolean(item));
  }

  const leftCards = template.leftCards;
  const rightCards = template.rightCards;
  const matches = template.matches;
  if (!Array.isArray(leftCards) || !Array.isArray(rightCards) || !Array.isArray(matches)) return undefined;

  return matches
    .map((pair) => {
      if (!pair || typeof pair !== "object") return null;
      if (!("leftId" in pair) || !("rightId" in pair)) return null;
      const left = findCardLabel(leftCards, String(pair.leftId));
      const right = findCardLabel(rightCards, String(pair.rightId));
      if (!left || !right) return null;
      return {
        leftId: String(pair.leftId),
        left,
        rightId: String(pair.rightId),
        right,
      };
    })
    .filter((item): item is { leftId: string; left: string; rightId: string; right: string } => Boolean(item));
}

function findCardLabel(cards: unknown[], id: string) {
  const card = cards.find((item) => item && typeof item === "object" && "id" in item && String(item.id) === id);
  if (!card || typeof card !== "object") return null;
  if ("text" in card && typeof card.text === "string") return card.text;
  if ("label" in card && typeof card.label === "string") return card.label;
  return null;
}

function readFillBlankText(template: Record<string, unknown>) {
  const sentence = readString(template.sentence) ?? readString(template.question);
  if (!sentence) return undefined;

  return sentence.split(/(__|\[A\]|\[B\])/g).map((part) => ({
    kind: part === "__" || part === "[A]" || part === "[B]" ? "blank" as const : "text" as const,
    value: part,
  }));
}

function readFillOptions(template: Record<string, unknown>) {
  const tiles = template.tiles;
  if (Array.isArray(tiles)) {
    return tiles.filter((tile): tile is string => typeof tile === "string").map((tile) => ({ id: tile, label: tile }));
  }

  const answer = readAcceptedFractionAnswer(template);
  if (answer) {
    const values = [answer.numerator, answer.denominator].filter(
      (value): value is string => typeof value === "string" && value.length > 0,
    );

    return Array.from(new Set(values)).map((value) => ({
      id: value,
      label: value,
    }));
  }

  return undefined;
}

function readAcceptedFractionAnswer(template: Record<string, unknown>) {
  const acceptedAnswers = template.acceptedAnswers;
  if (!Array.isArray(acceptedAnswers)) return undefined;

  const first = acceptedAnswers[0];
  if (!first || typeof first !== "object" || !("numerator" in first) || !("denominator" in first)) return undefined;

  return {
    numerator: String(first.numerator),
    denominator: String(first.denominator),
  };
}
