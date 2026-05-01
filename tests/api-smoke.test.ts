import { describe, expect, it } from "vitest";
import { buildApp } from "../src/app.js";
import { DemoStore } from "../src/data/store.js";
import { createDemoDatabase } from "../src/data/demo-data.js";

describe("api smoke", () => {
  it("runs teacher and student demo flows", async () => {
    const app = await buildApp({ demoStore: new DemoStore(createDemoDatabase()) });

    const teacherLogin = await app.inject({
      method: "POST",
      url: "/api/auth/demo-login",
      payload: { role: "teacher", email: "teacher.demo@eduyj.local" },
    });
    expect(teacherLogin.statusCode).toBe(200);
    const teacherToken = teacherLogin.json().data.session.accessToken;

    const students = await app.inject({
      method: "GET",
      url: "/api/teacher/students",
      headers: { authorization: `Bearer ${teacherToken}` },
    });
    expect(students.statusCode).toBe(200);
    expect(students.json().data).toHaveLength(2);

    const studentLogin = await app.inject({
      method: "POST",
      url: "/api/auth/student-access",
      payload: { accessCode: "STAR-001" },
    });
    expect(studentLogin.statusCode).toBe(200);
    const studentToken = studentLogin.json().data.session.accessToken;

    const today = await app.inject({
      method: "GET",
      url: "/api/student/missions/today",
      headers: { authorization: `Bearer ${studentToken}` },
    });
    expect(today.statusCode).toBe(200);
    expect(today.json().data[0].totalSteps).toBe(4);

    const start = await app.inject({
      method: "POST",
      url: "/api/student/missions/content_fraction_001/start",
      headers: { authorization: `Bearer ${studentToken}` },
    });
    expect(start.statusCode).toBe(200);
    const attemptId = start.json().data.id;

    const submit = await app.inject({
      method: "POST",
      url: "/api/student/missions/content_fraction_001/stages/stage_fraction_2/submit",
      headers: { authorization: `Bearer ${studentToken}` },
      payload: { attemptId, answer: { choiceId: "b" } },
    });
    expect(submit.statusCode).toBe(200);
    expect(submit.json().data.isCorrect).toBe(true);

    const realtime = await app.inject({
      method: "POST",
      url: "/api/student/missions/content_fraction_001/stages/stage_fraction_4/realtime-session",
      headers: { authorization: `Bearer ${studentToken}` },
      payload: { attemptId },
    });
    expect(realtime.statusCode).toBe(200);
    expect(realtime.json().data.practiceSpec.maxTurns).toBe(6);

    await app.close();
  });
});
