"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { backendAdapter } from "@/lib/api/backend-adapter";
import type { ContentType, MissionContent, StudentCaseFile, StudentListItem } from "@/lib/api/contracts";
import {
  reviewItems,
  sessionRecords,
  students as mockStudents,
  supportCases,
  type CaseStatus,
  type StudentProfile,
  type SupportCase,
} from "@/lib/demo-data";

type DashboardTab = "info" | "materials" | "records";

type MaterialReviewItem = {
  id: string;
  caseId: string;
  title: string;
  type: string;
  state: string;
  contentId?: string;
  content?: MissionContent;
};

type MaterialGenerationState = {
  status: "idle" | "running" | "succeeded" | "failed";
  phase: string;
  message: string;
  contentId?: string;
  errorCode?: string;
};

const tabs: Array<{ id: DashboardTab; label: string; description: string }> = [
  { id: "info", label: "학생 정보", description: "기본 정보와 현재 학습 상태" },
  { id: "materials", label: "자료 생성·검토", description: "AI 자료를 만들고 수업 전 확인" },
  { id: "records", label: "학습 기록", description: "피드백과 관찰 기록" },
];

const statusTone: Record<CaseStatus, string> = {
  intake: "bg-[#f1f5f9] text-[#475569] border-[#cbd5e1]",
  structured: "bg-[#eff6ff] text-[#1d4ed8] border-[#bfdbfe]",
  goal_set: "bg-[#eff6ff] text-[#1d4ed8] border-[#bfdbfe]",
  scene_review: "bg-[#fff7ed] text-[#9a3412] border-[#fed7aa]",
  follow_up: "bg-[#f0fdf4] text-[#15803d] border-[#bbf7d0]",
};

const learningStatus: Record<CaseStatus, { label: string; progress: number; currentUnit: string; nextLesson: string }> = {
  intake: {
    label: "학습 준비",
    progress: 15,
    currentUnit: "학습 성향 파악",
    nextLesson: "첫 미션 시작",
  },
  structured: {
    label: "기초 확인",
    progress: 35,
    currentUnit: "기초 개념 점검",
    nextLesson: "개념 연결 연습",
  },
  goal_set: {
    label: "수업 진행 중",
    progress: 50,
    currentUnit: "문제 조건 읽기",
    nextLesson: "확인 문항 생성",
  },
  scene_review: {
    label: "AI 자료 확인",
    progress: 63,
    currentUnit: "분수 1/4 이해",
    nextLesson: "빛나는 구역 찾기",
  },
  follow_up: {
    label: "후속 확인",
    progress: 82,
    currentUnit: "반복 학습",
    nextLesson: "보호자 안내",
  },
};

const workflowSteps = ["자료 생성", "자료 검토", "학습", "학습 피드백"];

const reviewStagePreviews = [
  {
    step: 1,
    stageRole: "concept_intro",
    templateType: "concept_intro",
    assetRole: "stage_1",
    title: "전체 구역 세기",
    description: "피자 지도가 몇 개의 같은 크기 구역으로 나뉘었는지 먼저 확인합니다.",
    question: "피자 지도는 전체 몇 구역으로 나뉘어 있나요?",
    choices: ["2구역", "3구역", "4구역"],
    imagePrompt: "피자 지도를 4조각으로 명확히 나누고 전체 구역이 잘 보이게 표시",
  },
  {
    step: 2,
    stageRole: "basic_problem",
    templateType: "sequence_ordering",
    assetRole: "stage_2",
    title: "빛나는 구역 찾기",
    description: "전체 중에서 빛나는 한 조각만 찾아 세어봅니다.",
    question: "빛나는 구역은 몇 개인가요?",
    choices: ["1구역", "2구역", "4구역"],
    imagePrompt: "4조각 피자 지도에서 오른쪽 아래 한 조각만 은은하게 빛나게 표시",
  },
  {
    step: 3,
    stageRole: "applied_problem",
    templateType: "card_match",
    assetRole: "stage_3",
    title: "분수로 문 열기",
    description: "전체 4구역 중 1구역을 분수로 표현합니다.",
    question: "4구역 중 1구역은 몇 분의 몇일까요?",
    choices: ["1/4", "2/4", "4/1"],
    imagePrompt: "4조각 중 1조각이 선택된 장면을 분수 1/4와 연결해 표현",
  },
  {
    step: 4,
    stageRole: "realtime_practice",
    templateType: "realtime_teach_back",
    assetRole: "stage_4_realtime",
    title: "AI에게 말해보기",
    description: "오늘 배운 1/4 표현을 상황 이미지와 함께 AI에게 직접 설명합니다.",
    question: "전체 4조각 중 1조각이 왜 1/4인지 말로 설명해볼까요?",
    choices: ["전체 조각 수 말하기", "고른 조각 수 말하기", "1/4 표현과 연결하기"],
    imagePrompt: "4조각 피자 중 1조각을 가리키며 학생이 AI에게 설명하는 realtime 연습 상황",
  },
];

const reviewStageReasons: Record<number, string> = {
  1: "분수를 표현하기 전에 전체가 몇 등분인지 확인해 전체-부분 관계의 기준을 세웁니다.",
  2: "전체 중에서 특정 부분만 구분하게 하여 분자의 의미를 시각적으로 연결합니다.",
  3: "앞 단계에서 센 전체와 부분을 실제 분수 기호 1/4로 바꾸는 단계입니다.",
  4: "학습한 분수 표현을 생활 장면에 적용해 개념 전이를 확인합니다.",
};

type ReviewStageDraft = (typeof reviewStagePreviews)[number];

