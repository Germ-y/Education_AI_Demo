import type { ApiAdapterOptions } from "../adapter";
import { getApiAdapter, type ApiDataSource } from "../client";
import type { SchoolSearchRequest, StudentRegistrationRequest } from "../contracts";

export function searchSchools(
  params: SchoolSearchRequest,
  options?: ApiAdapterOptions & { source?: ApiDataSource },
) {
  return getApiAdapter(options?.source).searchSchools(params, options);
}

export function createTeacherStudent(
  payload: StudentRegistrationRequest,
  options?: ApiAdapterOptions & { source?: ApiDataSource },
) {
  return getApiAdapter(options?.source).createTeacherStudent(payload, options);
}
