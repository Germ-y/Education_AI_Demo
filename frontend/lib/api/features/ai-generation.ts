import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { AgentRunRequest, ContentGenerationRequest } from "../contracts";

export function getAgentRun(agentRunId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getAgentRun(agentRunId, options);
}

export function listAgentRuns(
  params: { studentId?: string; caseId?: string; status?: "running" | "succeeded" | "failed" },
  options?: ApiAdapterOptions & { source?: ApiDataSource },
) {
  return getApiAdapter(options?.source).listAgentRuns(params, options);
}

export function createAgentRun(payload: AgentRunRequest, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).createAgentRun(payload, options);
}

export function createContentGeneration(payload: ContentGenerationRequest, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).createContentGeneration(payload, options);
}

export function generateContentAssetPackage(contentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).generateContentAssetPackage(contentId, options);
}

export function createContentAssetGenerationJob(contentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).createContentAssetGenerationJob(contentId, options);
}

export function getContentAssetGenerationJob(
  contentId: string,
  jobId: string,
  options?: ApiAdapterOptions & { source?: ApiDataSource },
) {
  return getApiAdapter(options?.source).getContentAssetGenerationJob(contentId, jobId, options);
}
