import type { ApiAdapter } from "./adapter";
import type {
  AgentRunPlan,
  ContextMe,
  ContentAsset,
  ContentStage,
  DemoLoginResponse,
  MissionContent,
  PublicContextBundle,
  RealtimeSessionResponse,
  SchoolProfile,
  StudentAccessResponse,
  StudentCaseFile,
  StudentListItem,
  StudentMissionSummary,
  StudentProfile,
} from "./contracts";

const now = "2026-05-02T00:00:00.000Z";

const organization = {
  id: "org_yeongju_center",
  externalKey: "demo_org_yeongju_center",
  name: "영주 기초학력거점지원센터",
  type: "learning_support_center",
  regionCode: "47210",
} satisfies ContextMe["organization"];

const teacher = {
  id: "user_teacher_demo",
  organizationId: organization.id,
  email: "teacher.demo@eduyj.local",
  displayName: "데모 선생님",
  role: "teacher",
  status: "active",
} satisfies ContextMe["user"];

const schools: Record<string, SchoolProfile> = {
  demo_middle_school: {
    id: "school_demo_middle",
    schoolCode: "demo_middle_school",
    officeCode: "R10",
    name: "영주 데모중학교",
    schoolLevel: "middle",
    regionCode: "47210",
    address: "경상북도 영주시",
    source: "seed_snapshot",
  },
  demo_elementary_school: {
    id: "school_demo_elementary",
    schoolCode: "demo_elementary_school",
    officeCode: "R10",
    name: "영주 데모초등학교",
    schoolLevel: "elementary",
    regionCode: "47210",
    address: "경상북도 영주시",
    source: "seed_snapshot",
  },
};

const students: StudentProfile[] = [
  {
    id: "student_learning_fraction",
    organizationId: organization.id,
    externalKey: "demo_student_learning_fraction",
    displayName: "민지",
    grade: "middle_2",
    schoolCode: "demo_middle_school",
    studentType: "learning_focus",
    primaryNeed: "분수의 전체-부분 관계 이해",
    profileJson: { interests: ["요리", "탐험"], readingLoad: "low", choiceCountLimit: 3 },
    status: "active",
  },
  {
    id: "student_life_bus",
    organizationId: organization.id,
    externalKey: "demo_student_life_bus",
    displayName: "하늘",
    grade: "elementary_6",
    schoolCode: "demo_elementary_school",
    studentType: "life_support",
    primaryNeed: "센터 이동 순서와 도움 요청 연습",
    profileJson: { interests: ["동네 지도", "역할극"], readingLoad: "very_low", choiceCountLimit: 2 },
    status: "active",
  },
];

const publicContexts: Record<string, PublicContextBundle> = {
  demo_middle_school: {
    studentId: "student_learning_fraction",
    school: schools.demo_middle_school,
    calendar: [{ date: "2026-05-06", title: "중간고사 준비 기간", source: "NEIS_SCHOOL_SCHEDULE" }],
    timetableSummary: { todaySubjects: ["수학", "국어", "영어"], source: "NEIS_TIMETABLE" },
    educationStats: [{ label: "지역 학습지원 프로그램", value: "2026년 seed snapshot 기준", source: "KESS" }],
    lastSyncedAt: now,
  },
  demo_elementary_school: {
    studentId: "student_life_bus",
    school: schools.demo_elementary_school,
    calendar: [{ date: "2026-05-08", title: "현장체험학습 안내", source: "NEIS_SCHOOL_SCHEDULE" }],
    timetableSummary: { todaySubjects: ["사회", "수학", "창체"], source: "NEIS_TIMETABLE" },
    educationStats: [{ label: "통학 안전 지도", value: "seed snapshot", source: "manual_seed" }],
    lastSyncedAt: now,
  },
};

function imageAsset(contentId: string, assetRole: ContentAsset["assetRole"], stageId: string | null): ContentAsset {
  const url = "/examples/generated/fraction-mission/fraction-pizza.png";
  return {
    id: `asset_${contentId}_${assetRole}`,
    missionContentId: contentId,
    stageId,
    assetRole,
    assetType: "image",
    provider: "openai",
    model: "gpt-image-2",
    promptJson: {},
    storageUrl: url,
    previewUrl: url,
    qaStatus: "passed",
    approvalStatus: "approved",
  };
}

