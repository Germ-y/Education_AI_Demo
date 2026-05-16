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
  retry?: number;
};

const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:4000";
const DEFAULT_SAFE_REQUEST_RETRY_COUNT = 2;
const RETRY_DELAY_MS = 350;

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { baseUrl = DEFAULT_API_BASE_URL, token, headers, body, retry, ...init } = options;
  const method = init.method?.toUpperCase() ?? "GET";
  const retryCount = retry ?? (method === "GET" || method === "HEAD" ? DEFAULT_SAFE_REQUEST_RETRY_COUNT : 0);
  const response = await fetchWithRetry(`${baseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  }, retryCount);
  const envelope = (await parseJson(response)) as ApiEnvelope<T>;

  if ("error" in envelope) {
    throw new ApiFetchError(response.status, envelope.error);
  }

  if ("detail" in envelope) {
    throw new ApiFetchError(response.status, normalizeFastApiError(envelope));
  }

  return envelope.data;
}

async function fetchWithRetry(input: RequestInfo | URL, init: RequestInit, retryCount: number): Promise<Response> {
  let lastError: unknown;

  for (let attempt = 0; attempt <= retryCount; attempt += 1) {
    try {
      return await fetch(input, init);
    } catch (error) {
      lastError = error;
      if (attempt === retryCount || isAbortError(error)) break;
      await wait(RETRY_DELAY_MS * (attempt + 1));
    }
  }

  throw lastError;
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
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
