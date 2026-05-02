import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { AgentRunRequest } from "../contracts";

export function createAgentRun(payload: AgentRunRequest, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).createAgentRun(payload, options);
}
