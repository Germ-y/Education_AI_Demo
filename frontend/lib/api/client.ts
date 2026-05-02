import type { ApiAdapter } from "./adapter";
import { backendAdapter } from "./backend-adapter";

export type ApiDataSource = "backend";

export function getApiAdapter(source?: ApiDataSource): ApiAdapter {
  void source;
  return backendAdapter;
}
