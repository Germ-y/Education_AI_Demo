import type { ApiAdapter } from "./adapter";
import { backendAdapter } from "./backend-adapter";
import { devAdapter } from "./dev-adapter";

export type ApiDataSource = "dev" | "backend";

export function getApiAdapter(source: ApiDataSource = getDefaultDataSource()): ApiAdapter {
  return source === "backend" ? backendAdapter : devAdapter;
}

function getDefaultDataSource(): ApiDataSource {
  return process.env.NEXT_PUBLIC_EDUYJ_API_SOURCE === "backend" ? "backend" : "dev";
}
