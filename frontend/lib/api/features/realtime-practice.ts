import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { RealtimeSessionRequest } from "../contracts";

export function createRealtimeSession(
  contentId: string,
  stageId: string,
  payload: RealtimeSessionRequest,
  options?: ApiAdapterOptions & { source?: ApiDataSource },
) {
  return getApiAdapter(options?.source).createRealtimeSession(contentId, stageId, payload, options);
}
