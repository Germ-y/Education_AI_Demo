import { apiFetch } from "../api-fetch";
import type { ApiAdapterOptions } from "../adapter";
import type { ContentAttempt, StageSubmitRequest, StageSubmitResponse } from "../contracts";

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
