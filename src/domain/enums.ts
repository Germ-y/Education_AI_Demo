export const UserRoles = ["center_admin", "teacher", "content_reviewer", "guardian", "student"] as const;
export type UserRole = (typeof UserRoles)[number];

export const StudentTypes = ["life_support", "learning_focus"] as const;
export type StudentType = (typeof StudentTypes)[number];

export const MissionStatuses = [
  "draft",
  "generating",
  "teacher_review",
  "revision_requested",
  "approved",
  "published",
  "archived",
] as const;
export type MissionStatus = (typeof MissionStatuses)[number];

export const StageRoles = [
  "scenario_intro",
  "clue_identification",
  "action_selection",
  "concept_intro",
  "basic_problem",
  "applied_problem",
  "realtime_practice",
] as const;
export type StageRole = (typeof StageRoles)[number];

export const TemplateTypes = [
  "scenario_intro",
  "scene_observation",
  "highlight_clue",
  "card_match",
  "action_choice",
  "sequence_ordering",
  "decision_card",
  "concept_intro",
  "scene_question",
  "clue_question",
  "blank_fill",
  "partition_picker",
  "applied_question",
  "mini_simulation",
  "realtime_roleplay",
  "realtime_teach_back",
] as const;
export type TemplateType = (typeof TemplateTypes)[number];

export const RealtimeTemplateTypes = ["realtime_roleplay", "realtime_teach_back"] as const;
export type RealtimeTemplateType = (typeof RealtimeTemplateTypes)[number];

export const AssetRoles = ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"] as const;
export type AssetRole = (typeof AssetRoles)[number];

export const AssetTypes = ["image", "audio_optional"] as const;
export type AssetType = (typeof AssetTypes)[number];

export const AttemptStatuses = ["in_progress", "completed", "abandoned"] as const;
export type AttemptStatus = (typeof AttemptStatuses)[number];

export const RealtimeSessionStatuses = ["created", "active", "completed", "failed", "expired"] as const;
export type RealtimeSessionStatus = (typeof RealtimeSessionStatuses)[number];
