import type { FastifyReply, FastifyRequest } from "fastify";
import { ZodError } from "zod";

export function ok<T>(request: FastifyRequest, data: T) {
  return {
    data,
    meta: {
      requestId: request.id,
    },
  };
}

export function fail(reply: FastifyReply, statusCode: number, code: string, message: string, details?: unknown) {
  return reply.status(statusCode).send({
    error: {
      code,
      message,
      details: details ?? {},
    },
  });
}

export function handleRouteError(reply: FastifyReply, error: unknown) {
  if (error instanceof ZodError) {
    return fail(reply, 400, "VALIDATION_ERROR", "요청 형식이 올바르지 않습니다.", error.flatten());
  }
  throw error;
}