function StatusBadge({ supportCase }: { supportCase: SupportCase }) {
  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${statusTone[supportCase.status]}`}>
      {learningStatus[supportCase.status].label}
    </span>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-[#f8fafc] p-4">
      <p className="text-sm font-bold text-[#64748b]">{label}</p>
      <p className="mt-2 text-lg font-black leading-7 text-[#172033]">{value}</p>
    </div>
  );
}

function mapDashboardStudent(caseFile: StudentCaseFile): StudentProfile {
  const interests = Array.isArray(caseFile.profile.profileJson.interests)
    ? caseFile.profile.profileJson.interests.filter((item): item is string => typeof item === "string")
    : [];

  return {
    id: caseFile.profile.id,
    name: caseFile.profile.displayName,
    displayName: caseFile.profile.displayName,
    grade: formatGrade(caseFile.profile.grade),
    school: caseFile.schoolContext?.school.name ?? schoolNameFromCode(caseFile.profile.schoolCode),
    guardianName: "보호자",
    phone: "-",
    level: caseFile.profile.studentType === "life_support" ? 2 : 3,
    rewardTokens: caseFile.profile.studentType === "life_support" ? 96 : 120,
    nextRewardTokens: 30,
    attendanceRate: 92,
    understandingRate: caseFile.profile.studentType === "life_support" ? 68 : 76,
    interests,
    strengths: caseFile.memoryCard?.effectiveExplanationStyles ?? ["시각 자료", "짧은 단계"],
  };
}

function mapDashboardCase(caseFile: StudentCaseFile, summary?: StudentListItem): SupportCase {
  const hasContent = caseFile.recentContents.some((content) => content.status === "published");

  return {
    id: caseFile.openCase.id,
    studentId: caseFile.profile.id,
    status: hasContent ? "scene_review" : "structured",
    statusLabel: hasContent ? "자료 검토" : "자료 생성 필요",
    caseType: caseFile.profile.studentType === "life_support" ? "일상생활 지원형" : "학습집중형",
    primaryNeed: caseFile.profile.primaryNeed,
    sessionGoal: caseFile.recentContents[0]?.sessionGoal ?? caseFile.openCase.currentGoal,
    supportStrategy: caseFile.memoryCard?.effectiveExplanationStyles.join(", ") ?? "학생 반응을 보고 짧은 단계로 진행",
    nextAction: summary?.nextSessionSuggestion ?? caseFile.plannerItems[0]?.goalText ?? "다음 회기 목표 확인",
    riskNote: caseFile.memoryCard?.emotionalStateNote ?? "초기 데이터 수집 중입니다.",
    challengeTags: caseFile.memoryCard?.learningProblemTypes ?? [caseFile.profile.primaryNeed],
    planTags: caseFile.plannerItems.map((item) => item.goalText).slice(0, 3),
  };
}

function formatGrade(grade: string): string {
  const match = /^(elementary|middle|high)_(\d+)$/.exec(grade);
  if (!match) return grade;
  const label = match[1] === "elementary" ? "초" : match[1] === "middle" ? "중" : "고";
  return `${label}${match[2]}`;
}

function schoolNameFromCode(schoolCode: string | null | undefined): string {
  if (schoolCode === "8811046") return "영주중앙초등학교";
  if (schoolCode === "8811058") return "영주중학교";
  if (schoolCode === "8811067") return "영주가흥초등학교";
  return "학교 정보 확인 중";
}

function contentTypeFromCaseFile(caseFile: StudentCaseFile | undefined, supportCase: SupportCase): ContentType {
  if (caseFile) return caseFile.profile.studentType;
  return supportCase.caseType.includes("일상생활") ? "life_support" : "learning_focus";
}

function describeContentType(contentType: ContentType): string {
  return contentType === "life_support" ? "일상생활 지원형" : "학습집중형";
}

function mapContentToReviewItem(content: MissionContent): MaterialReviewItem {
  return {
    id: content.id,
    caseId: content.caseId,
    title: content.title,
    type: `백엔드 생성 미션 · ${describeContentType(content.contentType)}`,
    state: content.status === "teacher_review" ? "검토 대기" : content.status === "published" ? "배포됨" : content.status,
    contentId: content.id,
    content,
  };
}

function choicesFromTemplate(templateJson: Record<string, unknown>): string[] {
  const choices = templateJson.choices;
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

  const cards = templateJson.cards;
  if (Array.isArray(cards)) {
    return cards
      .map((card) => {
        if (typeof card === "string") return card;
        if (card && typeof card === "object" && "text" in card && typeof card.text === "string") return card.text;
        if (card && typeof card === "object" && "label" in card && typeof card.label === "string") return card.label;
        return null;
      })
      .filter((choice): choice is string => Boolean(choice));
  }

  const leftCards = templateJson.leftCards;
  const rightCards = templateJson.rightCards;
  if (Array.isArray(leftCards) && Array.isArray(rightCards)) {
    return ["왼쪽 카드와 오른쪽 카드를 연결", `${leftCards.length}개 카드`, `${rightCards.length}개 카드`];
  }

  const acceptedAnswers = templateJson.acceptedAnswers;
  if (Array.isArray(acceptedAnswers) && acceptedAnswers.length > 0) return ["정답 칸 채우기", "다시 생각하기", "힌트 보기"];

  return ["확인했어요"];
}

function mapContentToReviewStages(content: MissionContent): ReviewStageDraft[] {
  return [...content.stages]
    .sort((a, b) => a.step - b.step)
    .map((stage) => {
      const imageAssetId = typeof stage.templateJson.imageAssetId === "string" ? stage.templateJson.imageAssetId : undefined;
      const imageAsset = content.assets.find((asset) => asset.id === imageAssetId || asset.assetRole === (stage.step === 4 ? "stage_4_realtime" : `stage_${stage.step}`));
      const imagePrompt =
        imageAsset?.promptJson && typeof imageAsset.promptJson.prompt === "string"
          ? imageAsset.promptJson.prompt
          : "이미지 promptJson.prompt가 아직 없습니다.";
      const question =
        typeof stage.templateJson.question === "string"
          ? stage.templateJson.question
          : typeof stage.templateJson.missionText === "string"
            ? stage.templateJson.missionText
            : stage.studentInstruction;

      return {
        step: stage.step,
        stageRole: stage.stageRole,
        templateType: stage.templateType,
        assetRole: stage.step === 4 ? "stage_4_realtime" : `stage_${stage.step}`,
        title: stage.studentTitle,
        description: stage.studentInstruction,
        question,
        choices: choicesFromTemplate(stage.templateJson),
        imagePrompt,
      };
    });
}

function errorMessageOf(error: unknown): { message: string; code?: string } {
  if (error instanceof Error) {
    const maybeCode = "code" in error && typeof error.code === "string" ? error.code : undefined;
    return { message: error.message, code: maybeCode };
  }
  return { message: "AI 자료 생성 중 알 수 없는 오류가 발생했습니다." };
}

export default function DashboardPage() {
  const [dashboardStudents, setDashboardStudents] = useState<StudentProfile[]>(mockStudents);
  const [dashboardCases, setDashboardCases] = useState<SupportCase[]>(supportCases);
  const [caseFilesByStudent, setCaseFilesByStudent] = useState<Record<string, StudentCaseFile>>({});
  const [apiState, setApiState] = useState<"loading" | "ready" | "error">("loading");
  const [apiMessage, setApiMessage] = useState("백엔드 학생 데이터를 불러오는 중입니다.");
  const [selectedStudentId, setSelectedStudentId] = useState(mockStudents[0].id);
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState<DashboardTab>("info");
  const [lessonDrafts, setLessonDrafts] = useState<Record<string, string>>({});
  const [difficultyDrafts, setDifficultyDrafts] = useState<Record<string, string>>({});
  const [generatedReviewItems, setGeneratedReviewItems] = useState<MaterialReviewItem[]>([]);
  const [materialGeneration, setMaterialGeneration] = useState<MaterialGenerationState>({
    status: "idle",
    phase: "idle",
    message: "",
  });
  const [openReportId, setOpenReportId] = useState<string | null>(null);
  const [openReviewId, setOpenReviewId] = useState<string | null>(null);
  const [selectedFeedbackId, setSelectedFeedbackId] = useState<string | null>(null);
  const [approvedMaterialIds, setApprovedMaterialIds] = useState<string[]>([]);
  const [appliedMaterialIds, setAppliedMaterialIds] = useState<string[]>([]);
  const [revisionMaterialIds, setRevisionMaterialIds] = useState<string[]>([]);
  const [rejectedMaterialIds, setRejectedMaterialIds] = useState<string[]>([]);
  const [editingReviewIds, setEditingReviewIds] = useState<string[]>([]);
  const [editingImageKey, setEditingImageKey] = useState<string | null>(null);
  const [reviewPreviewStep, setReviewPreviewStep] = useState(1);
  const [reviewPreviewScale, setReviewPreviewScale] = useState(1);
  const reviewPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reportPreviewScale, setReportPreviewScale] = useState(1);
  const reportPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reviewStageDrafts, setReviewStageDrafts] = useState<Record<string, ReviewStageDraft[]>>({});
  const [memoDrafts, setMemoDrafts] = useState<Record<string, string>>({});
  const [savedMemos, setSavedMemos] = useState<Record<string, string>>({});
  const [feedbackDrafts, setFeedbackDrafts] = useState<Record<string, string>>({});
  const [savedFeedbackRecords, setSavedFeedbackRecords] = useState<
    Array<{ id: string; recordId: string; feedback: string; savedAt: string }>
  >([]);

  const filteredStudents = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return dashboardStudents;

    return dashboardStudents.filter((student) => {
      const supportCase = dashboardCases.find((item) => item.studentId === student.id);
      return [student.name, student.school, student.grade, supportCase?.primaryNeed, supportCase?.caseType]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(normalized));
    });
  }, [dashboardCases, dashboardStudents, query]);

  const selectedStudent = dashboardStudents.find((student) => student.id === selectedStudentId) ?? dashboardStudents[0] ?? mockStudents[0];
  const selectedCase =
    dashboardCases.find((supportCase) => supportCase.studentId === selectedStudent.id) ?? dashboardCases[0] ?? supportCases[0];
  const selectedCaseFile = caseFilesByStudent[selectedStudent.id];
  const selectedContentType = contentTypeFromCaseFile(selectedCaseFile, selectedCase);
  const lessonDraft = lessonDrafts[selectedCase.id] ?? selectedCase.sessionGoal;
  const difficultyDraft = difficultyDrafts[selectedCase.id] ?? "기초";
  const backendCaseReviewItems = (selectedCaseFile?.recentContents ?? []).map(mapContentToReviewItem);
  const caseReviewItems = reviewItems.filter((item) => item.caseId === selectedCase.id) as MaterialReviewItem[];
  const generatedCaseReviewItems = generatedReviewItems.filter((item) => item.caseId === selectedCase.id);
  const uniqueReviewItems = [...generatedCaseReviewItems, ...backendCaseReviewItems, ...caseReviewItems].filter(
    (item, index, items) => items.findIndex((candidate) => candidate.id === item.id) === index,
  );
  const selectedReviewItems =
    uniqueReviewItems.length > 0
      ? uniqueReviewItems
      : selectedCase.status === "scene_review"
        ? [
            {
              id: `review-${selectedCase.id}`,
              caseId: selectedCase.id,
              title: selectedCase.sessionGoal,
              type: "백엔드 배포 미션",
              state: "검토 대기",
            },
          ]
        : [];
  const selectedRecords = sessionRecords.filter((record) => record.caseId === selectedCase.id);
  const currentWorkflowStep = selectedCase.status === "follow_up" ? 4 : selectedCase.status === "scene_review" ? 2 : 3;
  const sessionLogs = selectedRecords.map((record, index) => {
    const attemptCount = index === 0 ? 9 : 7;
    const wrongCount = index === 0 ? 4 : 2;
    const averageResponseSeconds = index === 0 ? 42 : 55;
    const completionRate = index === 0 ? 75 : 68;

    return {
      ...record,
      attemptCount,
      wrongCount,
      averageResponseSeconds,
      completionRate,
      secondsPerQuestion: Math.round((record.durationMinutes * 60) / attemptCount),
      accuracyRate: Math.round(((attemptCount - wrongCount) / attemptCount) * 100),
    };
  });
  const feedbackQueue = sessionLogs.slice(0, 2);
  const pendingFeedbackQueue = feedbackQueue.filter(
    (record) => !savedFeedbackRecords.some((feedback) => feedback.recordId === record.id),
  );
  const feedbackTarget =
    feedbackQueue.find((record) => record.id === selectedFeedbackId) ?? feedbackQueue[0] ?? sessionLogs[0];
  const openReport = sessionLogs.find((record) => record.id === openReportId);
  const openReportStageStep = openReport
    ? Math.min(Math.max(sessionLogs.findIndex((record) => record.id === openReport.id) + 1, 1), reviewStagePreviews.length)
    : 1;
  const openReview = selectedReviewItems.find((item) => item.id === openReviewId);
  const openReviewStages = openReview
    ? (reviewStageDrafts[openReview.id] ?? (openReview.content ? mapContentToReviewStages(openReview.content) : reviewStagePreviews))
    : reviewStagePreviews;
  const isReviewEditing = openReview ? editingReviewIds.includes(openReview.id) : false;
  const savedMemo = savedMemos[selectedCase.id] ?? selectedCase.riskNote;
  const memoValue = memoDrafts[selectedCase.id] ?? savedMemo;
  const isMemoDirty = memoValue !== savedMemo;

  useEffect(() => {
    let cancelled = false;

    async function loadTeacherData() {
      try {
        const list = await backendAdapter.getTeacherStudents();
        const caseFiles = await Promise.all(
          list.map((student) => backendAdapter.getTeacherStudent(student.studentId)),
        );

        if (cancelled) return;

        const nextStudents = caseFiles.map((caseFile) => mapDashboardStudent(caseFile));
        const nextCases = caseFiles.map((caseFile) =>
          mapDashboardCase(caseFile, list.find((item) => item.studentId === caseFile.profile.id)),
        );
        const nextCaseFilesByStudent = Object.fromEntries(caseFiles.map((caseFile) => [caseFile.profile.id, caseFile]));

        setDashboardStudents(nextStudents);
        setDashboardCases(nextCases);
        setCaseFilesByStudent(nextCaseFilesByStudent);
        setSelectedStudentId((current) => (nextStudents.some((student) => student.id === current) ? current : nextStudents[0]?.id ?? current));
        setApiState("ready");
        setApiMessage(`백엔드에서 학생 ${nextStudents.length}명과 케이스 파일을 불러왔습니다.`);
      } catch (error) {
        if (cancelled) return;
        setApiState("error");
        setApiMessage(error instanceof Error ? error.message : "백엔드 학생 데이터를 불러오지 못했습니다.");
      }
    }

    loadTeacherData();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleGenerateMaterial = async () => {
    const requestedGoal = lessonDraft.trim();
    if (!requestedGoal || materialGeneration.status === "running") return;

    try {
      setMaterialGeneration({
        status: "running",
        phase: "orchestrator",
        message: "오케스트레이터가 학생 맥락과 수업 내용을 분석하는 중입니다.",
      });

      const orchestrator = await backendAdapter.createAgentRun({
        studentId: selectedStudent.id,
        caseId: selectedCase.id,
        contentType: selectedContentType,
        requestedGoal: `[난이도: ${difficultyDraft}] ${requestedGoal}`,
      });
      const orchestratorRun = orchestrator.agentRun;
      if (!orchestratorRun || orchestratorRun.status !== "succeeded") {
        throw new Error(orchestratorRun?.errorMessage ?? "오케스트레이터 실행이 성공하지 못했습니다.");
      }

      setMaterialGeneration({
        status: "running",
        phase: "content",
        message: "콘텐츠 에이전트가 4단계 MissionContent와 5개 이미지/5개 음성 asset 계약을 만드는 중입니다.",
      });

      const generated = await backendAdapter.createContentGeneration({
        orchestratorRunId: orchestratorRun.id,
        studentId: selectedStudent.id,
        caseId: selectedCase.id,
      });
      const contentRun = generated.agentRun;
      if (!contentRun || contentRun.status !== "succeeded" || !generated.content) {
        throw new Error(contentRun?.errorMessage ?? "MissionContent 생성 결과가 비어 있습니다.");
      }

      setMaterialGeneration({
        status: "running",
        phase: "assets",
        message: "gpt-image-2 이미지 5장과 ElevenLabs 안내 음성 5개를 실제 provider로 생성하는 중입니다.",
        contentId: generated.content.id,
      });

      await backendAdapter.generateContentAssetPackage(generated.content.id);
      const refreshedContent = await backendAdapter.getReviewableContent(generated.content.id);
      const reviewItem: MaterialReviewItem = {
        id: refreshedContent.id,
        caseId: refreshedContent.caseId,
        title: refreshedContent.title,
        type: `AI 생성 미션 · ${describeContentType(refreshedContent.contentType)}`,
        state: "검토 대기",
        contentId: refreshedContent.id,
        content: refreshedContent,
      };

      setGeneratedReviewItems((current) => [reviewItem, ...current.filter((item) => item.id !== reviewItem.id)]);
      setReviewStageDrafts((current) => ({
        ...current,
        [reviewItem.id]: mapContentToReviewStages(refreshedContent),
      }));
      setOpenReviewId(reviewItem.id);
      setReviewPreviewStep(1);
      setMaterialGeneration({
        status: "succeeded",
        phase: "done",
        message: "AI 자료 생성과 asset 패키지 생성이 완료되었습니다. 오른쪽 목록에서 검토할 수 있습니다.",
        contentId: refreshedContent.id,
      });
    } catch (error) {
      const { message, code } = errorMessageOf(error);
      setMaterialGeneration({
        status: "failed",
        phase: "review_required",
        message,
        errorCode: code,
      });
    }
  };

  const updateReviewStageDraft = (
    reviewId: string,
    step: number,
    updater: (stage: ReviewStageDraft) => ReviewStageDraft,
  ) => {
    setReviewStageDrafts((current) => {
      const stages = current[reviewId] ?? reviewStagePreviews;
      return {
        ...current,
        [reviewId]: stages.map((stage) => (stage.step === step ? updater(stage) : stage)),
      };
    });
  };

  useEffect(() => {
    if (!openReview) return;
    const frame = reviewPreviewFrameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const { width, height } = frame.getBoundingClientRect();
      setReviewPreviewScale(Math.min(width / 1024, height / 768) + 0.004);
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [openReview]);

  useEffect(() => {
    if (!openReport) return;
    const frame = reportPreviewFrameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const { width, height } = frame.getBoundingClientRect();
      setReportPreviewScale(Math.min(width / 1024, height / 768) + 0.004);
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [openReport]);

  return (
    <main className="relative min-h-screen bg-[#f5f7fa] text-[#172033]">
      <Link
        href="/"
        className="fixed bottom-6 right-6 z-50 rounded-full border border-[#25466f] bg-[#1f3a5f] px-5 py-3 text-base font-black text-white shadow-[0_12px_30px_rgba(31,58,95,0.25)]"
      >
        데모 홈
      </Link>
      <div className="grid min-h-screen xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside className="sticky top-0 flex h-screen flex-col border-r border-[#d8dee8] bg-white">
          <div className="border-b border-[#e5e9f0] p-6">
            <p className="text-sm font-bold text-[#1f3a5f]">배움동행 교사용</p>
            <h1 className="mt-2 text-2xl font-black">학생 관리</h1>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#64748b]">
              학생을 검색하고, 오늘 수업에 필요한 상태와 자료를 확인합니다.
            </p>
            <div
              className={`mt-4 rounded-md border px-3 py-2 text-xs font-bold leading-5 ${
                apiState === "ready"
                  ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                  : apiState === "error"
                    ? "border-[#fecaca] bg-[#fef2f2] text-[#991b1b]"
                    : "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]"
              }`}
            >
              {apiMessage}
            </div>
          </div>

          <div className="space-y-3 border-b border-[#e5e9f0] p-4">
            <label className="block">
              <span className="sr-only">학생 검색</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="w-full rounded-md border border-[#cbd5e1] bg-white px-4 py-3 text-sm font-bold outline-none placeholder:text-[#94a3b8] focus:border-[#1f3a5f]"
                placeholder="학생 이름, 학교, 학습 이슈 검색"
              />
            </label>
            <button className="w-full rounded-md bg-[#1f3a5f] px-4 py-3 text-sm font-bold text-white">
              학생 등록
            </button>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto divide-y divide-[#e5e9f0]">
            {filteredStudents.map((student) => {
              const supportCase = dashboardCases.find((item) => item.studentId === student.id) ?? dashboardCases[0] ?? supportCases[0];

              return (
                <button
                  key={student.id}
                  onClick={() => {
                    setSelectedStudentId(student.id);
                    setActiveTab("info");
                  }}
                  className={`w-full p-5 text-left transition ${
                    selectedStudentId === student.id ? "bg-[#eef4fb]" : "bg-white hover:bg-[#f8fafc]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-lg font-black">{student.name}</p>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        {student.school} · {student.grade}
                      </p>
                    </div>
                    <StatusBadge supportCase={supportCase} />
                  </div>
                  <p className="mt-4 text-sm font-semibold leading-6 text-[#334155]">
                    {supportCase.primaryNeed}
                  </p>
                </button>
              );
            })}
            {filteredStudents.length === 0 && (
              <div className="p-6 text-sm font-bold leading-6 text-[#64748b]">검색 결과가 없습니다.</div>
            )}
          </div>
        </aside>

        <section className="min-w-0 px-5 py-5 lg:px-8">
          <article className="overflow-hidden rounded-xl border border-[#d8dee8] bg-white">
            <section className="border-b border-[#e5e9f0] bg-[#fbfcfe] p-6">
              <div className="flex flex-wrap items-start justify-between gap-5">
                <div className="flex items-start gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#dfe8f4] text-2xl font-black text-[#1f3a5f]">
                    {selectedStudent.name.slice(0, 1)}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-3xl font-black">{selectedStudent.name}</h3>
                      <StatusBadge supportCase={selectedCase} />
                    </div>
                    <p className="mt-2 font-semibold text-[#64748b]">
                      {selectedStudent.school} · {selectedStudent.grade} · {selectedCase.caseType}
                    </p>
                    <p className="mt-3 max-w-2xl text-sm font-semibold leading-6 text-[#334155]">
                      {selectedCase.primaryNeed}
                    </p>
                  </div>
                </div>
                <div className="min-w-[440px] rounded-lg bg-[#f8fafc] p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-bold text-[#64748b]">현재 단계</p>
                      <p className="mt-1 text-lg font-black text-[#172033]">{workflowSteps[currentWorkflowStep - 1]}</p>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#64748b]">출석</p>
                      <p className="mt-1 text-lg font-black text-[#172033]">{selectedStudent.attendanceRate}%</p>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-4 gap-3">
                    {workflowSteps.map((step, index) => {
                      const isDone = index + 1 <= currentWorkflowStep;

                      return (
                        <div key={step}>
                          <div className={`h-3 rounded-full ${isDone ? "bg-[#1f3a5f]" : "bg-[#dbe3ee]"}`} />
                          <p className={`mt-2 text-sm font-black ${isDone ? "text-[#1f3a5f]" : "text-[#94a3b8]"}`}>
                            {step}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </section>

            <nav className="grid border-b border-[#e5e9f0] bg-white md:grid-cols-3">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`border-b-2 px-6 py-4 text-left transition md:border-b-0 md:border-r md:last:border-r-0 ${
                    activeTab === tab.id
                      ? "border-[#1f3a5f] bg-[#eef4fb]"
                      : "border-transparent bg-white hover:bg-[#f8fafc]"
                  }`}
                >
                  <p className="font-black">{tab.label}</p>
                  <p className="mt-1 text-sm font-semibold text-[#64748b]">{tab.description}</p>
                </button>
              ))}
            </nav>

            <div className="min-h-[560px]">
            {activeTab === "info" && (
              <section className="space-y-6 p-6">
                <section className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
                  <InfoBlock label="핵심 어려움" value={selectedCase.primaryNeed} />
                  <InfoBlock label="지원 전략" value={selectedCase.supportStrategy} />
                </section>

                <section className="grid gap-5 lg:grid-cols-2">
                  <div className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                    <h3 className="text-xl font-black">강점</h3>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {selectedStudent.strengths.map((strength) => (
                        <span
                          key={strength}
                          className="rounded-full bg-[#eef4fb] px-3 py-1 text-sm font-bold text-[#1f3a5f]"
                        >
                          {strength}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                    <h3 className="text-xl font-black">약점</h3>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {selectedCase.challengeTags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-[#fff7ed] px-3 py-1 text-sm font-bold text-[#9a3412]"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </section>

                <section className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                  <h3 className="text-xl font-black">추가 메모</h3>
                  <textarea
                    value={memoValue}
                    onChange={(event) =>
                      setMemoDrafts((current) => ({
                        ...current,
                        [selectedCase.id]: event.target.value,
                      }))
                    }
                    className="mt-4 h-32 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-4 text-sm font-semibold leading-6 outline-none focus:border-[#1f3a5f]"
                  />
                  <div className="mt-3 flex justify-end">
                    <button className="hidden">
                      수정
                    </button>
                    <button
                      disabled={!isMemoDirty}
                      onClick={() => {
                        setSavedMemos((current) => ({
                          ...current,
                          [selectedCase.id]: memoValue,
                        }));
                      }}
                      className={`rounded-md px-4 py-2 text-sm font-bold transition ${
                        isMemoDirty
                          ? "bg-[#1f3a5f] text-white shadow-[0_8px_18px_rgba(31,58,95,0.18)]"
                          : "cursor-not-allowed bg-[#e2e8f0] text-[#94a3b8]"
                      }`}
                    >
                      저장
                    </button>
                  </div>
                </section>
              </section>
            )}

            {activeTab === "materials" && (
              <section className="grid min-h-[calc(100vh-430px)] gap-5 p-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                <section className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                  <div className="flex h-full flex-col">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-xl font-black">자료 만들기</h3>
                        <p className="mt-1 text-sm font-semibold text-[#64748b]">
                          수업 내용과 난이도를 정하면 오케스트레이터가 학생 맥락을 함께 분석합니다.
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 space-y-4">
                      <label className="block">
                        <span className="text-sm font-bold text-[#64748b]">수업 내용</span>
                        <textarea
                          key={`lesson-${selectedCase.id}`}
                          className="mt-2 h-36 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-4 text-sm font-semibold outline-none focus:border-[#1f3a5f]"
                          value={lessonDraft}
                          onChange={(event) =>
                            setLessonDrafts((current) => ({
                              ...current,
                              [selectedCase.id]: event.target.value,
                            }))
                          }
                        />
                      </label>

                      <label className="block">
                        <span className="text-sm font-bold text-[#64748b]">난이도</span>
                        <select
                          className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-bold outline-none focus:border-[#1f3a5f]"
                          value={difficultyDraft}
                          onChange={(event) =>
                            setDifficultyDrafts((current) => ({
                              ...current,
                              [selectedCase.id]: event.target.value,
                            }))
                          }
                        >
                          <option value="기초">기초 · 설명을 더 짧고 쉽게</option>
                          <option value="보통">보통 · 문제와 피드백 균형</option>
                          <option value="도전">도전 · 3단계 응용 강화</option>
                        </select>
                      </label>

                      <div className="rounded-md bg-[#f8fafc] p-3">
                        <p className="text-sm font-bold text-[#64748b]">AI에 함께 전달되는 학생 컨텍스트</p>
                        <p className="mt-1 text-sm font-semibold leading-6 text-[#334155]">
                          {selectedStudent.name} · {selectedStudent.school} · {describeContentType(selectedContentType)} · {selectedCase.primaryNeed}
                        </p>
                        <p className="mt-1 text-xs font-bold leading-5 text-[#64748b]">
                          난이도 {difficultyDraft} / 케이스 {selectedCase.id}
                        </p>
                      </div>

                      <button
                        onClick={handleGenerateMaterial}
                        disabled={materialGeneration.status === "running" || !lessonDraft.trim()}
                        className="w-full rounded-md bg-[#1f3a5f] px-4 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
                      >
                        {materialGeneration.status === "running" ? "AI 자료 생성 중..." : "AI 자료 생성하기"}
                      </button>
                      {materialGeneration.message && (
                        <div
                          className={`rounded-md border px-4 py-3 text-sm font-bold leading-6 ${
                            materialGeneration.status === "failed"
                              ? "border-[#fecaca] bg-[#fef2f2] text-[#991b1b]"
                              : materialGeneration.status === "succeeded"
                                ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                : "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]"
                          }`}
                        >
                          <p>{materialGeneration.message}</p>
                          {materialGeneration.errorCode && <p className="mt-1 text-xs">오류 코드: {materialGeneration.errorCode}</p>}
                          {materialGeneration.contentId && <p className="mt-1 text-xs">콘텐츠 ID: {materialGeneration.contentId}</p>}
                        </div>
                      )}
                    </div>
                  </div>
                </section>

                <div className="space-y-4">
                  <section className="space-y-3">
                    <div>
                      <h3 className="text-xl font-black">생성된 자료</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        검토가 끝난 자료는 학생 화면으로 보낼 수 있습니다.
                      </p>
                    </div>
                    {selectedReviewItems.map((item) => (
                      <div key={item.id} className="rounded-md border border-[#e5e9f0] bg-white p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate text-base font-black">{item.title}</p>
                            <p className="mt-1 truncate text-sm font-semibold text-[#64748b]">{item.type}</p>
                          </div>
                          <span
                            className={`shrink-0 rounded-full border px-3 py-1 text-xs font-bold ${
                              appliedMaterialIds.includes(item.id)
                                ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                : approvedMaterialIds.includes(item.id)
                                  ? "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]"
                                  : rejectedMaterialIds.includes(item.id)
                                    ? "border-[#fecaca] bg-[#fef2f2] text-[#991b1b]"
                                    : revisionMaterialIds.includes(item.id)
                                      ? "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
                                      : "border-[#cbd5e1] bg-[#f8fafc] text-[#475569]"
                            }`}
                          >
                            {appliedMaterialIds.includes(item.id)
                              ? "적용 완료"
                              : approvedMaterialIds.includes(item.id)
                                ? "검토 완료"
                                : rejectedMaterialIds.includes(item.id)
                                  ? "사용 안 함"
                                  : revisionMaterialIds.includes(item.id)
                                    ? "수정 중"
                                    : item.state}
                          </span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <button
                            onClick={() => {
                              setReviewPreviewStep(1);
                              setOpenReviewId(item.id);
                            }}
                            className="rounded-md border border-[#cbd5e1] bg-white px-3 py-2 text-sm font-bold text-[#334155]"
                          >
                            검토하기
                          </button>
                          <button
                            onClick={() => {
                              if (!approvedMaterialIds.includes(item.id) || rejectedMaterialIds.includes(item.id)) return;
                              setAppliedMaterialIds((current) =>
                                current.includes(item.id) ? current : [...current, item.id],
                              );
                            }}
                            className={`rounded-md px-3 py-2 text-sm font-bold ${
                              appliedMaterialIds.includes(item.id)
                                ? "bg-[#dcfce7] text-[#15803d]"
                                : approvedMaterialIds.includes(item.id)
                                  ? "bg-[#1f3a5f] text-white"
                                  : "bg-[#e2e8f0] text-[#64748b]"
                            }`}
                          >
                            {appliedMaterialIds.includes(item.id) ? "적용됨" : "수업에 적용하기"}
                          </button>
                        </div>
                      </div>
                    ))}
                  </section>
                </div>
              </section>
            )}

            {activeTab === "records" && (
              <section className="space-y-6 p-6">
                <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
                  <div className="hidden">
                    <div>
                      <h3 className="text-xl font-black">피드백 대기</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        피드백을 남겨야 하는 학습 기록입니다.
                      </p>
                    </div>
                    {feedbackQueue.map((record) => (
                      <button
                        key={record.id}
                        onClick={() => setSelectedFeedbackId(record.id)}
                        className={`w-full rounded-lg border p-4 text-left transition ${
                          feedbackTarget?.id === record.id
                            ? "border-[#1f3a5f] bg-[#eef4fb]"
                            : "border-[#e5e9f0] bg-white hover:bg-[#f8fafc]"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-black">
                              {record.session} · {record.date}
                            </p>
                            <p className="mt-1 text-sm font-bold text-[#64748b]">
                              이해도 {record.understanding} · 집중도 {record.focus}
                            </p>
                          </div>
                          <span className="rounded-full bg-[#fff7ed] px-3 py-1 text-xs font-bold text-[#9a3412]">
                            작성 필요
                          </span>
                        </div>
	                        <div className="hidden">
                          <InfoBlock label="걸린 시간" value={`${record.durationMinutes}분`} />
                          <InfoBlock label="오답 횟수" value={`${record.wrongCount}회`} />
                          <InfoBlock label="정답률" value={`${record.accuracyRate}%`} />
                        </div>
                      </button>
                    ))}
                  </div>

                  <div className="rounded-lg border border-[#e5e9f0] bg-white p-5 xl:order-1">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-xl font-black">교육 피드백 작성</h3>
                        <p className="mt-1 text-sm font-semibold text-[#64748b]">
                          선택한 학습 기록에 대한 피드백을 남깁니다.
                        </p>
                      </div>
                      <span className="rounded-full bg-[#eef4fb] px-3 py-1 text-xs font-black text-[#1f3a5f]">
                        {pendingFeedbackQueue.length}개 작성 대상
                      </span>
                    </div>
                    <div className="mt-5 space-y-4">
                      {pendingFeedbackQueue.length === 0 && (
                        <div className="rounded-lg border border-[#bbf7d0] bg-[#f0fdf4] p-4 text-sm font-bold text-[#15803d]">
                          모든 차시 피드백이 최근 기록에 저장되었습니다.
                        </div>
                      )}
                      {pendingFeedbackQueue.map((record) => (
                        <section key={record.id} className="rounded-lg border border-[#e5e9f0] bg-[#f8fafc] p-4">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <p className="text-sm font-bold text-[#64748b]">피드백 작성 대상</p>
                              <p className="mt-1 text-base font-black text-[#172033]">
                                {record.session} · {record.date}
                              </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <Link
                                href={`/student/stage?studentId=${encodeURIComponent(selectedStudent.id)}&preview=1`}
                                target="_blank"
                                className="rounded-md border border-[#cbd5e1] bg-white px-3 py-2 text-xs font-black text-[#334155]"
                              >
                                학습 자료 보기
                              </Link>
                              <span className="rounded-full bg-[#fff7ed] px-3 py-1 text-xs font-bold text-[#9a3412]">
                                작성 필요
                              </span>
                            </div>
                          </div>
                          <div className="mt-4 grid gap-2 md:grid-cols-3">
                            <InfoBlock label="걸린 시간" value={`${record.durationMinutes}분`} />
                            <InfoBlock label="오답 횟수" value={`${record.wrongCount}회`} />
                            <InfoBlock label="정답률" value={`${record.accuracyRate}%`} />
                          </div>
                          <textarea
                            value={feedbackDrafts[record.id] ?? ""}
                            onChange={(event) => {
                              setFeedbackDrafts((current) => ({
                                ...current,
                                [record.id]: event.target.value,
                              }));
                            }}
                            className="mt-4 h-40 w-full resize-none rounded-md border border-[#cbd5e1] bg-white p-4 outline-none focus:border-[#1f3a5f]"
                            placeholder="학생 반응, 이해도 변화, 다음 수업에서 반영할 피드백을 기록하세요."
                          />
                          <div className="mt-3 flex justify-end">
                            <button
                              onClick={() => {
                                const feedback = feedbackDrafts[record.id]?.trim();
                                if (!feedback) return;

                                setSavedFeedbackRecords((current) => [
                                  {
                                    id: `feedback-${record.id}-${Date.now()}`,
                                    recordId: record.id,
                                    feedback,
                                    savedAt: "방금 저장",
                                  },
                                  ...current.filter((item) => item.recordId !== record.id),
                                ]);
                              }}
                              disabled={!feedbackDrafts[record.id]?.trim()}
                              className="rounded-md bg-[#1f3a5f] px-4 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
                            >
                              저장
                            </button>
                          </div>
                        </section>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-4 rounded-lg border border-[#e5e9f0] bg-white p-5 xl:order-2">
                    <h3 className="text-xl font-black">최근 기록</h3>
                    {savedFeedbackRecords.map((feedbackRecord) => {
                      const sourceRecord = sessionLogs.find((record) => record.id === feedbackRecord.recordId);
                      if (!sourceRecord) return null;

                      return (
                        <button
                          key={feedbackRecord.id}
                          onClick={() => setOpenReportId(sourceRecord.id)}
                          className="w-full rounded-md bg-[#f8fafc] p-4 text-left transition hover:bg-[#eef4fb]"
                        >
                          <p className="font-black">
                            {sourceRecord.session} · {sourceRecord.date}
                          </p>
                          <p className="mt-1 text-sm font-bold text-[#64748b]">
                            교육 피드백 · {feedbackRecord.savedAt}
                          </p>
                          <p className="mt-2 text-sm leading-6">{feedbackRecord.feedback}</p>
                          <p className="mt-3 text-sm font-black text-[#1f3a5f]">리포트 보기</p>
                        </button>
                      );
                    })}
                    {sessionLogs.map((record) => (
                      <button
                        key={record.id}
                        onClick={() => setOpenReportId(record.id)}
                        className="w-full rounded-md bg-[#f8fafc] p-4 text-left transition hover:bg-[#eef4fb]"
                      >
                        <p className="font-black">
                          {record.session} · {record.date}
                        </p>
                        <p className="mt-1 text-sm font-bold text-[#64748b]">
                          {record.durationMinutes}분 · 이해도 {record.understanding} · 집중도 {record.focus}
                        </p>
                        <p className="mt-2 text-sm leading-6">{record.note}</p>
                        <p className="mt-3 text-sm font-black text-[#1f3a5f]">리포트 보기</p>
                      </button>
                    ))}
                  </div>
                </section>
              </section>
            )}
            </div>
          </article>
        </section>
      </div>
      {openReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-6">
          <section className="flex h-[min(88vh,820px)] w-[min(92vw,1280px)] flex-col rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e5e9f0] px-6 py-4">
              <div>
                <p className="text-sm font-bold text-[#64748b]">학습 리포트</p>
                <h3 className="mt-1 text-2xl font-black">
                  {openReport.session} · {openReport.date}
                </h3>
              </div>
              <button
                onClick={() => setOpenReportId(null)}
                aria-label="닫기"
                className="flex h-11 w-11 items-center justify-center rounded-md border border-[#cbd5e1] bg-white text-2xl font-bold leading-none text-[#334155]"
              >
                ×
              </button>
            </div>

            <div className="min-h-0 flex-1 px-6 py-4">
              <section className="rounded-lg border border-[#d8dee8] bg-[#e7edf4] p-3">
                <div className="mb-2">
                  <div>
                    <p className="text-xs font-black text-[#64748b]">차시 자료</p>
                    <p className="mt-1 text-base font-black text-[#172033]">스테이지 {openReportStageStep} 학습 화면</p>
                  </div>
                </div>
                <div
                  ref={reportPreviewFrameRef}
                  className="relative mx-auto aspect-[4/3] h-[min(40vh,420px)] overflow-hidden rounded-md bg-[#e7edf4]"
                >
                  <iframe
                    title={`학습 리포트 자료 스테이지 ${openReportStageStep}`}
                    src={`/student/stage?studentId=${encodeURIComponent(selectedStudent.id)}&step=${openReportStageStep}&preview=1`}
                    className="absolute left-1/2 top-1/2 h-[768px] w-[1024px] origin-center border-0"
                    style={{ transform: `translate(-50%, -50%) scale(${reportPreviewScale})` }}
                  />
                </div>
              </section>

              <div className="mt-3 grid gap-2 md:grid-cols-6">
                <InfoBlock label="걸린 시간" value={`${openReport.durationMinutes}분`} />
                <InfoBlock label="평균 응답" value={`${openReport.averageResponseSeconds}초`} />
                <InfoBlock label="문제당 시간" value={`${openReport.secondsPerQuestion}초`} />
                <InfoBlock label="시도 횟수" value={`${openReport.attemptCount}회`} />
                <InfoBlock label="오답 횟수" value={`${openReport.wrongCount}회`} />
                <InfoBlock label="정답률" value={`${openReport.accuracyRate}%`} />
              </div>

              <div className="mt-3 rounded-lg bg-[#f8fafc] p-4">
                <p className="text-sm font-bold text-[#64748b]">기록 요약</p>
                <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">{openReport.note}</p>
              </div>
            </div>
          </section>
        </div>
      )}
      {openReview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-5">
          <section className="flex h-[min(90vh,920px)] w-[min(94vw,1560px)] flex-col rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
            <div className="flex items-start justify-between gap-4 border-b border-[#e5e9f0] px-6 py-5">
              <div>
                <p className="text-sm font-bold text-[#64748b]">자료 검토</p>
                <h3 className="mt-1 text-2xl font-black">{openReview.title}</h3>
                <p className="mt-1 text-sm font-semibold text-[#64748b]">
                  4개 스테이지를 확인하고 필요한 부분만 수정합니다.
                </p>
              </div>
              <button
                onClick={() => {
                  setOpenReviewId(null);
                  setEditingImageKey(null);
                }}
                aria-label="닫기"
                className="flex h-11 w-11 items-center justify-center rounded-md border border-[#cbd5e1] bg-white text-2xl font-bold leading-none text-[#334155]"
              >
                ×
              </button>
            </div>

            <div className="grid min-h-0 flex-1 gap-[clamp(16px,1.2vw,24px)] px-[clamp(24px,2vw,36px)] py-[clamp(18px,1.5vw,28px)] lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,0.85fr)]">
              <section className="flex min-h-0 flex-col rounded-lg border border-[#d8dee8] bg-[#e7edf4] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-black text-[#64748b]">학생 화면 미리보기</p>
                    <p className="mt-1 text-lg font-black text-[#172033]">스테이지 {reviewPreviewStep}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {openReviewStages.map((stage) => (
                      <button
                        key={stage.step}
                        onClick={() => setReviewPreviewStep(stage.step)}
                        className={`rounded-full px-3 py-1 text-xs font-black ${
                          reviewPreviewStep === stage.step ? "bg-[#1f3a5f] text-white" : "bg-white text-[#475569]"
                        }`}
                      >
                        {stage.step}
                      </button>
                    ))}
                  </div>
                </div>
                <div
                  ref={reviewPreviewFrameRef}
                  className="relative aspect-[4/3] w-full overflow-hidden rounded-md border border-[#cbd5e1] bg-[#e7edf4]"
                >
                  <iframe
                    key={`${openReview.id}-${reviewPreviewStep}`}
                    title={`학생 화면 스테이지 ${reviewPreviewStep}`}
                    src={`/student/stage?studentId=${encodeURIComponent(selectedStudent.id)}${
                      openReview.contentId ? `&contentId=${encodeURIComponent(openReview.contentId)}` : ""
                    }&step=${reviewPreviewStep}&preview=1`}
                    className="absolute left-1/2 top-1/2 h-[768px] w-[1024px] origin-center border-0"
                    style={{ transform: `translate(-50%, -50%) scale(${reviewPreviewScale})` }}
                  />
                </div>
              </section>
              <div className="min-h-0 space-y-4 overflow-y-auto pr-2">
                {openReviewStages.map((stage, index) => {
                  const imageKey = `${openReview.id}-${stage.step}`;
                  const isImageEditing = editingImageKey === imageKey;

                  return (
                    <section key={stage.step} className="rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-5">
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="rounded-full bg-[#1f3a5f] px-3 py-1 text-xs font-black text-white">
                            스테이지 {stage.step}
                          </span>
                          <h4 className="text-lg font-black text-[#172033]">{stage.title}</h4>
                        </div>
                        {index === 0 && (
                          <span className="rounded-full border border-[#bbf7d0] bg-[#f0fdf4] px-3 py-1 text-xs font-bold text-[#15803d]">
                            정답 포함
                          </span>
                        )}
                      </div>

                      <div className="grid gap-4">
                        <div className="hidden">
                          <div className="relative aspect-[4/3] overflow-hidden rounded-lg border border-[#d8dee8] bg-[#e7edf4]">
                            <button
                              onClick={() => setEditingImageKey(isImageEditing ? null : imageKey)}
                              className="absolute right-2 top-2 z-10 rounded-full border border-[#cbd5e1] bg-white/95 px-3 py-1 text-xs font-black text-[#334155] shadow-sm"
                            >
                              화면 수정
                            </button>
                            <iframe
                              title={`학생 화면 스테이지 ${stage.step}`}
                              src={`/student/stage?studentId=${encodeURIComponent(selectedStudent.id)}${
                                openReview.contentId ? `&contentId=${encodeURIComponent(openReview.contentId)}` : ""
                              }&step=${stage.step}&preview=1`}
                              className="absolute left-0 top-0 h-[768px] w-[1024px] origin-top-left scale-[0.205] border-0"
                            />
                          </div>
                          {isImageEditing && (
                            <div className="absolute left-[calc(100%+12px)] top-1 z-30 w-72 rounded-lg border border-[#fed7aa] bg-[#fff7ed] p-3 shadow-[0_18px_45px_rgba(154,52,18,0.18)] before:absolute before:left-[-7px] before:top-8 before:h-3 before:w-3 before:rotate-45 before:border-b before:border-l before:border-[#fed7aa] before:bg-[#fff7ed] max-lg:left-0 max-lg:top-[calc(100%+10px)] max-lg:w-full max-lg:before:left-8 max-lg:before:top-[-7px] max-lg:before:border-b-0 max-lg:before:border-l-0 max-lg:before:border-r max-lg:before:border-t">
                              <label className="text-xs font-black text-[#9a3412]" htmlFor={`image-prompt-${stage.step}`}>
                                화면 수정 프롬프트
                              </label>
                              <textarea
                                id={`image-prompt-${stage.step}`}
                                className="mt-2 h-20 w-full resize-none rounded-md border border-[#fdba74] bg-white p-3 text-xs font-semibold leading-5 outline-none focus:border-[#ea580c]"
                                value={stage.imagePrompt}
                                onChange={(event) =>
                                  updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                    ...currentStage,
                                    imagePrompt: event.target.value,
                                  }))
                                }
                              />
                              <button
                                onClick={() => {
                                  setRevisionMaterialIds((current) =>
                                    current.includes(openReview.id) ? current : [...current, openReview.id],
                                  );
                                  setEditingImageKey(null);
                                }}
                                className="mt-2 w-full rounded-md bg-[#9a3412] px-3 py-2 text-xs font-black text-white"
                              >
                                화면 재생성
                              </button>
                            </div>
                          )}
                        </div>

                        <div className="grid gap-3">
                          <div className="rounded-md bg-white p-4">
                            <p className="text-xs font-black text-[#64748b]">내용</p>
                            {isReviewEditing ? (
                              <textarea
                                className="mt-2 h-20 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-3 text-sm font-semibold leading-6 outline-none focus:border-[#1f3a5f]"
                                value={stage.description}
                                onChange={(event) =>
                                  updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                    ...currentStage,
                                    description: event.target.value,
                                  }))
                                }
                              />
                            ) : (
                              <>
                                <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">{stage.description}</p>
                                <div className="mt-4 border-l-4 border-[#1f3a5f] bg-[#f2f6fb] px-4 py-3">
                                  <p className="text-xs font-black uppercase tracking-[0.08em] text-[#1f3a5f]">
                                    설계 의도
                                  </p>
                                  <p className="mt-2 text-sm font-bold leading-6 text-[#26364d]">
                                    {reviewStageReasons[stage.step]}
                                  </p>
                                </div>
                              </>
                            )}

                            <p className="mt-4 text-xs font-black text-[#64748b]">문제</p>
                            {isReviewEditing ? (
                              <input
                                className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-[#fbfcfe] px-3 py-2 text-sm font-black outline-none focus:border-[#1f3a5f]"
                                value={stage.question}
                                onChange={(event) =>
                                  updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                    ...currentStage,
                                    question: event.target.value,
                                  }))
                                }
                              />
                            ) : (
                              <p className="mt-2 text-base font-black leading-7 text-[#172033]">{stage.question}</p>
                            )}
                          </div>

                          <div className="rounded-md bg-white p-4">
                            <p className="text-xs font-black text-[#64748b]">선택지</p>
                            <div className="mt-2 space-y-2">
                              {stage.choices.map((choice, choiceIndex) =>
                                isReviewEditing ? (
                                  <input
                                    key={`${stage.step}-${choiceIndex}`}
                                    className="w-full rounded-md border border-[#cbd5e1] bg-[#fbfcfe] px-3 py-2 text-sm font-bold outline-none focus:border-[#1f3a5f]"
                                    value={choice}
                                    onChange={(event) =>
                                      updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                        ...currentStage,
                                        choices: currentStage.choices.map((currentChoice, currentChoiceIndex) =>
                                          currentChoiceIndex === choiceIndex ? event.target.value : currentChoice,
                                        ),
                                      }))
                                    }
                                  />
                                ) : (
                                  <div
                                    key={choice}
                                    className={`rounded-md border px-3 py-2 text-sm font-black ${
                                      choiceIndex === 0
                                        ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                        : "border-[#e5e9f0] bg-[#f8fafc] text-[#334155]"
                                    }`}
                                  >
                                    {choice}
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </section>
                  );
                })}
              </div>
            </div>

            <div className="flex flex-wrap justify-end gap-3 border-t border-[#e5e9f0] px-6 py-4">
              <button
                onClick={() => {
                  setRejectedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingImageKey(null);
                  setOpenReviewId(null);
                }}
                className="rounded-md border border-[#fecaca] bg-[#fef2f2] px-5 py-3 text-sm font-bold text-[#991b1b]"
              >
                사용 안 함
              </button>
              <button
                onClick={() => {
	                  if (isReviewEditing) {
	                    setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
	                    setEditingImageKey(null);
	                    return;
	                  }

	                  setEditingReviewIds((current) => [...current, openReview.id]);
                  setRevisionMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                }}
	                className={`rounded-md border px-5 py-3 text-sm font-bold ${
	                  isReviewEditing
	                    ? "border-[#1f3a5f] bg-[#1f3a5f] text-white"
	                    : "border-[#cbd5e1] bg-white text-[#334155]"
	                }`}
              >
                {isReviewEditing ? "수정 저장" : "직접 수정"}
              </button>
              <button
                onClick={() => {
                  setApprovedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingImageKey(null);
                  setOpenReviewId(null);
                }}
                className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white"
              >
                사용 승인
              </button>
            </div>
          </section>
        </div>
      )}
      {/* Legacy review modal removed after stage-by-stage review redesign.
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-6">
          <section className="w-full max-w-3xl rounded-xl bg-white p-6 shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e5e9f0] pb-4">
              <div>
                <p className="text-sm font-bold text-[#64748b]">자료 검토</p>
                <h3 className="mt-1 text-2xl font-black">{openReview.title}</h3>
                <p className="mt-2 text-sm font-semibold text-[#64748b]">{openReview.type}</p>
              </div>
              <button
                onClick={() => setOpenReviewId(null)}
                className="rounded-md border border-[#cbd5e1] bg-white px-4 py-2 text-sm font-bold text-[#334155]"
              >
                닫기
              </button>
            </div>

            <div className="mt-5 rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-5">
              <p className="text-sm font-bold text-[#64748b]">생성 자료 미리보기</p>
              <div className="mt-4 grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
                <section className="rounded-lg bg-white p-5">
                  <h4 className="text-xl font-black">빛나는 구역 찾기</h4>
                  <p className="mt-3 text-sm font-semibold leading-6 text-[#334155]">
                    4조각으로 나뉜 피자 지도에서 빛나는 한 조각을 찾고, 전체 중 일부를 1/4로 표현하는
                    학생용 미션입니다.
                  </p>
                  <div className="mt-5 aspect-[16/9] rounded-lg border border-[#ecd27a] bg-[#f6df7d] p-4">
                    <div className="grid h-full grid-cols-2 gap-1 rounded-md border-4 border-[#e4bd4e] bg-[#f8e48f]">
                      <div className="border-r border-b border-[#e4bd4e]" />
                      <div className="border-b border-[#e4bd4e]" />
                      <div className="border-r border-[#e4bd4e]" />
                      <div className="ring-4 ring-[#fff176]" />
                    </div>
                  </div>
                </section>

                <section className="space-y-4">
                  <div className="rounded-lg bg-white p-5">
                    <p className="text-sm font-bold text-[#64748b]">학생 질문</p>
                    <input
                      className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-[#fbfcfe] px-4 py-3 text-xl font-black outline-none focus:border-[#1f3a5f]"
                      defaultValue="4구역 중 1구역은 몇 분의 몇일까요?"
                    />
                  </div>
                  <div className="rounded-lg bg-white p-5">
                    <p className="text-sm font-bold text-[#64748b]">선택지</p>
                    <div className="mt-3 grid gap-2">
                      {["1/4", "2/4", "4/1"].map((choice, index) => (
                        <div
                          key={choice}
                          className={`rounded-md border px-4 py-3 text-lg font-black ${
                            index === 0
                              ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                              : "border-[#e5e9f0] bg-[#f8fafc] text-[#334155]"
                          }`}
                        >
                          {choice}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-lg bg-white p-5">
                    <p className="text-sm font-bold text-[#64748b]">이미지 재생성 프롬프트</p>
                    <textarea
                      className="mt-2 h-24 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-4 text-sm font-semibold outline-none focus:border-[#1f3a5f]"
                      placeholder="이미지를 다시 만들 때 반영할 내용을 적어주세요."
                      defaultValue="피자 지도를 4조각으로 명확히 나누고, 오른쪽 아래 한 조각만 빛나게 표시"
                    />
                  </div>
                </section>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <button
                onClick={() => {
                  setRejectedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setOpenReviewId(null);
                }}
                className="rounded-md border border-[#fecaca] bg-[#fef2f2] px-5 py-3 text-sm font-bold text-[#991b1b]"
              >
                사용 안 함
              </button>
              <button
                onClick={() => {
                  setRevisionMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                }}
                className="rounded-md border border-[#cbd5e1] bg-white px-5 py-3 text-sm font-bold text-[#334155]"
              >
                직접 수정
              </button>
              <button
                onClick={() => {
                  setRevisionMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                }}
                className="rounded-md border border-[#fed7aa] bg-[#fff7ed] px-5 py-3 text-sm font-bold text-[#9a3412]"
              >
                이미지 재생성
              </button>
              <button
                onClick={() => {
                  setApprovedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setOpenReviewId(null);
                }}
                className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white"
              >
                사용 승인
              </button>
            </div>
          </section>
        </div>
      */}
    </main>
  );
}
