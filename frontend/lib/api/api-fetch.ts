import type { ApiEnvelope, ApiError, FastApiError } from "./contracts";

export class ApiFetchError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(status: number, error: ApiError["error"]) {
    super(error.message);
    this.name = "ApiFetchError";
    this.code = error.code;
    this.status = status;
    this.details = error.details;
  }
}

export type ApiFetchOptions = Omit<RequestInit, "body"> & {
  baseUrl?: string;
  token?: string;
  body?: unknown;
};

const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:4000";

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { baseUrl = DEFAULT_API_BASE_URL, token, headers, body, ...init } = options;
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const envelope = (await parseJson(response)) as ApiEnvelope<T>;

  if ("error" in envelope) {
    throw new ApiFetchError(response.status, envelope.error);
  }

  if ("detail" in envelope) {
    throw new ApiFetchError(response.status, normalizeFastApiError(envelope));
  }

  return envelope.data;
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return response.ok ? { data: undefined, meta: { requestId: "" } } : { detail: response.statusText };
  }

  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

function normalizeFastApiError(envelope: FastApiError): ApiError["error"] {
  if (typeof envelope.detail === "string") {
    return {
      code: "HTTP_ERROR",
      message: envelope.detail,
      details: {},
    };
  }

  return {
    code: envelope.detail.code ?? "HTTP_ERROR",
    message: envelope.detail.message ?? "요청을 처리하지 못했습니다.",
    details: envelope.detail.details ?? {},
  };
}
