import Link from "next/link";

const roles = [
  {
    href: "/dashboard",
    label: "교사용",
    title: "학생 관리 화면으로 이동",
    description: "학생 검색, 학습 진행 확인, 수업 자료 검토, 기록을 관리합니다.",
    accent: "bg-[#1f3a5f]",
  },
  {
    href: "/student",
    label: "학생용",
    title: "오늘의 학습 길로 이동",
    description: "오늘 해야 할 미션과 단계별 학습을 태블릿 화면에서 이어갑니다.",
    accent: "bg-[#27ae60]",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f6f3ea] text-[#1f211d]">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-6 py-12">
        <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <p className="text-sm font-bold text-[#2b7a78]">배움동행</p>
            <h1 className="mt-4 max-w-2xl text-5xl font-black leading-tight md:text-6xl">
              AI가 모두의 배움에 동행하겠습니다.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-[#61665c]">
              교사는 학생별 학습 흐름을 관리하고, 학생은 오늘의 미션에 집중해 학습을 이어갑니다.
            </p>
          </div>

          <div className="grid gap-4">
            {roles.map((role) => (
              <Link
                key={role.href}
                href={role.href}
                className="group rounded-[28px] border border-[#ded8c8] bg-white p-6 shadow-[0_24px_70px_rgba(57,50,34,0.10)] transition hover:-translate-y-1 hover:border-[#b9b09b]"
              >
                <div className="flex items-start justify-between gap-5">
                  <div>
                    <span className={`inline-flex rounded-full px-3 py-1 text-sm font-bold text-white ${role.accent}`}>
                      {role.label}
                    </span>
                    <h2 className="mt-5 text-3xl font-black">{role.title}</h2>
                    <p className="mt-3 max-w-md text-base leading-7 text-[#666b62]">{role.description}</p>
                  </div>
                  <span className="mt-2 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#f2efe6] text-2xl transition group-hover:bg-[#1f211d] group-hover:text-white">
                    →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
