import { apiFetch } from "../api-fetch";
import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { ContentApprovalRequest, ContentRejectRequest, ContentReviewUpdateRequest, MissionContent } from "../contracts";

export function getReviewableContent(contentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getReviewableContent(contentId, options);
}

export function approveContent(
  contentId: string,
  payload: ContentApprovalRequest,
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
  payload: ContentRejectRequest,
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
  payload: ContentReviewUpdateRequest,
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
