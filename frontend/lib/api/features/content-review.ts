import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";

export function getReviewableContent(contentId: string, options?: ApiAdapterOptions & { source?: ApiDataSource }) {
  return getApiAdapter(options?.source).getReviewableContent(contentId, options);
}
