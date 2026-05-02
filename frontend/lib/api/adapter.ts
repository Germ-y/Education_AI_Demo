import type {
  AgentRunPlan,
  AgentRunRequest,
  ContextMe,
  DemoLoginRequest,
  DemoLoginResponse,
  MissionContent,
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
  createAgentRun(payload: AgentRunRequest, options?: ApiAdapterOptions): Promise<AgentRunPlan>;
};
