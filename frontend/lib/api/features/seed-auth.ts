import { getApiAdapter, type ApiDataSource } from "../client";
import type { DemoLoginRequest, StudentAccessRequest } from "../contracts";

export function demoLogin(payload: DemoLoginRequest, source?: ApiDataSource) {
  return getApiAdapter(source).demoLogin(payload);
}

export function studentAccess(payload: StudentAccessRequest, source?: ApiDataSource) {
  return getApiAdapter(source).studentAccess(payload);
}
