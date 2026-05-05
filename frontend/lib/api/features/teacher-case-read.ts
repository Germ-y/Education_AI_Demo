import type { ApiAdapterOptions } from "../adapter";
import { apiFetch } from "../api-fetch";
import { getApiAdapter, type ApiDataSource } from "../client";
import type {
  CaseNote,
  CaseNoteCreate,
  MemoryCard,
  StudentContextBrief,
  SupportProfileConfirmRequest,
  SupportProfileDraftResponse,
  TeacherReport,
  TeacherReportCreateRequest,
} from "../contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:4000";

export function getTeacherStudents(options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getTeacherStudents(options);
}

export function getTeacherStudent(studentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getTeacherStudent(studentId, options);
}

export function getTeacherStudentReport(studentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getTeacherStudentReport(studentId, options);
}

export function createTeacherStudentNote(
  studentId: string,
  payload: CaseNoteCreate,
  options?: ApiAdapterOptions,
) {
  return apiFetch<CaseNote>(`/api/teacher/students/${encodeURIComponent(studentId)}/notes`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}

export function applyReviewSummaryToMemory(reviewId: string, options?: ApiAdapterOptions) {
  return apiFetch<MemoryCard>(`/api/review-summaries/${encodeURIComponent(reviewId)}/apply-to-memory`, {
    method: "POST",
    token: options?.token,
  });
}

export function createSupportProfileDraft(studentId: string, options?: ApiAdapterOptions) {
  return apiFetch<SupportProfileDraftResponse>(`/api/teacher/students/${encodeURIComponent(studentId)}/support-profile-drafts`, {
    method: "POST",
    token: options?.token,
  });
}

export function confirmSupportProfile(
  studentId: string,
  payload: SupportProfileConfirmRequest,
  options?: ApiAdapterOptions,
) {
  return apiFetch(`/api/teacher/students/${encodeURIComponent(studentId)}/support-profiles`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}

export function getStudentContextBrief(studentId: string, options?: ApiAdapterOptions) {
  return apiFetch<StudentContextBrief>(`/api/teacher/students/${encodeURIComponent(studentId)}/context-brief`, {
    token: options?.token,
  });
}

export function refreshStudentContextBrief(studentId: string, options?: ApiAdapterOptions) {
  return apiFetch<StudentContextBrief>(`/api/teacher/students/${encodeURIComponent(studentId)}/context-brief/refresh`, {
    method: "POST",
    token: options?.token,
  });
}

export async function createTeacherReportDraft(reviewId: string, options?: ApiAdapterOptions) {
  const response = await fetch(`${API_BASE_URL}/api/review-summaries/${encodeURIComponent(reviewId)}/report-drafts/stream`, {
    method: "POST",
    headers: options?.token ? { Authorization: `Bearer ${options.token}` } : undefined,
  });
  if (!response.ok) throw new Error("AI 리포트 초안을 만들지 못했습니다.");
  const raw = await response.text();
  let bodyMarkdown = "";
  let draftId = "";
  let memoryCandidates: string[] = [];
  raw.split("\n\n").forEach((block) => {
    const eventLine = block.split("\n").find((line) => line.startsWith("event: "));
    const dataLine = block.split("\n").find((line) => line.startsWith("data: "));
    if (!eventLine || !dataLine) return;
    const event = eventLine.replace("event: ", "");
    const data = JSON.parse(dataLine.replace("data: ", "")) as Record<string, unknown>;
    if (event === "draft_delta" && typeof data.text === "string") bodyMarkdown += data.text;
    if (event === "draft_metadata" && Array.isArray(data.memoryCandidates)) {
      memoryCandidates = data.memoryCandidates.filter((item): item is string => typeof item === "string");
    }
    if (event === "done" && typeof data.draftId === "string") draftId = data.draftId;
  });
  return { draftId, bodyMarkdown, memoryCandidates };
}

export function saveTeacherReport(payload: TeacherReportCreateRequest, options?: ApiAdapterOptions) {
  return apiFetch<TeacherReport>("/api/teacher-reports", {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}
