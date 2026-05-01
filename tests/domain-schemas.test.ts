import { describe, expect, it } from "vitest";
import { createDemoDatabase } from "../src/data/demo-data.js";
import { ContentAssetSchema, ContentStageSchema, MissionContentSchema } from "../src/domain/schemas.js";

describe("mission content schema", () => {
  it("accepts the demo 4-stage mission packages", () => {
    const db = createDemoDatabase();

    for (const content of db.missionContents) {
      expect(() => MissionContentSchema.parse(content)).not.toThrow();
      expect(content.totalSteps).toBe(4);
      expect(content.stages.map((stage) => stage.step).sort()).toEqual([1, 2, 3, 4]);
    }
  });

  it("rejects a fifth stage", () => {
    const db = createDemoDatabase();
    const content = db.missionContents[0];

    expect(() =>
      MissionContentSchema.parse({
        ...content,
        totalSteps: 5,
        stages: [
          ...content.stages,
          {
            ...content.stages[0],
            id: "stage_bad_5",
            step: 5,
            sortOrder: 5,
          },
        ],
      }),
    ).toThrow();
  });

  it("allows realtime templates only at stage 4", () => {
    const db = createDemoDatabase();
    const stage = db.missionContents[0].stages[0];

    expect(() =>
      ContentStageSchema.parse({
        ...stage,
        templateType: "realtime_teach_back",
      }),
    ).toThrow();
  });

  it("rejects video asset roles", () => {
    const db = createDemoDatabase();
    const asset = db.missionContents[0].assets[0];

    expect(() =>
      ContentAssetSchema.parse({
        ...asset,
        assetRole: "video",
      }),
    ).toThrow();
  });
});
