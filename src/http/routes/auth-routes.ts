import type { FastifyInstance } from "fastify";
import type { DemoStore } from "../../data/store.js";
import { DemoLoginRequestSchema, StudentAccessRequestSchema } from "../../domain/schemas.js";
import { fail, handleRouteError, ok } from "../response.js";

export async function registerAuthRoutes(app: FastifyInstance, store: DemoStore) {
  app.post("/api/auth/demo-login", async (request, reply) => {
    try {
      const body = DemoLoginRequestSchema.parse(request.body);
      const session = store.createUserSession(body.role, body.email);
      if (!session) {
        return fail(reply, 404, "DEMO_USER_NOT_FOUND", "데모 사용자를 찾을 수 없습니다.");
      }
      const user = store.db.users.find((candidate) => candidate.id === session.id);
      return ok(request, {
        user,
        session: {
          accessToken: session.token,
          expiresAt: session.expiresAt,
        },
      });
    } catch (error) {
      return handleRouteError(reply, error);
    }
  });

  app.post("/api/auth/student-access", async (request, reply) => {
    try {
      const body = StudentAccessRequestSchema.parse(request.body);
      const session = store.createStudentSession(body.accessCode);
      if (!session || !session.studentId) {
        return fail(reply, 404, "STUDENT_ACCESS_NOT_FOUND", "학생 접근 코드를 확인해 주세요.");
      }
      const student = store.db.students.find((candidate) => candidate.id === session.studentId);
      return ok(request, {
        student,
        session: {
          accessToken: session.token,
          expiresAt: session.expiresAt,
        },
      });
    } catch (error) {
      return handleRouteError(reply, error);
    }
  });
}
