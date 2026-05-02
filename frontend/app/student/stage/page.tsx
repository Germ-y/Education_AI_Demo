import Link from "next/link";
import { getBackendStudentScenario } from "@/lib/scenario-data";
import { StudentStageExperience } from "./StudentStageExperience";

export default async function StudentStagePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const studentIdParam = Array.isArray(params.studentId) ? params.studentId[0] : params.studentId;
  const result = await getBackendStudentScenario(studentIdParam);

  if (result.kind === "empty") {
    return (
      <main className="grid min-h-screen place-items-center bg-[#e7edf4] px-6 text-[#1f211d]">
        <section className="max-w-xl rounded-[28px] border border-[#d8dee8] bg-white p-8 shadow-[0_24px_70px_rgba(57,78,97,0.14)]">
          <p className="text-sm font-black text-[#1f3a5f]">{result.student.displayName} · {result.student.grade}</p>
          <h1 className="mt-3 text-3xl font-black">실행할 미션 콘텐츠가 없어요</h1>
          <p className="mt-4 text-base font-bold leading-7 text-[#596157]">{result.message}</p>
          <Link href="/dashboard" className="mt-6 inline-flex rounded-[18px] bg-[#1f3a5f] px-5 py-3 text-sm font-black text-white">
            교사용 자료 만들기로 이동
          </Link>
        </section>
      </main>
    );
  }

  const context = result.context;
  const stepParam = Array.isArray(params.step) ? params.step[0] : params.step;
  const completeParam = Array.isArray(params.complete) ? params.complete[0] : params.complete;
  const previewParam = Array.isArray(params.preview) ? params.preview[0] : params.preview;
  const requestedStep = Number(stepParam);
  const initialStep =
    Number.isInteger(requestedStep) && requestedStep >= 1 && requestedStep <= context.scene.totalSteps
      ? requestedStep
      : context.scene.currentStep;

  const studentQuery = `studentId=${encodeURIComponent(result.studentId)}`;

  return (
    <StudentStageExperience
      context={context}
      initialStep={initialStep}
      initialMode={completeParam === "1" ? "complete" : "stage"}
      pathHref={`/student/path?${studentQuery}`}
      nextHref={`/student/path?${studentQuery}&complete=1`}
      previewMode={previewParam === "1"}
    />
  );
}
