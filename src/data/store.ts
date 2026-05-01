import { randomUUID } from "node:crypto";
import { createDemoDatabase } from "./demo-data.js";
import type { ContentAttempt, DemoDatabase, MemoryCard, RealtimePracticeSession } from "../domain/models.js";
import type { MissionContent } from "../domain/schemas.js";

export type SessionPrincipal = {
  token: string;
  kind: "user" | "student";
  id: string;
  role: string;
  studentId?: string;
  expiresAt: string;
};

export class DemoStore {
  readonly db: DemoDatabase;
  private readonly sessions = new Map<string, SessionPrincipal>();

  constructor(seed: DemoDatabase = createDemoDatabase()) {
    this.db = seed;
  }

  createUserSession(role: string, email?: string): SessionPrincipal | undefined {
    const user = this.db.users.find((candidate) => candidate.role === role && (!email || candidate.email === email));
    if (!user) return undefined;
    const session = this.createSession({ kind: "user", id: user.id, role: user.role });
    this.sessions.set(session.token, session);
    return session;
  }

  createStudentSession(accessCode: string): SessionPrincipal | undefined {
    const account = this.db.studentAccounts.find(
      (candidate) => candidate.status === "active" && candidate.accessCode === accessCode,
    );
    if (!account) return undefined;
    const session = this.createSession({
      kind: "student",
      id: account.id,
      role: "student",
      studentId: account.studentId,
    });
    this.sessions.set(session.token, session);
    return session;
  }

  getSession(token?: string): SessionPrincipal | undefined {
    if (!token) return undefined;
    return this.sessions.get(token);
  }

  listTeacherStudents(params: { studentType?: string; q?: string; teacherId?: string }) {
    const openCases = this.db.supportCases.filter(
      (supportCase) =>
        supportCase.caseStatus === "open" && (!params.teacherId || supportCase.ownerTeacherId === params.teacherId),
    );
    const openCaseByStudentId = new Map(openCases.map((supportCase) => [supportCase.studentId, supportCase]));

    return this.db.students
      .filter((student) => openCaseByStudentId.has(student.id))
      .filter((student) => !params.studentType || student.studentType === params.studentType)
      .filter((student) => !params.q || student.displayName.includes(params.q) || student.primaryNeed.includes(params.q))
      .map((student) => {
        const latestContent = this.db.missionContents.find((content) => content.studentId === student.id);
        const planner = this.db.plannerItems.find(
          (item) => item.studentId === student.id && item.periodType === "next_session" && item.status === "planned",
        );
        return {
          studentId: student.id,
          displayName: student.displayName,
          grade: student.grade,
          studentType: student.studentType,
          primaryNeed: student.primaryNeed,
          latestContentStatus: latestContent?.status ?? "none",
          nextSessionSuggestion: planner?.goalText ?? "다음 회기 목표를 설정해 주세요.",
        };
      });
  }

  getStudentCaseFile(studentId: string) {
    const student = this.db.students.find((candidate) => candidate.id === studentId);
    if (!student) return undefined;
    const openCase = this.db.supportCases.find((supportCase) => supportCase.studentId === studentId && supportCase.caseStatus === "open");
    if (!openCase) return undefined;
    const memoryCard = this.db.memoryCards.find((card) => card.studentId === studentId && card.status === "active");
    const recentContents = this.db.missionContents.filter((content) => content.studentId === studentId);
    return {
      profile: student,
      openCase,
      memoryCard,
      weeklyRecords: this.db.caseNotes.filter((note) => note.caseId === openCase.id),
      monthlySummary: {
        repeatedProblemTypes: memoryCard?.learningProblemTypes ?? [],
        growth: "seed 데모 기준 최근 수행 안정화",
        stillBlocking: memoryCard?.nextSessionCautions ?? [],
      },
      recentContents,
      plannerItems: this.db.plannerItems.filter((item) => item.studentId === studentId),
      publicContextSummary: {
        schoolCode: student.schoolCode,
        sources: this.db.publicDataSources.map((source) => source.sourceCode),
      },
    };
  }

  patchMemoryCard(studentId: string, patch: Partial<MemoryCard>) {
    const index = this.db.memoryCards.findIndex((card) => card.studentId === studentId && card.status === "active");
    if (index === -1) return undefined;
    this.db.memoryCards[index] = { ...this.db.memoryCards[index], ...patch };
    return this.db.memoryCards[index];
  }

  listPublishedMissionsForStudent(studentId: string): MissionContent[] {
    return this.db.missionContents.filter((content) => content.studentId === studentId && content.status === "published");
  }

  getPublishedMissionForStudent(studentId: string, contentId: string): MissionContent | undefined {
    return this.db.missionContents.find(
      (content) => content.id === contentId && content.studentId === studentId && content.status === "published",
    );
  }

  createAttempt(studentId: string, missionContentId: string): ContentAttempt {
    const attempt: ContentAttempt = {
      id: `attempt_${randomUUID()}`,
      studentId,
      missionContentId,
      status: "in_progress",
      currentStep: 1,
      startedAt: new Date().toISOString(),
    };
    this.db.attempts.push(attempt);
    return attempt;
  }

