import type { FastifyInstance } from "fastify";
import type { DemoStore } from "../../data/store.js";
import { requirePrincipal } from "../auth.js";
import { ok } from "../response.js";

export async function registerPublicDataRoutes(app: FastifyInstance, store: DemoStore) {
  app.get(
    "/api/public-data/sources",
    { preHandler: requirePrincipal(store, ["teacher", "center_admin", "content_reviewer"]) },
    async (request) => ok(request, store.db.publicDataSources),
  );
}
