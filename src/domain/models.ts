import type { StudentType } from "./enums.js";
import type { MissionContent } from "./schemas.js";

export type Organization = {
  id: string;
  externalKey: string;
  name: string;
  type: "learning_support_center" | "school" | "demo";
  regionCode?: string;
};

export type User = {
  id: string;
  organizationId: string;
  email: string;
  displayName: string;
  role: "center_admin" | "teacher" | "content_reviewer" | "guardian";
  status: "active" | "invited" | "disabled";
};

export type Student = {
  id: string;
  organizationId: string;
  externalKey: string;
  displayName: string;
  grade: string;
  schoolCode?: string;
  studentType: StudentType;
  primaryNeed: string;
  profileJson: Record<string, unknown>;
  status: "active" | "archived";
};

export type StudentAccount = {
  id: string;
  studentId: string;
  accessCode: string;
  status: "active" | "disabled";
};

export type SupportCase = {
  id: string;
  studentId: string;
  ownerTeacherId: string;
  caseStatus: "open" | "paused" | "closed";
  currentGoal: string;
  openedAt: string;
};

export type CaseNote = {
  id: string;
  caseId: string;
  authorId: string;
  noteType: "consultation" | "session" | "teacher_comment" | "guardian";
  body: string;
  visibility: "teacher_only" | "center" | "guardian_summary";
  createdAt: string;
};

export type MemoryCard = {
  id: string;
  studentId: string;
  caseId: string;
  version: number;
  learningProblemTypes: string[];
  recent4wResponseJson: Record<string, unknown>;
  emotionalStateNote?: string;
  effectiveExplanationStyles: string[];
  frequentBlockingUnits: string[];
  guardianCooperationStatus?: string;
  nextSessionCautions: string[];
  teacherVerifiedAt?: string;
  status: "active" | "superseded";
};

export type PlannerItem = {
  id: string;
  studentId: string;
  caseId: string;
  periodType: "weekly" | "monthly" | "next_session";
  goalText: string;
  checklistJson: Record<string, unknown>;
  status: "planned" | "done" | "skipped";
};

export type ActivityEvent = {
  id: string;
  attemptId?: string;
  studentId: string;
  stageId?: string;
  eventType: string;
  payloadJson: Record<string, unknown>;
  occurredAt: string;
};

export type ContentAttempt = {
  id: string;
  missionContentId: string;
  studentId: string;
  status: "in_progress" | "completed" | "abandoned";
  currentStep: number;
  startedAt: string;
  completedAt?: string;
  scoreJson?: Record<string, unknown>;
};

export type RealtimePracticeSession = {
  id: string;
  attemptId: string;
  missionContentId: string;
  stageId: string;
  studentId: string;
  provider: "openai";
  model: string;
  status: "created" | "active" | "completed" | "failed" | "expired";
  specSnapshotJson: Record<string, unknown>;
  startedAt?: string;
  endedAt?: string;
  turnCount: number;
  durationSec: number;
  rubricResultJson?: Record<string, unknown>;
  transcriptSummary?: string;
};

export type PublicDataSource = {
  id: string;
  sourceCode: string;
  name: string;
  baseUrl?: string;
  authType: "api_key" | "none" | "manual_seed";
  enabled: boolean;
};

export type DemoDatabase = {
  organizations: Organization[];
  users: User[];
  students: Student[];
  studentAccounts: StudentAccount[];
  supportCases: SupportCase[];
  caseNotes: CaseNote[];
  memoryCards: MemoryCard[];
  plannerItems: PlannerItem[];
  missionContents: MissionContent[];
  attempts: ContentAttempt[];
  activityEvents: ActivityEvent[];
  realtimeSessions: RealtimePracticeSession[];
  publicDataSources: PublicDataSource[];
};
