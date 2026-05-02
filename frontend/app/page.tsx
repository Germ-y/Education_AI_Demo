import Link from "next/link";
import { getStudentCaseSummaries } from "@/lib/demo-data";

const teacherRole = {
  href: "/dashboard",
  label: "교사용",
  title: "학생 관리 화면으로 이동",
  description: "학습 진행 확인, 자료 생성 및 검토, 기록을 관리합니다.",
  accent: "bg-[#1f3a5f]",
};

export default function Home() {
  const studentCases = getStudentCaseSummaries();

  return (
    <main className="min-h-screen bg-[#f6f3ea] text-[#1f211d]">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-6 py-12">
        <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <p className="text-sm font-bold text-[#2b7a78]">배움 동행</p>
            <h1 className="mt-4 max-w-2xl text-5xl font-black leading-tight md:text-6xl">
              AI가 모두의 배움을 동행합니다
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-[#61665c]">
              교사는 학생별 학습 흐름을 관리하고, 학생은 오늘의 미션에 집중해 학습을 이어갑니다.
            </p>
          </div>

          <div className="grid gap-4">
            <Link
              href={teacherRole.href}
              className="group rounded-[28px] border border-[#ded8c8] bg-white p-6 shadow-[0_24px_70px_rgba(57,50,34,0.10)] transition hover:-translate-y-1 hover:border-[#b9b09b]"
            >
              <div className="flex items-start justify-between gap-5">
                <div>
                  <span className={`inline-flex rounded-full px-3 py-1 text-sm font-bold text-white ${teacherRole.accent}`}>
                    {teacherRole.label}
                  </span>
                  <h2 className="mt-5 text-3xl font-black">{teacherRole.title}</h2>
                  <p className="mt-3 max-w-md text-base leading-7 text-[#666b62]">{teacherRole.description}</p>
                </div>
                <span className="mt-2 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#f2efe6] text-2xl transition group-hover:bg-[#1f211d] group-hover:text-white">
                  →
                </span>
              </div>
            </Link>

            <div className="rounded-[28px] border border-[#ded8c8] bg-white p-6 shadow-[0_24px_70px_rgba(57,50,34,0.10)]">
              <span className="inline-flex rounded-full bg-[#27ae60] px-3 py-1 text-sm font-bold text-white">
                학생용
              </span>
              <h2 className="mt-5 text-3xl font-black">학생별 학습 화면으로 이동</h2>
              <p className="mt-3 max-w-md text-base leading-7 text-[#666b62]">
                세 명의 학생 중 한 명을 골라 각자 다른 미션 화면을 확인합니다.
              </p>

              <div className="mt-5 grid gap-3">
                {studentCases.map((studentCase) => (
                  <Link
                    key={studentCase.caseId}
                    href={`/student?caseId=${encodeURIComponent(studentCase.caseId)}`}
                    className="group rounded-[18px] border border-[#dfe7d8] bg-[#f7fbf2] px-4 py-4 transition hover:-translate-y-0.5 hover:border-[#9ec391] hover:bg-white"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <p className="truncate text-lg font-black">{studentCase.studentName}</p>
                        <p className="mt-1 text-sm font-bold text-[#66705f]">
                          {studentCase.grade} · {studentCase.label}
                        </p>
                        <p className="mt-2 line-clamp-2 text-sm font-semibold leading-6 text-[#4f5b4b]">
                          {studentCase.title}
                        </p>
                      </div>
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-xl transition group-hover:bg-[#27ae60] group-hover:text-white">
                        →
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
