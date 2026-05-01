import type { FastifyInstance } from "fastify";
import type { DemoStore } from "../../data/store.js";
import { MemoryCardPatchSchema } from "../../domain/schemas.js";
import { type AuthenticatedRequest, requirePrincipal } from "../auth.js";
import { fail, handleRouteError, ok } from "../response.js";

export async function registerTeacherRoutes(app: FastifyInstance, store: DemoStore) {
  app.get(
    "/api/teacher/students",
    { preHandler: requirePrincipal(store, ["teacher", "center_admin", "content_reviewer"]) },
    async (request) => {
      const principal = (request as AuthenticatedRequest).principal;
      const query = request.query as { studentType?: string; q?: string };
      const students = store.listTeacherStudents({
        studentType: query.studentType,
        q: query.q,
        teacherId: principal.role === "teacher" ? principal.id : undefined,
      });
      return ok(request, students);
    },
  );

  app.get(
    "/api/teacher/students/:studentId",
    { preHandler: requirePrincipal(store, ["teacher", "center_admin", "content_reviewer"]) },
    async (request, reply) => {
      const params = request.params as { studentId: string };
      const caseFile = store.getStudentCaseFile(params.studentId);
      if (!caseFile) {
        return fail(reply, 404, "STUDENT_NOT_FOUND", "학생 케이스를 찾을 수 없습니다.");
      }
      return ok(request, caseFile);
    },
  );

  app.patch(
    "/api/teacher/students/:studentId/memory-card",
    { preHandler: requirePrincipal(store, ["teacher", "center_admin"]) },
    async (request, reply) => {
      try {
        const params = request.params as { studentId: string };
        const body = MemoryCardPatchSchema.parse(request.body);
        const updated = store.patchMemoryCard(params.studentId, body);
        if (!updated) {
          return fail(reply, 404, "MEMORY_CARD_NOT_FOUND", "활성 메모리 카드를 찾을 수 없습니다.");
        }
        return ok(request, updated);
      } catch (error) {
        return handleRouteError(reply, error);
      }
    },
  );
}
