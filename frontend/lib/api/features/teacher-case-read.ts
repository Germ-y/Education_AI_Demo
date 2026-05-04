import type { ApiAdapterOptions } from "../adapter";
import { apiFetch } from "../api-fetch";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { CaseNote, CaseNoteCreate } from "../contracts";

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
