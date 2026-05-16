import Link from "next/link";
import type { StudentRuntimePreviewOnlyError } from "@/lib/student-context-source";

export function StudentPreviewOnlyNotice(_props: {
  error: StudentRuntimePreviewOnlyError;
  step?: number;
}) {
  void _props;

  return (
    <main className="grid min-h-screen place-items-center bg-[#e7edf4] p-6 text-[#172033]">
      <section className="w-full max-w-[640px] rounded-xl border border-[#d8dee8] bg-white p-6 shadow-[0_24px_70px_rgba(15,23,42,0.16)]">
        <p className="text-sm font-black text-[#64748b]">학생 런타임 차단</p>
        <h1 className="mt-2 text-2xl font-black leading-tight break-keep">
          아직 학생에게 배포되지 않은 자료입니다.
        </h1>
        <p className="mt-3 text-sm font-bold leading-6 text-[#475569]">
          검토 중인 자료는 대시보드의 제안 검토 화면에서 확인합니다. 학생 화면에서는 배포 완료 상태의 콘텐츠만 실행됩니다.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="rounded-md border border-[#cbd5e1] bg-white px-5 py-3 text-sm font-black text-[#334155]"
          >
            대시보드로 이동
          </Link>
        </div>
      </section>
    </main>
  );
}
