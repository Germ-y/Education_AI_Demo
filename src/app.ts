import cors from "@fastify/cors";
import sensible from "@fastify/sensible";
import { randomUUID } from "node:crypto";
import Fastify from "fastify";
import { store, type DemoStore } from "./data/store.js";
import { registerAuthRoutes } from "./http/routes/auth-routes.js";
import { registerPublicDataRoutes } from "./http/routes/public-data-routes.js";
import { registerStudentRoutes } from "./http/routes/student-routes.js";
import { registerTeacherRoutes } from "./http/routes/teacher-routes.js";
import { ok } from "./http/response.js";

export async function buildApp(options: { demoStore?: DemoStore } = {}) {
  const app = Fastify({
    logger: process.env.NODE_ENV !== "test",
    genReqId: () => randomUUID(),
  });
  const activeStore = options.demoStore ?? store;

  await app.register(cors, { origin: true, credentials: true });
  await app.register(sensible);

  app.get("/health", async (request) =>
    ok(request, {
      status: "ok",
      service: "eduyj-backend",
      mode: "demo-seed",
    }),
  );

  await registerAuthRoutes(app, activeStore);
  await registerTeacherRoutes(app, activeStore);
  await registerStudentRoutes(app, activeStore);
  await registerPublicDataRoutes(app, activeStore);

  return app;
}
