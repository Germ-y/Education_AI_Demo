import { apiFetch } from "../api-fetch";
import type { ApiAdapterOptions } from "../adapter";
import type {
  ContentAttempt,
  ReflectionRequest,
  ReflectionResponse,
  StageSubmitRequest,
  StageSubmitResponse,
  StudentActivityEventRequest,
} from "../contracts";

export function startStudentMission(contentId: string, options?: ApiAdapterOptions) {
  return apiFetch<ContentAttempt>(`/api/student/missions/${encodeURIComponent(contentId)}/start`, {
    method: "POST",
    token: options?.token,
  });
}

export function submitStudentMissionStage(
  contentId: string,
  stageId: string,
  payload: StageSubmitRequest,
  options?: ApiAdapterOptions,
) {
  return apiFetch<StageSubmitResponse>(
    `/api/student/missions/${encodeURIComponent(contentId)}/stages/${encodeURIComponent(stageId)}/submit`,
    { method: "POST", body: payload, token: options?.token },
  );
}

export function saveStudentMissionEvent(
  contentId: string,
  payload: StudentActivityEventRequest,
  options?: ApiAdapterOptions,
) {
  return apiFetch<Record<string, unknown>>(`/api/student/missions/${encodeURIComponent(contentId)}/events`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}

export function saveStudentMissionReflection(
  contentId: string,
  payload: ReflectionRequest,
  options?: ApiAdapterOptions,
) {
  return apiFetch<ReflectionResponse>(`/api/student/missions/${encodeURIComponent(contentId)}/post-practice-reflection`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}

export function completeStudentMission(contentId: string, attemptId: string, options?: ApiAdapterOptions) {
  return apiFetch<ContentAttempt>(`/api/student/missions/${encodeURIComponent(contentId)}/complete`, {
    method: "POST",
    body: { attemptId },
    token: options?.token,
  });
}
