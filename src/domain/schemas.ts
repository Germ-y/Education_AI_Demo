import { z } from "zod";
import {
  AssetRoles,
  AssetTypes,
  AttemptStatuses,
  MissionStatuses,
  RealtimeSessionStatuses,
  RealtimeTemplateTypes,
  StageRoles,
  StudentTypes,
  TemplateTypes,
  UserRoles,
} from "./enums.js";

export const UserRoleSchema = z.enum(UserRoles);
export const StudentTypeSchema = z.enum(StudentTypes);
export const MissionStatusSchema = z.enum(MissionStatuses);
export const StageRoleSchema = z.enum(StageRoles);
export const TemplateTypeSchema = z.enum(TemplateTypes);
export const RealtimeTemplateTypeSchema = z.enum(RealtimeTemplateTypes);
export const AssetRoleSchema = z.enum(AssetRoles);
export const AssetTypeSchema = z.enum(AssetTypes);
export const AttemptStatusSchema = z.enum(AttemptStatuses);
export const RealtimeSessionStatusSchema = z.enum(RealtimeSessionStatuses);

export const ChoiceSchema = z.object({
  id: z.string().min(1),
  text: z.string().min(1),
});

export const RubricItemSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  required: z.boolean(),
});

export const RealtimePracticeSpecSchema = z.object({
  id: z.string().min(1),
  stageId: z.string().min(1),
  templateType: RealtimeTemplateTypeSchema,
  imageAssetId: z.string().min(1),
  mode: z.enum(["voice_or_text", "voice", "text"]),
  practiceTitle: z.string().min(1),
  situationText: z.string().min(1),
  aiRole: z.string().min(1),
  openingLine: z.string().min(1),
  studentGoal: z.string().min(1),
  rubric: z.array(RubricItemSchema).min(1),
  allowedFeedback: z.array(z.string().min(1)).min(1),
  forbidden: z.array(z.string().min(1)).min(1),
  maxTurns: z.number().int().positive().max(12),
  maxDurationSec: z.number().int().positive().max(300),
  postPracticeReflection: z.array(z.string().min(1)).min(1),
});

export const ContentStageSchema = z
  .object({
    id: z.string().min(1),
    missionContentId: z.string().min(1),
    step: z.number().int().min(1).max(4),
    stageRole: StageRoleSchema,
    templateType: TemplateTypeSchema,
    studentTitle: z.string().min(1),
    studentInstruction: z.string().min(1),
    templateJson: z.record(z.unknown()).default({}),
    realtimeSpec: RealtimePracticeSpecSchema.optional(),
    sortOrder: z.number().int().min(1).max(4),
  })
  .superRefine((stage, context) => {
    const isRealtimeTemplate = RealtimeTemplateTypes.includes(stage.templateType as (typeof RealtimeTemplateTypes)[number]);
    if (stage.step === 4 && !isRealtimeTemplate) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "4단계는 realtime_roleplay 또는 realtime_teach_back 템플릿이어야 합니다.",
        path: ["templateType"],
      });
    }
    if (stage.step !== 4 && isRealtimeTemplate) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Realtime 템플릿은 4단계에서만 사용할 수 있습니다.",
        path: ["step"],
      });
    }
    if (stage.step === 4 && !stage.realtimeSpec) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "4단계에는 승인 대상 RealtimePracticeSpec이 필요합니다.",
        path: ["realtimeSpec"],
      });
    }
  });

export const ContentAssetSchema = z.object({
  id: z.string().min(1),
  missionContentId: z.string().min(1),
  stageId: z.string().min(1).optional(),
  assetRole: AssetRoleSchema,
  assetType: AssetTypeSchema,
  provider: z.string().min(1),
  model: z.string().min(1),
  promptJson: z.record(z.unknown()).optional(),
  storageUrl: z.string().min(1),
  previewUrl: z.string().min(1).optional(),
  qaStatus: z.enum(["pending", "passed", "failed"]),
  approvalStatus: z.enum(["pending", "approved", "rejected"]),
});

export const MissionContentSchema = z
  .object({
    id: z.string().min(1),
    caseId: z.string().min(1),
    studentId: z.string().min(1),
    contentType: StudentTypeSchema,
    title: z.string().min(1),
    sessionGoal: z.string().min(1),
    status: MissionStatusSchema,
    totalSteps: z.literal(4),
    stages: z.array(ContentStageSchema).length(4),
    assets: z.array(ContentAssetSchema).min(5),
    briefJson: z.record(z.unknown()).default({}),
    teacherReviewSummary: z.string().optional(),
    approvedByUserId: z.string().optional(),
    approvedAt: z.string().datetime().optional(),
    publishedAt: z.string().datetime().optional(),
  })
  .superRefine((content, context) => {
    const steps = content.stages.map((stage) => stage.step).sort((a, b) => a - b);
    if (steps.join(",") !== "1,2,3,4") {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "MissionContent는 정확히 1~4단계를 가져야 합니다.",
        path: ["stages"],
      });
    }
    const assetRoles = new Set(content.assets.map((asset) => asset.assetRole));
    for (const role of AssetRoles) {
      if (!assetRoles.has(role)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: `필수 이미지 asset role이 없습니다: ${role}`,
          path: ["assets"],
        });
      }
    }
  });

export type RealtimePracticeSpec = z.infer<typeof RealtimePracticeSpecSchema>;
export type ContentStage = z.infer<typeof ContentStageSchema>;
export type ContentAsset = z.infer<typeof ContentAssetSchema>;
export type MissionContent = z.infer<typeof MissionContentSchema>;

export const DemoLoginRequestSchema = z.object({
  role: UserRoleSchema.exclude(["student"]),
  email: z.string().email().optional(),
});

export const StudentAccessRequestSchema = z.object({
  accessCode: z.string().min(1),
});

export const MemoryCardPatchSchema = z.object({
  emotionalStateNote: z.string().optional(),
  effectiveExplanationStyles: z.array(z.string()).optional(),
  frequentBlockingUnits: z.array(z.string()).optional(),
  guardianCooperationStatus: z.string().optional(),
  nextSessionCautions: z.array(z.string()).optional(),
});

export const StageSubmitRequestSchema = z.object({
  attemptId: z.string().min(1),
  answer: z.record(z.unknown()),
  clientEventId: z.string().min(1).optional(),
});

export const ReflectionRequestSchema = z.object({
  attemptId: z.string().min(1),
  reflectionChoice: z.string().min(1),
  shortText: z.string().optional(),
});
