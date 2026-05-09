export type ApiSuccess<T> = {
  data: T;
  meta: {
    requestId: string;
  };
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export type FastApiError = {
  detail:
    | string
    | {
        code?: string;
        message?: string;
        details?: Record<string, unknown>;
      };
};

export type ApiEnvelope<T> = ApiSuccess<T> | ApiError | FastApiError;

export type ContentType = "life_support" | "learning_focus";
export type MissionStatus = "draft" | "generating" | "teacher_review" | "revision_requested" | "approved" | "published" | "archived";
export type StudentStatus = "active" | "archived";
export type UserRole = "center_admin" | "teacher" | "content_reviewer" | "guardian" | "student";
export type CaseStatus = "open" | "paused" | "closed";

export type StageRole =
  | "scenario_intro"
  | "clue_identification"
  | "action_selection"
  | "concept_intro"
  | "basic_problem"
  | "applied_problem"
  | "realtime_practice";

export type TemplateType =
  | "scenario_intro"
  | "scene_observation"
  | "highlight_clue"
  | "image_quiz"
  | "card_match"
  | "action_choice"
  | "sequence_ordering"
  | "decision_card"
  | "concept_intro"
  | "scene_question"
  | "clue_question"
  | "blank_fill"
  | "partition_picker"
  | "applied_question"
  | "mini_simulation"
  | "explanation_choice"
  | "wrong_explanation_fix"
  | "realtime_roleplay"
  | "realtime_teach_back";

export type AssetRole = "hero" | "stage_1" | "stage_2" | "stage_3" | "stage_4_realtime";

export type Organization = {
  id: string;
  externalKey: string;
  name: string;
  type: "learning_support_center" | "school" | "demo";
  regionCode?: string | null;
};

export type UserProfile = {
  id: string;
  organizationId: string;
  email: string;
  displayName: string;
  role: Exclude<UserRole, "student">;
  status: "active" | "invited" | "disabled";
};

export type AuthSession = {
  accessToken: string;
  expiresAt: string;
};

export type DemoLoginRequest = {
  role: "center_admin" | "teacher" | "content_reviewer" | "guardian";
  email?: string | null;
};

export type DemoLoginResponse = {
  user: UserProfile;
  session: AuthSession;
};

export type StudentAccessRequest = {
  accessCode: string;
};

export type StudentAccessResponse = {
  student: StudentProfile;
  session: AuthSession;
};

export type StudentProfile = {
  id: string;
  organizationId: string;
  externalKey: string;
  displayName: string;
  grade: string;
  gradeLabel?: string;
  schoolCode?: string | null;
  studentType: ContentType;
  studentTypeLabel?: string;
  trackLabel?: string;
  primaryNeed: string;
  profileJson: Record<string, unknown>;
  attendanceRate?: number | null;
  attendanceLabel?: string;
  accessCode?: string | null;
  strengths?: string[];
  weaknesses?: string[];
  status: StudentStatus;
};

export type SchoolProfile = {
  id: string;
  schoolCode: string;
  officeCode?: string | null;
  name?: string;
  schoolName?: string;
  schoolLevel?: "elementary" | "middle" | "high" | "unknown";
  schoolKind?: string;
  regionCode?: string | null;
  regionName?: string | null;
  address?: string | null;
  roadAddress?: string | null;
  source?: "seed_snapshot" | "NEIS" | "manual";
  sourceCode?: string;
};

export type SchoolSearchRequest = {
  q: string;
  officeCode?: string;
  syncIfMissing?: boolean;
};

export type SchoolSearchResponse = {
  schools: SchoolProfile[];
  source: {
    provider: string;
    cacheStatus: string;
    neisStatus?: string;
    counts?: Record<string, unknown>;
  };
};

export type ContextMe = {
  user: UserProfile;
  organization: Organization;
  mode: "demo_seed";
};

export type SchoolCalendarItem = {
  date: string;
  title: string;
  source: string;
};

export type SchoolTimetableSlot = {
  id?: string;
  schoolCode?: string;
  officeCode?: string;
  academicYear?: string;
  semester?: string;
  timetableDate: string;
  grade: string;
  className: string;
  period: number;
  subjectName?: string | null;
  sourceCode?: string;
  retrievedAt?: string;
};

export type EducationStat = {
  label: string;
  value: string;
  source: string;
};

export type PublicContextBundle = {
  studentId?: string;
  school: SchoolProfile;
  calendar: Array<SchoolCalendarItem | Record<string, unknown>>;
  timetable?: SchoolTimetableSlot[];
  timetableSummary: {
    todaySubjects: string[];
    source: string;
    date?: string | null;
    cacheStatus?: string;
  };
  educationStats?: EducationStat[];
  lastSyncedAt?: string | null;
};

export type SchoolTimetableDay = {
  date: string;
  weekdayLabel: string;
  subjects: string[];
  slots: SchoolTimetableSlot[];
  cacheStatus: string;
};

export type SchoolWeeklyTimetable = {
  school: SchoolProfile;
  weekStart: string;
  weekEnd: string;
  grade: string;
  className: string;
  days: SchoolTimetableDay[];
  source: {
    provider: string;
    cacheStatus: string;
    counts?: Record<string, unknown> | null;
  };
  orchestratorHints: string[];
};

export type StudentListItem = {
  studentId: string;
  displayName: string;
  grade: string;
  gradeLabel?: string;
  schoolName?: string;
  studentType: ContentType;
  studentTypeLabel?: string;
  trackLabel?: string;
  primaryNeed: string;
  attendanceRate?: number | null;
  attendanceLabel?: string;
  accessCode?: string | null;
  strengths?: string[];
  weaknesses?: string[];
  caseStatus?: CaseStatus;
  latestContentStatus: MissionStatus | "completed" | "none";
  dashboardStage?: "initial_review" | "material_generation" | "material_review" | "learning" | "feedback";
  dashboardStageLabel?: string;
  statusLabel?: string;
  supportStrategy?: string | null;
  summaryLine?: string;
  aiContextSummary?: string;
  nextSessionSuggestion: string;
};

export type StudentRegistrationRequest = {
  displayName: string;
  schoolCode?: string | null;
  schoolName?: string | null;
  officeCode?: string;
  grade: string;
  gradeNumber?: string | null;
  className?: string | null;
  studentType: ContentType;
  trackLabel?: string | null;
  currentGoal: string;
  observationNote?: string | null;
  strengths: string[];
  weaknesses: string[];
  preferredSupports: string[];
  supportIntake?: Record<string, unknown> | null;
  timetableDate?: string | null;
};

export type SupportCaseSummary = {
  id: string;
  studentId: string;
  ownerTeacherId: string;
  caseStatus: CaseStatus;
  currentGoal: string;
  dashboardStage?: "initial_review" | "material_generation" | "material_review" | "learning" | "feedback";
  supportStrategy?: string | null;
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

export type CaseNoteCreate = {
  noteType: CaseNote["noteType"];
  body: string;
  visibility?: CaseNote["visibility"];
};

export type MemoryCard = {
  id: string;
  studentId: string;
  caseId: string;
  version: number;
  learningProblemTypes: string[];
  recent4wResponseJson: Record<string, unknown>;
  emotionalStateNote?: string | null;
  effectiveExplanationStyles: string[];
  frequentBlockingUnits: string[];
  guardianCooperationStatus?: string | null;
  nextSessionCautions: string[];
  teacherVerifiedAt?: string | null;
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

export type DashboardProfile = {
  headline: string;
  currentStageLabel: string;
  attendanceLabel: string;
  primaryNeedTitle: string;
  primaryNeedDetail: string;
  supportStrategyTitle: string;
  supportStrategyDetail?: string | null;
  strengths: string[];
  weaknesses: string[];
  emotionalNote?: string | null;
  responsePattern?: string | null;
  guardianCooperation?: string | null;
  schoolContextNote?: string | null;
  nextSessionFocus: string[];
  aiContextSummary: string;
  autoContext: Array<{ label: string; value: string }>;
  supportProfileStatus?: "none" | "confirmed";
  lessonDesignHints?: string[];
  learningResponsePattern?: Record<string, unknown> | null;
  behaviorSupportProfile?: Record<string, unknown> | null;
  supportCautions?: string[];
};

export type StudentContextBundle = {
  student: {
    id: string;
    name: string;
    displayName: string;
    grade: string;
    gradeLabel: string;
    studentType: ContentType;
    studentTypeLabel: string;
    trackLabel: string;
  };
  caseSummary: Record<string, unknown>;
  teacherInputs: CaseNote[];
  previousLessons: Array<Record<string, unknown>>;
  memoryCard: MemoryCard | null;
  schoolContext: PublicContextBundle | null;
  autoContext: Array<{ label: string; value: string }>;
  aiReadyContext: {
    summary: string;
    mustUse: string[];
    avoid: string[];
    evidenceSources: Array<Record<string, unknown>>;
    contextBriefId?: string | null;
    contextBriefDirty?: boolean;
  };
  supportProfile?: StudentSupportProfile | null;
  contextBrief?: StudentContextBrief | null;
};

export type StudentSupportProfile = {
  id: string;
  studentId: string;
  sourceIntakeId?: string | null;
  status: "draft" | "confirmed" | "superseded";
  profileJson: Record<string, unknown>;
  generatedBy: string;
  teacherConfirmedByUserId?: string | null;
  createdAt: string;
  confirmedAt?: string | null;
};

export type SupportProfileDraftResponse = {
  draftId: string;
  studentId: string;
  status: "completed";
  profileDraft: Record<string, unknown>;
  supportProfile: StudentSupportProfile;
};

export type SupportProfileConfirmRequest = {
  draftId?: string | null;
  profileDraft: Record<string, unknown>;
  teacherNote?: string | null;
};

export type StudentContextBrief = {
  id: string;
  studentId: string;
  briefText: string;
  studentType: string;
  readingLoad: string;
  choiceCount: number;
  recentSuccessPatterns: string[];
  recentDifficultyPatterns: string[];
  recommendedScaffolds: string[];
  avoidTopicRegression: string[];
  sourceWatermark: string;
  dirty: boolean;
  status: "dirty" | "refreshed";
  sourceJson: Record<string, unknown>;
  model: string;
  refreshedAt?: string | null;
  createdAt: string;
};

export type StudentCaseFile = {
  profile: StudentProfile;
  schoolContext?: PublicContextBundle;
  dashboardProfile?: DashboardProfile;
  contextBundle?: StudentContextBundle;
  supportProfileDraft?: StudentSupportProfile | null;
  supportProfile?: StudentSupportProfile | null;
  contextBrief?: StudentContextBrief | null;
  openCase: SupportCaseSummary;
  memoryCard: MemoryCard | null;
  weeklyRecords: CaseNote[];
  monthlySummary: Record<string, unknown> | string;
  recentContents: MissionContent[];
  plannerItems: PlannerItem[];
  publicContextSummary?: Record<string, unknown>;
};

export type TeacherReportDraft = {
  id: string;
  reviewSummaryId: string;
  studentId: string;
  contentId: string;
  status: "streaming" | "completed" | "failed";
  bodyMarkdown: string;
  nextLearningSuggestions: string[];
  memoryCandidates: string[];
  inputSnapshotJson: Record<string, unknown>;
  model: string;
  createdAt: string;
  completedAt?: string | null;
};

export type TeacherReport = {
  id: string;
  draftId?: string | null;
  reviewSummaryId: string;
  studentId: string;
  contentId: string;
  teacherBody: string;
  selectedMemoryCandidates: string[];
  createdByUserId: string;
  createdAt: string;
};

export type TeacherReportCreateRequest = {
  draftId?: string | null;
  reviewSummaryId: string;
  studentId: string;
  contentId: string;
  teacherBody: string;
  selectedMemoryCandidates: string[];
};

export type StudentRegistrationResponse = {
  student: StudentCaseFile | null;
  created: boolean;
  accessCode: string | null;
};

export type StudentReportItem = {
  id: string;
  studentId: string;
  caseId: string;
  contentId: string;
  contentTitle?: string | null;
  attemptId: string;
  startedAt: string;
  completedAt?: string | null;
  completionRate: number;
  accuracyRate: number;
  durationSec?: number | null;
  answerCount: number;
  wrongCount: number;
  hintCount: number;
  shortSummary: string;
  wrongPatternJson: Record<string, unknown>;
  realtimeResultJson: Record<string, unknown>;
  realtimeTranscriptSummary?: string | null;
  reflection?: Record<string, unknown> | null;
  aiReportDrafts?: TeacherReportDraft[];
  teacherReports?: TeacherReport[];
};

export type StudentReport = {
  student: StudentProfile;
  openCase: SupportCaseSummary;
  reports: StudentReportItem[];
};

export type Choice = {
  id: string;
  text: string;
};

export type RubricItem = {
  id: string;
  label: string;
  required: boolean;
};

export type RealtimePracticeSpec = {
  id: string;
  stageId: string;
  templateType: "realtime_roleplay" | "realtime_teach_back";
  imageAssetId: string;
  mode: "voice_or_text" | "voice" | "text";
  practiceTitle: string;
  situationText: string;
  aiRole: string;
  openingLine: string;
  studentGoal: string;
  rubric: RubricItem[];
  allowedFeedback: string[];
  forbidden: string[];
  maxTurns: number;
  maxDurationSec: number;
  postPracticeReflection: string[];
};

export type StudentStageTitle =
  | "상황 만나기"
  | "단서 찾기"
  | "행동 고르기"
  | "한 번 해보기"
  | "개념 열기"
  | "문제 1"
  | "문제 2"
  | "설명해보기";

export type ContentStage = {
  id: string;
  missionContentId: string;
  step: 1 | 2 | 3 | 4;
  stageRole: StageRole;
  templateType: TemplateType;
  studentTitle: StudentStageTitle;
  studentInstruction: string;
  templateJson: Record<string, unknown>;
  realtimeSpec: RealtimePracticeSpec | null;
  sortOrder: 1 | 2 | 3 | 4;
};

export type ContentAsset = {
  id: string;
  missionContentId: string;
  stageId?: string | null;
  assetRole: AssetRole;
  assetType: "image" | "audio";
  provider: string;
  model: string;
  promptJson?: Record<string, unknown> | null;
  sourceText?: string | null;
  storageUrl: string;
  previewUrl?: string | null;
  qaStatus: "pending" | "passed" | "failed";
  approvalStatus: "pending" | "approved" | "rejected";
};

export type MissionContent = {
  id: string;
  caseId: string;
  studentId: string;
  contentType: ContentType;
  title: string;
  sessionGoal: string;
  status: MissionStatus;
  totalSteps: 4;
  stages: ContentStage[];
  assets: ContentAsset[];
  briefJson: Record<string, unknown>;
  teacherReviewSummary?: string | null;
  approvedByUserId?: string | null;
  approvedAt?: string | null;
  publishedAt?: string | null;
};

export type ContentApprovalRequest = {
  approvedStageIds: string[];
  approvedAssetIds: string[];
  reviewNote?: string | null;
};

export type ContentRejectRequest = {
  reason: string;
  requestedChanges?: string[];
};

export type ContentStagePatch = {
  stageId: string;
  studentInstruction?: string | null;
  question?: string | null;
  choices?: string[] | null;
  realtimeStudentGoal?: string | null;
};

export type ContentReviewUpdateRequest = {
  stages: ContentStagePatch[];
};

export type SeedContext = {
  organization: Organization;
  teacher: UserProfile;
  students: StudentProfile[];
  schools: SchoolProfile[];
  cases: SupportCaseSummary[];
  contents: MissionContent[];
  mappings: Array<{
    studentId: string;
    caseId: string;
    contentId: string;
    title?: string;
    status?: MissionStatus | string;
    updatedAt?: string | null;
    latestAttemptStatus?: "in_progress" | "completed" | "abandoned" | null;
    latestAttemptCurrentStep?: 1 | 2 | 3 | 4 | null;
    latestAttemptCompletedAt?: string | null;
    isCompleted?: boolean;
  }>;
};

export type StudentMissionSummary = {
  contentId: string;
  title: string;
  contentType: ContentType;
  totalSteps: 4;
  heroImageUrl?: string | null;
  heroAudioUrl?: string | null;
  status: "published";
};

export type ContentAttempt = {
  id: string;
  missionContentId: string;
  studentId: string;
  status: "in_progress" | "completed" | "abandoned";
  currentStep: 1 | 2 | 3 | 4;
  startedAt: string;
  completedAt?: string | null;
  scoreJson?: Record<string, unknown> | null;
};

export type StageSubmitRequest = {
  attemptId: string;
  answer: Record<string, unknown>;
  clientEventId?: string;
};

export type StudentActivityEventRequest = {
  attemptId?: string | null;
  stageId?: string | null;
  eventType: string;
  payloadJson?: Record<string, unknown>;
};

export type ReflectionRequest = {
  attemptId: string;
  reflectionChoice: string;
  shortText?: string | null;
};

export type ReflectionResponse = {
  saved: boolean;
};

export type StageSubmitResponse = {
  isRealtimeStage: boolean;
  isCorrect: boolean;
  feedback: string;
  nextStep: 1 | 2 | 3 | 4;
};

export type RealtimeSessionRequest = {
  attemptId: string;
};

export type RealtimeSessionResponse = {
  sessionId: string;
  provider: "openai";
  model: string;
  clientSecret: string;
  expiresAt: string;
  webrtcUrl: string;
  practiceSpec: {
    practiceTitle: string;
    imageAssetUrl?: string | null;
    openingAudioUrl?: string | null;
    openingLine: string;
    maxTurns: number;
    maxDurationSec: number;
  };
};

export type RealtimeSessionEventRequest = {
  eventType: string;
  payloadJson: Record<string, unknown>;
};

export type RealtimeSessionCompleteRequest = {
  turnCount: number;
  durationSec: number;
  rubricResult: Record<string, unknown>;
  transcriptSummary?: string | null;
};

export type ReviewableContent = MissionContent;

export type AgentRun = {
  id: string;
  agentType: string;
  promptVersion: string;
  outputSchemaName: string;
  inputSnapshotJson: Record<string, unknown>;
  outputJson?: Record<string, unknown> | null;
  model: string;
  status: "running" | "succeeded" | "failed";
  tokenUsageJson?: Record<string, unknown> | null;
  errorCode?: string | null;
  errorMessage?: string | null;
  reviewRequired: boolean;
  createdAt: string;
  completedAt?: string | null;
};

export type AgentRunRequest = {
  studentId: string;
  caseId: string;
  requestedGoal: string;
  contentType: ContentType;
};

export type OrchestratorRunResponse = {
  agentRun: AgentRun | null;
};

export type ContentGenerationRequest = {
  orchestratorRunId: string;
  studentId: string;
  caseId: string;
};

export type ContentGenerationResponse = {
  agentRun: AgentRun | null;
  content: MissionContent | null;
};

export type AssetPackageGenerationResponse = {
  contentId: string;
  generatedCount: number;
  assets: ContentAsset[];
};

export type AssetGenerationJobAsset = {
  assetId: string;
  assetRole: AssetRole;
  assetType: "image" | "audio";
  stageId?: string | null;
  status: "queued" | "running" | "succeeded" | "skipped" | "failed";
  storageUrl?: string | null;
  previewUrl?: string | null;
  qaStatus: "pending" | "passed" | "failed";
  approvalStatus: "pending" | "approved" | "rejected";
  errorCode?: string | null;
  errorMessage?: string | null;
  updatedAt?: string | null;
};

export type AssetGenerationJob = {
  jobId: string;
  contentId: string;
  teacherId?: string | null;
  status: "queued" | "running" | "partial_failed" | "succeeded" | "failed";
  queuedAt: string;
  startedAt?: string | null;
  completedAt?: string | null;
  totalCount: number;
  completedCount: number;
  failedCount: number;
  generatedCount: number;
  assets: AssetGenerationJobAsset[];
  errorCode?: string | null;
  errorMessage?: string | null;
};
