import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { AgentRunRequest, ContentGenerationRequest } from "../contracts";

export function createAgentRun(payload: AgentRunRequest, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).createAgentRun(payload, options);
}

export function createContentGeneration(payload: ContentGenerationRequest, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).createContentGeneration(payload, options);
}

export function generateContentAssetPackage(contentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).generateContentAssetPackage(contentId, options);
}
