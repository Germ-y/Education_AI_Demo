import Link from "next/link";
import Image from "next/image";
import { getStudentContext, type SceneTheme } from "@/lib/demo-data";

function StarMascot() {
  return (
    <div className="relative h-[154px] w-[172px]" aria-hidden="true">
      <div className="absolute bottom-3 left-1/2 h-4 w-24 -translate-x-1/2 rounded-full bg-black/10 blur-md" />
      <div className="absolute inset-0 animate-[starMascotFloat_4.8s_ease-in-out_infinite]">
        <Image
          src="/assets/star-mascot/without-arm-eyes.svg"
          alt=""
          fill
          sizes="172px"
          className="object-contain"
          draggable={false}
          priority
        />
        <div className="absolute inset-0 animate-[starMascotWave_2.6s_ease-in-out_infinite]">
          <Image
            src="/assets/star-mascot/arm.svg"
            alt=""
            fill
            sizes="172px"
            className="object-contain"
            draggable={false}
          />
        </div>
        <Image
          src="/assets/star-mascot/eyes.svg"
          alt=""
          fill
          sizes="172px"
          className="animate-[starMascotBlink_4.2s_ease-in-out_infinite] object-contain"
          draggable={false}
        />
      </div>
    </div>
  );
}

function StageNode({
  step,
  state,
  theme,
}: {
  step: number;
  state: "done" | "current" | "locked";
  theme: SceneTheme;
}) {
  const nodeStyle =
    state === "current"
      ? { borderColor: theme.highlight, backgroundColor: theme.accent, color: "#ffffff" }
      : state === "done"
        ? { borderColor: theme.border, backgroundColor: theme.accentSoft, color: theme.accentStrong }
        : undefined;

  return (
    <div
      className={`flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-full border-[5px] text-xl font-black shadow-[0_12px_26px_rgba(74,85,104,0.16)] transition duration-300 group-hover:-translate-y-1 group-hover:scale-105 ${
        state === "locked"
          ? "border-[#e2e4e6] bg-[#c8ccd0] text-white"
          : ""
      }`}
      style={nodeStyle}
    >
      {state === "done" ? "✓" : step}
    </div>
  );
}

