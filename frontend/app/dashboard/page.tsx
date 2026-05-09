"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  approveContent,
  createAgentRun,
  createContentAssetGenerationJob,
  createContentGeneration,
  createSupportProfileDraft,
  createTeacherStudentNote,
  createTeacherReportDraft,
  confirmSupportProfile,
  getAgentRun,
  getContentAssetGenerationJob,
  getReviewableContent,
  getTeacherStudent,
  getTeacherStudentReport,
  getTeacherStudents,
  listAgentRuns,
  publishContent,
  refreshStudentContextBrief,
  rejectContent,
  saveTeacherReport,
  updateContentReview,
  type AgentRun,
  type AssetGenerationJob,
  type CaseNote,
  type MissionContent,
  type StudentCaseFile,
  type StudentListItem,
  type StudentRegistrationResponse,
  type StudentReport,
  type SupportProfileDraftResponse,
} from "@/lib/api";
import { StudentRegistrationModal } from "./StudentRegistrationModal";

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
  generatedAtLabel: string | null;
};

type GenerationStatus = {
  state: "running" | "succeeded" | "failed";
  message: string;
};

type PendingGenerationJob = {
  caseId: string;
  studentId: string;
  requestedGoal: string;
  contentType: string;
  phase: "orchestrator" | "content" | "assets";
  orchestratorRunId?: string;
  contentRunId?: string;
  contentId?: string;
  assetJobId?: string;
  startedAt: string;
};

const PENDING_GENERATION_STORAGE_KEY = "eduyj:pending-generation-jobs";
const GENERATION_RUNNING_TIMEOUT_MS = 30 * 60 * 1000;
const ASSET_GENERATION_RUNNING_TIMEOUT_MS = 60 * 60 * 1000;
const ASSET_GENERATION_POLL_INTERVAL_MS = 3000;

