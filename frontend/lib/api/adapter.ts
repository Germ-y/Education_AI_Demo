import type {
  AssetPackageGenerationResponse,
  AssetGenerationJob,
  AgentRun,
  AgentRunRequest,
  ContentGenerationRequest,
  ContentGenerationResponse,
  ContextMe,
  DemoLoginRequest,
  DemoLoginResponse,
  MissionContent,
  OrchestratorRunResponse,
  GenerationJob,
  GenerationJobRequest,
  GenerationJobResponse,
  PublicContextBundle,
  RealtimeSessionRequest,
  RealtimeSessionResponse,
  ReviewableContent,
  SeedContext,
  SchoolSearchRequest,
  SchoolSearchResponse,
  StudentAccessRequest,
  StudentAccessResponse,
  StudentCaseFile,
  StudentListItem,
  StudentMissionSummary,
  StudentRegistrationRequest,
  StudentRegistrationResponse,
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
  createTeacherStudent(payload: StudentRegistrationRequest, options?: ApiAdapterOptions): Promise<StudentRegistrationResponse>;
  getTeacherStudent(studentId: string, options?: ApiAdapterOptions): Promise<StudentCaseFile>;
  getTeacherStudentReport(studentId: string, options?: ApiAdapterOptions): Promise<StudentReport>;
  searchSchools(params: SchoolSearchRequest, options?: ApiAdapterOptions): Promise<SchoolSearchResponse>;
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
  createGenerationJob(payload: GenerationJobRequest, options?: ApiAdapterOptions): Promise<GenerationJobResponse>;
  listGenerationJobs(params: { studentId?: string; caseId?: string; status?: GenerationJob["status"] }, options?: ApiAdapterOptions): Promise<GenerationJob[]>;
  getGenerationJob(jobId: string, options?: ApiAdapterOptions): Promise<GenerationJob>;
  generateContentAssetPackage(contentId: string, options?: ApiAdapterOptions): Promise<AssetPackageGenerationResponse>;
  createContentAssetGenerationJob(contentId: string, options?: ApiAdapterOptions): Promise<AssetGenerationJob>;
  getContentAssetGenerationJob(contentId: string, jobId: string, options?: ApiAdapterOptions): Promise<AssetGenerationJob>;
};
