import { getStudentContext } from "@/lib/demo-data";
import { StudentStageExperience } from "./StudentStageExperience";

export default async function StudentStagePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const caseIdParam = Array.isArray(params.caseId) ? params.caseId[0] : params.caseId;
  const context = getStudentContext(caseIdParam);
  const stepParam = Array.isArray(params.step) ? params.step[0] : params.step;
  const completeParam = Array.isArray(params.complete) ? params.complete[0] : params.complete;
  const previewParam = Array.isArray(params.preview) ? params.preview[0] : params.preview;
  const requestedStep = Number(stepParam);
  const initialStep =
    Number.isInteger(requestedStep) && requestedStep >= 1 && requestedStep <= context.scene.totalSteps
      ? requestedStep
      : context.scene.currentStep;

  const caseQuery = `caseId=${encodeURIComponent(context.scene.caseId)}`;

  return (
    <StudentStageExperience
      context={context}
      initialStep={initialStep}
      initialMode={completeParam === "1" ? "complete" : "stage"}
      pathHref={`/student/path?${caseQuery}`}
      nextHref={`/student/path?${caseQuery}&complete=1`}
      previewMode={previewParam === "1"}
    />
  );
}
