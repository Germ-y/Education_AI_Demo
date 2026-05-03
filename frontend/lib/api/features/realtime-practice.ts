import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import { apiFetch } from "../api-fetch";
import type { RealtimeSessionCompleteRequest, RealtimeSessionEventRequest, RealtimeSessionRequest } from "../contracts";

export function createRealtimeSession(
  contentId: string,
  stageId: string,
  payload: RealtimeSessionRequest,
  options?: ApiAdapterOptions & { source?: ApiDataSource },
) {
  return getApiAdapter(options?.source).createRealtimeSession(contentId, stageId, payload, options);
}

export function saveRealtimeSessionEvent(sessionId: string, payload: RealtimeSessionEventRequest, options?: ApiAdapterOptions) {
  return apiFetch<Record<string, unknown>>(`/api/student/realtime-sessions/${encodeURIComponent(sessionId)}/events`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}

export function completeRealtimeSession(sessionId: string, payload: RealtimeSessionCompleteRequest, options?: ApiAdapterOptions) {
  return apiFetch<Record<string, unknown>>(`/api/student/realtime-sessions/${encodeURIComponent(sessionId)}/complete`, {
    method: "POST",
    body: payload,
    token: options?.token,
  });
}
