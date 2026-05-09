import type { ApiAdapterOptions } from "../adapter";
import { apiFetch } from "../api-fetch";
import { getApiAdapter, type ApiDataSource } from "../client";
import type {
  CaseNote,
  CaseNoteCreate,
  MemoryCard,
  SchoolWeeklyTimetable,
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

export function getSchoolWeeklyTimetable(
  schoolCode: string,
  params: { weekStart?: string; grade: string; className: string; syncIfMissing?: boolean },
  options?: ApiAdapterOptions,
) {
  const searchParams = new URLSearchParams();
  if (params.weekStart) searchParams.set("weekStart", params.weekStart);
  searchParams.set("grade", params.grade);
  searchParams.set("className", params.className);
  if (params.syncIfMissing !== undefined) searchParams.set("syncIfMissing", String(params.syncIfMissing));
  return apiFetch<SchoolWeeklyTimetable>(
    `/api/public-data/schools/${encodeURIComponent(schoolCode)}/weekly-timetable?${searchParams.toString()}`,
    { token: options?.token },
  );
}

export async function createTeacherReportDraft(
  reviewId: string,
  options?: ApiAdapterOptions & {
    onDelta?: (text: string) => void;
    teacherObservation?: string;
  },
) {
  const response = await fetch(`${API_BASE_URL}/api/review-summaries/${encodeURIComponent(reviewId)}/report-drafts/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(options?.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: JSON.stringify({ teacherObservation: options?.teacherObservation ?? "" }),
  });
  if (!response.ok) throw new Error("리포트 초안을 만들지 못했습니다.");
  let bodyMarkdown = "";
  let draftId = "";
  let memoryCandidates: string[] = [];
  let streamError: string | null = null;

  const handleBlock = (block: string) => {
    const eventLine = block.split("\n").find((line) => line.startsWith("event: "));
    const dataLine = block.split("\n").find((line) => line.startsWith("data: "));
    if (!eventLine || !dataLine) return;
    const event = eventLine.replace("event: ", "");
    const data = JSON.parse(dataLine.replace("data: ", "")) as Record<string, unknown>;
    if (event === "draft_delta" && typeof data.text === "string") {
      bodyMarkdown += data.text;
      options?.onDelta?.(data.text);
    }
    if (event === "draft_metadata" && Array.isArray(data.memoryCandidates)) {
      memoryCandidates = data.memoryCandidates.filter((item): item is string => typeof item === "string");
    }
    if (event === "error") {
      streamError = typeof data.message === "string" ? data.message : "리포트 초안 생성 중 오류가 발생했습니다.";
    }
    if (event === "done" && typeof data.draftId === "string") draftId = data.draftId;
  };

  if (!response.body) {
    const raw = await response.text();
    raw.split("\n\n").forEach(handleBlock);
    if (streamError) throw new Error(streamError);
    return { draftId, bodyMarkdown, memoryCandidates };
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    blocks.forEach(handleBlock);
  }
  buffer += decoder.decode();
  if (buffer.trim()) handleBlock(buffer);
  if (streamError) throw new Error(streamError);
  return { draftId, bodyMarkdown, memoryCandidates };
}

export function saveTeacherReport(payload: TeacherReportCreateRequest, options?: ApiAdapterOptions) {
  return apiFetch<TeacherReport>("/api/teacher-reports", {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}