export default async function StudentHomePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const caseIdParam = Array.isArray(params.caseId) ? params.caseId[0] : params.caseId;
  const { student, scene } = getStudentContext(caseIdParam);
  const completeParam = Array.isArray(params.complete) ? params.complete[0] : params.complete;
  const isComplete = completeParam === "1";
  const theme = scene.theme;
  const caseQuery = `caseId=${encodeURIComponent(scene.caseId)}`;

  return (
    <main className="relative flex h-screen overflow-hidden bg-[#e7edf4] p-4 text-[#1f211d]">
      <Link
        href="/"
        className="fixed bottom-6 right-6 z-50 rounded-full border border-[#25466f] bg-[#1f3a5f] px-5 py-3 text-base font-black text-white shadow-[0_12px_30px_rgba(31,58,95,0.25)]"
      >
        데모 홈
      </Link>
      <div className="m-auto">
        <div className="relative aspect-[4/3] h-[min(calc(100vh-32px),820px)] rounded-[44px] bg-[#202939] p-4 shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
          <div className="absolute bottom-5 left-1/2 h-1.5 w-24 -translate-x-1/2 rounded-full bg-white/22" />

          <div className="h-full overflow-hidden rounded-[30px] bg-[#fbfaf4]">
            <header className="flex h-[92px] items-center justify-between gap-5 border-b border-[#efe7d7] bg-[#fbfaf4]/95 px-10">
              <div className="flex min-w-0 items-center gap-4">
                <Link
                  href={`/student?${caseQuery}`}
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border text-xl font-black shadow-sm transition duration-200 hover:-translate-y-0.5 hover:scale-105 hover:shadow-[0_12px_26px_rgba(57,78,97,0.16)]"
                  style={{ borderColor: theme.border, backgroundColor: theme.accentPale, color: theme.accent }}
                  aria-label="학생 시작 화면으로 돌아가기"
                >
                  ←
                </Link>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-[#6d746c]">
                    {student.displayName} · {student.grade}
                  </p>
                  <h1 className="truncate text-2xl font-black">{scene.missionTitle}</h1>
                </div>
              </div>
              <div className="h-10 w-10 shrink-0" aria-hidden="true" />
            </header>

            <section className="relative grid h-[calc(100%-92px)] grid-cols-[300px_minmax(0,1fr)] gap-8 px-12 py-8">
              <div className="absolute left-0 top-16 h-64 w-64 rounded-full bg-[#fff0b8]/45 blur-3xl" />
              <div
                className="absolute bottom-0 right-0 h-72 w-72 rounded-full blur-3xl"
                style={{ backgroundColor: `${theme.glow}88` }}
              />
              <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden" aria-hidden="true">
                <div
                  className="absolute right-[8%] top-[10%] h-16 w-16 opacity-85"
                  style={{
                    backgroundColor: theme.highlight,
                    clipPath:
                      "polygon(50% 0%, 61% 34%, 97% 35%, 68% 55%, 79% 91%, 50% 69%, 21% 91%, 32% 55%, 3% 35%, 39% 34%)",
                  }}
                />
                <div className="absolute left-[44%] bottom-[13%] grid grid-cols-3 gap-2 opacity-70">
                  {[0, 1, 2, 3, 4, 5].map((dot) => (
                    <span
                      key={dot}
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: dot % 2 === 0 ? theme.accent : theme.highlight }}
                    />
                  ))}
                </div>
                <div
                  className="absolute right-[30%] bottom-[4%] h-10 w-28 rounded-full opacity-60"
                  style={{ backgroundColor: theme.highlight }}
                />
              </div>

              <aside className="relative z-[1] flex translate-x-3 flex-col justify-center">
                <p className="text-base font-black">{student.displayName}아,</p>
                <h2 className="mt-2 max-w-[270px] text-3xl font-black leading-tight">
                  {scene.pathHeadline}
                </h2>
                <p className="mt-4 max-w-[260px] text-sm font-bold leading-6 text-[#676b62]">
                  {scene.pathDescription}
                </p>
                <div className="mt-5">
                  <StarMascot />
                </div>
                <div
                  className="mt-5 max-w-[270px] rounded-[22px] border p-4 shadow-sm"
                  style={{ borderColor: theme.border, backgroundColor: `${theme.accentPale}f2` }}
                >
                  <p className="text-sm font-black" style={{ color: theme.accent }}>
                    오늘의 미션
                  </p>
                  <h3 className="mt-1 text-xl font-black">{scene.missionTitle}</h3>
                  <div className="mt-4 grid grid-cols-4 gap-2">
                    {scene.stages.map((stage) => (
                      <div
                        key={stage.step}
                        className={`h-4 rounded-full shadow-inner ${
                            isComplete || stage.step <= scene.currentStep ? "" : "bg-[#dbe4d2]"
                          }`}
                          style={isComplete || stage.step <= scene.currentStep ? { backgroundColor: theme.accent } : undefined}
                        />
                    ))}
                  </div>
                </div>
              </aside>

              <section className="relative z-[1] my-auto h-[88%] min-h-0 overflow-visible">
                <svg
                  className="absolute inset-0 h-full w-full"
                  viewBox="0 0 760 500"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <path
                    d="M175 105 C 320 72, 505 128, 492 220 C 476 314, 252 300, 268 370 C 287 450, 520 420, 555 442"
                    fill="none"
                    stroke={theme.path}
                    strokeLinecap="round"
                    strokeWidth="58"
                  />
                  <path
                    d="M175 105 C 320 72, 505 128, 492 220 C 476 314, 252 300, 268 370 C 287 450, 520 420, 555 442"
                    fill="none"
                    stroke={theme.pathLight}
                    strokeLinecap="round"
                    strokeWidth="18"
                  />
                </svg>
                <div className="absolute left-[18%] top-[14%] h-10 w-24 rounded-full bg-[#dbe8c5]" />
                <div className="absolute bottom-[18%] left-[22%] h-10 w-24 rounded-full bg-[#dbe8c5]" />

                {scene.stages.map((mission, index) => {
                  const point = {
                    x: mission.x,
                    y: mission.y,
                    side: index % 2 === 0 ? "right" : "left",
                  } as const;
                  const cardTone =
                    !isComplete && mission.state === "current"
                      ? "border"
                      : isComplete || mission.state === "done"
                        ? "bg-white/90"
                        : "bg-white/78 text-[#777d83]";
                  const cardStyle =
                    !isComplete && mission.state === "current"
                      ? { borderColor: theme.border, backgroundColor: theme.accentSoft }
                      : undefined;
                  const nodeState = isComplete ? "done" : mission.state;

                  return (
                    <Link
                      key={mission.step}
                      href={
                        mission.state === "locked" && !isComplete
                          ? `/student/path?${caseQuery}`
                          : `/student/stage?${caseQuery}&step=${mission.step}`
                      }
                      className="group absolute z-10 flex -translate-y-1/2 items-center gap-3 transition duration-300 hover:z-30"
                      style={{ left: point.x, top: point.y }}
                    >
                      {point.side === "left" && (
                        <div
                          className={`w-[172px] rounded-[18px] px-4 py-3 shadow-[0_14px_35px_rgba(40,47,35,0.10)] transition duration-300 group-hover:-translate-y-1 group-hover:shadow-[0_18px_38px_rgba(40,47,35,0.16)] ${cardTone}`}
                          style={cardStyle}
                        >
                          <p className="text-base font-black leading-5">{mission.title}</p>
                          <p className="mt-1 text-xs font-bold leading-5 text-[#6d746c]">{mission.subtitle}</p>
                        </div>
                      )}
                      <StageNode step={mission.step} state={nodeState} theme={theme} />
                      {point.side === "right" && (
                        <div
                          className={`w-[172px] rounded-[18px] px-4 py-3 shadow-[0_14px_35px_rgba(40,47,35,0.10)] transition duration-300 group-hover:-translate-y-1 group-hover:shadow-[0_18px_38px_rgba(40,47,35,0.16)] ${cardTone}`}
                          style={cardStyle}
                        >
                          <p className="text-base font-black leading-5">{mission.title}</p>
                          <p className="mt-1 text-xs font-bold leading-5 text-[#6d746c]">{mission.subtitle}</p>
                        </div>
                      )}
                    </Link>
                  );
                })}
              </section>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
