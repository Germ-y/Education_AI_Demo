import type { FastifyReply, FastifyRequest } from "fastify";
import type { DemoStore, SessionPrincipal } from "../data/store.js";
import { fail } from "./response.js";

export type AuthenticatedRequest = FastifyRequest & {
  principal: SessionPrincipal;
};

export function getBearerToken(request: FastifyRequest) {
  const header = request.headers.authorization;
  if (!header || Array.isArray(header)) return undefined;
  const [scheme, token] = header.split(" ");
  if (scheme !== "Bearer" || !token) return undefined;
  return token;
}

export function requirePrincipal(store: DemoStore, allowedRoles?: string[]) {
  return async (request: FastifyRequest, reply: FastifyReply) => {
    const principal = store.getSession(getBearerToken(request));
    if (!principal) {
      return fail(reply, 401, "UNAUTHORIZED", "로그인이 필요합니다.");
    }
    if (allowedRoles && !allowedRoles.includes(principal.role)) {
      return fail(reply, 403, "FORBIDDEN", "이 API를 사용할 권한이 없습니다.");
    }
    (request as AuthenticatedRequest).principal = principal;
  };
}