const fractionStages: ContentStage[] = [
  {
    id: "stage_fraction_1",
    missionContentId: "content_fraction_001",
    step: 1,
    stageRole: "concept_intro",
    templateType: "concept_intro",
    studentTitle: "개념 열기",
    studentInstruction: "피자 그림을 보며 전체와 부분을 확인해요.",
    templateJson: {
      imageAssetId: "asset_content_fraction_001_stage_1",
      storyText: "피자가 같은 크기 4조각으로 나뉘어 있어요.",
      missionText: "빛나는 조각이 전체 중 얼마나 되는지 찾아봐요.",
    },
    realtimeSpec: null,
    sortOrder: 1,
  },
  {
    id: "stage_fraction_2",
    missionContentId: "content_fraction_001",
    step: 2,
    stageRole: "basic_problem",
    templateType: "partition_picker",
    studentTitle: "문제 1",
    studentInstruction: "전체 조각 수를 먼저 확인해요.",
    templateJson: {
      imageAssetId: "asset_content_fraction_001_stage_2",
      question: "전체는 몇 조각인가요?",
      choices: [
        { id: "a", text: "1조각" },
        { id: "b", text: "4조각" },
        { id: "c", text: "2조각" },
      ],
      answer: "b",
      correctFeedback: "맞아요. 전체는 4조각이에요.",
      wrongFeedback: "피자가 몇 칸으로 나뉘었는지 다시 살펴봐요.",
    },
    realtimeSpec: null,
    sortOrder: 2,
  },
  {
    id: "stage_fraction_3",
    missionContentId: "content_fraction_001",
    step: 3,
    stageRole: "applied_problem",
    templateType: "blank_fill",
    studentTitle: "문제 2",
    studentInstruction: "고른 조각 수와 전체 조각 수를 분수 자리에 넣어봐요.",
    templateJson: {
      imageAssetId: "asset_content_fraction_001_stage_3",
      question: "전체 4개 중 1개는 __ / __ 이에요.",
      acceptedAnswers: [{ numerator: "1", denominator: "4" }],
      correctFeedback: "좋아요. 위에는 고른 1, 아래에는 전체 4가 들어가요.",
      wrongFeedback: "위에는 고른 조각 수, 아래에는 전체 조각 수를 넣어요.",
    },
    realtimeSpec: null,
    sortOrder: 3,
  },
  {
    id: "stage_fraction_4",
    missionContentId: "content_fraction_001",
    step: 4,
    stageRole: "realtime_practice",
    templateType: "realtime_teach_back",
    studentTitle: "AI에게 말해보기",
    studentInstruction: "AI에게 왜 1/4인지 말로 설명해봐요.",
    templateJson: { imageAssetId: "asset_content_fraction_001_stage_4_realtime" },
    realtimeSpec: {
      id: "rt_spec_fraction_001",
      stageId: "stage_fraction_4",
      templateType: "realtime_teach_back",
      imageAssetId: "asset_content_fraction_001_stage_4_realtime",
      mode: "voice_or_text",
      practiceTitle: "AI에게 분수 설명하기",
      situationText: "AI가 빛나는 피자 조각을 보고 왜 1/4인지 궁금해해요.",
      aiRole: "질문하는 친구",
      openingLine: "왜 4/1이 아니라 1/4인지 설명해줄래?",
      studentGoal: "전체 4개 중 고른 것이 1개라서 1/4이라고 설명하기",
      rubric: [
        { id: "mention_whole", label: "전체가 4개임을 말한다", required: true },
        { id: "mention_part", label: "고른 것이 1개임을 말한다", required: true },
        { id: "connect_fraction", label: "1/4 표현과 연결한다", required: true },
      ],
      allowedFeedback: ["좋아요. 전체가 몇 개인지 말했어요.", "이제 1/4 표현까지 이어서 말해봐요."],
      forbidden: ["진단 명칭 말하지 않기", "개인정보 묻지 않기"],
      maxTurns: 6,
      maxDurationSec: 120,
      postPracticeReflection: ["쉬웠어요", "조금 헷갈렸어요", "다시 연습하고 싶어요"],
    },
    sortOrder: 4,
  },
];

