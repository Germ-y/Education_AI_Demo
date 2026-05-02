import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";

export function getTeacherStudents(options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getTeacherStudents(options);
}

export function getTeacherStudent(studentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getTeacherStudent(studentId, options);
}

export function getTeacherStudentReport(studentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getTeacherStudentReport(studentId, options);
}
