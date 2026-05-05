import { getStudentContextForRoute, isStudentRuntimePreviewOnlyError } from "@/lib/student-context-source";
import { StudentPreviewOnlyNotice } from "../StudentPreviewOnlyNotice";
import { StudentStageExperience } from "./StudentStageExperience";

export default async function StudentStagePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const caseIdParam = Array.isArray(params.caseId) ? params.caseId[0] : params.caseId;
  const contentIdParam = Array.isArray(params.contentId) ? params.contentId[0] : params.contentId;
  const stepParam = Array.isArray(params.step) ? params.step[0] : params.step;
  const completeParam = Array.isArray(params.complete) ? params.complete[0] : params.complete;
  const previewParam = Array.isArray(params.preview) ? params.preview[0] : params.preview;
  const requestedStep = Number(stepParam);
  let context: Awaited<ReturnType<typeof getStudentContextForRoute>>;
  try {
    context = await getStudentContextForRoute({ caseId: caseIdParam, contentId: contentIdParam, preview: previewParam === "1" });
  } catch (error) {
    if (isStudentRuntimePreviewOnlyError(error)) {
      return <StudentPreviewOnlyNotice error={error} step={Number.isInteger(requestedStep) ? requestedStep : undefined} />;
    }
    throw error;
  }

  const maxOpenStep =
    completeParam === "1" || previewParam === "1" || context.scene.isCompleted
      ? context.scene.totalSteps
      : context.scene.currentStep;
  const initialStep =
    Number.isInteger(requestedStep) && requestedStep >= 1 && requestedStep <= maxOpenStep
      ? requestedStep
      : context.scene.currentStep;

  const caseQuery = `caseId=${encodeURIComponent(context.scene.caseId)}${
    context.scene.contentId ? `&contentId=${encodeURIComponent(context.scene.contentId)}` : ""
  }`;

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