const missions: MissionContent[] = [
  {
    id: "content_fraction_001",
    caseId: "case_learning_fraction",
    studentId: "student_learning_fraction",
    contentType: "learning_focus",
    title: "분수 탐험: 빛나는 한 조각",
    sessionGoal: "전체 4개 중 1개를 1/4로 표현하고 말로 설명한다.",
    status: "published",
    totalSteps: 4,
    stages: fractionStages,
    assets: [
      imageAsset("content_fraction_001", "hero", null),
      imageAsset("content_fraction_001", "stage_1", "stage_fraction_1"),
      imageAsset("content_fraction_001", "stage_2", "stage_fraction_2"),
      imageAsset("content_fraction_001", "stage_3", "stage_fraction_3"),
      imageAsset("content_fraction_001", "stage_4_realtime", "stage_fraction_4"),
    ],
    briefJson: { strategy: "정적 1~3단계와 4단계 realtime teach-back" },
    teacherReviewSummary: "분모/분자 위치 혼동을 줄이기 위해 전체 수를 먼저 세는 흐름입니다.",
    approvedByUserId: teacher.id,
    approvedAt: now,
    publishedAt: now,
  },
];

function getStudent(studentId: string): StudentProfile {
  const student = students.find((item) => item.id === studentId);
  if (!student) throw new Error(`Unknown dev student: ${studentId}`);
  return student;
}

function getMission(contentId: string): MissionContent {
  const mission = missions.find((item) => item.id === contentId && item.status === "published");
  if (!mission) throw new Error(`Unknown dev mission: ${contentId}`);
  return mission;
}