  getAttempt(attemptId: string): ContentAttempt | undefined {
    return this.db.attempts.find((attempt) => attempt.id === attemptId);
  }

  submitStage(params: {
    studentId: string;
    contentId: string;
    stageId: string;
    attemptId: string;
    answer: Record<string, unknown>;
  }) {
    const mission = this.getPublishedMissionForStudent(params.studentId, params.contentId);
    const stage = mission?.stages.find((candidate) => candidate.id === params.stageId);
    const attempt = this.getAttempt(params.attemptId);
    if (!mission || !stage || !attempt || attempt.studentId !== params.studentId) return undefined;
    if (stage.step === 4) {
      return { isRealtimeStage: true as const };
    }
    const result = evaluateAnswer(stage.templateJson, params.answer);
    attempt.currentStep = Math.min(4, stage.step + 1);
    this.db.activityEvents.push({
      id: `event_${randomUUID()}`,
      attemptId: attempt.id,
      studentId: params.studentId,
      stageId: stage.id,
      eventType: "answer_submitted",
      payloadJson: { answer: params.answer, isCorrect: result.isCorrect },
      occurredAt: new Date().toISOString(),
    });
    return {
      isRealtimeStage: false as const,
      isCorrect: result.isCorrect,
      feedback: result.isCorrect ? result.correctFeedback : result.wrongFeedback,
      nextStep: attempt.currentStep,
    };
  }

  createRealtimeSession(params: { studentId: string; contentId: string; stageId: string; attemptId: string }) {
    const mission = this.getPublishedMissionForStudent(params.studentId, params.contentId);
    const stage = mission?.stages.find((candidate) => candidate.id === params.stageId);
    const attempt = this.getAttempt(params.attemptId);
    if (!mission || !stage || !attempt || attempt.studentId !== params.studentId || stage.step !== 4 || !stage.realtimeSpec) {
      return undefined;
    }
    const session: RealtimePracticeSession = {
      id: `rt_session_${randomUUID()}`,
      attemptId: attempt.id,
      missionContentId: mission.id,
      stageId: stage.id,
      studentId: params.studentId,
      provider: "openai",
      model: process.env.OPENAI_REALTIME_MODEL || "gpt-realtime",
      status: "created",
      specSnapshotJson: stage.realtimeSpec,
      turnCount: 0,
      durationSec: 0,
    };
    this.db.realtimeSessions.push(session);
    return session;
  }

  saveReflection(params: { studentId: string; contentId: string; attemptId: string; reflectionChoice: string; shortText?: string }) {
    const attempt = this.getAttempt(params.attemptId);
    if (!attempt || attempt.studentId !== params.studentId || attempt.missionContentId !== params.contentId) return undefined;
    this.db.activityEvents.push({
      id: `event_${randomUUID()}`,
      attemptId: attempt.id,
      studentId: params.studentId,
      eventType: "post_practice_reflection",
      payloadJson: { reflectionChoice: params.reflectionChoice, shortText: params.shortText },
      occurredAt: new Date().toISOString(),
    });
    return { saved: true };
  }

  completeAttempt(params: { studentId: string; contentId: string; attemptId: string }) {
    const attempt = this.getAttempt(params.attemptId);
    if (!attempt || attempt.studentId !== params.studentId || attempt.missionContentId !== params.contentId) return undefined;
    attempt.status = "completed";
    attempt.currentStep = 4;
    attempt.completedAt = new Date().toISOString();
    attempt.scoreJson = { completionRate: 1 };
    return attempt;
  }

  private createSession(params: Omit<SessionPrincipal, "token" | "expiresAt">): SessionPrincipal {
    return {
      ...params,
      token: `demo.${params.kind}.${randomUUID()}`,
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 12).toISOString(),
    };
  }
}

function evaluateAnswer(templateJson: Record<string, unknown>, answer: Record<string, unknown>) {
  const correctFeedback = String(templateJson.correctFeedback ?? "좋아요.");
  const wrongFeedback = String(templateJson.wrongFeedback ?? "다시 확인해볼까요?");

  if (typeof templateJson.answer === "string") {
    return {
      isCorrect: answer.choiceId === templateJson.answer,
      correctFeedback,
      wrongFeedback,
    };
  }

  if (Array.isArray(templateJson.answer)) {
    const submitted = Array.isArray(answer.order) ? answer.order : [];
    return {
      isCorrect: JSON.stringify(submitted) === JSON.stringify(templateJson.answer),
      correctFeedback,
      wrongFeedback,
    };
  }

  if (Array.isArray(templateJson.acceptedAnswers)) {
    return {
      isCorrect: templateJson.acceptedAnswers.some((accepted) => JSON.stringify(accepted) === JSON.stringify(answer)),
      correctFeedback,
      wrongFeedback,
    };
  }

  return { isCorrect: false, correctFeedback, wrongFeedback };
}

export const store = new DemoStore();
