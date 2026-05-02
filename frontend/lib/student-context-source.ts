import { getContextSeed, getStudentMission, type MissionContent, type TemplateType } from "@/lib/api";
import { getTemplateRenderer, validateMissionContent } from "@/lib/mission-content";
import {
  getStudentContext,
  type SceneTheme,
  type SceneVisual,
  type StageQuestion,
  type StudentContext,
} from "@/lib/demo-data";

type StudentRouteParams = {
  caseId?: string;
  contentId?: string;
};

const fallbackTheme: SceneTheme = {
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

const fallbackVisual: SceneVisual = {
  kind: "fraction",
  label: "미션 이미지",
  helperLabel: "오늘의 단계",
  activeIndex: 0,
  segments: [
    { label: "1", caption: "첫 단계", color: "#ffd36b" },
    { label: "2", caption: "두 번째", color: "#94d86a" },
    { label: "3", caption: "세 번째", color: "#8fb8ff" },
    { label: "4", caption: "연습", color: "#f08a7a" },
  ],
};

export async function getStudentContextForRoute({ caseId, contentId }: StudentRouteParams): Promise<StudentContext> {
  if (!contentId) return getStudentContext(caseId);

  const [seed, mission] = await Promise.all([getContextSeed(), getStudentMission(contentId)]);
  const validation = validateMissionContent(mission);

  if (!validation.ok) {
    throw new Error(`MissionContent contract invalid: ${validation.errors.join(" ")}`);
  }

  const student = seed.students.find((item) => item.id === mission.studentId);
  const supportCase = seed.cases.find((item) => item.id === mission.caseId);
  const school = seed.schools.find((item) => item.schoolCode === student?.schoolCode);

  if (!student || !supportCase) {
    return getStudentContext(caseId);
  }

  return {
    student: {
      id: student.id,
      name: student.displayName,
      displayName: student.displayName,
      grade: student.grade,
      school: school?.name ?? "데모 학교",
      guardianName: "",
      phone: "",
      level: 1,
      rewardTokens: 0,
      nextRewardTokens: 10,
      attendanceRate: 90,
      understandingRate: 50,
      interests: readStringArray(student.profileJson.interests),
      strengths: ["짧은 단계로 학습하기"],
    },
    supportCase: {
      id: supportCase.id,
      studentId: supportCase.studentId,
      status: "scene_review",
      statusLabel: "학습 준비",
      caseType: student.studentType === "learning_focus" ? "학습 집중" : "생활 연습",
      primaryNeed: student.primaryNeed,
      sessionGoal: mission.sessionGoal,
      supportStrategy: "승인된 정적 콘텐츠와 4단계 realtime 연습",
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
      .filter((asset) => asset.assetType === "image")
      .map((asset) => ({
        assetId: asset.id,
        assetRole: asset.assetRole,
        alt: asset.assetRole,
      })),
    theme: fallbackTheme,
    stages: sortedStages.map((stage) => ({
      step: stage.step,
      title: stage.studentTitle,
      subtitle: stage.studentInstruction,
      state: stage.step === 1 ? "current" : "locked",
    })),
    visual: fallbackVisual,
    question: {
      prompt: sortedStages[0]?.studentInstruction ?? mission.sessionGoal,
      choices: ["좋아요", "다시 볼래요", "넘어갈래요"],
      correctAnswer: "좋아요",
      hint: "오늘 미션을 천천히 시작해봐요.",
      correctFeedback: "좋아요. 다음 단계로 갈 수 있어요.",
      wrongFeedback: "괜찮아요. 다시 천천히 봐요.",
      nextActionLabel: "학습 길로 돌아가기 →",
    },
    stageQuestions: sortedStages.map(stageToQuestion),
  };
}

function stageToQuestion(stage: MissionContent["stages"][number]): StageQuestion {
  const renderer = getTemplateRenderer(stage.templateType);
  const template = stage.templateJson;
  const question = readString(template.question) ?? readString(template.missionText) ?? stage.studentInstruction;
  const correctAnswer = readAnswer(stage.templateType, template);

  return {
    step: stage.step,
    stageId: stage.id,
    stageRole: stage.stageRole,
    templateType: stage.templateType,
    assetRole: stage.step === 4 ? "stage_4_realtime" : `stage_${stage.step}`,
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
  if (!Array.isArray(choices)) return undefined;
  return choices
    .map((choice) => {
      if (typeof choice === "string") return choice;
      if (choice && typeof choice === "object" && "text" in choice && typeof choice.text === "string") return choice.text;
      return null;
    })
    .filter((choice): choice is string => Boolean(choice));
}

function readAnswer(templateType: TemplateType, template: Record<string, unknown>) {
  if (typeof template.answer === "string") return template.answer;
  if (templateType === "blank_fill") {
    const acceptedAnswers = template.acceptedAnswers;
    if (Array.isArray(acceptedAnswers)) {
      const first = acceptedAnswers[0];
      if (first && typeof first === "object" && "numerator" in first && "denominator" in first) {
        return `${first.numerator}|${first.denominator}`;
      }
    }
  }
  return undefined;
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
  if (!Array.isArray(pairs)) return undefined;
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

  return undefined;
}
