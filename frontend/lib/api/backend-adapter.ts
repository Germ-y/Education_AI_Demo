import { apiFetch } from "./api-fetch";
import type { ApiAdapter } from "./adapter";
import type {
  AssetPackageGenerationResponse,
  ContentGenerationResponse,
  ContextMe,
  DemoLoginResponse,
  MissionContent,
  OrchestratorRunResponse,
  PublicContextBundle,
  RealtimeSessionResponse,
  ReviewableContent,
  StudentAccessResponse,
  StudentCaseFile,
  StudentListItem,
  StudentMissionSummary,
} from "./contracts";

export const backendAdapter: ApiAdapter = {
  demoLogin: (payload) => apiFetch<DemoLoginResponse>("/api/auth/demo-login", { method: "POST", body: payload }),

  studentAccess: (payload) =>
    apiFetch<StudentAccessResponse>("/api/auth/student-access", { method: "POST", body: payload }),

  getContextMe: (options) => apiFetch<ContextMe>("/api/context/me", { token: options?.token }),

  getTeacherStudents: (options) => apiFetch<StudentListItem[]>("/api/teacher/students", { token: options?.token }),

  getTeacherStudent: (studentId, options) =>
    apiFetch<StudentCaseFile>(`/api/teacher/students/${encodeURIComponent(studentId)}`, { token: options?.token }),

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
