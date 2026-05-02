import type { AssetRole, ContentAsset, ContentStage, MissionContent, TemplateType } from "@/lib/api/contracts";

const requiredAssetRoles: AssetRole[] = ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"];

export type MissionValidationResult = {
  ok: boolean;
  errors: string[];
};

export type ResolvedStageAssets = {
  image: ContentAsset | null;
  audio: ContentAsset | null;
};

export type StageTemplateRenderer =
  | "static_intro"
  | "image_quiz"
  | "card_match"
  | "sequence_ordering"
  | "blank_fill"
  | "realtime_practice";

export function validateMissionContent(mission: MissionContent): MissionValidationResult {
  const errors: string[] = [];
  const stageSteps = mission.stages.map((stage) => stage.step).sort((left, right) => left - right);
  const imageAssetRoles = new Set(mission.assets.filter((asset) => asset.assetType === "image").map((asset) => asset.assetRole));

  if (mission.totalSteps !== 4) errors.push("MissionContent.totalSteps must be 4.");
  if (mission.stages.length !== 4) errors.push("MissionContent.stages must contain exactly 4 stages.");
  if (stageSteps.join(",") !== "1,2,3,4") errors.push("MissionContent.stages must have steps [1,2,3,4].");

  for (const role of requiredAssetRoles) {
    if (!imageAssetRoles.has(role)) errors.push(`MissionContent.assets missing image ${role}.`);
  }

  for (const stage of mission.stages) {
    if (stage.step === 4) {
      if (stage.stageRole !== "realtime_practice") errors.push("Stage 4 must use realtime_practice stageRole.");
      if (!stage.realtimeSpec) errors.push("Stage 4 must include realtimeSpec.");
    } else if (stage.realtimeSpec) {
      errors.push(`Stage ${stage.step} must not include realtimeSpec.`);
    }
  }

  return { ok: errors.length === 0, errors };
}

export function getAssetByRole(
  mission: MissionContent,
  assetRole: AssetRole,
  assetType: ContentAsset["assetType"] = "image",
) {
  return mission.assets.find((asset) => asset.assetRole === assetRole && asset.assetType === assetType) ?? null;
}

export function getStageAssetRole(step: ContentStage["step"]): AssetRole {
  return step === 4 ? "stage_4_realtime" : `stage_${step}` as AssetRole;
}

export function resolveStageAssets(mission: MissionContent, stage: ContentStage): ResolvedStageAssets {
  const imageAssetId = typeof stage.templateJson.imageAssetId === "string" ? stage.templateJson.imageAssetId : null;
  const audioAssetId = typeof stage.templateJson.audioAssetId === "string" ? stage.templateJson.audioAssetId : null;
  const fallbackRole = getStageAssetRole(stage.step);

  return {
    image:
      mission.assets.find((asset) => asset.id === imageAssetId && asset.assetType === "image") ??
      getAssetByRole(mission, fallbackRole, "image"),
    audio:
      mission.assets.find((asset) => asset.id === audioAssetId && asset.assetType === "audio") ??
      getAssetByRole(mission, fallbackRole, "audio"),
  };
}

export function getTemplateRenderer(templateType: TemplateType): StageTemplateRenderer {
  if (templateType === "realtime_roleplay" || templateType === "realtime_teach_back") return "realtime_practice";
  if (templateType === "card_match") return "card_match";
  if (templateType === "sequence_ordering") return "sequence_ordering";
  if (templateType === "blank_fill") return "blank_fill";
  if (
    templateType === "scene_question" ||
    templateType === "clue_question" ||
    templateType === "partition_picker" ||
    templateType === "applied_question" ||
    templateType === "action_choice" ||
    templateType === "decision_card"
  ) {
    return "image_quiz";
  }

  return "static_intro";
}