function readPendingGenerationJobs(): Record<string, PendingGenerationJob> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(PENDING_GENERATION_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, PendingGenerationJob>;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writePendingGenerationJobs(jobs: Record<string, PendingGenerationJob>) {
  if (typeof window === "undefined") return;
  if (Object.keys(jobs).length === 0) {
    window.localStorage.removeItem(PENDING_GENERATION_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(PENDING_GENERATION_STORAGE_KEY, JSON.stringify(jobs));
}

function getGeneratedContentId(agentRun: AgentRun) {
  const output = agentRun.outputJson;
  if (!output) return null;
  const candidate = typeof output.missionContent === "object" && output.missionContent !== null ? output.missionContent : output;
  const id = (candidate as { id?: unknown }).id;
  return typeof id === "string" ? id : null;
}

function getSnapshotText(agentRun: AgentRun, key: string) {
  const value = agentRun.inputSnapshotJson[key];
  return typeof value === "string" ? value : "";
}

function isTimedOutIsoDate(value: string, timeoutMs = GENERATION_RUNNING_TIMEOUT_MS) {
  const timestamp = new Date(value).getTime();
  return Number.isFinite(timestamp) && Date.now() - timestamp > timeoutMs;
}

function isAgentRunTimedOut(agentRun: AgentRun) {
  return agentRun.status === "running" && isTimedOutIsoDate(agentRun.createdAt);
}

function isPendingGenerationJobTimedOut(job: PendingGenerationJob) {
  return isTimedOutIsoDate(
    job.startedAt,
    job.phase === "assets" ? ASSET_GENERATION_RUNNING_TIMEOUT_MS : GENERATION_RUNNING_TIMEOUT_MS,
  );
}

function getPendingJobFromAgentRun(agentRun: AgentRun): PendingGenerationJob | null {
  const studentId = getSnapshotText(agentRun, "studentId");
  const caseId = getSnapshotText(agentRun, "caseId");
  if (!studentId || !caseId) return null;

  if (agentRun.agentType === "orchestrator") {
    return {
      caseId,
      studentId,
      requestedGoal: getSnapshotText(agentRun, "requestedGoal"),
      contentType: getSnapshotText(agentRun, "contentType") || "learning_focus",
      phase: "orchestrator",
      orchestratorRunId: agentRun.id,
      startedAt: agentRun.createdAt,
    };
  }

  if (agentRun.agentType === "content") {
    const contentId = agentRun.status === "succeeded" ? getGeneratedContentId(agentRun) : null;
    return {
      caseId,
      studentId,
      requestedGoal: "",
      contentType: "learning_focus",
      phase: contentId ? "assets" : "content",
      orchestratorRunId: getSnapshotText(agentRun, "orchestratorRunId") || undefined,
      contentRunId: agentRun.id,
      contentId: contentId ?? undefined,
      startedAt: contentId ? new Date().toISOString() : agentRun.createdAt,
    };
  }

  return null;
}

type ReviewStageDraft = {
  step: 1 | 2 | 3 | 4;
  stageRole: string;
  templateType: string;
  assetRole: string;
  isRealtimeStage: boolean;
  title: string;
  description: string;
  question: string;
  choices: string[];
  imagePrompt: string;
  realtimePracticeTitle?: string;
  realtimeSituationText?: string;
  realtimeOpeningLine?: string;
  realtimeStudentGoal?: string;
  realtimeRubric?: string[];
  realtimeAllowedFeedback?: string[];
  realtimeMaxDurationSec?: number;
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

type SavedFeedbackRecord = {
  id: string;
  recordId: string;
  feedback: string;
  savedAt: string;
};

type GeneratedReportDraft = {
  draftId: string;
  bodyMarkdown: string;
  memoryCandidates: string[];
};

const tabs: Array<{ id: DashboardTab; label: string; description: string }> = [
  { id: "info", label: "학생 정보", description: "기본 정보와 현재 학습 상태" },
  { id: "materials", label: "자료 제안·검토", description: "수업 자료 제안을 확인" },
  { id: "records", label: "학습 기록", description: "피드백과 관찰 기록" },
];

const realtimeSpeakingTargetTurns = 3;

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
    label: "자료 제안 확인",
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
const reportFeedbackNotePrefix = "review_summary_feedback:";
const studentPreviewViewport = {
  width: 1160,
  height: 890,
};

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
  const compactPrimaryNeed = compactGoalText(item.primaryNeed);

  return {
    id: `${item.studentId}-case-summary`,
    studentId: item.studentId,
    status,
    statusLabel: item.statusLabel ?? item.dashboardStageLabel ?? learningStatus[status].label,
    caseType: item.trackLabel ?? item.studentTypeLabel ?? (item.studentType === "learning_focus" ? "학습지원형" : "일상생활 지원형"),
    primaryNeed: compactPrimaryNeed,
    sessionGoal: compactPrimaryNeed,
    supportStrategy: item.supportStrategy ?? item.aiContextSummary ?? (item.studentType === "learning_focus" ? "초기 학습 반응 확인" : "상황 장면 기반"),
    nextAction: item.nextSessionSuggestion,
    riskNote: "학생 화면에는 진단 표현을 노출하지 않음",
    challengeTags: item.weaknesses && item.weaknesses.length > 0 ? item.weaknesses : [compactPrimaryNeed],
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
    primaryNeed: dashboard?.primaryNeedDetail ?? compactGoalText(caseFile.profile.primaryNeed),
    sessionGoal: caseFile.openCase.currentGoal,
    supportStrategy:
      dashboard?.supportStrategyDetail ??
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

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
}

function compactGoalText(value: string) {
  return value
    .replace(/\s*수업이 좋겠어요\.?$/u, "")
    .replace(/\s*콘텐츠가 좋겠어요\.?$/u, "")
    .replace(/\s*해보면 좋겠어요\.?$/u, "");
}

function toProposalLabel(label: string) {
  if (label === "자료 생성") return "자료 제안";
  if (label === "자료 검토") return "제안 검토";
  if (label === "AI 자료 확인") return "자료 제안 확인";
  return label;
}

function toPercentScore(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) return 0;
  const percent = value <= 1 ? value * 100 : value;
  return Math.min(100, Math.max(0, Math.round(percent)));
}

function toTimestamp(value?: string | null) {
  if (!value) return 0;
  const timestamp = new Date(value).getTime();
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function parseReportFeedbackNote(note: CaseNote): SavedFeedbackRecord | null {
  if (!note.body.startsWith(reportFeedbackNotePrefix)) return null;

  const [recordIdLine = "", ...feedbackLines] = note.body.slice(reportFeedbackNotePrefix.length).split("\n");
  const recordId = recordIdLine.trim();
  const feedback = feedbackLines.join("\n").trim();
  if (!recordId || !feedback) return null;

  return {
    id: note.id,
    recordId,
    feedback,
    savedAt: note.createdAt.slice(0, 10),
  };
}

function markdownToPlainSummary(markdown: string, maxLength = 120) {
  const plain = markdown
    .split("\n")
    .map((line) => line.replace(/^#{1,6}\s*/, "").replace(/^-\s*/, "").trim())
    .filter(Boolean)
    .join(" ");
  return plain.length > maxLength ? `${plain.slice(0, maxLength).trim()}...` : plain;
}

function composeTeacherReportBody(aiDraftMarkdown: string | undefined, teacherMemo: string | undefined) {
  const parts = [];
  if (aiDraftMarkdown?.trim()) parts.push(aiDraftMarkdown.trim());
  if (teacherMemo?.trim()) {
    parts.push(["## 선생님 관찰 기록", teacherMemo.trim()].join("\n"));
  }
  return parts.join("\n\n").trim();
}

function teacherObservationMemoryCandidate(teacherMemo: string | undefined) {
  const cleaned = teacherMemo?.trim();
  if (!cleaned) return null;
  return `선생님 관찰: ${markdownToPlainSummary(cleaned, 180)}`;
}

function MarkdownReport({ markdown }: { markdown: string }) {
  const blocks: Array<{ type: "heading"; text: string } | { type: "list"; items: string[] } | { type: "paragraph"; text: string }> = [];
  let pendingList: string[] = [];

  const flushList = () => {
    if (pendingList.length > 0) {
      blocks.push({ type: "list", items: pendingList });
      pendingList = [];
    }
  };

  markdown.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }
    if (trimmed.startsWith("## ")) {
      flushList();
      blocks.push({ type: "heading", text: trimmed.replace(/^##\s*/, "") });
      return;
    }
    if (trimmed.startsWith("- ")) {
      pendingList.push(trimmed.replace(/^-\s*/, ""));
      return;
    }
    flushList();
    blocks.push({ type: "paragraph", text: trimmed.replace(/^#{1,6}\s*/, "") });
  });
  flushList();

  return (
    <div className="space-y-3 text-sm leading-6 text-[#334155]">
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          return (
            <h4 key={`${block.type}-${index}`} className="pt-1 text-sm font-black text-[#172033]">
              {block.text}
            </h4>
          );
        }
        if (block.type === "list") {
          return (
            <ul key={`${block.type}-${index}`} className="space-y-1.5">
              {block.items.map((item, itemIndex) => (
                <li key={`${item}-${itemIndex}`} className="flex gap-2 font-semibold">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1f3a5f]" />
                  <span className="min-w-0 break-keep [overflow-wrap:anywhere]">{item}</span>
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={`${block.type}-${index}`} className="font-semibold break-keep [overflow-wrap:anywhere]">
            {block.text}
          </p>
        );
      })}
    </div>
  );
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
    return "앞 단계에서 익힌 내용을 실제 말하기 상황으로 옮기는 실시간 발화 연습으로 연결합니다.";
  }

  if (stage.step === 1) {
    return "긴 설명 전에 그림 단서를 먼저 확인하며 쉬운 성공 경험으로 시작합니다.";
  }

  if (stage.step === 2) {
    return "짧은 선택지나 카드로 핵심 단서를 한 번 더 확인합니다.";
  }

  return "앞 단계에서 고른 단서를 문장이나 기호와 연결해 수업 목표로 정리합니다.";
}

function getAiGenerationFailureMessage(agentRun?: AgentRun | null) {
  if (agentRun?.errorCode === "OPENAI_API_KEY_MISSING") {
    return "서버에 자료 생성 설정이 없어 실제 자료 생성은 아직 실행되지 않았습니다. 설정을 연결하면 같은 버튼으로 생성됩니다.";
  }

  if (agentRun?.errorMessage) {
    return agentRun.errorMessage;
  }

  return "자료 제안을 만들지 못했습니다. 잠시 뒤 다시 시도해 주세요.";
}

function getClientGenerationErrorMessage(error: unknown) {
  const code = typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
  if (code === "OPENAI_API_KEY_MISSING") {
    return "서버에 자료 생성 설정이 없어 실제 자료 생성은 아직 실행되지 않았습니다. 설정을 연결하면 같은 버튼으로 생성됩니다.";
  }

  if (error instanceof Error && error.message && !error.message.includes("OPENAI_API_KEY")) {
    return error.message;
  }

  return "자료 제안 요청 중 문제가 생겼습니다. 잠시 뒤 다시 시도해 주세요.";
}

function isGeneratedMediaReady(asset?: MissionContent["assets"][number] | null) {
  const url = asset?.previewUrl || asset?.storageUrl;
  if (asset?.qaStatus !== "passed") return false;
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

function findPendingGenerationContent(job: PendingGenerationJob, caseFile?: StudentCaseFile | null) {
  if (!caseFile || !job.contentId) return null;
  return caseFile.recentContents.find((content) => content.id === job.contentId) ?? null;
}

function findCompletedReviewContentForGenerationJob(job: PendingGenerationJob, caseFile?: StudentCaseFile | null) {
  if (!caseFile) return null;
  const exactContent = findPendingGenerationContent(job, caseFile);
  if (isPendingGenerationContentComplete(exactContent)) return exactContent;

  const matchesSelectedCase =
    job.caseId === caseFile.openCase.id || Boolean(job.studentId && job.studentId === caseFile.profile.id);
  if (!matchesSelectedCase) return null;

  return (
    caseFile.recentContents
      .filter(isReviewQueueContent)
      .filter(isPendingGenerationContentComplete)
      .sort((left, right) => getContentActivityTime(right) - getContentActivityTime(left))[0] ?? null
  );
}

function isPendingGenerationContentUsable(content: MissionContent | null): content is MissionContent {
  return (
    content !== null &&
    (content.status === "teacher_review" || content.status === "approved" || content.status === "published")
  );
}

function isPendingGenerationContentComplete(content: MissionContent | null): content is MissionContent {
  return isPendingGenerationContentUsable(content) && !hasMissingGeneratedMedia(content);
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function isAssetGenerationJobRunning(job: AssetGenerationJob) {
  return job.status === "queued" || job.status === "running";
}

function getAssetGenerationJobMessage(job: AssetGenerationJob) {
  const progress = `${Math.min(job.completedCount + job.failedCount, job.totalCount)}/${job.totalCount}`;
  if (job.status === "queued") return `이미지와 음성 asset 생성 job을 준비 중입니다. (${progress})`;
  if (job.status === "running") return `이미지와 음성 asset을 생성하는 중입니다. (${progress})`;
  if (job.status === "partial_failed") return `일부 asset 생성에 실패했습니다. 성공한 asset은 유지했고 실패 ${job.failedCount}개만 다시 생성할 수 있습니다.`;
  if (job.status === "failed") return job.errorMessage ?? "이미지와 음성 asset 생성에 실패했습니다.";
  return "이미지와 음성까지 포함한 검토용 수업 자료가 만들어졌습니다.";
}

async function generateAssetPackageWithRecovery(
  content: MissionContent,
  options: {
    assetJobId?: string;
    onJobUpdate?: (job: AssetGenerationJob) => void;
  } = {},
) {
  const generatedContent = content;
  let job: AssetGenerationJob | null = null;
  let assetGenerationErrorMessage: string | null = null;

  try {
    job = options.assetJobId
      ? await getContentAssetGenerationJob(generatedContent.id, options.assetJobId)
      : await createContentAssetGenerationJob(generatedContent.id);
    options.onJobUpdate?.(job);

    while (isAssetGenerationJobRunning(job)) {
      await wait(ASSET_GENERATION_POLL_INTERVAL_MS);
      job = await getContentAssetGenerationJob(generatedContent.id, job.jobId);
      options.onJobUpdate?.(job);
    }

    if (job.status === "partial_failed" || job.status === "failed") {
      assetGenerationErrorMessage = getAssetGenerationJobMessage(job);
    }
  } catch (assetError) {
    assetGenerationErrorMessage = getClientGenerationErrorMessage(assetError);
  }

  const refreshedContent = await getReviewableContent(generatedContent.id).catch(() => null);
  if (isPendingGenerationContentComplete(refreshedContent)) {
    return {
      content: refreshedContent,
      errorMessage: null,
      job,
    };
  }

  return {
    content: refreshedContent ?? generatedContent,
    errorMessage: assetGenerationErrorMessage,
    job,
  };
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

function mapContentToReviewItem(content: MissionContent): MaterialReviewItem {
  return {
    id: content.id,
    caseId: content.caseId,
    title: content.title.trim() || "검토할 수업 자료 제안",
    type: `수업 전 검토 제안 · ${describeContentType(content)}`,
    state: describeMissionStatus(content.status),
    contentId: content.id,
    content,
    generatedAtLabel: formatContentGeneratedAt(content),
  };
}

function getContentActivityTime(content: MissionContent) {
  const generatedAt = content.briefJson.generatedAt;
  const timestamp = content.publishedAt ?? content.approvedAt ?? (typeof generatedAt === "string" ? generatedAt : "");
  const value = timestamp ? new Date(timestamp).getTime() : 0;
  return Number.isFinite(value) ? value : 0;
}

function hasGeneratedAt(content: MissionContent) {
  return typeof content.briefJson.generatedAt === "string" && content.briefJson.generatedAt.trim().length > 0;
}

function isReviewQueueContent(content: MissionContent) {
  return hasGeneratedAt(content) && (content.status === "teacher_review" || content.status === "approved");
}

function formatContentGeneratedAt(content: MissionContent) {
  const generatedAt = content.briefJson.generatedAt;
  if (typeof generatedAt !== "string") return null;
  const date = new Date(generatedAt);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function getActivePublishedContentIds(contents: MissionContent[] = []) {
  const latestByCase = new Map<string, MissionContent>();
  contents
    .filter((content) => content.status === "published")
    .forEach((content) => {
      const current = latestByCase.get(content.caseId);
      if (!current || getContentActivityTime(content) > getContentActivityTime(current)) {
        latestByCase.set(content.caseId, content);
      }
    });

  return new Set(Array.from(latestByCase.values()).map((content) => content.id));
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
        isRealtimeStage: stage.step === 4 || stage.stageRole === "realtime_practice",
        title: stage.studentTitle,
        description: stage.studentInstruction,
        question: stage.realtimeSpec?.studentGoal ?? question,
        choices: stage.step === 4 || stage.stageRole === "realtime_practice" ? [] : choicesFromTemplate(stage.templateJson),
        imagePrompt,
        realtimePracticeTitle: stage.realtimeSpec?.practiceTitle,
        realtimeSituationText: stage.realtimeSpec?.situationText,
        realtimeOpeningLine: stage.realtimeSpec?.openingLine,
        realtimeStudentGoal: stage.realtimeSpec?.studentGoal,
        realtimeRubric: stage.realtimeSpec?.rubric.map((item) => item.label),
        realtimeAllowedFeedback: stage.realtimeSpec?.allowedFeedback,
        realtimeMaxDurationSec: stage.realtimeSpec?.maxDurationSec,
      };
    });
}

function buildReviewStagePatches(content: MissionContent, drafts: ReviewStageDraft[]) {
  return drafts.flatMap((draft) => {
    const stage = content.stages.find((item) => item.step === draft.step);
    if (!stage) return [];

    return [
      {
        stageId: stage.id,
        studentInstruction: draft.description,
        question: draft.question,
        choices: draft.isRealtimeStage ? undefined : draft.choices,
        realtimeStudentGoal: draft.isRealtimeStage ? draft.question : undefined,
      },
    ];
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
  const [isRegistrationOpen, setIsRegistrationOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState<DashboardTab>("info");
  const [openReportId, setOpenReportId] = useState<string | null>(null);
  const [openReviewId, setOpenReviewId] = useState<string | null>(null);
  const [selectedFeedbackId, setSelectedFeedbackId] = useState<string | null>(null);
  const [approvedMaterialIds, setApprovedMaterialIds] = useState<string[]>([]);
  const [appliedMaterialIds, setAppliedMaterialIds] = useState<string[]>([]);
  const [reusedReportContentIds, setReusedReportContentIds] = useState<string[]>([]);
  const [revisionMaterialIds, setRevisionMaterialIds] = useState<string[]>([]);
  const [rejectedMaterialIds, setRejectedMaterialIds] = useState<string[]>([]);
  const [editingReviewIds, setEditingReviewIds] = useState<string[]>([]);
  const [reviewActionId, setReviewActionId] = useState<string | null>(null);
  const [reviewPreviewStep, setReviewPreviewStep] = useState(1);
  const [reviewPreviewRefreshKey, setReviewPreviewRefreshKey] = useState(0);
  const [reviewPreviewScale, setReviewPreviewScale] = useState(0.65);
  const reviewPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reportPreviewScale, setReportPreviewScale] = useState(0.65);
  const reportPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reportPreviewStep, setReportPreviewStep] = useState(1);
  const [reviewStageDrafts, setReviewStageDrafts] = useState<Record<string, ReviewStageDraft[]>>({});
  const [memoDrafts, setMemoDrafts] = useState<Record<string, string>>({});
  const [savedMemos, setSavedMemos] = useState<Record<string, string>>({});
  const [savingMemoCaseId, setSavingMemoCaseId] = useState<string | null>(null);
  const [lessonDrafts, setLessonDrafts] = useState<Record<string, string>>({});
  const [generationStatuses, setGenerationStatuses] = useState<Record<string, GenerationStatus>>({});
  const [pendingGenerationJobs, setPendingGenerationJobs] = useState<Record<string, PendingGenerationJob>>(readPendingGenerationJobs);
  const generationPollLocks = useRef<Set<string>>(new Set());
  const [feedbackDrafts, setFeedbackDrafts] = useState<Record<string, string>>({});
  const [generatedReportDrafts, setGeneratedReportDrafts] = useState<Record<string, GeneratedReportDraft>>({});
  const [savedFeedbackRecords, setSavedFeedbackRecords] = useState<SavedFeedbackRecord[]>([]);
  const [savingFeedbackRecordId, setSavingFeedbackRecordId] = useState<string | null>(null);
  const [generatingReportDraftId, setGeneratingReportDraftId] = useState<string | null>(null);
  const [supportProfileDraft, setSupportProfileDraft] = useState<SupportProfileDraftResponse | null>(null);
  const [supportProfileAction, setSupportProfileAction] = useState<"draft" | "confirm" | "refresh" | null>(null);
  const [reportReuseError, setReportReuseError] = useState("");

  const updatePendingGenerationJobs = useCallback((updater: (current: Record<string, PendingGenerationJob>) => Record<string, PendingGenerationJob>) => {
    setPendingGenerationJobs((current) => {
      const next = updater(current);
      writePendingGenerationJobs(next);
      return next;
    });
  }, []);

  useEffect(() => {
    writePendingGenerationJobs(pendingGenerationJobs);
  }, [pendingGenerationJobs]);

  useEffect(() => {
    if (!selectedStudentId) return;

    let ignore = false;
    async function restoreServerGenerationJob() {
      try {
        const runs = await listAgentRuns({ studentId: selectedStudentId });
        if (ignore) return;
        let restorableRun =
          runs.find(
            (run) =>
              run.status === "running" &&
              !isAgentRunTimedOut(run) &&
              (run.agentType === "orchestrator" || run.agentType === "content"),
          ) ?? null;
        if (!restorableRun) {
          restorableRun =
            runs.find((run) => {
              if (run.status !== "succeeded" || run.agentType !== "orchestrator") return false;
              return !runs.some(
                (candidate) =>
                  candidate.agentType === "content" &&
                  getSnapshotText(candidate, "orchestratorRunId") === run.id,
              );
            }) ?? null;
        }
        if (!restorableRun) {
          for (const run of runs) {
            if (run.status !== "succeeded" || run.agentType !== "content") continue;
            const contentId = getGeneratedContentId(run);
            if (!contentId) continue;
            const content = await getReviewableContent(contentId).catch(() => null);
            if (isPendingGenerationContentUsable(content) && hasMissingGeneratedMedia(content)) {
              restorableRun = run;
              break;
            }
          }
        }
        if (!restorableRun) return;

        const job = getPendingJobFromAgentRun(restorableRun);
        if (!job) return;
        updatePendingGenerationJobs((current) => {
          if (current[job.caseId]) return current;
          return { ...current, [job.caseId]: job };
        });
      } catch {
        // Local storage restoration still covers the normal path.
      }
    }

    void restoreServerGenerationJob();
    return () => {
      ignore = true;
    };
  }, [selectedStudentId, updatePendingGenerationJobs]);

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
    setSupportProfileDraft(null);

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
  const visibleSupportProfileJson =
    activeCaseFile?.supportProfile?.profileJson ??
    supportProfileDraft?.profileDraft ??
    activeCaseFile?.supportProfileDraft?.profileJson ??
    {};
  const supportProfileStatus = activeCaseFile?.supportProfile
    ? "confirmed"
    : supportProfileDraft || activeCaseFile?.supportProfileDraft
      ? "draft"
      : "none";
  const learningResponsePattern = (
    visibleSupportProfileJson.learningResponsePattern ??
    dashboardProfile?.learningResponsePattern ??
    {}
  ) as Record<string, unknown>;
  const behaviorSupportProfile = (
    visibleSupportProfileJson.behaviorSupportProfile ??
    dashboardProfile?.behaviorSupportProfile ??
    {}
  ) as Record<string, unknown>;
  const responseWorksWell = stringList(learningResponsePattern.worksWell);
  const responseCanBeHard = stringList(learningResponsePattern.canBeHard);
  const replacementSkills = stringList(behaviorSupportProfile.replacementSkills);
  const recommendedScaffolds = stringList(behaviorSupportProfile.recommendedScaffolds);
  const supportProfileStrengths = stringList(visibleSupportProfileJson.strengths);
  const supportProfileCautions = stringList(visibleSupportProfileJson.supportCautions);
  const supportProfileLessonHints = stringList(visibleSupportProfileJson.lessonDesignHints);
  const activeContextBrief = activeCaseFile?.contextBrief ?? activeCaseFile?.contextBundle?.contextBrief ?? null;

  useEffect(() => {
    if (!activeCaseFile) return;

    const latestMemo = [...activeCaseFile.weeklyRecords]
      .filter((note) => note.noteType === "teacher_comment")
      .sort((left, right) => toTimestamp(right.createdAt) - toTimestamp(left.createdAt))[0];
    const memo = latestMemo?.body ?? "";
    const caseId = activeCaseFile.openCase.id;

    setSavedMemos((current) => (current[caseId] === memo ? current : { ...current, [caseId]: memo }));
    setMemoDrafts((current) => (current[caseId] === undefined ? { ...current, [caseId]: memo } : current));
  }, [activeCaseFile]);

  useEffect(() => {
    if (!activeCaseFile) return;

    const completedJobIds = Object.values(pendingGenerationJobs)
      .filter((job) => Boolean(findCompletedReviewContentForGenerationJob(job, activeCaseFile)))
      .map((job) => job.caseId);
    if (completedJobIds.length === 0) return;

    updatePendingGenerationJobs((current) => {
      const next = { ...current };
      completedJobIds.forEach((caseId) => {
        delete next[caseId];
      });
      return next;
    });
    setGenerationStatuses((currentStatuses) => {
      const nextStatuses = { ...currentStatuses };
      completedJobIds.forEach((caseId) => {
        nextStatuses[caseId] = {
          state: "succeeded",
          message: "이미지와 음성까지 준비된 검토 자료가 만들어졌습니다.",
        };
      });
      return nextStatuses;
    });
  }, [activeCaseFile, pendingGenerationJobs, updatePendingGenerationJobs]);

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
  const serverSavedFeedbackRecords = useMemo(
    () => {
      const noteRecords = (activeCaseFile?.weeklyRecords ?? [])
        .map(parseReportFeedbackNote)
        .filter((item): item is SavedFeedbackRecord => Boolean(item));
      const teacherReportRecords = (activeReport?.reports ?? []).flatMap((record) =>
        (record.teacherReports ?? []).map((report) => ({
          id: report.id,
          recordId: record.id,
          feedback: report.teacherBody,
          savedAt: report.createdAt.slice(0, 10),
        })),
      );
      return [...teacherReportRecords, ...noteRecords];
    },
    [activeCaseFile?.weeklyRecords, activeReport?.reports],
  );
  const storedFeedbackRecords = useMemo(() => {
    const byRecordId = new Map<string, SavedFeedbackRecord>();
    savedFeedbackRecords.forEach((item) => byRecordId.set(item.recordId, item));
    serverSavedFeedbackRecords.forEach((item) => byRecordId.set(item.recordId, item));
    return Array.from(byRecordId.values());
  }, [savedFeedbackRecords, serverSavedFeedbackRecords]);
  const completedContentIds = new Set((activeReport?.reports ?? []).map((record) => record.contentId));
  const selectedReviewItems = (activeCaseFile?.recentContents ?? [])
    .filter((content) => !completedContentIds.has(content.id))
    .filter(isReviewQueueContent)
    .sort((left, right) => getContentActivityTime(right) - getContentActivityTime(left))
    .map((content) => mapContentToReviewItem(content));
  const selectedPublishedContents = (activeCaseFile?.recentContents ?? [])
    .filter((content) => content.status === "published")
    .sort((left, right) => getContentActivityTime(right) - getContentActivityTime(left));
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
    (record) => !storedFeedbackRecords.some((feedback) => feedback.recordId === record.id),
  );
  const feedbackTarget =
    feedbackQueue.find((record) => record.id === selectedFeedbackId) ?? feedbackQueue[0] ?? sessionLogs[0];
  const openReport = sessionLogs.find((record) => record.id === openReportId);
  const openReportTeacherFeedback = openReport
    ? storedFeedbackRecords.find((feedback) => feedback.recordId === openReport.id)
    : null;
  const openReportStageStep = reportPreviewStep;
  const isOpenReportReusing = openReport ? reviewActionId === openReport.contentId : false;
  const isOpenReportReused = openReport ? reusedReportContentIds.includes(openReport.contentId) : false;
  const openReview = selectedReviewItems.find((item) => item.id === openReviewId);
  const openReviewStages = openReview ? (reviewStageDrafts[openReview.id] ?? mapContentToReviewStages(openReview.content)) : reviewStagePreviews;
  const openReviewSelectedStages = openReviewStages.filter((stage) => stage.step === reviewPreviewStep);
  const openReviewNeedsMediaGeneration = openReview ? hasMissingGeneratedMedia(openReview.content) : false;
  const isReviewEditing = openReview ? editingReviewIds.includes(openReview.id) : false;
  const activePublishedContentIds = getActivePublishedContentIds(activeCaseFile?.recentContents);
  const isMaterialApproved = (item: MaterialReviewItem) =>
    item.content.status === "approved" || item.content.status === "published" || approvedMaterialIds.includes(item.id);
  const isMaterialApplied = (item: MaterialReviewItem) =>
    activePublishedContentIds.has(item.contentId) || appliedMaterialIds.includes(item.id);
  const isMaterialRejected = (item: MaterialReviewItem) =>
    item.content.status === "revision_requested" || rejectedMaterialIds.includes(item.id);
  const savedMemo = savedMemos[selectedCase.id] ?? "";
  const memoValue = memoDrafts[selectedCase.id] ?? savedMemo;
  const isMemoDirty = memoValue !== savedMemo;
  const isSavingMemo = savingMemoCaseId === selectedCase.id;
  const canSaveMemo = isMemoDirty && memoValue.trim().length > 0 && !isSavingMemo;
  const lessonDraftValue = lessonDrafts[selectedCase.id] ?? "";
  const aiRecommendedGoal = useMemo(() => {
    const presentationSupports = [...(activeContextBrief?.recommendedScaffolds ?? [])].slice(0, 3);
    const observedStrengths = [...(activeContextBrief?.recentSuccessPatterns ?? [])].slice(0, 2);
    const regressionGuards = [
      selectedCase.primaryNeed,
      ...(activeContextBrief?.avoidTopicRegression ?? []),
    ].filter(Boolean);
    return [
      "[AI 추천 생성]",
      "선생님 추가 입력 없이 학생 기억장치의 지원 방식만 참고해 오늘 사용할 새 수업 주제와 활동을 추천 생성합니다.",
      "기억장치에 남은 과거 상황은 예시 소재일 뿐이며, 새 수업 주제를 덮어쓰지 않습니다.",
      "수업 적용 힌트는 문제 수준을 낮추는 지시가 아니라 화면 제시 방식입니다.",
      observedStrengths.length ? `관찰된 수행 강점: ${observedStrengths.join(" / ")}` : "",
      presentationSupports.length ? `제시 방식 조정: ${presentationSupports.join(" / ")}` : "",
      regressionGuards.length ? `반복하지 않을 과거 예시 소재: ${regressionGuards.join(" / ")}` : "",
    ]
      .filter(Boolean)
      .join("\n");
  }, [
    activeContextBrief?.avoidTopicRegression,
    activeContextBrief?.recentSuccessPatterns,
    activeContextBrief?.recommendedScaffolds,
    selectedCase.primaryNeed,
  ]);
  const selectedPendingGenerationJob = Object.values(pendingGenerationJobs).find(
    (job) => job.caseId === selectedCase.id || (selectedCase.studentId && job.studentId === selectedCase.studentId),
  );
  const selectedPendingGenerationContent = selectedPendingGenerationJob
    ? findPendingGenerationContent(selectedPendingGenerationJob, activeCaseFile)
    : null;
  const selectedCompletedReviewContent = selectedPendingGenerationJob
    ? findCompletedReviewContentForGenerationJob(selectedPendingGenerationJob, activeCaseFile)
    : null;
  const isSelectedPendingGenerationComplete =
    isPendingGenerationContentComplete(selectedPendingGenerationContent) ||
    isPendingGenerationContentComplete(selectedCompletedReviewContent);
  const selectedPendingGenerationStatus: GenerationStatus | undefined = selectedPendingGenerationJob
    ? {
        state: isSelectedPendingGenerationComplete
          ? "succeeded"
          : isPendingGenerationJobTimedOut(selectedPendingGenerationJob)
            ? "failed"
            : "running",
        message: isSelectedPendingGenerationComplete
          ? "이미지와 음성까지 준비된 검토 자료가 만들어졌습니다."
          : isPendingGenerationJobTimedOut(selectedPendingGenerationJob)
          ? "생성 작업이 오래 응답하지 않아 멈춘 것으로 표시했습니다. 다시 제안받기를 눌러 주세요."
          : selectedPendingGenerationJob.phase === "orchestrator"
            ? "학생 기록을 바탕으로 수업 방향을 정리하는 중입니다."
            : selectedPendingGenerationJob.phase === "content"
              ? "검토할 수업 콘텐츠 구조를 만드는 중입니다."
              : "이미지와 음성 asset을 연결하는 중입니다.",
      }
    : undefined;
  const generationStatus =
    isSelectedPendingGenerationComplete && selectedPendingGenerationStatus
      ? selectedPendingGenerationStatus
      : generationStatuses[selectedCase.id] ??
        (selectedPendingGenerationJob ? generationStatuses[selectedPendingGenerationJob.caseId] : undefined) ??
        selectedPendingGenerationStatus;
  const isGeneratingContent =
    generationStatus?.state === "running" ||
    Boolean(
      selectedPendingGenerationJob &&
        !isSelectedPendingGenerationComplete &&
        !isPendingGenerationJobTimedOut(selectedPendingGenerationJob),
    );

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

  const continueGenerationJob = useCallback(async (job: PendingGenerationJob) => {
    if (generationPollLocks.current.has(job.caseId)) return;
    generationPollLocks.current.add(job.caseId);

    const setRunningMessage = (message: string) => {
      setGenerationStatuses((current) => ({
        ...current,
        [job.caseId]: { state: "running", message },
      }));
    };

    const failJob = (message: string) => {
      setGenerationStatuses((current) => ({
        ...current,
        [job.caseId]: { state: "failed", message },
      }));
      updatePendingGenerationJobs((current) => {
        const next = { ...current };
        delete next[job.caseId];
        return next;
      });
    };

    const completeJob = (content: MissionContent) => {
      setSelectedCaseFile((current) =>
        current && current.profile.id === content.studentId
          ? {
              ...current,
              recentContents: [content, ...current.recentContents.filter((item) => item.id !== content.id)],
            }
          : current,
      );
      setReviewPreviewStep(1);
      setOpenReviewId(content.id);
      setGenerationStatuses((current) => ({
        ...current,
        [job.caseId]: {
          state: "succeeded",
          message: "이미지와 음성까지 준비된 검토 자료가 만들어졌습니다.",
        },
      }));
      updatePendingGenerationJobs((current) => {
        const next = { ...current };
        delete next[job.caseId];
        return next;
      });
    };

    const completeAssetGeneration = async (assetJob: PendingGenerationJob) => {
      if (!assetJob.contentId) {
        failJob("생성된 콘텐츠를 찾지 못했습니다. 다시 시도해 주세요.");
        return;
      }

      const localContent = findPendingGenerationContent(assetJob, activeCaseFile);
      if (localContent && !isPendingGenerationContentUsable(localContent)) {
        failJob("이 자료는 이미 사용 안 함 상태라 생성 이어가기를 중단했습니다. 새 자료 제안을 다시 실행해 주세요.");
        return;
      }
      if (isPendingGenerationContentComplete(localContent)) {
        completeJob(localContent);
        return;
      }

      setRunningMessage("이미지와 음성 asset을 연결하는 중입니다.");
      let generatedContent = await getReviewableContent(assetJob.contentId);
      if (!isPendingGenerationContentUsable(generatedContent)) {
        failJob("이 자료는 이미 사용 안 함 상태라 생성 이어가기를 중단했습니다. 새 자료 제안을 다시 실행해 주세요.");
        return;
      }
      if (!hasMissingGeneratedMedia(generatedContent)) {
        completeJob(generatedContent);
        return;
      }

      const assetGenerationResult = await generateAssetPackageWithRecovery(generatedContent, {
        assetJobId: assetJob.assetJobId,
        onJobUpdate: (jobStatus) => {
          updatePendingGenerationJobs((current) => ({
            ...current,
            [assetJob.caseId]: {
              ...(current[assetJob.caseId] ?? assetJob),
              phase: "assets",
              contentId: generatedContent.id,
              assetJobId: jobStatus.jobId,
              startedAt: jobStatus.startedAt ?? jobStatus.queuedAt,
            },
          }));
          setGenerationStatuses((current) => ({
            ...current,
            [assetJob.caseId]: {
              state: isAssetGenerationJobRunning(jobStatus) ? "running" : jobStatus.status === "succeeded" ? "succeeded" : "failed",
              message: getAssetGenerationJobMessage(jobStatus),
            },
          }));
        },
      });
      generatedContent = assetGenerationResult.content;
      const assetGenerationErrorMessage = assetGenerationResult.errorMessage;

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

      const refreshedCaseFile = await getTeacherStudent(assetJob.studentId).catch(() => null);
      if (refreshedCaseFile) {
        setSelectedCaseFile(refreshedCaseFile);
      }
      const refreshedReport = await getTeacherStudentReport(assetJob.studentId).catch(() => null);
      if (refreshedReport) {
        setSelectedReport(refreshedReport);
      }

      setReviewPreviewStep(1);
      setOpenReviewId(generatedContent.id);
      setGenerationStatuses((current) => ({
        ...current,
        [assetJob.caseId]: {
          state: assetGenerationErrorMessage ? "failed" : "succeeded",
          message: assetGenerationErrorMessage
            ? `수업 구조는 만들어졌지만 이미지/음성 생성에 실패했습니다. ${assetGenerationErrorMessage}`
            : "이미지와 음성까지 포함한 검토용 수업 자료가 만들어졌습니다.",
        },
      }));
      updatePendingGenerationJobs((current) => {
        const next = { ...current };
        delete next[assetJob.caseId];
        return next;
      });
    };

    try {
      if (job.phase === "assets" && job.contentId) {
        const localContent = findPendingGenerationContent(job, activeCaseFile);
        if (isPendingGenerationContentComplete(localContent)) {
          completeJob(localContent);
          return;
        }

        const existingContent = await getReviewableContent(job.contentId).catch(() => null);
        if (isPendingGenerationContentComplete(existingContent)) {
          completeJob(existingContent);
          return;
        }
      }

      if (isPendingGenerationJobTimedOut(job)) {
        failJob("생성 작업이 오래 응답하지 않아 멈춘 것으로 표시했습니다. 다시 제안받기를 눌러 주세요.");
        return;
      }

      if (job.phase === "orchestrator") {
        if (!job.orchestratorRunId) {
          failJob("자료 방향 생성 기록을 찾지 못했습니다. 다시 시도해 주세요.");
          return;
        }

        setRunningMessage("학생 기록을 바탕으로 수업 방향을 정리하는 중입니다.");
        const orchestratorRun = await getAgentRun(job.orchestratorRunId);
        if (isAgentRunTimedOut(orchestratorRun)) {
          failJob("자료 방향 생성이 오래 응답하지 않아 중단된 것으로 표시했습니다. 다시 시도해 주세요.");
          return;
        }
        if (orchestratorRun.status === "running") return;
        if (orchestratorRun.status === "failed") {
          failJob(getAiGenerationFailureMessage(orchestratorRun));
          return;
        }

        const generationResult = await createContentGeneration({
          orchestratorRunId: orchestratorRun.id,
          studentId: job.studentId,
          caseId: job.caseId,
        });
        if (!generationResult.agentRun) {
          failJob("콘텐츠 생성 기록을 만들지 못했습니다. 다시 시도해 주세요.");
          return;
        }

        updatePendingGenerationJobs((current) => ({
          ...current,
          [job.caseId]: {
            ...job,
            phase: "content",
            contentRunId: generationResult.agentRun?.id,
            startedAt: new Date().toISOString(),
          },
        }));
        setRunningMessage("검토할 수업 콘텐츠 구조를 만드는 중입니다.");
        return;
      }

      if (job.phase === "content") {
        if (!job.contentRunId) {
          failJob("콘텐츠 생성 기록을 찾지 못했습니다. 다시 시도해 주세요.");
          return;
        }

        setRunningMessage("검토할 수업 콘텐츠 구조를 만드는 중입니다.");
        const contentRun = await getAgentRun(job.contentRunId);
        if (isAgentRunTimedOut(contentRun)) {
          failJob("콘텐츠 생성이 오래 응답하지 않아 중단된 것으로 표시했습니다. 다시 시도해 주세요.");
          return;
        }
        if (contentRun.status === "running") return;
        if (contentRun.status === "failed") {
          failJob(getAiGenerationFailureMessage(contentRun));
          return;
        }

        const contentId = getGeneratedContentId(contentRun);
        if (!contentId) {
          failJob("생성된 콘텐츠 ID를 확인하지 못했습니다. 다시 시도해 주세요.");
          return;
        }

        updatePendingGenerationJobs((current) => ({
          ...current,
          [job.caseId]: {
            ...job,
            phase: "assets",
            contentId,
            startedAt: new Date().toISOString(),
          },
        }));
        await completeAssetGeneration({
          ...job,
          phase: "assets",
          contentId,
          startedAt: new Date().toISOString(),
        });
        return;
      }

      if (!job.contentId) {
        failJob("생성된 콘텐츠를 찾지 못했습니다. 다시 시도해 주세요.");
        return;
      }

      setRunningMessage("이미지와 음성 asset을 연결하는 중입니다.");
      let generatedContent = await getReviewableContent(job.contentId);
      if (!isPendingGenerationContentUsable(generatedContent)) {
        failJob("이 자료는 이미 사용 안 함 상태라 생성 이어가기를 중단했습니다. 새 자료 제안을 다시 실행해 주세요.");
        return;
      }
      const assetGenerationResult = await generateAssetPackageWithRecovery(generatedContent, {
        assetJobId: job.assetJobId,
        onJobUpdate: (jobStatus) => {
          updatePendingGenerationJobs((current) => ({
            ...current,
            [job.caseId]: {
              ...(current[job.caseId] ?? job),
              phase: "assets",
              contentId: generatedContent.id,
              assetJobId: jobStatus.jobId,
              startedAt: jobStatus.startedAt ?? jobStatus.queuedAt,
            },
          }));
          setGenerationStatuses((current) => ({
            ...current,
            [job.caseId]: {
              state: isAssetGenerationJobRunning(jobStatus) ? "running" : jobStatus.status === "succeeded" ? "succeeded" : "failed",
              message: getAssetGenerationJobMessage(jobStatus),
            },
          }));
        },
      });
      generatedContent = assetGenerationResult.content;
      const assetGenerationErrorMessage = assetGenerationResult.errorMessage;

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

      const refreshedCaseFile = await getTeacherStudent(job.studentId).catch(() => null);
      if (refreshedCaseFile) {
        setSelectedCaseFile(refreshedCaseFile);
      }
      const refreshedReport = await getTeacherStudentReport(job.studentId).catch(() => null);
      if (refreshedReport) {
        setSelectedReport(refreshedReport);
      }

      setReviewPreviewStep(1);
      setOpenReviewId(generatedContent.id);
      setGenerationStatuses((current) => ({
        ...current,
        [job.caseId]: {
          state: assetGenerationErrorMessage ? "failed" : "succeeded",
          message: assetGenerationErrorMessage
            ? `수업 구조는 만들어졌지만 이미지/음성 생성에 실패했습니다. ${assetGenerationErrorMessage}`
            : "이미지와 음성까지 포함한 검토용 수업 자료가 만들어졌습니다.",
        },
      }));
      updatePendingGenerationJobs((current) => {
        const next = { ...current };
        delete next[job.caseId];
        return next;
      });
    } catch (error) {
      failJob(getClientGenerationErrorMessage(error));
    } finally {
      generationPollLocks.current.delete(job.caseId);
    }
  }, [activeCaseFile, updatePendingGenerationJobs]);

  useEffect(() => {
    Object.values(pendingGenerationJobs).forEach((job) => {
      if (findCompletedReviewContentForGenerationJob(job, activeCaseFile)) {
        setGenerationStatuses((current) => ({
          ...current,
          [job.caseId]: {
            state: "succeeded",
            message: "이미지와 음성까지 준비된 검토 자료가 만들어졌습니다.",
          },
        }));
        return;
      }

      setGenerationStatuses((current) => ({
        ...current,
        [job.caseId]: {
          state: "running",
          message:
            job.phase === "orchestrator"
              ? "학생 기록을 바탕으로 수업 방향을 정리하는 중입니다."
              : job.phase === "content"
                ? "검토할 수업 콘텐츠 구조를 만드는 중입니다."
                : "이미지와 음성 asset을 연결하는 중입니다.",
        },
      }));
      void continueGenerationJob(job);
    });

    if (Object.keys(pendingGenerationJobs).length === 0) return;
    const timer = window.setInterval(() => {
      Object.values(readPendingGenerationJobs()).forEach((job) => {
        void continueGenerationJob(job);
      });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [activeCaseFile, continueGenerationJob, pendingGenerationJobs]);

  const handleGenerateContent = async (mode: "teacher_request" | "ai_recommendation" = "teacher_request") => {
    if (!selectedCase.id || !selectedCase.studentId || isGeneratingContent) return;

    const requestedGoal = mode === "ai_recommendation" ? aiRecommendedGoal : lessonDraftValue.trim() || selectedCase.primaryNeed;
    const contentType = activeCaseFile?.profile.studentType ?? selectedApiStudent?.studentType ?? "learning_focus";
    setActiveTab("materials");

    setGenerationStatuses((current) => ({
          ...current,
          [selectedCase.id]: {
            state: "running",
            message:
              mode === "ai_recommendation"
                ? "기억장치를 바탕으로 AI 추천 수업 방향을 정리하는 중입니다."
                : "학생 기록을 바탕으로 수업 방향을 정리하는 중입니다.",
          },
        }));

    try {
      const orchestratorResult = await createAgentRun({
        studentId: selectedCase.studentId,
        caseId: selectedCase.id,
        requestedGoal,
        contentType,
      });

      if (!orchestratorResult.agentRun) {
        setGenerationStatuses((current) => ({
          ...current,
          [selectedCase.id]: {
            state: "failed",
            message: "자료 방향 생성 기록을 만들지 못했습니다. 다시 시도해 주세요.",
          },
        }));
        return;
      }

      const job: PendingGenerationJob = {
        caseId: selectedCase.id,
        studentId: selectedCase.studentId,
        requestedGoal,
        contentType,
        phase: "orchestrator",
        orchestratorRunId: orchestratorResult.agentRun.id,
        startedAt: new Date().toISOString(),
      };

      updatePendingGenerationJobs((current) => ({
        ...current,
        [selectedCase.id]: job,
      }));
      void continueGenerationJob(job);
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

  const handleRetryMaterialAssets = (item: MaterialReviewItem) => {
    if (isGeneratingContent || !hasMissingGeneratedMedia(item.content)) return;

    const job: PendingGenerationJob = {
      caseId: item.caseId,
      studentId: item.content.studentId,
      requestedGoal: item.content.sessionGoal,
      contentType: item.content.contentType,
      phase: "assets",
      contentId: item.contentId,
      startedAt: new Date().toISOString(),
    };
    setActiveTab("materials");
    setGenerationStatuses((current) => ({
      ...current,
      [job.caseId]: {
        state: "running",
        message: "실패했거나 비어 있는 이미지와 음성 asset만 다시 생성합니다.",
      },
    }));
    updatePendingGenerationJobs((current) => ({
      ...current,
      [job.caseId]: job,
    }));
    void continueGenerationJob(job);
  };

  const refreshStudentData = async (studentId: string) => {
    const [items, caseFile, report] = await Promise.all([
      getTeacherStudents(),
      getTeacherStudent(studentId),
      getTeacherStudentReport(studentId),
    ]);
    setTeacherStudentItems(items);
    setSelectedStudentId(studentId);
    setSelectedCaseFile(caseFile);
    setSelectedReport(report);
  };

  const refreshSelectedStudentData = async () => {
    if (!selectedCase.studentId) return;
    await refreshStudentData(selectedCase.studentId);
  };

  const handleRegisteredStudent = async (response: StudentRegistrationResponse) => {
    const studentId = response.student?.profile.id;
    const items = await getTeacherStudents();
    setTeacherStudentItems(items);
    setQuery("");
    setActiveTab("info");
    if (!studentId) return;
    setSelectedStudentId(studentId);
    const [caseFile, report] = await Promise.all([getTeacherStudent(studentId), getTeacherStudentReport(studentId)]);
    setSelectedCaseFile(caseFile);
    setSelectedReport(report);
  };

  const handleStartRegisteredStudentMaterials = async (response: StudentRegistrationResponse) => {
    const studentId = response.student?.profile.id;
    if (studentId && selectedStudentId !== studentId) {
      await refreshStudentData(studentId);
    }
    setActiveTab("materials");
  };

  const handleSaveMemo = async () => {
    if (!canSaveMemo || !selectedCase.studentId || !selectedCase.id) return;

    const nextMemo = memoValue.trim();
    setSavingMemoCaseId(selectedCase.id);
    try {
      await createTeacherStudentNote(selectedCase.studentId, {
        noteType: "teacher_comment",
        body: nextMemo,
        visibility: "teacher_only",
      });
      setSavedMemos((current) => ({
        ...current,
        [selectedCase.id]: nextMemo,
      }));
      setMemoDrafts((current) => ({
        ...current,
        [selectedCase.id]: nextMemo,
      }));
      await refreshSelectedStudentData();
    } finally {
      setSavingMemoCaseId(null);
    }
  };

  const handleCreateSupportProfileDraft = async () => {
    if (!selectedCase.studentId || supportProfileAction) return;
    setSupportProfileAction("draft");
    try {
      const draft = await createSupportProfileDraft(selectedCase.studentId);
      setSupportProfileDraft(draft);
    } finally {
      setSupportProfileAction(null);
    }
  };

  const handleConfirmSupportProfile = async () => {
    if (!selectedCase.studentId || !supportProfileDraft || supportProfileAction) return;
    setSupportProfileAction("confirm");
    try {
      await confirmSupportProfile(selectedCase.studentId, {
        draftId: supportProfileDraft.draftId,
        profileDraft: supportProfileDraft.profileDraft,
      });
      setSupportProfileDraft(null);
      await refreshSelectedStudentData();
    } finally {
      setSupportProfileAction(null);
    }
  };

  const handleRefreshContextBrief = async () => {
    if (!selectedCase.studentId || supportProfileAction) return;
    setSupportProfileAction("refresh");
    try {
      await refreshStudentContextBrief(selectedCase.studentId);
      await refreshSelectedStudentData();
    } finally {
      setSupportProfileAction(null);
    }
  };

  const handleGenerateTeacherReportDraft = async (record: SessionLog) => {
    if (generatingReportDraftId) return;
    setGeneratingReportDraftId(record.id);
    setGeneratedReportDrafts((current) => ({
      ...current,
      [record.id]: { draftId: "", bodyMarkdown: "", memoryCandidates: [] },
    }));
    try {
      const draft = await createTeacherReportDraft(record.id, {
        teacherObservation: feedbackDrafts[record.id] ?? "",
        onDelta: (text) => {
          setGeneratedReportDrafts((current) => ({
            ...current,
            [record.id]: {
              ...(current[record.id] ?? { draftId: "", bodyMarkdown: "", memoryCandidates: [] }),
              bodyMarkdown: `${current[record.id]?.bodyMarkdown ?? ""}${text}`,
            },
          }));
        },
      });
      setGeneratedReportDrafts((current) => ({ ...current, [record.id]: draft }));
    } finally {
      setGeneratingReportDraftId(null);
    }
  };

  const handleSaveTeacherFeedback = async (record: SessionLog) => {
    const teacherMemo = feedbackDrafts[record.id]?.trim();
    const generatedDraft = generatedReportDrafts[record.id];
    const reportBody = composeTeacherReportBody(generatedDraft?.bodyMarkdown, teacherMemo);
    if (!reportBody || !selectedCase.studentId || savingFeedbackRecordId) return;

    setSavingFeedbackRecordId(record.id);
    try {
      const teacherObservationCandidate = teacherObservationMemoryCandidate(teacherMemo);
      const selectedMemoryCandidates = [
        ...(teacherObservationCandidate ? [teacherObservationCandidate] : []),
        ...(generatedDraft?.memoryCandidates ?? [record.note]),
      ].slice(0, 3);
      await saveTeacherReport({
        draftId: generatedDraft?.draftId || null,
        reviewSummaryId: record.id,
        studentId: selectedCase.studentId,
        contentId: record.contentId,
        teacherBody: reportBody,
        selectedMemoryCandidates,
      });
      setSavedFeedbackRecords((current) => [
        {
          id: `feedback-${record.id}-${Date.now()}`,
          recordId: record.id,
          feedback: reportBody,
          savedAt: "방금 저장",
        },
        ...current.filter((item) => item.recordId !== record.id),
      ]);
      setFeedbackDrafts((current) => ({
        ...current,
        [record.id]: "",
      }));
      setGeneratedReportDrafts((current) => {
        const next = { ...current };
        delete next[record.id];
        return next;
      });
      await refreshSelectedStudentData();
    } finally {
      setSavingFeedbackRecordId(null);
    }
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

  const handleSaveReviewEdits = async () => {
    if (!openReview || reviewActionId) return;

    setReviewActionId(openReview.id);
    try {
      const content = await updateContentReview(openReview.contentId, {
        stages: buildReviewStagePatches(openReview.content, openReviewStages),
      });
      updateCurrentContent(content);
      setReviewStageDrafts((current) => ({
        ...current,
        [openReview.id]: mapContentToReviewStages(content),
      }));
      setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
      setRevisionMaterialIds((current) => (current.includes(openReview.id) ? current : [...current, openReview.id]));
      setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
      setReviewPreviewRefreshKey((current) => current + 1);
      await refreshSelectedStudentData();
    } catch {
      setReviewActionError("수정 내용을 DB에 저장하지 못했습니다. 다시 확인해 주세요.");
    } finally {
      setReviewActionId(null);
    }
  };

  const handleApproveReview = async () => {
    if (!openReview || openReviewNeedsMediaGeneration || reviewActionId) return;

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
    if (
      isMaterialApplied(item) ||
      !isMaterialApproved(item) ||
      isMaterialRejected(item) ||
      hasMissingGeneratedMedia(item.content) ||
      reviewActionId
    ) {
      return;
    }

    setReviewActionId(item.id);
    try {
      const content = await publishContent(item.contentId);
      updateCurrentContent(content);
      setAppliedMaterialIds((current) => [
        ...current.filter((id) => {
          const reviewItem = selectedReviewItems.find((candidate) => candidate.id === id);
          return reviewItem?.caseId !== item.caseId;
        }),
        item.id,
      ]);
      await refreshSelectedStudentData();
    } catch {
      setReviewActionError("수업 적용 상태를 저장하지 못했습니다. 승인된 자료인지 다시 확인해 주세요.");
    } finally {
      setReviewActionId(null);
    }
  };

  const handleReuseReportContent = async (record: SessionLog) => {
    if (reviewActionId || reusedReportContentIds.includes(record.contentId)) return;

    setReportReuseError("");
    setReviewActionId(record.contentId);
    try {
      const content = await publishContent(record.contentId);
      updateCurrentContent(content);
      setAppliedMaterialIds((current) => [
        ...current.filter((id) => {
          const reviewItem = selectedReviewItems.find((candidate) => candidate.id === id);
          return reviewItem?.caseId !== record.caseId;
        }),
        record.contentId,
      ]);
      setReusedReportContentIds((current) =>
        current.includes(record.contentId) ? current : [...current, record.contentId],
      );
      await refreshSelectedStudentData();
    } catch {
      setReportReuseError("학생 화면에 다시 적용하지 못했습니다. 잠시 후 다시 눌러 주세요.");
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
      setReviewPreviewScale(
        Math.min(
          1,
          Math.max(0.1, (width - 24) / studentPreviewViewport.width),
          Math.max(0.1, (height - 24) / studentPreviewViewport.height),
        ),
      );
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
      setReportPreviewScale(
        Math.min(
          1,
          Math.max(0.1, (width - 24) / studentPreviewViewport.width),
          Math.max(0.1, (height - 24) / studentPreviewViewport.height),
        ),
      );
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
            <button
              type="button"
              onClick={() => setIsRegistrationOpen(true)}
              className="w-full rounded-md bg-[#1f3a5f] px-4 py-3 text-sm font-bold text-white"
            >
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
                  <InfoBlock label="현재 지원 목표" value={dashboardProfile?.primaryNeedDetail ?? selectedCase.primaryNeed} />
                  <InfoBlock label="수업 설계 힌트" value={dashboardProfile?.supportStrategyDetail ?? selectedCase.supportStrategy} />
                  <InfoBlock
                    label="기억장치 상태"
                    value={
                      activeContextBrief
                        ? activeContextBrief.dirty
                          ? "갱신 필요"
                          : "갱신 완료"
                        : "생성 전"
                    }
                  />
                </section>

                <section className="rounded-lg border border-[#d8dee8] bg-white p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-xl font-black">기억장치</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        매주 또는 새 수업 기록이 생길 때 다시 정리되는 AI용 학생 맥락입니다.
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-black ${
                        activeContextBrief
                          ? activeContextBrief.dirty
                            ? "bg-[#fff7ed] text-[#9a3412]"
                            : "bg-[#f0fdf4] text-[#15803d]"
                          : "bg-[#f1f5f9] text-[#64748b]"
                      }`}
                    >
                      {activeContextBrief ? (activeContextBrief.dirty ? "갱신 필요" : "갱신 완료") : "생성 전"}
                    </span>
                  </div>

                  {activeContextBrief?.briefText ? (
                    <>
                      <p className="mt-4 rounded-md bg-[#f8fafc] px-4 py-3 text-sm font-semibold leading-6 text-[#334155]">
                        {activeContextBrief.briefText}
                      </p>
                      <div className="mt-4 grid gap-4 md:grid-cols-3">
                        <div>
                          <p className="text-sm font-black text-[#64748b]">관찰된 수행 강점</p>
                          <p className="mt-1 text-xs font-semibold leading-5 text-[#94a3b8]">
                            실제 반응 기록에서 확인된 시작점입니다.
                          </p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {(activeContextBrief.recentSuccessPatterns.length ? activeContextBrief.recentSuccessPatterns : ["기록 확인 중"]).map((item) => (
                              <span key={item} className="rounded-full bg-[#eef4fb] px-3 py-1 text-xs font-bold text-[#1f3a5f]">
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-black text-[#64748b]">주의할 흐름</p>
                          <p className="mt-1 text-xs font-semibold leading-5 text-[#94a3b8]">
                            다음 수업에서 먼저 확인할 부담 조건입니다.
                          </p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {(activeContextBrief.recentDifficultyPatterns.length ? activeContextBrief.recentDifficultyPatterns : ["기록 확인 중"]).map((item) => (
                              <span key={item} className="rounded-full bg-[#fff7ed] px-3 py-1 text-xs font-bold text-[#9a3412]">
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-black text-[#64748b]">제시 방식 조정</p>
                          <p className="mt-1 text-xs font-semibold leading-5 text-[#94a3b8]">
                            문제 수준을 낮추는 값이 아니라 화면과 안내 방식을 조정하는 값입니다.
                          </p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {(activeContextBrief.recommendedScaffolds.length ? activeContextBrief.recommendedScaffolds : ["기록 확인 중"]).map((item) => (
                              <span key={item} className="rounded-full bg-[#f0fdf4] px-3 py-1 text-xs font-bold text-[#15803d]">
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="mt-4 rounded-md bg-[#f8fafc] px-4 py-3 text-sm font-semibold leading-6 text-[#64748b]">
                      아직 생성된 기억장치가 없습니다. 지원 초안을 확정하거나 수업 기록을 저장하면 다음 자료 생성에 반영할 요약을 만들 수 있습니다.
                    </p>
                  )}
                </section>

                <section className="rounded-lg border border-[#d8dee8] bg-[#fbfcfe] p-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-xl font-black">초기 지원 프로필</h3>
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-black ${
                            supportProfileStatus === "confirmed"
                              ? "bg-[#dcfce7] text-[#15803d]"
                              : supportProfileStatus === "draft"
                                ? "bg-[#eff6ff] text-[#1d4ed8]"
                                : "bg-[#f1f5f9] text-[#64748b]"
                          }`}
                        >
                          {supportProfileStatus === "confirmed" ? "교사 확인 완료" : supportProfileStatus === "draft" ? "초안" : "작성 전"}
                        </span>
                      </div>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        학생 등록 원자료에서 만든 수업 방식 프로필입니다. 기억장치와 별도로 관리되고, 교사 확인 뒤 다음 자료 생성에 반영됩니다.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => void handleCreateSupportProfileDraft()}
                        disabled={!selectedCase.studentId || Boolean(supportProfileAction)}
                        className="rounded-md border border-[#cbd5e1] bg-white px-4 py-2 text-sm font-black text-[#334155] disabled:cursor-not-allowed disabled:text-[#94a3b8]"
                      >
                        {supportProfileAction === "draft" ? "생성 중" : "지원 초안 생성"}
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleRefreshContextBrief()}
                        disabled={!selectedCase.studentId || Boolean(supportProfileAction)}
                        className="rounded-md border border-[#cbd5e1] bg-white px-4 py-2 text-sm font-black text-[#334155] disabled:cursor-not-allowed disabled:text-[#94a3b8]"
                      >
                        {supportProfileAction === "refresh" ? "갱신 중" : "기억장치 갱신"}
                      </button>
                    </div>
                  </div>
                  <p className="mt-3 rounded-md bg-white px-4 py-3 text-sm font-semibold leading-6 text-[#64748b]">
                    기억장치 갱신은 수업 기록, 선생님 관찰 기록, 확정된 지원 프로필을 다시 요약합니다. 초기 지원 프로필 초안은 바꾸지 않습니다.
                  </p>

                  {supportProfileDraft && (
                    <div className="mt-4 rounded-lg border border-[#bfdbfe] bg-white p-4">
                      <p className="text-sm font-black text-[#1d4ed8]">수업 설계 초안</p>
                      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm font-semibold leading-6 text-[#334155]">
                        {stringList(supportProfileDraft.profileDraft.lessonDesignHints).map((hint) => (
                          <li key={hint}>{hint}</li>
                        ))}
                      </ul>
                      <div className="mt-3 flex justify-end">
                        <button
                          type="button"
                          onClick={() => void handleConfirmSupportProfile()}
                          disabled={Boolean(supportProfileAction)}
                          className="rounded-md bg-[#1f3a5f] px-4 py-2 text-sm font-black text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
                        >
                          {supportProfileAction === "confirm" ? "저장 중" : "교사 확인 완료"}
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    <InfoBlock
                      label="관찰된 강점"
                      value={(
                        responseWorksWell.length
                          ? responseWorksWell
                          : supportProfileStrengths.length
                            ? supportProfileStrengths
                            : supportProfileLessonHints.length
                              ? supportProfileLessonHints
                              : ["지원 초안 생성 전"]
                      ).join(", ")}
                    />
                    <InfoBlock
                      label="지원이 필요한 상황"
                      value={(
                        responseCanBeHard.length
                          ? responseCanBeHard
                          : supportProfileCautions.length
                            ? supportProfileCautions
                            : selectedCase.challengeTags
                      ).join(", ")}
                    />
                    <InfoBlock
                      label="수업 적용 힌트"
                      value={(recommendedScaffolds.length ? recommendedScaffolds : supportProfileLessonHints.length ? supportProfileLessonHints : selectedCase.planTags).join(", ")}
                    />
                    <InfoBlock
                      label="연습할 표현·기술"
                      value={(replacementSkills.length ? replacementSkills : ["확정 프로필 저장 뒤 표시"]).join(", ")}
                    />
                  </div>
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
                    <h3 className="text-xl font-black">주의할 점</h3>
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
                      <h3 className="text-xl font-black">선생님 통합 메모</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        특정 콘텐츠가 아니라 학생 전체에 대해 계속 참고할 관찰과 조정점을 남깁니다.
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
                    placeholder="예: 긴 설명보다 그림 단서를 먼저 볼 때 안정적입니다. 실패 직후에는 바로 재촉하기보다 쉬운 선택지로 다시 시작하면 좋습니다."
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
                      onClick={() => void handleSaveMemo()}
                      className={`rounded-md px-4 py-2 text-sm font-bold transition ${
                        canSaveMemo
                          ? "bg-[#1f3a5f] text-white shadow-[0_8px_18px_rgba(31,58,95,0.18)]"
                          : "cursor-not-allowed bg-[#e2e8f0] text-[#94a3b8]"
                      }`}
                    >
                      {isSavingMemo ? "저장 중" : "메모리로 저장"}
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

                      <div className="grid gap-2 sm:grid-cols-2">
                        <button
                          disabled={!selectedCase.id || isGeneratingContent}
                          onClick={() => void handleGenerateContent("teacher_request")}
                          className={`rounded-md px-4 py-3 text-sm font-bold text-white ${
                            !selectedCase.id || isGeneratingContent
                              ? "cursor-not-allowed bg-[#94a3b8]"
                              : "bg-[#1f3a5f] hover:bg-[#172b47]"
                          }`}
                        >
                          {isGeneratingContent ? "자료를 제안하는 중" : "입력 내용으로 생성"}
                        </button>
                        <button
                          disabled={!selectedCase.id || isGeneratingContent}
                          onClick={() => void handleGenerateContent("ai_recommendation")}
                          className={`rounded-md border px-4 py-3 text-sm font-bold ${
                            !selectedCase.id || isGeneratingContent
                              ? "cursor-not-allowed border-[#cbd5e1] bg-[#f1f5f9] text-[#94a3b8]"
                              : "border-[#bfdbfe] bg-[#eff6ff] text-[#1f3a5f] hover:bg-[#dbeafe]"
                          }`}
                        >
                          {isGeneratingContent ? "추천 준비 중" : "AI 추천 생성"}
                        </button>
                      </div>
                    </div>
                  </div>
                </section>

                <div className="space-y-4">
                  <section className="space-y-3">
                    <div>
                      <h3 className="text-xl font-black">검토할 수업 자료 제안</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        제안된 자료를 확인하고 선생님 판단으로 적용합니다.
                      </p>
                    </div>
                    {generationStatus && generationStatus.state !== "succeeded" && (
                      <div
                        className={`rounded-md border p-4 ${
                          generationStatus.state === "failed"
                            ? "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
                            : "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          {generationStatus.state === "failed" ? (
                            <div className="mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-full border border-[#fed7aa] bg-white text-xs font-black">
                              !
                            </div>
                          ) : (
                            <div className="mt-1 h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-[#93c5fd] border-t-[#1d4ed8]" />
                          )}
                          <div>
                            <p className="text-base font-black">
                              {generationStatus.state === "failed" ? "생성 확인 필요" : "검토 자료 생성 중"}
                            </p>
                            <p className="mt-1 text-sm font-bold leading-6">{generationStatus.message}</p>
                            {generationStatus.state === "running" && (
                              <p className="mt-2 text-xs font-bold text-[#3b82f6]">새로고침해도 여기에서 이어서 확인합니다.</p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                    {selectedReviewItems.length === 0 && !isGeneratingContent && (
                      <div className="rounded-md border border-[#e5e9f0] bg-white p-4 text-sm font-bold leading-6 text-[#64748b]">
                        검토할 수업 자료 제안이 없습니다. 학생이 완료한 자료는 학습 기록에서 확인할 수 있어요.
                      </div>
                    )}
                    {selectedReviewItems.map((item) => {
                      const materialApplied = isMaterialApplied(item);
                      const materialApproved = isMaterialApproved(item);
                      const materialRejected = isMaterialRejected(item);
                      const isActionRunning = reviewActionId === item.id;
                      const needsMediaGeneration = hasMissingGeneratedMedia(item.content);
                      const teacherPreviewHref = `/student/stage?caseId=${encodeURIComponent(item.caseId)}&contentId=${encodeURIComponent(item.content.id)}&preview=1`;

                      return (
                        <div key={item.id} className="rounded-md border border-[#e5e9f0] bg-white p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate text-base font-black">{item.title}</p>
                              <p className="mt-1 truncate text-sm font-semibold text-[#64748b]">{item.type}</p>
                              {item.generatedAtLabel && (
                                <p className="mt-1 text-xs font-black text-[#94a3b8]">생성 {item.generatedAtLabel}</p>
                              )}
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
                          <div className="mt-3 flex flex-wrap items-center gap-2">
                            <button
                              onClick={() => {
                                setReviewPreviewStep(1);
                                setOpenReviewId(item.id);
                              }}
                              className="rounded-md border border-[#cbd5e1] bg-white px-3 py-2 text-sm font-bold text-[#334155]"
                            >
                              제안 검토하기
                            </button>
                            <Link
                              href={teacherPreviewHref}
                              target="_blank"
                              className="rounded-md border border-[#bfdbfe] bg-[#eff6ff] px-3 py-2 text-sm font-bold text-[#1d4ed8]"
                            >
                              교사용 미리보기
                            </Link>
                            {needsMediaGeneration && (
                              <button
                                onClick={() => handleRetryMaterialAssets(item)}
                                disabled={isGeneratingContent}
                                className="rounded-md border border-[#fed7aa] bg-[#fff7ed] px-3 py-2 text-sm font-bold text-[#9a3412] disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                이미지/음성 다시 생성
                              </button>
                            )}
                            <button
                              onClick={() => handlePublishMaterial(item)}
                              disabled={
                                materialApplied ||
                                !materialApproved ||
                                materialRejected ||
                                needsMediaGeneration ||
                                isActionRunning
                              }
                              className={`rounded-md px-3 py-2 text-sm font-bold ${
                                materialApplied
                                  ? "bg-[#dcfce7] text-[#15803d]"
                                  : materialApproved && !needsMediaGeneration
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

                  <section className="space-y-3">
                    <div>
                      <h3 className="text-xl font-black">현재 배포된 수업 자료</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        학생 화면에서 바로 열 수 있는 자료입니다.
                      </p>
                    </div>
                    {selectedPublishedContents.length === 0 ? (
                      <div className="rounded-md border border-[#e5e9f0] bg-white p-4 text-sm font-bold leading-6 text-[#64748b]">
                        아직 학생에게 배포된 수업 자료가 없습니다.
                      </div>
                    ) : (
                      selectedPublishedContents.map((content) => {
                        const contentCompleted = completedContentIds.has(content.id);
                        const generatedAtLabel = formatContentGeneratedAt(content);
                        return (
                          <div key={content.id} className="rounded-md border border-[#bbf7d0] bg-[#f0fdf4] p-4">
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="truncate text-base font-black text-[#172033]">{content.title}</p>
                                <p className="mt-1 truncate text-sm font-semibold text-[#15803d]">{describeContentType(content)}</p>
                                {generatedAtLabel && (
                                  <p className="mt-1 text-xs font-black text-[#64748b]">생성 {generatedAtLabel}</p>
                                )}
                              </div>
                              <span className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-black text-[#15803d]">
                                {contentCompleted ? "학습 완료" : "배포됨"}
                              </span>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                              <Link
                                href={`/student/stage?caseId=${encodeURIComponent(content.caseId)}&contentId=${encodeURIComponent(content.id)}&preview=1`}
                                target="_blank"
                                className="rounded-md border border-[#bbf7d0] bg-white px-3 py-2 text-sm font-bold text-[#15803d]"
                              >
                                교사용 미리보기
                              </Link>
                              <Link
                                href={`/student/stage?caseId=${encodeURIComponent(content.caseId)}&contentId=${encodeURIComponent(content.id)}`}
                                target="_blank"
                                className="rounded-md bg-[#15803d] px-3 py-2 text-sm font-bold text-white"
                              >
                                학생 화면 열기
                              </Link>
                            </div>
                          </div>
                        );
                      })
                    )}
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
                      {pendingFeedbackQueue.map((record) => {
                        const isSavingFeedback = savingFeedbackRecordId === record.id;

                        return (
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
                          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-md border border-[#bfdbfe] bg-white px-4 py-3">
                            <div>
                              <p className="text-xs font-black text-[#1d4ed8]">리포트 초안</p>
                              <p className="mt-1 text-sm font-semibold text-[#64748b]">
                                학생 수행 결과, 회고, 선생님 관찰 기록을 바탕으로 마크다운 초안을 실시간으로 받아 표시합니다.
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => void handleGenerateTeacherReportDraft(record)}
                              disabled={Boolean(generatingReportDraftId)}
                              className="rounded-md border border-[#cbd5e1] bg-[#eef4fb] px-4 py-2 text-sm font-black text-[#1f3a5f] disabled:cursor-not-allowed disabled:text-[#94a3b8]"
                            >
                              {generatingReportDraftId === record.id ? "생성 중" : "리포트 초안 생성"}
                            </button>
                          </div>
                          {generatedReportDrafts[record.id]?.bodyMarkdown && (
                            <div className="mt-3 rounded-md border border-[#bfdbfe] bg-[#f8fbff] px-4 py-3">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <p className="text-xs font-black text-[#1d4ed8]">리포트 초안 미리보기</p>
                                <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-black text-[#64748b]">
                                  이번 콘텐츠 기록
                                </span>
                              </div>
                              <div className="mt-3 rounded-md bg-white px-4 py-3">
                                <MarkdownReport markdown={generatedReportDrafts[record.id].bodyMarkdown} />
                              </div>
                            </div>
                          )}
                          {(generatedReportDrafts[record.id]?.memoryCandidates.length ?? 0) > 0 && (
                            <div className="mt-3 rounded-md border border-[#d9ebc9] bg-white px-4 py-3">
                              <p className="text-xs font-black text-[#16803c]">기억장치 반영 후보</p>
                              <div className="mt-2 flex flex-wrap gap-2">
                                {generatedReportDrafts[record.id].memoryCandidates.map((candidate) => (
                                  <span key={candidate} className="rounded-full bg-[#f0fdf4] px-3 py-1 text-xs font-bold text-[#15803d]">
                                    {candidate}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          <div className="mt-4">
                            <label className="text-xs font-black text-[#64748b]" htmlFor={`teacher-report-memo-${record.id}`}>
                              선생님 수업 관찰 기록
                            </label>
                            <p className="mt-1 text-xs font-semibold text-[#94a3b8]">
                              이번 콘텐츠를 지켜보며 확인한 잘된 점, 부족한 점, 다음 수업 반영점을 적습니다.
                            </p>
                          <textarea
                            id={`teacher-report-memo-${record.id}`}
                            value={feedbackDrafts[record.id] ?? ""}
                            onChange={(event) => {
                              setFeedbackDrafts((current) => ({
                                ...current,
                                [record.id]: event.target.value,
                              }));
                            }}
                            className="mt-2 h-28 w-full resize-none rounded-md border border-[#cbd5e1] bg-white p-4 outline-none focus:border-[#1f3a5f]"
                            placeholder="예: 그림 단서는 바로 찾았지만 실제 말하기에서는 먼저 물어보는 표현이 부족했습니다. 다음에는 더 현실적인 상황에서 확인 질문을 연습하면 좋겠습니다."
                          />
                          </div>
                          <div className="mt-3 flex justify-end">
                            <button
                              onClick={() => void handleSaveTeacherFeedback(record)}
                              disabled={!composeTeacherReportBody(generatedReportDrafts[record.id]?.bodyMarkdown, feedbackDrafts[record.id]).trim() || Boolean(savingFeedbackRecordId)}
                              className="rounded-md bg-[#1f3a5f] px-4 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
                            >
                              {isSavingFeedback ? "저장 중" : "리포트 확인 후 저장"}
                            </button>
                          </div>
                        </section>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-4 rounded-lg border border-[#e5e9f0] bg-white p-5 xl:order-2">
                    <h3 className="text-xl font-black">최근 기록</h3>
                    {storedFeedbackRecords.length === 0 && (
                      <div className="rounded-md bg-[#f8fafc] p-4 text-sm font-bold leading-6 text-[#64748b]">
                        선생님 리포트로 저장된 최근 기록이 아직 없습니다.
                      </div>
                    )}
                    {storedFeedbackRecords.map((feedbackRecord) => {
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
                          <p className="mt-2 line-clamp-3 text-sm font-semibold leading-6 text-[#334155]">
                            {markdownToPlainSummary(feedbackRecord.feedback)}
                          </p>
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
      {isRegistrationOpen && (
        <StudentRegistrationModal
          open={isRegistrationOpen}
          onClose={() => setIsRegistrationOpen(false)}
          onRegistered={handleRegisteredStudent}
          onStartMaterials={handleStartRegisteredStudentMaterials}
        />
      )}
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

            <div className="grid min-h-0 flex-1 gap-4 overflow-y-auto px-6 py-4 xl:grid-cols-[minmax(0,0.94fr)_minmax(390px,0.72fr)] xl:overflow-hidden">
              <section className="flex min-h-[420px] flex-col rounded-lg border border-[#d8dee8] bg-[#f1f5f9] p-3 xl:min-h-0">
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
                  className="relative mx-auto aspect-[4/3] min-h-[300px] w-full max-w-[720px] flex-1 overflow-hidden rounded-md bg-[#e7edf4] shadow-inner"
                >
                  <iframe
                    title={`학습 리포트 자료 스테이지 ${openReportStageStep}`}
                    src={`/student/stage?caseId=${encodeURIComponent(openReport.caseId)}&contentId=${encodeURIComponent(openReport.contentId)}&step=${openReportStageStep}&preview=1`}
                    className="absolute left-1/2 top-1/2 origin-center border-0"
                    style={{
                      width: studentPreviewViewport.width,
                      height: studentPreviewViewport.height,
                      transform: `translate(-50%, -50%) scale(${reportPreviewScale})`,
                    }}
                  />
                </div>
              </section>

              <aside className="min-h-0 space-y-3 xl:overflow-y-auto xl:pr-2">
                <div className="grid gap-2 sm:grid-cols-2 2xl:grid-cols-3">
                  <InfoBlock label="걸린 시간" value={`${openReport.durationMinutes}분`} />
                  <InfoBlock label="평균 응답" value={`${openReport.averageResponseSeconds}초`} />
                  <InfoBlock label="문제당 시간" value={`${openReport.secondsPerQuestion}초`} />
                  <InfoBlock label="시도 횟수" value={`${openReport.attemptCount}회`} />
                  <InfoBlock label="오답 횟수" value={`${openReport.wrongCount}회`} />
                  <InfoBlock label="정답률" value={`${openReport.accuracyRate}%`} />
                </div>

                <div className="rounded-lg border border-[#d9ebc9] bg-[#f4fbef] p-4">
                  <p className="text-sm font-bold text-[#16803c]">학생 회고</p>
                  <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">
                    {openReport.reflectionText ?? "아직 저장된 회고가 없습니다."}
                  </p>
                </div>

                <div className="rounded-lg bg-[#f8fafc] p-4">
                  <p className="text-sm font-bold text-[#64748b]">기록 요약</p>
                  <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">{openReport.note}</p>
                </div>

                <div className="rounded-lg border border-[#cbd5e1] bg-white p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-bold text-[#1f3a5f]">선생님 리포트</p>
                    {openReportTeacherFeedback && (
                      <span className="rounded-full bg-[#eef4fb] px-3 py-1 text-xs font-black text-[#1f3a5f]">
                        {openReportTeacherFeedback.savedAt}
                      </span>
                    )}
                  </div>
                  {openReportTeacherFeedback?.feedback ? (
                    <div className="mt-3">
                      <MarkdownReport markdown={openReportTeacherFeedback.feedback} />
                    </div>
                  ) : (
                    <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">
                      아직 선생님 리포트가 저장되지 않았습니다.
                    </p>
                  )}
                </div>
                <div className="rounded-lg border border-[#d9ebc9] bg-[#f4fbef] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-[#16803c]">재사용</p>
                      <p className="mt-1 text-sm font-semibold leading-6 text-[#334155]">
                        이 리포트의 수업을 학생 화면에 다시 적용합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleReuseReportContent(openReport)}
                      disabled={isOpenReportReusing || isOpenReportReused}
                      className="rounded-md bg-[#5dae6b] px-5 py-3 text-sm font-black text-white shadow-[0_10px_24px_rgba(93,174,107,0.22)] transition hover:bg-[#4d9f5d] disabled:cursor-not-allowed disabled:bg-[#c7d2c6]"
                    >
                      {isOpenReportReusing ? "적용 중" : isOpenReportReused ? "적용됨" : "학생 화면에 재사용"}
                    </button>
                  </div>
                  {reportReuseError && <p className="mt-2 text-sm font-bold text-[#b42318]">{reportReuseError}</p>}
                </div>
              </aside>
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
                {openReview.generatedAtLabel && (
                  <p className="mt-1 text-xs font-black text-[#94a3b8]">생성 {openReview.generatedAtLabel}</p>
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
                    className="absolute left-1/2 top-1/2 origin-center border-0"
                    style={{
                      width: studentPreviewViewport.width,
                      height: studentPreviewViewport.height,
                      transform: `translate(-50%, -50%) scale(${reviewPreviewScale})`,
                    }}
                  />
                </div>
              </section>
              <div className="min-h-0 space-y-4 overflow-y-auto pr-2">
                {openReviewSelectedStages.map((stage) => (
                    <section key={stage.step} className="rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-5">
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="rounded-full bg-[#1f3a5f] px-3 py-1 text-xs font-black text-white">
                            스테이지 {stage.step}
                          </span>
                          <h4 className="text-lg font-black text-[#172033]">{stage.title}</h4>
                        </div>
                        {!stage.isRealtimeStage && (
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

                            <p className="mt-4 text-xs font-black text-[#64748b]">
                              {stage.isRealtimeStage ? "발화 목표" : "문제"}
                            </p>
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

                          {stage.isRealtimeStage && (
                            <div className="rounded-md border border-[#d8e8d2] bg-[#f7fcf4] p-4">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <p className="text-xs font-black text-[#16803c]">발화 연습</p>
                                <span className="rounded-full bg-white px-3 py-1 text-xs font-black text-[#16803c]">
                                  {stage.realtimeMaxDurationSec ? `${stage.realtimeMaxDurationSec}초` : "실시간"}
                                  {` · 발화 ${realtimeSpeakingTargetTurns}회`}
                                </span>
                              </div>
                              <p className="mt-2 text-sm font-black leading-6 text-[#172033]">
                                {stage.realtimePracticeTitle ?? stage.title}
                              </p>
                              {stage.realtimeSituationText && (
                                <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">
                                  {stage.realtimeSituationText}
                                </p>
                              )}
                              {stage.realtimeOpeningLine && (
                                <div className="mt-3 rounded-md bg-white px-3 py-2">
                                  <p className="text-xs font-black text-[#64748b]">시작 멘트</p>
                                  <p className="mt-1 text-sm font-bold leading-6 text-[#334155]">
                                    {stage.realtimeOpeningLine}
                                  </p>
                                </div>
                              )}
                              {stage.realtimeRubric && stage.realtimeRubric.length > 0 && (
                                <div className="mt-3 rounded-md bg-white px-3 py-2">
                                  <p className="text-xs font-black text-[#64748b]">확인할 점</p>
                                  <div className="mt-2 flex flex-wrap gap-2">
                                    {stage.realtimeRubric.map((rubric) => (
                                      <span
                                        key={rubric}
                                        className="rounded-full border border-[#d9ebc9] bg-[#f4fbef] px-3 py-1 text-xs font-black text-[#16803c]"
                                      >
                                        {rubric}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {stage.realtimeAllowedFeedback && stage.realtimeAllowedFeedback.length > 0 && (
                                <div className="mt-3 rounded-md bg-white px-3 py-2">
                                  <p className="text-xs font-black text-[#64748b]">피드백 예시</p>
                                  <div className="mt-2 space-y-1">
                                    {stage.realtimeAllowedFeedback.map((feedback) => (
                                      <p key={feedback} className="text-sm font-semibold leading-6 text-[#334155]">
                                        {feedback}
                                      </p>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {!stage.isRealtimeStage && (
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
                                    key={`${stage.step}-${choiceIndex}`}
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
                          )}
                        </div>
                      </div>
                    </section>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap justify-end gap-3 border-t border-[#e5e9f0] px-6 py-4">
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
                    void handleSaveReviewEdits();
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
                disabled={reviewActionId === openReview.id}
              >
                {isReviewEditing ? "수정 저장" : "직접 수정"}
              </button>
              <button
                onClick={handleApproveReview}
                disabled={reviewActionId === openReview.id || openReviewNeedsMediaGeneration}
                className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
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
