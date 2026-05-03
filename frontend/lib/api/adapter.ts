import type {
  AssetPackageGenerationResponse,
  AgentRun,
  AgentRunRequest,
  ContentGenerationRequest,
  ContentGenerationResponse,
  ContextMe,
  DemoLoginRequest,
  DemoLoginResponse,
  MissionContent,
  OrchestratorRunResponse,
  PublicContextBundle,
  RealtimeSessionRequest,
  RealtimeSessionResponse,
  ReviewableContent,
  SeedContext,
  StudentAccessRequest,
  StudentAccessResponse,
  StudentCaseFile,
  StudentListItem,
  StudentMissionSummary,
  StudentReport,
} from "./contracts";

export type ApiAdapterOptions = {
  token?: string;
};

export type ApiAdapter = {
  demoLogin(payload: DemoLoginRequest): Promise<DemoLoginResponse>;
  studentAccess(payload: StudentAccessRequest): Promise<StudentAccessResponse>;
  getContextSeed(options?: ApiAdapterOptions): Promise<SeedContext>;
  getContextMe(options?: ApiAdapterOptions): Promise<ContextMe>;
  getTeacherStudents(options?: ApiAdapterOptions): Promise<StudentListItem[]>;
  getTeacherStudent(studentId: string, options?: ApiAdapterOptions): Promise<StudentCaseFile>;
  getTeacherStudentReport(studentId: string, options?: ApiAdapterOptions): Promise<StudentReport>;
  getSchoolContext(schoolId: string, options?: ApiAdapterOptions): Promise<PublicContextBundle>;
  getTodayStudentMissions(options?: ApiAdapterOptions): Promise<StudentMissionSummary[]>;
  getStudentMission(contentId: string, options?: ApiAdapterOptions): Promise<MissionContent>;
  getReviewableContent(contentId: string, options?: ApiAdapterOptions): Promise<ReviewableContent>;
  createRealtimeSession(
    contentId: string,
    stageId: string,
    payload: RealtimeSessionRequest,
    options?: ApiAdapterOptions,
  ): Promise<RealtimeSessionResponse>;
  getAgentRun(agentRunId: string, options?: ApiAdapterOptions): Promise<AgentRun>;
  listAgentRuns(params: { studentId?: string; caseId?: string; status?: AgentRun["status"] }, options?: ApiAdapterOptions): Promise<AgentRun[]>;
  createAgentRun(payload: AgentRunRequest, options?: ApiAdapterOptions): Promise<OrchestratorRunResponse>;
  createContentGeneration(payload: ContentGenerationRequest, options?: ApiAdapterOptions): Promise<ContentGenerationResponse>;
  generateContentAssetPackage(contentId: string, options?: ApiAdapterOptions): Promise<AssetPackageGenerationResponse>;
};
