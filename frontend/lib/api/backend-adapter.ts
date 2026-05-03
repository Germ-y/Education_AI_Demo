import { apiFetch } from "./api-fetch";
import type { ApiAdapter } from "./adapter";
import type {
  AssetPackageGenerationResponse,
  AgentRun,
  ContentGenerationResponse,
  ContextMe,
  DemoLoginResponse,
  MissionContent,
  OrchestratorRunResponse,
  PublicContextBundle,
  RealtimeSessionResponse,
  ReviewableContent,
  SeedContext,
  StudentAccessResponse,
  StudentCaseFile,
  StudentListItem,
  StudentMissionSummary,
  StudentReport,
} from "./contracts";

type BackendSeedContext = {
  mode: "demo_seed";
  organization: SeedContext["organization"];
  teacher: SeedContext["teacher"];
  students: Array<StudentListItem & { schoolCode?: string | null; accessCode?: string | null }>;
  assignments: Array<{
    teacherId: string;
    studentId: string;
    caseId: string;
    caseStatus: "open" | "paused" | "closed";
    dashboardStage?: "initial_review" | "material_generation" | "material_review" | "learning" | "feedback";
    supportStrategy?: string | null;
  }>;
  missionMappings: Array<{
    contentId: string;
    studentId: string;
    caseId: string;
    status?: string;
    totalSteps?: number;
    updatedAt?: string | null;
    latestAttemptStatus?: "in_progress" | "completed" | "abandoned" | null;
    latestAttemptCurrentStep?: 1 | 2 | 3 | 4 | null;
    latestAttemptCompletedAt?: string | null;
    isCompleted?: boolean;
  }>;
};

export const backendAdapter: ApiAdapter = {
  demoLogin: (payload) => apiFetch<DemoLoginResponse>("/api/auth/demo-login", { method: "POST", body: payload }),

  studentAccess: (payload) =>
    apiFetch<StudentAccessResponse>("/api/auth/student-access", { method: "POST", body: payload }),

  getContextSeed: async (options) => normalizeSeedContext(await apiFetch<BackendSeedContext>("/api/context/seed", { token: options?.token })),

  getContextMe: (options) => apiFetch<ContextMe>("/api/context/me", { token: options?.token }),

  getTeacherStudents: (options) => apiFetch<StudentListItem[]>("/api/teacher/students", { token: options?.token }),

  getTeacherStudent: (studentId, options) =>
    apiFetch<StudentCaseFile>(`/api/teacher/students/${encodeURIComponent(studentId)}`, { token: options?.token }),

  getTeacherStudentReport: (studentId, options) =>
    apiFetch<StudentReport>(`/api/teacher/students/${encodeURIComponent(studentId)}/report`, { token: options?.token }),

  getSchoolContext: (schoolId, options) =>
    apiFetch<PublicContextBundle>(`/api/public-data/schools/${encodeURIComponent(schoolId)}/context`, { token: options?.token }),

  getTodayStudentMissions: (options) => apiFetch<StudentMissionSummary[]>("/api/student/missions/today", { token: options?.token }),

  getStudentMission: (contentId, options) =>
    apiFetch<MissionContent>(`/api/student/missions/${encodeURIComponent(contentId)}`, { token: options?.token }),

  getReviewableContent: (contentId, options) =>
    apiFetch<ReviewableContent>(`/api/contents/${encodeURIComponent(contentId)}`, { token: options?.token }),

  createRealtimeSession: (contentId, stageId, payload, options) =>
    apiFetch<RealtimeSessionResponse>(
      `/api/student/missions/${encodeURIComponent(contentId)}/stages/${encodeURIComponent(stageId)}/realtime-session`,
      { method: "POST", body: payload, token: options?.token },
    ),

  getAgentRun: (agentRunId, options) =>
    apiFetch<AgentRun>(`/api/ai/agent-runs/${encodeURIComponent(agentRunId)}`, { token: options?.token }),

  listAgentRuns: (params, options) => {
    const searchParams = new URLSearchParams();
    if (params.studentId) searchParams.set("student_id", params.studentId);
    if (params.caseId) searchParams.set("case_id", params.caseId);
    if (params.status) searchParams.set("status", params.status);
    const query = searchParams.toString();
    return apiFetch<AgentRun[]>(`/api/ai/agent-runs${query ? `?${query}` : ""}`, { token: options?.token });
  },

  createAgentRun: (payload, options) =>
    apiFetch<OrchestratorRunResponse>("/api/ai/orchestrator-runs", { method: "POST", body: payload, token: options?.token }),

  createContentGeneration: (payload, options) =>
    apiFetch<ContentGenerationResponse>("/api/ai/content-generations", { method: "POST", body: payload, token: options?.token }),

  generateContentAssetPackage: (contentId, options) =>
    apiFetch<AssetPackageGenerationResponse>(`/api/contents/${encodeURIComponent(contentId)}/assets/generate-package`, {
      method: "POST",
      token: options?.token,
    }),
};

function normalizeSeedContext(seed: BackendSeedContext): SeedContext {
  return {
    organization: seed.organization,
    teacher: seed.teacher,
    students: seed.students.map((student) => ({
      id: student.studentId,
      organizationId: seed.organization.id,
      externalKey: student.studentId,
      displayName: student.displayName,
      grade: student.grade,
      gradeLabel: student.gradeLabel,
      schoolCode: student.schoolCode,
      studentType: student.studentType,
      studentTypeLabel: student.studentTypeLabel,
      trackLabel: student.trackLabel,
      primaryNeed: student.primaryNeed,
      profileJson: {},
      attendanceRate: student.attendanceRate,
      attendanceLabel: student.attendanceLabel,
      accessCode: student.accessCode,
      strengths: student.strengths ?? [],
      weaknesses: student.weaknesses ?? [],
      status: "active",
    })),
    schools: [],
    cases: seed.assignments.map((assignment) => ({
      id: assignment.caseId,
      studentId: assignment.studentId,
      ownerTeacherId: assignment.teacherId,
      caseStatus: assignment.caseStatus,
      currentGoal: seed.students.find((student) => student.studentId === assignment.studentId)?.primaryNeed ?? "",
      dashboardStage: assignment.dashboardStage,
      supportStrategy: assignment.supportStrategy,
      openedAt: "",
    })),
    contents: [],
    mappings: seed.missionMappings.map((mapping) => ({
      studentId: mapping.studentId,
      caseId: mapping.caseId,
      contentId: mapping.contentId,
      status: mapping.status,
      updatedAt: mapping.updatedAt,
      latestAttemptStatus: mapping.latestAttemptStatus,
      latestAttemptCurrentStep: mapping.latestAttemptCurrentStep,
      latestAttemptCompletedAt: mapping.latestAttemptCompletedAt,
      isCompleted: mapping.isCompleted,
    })),
  };
}
