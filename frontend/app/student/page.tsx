import Link from "next/link";
import Image from "next/image";
import { getStudentContextForRoute } from "@/lib/student-context-source";

function StarterStar() {
  return (
    <div className="relative h-[250px] w-[278px]" aria-hidden="true">
      <div className="absolute bottom-5 left-1/2 h-7 w-40 -translate-x-1/2 rounded-full bg-black/10 blur-md" />
      <div className="absolute inset-0 animate-[starMascotFloat_4.8s_ease-in-out_infinite]">
        <Image
          src="/assets/star-mascot/without-arm-eyes.svg"
          alt=""
          fill
          sizes="278px"
          className="object-contain"
          draggable={false}
          priority
        />
        <div className="absolute inset-0 animate-[starMascotWave_2.6s_ease-in-out_infinite]">
          <Image
            src="/assets/star-mascot/arm.svg"
            alt=""
            fill
            sizes="278px"
            className="object-contain"
            draggable={false}
          />
        </div>
        <Image
          src="/assets/star-mascot/eyes.svg"
          alt=""
          fill
          sizes="278px"
          className="animate-[starMascotBlink_4.2s_ease-in-out_infinite] object-contain"
          draggable={false}
        />
      </div>
    </div>
  );
}

export default async function StudentStartPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const caseIdParam = Array.isArray(params.caseId) ? params.caseId[0] : params.caseId;
  const contentIdParam = Array.isArray(params.contentId) ? params.contentId[0] : params.contentId;
  const { student, scene } = await getStudentContextForRoute({ caseId: caseIdParam, contentId: contentIdParam });
  const theme = scene.theme;
  const nextStage = scene.stages[scene.currentStep - 1] ?? scene.stages[0];
  const caseQuery = `caseId=${encodeURIComponent(scene.caseId)}${scene.contentId ? `&contentId=${encodeURIComponent(scene.contentId)}` : ""}`;
  const pathHref = `/student/path?${caseQuery}`;
  const heroImage = scene.assets?.find((asset) => asset.assetRole === "hero" && asset.assetType === "image" && asset.url);
  const heroAudio = scene.assets?.find((asset) => asset.assetRole === "hero" && asset.assetType === "audio" && asset.url);

  return (
    <main className="relative flex h-screen overflow-hidden bg-[#e7edf4] p-4 text-[#1f211d]">
      <Link
        href="/"
        className="fixed bottom-6 right-6 z-50 rounded-full border border-[#25466f] bg-[#1f3a5f] px-5 py-3 text-base font-black text-white shadow-[0_12px_30px_rgba(31,58,95,0.25)] transition duration-200 hover:-translate-y-0.5"
      >
        홈으로
      </Link>

      <div className="m-auto">
        <div className="relative aspect-[4/3] h-[min(calc(100vh-32px),820px)] rounded-[44px] bg-[#202939] p-4 shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
          <div className="absolute bottom-5 left-1/2 h-1.5 w-24 -translate-x-1/2 rounded-full bg-white/22" />

          <div className="relative h-full overflow-hidden rounded-[30px] bg-[#fbfaf4]">
            <div className="absolute left-0 top-0 h-72 w-72 rounded-full bg-[#fff0b8]/50 blur-3xl" />
            <div
              className="absolute bottom-0 right-0 h-[420px] w-[420px] rounded-full blur-3xl"
              style={{ backgroundColor: `${theme.glow}b8` }}
            />

            <div className="relative grid h-full grid-cols-[minmax(0,0.92fr)_minmax(360px,0.72fr)] gap-10 px-14 py-12">
              <section className="flex min-h-0 flex-col justify-center">
                <div
                  className="inline-flex w-fit rounded-full border px-5 py-2 text-base font-black"
                  style={{ borderColor: theme.border, backgroundColor: theme.accentPale, color: theme.accentStrong }}
                >
                  {student.displayName} · {student.grade}
                </div>

                <p className="mt-10 text-lg font-black" style={{ color: theme.accentStrong }}>
                  오늘의 시작점
                </p>
                <h1 className="mt-3 max-w-[660px] text-6xl font-black leading-[1.08]">
                  {nextStage.title}부터 열어볼까요?
                </h1>
                <p className="mt-6 max-w-[620px] text-xl font-bold leading-9 text-[#596157]">
                  바로 문제로 뛰어들기 전에 오늘 할 미션만 짧게 보고 시작해요. 준비되면 학습하기를 눌러 길 화면으로 이동해요.
                </p>

                <div className="mt-9 flex items-center gap-4">
                  <Link
                    href={pathHref}
                    className="rounded-[22px] px-8 py-5 text-xl font-black text-white shadow-[0_18px_40px_rgba(39,174,96,0.30)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105"
                    style={{ backgroundColor: theme.accent }}
                  >
                    학습하기
                  </Link>
                  <div className="text-base font-black text-[#5f675d]">
                    <span style={{ color: theme.accentStrong }}>{scene.currentStep}</span>
                    <span className="mx-1 text-[#9aa39b]">/</span>
                    {scene.totalSteps} 단계 진행 중
                  </div>
                </div>

                <div className="mt-10 max-w-[620px]">
                  <div className="flex items-center justify-between text-sm font-black text-[#6d746c]">
                    <span>{scene.missionTitle}</span>
                    <span>
                      {scene.currentStep}/{scene.totalSteps}
                    </span>
                  </div>
                  <div className="mt-3 grid grid-cols-4 gap-3">
                    {scene.stages.map((stage) => (
                      <span
                        key={stage.step}
                        className="h-5 rounded-full shadow-inner"
                        style={{
                          backgroundColor: stage.state === "locked" ? "#dbe4d2" : theme.accent,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </section>

              <aside className="flex min-h-0 items-center justify-center">
                <div className="relative w-full max-w-[430px]">
                  {heroImage?.url ? (
                    <div
                      className="overflow-hidden rounded-[28px] border bg-white p-3 shadow-[0_20px_54px_rgba(57,78,97,0.10)]"
                      style={{ borderColor: theme.border }}
                    >
                      <Image
                        src={heroImage.url}
                        alt={heroImage.alt}
                        width={720}
                        height={480}
                        className="h-[240px] w-full rounded-[20px] object-cover"
                        unoptimized
                        priority
                      />
                      {heroAudio?.url && (
                        <div className="mt-3">
                          <audio className="w-full" src={heroAudio.url} controls preload="auto" />
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="mx-auto flex justify-center">
                      <StarterStar />
                    </div>
                  )}
                  <div
                    className="mt-3 rounded-[26px] border px-7 py-6 shadow-[0_20px_54px_rgba(57,78,97,0.10)]"
                    style={{ borderColor: theme.border, backgroundColor: `${theme.accentPale}f4` }}
                  >
                    <p className="text-sm font-black" style={{ color: theme.accentStrong }}>
                      오늘의 미션
                    </p>
                    <h2 className="mt-2 text-4xl font-black leading-tight">{scene.missionTitle}</h2>
                    <p className="mt-4 text-lg font-bold leading-8 text-[#596157]">{nextStage.subtitle}</p>
                  </div>
                </div>
              </aside>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
