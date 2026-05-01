import type { FastifyInstance } from "fastify";
import type { DemoStore } from "../../data/store.js";
import { ReflectionRequestSchema, StageSubmitRequestSchema } from "../../domain/schemas.js";
import { type AuthenticatedRequest, requirePrincipal } from "../auth.js";
import { fail, handleRouteError, ok } from "../response.js";

export async function registerStudentRoutes(app: FastifyInstance, store: DemoStore) {
  app.get(
    "/api/student/missions/today",
    { preHandler: requirePrincipal(store, ["student"]) },
    async (request) => {
      const principal = (request as AuthenticatedRequest).principal;
      const missions = store.listPublishedMissionsForStudent(principal.studentId!);
      return ok(
        request,
        missions.map((mission) => ({
          contentId: mission.id,
          title: mission.title,
          contentType: mission.contentType,
          totalSteps: mission.totalSteps,
          heroImageUrl: mission.assets.find((asset) => asset.assetRole === "hero")?.previewUrl,
          status: mission.status,
        })),
      );
    },
  );

  app.get(
    "/api/student/missions/:contentId",
    { preHandler: requirePrincipal(store, ["student"]) },
    async (request, reply) => {
      const principal = (request as AuthenticatedRequest).principal;
      const params = request.params as { contentId: string };
      const mission = store.getPublishedMissionForStudent(principal.studentId!, params.contentId);
      if (!mission) {
        return fail(reply, 404, "MISSION_NOT_FOUND", "배포된 미션을 찾을 수 없습니다.");
      }
      return ok(request, mission);
    },
  );

  app.post(
    "/api/student/missions/:contentId/start",
    { preHandler: requirePrincipal(store, ["student"]) },
    async (request, reply) => {
      const principal = (request as AuthenticatedRequest).principal;
      const params = request.params as { contentId: string };
      const mission = store.getPublishedMissionForStudent(principal.studentId!, params.contentId);
      if (!mission) {
        return fail(reply, 404, "MISSION_NOT_FOUND", "배포된 미션을 찾을 수 없습니다.");
      }
      return ok(request, store.createAttempt(principal.studentId!, mission.id));
    },
  );

  app.post(
    "/api/student/missions/:contentId/stages/:stageId/submit",
    { preHandler: requirePrincipal(store, ["student"]) },
    async (request, reply) => {
      try {
        const principal = (request as AuthenticatedRequest).principal;
        const params = request.params as { contentId: string; stageId: string };
        const body = StageSubmitRequestSchema.parse(request.body);
        const result = store.submitStage({
          studentId: principal.studentId!,
          contentId: params.contentId,
          stageId: params.stageId,
          attemptId: body.attemptId,
          answer: body.answer,
        });
        if (!result) {
          return fail(reply, 404, "STAGE_NOT_FOUND", "제출할 단계를 찾을 수 없습니다.");
        }
        if (result.isRealtimeStage) {
          return fail(reply, 400, "REALTIME_STAGE_SUBMIT_BLOCKED", "4단계는 realtime-session API를 사용해야 합니다.");
        }
        return ok(request, result);
      } catch (error) {
        return handleRouteError(reply, error);
      }
    },
  );

  app.post(
    "/api/student/missions/:contentId/stages/:stageId/realtime-session",
    { preHandler: requirePrincipal(store, ["student"]) },
    async (request, reply) => {
      try {
        const principal = (request as AuthenticatedRequest).principal;
        const params = request.params as { contentId: string; stageId: string };
        const body = StageSubmitRequestSchema.pick({ attemptId: true }).parse(request.body);
        const session = store.createRealtimeSession({
          studentId: principal.studentId!,
          contentId: params.contentId,
          stageId: params.stageId,
          attemptId: body.attemptId,
        });
        if (!session) {
          return fail(reply, 400, "REALTIME_SESSION_NOT_ALLOWED", "승인된 4단계 realtime 스펙이 필요합니다.");
        }
        const spec = session.specSnapshotJson as {
          practiceTitle?: string;
          imageAssetId?: string;
          openingLine?: string;
          maxTurns?: number;
          maxDurationSec?: number;
        };
        const mission = store.getPublishedMissionForStudent(principal.studentId!, params.contentId)!;
        const imageAsset = mission.assets.find((asset) => asset.id === spec.imageAssetId);
        return ok(request, {
          sessionId: session.id,
          provider: session.provider,
          model: session.model,
          clientSecret: process.env.OPENAI_API_KEY ? `server-issued-${session.id}` : `demo-client-secret-${session.id}`,
          expiresAt: new Date(Date.now() + 1000 * 60 * 5).toISOString(),
          webrtcUrl: "https://api.openai.com/v1/realtime/calls",
          practiceSpec: {
            practiceTitle: spec.practiceTitle,
            imageAssetUrl: imageAsset?.previewUrl,
            openingLine: spec.openingLine,
            maxTurns: spec.maxTurns,
            maxDurationSec: spec.maxDurationSec,
          },
        });
      } catch (error) {
        return handleRouteError(reply, error);
      }
    },
  );

  app.post(
    "/api/student/missions/:contentId/post-practice-reflection",
    { preHandler: requirePrincipal(store, ["student"]) },
    async (request, reply) => {
      try {
        const principal = (request as AuthenticatedRequest).principal;
        const params = request.params as { contentId: string };
        const body = ReflectionRequestSchema.parse(request.body);
        const saved = store.saveReflection({
          studentId: principal.studentId!,
          contentId: params.contentId,
          attemptId: body.attemptId,
          reflectionChoice: body.reflectionChoice,
          shortText: body.shortText,
        });
        if (!saved) {
          return fail(reply, 404, "ATTEMPT_NOT_FOUND", "진행 중인 시도를 찾을 수 없습니다.");
        }
        return ok(request, saved);
      } catch (error) {
        return handleRouteError(reply, error);
      }
    },
  );

  app.post(
    "/api/student/missions/:contentId/complete",
    { preHandler: requirePrincipal(store, ["student"]) },
    async (request, reply) => {
      try {
        const principal = (request as AuthenticatedRequest).principal;
        const params = request.params as { contentId: string };
        const body = StageSubmitRequestSchema.pick({ attemptId: true }).parse(request.body);
        const completed = store.completeAttempt({
          studentId: principal.studentId!,
          contentId: params.contentId,
          attemptId: body.attemptId,
        });
        if (!completed) {
          return fail(reply, 404, "ATTEMPT_NOT_FOUND", "진행 중인 시도를 찾을 수 없습니다.");
        }
        return ok(request, completed);
      } catch (error) {
        return handleRouteError(reply, error);
      }
    },
  );
}