export const devAdapter: ApiAdapter = {
  async demoLogin(payload) {
    return {
      user: {
        ...teacher,
        role: payload.role,
        email: payload.email ?? teacher.email,
      },
      session: {
        accessToken: "dev-teacher-token",
        expiresAt: "2026-05-02T12:00:00.000Z",
      },
    } satisfies DemoLoginResponse;
  },

  async studentAccess(payload) {
    const student = payload.accessCode === "LIFE-BUS" ? getStudent("student_life_bus") : getStudent("student_learning_fraction");
    return {
      student,
      session: {
        accessToken: `dev-student-token-${student.id}`,
        expiresAt: "2026-05-02T12:00:00.000Z",
      },
    } satisfies StudentAccessResponse;
  },

  async getContextMe() {
    return { user: teacher, organization, mode: "demo_seed" };
  },

  async getTeacherStudents() {
    return students.map<StudentListItem>((student) => {
      const school = student.schoolCode ? schools[student.schoolCode] : undefined;
      const latestMission = missions.find((mission) => mission.studentId === student.id);

      return {
        studentId: student.id,
        displayName: student.displayName,
        grade: student.grade,
        schoolName: school?.name,
        studentType: student.studentType,
        primaryNeed: student.primaryNeed,
        caseStatus: "open",
        latestContentStatus: latestMission?.status ?? "none",
        nextSessionSuggestion:
          student.studentType === "learning_focus" ? "분모/분자 위치를 짧게 재확인" : "도움 요청 문장 1개 말하기",
      };
    });
  },

  async getTeacherStudent(studentId) {
    const student = getStudent(studentId);
    const schoolContext = student.schoolCode ? publicContexts[student.schoolCode] : undefined;
    const recentContents = missions.filter((mission) => mission.studentId === studentId);

    return {
      profile: student,
      schoolContext,
      openCase: {
        id: student.studentType === "learning_focus" ? "case_learning_fraction" : "case_life_bus",
        studentId: student.id,
        ownerTeacherId: teacher.id,
        caseStatus: "open",
        currentGoal: student.primaryNeed,
        openedAt: now,
      },
      memoryCard: {
        id: `memory_${student.id}`,
        studentId: student.id,
        caseId: student.studentType === "learning_focus" ? "case_learning_fraction" : "case_life_bus",
        version: 1,
        learningProblemTypes: student.studentType === "learning_focus" ? ["concept_misunderstanding"] : ["sequence_planning"],
        recent4wResponseJson: { summary: "seed read model" },
        emotionalStateNote: "첫 문제에서 성공 경험을 먼저 제공합니다.",
        effectiveExplanationStyles: ["visual_example", "short_steps"],
        frequentBlockingUnits: student.studentType === "learning_focus" ? ["fractions"] : ["daily_route"],
        guardianCooperationStatus: "normal",
        nextSessionCautions: ["진단 표현 없이 학습 행동만 기록"],
        teacherVerifiedAt: now,
        status: "active",
      },
      weeklyRecords: [
        {
          id: `note_${student.id}_001`,
          caseId: student.studentType === "learning_focus" ? "case_learning_fraction" : "case_life_bus",
          authorId: teacher.id,
          noteType: "session",
          body: "시각 자료에 반응이 좋고 짧은 단계 안내가 필요합니다.",
          visibility: "teacher_only",
          createdAt: now,
        },
      ],
      monthlySummary: { growth: "seed summary", stillBlocking: ["짧은 선택지 유지"] },
      recentContents,
      plannerItems: [
        {
          id: `planner_${student.id}_next`,
          studentId: student.id,
          caseId: student.studentType === "learning_focus" ? "case_learning_fraction" : "case_life_bus",
          periodType: "next_session",
          goalText: student.primaryNeed,
          checklistJson: { checks: ["정적 콘텐츠 확인", "4단계 realtime 진입"] },
          status: "planned",
        },
      ],
      publicContextSummary: { schoolCode: student.schoolCode, sources: ["seed_snapshot"] },
    } satisfies StudentCaseFile;
  },

  async getSchoolContext(schoolId) {
    const context = publicContexts[schoolId];
    if (!context) throw new Error(`Unknown dev school context: ${schoolId}`);
    return context;
  },

  async getTodayStudentMissions() {
    return missions.map<StudentMissionSummary>((mission) => {
      const hero = mission.assets.find((asset) => asset.assetRole === "hero");
      return {
        contentId: mission.id,
        title: mission.title,
        contentType: mission.contentType,
        totalSteps: mission.totalSteps,
        heroImageUrl: hero?.previewUrl,
        status: "published",
      };
    });
  },

  async getStudentMission(contentId) {
    return getMission(contentId);
  },

  async getReviewableContent(contentId) {
    return getMission(contentId);
  },

  async createRealtimeSession(contentId, stageId, payload) {
    const mission = getMission(contentId);
    const stage = mission.stages.find((item) => item.id === stageId);
    if (!stage || stage.step !== 4 || !stage.realtimeSpec) {
      throw new Error("Realtime session is allowed only for stage 4 with realtimeSpec.");
    }

    const asset = mission.assets.find((item) => item.id === stage.realtimeSpec?.imageAssetId);
    return {
      sessionId: `rt_session_dev_${payload.attemptId}`,
      provider: "openai",
      model: "gpt-realtime",
      clientSecret: `demo-client-secret-${payload.attemptId}`,
      expiresAt: "2026-05-02T12:10:00.000Z",
      webrtcUrl: "https://api.openai.com/v1/realtime/calls",
      practiceSpec: {
        practiceTitle: stage.realtimeSpec.practiceTitle,
        imageAssetUrl: asset?.previewUrl,
        openingLine: stage.realtimeSpec.openingLine,
        maxTurns: stage.realtimeSpec.maxTurns,
        maxDurationSec: stage.realtimeSpec.maxDurationSec,
      },
    } satisfies RealtimeSessionResponse;
  },

  async createAgentRun(payload) {
    return {
      orchestratorRunId: `agent_run_dev_${payload.studentId}`,
      sessionGoal: "seed 기반 생성 계획",
      selectedFlow:
        payload.contentType === "learning_focus"
          ? ["concept_intro", "partition_picker", "blank_fill", "realtime_teach_back"]
          : ["scenario_intro", "scene_observation", "sequence_ordering", "realtime_roleplay"],
      teacherSummary: "dev adapter preview plan",
    } satisfies AgentRunPlan;
  },
};
