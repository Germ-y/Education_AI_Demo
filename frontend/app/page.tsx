import Link from "next/link";
import { getContextSeed, type SeedContext } from "@/lib/api";

const teacherRole = {
  href: "/dashboard",
  label: "교사용",
  title: "학생 관리 화면으로 이동",
  description: "학습 진행 확인, 자료 생성 및 검토, 기록을 관리합니다.",
  accent: "bg-[#1f3a5f]",
};

function toStudentActivityDescription(primaryNeed: string) {
  if (primaryNeed.includes("시간 읽기 기초")) {
    return "시간 읽기 기초를 짧은 시각 단서와 2개 선택지로 익혀요.";
  }

  if (primaryNeed.includes("분수의 전체-부분 관계")) {
    return "분수의 전체-부분 관계를 단계적으로 익혀요.";
  }

  if (primaryNeed.includes("생활 상황에서 순서 확인")) {
    return "생활 상황에서 순서 확인과 도움 요청 표현을 연습해요.";
  }

  return primaryNeed.replace(/(수업|콘텐츠)이 좋겠어요\.?$/, "").trim();
}

function findLatestStudentMapping(mappings: SeedContext["mappings"], studentId: string) {
  return [...mappings]
    .filter((mapping) => mapping.studentId === studentId && mapping.status === "published")
    .sort((left, right) => toTimestamp(right.updatedAt) - toTimestamp(left.updatedAt))[0];
}

function toTimestamp(value?: string | null) {
  if (!value) return 0;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

export default async function Home() {
  const seed = await getContextSeed();
  const studentCases = seed.students.map((student) => {
    const supportCase = seed.cases.find((item) => item.studentId === student.id);
    const mapping = findLatestStudentMapping(seed.mappings, student.id);

    return {
      studentId: student.id,
      caseId: supportCase?.id,
      contentId: mapping?.contentId,
      studentName: student.displayName,
      grade: student.gradeLabel ?? student.grade,
      label: student.trackLabel ?? student.studentTypeLabel ?? (student.studentType === "learning_focus" ? "학습지원형" : "일상생활 지원형"),
      description: toStudentActivityDescription(student.primaryNeed),
    };
  });

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
              <p className="mt-3 text-base leading-7 text-[#666b62]">
                학생을 선택해 개별 학습 화면으로 이동합니다.
              </p>

              <div className="mt-5 grid gap-3">
                {studentCases.map((studentCase) => (
                  <Link
                    key={studentCase.studentId}
                    href={
                      studentCase.caseId
                        ? `/student?caseId=${encodeURIComponent(studentCase.caseId)}${
                            studentCase.contentId ? `&contentId=${encodeURIComponent(studentCase.contentId)}` : ""
                          }`
                        : `/student?studentId=${encodeURIComponent(studentCase.studentId)}`
                    }
                    className="group rounded-[18px] border border-[#dfe7d8] bg-[#f7fbf2] px-4 py-4 transition hover:-translate-y-0.5 hover:border-[#9ec391] hover:bg-white"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <p className="truncate text-lg font-black">{studentCase.studentName}</p>
                        <p className="mt-1 text-sm font-bold text-[#66705f]">
                          {studentCase.grade} · {studentCase.label}
                        </p>
                        <p className="mt-1 truncate text-xs font-bold text-[#7b8575]">{studentCase.description}</p>
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
