import { apiFetch } from "../api-fetch";
import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { MissionContent } from "../contracts";

export function getReviewableContent(contentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getReviewableContent(contentId, options);
}

export function approveContent(
  contentId: string,
  payload: { approvedStageIds: string[]; approvedAssetIds: string[]; reviewNote?: string | null },
  options?: ApiAdapterOptions,
) {
  return apiFetch<MissionContent>(`/api/contents/${encodeURIComponent(contentId)}/approve`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}

export function rejectContent(
  contentId: string,
  payload: { reason: string; requestedChanges?: string[] },
  options?: ApiAdapterOptions,
) {
  return apiFetch<MissionContent>(`/api/contents/${encodeURIComponent(contentId)}/reject`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}

export function updateContentReview(
  contentId: string,
  payload: {
    stages: Array<{
      stageId: string;
      studentInstruction?: string;
      question?: string;
      choices?: string[];
      realtimeStudentGoal?: string;
    }>;
  },
  options?: ApiAdapterOptions,
) {
  return apiFetch<MissionContent>(`/api/contents/${encodeURIComponent(contentId)}/review`, {
    method: "PATCH",
    body: payload,
    token: options?.token,
  });
}

export function publishContent(contentId: string, options?: ApiAdapterOptions) {
  return apiFetch<MissionContent>(`/api/contents/${encodeURIComponent(contentId)}/publish`, {
    method: "POST",
    token: options?.token,
  });
}
