"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  approveContent,
  createAgentRun,
  createContentGeneration,
  generateContentAssetPackage,
  getTeacherStudent,
  getTeacherStudentReport,
  getTeacherStudents,
  publishContent,
  rejectContent,
  type AgentRun,
  type MissionContent,
  type StudentCaseFile,
  type StudentListItem,
  type StudentReport,
} from "@/lib/api";

type DashboardTab = "info" | "materials" | "records";
type CaseStatus = "intake" | "structured" | "goal_set" | "scene_review" | "follow_up";

type SupportCase = {
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

type MaterialReviewItem = {
  id: string;
  caseId: string;
  title: string;
  type: string;
  state: string;
  contentId: string;
  content: MissionContent;
};

type GenerationStatus = {
  state: "running" | "succeeded" | "failed";
  message: string;
};

type ReviewStageDraft = {
  step: 1 | 2 | 3 | 4;
  stageRole: string;
  templateType: string;
  assetRole: string;
  title: string;
  description: string;
  question: string;
  choices: string[];
  imagePrompt: string;
};

type SessionLog = {
  id: string;
  caseId: string;
  contentId: string;
  session: string;
  date: string;
  durationMinutes: number;
  understanding: "상" | "중" | "하";
  focus: "상" | "중" | "하";
  note: string;
  attemptCount: number;
  wrongCount: number;
  averageResponseSeconds: number;
  completionRate: number;
  secondsPerQuestion: number;
  accuracyRate: number;
  reflectionText: string | null;
};

const tabs: Array<{ id: DashboardTab; label: string; description: string }> = [
  { id: "info", label: "학생 정보", description: "기본 정보와 현재 학습 상태" },
  { id: "materials", label: "자료 제안·검토", description: "AI 수업 자료 제안을 확인" },
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

const workflowSteps = ["자료 제안", "제안 검토", "학습", "학습 피드백"];

const reviewStagePreviews: ReviewStageDraft[] = [];

type DashboardStudentView = {
  id: string;
  name: string;
  school: string;
  grade: string;
  attendanceRate: number | null;
  strengths: string[];
  weaknesses: string[];
};

function toDashboardStatus(item?: StudentListItem): CaseStatus {
  if (item?.dashboardStage === "initial_review") return "intake";
  if (item?.dashboardStage === "material_generation") return "structured";
  if (item?.dashboardStage === "material_review") return "scene_review";
  if (item?.dashboardStage === "learning") return "goal_set";
  if (item?.dashboardStage === "feedback") return "follow_up";
  if (item?.latestContentStatus === "completed") return "follow_up";
  if (item?.latestContentStatus && item.latestContentStatus !== "none") return "scene_review";
  return "intake";
}

function toSupportCaseFromListItem(item: StudentListItem): SupportCase {
  const status = toDashboardStatus(item);

  return {
    id: `${item.studentId}-case-summary`,
    studentId: item.studentId,
    status,
    statusLabel: item.statusLabel ?? item.dashboardStageLabel ?? learningStatus[status].label,
    caseType: item.trackLabel ?? item.studentTypeLabel ?? (item.studentType === "learning_focus" ? "학습지원형" : "일상생활 지원형"),
    primaryNeed: item.primaryNeed,
    sessionGoal: item.primaryNeed,
    supportStrategy: item.supportStrategy ?? item.aiContextSummary ?? (item.studentType === "learning_focus" ? "초기 학습 반응 확인" : "상황 장면 기반"),
    nextAction: item.nextSessionSuggestion,
    riskNote: "학생 화면에는 진단 표현을 노출하지 않음",
    challengeTags: item.weaknesses && item.weaknesses.length > 0 ? item.weaknesses : [item.primaryNeed],
    planTags: [item.nextSessionSuggestion],
  };
}

function toSupportCaseFromCaseFile(caseFile: StudentCaseFile, listItem?: StudentListItem): SupportCase {
  const status = toDashboardStatus(listItem);
  const dashboard = caseFile.dashboardProfile;

  return {
    id: caseFile.openCase.id,
    studentId: caseFile.profile.id,
    status,
    statusLabel: dashboard?.currentStageLabel ?? listItem?.statusLabel ?? learningStatus[status].label,
    caseType: caseFile.profile.trackLabel ?? caseFile.profile.studentTypeLabel ?? (caseFile.profile.studentType === "learning_focus" ? "학습지원형" : "일상생활 지원형"),
    primaryNeed: dashboard?.primaryNeedTitle ?? caseFile.profile.primaryNeed,
    sessionGoal: caseFile.openCase.currentGoal,
    supportStrategy:
      dashboard?.supportStrategyTitle ??
      caseFile.openCase.supportStrategy ??
      toDisplayLabels(caseFile.memoryCard?.effectiveExplanationStyles, ["정적 콘텐츠", "실시간 연습"]).join(", "),
    nextAction: listItem?.nextSessionSuggestion ?? "다음 미션 확인",
    riskNote: dashboard?.aiContextSummary ?? (caseFile.memoryCard?.nextSessionCautions.join(", ") || "학생 화면에는 진단 표현을 노출하지 않음"),
    challengeTags:
      dashboard?.weaknesses && dashboard.weaknesses.length > 0
        ? dashboard.weaknesses
        : caseFile.profile.weaknesses && caseFile.profile.weaknesses.length > 0
        ? caseFile.profile.weaknesses
        : toDisplayLabels(caseFile.memoryCard?.learningProblemTypes),
    planTags: dashboard?.nextSessionFocus && dashboard.nextSessionFocus.length > 0 ? dashboard.nextSessionFocus : caseFile.plannerItems.map((item) => item.goalText),
  };
}

const memoryLabelMap: Record<string, string> = {
  scenario_image: "상황 그림",
  two_choice: "2개 선택지",
  short_audio: "짧은 음성 안내",
  visual_example: "그림 예시",
  short_steps: "짧은 단계 설명",
  mascot_teach_back: "마스코트와 말로 정리하기",
  roleplay: "역할 연습",
  concept_misunderstanding: "개념 이해 보완",
  numerator_denominator_confusion: "분모·분자 위치 확인",
  sequence_planning: "순서 계획 연습",
  help_request_avoidance: "도움 요청 말하기 연습",
  fractions: "분수",
  daily_route: "일상 이동",
  clock_hour_hand: "짧은 바늘 찾기",
  reading_order: "읽는 순서 확인",
  word_problem_conditions: "문장 조건 확인",
  asking_help: "도움 요청하기",
};

function toDisplayLabels(values: string[] | undefined, fallback: string[] = []) {
  const source = values && values.length > 0 ? values : fallback;
  return source.map((value) => memoryLabelMap[value] ?? value);
}

function toProposalLabel(label: string) {
  if (label === "자료 생성") return "자료 제안";
  if (label === "자료 검토") return "제안 검토";
  if (label === "AI 자료 확인") return "AI 제안 확인";
  return label;
}

function toPercentScore(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) return 0;
  const percent = value <= 1 ? value * 100 : value;
  return Math.min(100, Math.max(0, Math.round(percent)));
}

function toRecordLevel(percent: number): "상" | "중" | "하" {
  if (percent >= 80) return "상";
  if (percent >= 50) return "중";
  return "하";
}

function describeContentType(content: MissionContent) {
  return content.contentType === "life_support" ? "일상생활 지원형" : "학습집중형";
}

function getReviewStageReason(stage: ReviewStageDraft) {
  if (stage.step === 4) {
    return "앞 단계에서 익힌 내용을 실제 말하기 상황으로 옮기는 실시간 발화 연습을 넣으면 좋겠어요.";
  }

  if (stage.step === 1) {
    return "긴 설명 전에 그림 단서를 먼저 확인하며 쉬운 성공 경험으로 시작하면 좋겠어요.";
  }

  if (stage.step === 2) {
    return "짧은 선택지나 카드로 핵심 단서를 한 번 더 고르게 하면 좋겠어요.";
  }

  return "앞 단계에서 고른 단서를 문장이나 기호와 연결해 수업 목표로 정리하면 좋겠어요.";
}

function getAiGenerationFailureMessage(agentRun?: AgentRun | null) {
  if (agentRun?.errorCode === "OPENAI_API_KEY_MISSING") {
    return "서버에 AI 생성 설정이 없어 실제 자료 생성은 아직 실행되지 않았습니다. 설정을 연결하면 같은 버튼으로 생성됩니다.";
  }

  if (agentRun?.errorMessage) {
    return agentRun.errorMessage;
  }

  return "자료 제안을 만들지 못했습니다. 잠시 뒤 다시 시도해 주세요.";
}

function getClientGenerationErrorMessage(error: unknown) {
  const code = typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
  if (code === "OPENAI_API_KEY_MISSING") {
    return "서버에 AI 생성 설정이 없어 실제 자료 생성은 아직 실행되지 않았습니다. 설정을 연결하면 같은 버튼으로 생성됩니다.";
  }

  if (error instanceof Error && error.message && !error.message.includes("OPENAI_API_KEY")) {
    return error.message;
  }

  return "자료 제안 요청 중 문제가 생겼습니다. 잠시 뒤 다시 시도해 주세요.";
}

function isGeneratedMediaReady(asset?: MissionContent["assets"][number] | null) {
  const url = asset?.previewUrl || asset?.storageUrl;
  if (!url) return false;
  return /^https?:\/\//.test(url) || url.startsWith("/generated/");
}

function getStageAssetStatus(content: MissionContent, step: ReviewStageDraft["step"]) {
  const role = step === 4 ? "stage_4_realtime" : `stage_${step}`;
  const stage = content.stages.find((item) => item.step === step);
  const imageAssetId = typeof stage?.templateJson.imageAssetId === "string" ? stage.templateJson.imageAssetId : undefined;
  const audioAssetId = typeof stage?.templateJson.audioAssetId === "string" ? stage.templateJson.audioAssetId : undefined;
  const image =
    content.assets.find((asset) => asset.assetType === "image" && asset.id === imageAssetId) ??
    content.assets.find((asset) => asset.assetType === "image" && asset.assetRole === role);
  const audio =
    content.assets.find((asset) => asset.assetType === "audio" && asset.id === audioAssetId) ??
    content.assets.find((asset) => asset.assetType === "audio" && asset.assetRole === role);

  return {
    imageReady: isGeneratedMediaReady(image),
    audioReady: isGeneratedMediaReady(audio),
  };
}

function hasMissingGeneratedMedia(content: MissionContent) {
  const heroImage = content.assets.find((asset) => asset.assetType === "image" && asset.assetRole === "hero");
  const heroAudio = content.assets.find((asset) => asset.assetType === "audio" && asset.assetRole === "hero");
  if (!isGeneratedMediaReady(heroImage) || !isGeneratedMediaReady(heroAudio)) return true;

  return ([1, 2, 3, 4] as Array<ReviewStageDraft["step"]>).some((step) => {
    const status = getStageAssetStatus(content, step);
    return !status.imageReady || !status.audioReady;
  });
}

function describeMissionStatus(status: MissionContent["status"]) {
  if (status === "teacher_review") return "검토 대기";
  if (status === "revision_requested") return "사용 안 함";
  if (status === "approved") return "검토 완료";
  if (status === "published") return "배포됨";
  if (status === "generating") return "생성 중";
  if (status === "archived") return "보관됨";
  return "초안";
}

function mapContentToReviewItem(content: MissionContent, lessonProposalTitle?: string): MaterialReviewItem {
  const title = lessonProposalTitle?.trim()
    ? `${lessonProposalTitle.trim()} 자료 제안`
    : "검토할 수업 자료 제안";

  return {
    id: content.id,
    caseId: content.caseId,
    title,
    type: `수업 전 검토 제안 · ${describeContentType(content)}`,
    state: describeMissionStatus(content.status),
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

  const rightCards = templateJson.rightCards;
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

  return [];
}

function mapContentToReviewStages(content: MissionContent): ReviewStageDraft[] {
  return [...content.stages]
    .sort((left, right) => left.step - right.step)
    .map((stage) => {
      const role = stage.step === 4 ? "stage_4_realtime" : `stage_${stage.step}`;
      const imageAssetId = typeof stage.templateJson.imageAssetId === "string" ? stage.templateJson.imageAssetId : undefined;
      const imageAsset = content.assets.find((asset) => asset.id === imageAssetId || (asset.assetType === "image" && asset.assetRole === role));
      const imagePrompt =
        imageAsset?.promptJson && typeof imageAsset.promptJson.prompt === "string"
          ? imageAsset.promptJson.prompt
          : "이미지 프롬프트가 아직 생성되지 않았습니다.";
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
        assetRole: role,
        title: stage.studentTitle,
        description: stage.studentInstruction,
        question,
        choices: choicesFromTemplate(stage.templateJson),
        imagePrompt,
      };
    });
}

function StatusBadge({ supportCase }: { supportCase: SupportCase }) {
  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${statusTone[supportCase.status]}`}>
      {toProposalLabel(supportCase.statusLabel)}
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

export default function DashboardPage() {
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [teacherStudentItems, setTeacherStudentItems] = useState<StudentListItem[]>([]);
  const [selectedCaseFile, setSelectedCaseFile] = useState<StudentCaseFile | null>(null);
  const [selectedReport, setSelectedReport] = useState<StudentReport | null>(null);
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState<DashboardTab>("info");
  const [openReportId, setOpenReportId] = useState<string | null>(null);
  const [openReviewId, setOpenReviewId] = useState<string | null>(null);
  const [selectedFeedbackId, setSelectedFeedbackId] = useState<string | null>(null);
  const [approvedMaterialIds, setApprovedMaterialIds] = useState<string[]>([]);
  const [appliedMaterialIds, setAppliedMaterialIds] = useState<string[]>([]);
  const [revisionMaterialIds, setRevisionMaterialIds] = useState<string[]>([]);
  const [rejectedMaterialIds, setRejectedMaterialIds] = useState<string[]>([]);
  const [editingReviewIds, setEditingReviewIds] = useState<string[]>([]);
  const [reviewActionId, setReviewActionId] = useState<string | null>(null);
  const [reviewPreviewStep, setReviewPreviewStep] = useState(1);
  const [reviewPreviewRefreshKey, setReviewPreviewRefreshKey] = useState(0);
  const [reviewPreviewScale, setReviewPreviewScale] = useState(1);
  const reviewPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reportPreviewScale, setReportPreviewScale] = useState(1);
  const reportPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reportPreviewStep, setReportPreviewStep] = useState(1);
  const [reviewStageDrafts, setReviewStageDrafts] = useState<Record<string, ReviewStageDraft[]>>({});
  const [memoDrafts, setMemoDrafts] = useState<Record<string, string>>({});
  const [savedMemos, setSavedMemos] = useState<Record<string, string>>({});
  const [lessonDrafts, setLessonDrafts] = useState<Record<string, string>>({});
  const [generationStatuses, setGenerationStatuses] = useState<Record<string, GenerationStatus>>({});
  const [feedbackDrafts, setFeedbackDrafts] = useState<Record<string, string>>({});
  const [savedFeedbackRecords, setSavedFeedbackRecords] = useState<
    Array<{ id: string; recordId: string; feedback: string; savedAt: string }>
  >([]);

  useEffect(() => {
    let ignore = false;

    async function loadStudents() {
      try {
        const items = await getTeacherStudents();
        if (ignore) return;

        setTeacherStudentItems(items);
        if (items.length > 0) setSelectedStudentId(items[0].studentId);
      } catch {
        if (ignore) return;
        setTeacherStudentItems([]);
      }
    }

    loadStudents();

    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (teacherStudentItems.length === 0 || !selectedStudentId) return;

    let ignore = false;
    setSelectedCaseFile(null);
    setSelectedReport(null);
    setSelectedFeedbackId(null);
    setOpenReportId(null);
    setOpenReviewId(null);

    Promise.all([getTeacherStudent(selectedStudentId), getTeacherStudentReport(selectedStudentId)])
      .then(([caseFile, report]) => {
        if (!ignore) {
          setSelectedCaseFile(caseFile);
          setSelectedReport(report);
        }
      })
      .catch(() => {
        if (!ignore) {
          setSelectedCaseFile(null);
          setSelectedReport(null);
        }
      });

    return () => {
      ignore = true;
    };
  }, [selectedStudentId, teacherStudentItems.length]);

  const dashboardStudents = useMemo<DashboardStudentView[]>(() => {
    return teacherStudentItems.map((item) => ({
      id: item.studentId,
      name: item.displayName,
      school: item.schoolName ?? "학교 정보 확인 중",
      grade: item.gradeLabel ?? item.grade,
      attendanceRate: item.attendanceRate ?? null,
      strengths: item.strengths ?? [],
      weaknesses: item.weaknesses ?? [],
    }));
  }, [teacherStudentItems]);

  const filteredStudents = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return dashboardStudents;

    return dashboardStudents.filter((student) => {
      const apiStudent = teacherStudentItems.find((item) => item.studentId === student.id);
      return [student.name, student.school, student.grade, apiStudent?.primaryNeed, apiStudent?.studentType]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(normalized));
    });
  }, [dashboardStudents, query, teacherStudentItems]);

  const selectedStudent = dashboardStudents.find((student) => student.id === selectedStudentId) ?? dashboardStudents[0] ?? {
    id: "",
    name: "학생 정보 로딩 중",
    school: "학교 정보 확인 중",
    grade: "",
    attendanceRate: null,
    strengths: [],
    weaknesses: [],
  };
  const selectedApiStudent = teacherStudentItems.find((student) => student.studentId === selectedStudent.id);
  const activeCaseFile = selectedCaseFile?.profile.id === selectedStudent.id ? selectedCaseFile : null;
  const activeReport = selectedReport?.student.id === selectedStudent.id ? selectedReport : null;
  const dashboardProfile = activeCaseFile?.dashboardProfile;
  const selectedCase: SupportCase = activeCaseFile
    ? toSupportCaseFromCaseFile(activeCaseFile, selectedApiStudent)
    : selectedApiStudent
      ? toSupportCaseFromListItem(selectedApiStudent)
      : {
          id: "",
          studentId: "",
          status: "intake",
          statusLabel: "불러오는 중",
          caseType: "확인 중",
          primaryNeed: "학생 데이터를 불러오는 중입니다.",
          sessionGoal: "",
          supportStrategy: "실제 학생 데이터 연결 대기",
          nextAction: "학생 목록 로드",
          riskNote: "",
          challengeTags: [],
          planTags: [],
        };
  const selectedReviewItems = (activeCaseFile?.recentContents ?? []).map((content) =>
    mapContentToReviewItem(content, dashboardProfile?.primaryNeedTitle),
  );
  const selectedRecords: SessionLog[] = (activeReport?.reports ?? []).map((record) => {
    const durationMinutes = Math.max(1, Math.round((record.durationSec ?? 0) / 60));
    const attemptCount = Math.max(1, record.answerCount);
    const averageResponseSeconds = Math.round((record.durationSec ?? 0) / attemptCount);
    const completionRate = toPercentScore(record.completionRate);
    const accuracyRate = toPercentScore(record.accuracyRate);

    return {
      id: record.id,
      caseId: record.caseId,
      contentId: record.contentId,
      session: record.contentTitle ?? "학습 콘텐츠",
      date: record.completedAt?.slice(0, 10) ?? record.startedAt.slice(0, 10),
      durationMinutes,
      understanding: toRecordLevel(accuracyRate),
      focus: toRecordLevel(completionRate),
      note: record.shortSummary,
      attemptCount,
      wrongCount: record.wrongCount,
      averageResponseSeconds,
      completionRate,
      secondsPerQuestion: averageResponseSeconds,
      accuracyRate,
      reflectionText:
        typeof record.reflection?.shortText === "string"
          ? record.reflection.shortText
          : typeof record.reflection?.reflectionChoice === "string"
            ? record.reflection.reflectionChoice
            : null,
    };
  });
  const currentWorkflowStep =
    selectedCase.status === "intake"
      ? 0
      : selectedCase.status === "structured"
        ? 1
        : selectedCase.status === "scene_review"
          ? 2
          : selectedCase.status === "follow_up"
            ? 4
            : 3;
  const sessionLogs = selectedRecords;
  const feedbackQueue = sessionLogs;
  const pendingFeedbackQueue = feedbackQueue.filter(
    (record) => !savedFeedbackRecords.some((feedback) => feedback.recordId === record.id),
  );
  const feedbackTarget =
    feedbackQueue.find((record) => record.id === selectedFeedbackId) ?? feedbackQueue[0] ?? sessionLogs[0];
  const openReport = sessionLogs.find((record) => record.id === openReportId);
  const openReportTeacherFeedback = openReport
    ? savedFeedbackRecords.find((feedback) => feedback.recordId === openReport.id)
    : null;
  const openReportStageStep = reportPreviewStep;
  const openReview = selectedReviewItems.find((item) => item.id === openReviewId);
  const openReviewStages = openReview ? (reviewStageDrafts[openReview.id] ?? mapContentToReviewStages(openReview.content)) : reviewStagePreviews;
  const openReviewNeedsMediaGeneration = openReview ? hasMissingGeneratedMedia(openReview.content) : false;
  const isReviewEditing = openReview ? editingReviewIds.includes(openReview.id) : false;
  const isMaterialApproved = (item: MaterialReviewItem) =>
    item.content.status === "approved" || item.content.status === "published" || approvedMaterialIds.includes(item.id);
  const isMaterialApplied = (item: MaterialReviewItem) =>
    item.content.status === "published" || appliedMaterialIds.includes(item.id);
  const isMaterialRejected = (item: MaterialReviewItem) =>
    item.content.status === "revision_requested" || rejectedMaterialIds.includes(item.id);
  const savedMemo = savedMemos[selectedCase.id] ?? "";
  const memoValue = memoDrafts[selectedCase.id] ?? savedMemo;
  const isMemoDirty = memoValue !== savedMemo;
  const canSaveMemo = isMemoDirty && memoValue.trim().length > 0;
  const lessonDraftValue = lessonDrafts[selectedCase.id] ?? "";
  const generationStatus = generationStatuses[selectedCase.id];
  const isGeneratingContent = generationStatus?.state === "running";

  const updateReviewStageDraft = (
    reviewId: string,
    step: number,
    updater: (stage: ReviewStageDraft) => ReviewStageDraft,
  ) => {
    setReviewStageDrafts((current) => {
      const stages = current[reviewId] ?? (openReview?.id === reviewId ? mapContentToReviewStages(openReview.content) : reviewStagePreviews);
      return {
        ...current,
        [reviewId]: stages.map((stage) => (stage.step === step ? updater(stage) : stage)),
      };
    });
  };

  const handleGenerateContent = async () => {
    if (!selectedCase.id || !selectedCase.studentId || isGeneratingContent) return;

    const requestedGoal = lessonDraftValue.trim() || selectedCase.primaryNeed;
    const contentType = activeCaseFile?.profile.studentType ?? selectedApiStudent?.studentType ?? "learning_focus";

    setGenerationStatuses((current) => ({
      ...current,
      [selectedCase.id]: {
        state: "running",
        message: "선생님 요청을 바탕으로 자료 방향을 정리하는 중입니다.",
      },
    }));

    try {
      const orchestratorResult = await createAgentRun({
        studentId: selectedCase.studentId,
        caseId: selectedCase.id,
        requestedGoal,
        contentType,
      });

      if (!orchestratorResult.agentRun || orchestratorResult.agentRun.status !== "succeeded") {
        setGenerationStatuses((current) => ({
          ...current,
          [selectedCase.id]: {
            state: "failed",
            message: getAiGenerationFailureMessage(orchestratorResult.agentRun),
          },
        }));
        return;
      }

      setGenerationStatuses((current) => ({
        ...current,
        [selectedCase.id]: {
          state: "running",
          message: "오케스트레이터 결과로 검토용 콘텐츠 구조를 만드는 중입니다.",
        },
      }));

      const generationResult = await createContentGeneration({
        orchestratorRunId: orchestratorResult.agentRun.id,
        studentId: selectedCase.studentId,
        caseId: selectedCase.id,
      });

      if (!generationResult.content || generationResult.agentRun?.status !== "succeeded") {
        setGenerationStatuses((current) => ({
          ...current,
          [selectedCase.id]: {
            state: "failed",
            message: getAiGenerationFailureMessage(generationResult.agentRun),
          },
        }));
        return;
      }

      setGenerationStatuses((current) => ({
        ...current,
        [selectedCase.id]: {
          state: "running",
          message: "이미지와 음성 asset을 실제 생성하는 중입니다.",
        },
      }));

      let generatedContent = generationResult.content;
      let assetGenerationErrorMessage: string | null = null;
      try {
        const assetPackage = await generateContentAssetPackage(generatedContent.id);
        const assetsById = new Map(assetPackage.assets.map((asset) => [asset.id, asset]));
        generatedContent = {
          ...generatedContent,
          assets: generatedContent.assets.map((asset) => assetsById.get(asset.id) ?? asset),
        };
      } catch (assetError) {
        assetGenerationErrorMessage = getClientGenerationErrorMessage(assetError);
        setGenerationStatuses((current) => ({
          ...current,
          [selectedCase.id]: {
            state: "failed",
            message: `수업 구조는 만들어졌지만 이미지/음성 생성에 실패했습니다. ${assetGenerationErrorMessage}`,
          },
        }));
      }

      setSelectedCaseFile((current) =>
        current && current.profile.id === generatedContent.studentId
          ? {
              ...current,
              recentContents: [
                generatedContent,
                ...current.recentContents.filter((content) => content.id !== generatedContent.id),
              ],
            }
          : current,
      );

      const refreshedCaseFile = await getTeacherStudent(selectedCase.studentId).catch(() => null);
      if (refreshedCaseFile) {
        setSelectedCaseFile(refreshedCaseFile);
      }

      setReviewPreviewStep(1);
      setOpenReviewId(generatedContent.id);
      setGenerationStatuses((current) => ({
        ...current,
        [selectedCase.id]: {
          state: assetGenerationErrorMessage ? "failed" : "succeeded",
          message: assetGenerationErrorMessage
            ? `수업 구조는 만들어졌지만 이미지/음성 생성에 실패했습니다. ${assetGenerationErrorMessage}`
            : "이미지와 음성이 포함된 검토용 수업 자료가 만들어졌습니다.",
        },
      }));
    } catch (error) {
      setGenerationStatuses((current) => ({
        ...current,
        [selectedCase.id]: {
          state: "failed",
          message: getClientGenerationErrorMessage(error),
        },
      }));
    }
  };

  const refreshSelectedStudentData = async () => {
    if (!selectedCase.studentId) return;

    const [items, caseFile, report] = await Promise.all([
      getTeacherStudents(),
      getTeacherStudent(selectedCase.studentId),
      getTeacherStudentReport(selectedCase.studentId),
    ]);
    setTeacherStudentItems(items);
    setSelectedCaseFile(caseFile);
    setSelectedReport(report);
  };

  const updateCurrentContent = (content: MissionContent) => {
    setSelectedCaseFile((current) =>
      current && current.profile.id === content.studentId
        ? {
            ...current,
            recentContents: current.recentContents.map((item) => (item.id === content.id ? content : item)),
          }
        : current,
    );
  };

  const handleGenerateReviewAssets = async (item: MaterialReviewItem) => {
    if (reviewActionId) return;

    setReviewActionId(item.id);
    setGenerationStatuses((current) => ({
      ...current,
      [item.caseId]: {
        state: "running",
        message: "검수 자료의 이미지와 음성을 실제 생성하는 중입니다.",
      },
    }));

    try {
      const assetPackage = await generateContentAssetPackage(item.contentId);
      const assetsById = new Map(assetPackage.assets.map((asset) => [asset.id, asset]));
      const updatedContent: MissionContent = {
        ...item.content,
        assets: item.content.assets.map((asset) => assetsById.get(asset.id) ?? asset),
      };
      updateCurrentContent(updatedContent);
      setReviewPreviewRefreshKey((current) => current + 1);
      setGenerationStatuses((current) => ({
        ...current,
        [item.caseId]: {
          state: "succeeded",
          message: "검수 자료에 이미지와 음성이 연결되었습니다.",
        },
      }));
    } catch (error) {
      setGenerationStatuses((current) => ({
        ...current,
        [item.caseId]: {
          state: "failed",
          message: `이미지/음성 생성에 실패했습니다. ${getClientGenerationErrorMessage(error)}`,
        },
      }));
    } finally {
      setReviewActionId(null);
    }
  };

  const setReviewActionError = (message: string) => {
    if (!selectedCase.id) return;
    setGenerationStatuses((current) => ({
      ...current,
      [selectedCase.id]: { state: "failed", message },
    }));
  };

  const handleRejectReview = async () => {
    if (!openReview || reviewActionId) return;

    setReviewActionId(openReview.id);
    try {
      const content = await rejectContent(openReview.contentId, {
        reason: "교사 검토에서 이번 수업에 사용하지 않음",
        requestedChanges: [],
      });
      updateCurrentContent(content);
      setRejectedMaterialIds((current) => (current.includes(openReview.id) ? current : [...current, openReview.id]));
      setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
      await refreshSelectedStudentData();
      setOpenReviewId(null);
    } catch {
      setReviewActionError("자료 제안 사용 안 함 상태를 저장하지 못했습니다.");
    } finally {
      setReviewActionId(null);
    }
  };

  const handleApproveReview = async () => {
    if (!openReview || reviewActionId) return;

    setReviewActionId(openReview.id);
    try {
      const content = await approveContent(openReview.contentId, {
        approvedStageIds: openReview.content.stages.map((stage) => stage.id),
        approvedAssetIds: openReview.content.assets.map((asset) => asset.id),
        reviewNote: "교사 검토 완료",
      });
      updateCurrentContent(content);
      setApprovedMaterialIds((current) => (current.includes(openReview.id) ? current : [...current, openReview.id]));
      setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
      await refreshSelectedStudentData();
      setOpenReviewId(null);
    } catch {
      setReviewActionError("자료 제안 승인 상태를 저장하지 못했습니다.");
    } finally {
      setReviewActionId(null);
    }
  };

  const handlePublishMaterial = async (item: MaterialReviewItem) => {
    if (isMaterialApplied(item) || !isMaterialApproved(item) || isMaterialRejected(item) || reviewActionId) return;

    setReviewActionId(item.id);
    try {
      const content = await publishContent(item.contentId);
      updateCurrentContent(content);
      setAppliedMaterialIds((current) => (current.includes(item.id) ? current : [...current, item.id]));
      await refreshSelectedStudentData();
    } catch {
      setReviewActionError("수업 적용 상태를 저장하지 못했습니다. 승인된 자료인지 다시 확인해 주세요.");
    } finally {
      setReviewActionId(null);
    }
  };

  useEffect(() => {
    if (!openReview) return;
    const frame = reviewPreviewFrameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const { width, height } = frame.getBoundingClientRect();
      setReviewPreviewScale(Math.min(1, Math.max(0.1, (width - 24) / 1024), Math.max(0.1, (height - 24) / 768)));
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [openReview]);

  useEffect(() => {
    if (!openReportId) return;
    setReportPreviewStep(1);
  }, [openReportId]);

  useEffect(() => {
    if (!openReport) return;
    const frame = reportPreviewFrameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const { width, height } = frame.getBoundingClientRect();
      setReportPreviewScale(Math.min(1, Math.max(0.1, (width - 24) / 1024), Math.max(0.1, (height - 24) / 768)));
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [openReport, reportPreviewStep]);

  return (
    <main className="relative min-h-screen bg-[#f5f7fa] text-[#172033]">
      <Link
        href="/"
        className="fixed bottom-6 right-6 z-50 rounded-full border border-[#25466f] bg-[#1f3a5f] px-5 py-3 text-base font-black text-white shadow-[0_12px_30px_rgba(31,58,95,0.25)]"
      >
        홈으로
      </Link>
      <div className="grid min-h-screen xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside className="flex flex-col border-r border-[#d8dee8] bg-white xl:sticky xl:top-0 xl:h-screen">
          <div className="border-b border-[#e5e9f0] p-6">
            <p className="text-sm font-bold text-[#1f3a5f]">배움동행 교사용</p>
            <h1 className="mt-2 text-2xl font-black">학생 관리</h1>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#64748b]">
              학생을 검색하고, 오늘 수업에 필요한 상태와 자료를 확인합니다.
            </p>
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

          <div className="divide-y divide-[#e5e9f0] xl:min-h-0 xl:flex-1 xl:overflow-y-auto">
            {filteredStudents.map((student) => {
              const apiStudent = teacherStudentItems.find((item) => item.studentId === student.id);
              const supportCase = apiStudent
                ? toSupportCaseFromListItem(apiStudent)
                : {
                    id: "",
                    studentId: student.id,
                    status: "intake" as const,
                    statusLabel: "확인 중",
                    caseType: "확인 중",
                    primaryNeed: "학생 정보를 불러오는 중입니다.",
                    sessionGoal: "",
                    supportStrategy: "",
                    nextAction: "",
                    riskNote: "",
                    challengeTags: [],
                    planTags: [],
                  };

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
                <div className="flex min-w-0 items-start">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-3xl font-black">{selectedStudent.name}</h3>
                      <StatusBadge supportCase={selectedCase} />
                    </div>
                    <p className="mt-2 font-semibold text-[#64748b]">
                      {dashboardProfile?.headline ?? `${selectedStudent.school} · ${selectedStudent.grade} · ${selectedCase.caseType}`}
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
                      <p className="mt-1 text-lg font-black text-[#172033]">
                        {toProposalLabel(
                          dashboardProfile?.currentStageLabel ??
                            (currentWorkflowStep === 0 ? "초기 확인" : workflowSteps[currentWorkflowStep - 1]),
                        )}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#64748b]">출석</p>
                      <p className="mt-1 text-lg font-black text-[#172033]">
                        {dashboardProfile?.attendanceLabel ?? (selectedStudent.attendanceRate === null ? "기록 전" : `${selectedStudent.attendanceRate}%`)}
                      </p>
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
                <section className="grid gap-5 lg:grid-cols-3">
                  <InfoBlock label="수업 제안" value={dashboardProfile?.primaryNeedDetail ?? selectedCase.primaryNeed} />
                  <InfoBlock label="콘텐츠 방향 제안" value={dashboardProfile?.supportStrategyDetail ?? selectedCase.supportStrategy} />
                  <InfoBlock label="수업 유의점" value={selectedCase.riskNote} />
                </section>

                <section className="grid gap-5 lg:grid-cols-2">
                  <div className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                    <h3 className="text-xl font-black">강점</h3>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {((dashboardProfile?.strengths?.length ? dashboardProfile.strengths : selectedStudent.strengths).length > 0
                        ? dashboardProfile?.strengths?.length
                          ? dashboardProfile.strengths
                          : selectedStudent.strengths
                        : ["기록 전"]
                      ).map((strength) => (
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
                      {(dashboardProfile?.weaknesses?.length ? dashboardProfile.weaknesses : selectedCase.challengeTags).map((tag) => (
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
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-xl font-black">교사 메모</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        저장한 메모는 다음 자료 제안에서 AI가 참고할 학생 메모리로 이어집니다.
                      </p>
                    </div>
                    {savedMemo && (
                      <span className="rounded-full border border-[#bbf7d0] bg-[#f0fdf4] px-3 py-1 text-xs font-bold text-[#15803d]">
                        메모리 저장됨
                      </span>
                    )}
                  </div>
                  <textarea
                    value={memoValue}
                    placeholder="AI가 다음 자료를 제안할 때 기억해야 할 반응, 수업 조정점, 보호자 공유 전 확인할 내용을 적어주세요."
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
                      disabled={!canSaveMemo}
                      onClick={() => {
                        const nextMemo = memoValue.trim();
                        setSavedMemos((current) => ({
                          ...current,
                          [selectedCase.id]: nextMemo,
                        }));
                        setMemoDrafts((current) => ({
                          ...current,
                          [selectedCase.id]: nextMemo,
                        }));
                      }}
                      className={`rounded-md px-4 py-2 text-sm font-bold transition ${
                        canSaveMemo
                          ? "bg-[#1f3a5f] text-white shadow-[0_8px_18px_rgba(31,58,95,0.18)]"
                          : "cursor-not-allowed bg-[#e2e8f0] text-[#94a3b8]"
                      }`}
                    >
                      메모리로 저장
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
                        <h3 className="text-xl font-black">수업 자료 제안</h3>
                        <p className="mt-1 text-sm font-semibold text-[#64748b]">
                          선생님이 원하는 방향을 적으면 검토용 수업 자료를 제안받습니다.
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 space-y-4">
                      <label className="block">
                        <span className="text-sm font-bold text-[#64748b]">수업 제안 초안</span>
                        <textarea
                          className="mt-2 h-36 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-4 text-sm font-semibold outline-none focus:border-[#1f3a5f]"
                          key={`lesson-${selectedCase.id}`}
                          value={lessonDraftValue}
                          onChange={(event) =>
                            setLessonDrafts((current) => ({
                              ...current,
                              [selectedCase.id]: event.target.value,
                            }))
                          }
                          placeholder="오늘 만들고 싶은 수업 방향을 적어주세요. 비워두면 학생 기록을 바탕으로 기본 제안을 만듭니다."
                        />
                      </label>

                      <label className="block">
                        <span className="text-sm font-bold text-[#64748b]">난이도</span>
                        <select className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-bold outline-none focus:border-[#1f3a5f]">
                          <option>기초</option>
                          <option>보통</option>
                          <option>도전</option>
                        </select>
                      </label>

                      <button
                        disabled={!selectedCase.id || isGeneratingContent}
                        onClick={handleGenerateContent}
                        className={`w-full rounded-md px-4 py-3 text-sm font-bold text-white ${
                          !selectedCase.id || isGeneratingContent
                            ? "cursor-not-allowed bg-[#94a3b8]"
                            : "bg-[#1f3a5f] hover:bg-[#172b47]"
                        }`}
                      >
                        {isGeneratingContent ? "AI가 자료를 제안하는 중" : "AI 수업 자료 제안받기"}
                      </button>
                      {generationStatus && (
                        <div
                          className={`rounded-md border px-3 py-2 text-sm font-bold leading-6 ${
                            generationStatus.state === "succeeded"
                              ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                              : generationStatus.state === "failed"
                                ? "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
                                : "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]"
                          }`}
                        >
                          {generationStatus.message}
                        </div>
                      )}
                    </div>
                  </div>
                </section>

                <div className="space-y-4">
                  <section className="space-y-3">
                    <div>
                      <h3 className="text-xl font-black">검토할 수업 자료 제안</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        AI가 제안한 자료를 확인하고 선생님 판단으로 적용합니다.
                      </p>
                    </div>
                    {selectedReviewItems.map((item) => {
                      const materialApplied = isMaterialApplied(item);
                      const materialApproved = isMaterialApproved(item);
                      const materialRejected = isMaterialRejected(item);
                      const isActionRunning = reviewActionId === item.id;
                      const needsMediaGeneration = hasMissingGeneratedMedia(item.content);

                      return (
                        <div key={item.id} className="rounded-md border border-[#e5e9f0] bg-white p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate text-base font-black">{item.title}</p>
                              <p className="mt-1 truncate text-sm font-semibold text-[#64748b]">{item.type}</p>
                            </div>
                            <span
                              className={`shrink-0 rounded-full border px-3 py-1 text-xs font-bold ${
                                materialApplied
                                  ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                  : materialApproved
                                    ? "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]"
                                    : materialRejected
                                      ? "border-[#fecaca] bg-[#fef2f2] text-[#991b1b]"
                                      : revisionMaterialIds.includes(item.id)
                                        ? "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
                                        : "border-[#cbd5e1] bg-[#f8fafc] text-[#475569]"
                              }`}
                            >
                              {materialApplied
                                ? "적용 완료"
                                : materialApproved
                                  ? "검토 완료"
                                  : materialRejected
                                    ? "사용 안 함"
                                    : revisionMaterialIds.includes(item.id)
                                      ? "수정 중"
                                      : item.state}
                            </span>
                          </div>
                          {needsMediaGeneration && (
                            <div className="mt-3 rounded-md border border-[#fed7aa] bg-[#fff7ed] px-3 py-2 text-sm font-bold leading-6 text-[#9a3412]">
                              이미지나 음성 파일이 아직 연결되지 않았습니다. 생성 설정을 확인한 뒤 다시 자료를 만들면 검수 화면에 함께 표시됩니다.
                            </div>
                          )}
                          <div className="mt-3 flex flex-wrap gap-2">
                            <button
                              onClick={() => {
                                setReviewPreviewStep(1);
                                setOpenReviewId(item.id);
                              }}
                              className="rounded-md border border-[#cbd5e1] bg-white px-3 py-2 text-sm font-bold text-[#334155]"
                            >
                              제안 검토하기
                            </button>
                            {needsMediaGeneration && (
                              <button
                                onClick={() => handleGenerateReviewAssets(item)}
                                disabled={isActionRunning}
                                className="rounded-md border border-[#fed7aa] bg-[#fff7ed] px-3 py-2 text-sm font-bold text-[#9a3412] disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                {isActionRunning ? "생성 중" : "이미지·음성 생성하기"}
                              </button>
                            )}
                            <button
                              onClick={() => handlePublishMaterial(item)}
                              disabled={materialApplied || !materialApproved || materialRejected || isActionRunning}
                              className={`rounded-md px-3 py-2 text-sm font-bold ${
                                materialApplied
                                  ? "bg-[#dcfce7] text-[#15803d]"
                                  : materialApproved
                                    ? "bg-[#1f3a5f] text-white"
                                    : "bg-[#e2e8f0] text-[#64748b]"
                              }`}
                            >
                              {isActionRunning ? "저장 중" : materialApplied ? "적용됨" : "수업에 적용하기"}
                            </button>
                          </div>
                        </div>
                      );
                    })}
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
                        <h3 className="text-xl font-black">학습 기록 작성 대상</h3>
                        <p className="mt-1 text-sm font-semibold text-[#64748b]">
                          학생이 미션을 마치면 먼저 이곳에 들어오고, 선생님 리포트를 저장하면 최근 기록으로 이동합니다.
                        </p>
                      </div>
                      <span className="rounded-full bg-[#eef4fb] px-3 py-1 text-xs font-black text-[#1f3a5f]">
                        작성 대기 {pendingFeedbackQueue.length}개
                      </span>
                    </div>
                    <div className="mt-5 space-y-4">
                      {sessionLogs.length === 0 && (
                        <div className="rounded-lg border border-[#dbe3ef] bg-[#f8fafc] p-4 text-sm font-bold text-[#475569]">
                          아직 완료된 학습 기록이 없습니다. 학생이 미션을 마치고 회고가 저장되면 이곳에서 피드백을 작성할 수 있습니다.
                        </div>
                      )}
                      {sessionLogs.length > 0 && pendingFeedbackQueue.length === 0 && (
                        <div className="rounded-lg border border-[#bbf7d0] bg-[#f0fdf4] p-4 text-sm font-bold text-[#15803d]">
                          모든 학습 기록이 선생님 리포트로 저장되었습니다.
                        </div>
                      )}
                      {pendingFeedbackQueue.map((record) => (
                        <section key={record.id} className="rounded-lg border border-[#e5e9f0] bg-[#f8fafc] p-4">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <p className="text-sm font-bold text-[#64748b]">학생 학습 완료</p>
                              <p className="mt-1 text-base font-black text-[#172033]">
                                {record.session} · {record.date}
                              </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <Link
                                href={`/student/stage?caseId=${encodeURIComponent(record.caseId)}&contentId=${encodeURIComponent(record.contentId)}&preview=1`}
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
                          <div className="mt-3 rounded-md border border-[#d9ebc9] bg-white px-4 py-3">
                            <p className="text-xs font-black text-[#16803c]">학생 회고</p>
                            <p className="mt-1 text-sm font-semibold leading-6 text-[#334155]">
                              {record.reflectionText ?? "아직 저장된 회고가 없습니다."}
                            </p>
                          </div>
                          <div className="mt-3 rounded-md bg-white px-4 py-3">
                            <p className="text-xs font-black text-[#64748b]">자동 기록 요약</p>
                            <p className="mt-1 text-sm font-semibold leading-6 text-[#334155]">{record.note}</p>
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
                            placeholder="선생님 리포트를 작성하세요. 학생 반응, 이해도 변화, 다음 수업에서 반영할 내용을 남깁니다."
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
                              최근 기록으로 저장
                            </button>
                          </div>
                        </section>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-4 rounded-lg border border-[#e5e9f0] bg-white p-5 xl:order-2">
                    <h3 className="text-xl font-black">최근 기록</h3>
                    {savedFeedbackRecords.length === 0 && (
                      <div className="rounded-md bg-[#f8fafc] p-4 text-sm font-bold leading-6 text-[#64748b]">
                        선생님 리포트로 저장된 최근 기록이 아직 없습니다.
                      </div>
                    )}
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
                            선생님 리포트 · {feedbackRecord.savedAt}
                          </p>
                          <p className="mt-2 text-sm leading-6">{feedbackRecord.feedback}</p>
                          <p className="mt-3 text-sm font-black text-[#1f3a5f]">리포트 보기</p>
                        </button>
                      );
                    })}
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
          <section className="flex h-[min(90vh,900px)] w-[min(94vw,1320px)] flex-col rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
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

            <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">
              <section className="rounded-lg border border-[#d8dee8] bg-[#f1f5f9] p-3">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-black text-[#64748b]">차시 자료</p>
                    <p className="mt-1 text-base font-black text-[#172033]">스테이지 {openReportStageStep} 학습 화면</p>
                  </div>
                  <div className="flex rounded-lg bg-white p-1 shadow-sm">
                    {[1, 2, 3, 4].map((step) => (
                      <button
                        key={step}
                        type="button"
                        onClick={() => setReportPreviewStep(step)}
                        className={`h-8 w-10 rounded-md text-sm font-black transition ${
                          reportPreviewStep === step ? "bg-[#1f3a5f] text-white" : "text-[#64748b] hover:bg-[#eef2f7]"
                        }`}
                      >
                        {step}
                      </button>
                    ))}
                  </div>
                </div>
                <div
                  ref={reportPreviewFrameRef}
                  className="relative mx-auto aspect-[4/3] h-[min(46vh,520px)] min-h-[360px] max-w-[760px] overflow-hidden rounded-md bg-[#e7edf4] shadow-inner"
                >
                  <iframe
                    title={`학습 리포트 자료 스테이지 ${openReportStageStep}`}
                    src={`/student/stage?caseId=${encodeURIComponent(openReport.caseId)}&contentId=${encodeURIComponent(openReport.contentId)}&step=${openReportStageStep}&preview=1`}
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

              <div className="mt-3 grid gap-3 lg:grid-cols-[1fr_1fr]">
                <div className="rounded-lg bg-[#f8fafc] p-4">
                  <p className="text-sm font-bold text-[#64748b]">기록 요약</p>
                  <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">{openReport.note}</p>
                </div>
                <div className="rounded-lg border border-[#d9ebc9] bg-[#f4fbef] p-4">
                  <p className="text-sm font-bold text-[#16803c]">학생 회고</p>
                  <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">
                    {openReport.reflectionText ?? "아직 저장된 회고가 없습니다."}
                  </p>
                </div>
              </div>
              <div className="mt-3 rounded-lg border border-[#cbd5e1] bg-white p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-bold text-[#1f3a5f]">선생님 리포트</p>
                  {openReportTeacherFeedback && (
                    <span className="rounded-full bg-[#eef4fb] px-3 py-1 text-xs font-black text-[#1f3a5f]">
                      {openReportTeacherFeedback.savedAt}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">
                  {openReportTeacherFeedback?.feedback ?? "아직 선생님 리포트가 저장되지 않았습니다."}
                </p>
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
                <p className="text-sm font-bold text-[#64748b]">자료 제안 검토</p>
                <h3 className="mt-1 text-2xl font-black">{openReview.title}</h3>
                <p className="mt-1 text-sm font-semibold text-[#64748b]">
                  4개 스테이지를 확인하고 선생님 판단으로 필요한 부분만 조정합니다.
                </p>
                {openReviewNeedsMediaGeneration && (
                  <p className="mt-3 rounded-md border border-[#fed7aa] bg-[#fff7ed] px-3 py-2 text-sm font-bold leading-6 text-[#9a3412]">
                    이 자료는 이미지나 음성 파일이 아직 모두 연결되지 않았습니다. 생성 설정이 준비된 상태에서 다시 만들면 학생 화면 미리보기와 음성 재생이 함께 확인됩니다.
                  </p>
                )}
              </div>
              <button
                onClick={() => {
                  setOpenReviewId(null);
                }}
                aria-label="닫기"
                className="flex h-11 w-11 items-center justify-center rounded-md border border-[#cbd5e1] bg-white text-2xl font-bold leading-none text-[#334155]"
              >
                ×
              </button>
            </div>

            <div className="grid min-h-0 flex-1 gap-[clamp(16px,1.2vw,24px)] overflow-y-auto px-[clamp(24px,2vw,36px)] py-[clamp(18px,1.5vw,28px)] lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,0.85fr)] lg:overflow-hidden">
              <section className="flex min-h-[460px] flex-col overflow-hidden rounded-lg border border-[#d8dee8] bg-[#e7edf4] p-4 lg:min-h-0">
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
                  className="relative h-[520px] min-h-0 w-full overflow-hidden rounded-md border border-[#cbd5e1] bg-[#e7edf4] lg:flex-1"
                >
                  <iframe
                    key={`${openReview.id}-${reviewPreviewStep}-${reviewPreviewRefreshKey}`}
                    title={`학생 화면 스테이지 ${reviewPreviewStep}`}
                    src={`/student/stage?caseId=${encodeURIComponent(openReview.caseId)}&contentId=${encodeURIComponent(openReview.contentId)}&step=${reviewPreviewStep}&preview=1`}
                    className="absolute left-1/2 top-1/2 h-[768px] w-[1024px] origin-center border-0"
                    style={{ transform: `translate(-50%, -50%) scale(${reviewPreviewScale})` }}
                  />
                </div>
              </section>
              <div className="min-h-0 space-y-4 overflow-y-auto pr-2">
                {openReviewStages.map((stage, index) => {
                  const assetStatus = getStageAssetStatus(openReview.content, stage.step);
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
                                    {getReviewStageReason(stage)}
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
                            <p className="text-xs font-black text-[#64748b]">이미지·음성</p>
                            <div className="mt-3 flex flex-wrap gap-2">
                              <span
                                className={`rounded-full border px-3 py-1 text-xs font-black ${
                                  assetStatus.imageReady
                                    ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                    : "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
                                }`}
                              >
                                {assetStatus.imageReady ? "이미지 연결됨" : "이미지 생성 필요"}
                              </span>
                              <span
                                className={`rounded-full border px-3 py-1 text-xs font-black ${
                                  assetStatus.audioReady
                                    ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                    : "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
                                }`}
                              >
                                {assetStatus.audioReady ? "음성 연결됨" : "음성 생성 필요"}
                              </span>
                            </div>
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
              {openReviewNeedsMediaGeneration && (
                <button
                  onClick={() => handleGenerateReviewAssets(openReview)}
                  disabled={reviewActionId === openReview.id}
                  className="rounded-md border border-[#fed7aa] bg-[#fff7ed] px-5 py-3 text-sm font-bold text-[#9a3412] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {reviewActionId === openReview.id ? "생성 중" : "이미지·음성 생성하기"}
                </button>
              )}
              <button
                onClick={handleRejectReview}
                disabled={reviewActionId === openReview.id}
                className="rounded-md border border-[#fecaca] bg-[#fef2f2] px-5 py-3 text-sm font-bold text-[#991b1b]"
              >
                {reviewActionId === openReview.id ? "저장 중" : "사용 안 함"}
              </button>
              <button
                onClick={() => {
                  if (isReviewEditing) {
                    setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
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
                onClick={handleApproveReview}
                disabled={reviewActionId === openReview.id}
                className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white"
              >
                {reviewActionId === openReview.id ? "저장 중" : "사용 승인"}
              </button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
