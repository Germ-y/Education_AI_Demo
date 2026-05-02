import { getPrimaryStudentContext } from "@/lib/demo-data";
import { StudentStageExperience } from "./StudentStageExperience";

export default async function StudentStagePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const context = getPrimaryStudentContext();
  const params = await searchParams;
  const stepParam = Array.isArray(params.step) ? params.step[0] : params.step;
  const completeParam = Array.isArray(params.complete) ? params.complete[0] : params.complete;
  const previewParam = Array.isArray(params.preview) ? params.preview[0] : params.preview;
  const requestedStep = Number(stepParam);
  const initialStep =
    Number.isInteger(requestedStep) && requestedStep >= 1 && requestedStep <= context.scene.totalSteps
      ? requestedStep
      : context.scene.currentStep;

  return (
    <StudentStageExperience
      context={context}
      initialStep={initialStep}
      initialMode={completeParam === "1" ? "complete" : "stage"}
      nextHref="/student/path?complete=1"
      previewMode={previewParam === "1"}
    />
  );
}
