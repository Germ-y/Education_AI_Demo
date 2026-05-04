"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  completeRealtimeSession,
  completeStudentMission,
  createRealtimeSession,
  saveStudentMissionEvent,
  saveStudentMissionReflection,
  saveRealtimeSessionEvent,
  startStudentMission,
  studentAccess,
  submitStudentMissionStage,
} from "@/lib/api";
import type { SceneTheme, SceneVisual, StageQuestion, StudentContext } from "@/lib/student-scene-types";

function MiniStar() {
  return (
    <div className="relative h-20 w-20 shrink-0" aria-hidden="true">
      <Image
        src="/assets/complete-star/effect.svg"
        alt=""
        fill
        sizes="80px"
        className="animate-[completeStarEffectPop_2.2s_ease-in-out_infinite] object-contain"
        draggable={false}
        priority
      />
      <Image
        src="/assets/complete-star/without-eyes-effect.svg"
        alt=""
        fill
        sizes="80px"
        className="object-contain"
        draggable={false}
        priority
      />
      <Image
        src="/assets/complete-star/eyes.svg"
        alt=""
        fill
        sizes="80px"
        className="animate-[hintStarBlink_4.2s_ease-in-out_infinite] object-contain"
        draggable={false}
        priority
      />
    </div>
  );
}

function ProgressTrail({
  stages,
  activeStep,
  completedSteps,
  isFinished,
  theme,
}: {
  stages: StudentContext["scene"]["stages"];
  activeStep: number;
  completedSteps: number[];
  isFinished: boolean;
  theme: SceneTheme;
}) {
  return (
    <div className="flex items-center gap-2">
      {stages.map((stage, index) => {
        const isDone = isFinished || completedSteps.includes(stage.step);
        const isActive = !isFinished && stage.step === activeStep;

        return (
          <div key={stage.step} className="flex items-center gap-2">
            <span
              className={`flex h-10 w-10 items-center justify-center rounded-full border-[4px] text-sm font-black shadow-[0_8px_16px_rgba(74,85,104,0.12)] ${
                isDone || isActive ? "" : "border-[#e2e4e6] bg-[#c8ccd0] text-white"
              }`}
              style={
                isDone
                  ? { borderColor: theme.border, backgroundColor: theme.accentSoft, color: theme.accentStrong }
                  : isActive
                    ? { borderColor: theme.highlight, backgroundColor: theme.accent, color: "#ffffff" }
                    : undefined
              }
            >
              {isDone ? "✓" : stage.step}
            </span>
            {index < stages.length - 1 && (
              <span
                className={`h-2 w-8 rounded-full ${isDone ? "" : "bg-[#e3e7df]"}`}
                style={isDone ? { backgroundColor: theme.accent } : undefined}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function EmotionVisual({ visual }: { visual: SceneVisual }) {
  return (
    <div className="relative grid h-full min-h-[300px] grid-cols-2 gap-4 overflow-hidden rounded-[24px] border border-[#d9ebc9] bg-[#f4fbef] p-5 shadow-[inset_0_-12px_0_rgba(39,174,96,0.08)]">
      {visual.segments.map((segment, index) => (
        <div
          key={segment.label}
          className={`relative flex flex-col items-center justify-center rounded-[24px] border bg-white/88 p-5 text-center shadow-sm ${
            index === visual.activeIndex ? "border-[#58b957] ring-8 ring-[#dff2de]" : "border-white/70"
          }`}
        >
          <div
            className="relative h-20 w-20 rounded-full shadow-[inset_0_-8px_0_rgba(0,0,0,0.08)]"
            style={{ backgroundColor: segment.color }}
          >
            <span className="absolute left-5 top-7 h-2.5 w-2.5 rounded-full bg-[#25312a]" />
            <span className="absolute right-5 top-7 h-2.5 w-2.5 rounded-full bg-[#25312a]" />
            <span className="absolute left-1/2 top-11 h-4 w-9 -translate-x-1/2 rounded-b-full border-b-4 border-[#25312a]" />
          </div>
          <p className="mt-4 text-2xl font-black">{segment.label}</p>
          <p className="mt-1 text-sm font-bold text-[#6d746c]">{segment.caption}</p>
        </div>
      ))}
    </div>
  );
}

function FractionVisual({ visual, compact = false }: { visual: SceneVisual; compact?: boolean }) {
  return (
    <div
      className={`relative flex h-full items-center justify-center overflow-hidden rounded-[24px] border border-[#ead9b8] bg-[#f7d88d] p-5 shadow-[inset_0_-12px_0_rgba(166,105,38,0.10)] ${
        compact ? "min-h-[250px]" : "min-h-[300px]"
      }`}
    >
      <div className="absolute left-8 top-8 h-12 w-28 rounded-full bg-white/28" />
      <div className="absolute bottom-10 right-10 h-10 w-24 rounded-full bg-[#dbe8c5]/70" />
      <div
        className={`relative grid aspect-square grid-cols-2 gap-2 rounded-full border-[14px] border-[#d7832e] bg-[#f6b64a] p-3 shadow-[0_22px_45px_rgba(115,72,29,0.20),inset_0_10px_24px_rgba(255,255,255,0.25)] ${
          compact ? "w-[min(100%,340px)]" : "w-[min(100%,460px)]"
        }`}
      >
        {visual.segments.map((segment, index) => (
          <div
            key={segment.label}
            className={`relative overflow-hidden ${
              index === 0 ? "rounded-tl-full" : ""
            } ${index === 1 ? "rounded-tr-full" : ""} ${index === 2 ? "rounded-bl-full" : ""} ${
              index === 3 ? "rounded-br-full" : ""
            } ${index === visual.activeIndex ? "ring-8 ring-[#fff176] ring-offset-2 ring-offset-[#f6b64a]" : ""}`}
            style={{ backgroundColor: segment.color }}
          >
            <span className="absolute left-1/3 top-1/3 h-8 w-8 rounded-full bg-[#d64f2a]" />
            <span className="absolute bottom-1/4 right-1/4 h-5 w-5 rounded-full bg-[#3c8c45]" />
            {index === visual.activeIndex && <span className="absolute inset-4 rounded-br-full border-4 border-white/60" />}
          </div>
        ))}
      </div>
    </div>
  );
}

function PlannerVisual({ visual }: { visual: SceneVisual }) {
  return (
    <div className="relative flex h-full min-h-[300px] flex-col justify-center overflow-hidden rounded-[24px] border border-[#dce5ec] bg-[#eef5ff] p-6 shadow-[inset_0_-12px_0_rgba(33,90,154,0.08)]">
      <div className="grid gap-4">
        {visual.segments.map((segment, index) => (
          <div
            key={segment.label}
            className={`flex items-center gap-5 rounded-[24px] border bg-white/92 p-5 shadow-sm ${
              index === visual.activeIndex ? "border-[#58b957] ring-8 ring-[#dff2de]" : "border-white"
            }`}
          >
            <span
              className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-xl font-black text-[#1f211d]"
              style={{ backgroundColor: segment.color }}
            >
              {index + 1}
            </span>
            <div>
              <p className="text-2xl font-black">{segment.label}</p>
              <p className="mt-1 text-sm font-bold text-[#6d746c]">{segment.caption}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ClockVisual({ visual, compact = false }: { visual: SceneVisual; compact?: boolean }) {
  return (
    <div
      className={`grid h-full overflow-hidden rounded-[24px] border border-[#ead9b8] bg-[#fff6d9] p-5 shadow-[inset_0_-12px_0_rgba(166,105,38,0.10)] ${
        compact ? "min-h-[250px] grid-cols-[minmax(170px,0.78fr)_minmax(190px,1fr)] gap-4" : "min-h-[300px] grid-cols-[minmax(240px,0.82fr)_minmax(260px,1fr)] gap-5"
      }`}
    >
      <div className="relative flex min-h-0 items-center justify-center">
        <div className="relative aspect-square w-[min(100%,360px)] rounded-full border-[12px] border-[#d28a34] bg-white shadow-[0_22px_45px_rgba(115,72,29,0.18),inset_0_10px_24px_rgba(255,255,255,0.35)]">
          {[
            ["12", "left-1/2 top-5 -translate-x-1/2"],
            ["3", "right-6 top-1/2 -translate-y-1/2"],
            ["6", "bottom-5 left-1/2 -translate-x-1/2"],
            ["9", "left-6 top-1/2 -translate-y-1/2"],
          ].map(([label, position]) => (
            <span key={label} className={`absolute ${position} text-2xl font-black text-[#8a5a00]`}>
              {label}
            </span>
          ))}
          <span className="absolute left-1/2 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#1f3a5f]" />
          <span className="absolute left-1/2 top-1/2 h-3 w-[34%] origin-left -translate-y-1/2 rounded-full bg-[#1f3a5f] shadow-sm" />
          <span className="absolute left-1/2 top-1/2 h-[34%] w-2 origin-bottom -translate-x-1/2 -translate-y-full rounded-full bg-[#58b957] shadow-sm" />
          <span className="absolute bottom-9 left-1/2 -translate-x-1/2 rounded-full bg-[#fff3c4] px-3 py-1 text-xs font-black text-[#8a5a00]">
            짧은 바늘 먼저
          </span>
        </div>
      </div>
      <div className="grid min-h-0 content-center gap-3">
        {visual.segments.map((segment, index) => (
          <div
            key={`${segment.label}-${index}`}
            className={`rounded-[18px] border bg-white/90 px-4 py-3 shadow-sm ${
              index === visual.activeIndex ? "border-[#58b957] ring-4 ring-[#dff2de]" : "border-white/80"
            }`}
          >
            <p className="text-lg font-black leading-6 break-keep">{segment.label}</p>
            <p className="mt-1 text-xs font-bold leading-5 text-[#6d746c] break-keep">{segment.caption}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TransitVisual({ visual, compact = false }: { visual: SceneVisual; compact?: boolean }) {
  return (
    <div
      className={`grid h-full overflow-hidden rounded-[24px] border border-[#cfe4d3] bg-[#eef8f0] p-5 shadow-[inset_0_-12px_0_rgba(39,174,96,0.08)] ${
        compact ? "min-h-[250px] grid-cols-[minmax(190px,1fr)_minmax(170px,0.78fr)] gap-4" : "min-h-[300px] grid-cols-[minmax(260px,1fr)_minmax(240px,0.8fr)] gap-5"
      }`}
    >
      <div className="relative min-h-0 overflow-hidden rounded-[22px] border border-[#dce5ec] bg-[#dff1ff] p-5 shadow-sm">
        <div className="absolute inset-x-0 bottom-0 h-20 bg-[#c7dfb9]" />
        <div className="absolute bottom-16 left-8 h-24 w-14 rounded-t-full bg-[#1f3a5f] shadow-sm">
          <span className="absolute left-1/2 top-4 h-10 w-10 -translate-x-1/2 rounded-full bg-white text-center text-sm font-black leading-10 text-[#1f3a5f]">
            BUS
          </span>
        </div>
        <div className="absolute bottom-[76px] right-8 h-36 w-[58%] rounded-[24px] border-4 border-[#1f3a5f] bg-[#ffd36b] shadow-[0_18px_32px_rgba(31,58,95,0.18)]">
          <div className="absolute left-5 top-5 right-5 grid grid-cols-3 gap-3">
            <span className="h-12 rounded-lg bg-white/85" />
            <span className="h-12 rounded-lg bg-white/85" />
            <span className="h-12 rounded-lg bg-white/85" />
          </div>
          <span className="absolute bottom-5 left-7 h-8 w-8 rounded-full bg-[#1f3a5f]" />
          <span className="absolute bottom-5 right-7 h-8 w-8 rounded-full bg-[#1f3a5f]" />
          <span className="absolute bottom-16 left-1/2 -translate-x-1/2 rounded-full bg-white px-4 py-1 text-xl font-black text-[#1f3a5f]">
            21
          </span>
        </div>
        <div className="absolute left-8 top-8 rounded-[18px] bg-white/92 px-4 py-3 shadow-sm">
          <p className="text-xs font-black text-[#16803c]">센터 가는 길</p>
          <p className="mt-1 text-lg font-black text-[#1f211d]">번호를 먼저 봐요</p>
        </div>
      </div>
      <div className="grid min-h-0 content-center gap-3">
        {visual.segments.map((segment, index) => (
          <div
            key={`${segment.label}-${index}`}
            className={`rounded-[18px] border bg-white/90 px-4 py-3 shadow-sm ${
              index === visual.activeIndex ? "border-[#58b957] ring-4 ring-[#dff2de]" : "border-white/80"
            }`}
          >
            <p className="text-lg font-black leading-6 break-keep">{segment.label}</p>
            <p className="mt-1 text-xs font-bold leading-5 text-[#6d746c] break-keep">{segment.caption}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function LearningVisual({ visual, compact = false }: { visual: SceneVisual; compact?: boolean }) {
  if (visual.kind === "emotion") return <EmotionVisual visual={visual} />;
  if (visual.kind === "planner") return <PlannerVisual visual={visual} />;
  if (visual.kind === "clock") return <ClockVisual visual={visual} compact={compact} />;
  if (visual.kind === "transit") return <TransitVisual visual={visual} compact={compact} />;
  return <FractionVisual visual={visual} compact={compact} />;
}

function AudioPlayButton({ src, theme, floating = false }: { src: string; theme: SceneTheme; floating?: boolean }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const toggleAudio = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
      return;
    }

    try {
      await audio.play();
      setIsPlaying(true);
    } catch {
      setIsPlaying(false);
    }
  };

  return (
    <>
      <audio ref={audioRef} src={src} preload="auto" onEnded={() => setIsPlaying(false)} onPause={() => setIsPlaying(false)} className="hidden" />
      <button
        type="button"
        onClick={toggleAudio}
        aria-label={isPlaying ? "음성 멈추기" : "음성 듣기"}
        className={`flex h-12 w-12 items-center justify-center rounded-full border bg-white/95 text-lg font-black shadow-[0_14px_30px_rgba(57,78,97,0.18)] transition hover:-translate-y-0.5 hover:shadow-[0_18px_36px_rgba(57,78,97,0.22)] ${
          floating ? "absolute left-4 top-4 z-10" : ""
        }`}
        style={{ borderColor: theme.border, color: theme.accentStrong }}
      >
        {isPlaying ? "II" : "▶"}
      </button>
    </>
  );
}

function StageMedia({
  question,
  theme,
  compact = false,
  full = false,
  featured = false,
  dense = false,
}: {
  question: StageQuestion;
  theme: SceneTheme;
  compact?: boolean;
  full?: boolean;
  featured?: boolean;
  dense?: boolean;
}) {
  if (!question.imageUrl && !question.audioUrl) return null;

  return (
    <div
      className={`relative overflow-hidden rounded-[20px] border bg-white shadow-sm ${
        full
          ? "flex h-full min-h-[280px] flex-col p-3"
          : compact
            ? dense
              ? "mx-auto w-fit max-w-full p-2"
              : "p-2"
            : "p-3"
      }`}
      style={{ borderColor: theme.border }}
    >
      {question.imageUrl && (
        <Image
          src={question.imageUrl}
          alt={question.prompt}
          width={1536}
          height={1024}
          className={`rounded-[16px] bg-[#f8fafc] ${dense ? "object-contain" : "w-full object-contain"} ${
            full
              ? "min-h-0 flex-1"
              : compact
                ? dense
                  ? "h-[clamp(220px,23vh,250px)] w-auto max-w-full"
                  : featured
                    ? "h-[clamp(150px,20vh,190px)]"
                    : "h-[clamp(190px,28vh,280px)]"
                : "h-[clamp(260px,42vh,420px)]"
          }`}
          unoptimized
        />
      )}
      {question.audioUrl && (
        <div className={question.imageUrl ? "" : "grid min-h-24 place-items-center"}>
          <AudioPlayButton src={question.audioUrl} theme={theme} floating={Boolean(question.imageUrl)} />
        </div>
      )}
    </div>
  );
}

function StageVisualBoard({
  visual,
  question,
  theme,
  compact = false,
}: {
  visual: SceneVisual;
  question: StageQuestion;
  theme: SceneTheme;
  compact?: boolean;
}) {
  if (question.imageUrl || question.audioUrl) {
    return (
      <div className={`h-full ${compact ? "min-h-[150px]" : "min-h-[360px]"}`}>
        <StageMedia question={question} theme={theme} compact={compact} full={!compact} />
      </div>
    );
  }

  return (
    <div className={`grid h-full grid-rows-1 gap-3 ${compact ? "min-h-0" : "min-h-[300px]"}`}>
      <div className="min-h-0 overflow-hidden">
        <LearningVisual visual={visual} compact={compact} />
      </div>
    </div>
  );
}

function StageInlineNotice({
  answer,
  isCorrect,
  isStageComplete,
  isFinished,
  title,
  message,
  feedback,
  theme,
  wrongNotice,
}: {
  answer: string | null;
  isCorrect: boolean;
  isStageComplete: boolean;
  isFinished: boolean;
  title: string;
  message: string;
  feedback: string;
  theme: SceneTheme;
  wrongNotice: string | null;
}) {
  const showSuccess = ((answer && isCorrect) || isStageComplete) && !isFinished;
  const showWrong = Boolean(wrongNotice) && !isStageComplete && !isFinished;

  if (!showSuccess && !showWrong) return null;

  return (
    <div
      key={showSuccess ? `success-${title}` : wrongNotice ?? "wrong"}
      className={`pointer-events-none absolute left-5 right-5 top-[68px] z-20 origin-top animate-[stageNoticeIn_420ms_cubic-bezier(0.16,1,0.3,1)_both] rounded-[16px] px-4 py-3 text-sm font-bold leading-6 shadow-[0_16px_34px_rgba(31,41,55,0.12)] will-change-transform ${
        showSuccess ? "border border-[#f0dfb4] bg-[#fff7dd] text-[#6b4b12]" : "bg-[#fff0ed] text-[#b84232]"
      }`}
    >
      {showSuccess && (
        <p className="font-black" style={{ color: theme.accentStrong }}>
          {title}
        </p>
      )}
      <p className={showSuccess ? "mt-1" : ""}>{showSuccess ? message : feedback}</p>
    </div>
  );
}

function FloatingStageFeedback({
  showSuccess,
  showWrong,
  title,
  message,
  wrongMessage,
  theme,
}: {
  showSuccess: boolean;
  showWrong: boolean;
  title: string;
  message: string;
  wrongMessage: string;
  theme: SceneTheme;
}) {
  if (!showSuccess && !showWrong) return null;

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-[calc(100%+12px)] z-40 grid place-items-center">
      <div
        className={`rounded-[18px] px-5 py-3 text-center text-sm font-bold leading-6 shadow-[0_18px_42px_rgba(31,41,55,0.18)] ${
          showSuccess ? "border border-[#f0dfb4] bg-[#fff7dd] text-[#6b4b12]" : "bg-[#fff0ed] text-[#b84232]"
        }`}
        style={{ width: "min(560px, 72%)" }}
      >
        {showSuccess && (
          <p className="font-black" style={{ color: theme.accentStrong }}>
            {title}
          </p>
        )}
        <p className={showSuccess ? "mt-1" : ""}>{showSuccess ? message : wrongMessage}</p>
      </div>
    </div>
  );
}

function ChoiceButton({
  label,
  prefix,
  selected,
  correct,
  disabled,
  theme,
  onClick,
}: {
  label: string;
  prefix: string;
  selected: boolean;
  correct: boolean;
  disabled?: boolean;
  theme: SceneTheme;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex min-h-14 items-center gap-3 rounded-[18px] border px-4 py-3 text-left text-lg font-black leading-6 transition ${
        selected
          ? correct
            ? ""
            : "border-[#f08a7a] bg-[#fff0ed] text-[#b84232]"
          : "border-[#dde6ee] bg-[#fbfdff] hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(57,78,97,0.12)] disabled:opacity-70 disabled:hover:translate-y-0 disabled:hover:shadow-none"
      }`}
      style={selected && correct ? { borderColor: theme.accent, backgroundColor: theme.accentSoft, color: theme.accentStrong } : undefined}
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#eef3f7] text-sm">{prefix}</span>
      <span className="break-keep">{label}</span>
    </button>
  );
}

function ConceptCards({ question, theme }: { question: StageQuestion; theme: SceneTheme }) {
  return (
    <div className="space-y-3">
      {question.body && <p className="rounded-[18px] bg-[#fbfdff] px-4 py-4 text-base font-bold leading-7 text-[#4b5563]">{question.body}</p>}
      <div className="grid gap-3">
        {question.conceptCards?.map((card, index) => (
          <div key={`${card.title}-${index}`} className="rounded-[18px] border px-4 py-3" style={{ borderColor: theme.border, backgroundColor: theme.accentPale }}>
            <p className="text-base font-black" style={{ color: theme.accentStrong }}>
              {card.title}
            </p>
            <p className="mt-1 text-sm font-bold leading-6 text-[#596157]">{card.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function OxTemplate({
  question,
  answers,
  isCorrect,
  theme,
  onSelect,
  showConcept = true,
}: {
  question: StageQuestion;
  answers: Record<number, string>;
  isCorrect: boolean;
  theme: SceneTheme;
  onSelect: (index: number, choice: string) => void;
  showConcept?: boolean;
}) {
  const items =
    question.oxItems ??
    (question.oxStatement
      ? [
          {
            statement: question.oxStatement,
            correctAnswer: question.correctAnswer === "X" ? ("X" as const) : ("O" as const),
          },
        ]
      : []);

  return (
    <div className="space-y-3">
      {showConcept && <ConceptCards question={question} theme={theme} />}
      <div className="space-y-3 rounded-[20px] border border-[#dfe9d7] bg-[#fbfff7] p-4">
        <p className="text-xs font-black" style={{ color: theme.accentStrong }}>
          OX 확인
        </p>
        {items.map((item, itemIndex) => (
          <div key={`${item.statement}-${itemIndex}`} className="rounded-[18px] bg-white/82 p-3 shadow-sm">
            <p className="text-base font-black leading-7 break-keep">
              <span className="mr-2" style={{ color: theme.accentStrong }}>
                {itemIndex + 1}.
              </span>
              {item.statement}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3">
              {(question.choices ?? ["O", "X"]).map((choice, choiceIndex) => {
                const selected = answers[itemIndex] === choice;
                const isItemCorrect = choice === item.correctAnswer;

                return (
                  <button
                    key={`${item.statement}-${choice}-${choiceIndex}`}
                    onClick={() => onSelect(itemIndex, choice)}
                    disabled={isCorrect}
                    className={`h-14 rounded-[18px] border text-2xl font-black transition hover:-translate-y-0.5 ${
                      selected && !isItemCorrect ? "border-[#f08a7a] bg-[#fff0ed] text-[#b84232]" : "border-[#dde6ee] bg-white"
                    }`}
                    style={selected && isItemCorrect ? { borderColor: theme.accent, backgroundColor: theme.accentSoft, color: theme.accentStrong } : undefined}
                  >
                    {choice}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SequenceTemplate({
  question,
  selected,
  theme,
  onPick,
  onReset,
}: {
  question: StageQuestion;
  selected: string[];
  theme: SceneTheme;
  onPick: (id: string) => void;
  onReset: () => void;
}) {
  const items = question.sequenceItems ?? [];
  const slots = Array.from({ length: items.length }, (_, index) => selected[index] ?? "");
  const selectedIds = slots.filter(Boolean);
  const availableItems = items.filter((item) => !selectedIds.includes(item.id));

  return (
    <div className="grid min-h-0 grid-rows-[auto_auto_auto] gap-2 overflow-hidden rounded-[22px] border border-[#d9ebc9] bg-[#fbfff7] p-3 shadow-[inset_0_-10px_0_rgba(39,174,96,0.05)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-base font-black leading-5">{question.prompt}</p>
          <p className="mt-1 text-[11px] font-bold leading-4 text-[#596157]">{question.body ?? "카드를 끌어 올바른 순서대로 놓아보세요."}</p>
        </div>
        {selectedIds.length > 0 && (
          <button
            onClick={onReset}
            className="shrink-0 rounded-full border bg-white px-3 py-1.5 text-xs font-black shadow-sm"
            style={{ borderColor: theme.border, color: theme.accentStrong }}
          >
            다시 놓기
          </button>
        )}
      </div>

      <div className="rounded-[18px] border border-dashed border-[#cfd8cf] bg-white/70 p-2.5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-black" style={{ color: theme.accentStrong }}>
            순서 칸
          </p>
          <p className="text-[11px] font-bold text-[#8a5a00]">클릭해서 순서대로 놓기</p>
        </div>
        <div className="mt-2 grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.max(items.length, 1)}, minmax(0, 1fr))` }}>
          {slots.map((id, index) => {
            const item = items.find((candidate) => candidate.id === id);

          return (
            <div
              key={index}
              className={`flex h-[74px] flex-col items-center justify-center rounded-[16px] border-2 border-dashed px-2.5 py-2 text-center transition ${
                item ? "border-solid bg-white shadow-[0_10px_24px_rgba(57,78,97,0.10)]" : "bg-white/55"
              }`}
              style={{ borderColor: item ? theme.accent : "#cfd8cf" }}
            >
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-black text-white" style={{ backgroundColor: theme.accent }}>
                {index + 1}
              </span>
              <span className={`mt-1 block text-[15px] font-black leading-6 break-keep ${item ? "text-[#1f211d]" : "text-[#9aa39b]"}`}>
                {item?.label ?? "여기에 놓기"}
              </span>
              <span className="line-clamp-1 min-h-4 text-[10px] font-bold leading-4 text-[#6d746c] break-keep">
                {item?.caption ?? ""}
              </span>
            </div>
          );
        })}
        </div>
      </div>

      <div className="overflow-hidden rounded-[18px] border border-[#f0dfb4] bg-[#fff9e8] p-2.5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-black text-[#8a5a00]">카드 트레이</p>
          {availableItems.length > 0 && <p className="text-[11px] font-bold text-[#8a5a00]">카드를 차례대로 눌러요</p>}
        </div>
        <div className="mt-2 grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.min(Math.max(items.length, 1), 3)}, minmax(0, 1fr))` }}>
          {items.map((item) => {
            const picked = selectedIds.includes(item.id);

            return (
            <button
              key={item.id}
              onClick={() => onPick(item.id)}
              disabled={picked}
              className="h-[48px] cursor-grab rounded-[16px] border bg-white px-3 py-1.5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(57,78,97,0.12)] active:cursor-grabbing disabled:cursor-default disabled:opacity-35 disabled:hover:translate-y-0 disabled:hover:shadow-sm"
              style={{ borderColor: picked ? theme.accent : "#dde6ee" }}
            >
              <p className="line-clamp-2 text-[13px] font-black leading-[18px] break-keep">{item.label}</p>
              {item.caption && <p className="text-[10px] font-bold leading-4 text-[#6d746c] break-keep">{item.caption}</p>}
            </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SequenceStageBoard({
  visual,
  question,
  selected,
  theme,
  onPick,
  onReset,
}: {
  visual: SceneVisual;
  question: StageQuestion;
  selected: string[];
  theme: SceneTheme;
  onPick: (id: string) => void;
  onReset: () => void;
}) {
  return (
    <div className="grid h-full min-h-0 grid-rows-[minmax(220px,1fr)_auto] gap-3">
      <div className="min-h-0 overflow-hidden">
        <StageVisualBoard visual={visual} question={question} theme={theme} compact />
      </div>
      <div className="min-h-0 overflow-hidden">
        <SequenceTemplate question={question} selected={selected} theme={theme} onPick={onPick} onReset={onReset} />
      </div>
    </div>
  );
}

function CardMatchingTemplate({
  question,
  pairs,
  selectedLeft,
  theme,
  onLeft,
  onRight,
}: {
  question: StageQuestion;
  pairs: Record<string, string>;
  selectedLeft: string | null;
  theme: SceneTheme;
  onLeft: (id: string) => void;
  onRight: (id: string) => void;
}) {
  const items = question.matchingPairs ?? [];
  const rightItems = [...items].reverse();
  const matchedCount = Object.keys(pairs).length;
  const matchingRowHeight = 48;
  const matchingGap = 5;
  const matchingLaneHeight = items.length * matchingRowHeight + Math.max(0, items.length - 1) * matchingGap;
  const laneConnections = items
    .map((item, index) => {
      const rightId = pairs[item.leftId];
      const rightIndex = rightItems.findIndex((candidate) => candidate.rightId === rightId);

      if (!rightId || rightIndex < 0) return null;

      return {
        id: `${item.leftId}-${rightId}`,
        leftY: ((index + 0.5) / items.length) * 100,
        rightY: ((rightIndex + 0.5) / rightItems.length) * 100,
      };
    })
    .filter(Boolean) as Array<{ id: string; leftY: number; rightY: number }>;

  return (
    <div
      className={`grid h-full min-h-0 content-start gap-2.5 overflow-y-auto rounded-[22px] border border-[#d9ebc9] bg-[#fbfff7] p-3.5 shadow-[inset_0_-10px_0_rgba(39,174,96,0.05)] ${
        question.imageUrl || question.audioUrl ? "grid-rows-[auto_auto_auto]" : "grid-rows-[auto_auto]"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[1.35rem] font-black leading-7">서로 맞는 카드를 연결해보세요</p>
          <p className="mt-1 line-clamp-2 text-sm font-bold leading-5 text-[#596157]">{question.body ?? "왼쪽 카드를 누르고 맞는 오른쪽 카드를 눌러요."}</p>
        </div>
        <div className="rounded-full bg-white px-4 py-2 text-sm font-black shadow-sm" style={{ color: theme.accentStrong }}>
          {matchedCount} / {items.length}
        </div>
      </div>

      {(question.imageUrl || question.audioUrl) && (
        <div className="mx-auto min-h-[260px] w-full max-w-[780px]">
          <StageMedia question={question} theme={theme} compact dense />
        </div>
      )}

      <div
        className="grid grid-cols-[minmax(220px,1fr)_minmax(190px,0.52fr)_minmax(220px,1fr)] items-start gap-3 overflow-hidden"
        style={{ height: matchingLaneHeight }}
      >
        <div className="grid min-h-0 content-start gap-1.5">
          {items.map((item) => {
            const picked = selectedLeft === item.leftId;
            const matched = Boolean(pairs[item.leftId]);
            return (
              <button
                key={item.leftId}
                onClick={() => onLeft(item.leftId)}
                disabled={matched}
                className={`relative z-10 flex h-[48px] items-center rounded-[16px] border bg-white px-4 text-left text-[0.84rem] font-black leading-5 shadow-sm transition-all duration-200 ease-out hover:-translate-y-0.5 disabled:hover:translate-y-0 ${
                  picked ? "scale-[1.015] shadow-[0_16px_30px_rgba(39,174,96,0.16)]" : ""
                }`}
                style={{
                  borderColor: picked || matched ? theme.accent : "#dde6ee",
                  backgroundColor: matched ? theme.accentSoft : picked ? "#f8fff9" : "#ffffff",
                  boxShadow: picked ? `0 0 0 6px ${theme.accentSoft}` : undefined,
                }}
              >
                <span className="flex-1">{item.left}</span>
                {matched && (
                  <span className="ml-3 flex h-8 w-8 items-center justify-center rounded-full text-sm text-white" style={{ backgroundColor: theme.accent }}>
                    ✓
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div
          className="relative overflow-hidden rounded-[20px] border border-dashed border-[#cfd8cf] bg-white/65 px-4 py-4 text-center"
          style={{ height: matchingLaneHeight }}
        >
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            {laneConnections.map((connection) => (
              <path
                key={connection.id}
                d={`M 0 ${connection.leftY} C 34 ${connection.leftY}, 66 ${connection.rightY}, 100 ${connection.rightY}`}
                fill="none"
                stroke={theme.accent}
                strokeLinecap="round"
                strokeWidth="3.5"
                opacity="0.32"
              />
            ))}
          </svg>
          <div className="relative z-10 flex h-full flex-col">
            <div className="flex justify-center gap-2">
              {items.map((item, index) => (
                <span
                  key={item.leftId}
                  className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-black shadow-sm transition-all duration-200"
                  style={
                    pairs[item.leftId]
                      ? { backgroundColor: theme.accent, color: "#ffffff" }
                      : { backgroundColor: "#ffffff", color: theme.accentStrong }
                  }
                >
                  {pairs[item.leftId] ? "✓" : index + 1}
                </span>
              ))}
            </div>
            <div className="mt-2 w-full rounded-[18px] bg-white/90 px-4 py-2.5 shadow-[0_12px_26px_rgba(57,78,97,0.10)]">
              <p className="whitespace-nowrap text-sm font-black leading-6" style={{ color: theme.accentStrong }}>
                {selectedLeft ? "오른쪽 카드를 골라요" : "왼쪽 카드를 골라요"}
              </p>
              <p className="mt-1 text-[11px] font-bold leading-4 text-[#6d746c]">
                맞으면 바로 연결돼요
              </p>
            </div>
            <div className="mt-auto text-[11px] font-black text-[#8a5a00]">연결 {matchedCount}/{items.length}</div>
          </div>
        </div>

        <div className="grid min-h-0 content-start gap-1.5">
          {rightItems.map((item) => {
            const used = Object.values(pairs).includes(item.rightId);
            return (
              <button
                key={item.rightId}
                onClick={() => onRight(item.rightId)}
                disabled={!selectedLeft || used}
                className="relative z-10 flex h-[48px] items-center rounded-[16px] border bg-white px-4 text-left text-[0.84rem] font-black leading-5 shadow-sm transition-all duration-200 ease-out hover:-translate-y-0.5 disabled:opacity-45 disabled:hover:translate-y-0"
                style={{ borderColor: used ? theme.accent : "#dde6ee", backgroundColor: used ? theme.accentSoft : "#ffffff" }}
              >
                <span className="flex-1">{item.right}</span>
                {used && (
                  <span className="ml-3 flex h-8 w-8 items-center justify-center rounded-full text-sm text-white" style={{ backgroundColor: theme.accent }}>
                    ✓
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function FillBlankTemplate({
  question,
  slots,
  theme,
  onPick,
  onReset,
}: {
  question: StageQuestion;
  slots: string[];
  theme: SceneTheme;
  onPick: (id: string) => void;
  onReset: () => void;
}) {
  let blankIndex = 0;
  const hasSlots = slots.length > 0;
  const fillParts = getFillBlankParts(question);

  return (
    <div className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)_auto] gap-3 rounded-[22px] border border-[#d9ebc9] bg-[#fbfff7] p-4 shadow-[inset_0_-8px_0_rgba(39,174,96,0.05)]">
      <div className="flex items-start justify-between gap-3">
        {question.body && <p className="min-w-0 text-sm font-bold leading-6 text-[#596157] line-clamp-2">{question.body}</p>}
        <button
          onClick={onReset}
          disabled={!hasSlots}
          className="shrink-0 rounded-full border bg-white px-3 py-2 text-xs font-black shadow-sm transition disabled:opacity-35"
          style={{ borderColor: theme.border, color: theme.accentStrong }}
        >
          다시 채우기
        </button>
      </div>

      <div className="min-h-0 overflow-y-auto rounded-[20px] border border-[#dde6ee] bg-white px-4 py-5 text-center text-[1.35rem] font-black leading-9 break-keep">
        <div className="mx-auto max-w-[26rem]">
        {fillParts.map((part, index) => {
          if (part.kind === "text") return <span key={`${part.value}-${index}`}>{part.value}</span>;
          const value = slots[blankIndex++];
          return (
            <span key={`${part.value}-${index}`} className="mx-1 inline-flex h-11 min-w-20 items-center justify-center rounded-[14px] border-2 border-dashed bg-[#f8fff3] px-3 align-middle text-xl" style={{ borderColor: theme.accent, color: theme.accentStrong }}>
              {value || ""}
            </span>
          );
        })}
        </div>
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(82px,1fr))] gap-3 rounded-[20px] border border-[#f0dfb4] bg-[#fff9e8] p-3">
        {question.fillOptions?.map((option) => (
          <button
            key={option.id}
            onClick={() => onPick(option.id)}
            className="h-14 rounded-[16px] border bg-white px-2 text-xl font-black shadow-sm transition hover:-translate-y-0.5"
            style={{ borderColor: slots.includes(option.id) ? theme.accent : "#dde6ee" }}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function getFillBlankParts(question: StageQuestion) {
  const parts = question.fillBlankText ?? [];
  if (parts.some((part) => part.kind === "blank")) return parts;

  return [
    { kind: "text" as const, value: "알맞은 값을 골라 " },
    { kind: "blank" as const, value: "__" },
    { kind: "text" as const, value: " 칸에 넣어보세요." },
  ];
}

function getFillBlankCount(question: StageQuestion) {
  return getFillBlankParts(question).filter((part) => part.kind === "blank").length;
}

function getRealtimePracticeCopy(scene: StudentContext["scene"], question: StageQuestion) {
  const isLearningFocus = scene.contentType === "learning_focus";
  const isClockPractice = /시계|시침|분침|짧은 바늘|긴 바늘|약속 시간/.test(
    `${scene.title} ${scene.missionDescription} ${question.prompt}`,
  );
  const isTransitPractice = /버스|정류장|센터|도움|안내 직원/.test(`${scene.title} ${scene.missionDescription} ${question.prompt}`);
  const firstPrompt = question.realtimePracticeSpec?.firstPrompt ?? question.prompt;

  return {
    label: isLearningFocus ? "친구에게 설명하기" : "생활에 적용하기",
    title: isLearningFocus ? "내 말로 쉽게 설명해요" : "오늘 바로 쓸 말을 연습해요",
    partner: isLearningFocus ? "친구" : isTransitPractice ? "안내 직원" : "나",
    partnerLine: firstPrompt,
    studentLine: isLearningFocus
      ? isClockPractice
        ? "짧은 바늘을 먼저 보고, 그다음 긴 바늘을 보면 돼."
        : "먼저 중요한 단서를 보고, 내가 이해한 순서를 짧게 말해볼게."
      : isTransitPractice
        ? "센터에 가야 해요. 버스 알려 주세요."
        : "필요한 말을 짧게 말해볼게.",
    sceneLine: firstPrompt,
    actionLabel: isLearningFocus ? "설명 연습 시작" : "생활 적용 연습 시작",
  };
}

function RealtimePracticeRoom({
  question,
  scene,
  theme,
  isComplete,
  contentId,
  stageId,
  attemptId,
  token,
  accessCode,
  onRuntimeReady,
  onComplete,
  onFinish,
}: {
  question: StageQuestion;
  scene: StudentContext["scene"];
  theme: SceneTheme;
  isComplete: boolean;
  contentId?: string | null;
  stageId?: string;
  attemptId?: string | null;
  token?: string | null;
  accessCode?: string | null;
  onRuntimeReady: (nextToken: string, nextAttemptId: string) => void;
  onComplete: () => void;
  onFinish: () => void;
}) {
  const rubric = question.realtimePracticeSpec?.rubric ?? [];
  const practice = getRealtimePracticeCopy(scene, question);
  const timeLimitMinutes = Math.round((question.realtimePracticeSpec?.timeLimitSeconds ?? 180) / 60);
  const minimumStudentTurns = 1;
  const [draft, setDraft] = useState("");
  const [connectionState, setConnectionState] = useState<"idle" | "connecting" | "connected" | "ending" | "complete" | "error">("idle");
  const [statusMessage, setStatusMessage] = useState("시작을 누르면 별이와 실시간으로 대화할 수 있어요.");
  const [studentTurns, setStudentTurns] = useState(0);
  const [messages, setMessages] = useState<Array<{ id: number; role: "partner" | "student" | "system"; text: string }>>([
    { id: 1, role: "partner", text: practice.sceneLine },
  ]);
  const [livePartnerText, setLivePartnerText] = useState("");
  const [liveStudentText, setLiveStudentText] = useState("");
  const messageListRef = useRef<HTMLDivElement>(null);
  const remoteAudioRef = useRef<HTMLAudioElement>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const realtimeSessionIdRef = useRef<string | null>(null);
  const realtimeTokenRef = useRef<string | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const transcriptRef = useRef<string[]>([practice.sceneLine]);
  const partnerDraftRef = useRef("");
  const studentDraftRef = useRef("");
  const speechStartedAtRef = useRef<number | null>(null);
  const hasUserSubmittedRef = useRef(false);
  const responseInProgressRef = useRef(false);

  useEffect(() => {
    messageListRef.current?.scrollTo({
      top: messageListRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [livePartnerText, liveStudentText, messages]);

  useEffect(() => () => closeRealtimeConnection(), []);

  function closeRealtimeConnection() {
    dataChannelRef.current?.close();
    peerConnectionRef.current?.close();
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    dataChannelRef.current = null;
    peerConnectionRef.current = null;
    mediaStreamRef.current = null;
  }

  const appendMessage = (role: "partner" | "student" | "system", text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const label = role === "student" ? "학생" : role === "partner" ? "상대" : "시스템";
    transcriptRef.current = [...transcriptRef.current, `${label}: ${trimmed}`];
    setMessages((current) => [...current, { id: current.length + 1, role, text: trimmed }]);
  };

  const sendSessionEvent = (eventType: string, payloadJson: Record<string, unknown>) => {
    const sessionId = realtimeSessionIdRef.current;
    const activeToken = realtimeTokenRef.current ?? token;
    if (!sessionId || !activeToken) return;
    void saveRealtimeSessionEvent(sessionId, { eventType, payloadJson }, { token: activeToken }).catch(() => undefined);
  };

  const handleRealtimeEvent = (rawEvent: unknown) => {
    if (!rawEvent || typeof rawEvent !== "object" || !("type" in rawEvent)) return;
    const event = rawEvent as Record<string, unknown>;
    const type = String(event.type);

    if (type === "input_audio_buffer.speech_started") {
      speechStartedAtRef.current = Date.now();
      setStatusMessage("듣고 있어요. 천천히 말해보세요.");
      appendMessage("system", "마이크 입력을 듣고 있어요.");
      return;
    }

    if (type === "input_audio_buffer.speech_stopped") {
      const speechDurationMs = speechStartedAtRef.current ? Date.now() - speechStartedAtRef.current : 0;
      speechStartedAtRef.current = null;
      if (speechDurationMs > 0 && speechDurationMs < 700) {
        setStatusMessage("너무 짧은 소리는 넘겼어요. 말할 때만 천천히 이야기해 주세요.");
        return;
      }
      setStatusMessage("말을 들었어요. 답을 기다리는 중이에요.");
      appendMessage("system", "말을 들었어요. 답변을 기다리는 중이에요.");
      return;
    }

    if (
      (type === "conversation.item.input_audio_transcription.delta" || type === "conversation.item.input_audio_transcription.updated") &&
      typeof event.delta === "string"
    ) {
      studentDraftRef.current += event.delta;
      setLiveStudentText(studentDraftRef.current);
      return;
    }

    if (type === "conversation.item.input_audio_transcription.completed" || type === "conversation.item.input_audio_transcription.done") {
      const text = extractRealtimeEventText(event) || studentDraftRef.current.trim();
      if (text) {
        appendMessage("student", text);
        if (isMeaningfulStudentSpeech(text)) {
          setStudentTurns((current) => current + 1);
        }
        setDraft("");
      }
      studentDraftRef.current = "";
      setLiveStudentText("");
      return;
    }

    if (type === "response.audio_transcript.delta" && typeof event.delta === "string") {
      responseInProgressRef.current = true;
      partnerDraftRef.current += event.delta;
      setLivePartnerText(partnerDraftRef.current);
      return;
    }

    if ((type === "response.audio_transcript.done" || type === "response.output_text.done") && typeof event.transcript === "string") {
      appendMessage("partner", event.transcript);
      partnerDraftRef.current = "";
      setLivePartnerText("");
      return;
    }

    if (type === "response.output_text.done" && typeof event.text === "string") {
      appendMessage("partner", event.text);
      partnerDraftRef.current = "";
      setLivePartnerText("");
      return;
    }

    if (type === "response.created" || type === "response.in_progress") {
      responseInProgressRef.current = true;
      return;
    }

    if (type === "response.done") {
      responseInProgressRef.current = false;
      const text = extractRealtimeResponseText(event);
      const fallbackText = partnerDraftRef.current.trim();
      if (text || fallbackText) {
        appendMessage("partner", text || fallbackText);
      }
      partnerDraftRef.current = "";
      setLivePartnerText("");
      return;
    }

    if (type === "error") {
      const error = event.error;
      const message =
        error && typeof error === "object" && "message" in error && typeof error.message === "string"
          ? error.message
          : "잠시 뒤 다시 시도해 주세요.";
      setConnectionState("error");
      setStatusMessage(`실시간 대화 오류: ${message}`);
      appendMessage("system", `오류: ${message}`);
      partnerDraftRef.current = "";
      studentDraftRef.current = "";
      setLivePartnerText("");
      setLiveStudentText("");
      responseInProgressRef.current = false;
    }
  };

  const startRealtimeConversation = async () => {
    if (connectionState === "connecting" || connectionState === "connected") return;
    if (!contentId || !stageId) {
      setConnectionState("error");
      setStatusMessage("실시간 연습을 시작할 수 있는 단계 정보를 찾지 못했어요.");
      return;
    }

    setConnectionState("connecting");
    setStatusMessage("실시간 대화를 연결하고 있어요.");

    try {
      let activeToken = token;
      let activeAttemptId = attemptId;

      if ((!activeToken || !activeAttemptId) && accessCode) {
        setStatusMessage("학습 기록을 준비하고 있어요.");
        const access = await studentAccess({ accessCode });
        const attempt = await startStudentMission(contentId, { token: access.session.accessToken });
        activeToken = access.session.accessToken;
        activeAttemptId = attempt.id;
        onRuntimeReady(activeToken, activeAttemptId);
      }

      if (!activeToken || !activeAttemptId) {
        throw new Error("runtime_not_ready");
      }

      realtimeTokenRef.current = activeToken;
      const session = await createRealtimeSession(contentId, stageId, { attemptId: activeAttemptId }, { token: activeToken });
      realtimeSessionIdRef.current = session.sessionId;
      startedAtRef.current = Date.now();

      const peerConnection = new RTCPeerConnection();
      peerConnectionRef.current = peerConnection;
      peerConnection.ontrack = (event) => {
        if (remoteAudioRef.current) {
          remoteAudioRef.current.srcObject = event.streams[0];
        }
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = mediaStream;
      mediaStream.getAudioTracks().forEach((track) => peerConnection.addTrack(track, mediaStream));

      const dataChannel = peerConnection.createDataChannel("oai-events");
      dataChannelRef.current = dataChannel;
      dataChannel.addEventListener("open", () => {
        setConnectionState("connected");
        setStatusMessage("연결됐어요. 마이크로 말하거나 아래에 문장을 입력해도 돼요.");
        appendMessage("system", "실시간 대화가 연결됐어요. 말하거나 채팅을 보내세요.");
        sendSessionEvent("realtime_session_connected", { provider: session.provider, model: session.model });
      });
      dataChannel.addEventListener("message", (event) => {
        try {
          handleRealtimeEvent(JSON.parse(event.data));
        } catch {
          // Ignore non-JSON diagnostic frames.
        }
      });
      dataChannel.addEventListener("error", () => {
        setConnectionState("error");
        setStatusMessage("대화 채널 연결에 실패했어요.");
      });

      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      const sdpResponse = await fetch(session.webrtcUrl, {
        method: "POST",
        body: offer.sdp,
        headers: {
          Authorization: `Bearer ${session.clientSecret}`,
          "Content-Type": "application/sdp",
        },
      });

      if (!sdpResponse.ok) {
        throw new Error(await sdpResponse.text());
      }

      await peerConnection.setRemoteDescription({
        type: "answer",
        sdp: await sdpResponse.text(),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "알 수 없는 오류";
      console.error("Realtime conversation failed", error);
      closeRealtimeConnection();
      setConnectionState("error");
      setStatusMessage(`실시간 대화를 시작하지 못했어요. ${message.slice(0, 140)}`);
      appendMessage("system", `실시간 대화를 시작하지 못했어요. ${message.slice(0, 140)}`);
    }
  };

  const submitMessage = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const nextTurn = studentTurns + 1;
    hasUserSubmittedRef.current = true;
    appendMessage("student", trimmed);
    setStudentTurns(nextTurn);
    setDraft("");
    sendSessionEvent("realtime_text_message", { text: trimmed });

    const dataChannel = dataChannelRef.current;
    if (dataChannel?.readyState === "open") {
      dataChannel.send(
        JSON.stringify({
          type: "conversation.item.create",
          item: {
            type: "message",
            role: "user",
            content: [{ type: "input_text", text: trimmed }],
          },
        }),
      );
      if (responseInProgressRef.current) {
        setStatusMessage("?대떦 ?듬? ?앷컖???덈굹硫??ㅼ쓬 留먯쓣 蹂대궡二쇱꽭??");
        return;
      }
      responseInProgressRef.current = true;
      dataChannel.send(JSON.stringify({ type: "response.create" }));
    }
  };

  const finishRealtimeConversation = async () => {
    if (connectionState === "ending") return;
    setConnectionState("ending");
    setStatusMessage("대화 기록을 저장하고 있어요.");
    closeRealtimeConnection();

    const sessionId = realtimeSessionIdRef.current;
    const activeToken = realtimeTokenRef.current ?? token;
    if (!sessionId || !activeToken) {
      setConnectionState("complete");
      onComplete();
      return;
    }

    try {
      await completeRealtimeSession(
        sessionId,
        {
          turnCount: studentTurns,
          durationSec: startedAtRef.current ? Math.max(1, Math.round((Date.now() - startedAtRef.current) / 1000)) : 0,
          rubricResult: {
            practiced: studentTurns >= minimumStudentTurns,
            supportNeeded: studentTurns < minimumStudentTurns ? "학생 발화가 충분히 기록되지 않았습니다." : null,
          },
          transcriptSummary: transcriptRef.current.slice(-8).join(" / "),
        },
        { token: activeToken },
      );
      setConnectionState("complete");
      setStatusMessage("실시간 대화가 저장됐어요.");
      onComplete();
    } catch {
      setConnectionState("error");
      setStatusMessage("대화 저장에 실패했어요. 다시 마치기를 눌러 주세요.");
    }
  };

  return (
    <div className="grid h-full min-h-[440px] grid-cols-[minmax(360px,0.9fr)_minmax(390px,1fr)] gap-4 rounded-[24px] border border-[#dce5ec] bg-white p-4 shadow-[0_18px_48px_rgba(57,78,97,0.10)]">
      <div className="relative flex min-h-0 flex-col overflow-hidden rounded-[22px] border p-4" style={{ borderColor: theme.border, backgroundColor: theme.accentPale }}>
        <div className="relative z-10">
          <p className="text-sm font-black" style={{ color: theme.accentStrong }}>
            {practice.label}
          </p>
          <h3 className="mt-1.5 text-[1.65rem] font-black leading-tight break-keep text-[#172033]">{practice.title}</h3>
          <div className="mt-3">
            <StageMedia question={question} theme={theme} compact featured />
          </div>
        </div>

        <div className="relative z-10 mt-4 grid grid-cols-[minmax(0,1fr)_128px] items-end gap-3">
          <div className="relative rounded-[20px] border border-white/80 bg-white/90 p-3.5 shadow-sm before:absolute before:right-[-12px] before:top-1/2 before:h-6 before:w-6 before:-translate-y-1/2 before:rotate-45 before:border-r before:border-t before:border-white/80 before:bg-white/90">
            <p className="text-xs font-black" style={{ color: theme.accentStrong }}>
              {practice.partner}
            </p>
            <p className="mt-1.5 text-[clamp(0.9rem,1.9vh,1.15rem)] font-black leading-snug break-keep text-[#25312a]">
              {practice.partnerLine}
            </p>
          </div>
          <div className="justify-self-end">
            <QuestionStar />
          </div>
        </div>

        <audio ref={remoteAudioRef} autoPlay className="hidden" />
      </div>

      <div className="grid min-h-0 grid-rows-[auto_1fr_auto] overflow-hidden rounded-[22px] border border-[#e2e8f0] bg-[#f8fafc]">
        <div className="border-b border-[#e2e8f0] bg-white px-5 py-4">
          <p className="text-sm font-black text-[#172033]">실시간 채팅</p>
          <p className="mt-1 text-xs font-bold text-[#64748b]">
            마이크와 채팅을 함께 사용할 수 있어요 · 목표 시간 {timeLimitMinutes}분 · 내 말 {studentTurns}/{minimumStudentTurns}
          </p>
        </div>

        <div className="relative min-h-0">
        {isComplete && (
          <div className="pointer-events-none absolute inset-x-5 bottom-5 z-20">
            <div className="pointer-events-auto mx-auto flex max-w-[460px] items-center justify-between gap-3 rounded-[20px] border border-[#f0dfb4] bg-[#fff9e8] px-4 py-3 shadow-[0_18px_42px_rgba(31,41,55,0.18)] animate-[stageToastIn_220ms_ease-out_both]">
              <div className="min-w-0">
                <p className="text-sm font-black text-[#8a5a00]">대화가 마무리됐어요</p>
                <p className="mt-0.5 text-xs font-bold text-[#6b5a24]">오늘 연습을 완료할 수 있어요.</p>
              </div>
              <button
                type="button"
                onClick={onFinish}
                className="shrink-0 rounded-[14px] px-4 py-2 text-sm font-black text-white shadow-[0_10px_20px_rgba(39,174,96,0.22)] transition duration-200 hover:-translate-y-0.5"
                style={{ backgroundColor: theme.accentStrong }}
              >
                완료
              </button>
            </div>
          </div>
        )}
        <div ref={messageListRef} className="h-full min-h-0 space-y-3 overflow-y-auto px-5 py-4 pb-28">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`max-w-[82%] rounded-[18px] px-4 py-3 text-sm font-bold leading-6 shadow-sm ${
                message.role === "student"
                  ? "ml-auto rounded-tr-[6px] text-white"
                  : message.role === "system"
                    ? "mx-auto max-w-[92%] border border-[#d9ebc9] bg-[#f4fbef] text-center text-[#2f6b3a]"
                  : "rounded-tl-[6px] bg-white text-[#334155]"
              }`}
              style={message.role === "student" ? { backgroundColor: theme.accent } : undefined}
            >
              {message.role !== "system" && (
                <p className={`mb-1 text-[11px] font-black ${message.role === "student" ? "text-white/80" : "text-[#64748b]"}`}>
                  {message.role === "student" ? "나" : practice.partner}
                </p>
              )}
              {message.text}
            </div>
          ))}
          {liveStudentText && (
            <div className="ml-auto max-w-[82%] rounded-[18px] rounded-tr-[6px] px-4 py-3 text-sm font-bold leading-6 text-white shadow-sm" style={{ backgroundColor: theme.accent }}>
              <p className="mb-1 text-[11px] font-black text-white/80">나</p>
              {liveStudentText}
              <span className="ml-1 inline-block h-3 w-1 animate-pulse rounded-full bg-white/70" />
            </div>
          )}
          {livePartnerText && (
            <div className="max-w-[82%] rounded-[18px] rounded-tl-[6px] bg-white px-4 py-3 text-sm font-bold leading-6 text-[#334155] shadow-sm">
              <p className="mb-1 text-[11px] font-black text-[#64748b]">{practice.partner}</p>
              {livePartnerText}
              <span className="ml-1 inline-block h-3 w-1 animate-pulse rounded-full bg-[#94a3b8]" />
            </div>
          )}
          <div className="rounded-[18px] border border-[#f0dfb4] bg-[#fff9e8] px-4 py-3">
            <p className="text-xs font-black text-[#8a5a00]">확인할 점</p>
            <div className="mt-2 grid gap-2">
              {rubric.map((item, index) => (
                <div key={`${item}-${index}`} className="flex items-center gap-2 text-xs font-bold leading-5 text-[#5f4b16]">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-black text-white" style={{ backgroundColor: theme.accent }}>
                    {index + 1}
                  </span>
                  <span className="break-keep">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        </div>

        <div className="border-t border-[#e2e8f0] bg-white p-4">
          {connectionState === "idle" || connectionState === "error" ? (
            <button
              type="button"
              onClick={startRealtimeConversation}
              className="w-full rounded-[16px] px-5 py-3 text-sm font-black text-white shadow-[0_12px_24px_rgba(39,174,96,0.22)] transition duration-200 hover:-translate-y-0.5"
              style={{ backgroundColor: theme.accent }}
            >
              실시간 대화 시작
            </button>
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                submitMessage(draft);
              }}
              className="grid grid-cols-[1fr_auto_auto] gap-2"
            >
              <input
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                className="min-w-0 rounded-[16px] border border-[#dce5ec] bg-[#f8fafc] px-4 py-3 text-sm font-bold outline-none focus:border-[#94d86a] focus:bg-white"
                placeholder={question.actionLabel ?? practice.actionLabel}
                disabled={connectionState !== "connected"}
              />
              <button
                type="submit"
                className="rounded-[16px] px-5 py-3 text-sm font-black text-white shadow-[0_12px_24px_rgba(39,174,96,0.22)] transition duration-200 hover:-translate-y-0.5 disabled:opacity-45 disabled:hover:translate-y-0"
                style={{ backgroundColor: theme.accent }}
                disabled={!draft.trim() || connectionState !== "connected"}
              >
                보내기
              </button>
              <button
                type="button"
                onClick={finishRealtimeConversation}
                className="rounded-[16px] border border-[#dce5ec] bg-white px-5 py-3 text-sm font-black text-[#334155] shadow-sm transition duration-200 hover:-translate-y-0.5 disabled:opacity-45 disabled:hover:translate-y-0"
                disabled={connectionState === "connecting" || connectionState === "ending"}
              >
                마치기
              </button>
            </form>
          )}
          <p className="mt-2 text-xs font-bold leading-5 text-[#64748b]">{statusMessage}</p>
        </div>
      </div>
    </div>
  );
}

function extractRealtimeResponseText(event: Record<string, unknown>) {
  const response = event.response;
  if (!response || typeof response !== "object" || !("output" in response) || !Array.isArray(response.output)) {
    return "";
  }

  const parts: string[] = [];
  for (const output of response.output) {
    if (!output || typeof output !== "object" || !("content" in output) || !Array.isArray(output.content)) continue;

    for (const content of output.content) {
      if (!content || typeof content !== "object") continue;
      if ("transcript" in content && typeof content.transcript === "string") parts.push(content.transcript);
      if ("text" in content && typeof content.text === "string") parts.push(content.text);
    }
  }

  return parts.join(" ").trim();
}

function isMeaningfulStudentSpeech(text: string) {
  const normalized = text.replace(/[\s.,!?~…。、？！]/g, "");
  return normalized.length >= 2;
}

function extractRealtimeEventText(event: Record<string, unknown>) {
  if ("transcript" in event && typeof event.transcript === "string") return event.transcript.trim();
  if ("text" in event && typeof event.text === "string") return event.text.trim();

  const item = event.item;
  if (item && typeof item === "object" && "content" in item && Array.isArray(item.content)) {
    const parts = item.content
      .map((content) => {
        if (!content || typeof content !== "object") return "";
        if ("transcript" in content && typeof content.transcript === "string") return content.transcript;
        if ("text" in content && typeof content.text === "string") return content.text;
        return "";
      })
      .filter(Boolean);
    return parts.join(" ").trim();
  }

  return "";
}

function HintStar() {
  return (
    <div className="relative h-[72px] w-[72px] shrink-0" aria-hidden="true">
      <Image
        src="/assets/hint-star/without-eye.svg"
        alt=""
        fill
        sizes="72px"
        className="object-contain"
        draggable={false}
      />
      <Image
        src="/assets/hint-star/eye.svg"
        alt=""
        fill
        sizes="72px"
        className="animate-[hintStarBlink_4.2s_ease-in-out_infinite] object-contain"
        draggable={false}
      />
      <Image
        src="/assets/hint-star/light.svg"
        alt=""
        fill
        sizes="72px"
        className="animate-[hintStarLightFloat_2.8s_ease-in-out_infinite] object-contain"
        draggable={false}
      />
    </div>
  );
}

function QuestionStar() {
  return (
    <div className="relative h-32 w-32 shrink-0" aria-hidden="true">
      <Image
        src="/assets/question-star/without-eyes-question.svg"
        alt=""
        fill
        sizes="128px"
        className="object-contain"
        draggable={false}
      />
      <Image
        src="/assets/question-star/eyes.svg"
        alt=""
        fill
        sizes="128px"
        className="animate-[hintStarBlink_4.2s_ease-in-out_infinite] object-contain"
        draggable={false}
      />
      <Image
        src="/assets/question-star/question.svg"
        alt=""
        fill
        sizes="128px"
        className="animate-[questionStarWiggle_2.4s_ease-in-out_infinite] object-contain"
        draggable={false}
      />
    </div>
  );
}

const STAGE_FRAME_WIDTH = 1093;
const STAGE_FRAME_HEIGHT = 820;

export function StudentStageExperience({
  context,
  initialStep = context.scene.currentStep,
  initialMode = "stage",
  pathHref,
  nextHref,
  previewMode = false,
}: {
  context: StudentContext;
  initialStep?: number;
  initialMode?: "stage" | "complete";
  pathHref: string;
  nextHref: string;
  previewMode?: boolean;
}) {
  type PendingAnswerSubmission = {
    stageId: string;
    answer: Record<string, unknown>;
  };

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { student, scene } = context;
  const theme = scene.theme;
  const initialStageIndex = Math.max(
    0,
    scene.stages.findIndex((stage) => stage.step === initialStep),
  );
  const initialCompletedSteps =
    initialMode === "complete" || scene.isCompleted
      ? scene.stages.map((stage) => stage.step)
      : scene.stages.filter((stage) => stage.step < initialStep).map((stage) => stage.step);
  const [activeStageIndex, setActiveStageIndex] = useState(initialMode === "complete" ? scene.stages.length - 1 : initialStageIndex);
  const [answer, setAnswer] = useState<string | null>(null);
  const [wrongNotice, setWrongNotice] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>(initialCompletedSteps);
  const [isFinished, setIsFinished] = useState(initialMode === "complete");
  const [hasEverFinished, setHasEverFinished] = useState(initialMode === "complete" || Boolean(scene.isCompleted));
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [sequenceAnswer, setSequenceAnswer] = useState<string[]>([]);
  const [selectedMatchLeft, setSelectedMatchLeft] = useState<string | null>(null);
  const [matchingAnswer, setMatchingAnswer] = useState<Record<string, string>>({});
  const [fillBlankAnswer, setFillBlankAnswer] = useState<string[]>([]);
  const [oxReadySteps, setOxReadySteps] = useState<number[]>([]);
  const [oxAnswers, setOxAnswers] = useState<Record<number, string>>({});
  const [reflectionText, setReflectionText] = useState("");
  const [studentAccessToken, setStudentAccessToken] = useState<string | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  const [isCompletingMission, setIsCompletingMission] = useState(false);
  const [stageFrameScale, setStageFrameScale] = useState(1);
  const [isStageFrameReady, setIsStageFrameReady] = useState(false);
  const noticeCounter = useRef(0);
  const runtimeStartedRef = useRef(false);
  const pendingAnswerSubmissionsRef = useRef<PendingAnswerSubmission[]>([]);

  const activeStage = scene.stages[activeStageIndex] ?? scene.stages[0];
  const activeQuestion = useMemo(
    () =>
      scene.stageQuestions?.find((question) => question.step === activeStage.step) ?? {
      step: activeStage.step,
      prompt: scene.question.prompt,
      kind: "quiz" as const,
      choices: scene.question.choices,
      correctAnswer: scene.question.correctAnswer,
      hint: scene.question.hint,
      correctFeedback: scene.question.correctFeedback,
      wrongFeedback: scene.question.wrongFeedback,
      completionTitle: "스테이지 완료",
      completionMessage: "다음 단계로 이동할 준비가 되었어요.",
      visualActiveIndex: scene.visual.activeIndex,
      },
    [activeStage.step, scene.question, scene.stageQuestions, scene.visual.activeIndex],
  );
  const isOxReady = activeQuestion.kind === "ox" && oxReadySteps.includes(activeStage.step);
  const isRealtimeStage =
    activeStage.step === 4 &&
    activeQuestion.stageRole === "realtime_practice" &&
    (activeQuestion.templateType === "realtime_teach_back" || activeQuestion.templateType === "realtime_roleplay");
  const realtimePracticeCopy = isRealtimeStage ? getRealtimePracticeCopy(scene, activeQuestion) : null;
  const isChoiceStage = activeQuestion.kind === "quiz" || activeQuestion.kind === "scenario" || isOxReady;
  const isStructuredStage = activeQuestion.kind === "sequence" || activeQuestion.kind === "cardMatching" || activeQuestion.kind === "fillBlank";
  const isCorrect = (isChoiceStage || isStructuredStage) && answer === activeQuestion.correctAnswer;
  const isStageComplete = completedSteps.includes(activeStage.step);
  const isLastStage = activeStageIndex === scene.stages.length - 1;

  useEffect(() => {
    const resizeStageFrame = () => {
      const availableWidth = Math.max(320, window.innerWidth - 32);
      const availableHeight = Math.max(320, window.innerHeight - 32);
      setStageFrameScale(Math.min(availableWidth / STAGE_FRAME_WIDTH, availableHeight / STAGE_FRAME_HEIGHT));
      setIsStageFrameReady(true);
    };

    resizeStageFrame();
    window.addEventListener("resize", resizeStageFrame);
    return () => window.removeEventListener("resize", resizeStageFrame);
  }, []);

  useEffect(() => {
    if (
      previewMode ||
      initialMode === "complete" ||
      scene.status !== "published" ||
      !scene.contentId ||
      !student.accessCode ||
      runtimeStartedRef.current
    ) {
      return;
    }

    runtimeStartedRef.current = true;
    let ignore = false;

    async function startRuntime() {
      try {
        const access = await studentAccess({ accessCode: student.accessCode ?? "" });
        const attempt = await startStudentMission(scene.contentId ?? "", { token: access.session.accessToken });
        if (ignore) return;
        setStudentAccessToken(access.session.accessToken);
        setAttemptId(attempt.id);
        setRuntimeError(null);
      } catch {
        if (ignore) return;
        setRuntimeError("학습 기록 저장 연결을 시작하지 못했습니다. 잠시 뒤 다시 시도해 주세요.");
      }
    }

    startRuntime();

    return () => {
      ignore = true;
    };
  }, [initialMode, previewMode, scene.contentId, scene.status, student.accessCode]);

  useEffect(() => {
    if (!previewMode) return;
    window.parent.postMessage({ type: "student-preview-stage", step: activeStage.step }, window.location.origin);
  }, [activeStage.step, previewMode]);

  useEffect(() => {
    if (initialMode === "complete" || isFinished) return;

    const stepParam = String(activeStage.step);
    if (searchParams.get("step") === stepParam) return;

    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.set("step", stepParam);
    nextParams.delete("complete");
    router.replace(`${pathname}?${nextParams.toString()}`, { scroll: false });
  }, [activeStage.step, initialMode, isFinished, pathname, router, searchParams]);

  const progressPercent = Math.round((completedSteps.length / scene.stages.length) * 100);
  const activeVisual = {
    ...scene.visual,
    helperLabel: activeStage.title,
    activeIndex: activeQuestion.visualActiveIndex ?? scene.visual.activeIndex,
  };

  const feedback = useMemo(() => {
    if (isFinished) return "오늘의 모든 스테이지를 끝냈어요. 학습 길에서 결과를 확인할 수 있어요.";
    if (!answer) return activeQuestion.hint;
    if (isCorrect) return activeQuestion.correctFeedback;
    return activeQuestion.wrongFeedback;
  }, [activeQuestion, answer, isCorrect, isFinished]);

  const canPersistRuntime = !previewMode && scene.status === "published" && Boolean(scene.contentId && attemptId && studentAccessToken);

  const queueAnswerSubmission = (question: StageQuestion, answerPayload: Record<string, unknown>) => {
    if (previewMode || scene.status !== "published" || !question.stageId) return;
    pendingAnswerSubmissionsRef.current.push({ stageId: question.stageId, answer: answerPayload });
  };

  const flushPendingAnswerSubmissions = async (contentId: string, activeAttemptId: string, activeToken: string) => {
    const pending = pendingAnswerSubmissionsRef.current;
    if (pending.length === 0) return;

    pendingAnswerSubmissionsRef.current = [];
    for (const item of pending) {
      await submitStudentMissionStage(contentId, item.stageId, { attemptId: activeAttemptId, answer: item.answer }, { token: activeToken });
    }
  };

  const persistStudentEvent = (question: StageQuestion, eventType: string, payloadJson: Record<string, unknown>) => {
    if (!canPersistRuntime || !scene.contentId || !studentAccessToken) return;

    void saveStudentMissionEvent(
      scene.contentId,
      {
        attemptId,
        stageId: question.stageId,
        eventType,
        payloadJson,
      },
      { token: studentAccessToken },
    ).catch(() => {
      setRuntimeError("학습 기록 일부를 저장하지 못했습니다. 다음 기록 저장을 다시 시도합니다.");
    });
  };

  const submitRuntimeAnswer = (question: StageQuestion, answerPayload: Record<string, unknown>) => {
    if (!canPersistRuntime || !scene.contentId || !attemptId || !studentAccessToken || !question.stageId) {
      queueAnswerSubmission(question, answerPayload);
      return;
    }

    void submitStudentMissionStage(scene.contentId, question.stageId, { attemptId, answer: answerPayload }, { token: studentAccessToken })
      .then(() => setRuntimeError(null))
      .catch(() => {
        setRuntimeError("답안 기록을 저장하지 못했습니다. 학습은 계속할 수 있어요.");
      });
  };

  const toRuntimeChoicePayload = (question: StageQuestion, choice: string) => {
    return question.runtimeChoiceAnswers?.[choice] ?? { choiceText: choice };
  };

  const selectAnswer = (choice: string) => {
    if (!activeQuestion.correctAnswer) return;

    setAnswer(choice);
    setAttempts((value) => value + 1);
    submitRuntimeAnswer(activeQuestion, toRuntimeChoicePayload(activeQuestion, choice));

    if (choice === activeQuestion.correctAnswer) {
      setWrongNotice(null);
      setCompletedSteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
    } else {
      noticeCounter.current += 1;
      const noticeId = `${choice}-${noticeCounter.current}`;
      setWrongNotice(noticeId);
      window.setTimeout(() => {
        setWrongNotice((current) => (current === noticeId ? null : current));
        setAnswer((current) => (current === choice ? null : current));
      }, 1500);
    }
  };

  const markStructuredAnswer = (value: string) => {
    if (!activeQuestion.correctAnswer) return;

    setAnswer(value);
    setAttempts((current) => current + 1);
    submitRuntimeAnswer(
      activeQuestion,
      value === activeQuestion.correctAnswer && activeQuestion.runtimeCorrectAnswer
        ? activeQuestion.runtimeCorrectAnswer
        : { answer: value },
    );

    if (value === activeQuestion.correctAnswer) {
      setWrongNotice(null);
      setCompletedSteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
    } else {
      noticeCounter.current += 1;
      const noticeId = `${value}-${noticeCounter.current}`;
      setWrongNotice(noticeId);
      window.setTimeout(() => {
        setWrongNotice((current) => (current === noticeId ? null : current));
        setAnswer((current) => (current === value ? null : current));
        setSequenceAnswer([]);
        setSelectedMatchLeft(null);
        setMatchingAnswer({});
        setFillBlankAnswer([]);
        setOxAnswers({});
      }, 1500);
    }
  };

  const selectOxAnswer = (itemIndex: number, choice: string) => {
    if (isStageComplete) return;

    const itemCount = activeQuestion.oxItems?.length ?? (activeQuestion.oxStatement ? 1 : 0);
    const nextAnswers = { ...oxAnswers, [itemIndex]: choice };
    setOxAnswers(nextAnswers);

    if (Object.keys(nextAnswers).length === itemCount) {
      markStructuredAnswer(
        Array.from({ length: itemCount }, (_, index) => nextAnswers[index])
          .filter(Boolean)
          .join("|"),
      );
    }
  };

  const pickSequenceItem = (id: string) => {
    if (sequenceAnswer.includes(id) || isStageComplete) return;

    const itemCount = activeQuestion.sequenceItems?.length ?? 0;
    const nextAnswer = Array.from({ length: itemCount }, (_, index) => sequenceAnswer[index] ?? "");
    const emptyIndex = nextAnswer.findIndex((value) => !value);

    if (emptyIndex < 0) return;

    nextAnswer[emptyIndex] = id;
    setSequenceAnswer(nextAnswer);

    if (nextAnswer.every(Boolean)) {
      markStructuredAnswer(nextAnswer.join(">"));
    }
  };

  const connectMatchingCard = (rightId: string) => {
    if (!selectedMatchLeft || isStageComplete) return;

    setAttempts((current) => current + 1);

    const expectedPair = activeQuestion.matchingPairs?.find((pair) => pair.leftId === selectedMatchLeft);

    if (expectedPair?.rightId !== rightId) {
      persistStudentEvent(activeQuestion, "answer_submitted", {
        answer: { matches: { [selectedMatchLeft]: rightId } },
        isCorrect: false,
      });
      noticeCounter.current += 1;
      const noticeId = `${selectedMatchLeft}-${rightId}-${noticeCounter.current}`;
      setWrongNotice(noticeId);
      setSelectedMatchLeft(null);
      window.setTimeout(() => {
        setWrongNotice((current) => (current === noticeId ? null : current));
      }, 1500);
      return;
    }

    const nextAnswer = { ...matchingAnswer, [selectedMatchLeft]: rightId };
    setMatchingAnswer(nextAnswer);
    setSelectedMatchLeft(null);

    if (Object.keys(nextAnswer).length === activeQuestion.matchingPairs?.length) {
      const finalAnswer = activeQuestion.matchingPairs.map((pair) => `${pair.leftId}:${nextAnswer[pair.leftId]}`).join("|");
      submitRuntimeAnswer(activeQuestion, { matches: nextAnswer });
      setAnswer(finalAnswer);
      setWrongNotice(null);
      setCompletedSteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
    }
  };

  const fillBlank = (id: string) => {
    if (isStageComplete) return;

    const blankCount = getFillBlankCount(activeQuestion);
    const nextAnswer = [...fillBlankAnswer, id].slice(0, blankCount);
    setFillBlankAnswer(nextAnswer);

    if (nextAnswer.length === blankCount) {
      markStructuredAnswer(nextAnswer.join("|"));
    }
  };

  const completeOpenStage = () => {
    persistStudentEvent(activeQuestion, "stage_completed", { kind: "concept_acknowledged" });
    setCompletedSteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
    setAnswer("completed");
  };

  const completeRealtimePractice = () => {
    if (!isRealtimeStage) return;
    persistStudentEvent(activeQuestion, "realtime_practice_completed", {
      mode: "openai_realtime",
      prompt: activeQuestion.realtimePracticeSpec?.firstPrompt ?? activeQuestion.prompt,
    });
    setAttempts((current) => current + 1);
    setCompletedSteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
    setAnswer("realtime-completed");
  };

  const showOxCheck = () => {
    setAnswer(null);
    setWrongNotice(null);
    setOxAnswers({});
    setOxReadySteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
  };

  const goToNextStage = () => {
    setIsTransitioning(true);

    window.setTimeout(() => {
      if (isLastStage) {
        setIsFinished(true);
        setHasEverFinished(true);
      } else {
        setActiveStageIndex((index) => index + 1);
      }

      setAnswer(null);
      setWrongNotice(null);
      setAttempts(0);
      setSequenceAnswer([]);
      setSelectedMatchLeft(null);
      setMatchingAnswer({});
      setFillBlankAnswer([]);
      setOxAnswers({});
      window.setTimeout(() => setIsTransitioning(false), 80);
    }, 120);
  };

  const resetMission = () => {
    setIsTransitioning(false);
    setActiveStageIndex(0);
    setAnswer(null);
    setWrongNotice(null);
    setAttempts(0);
    setCompletedSteps(hasEverFinished ? scene.stages.map((stage) => stage.step) : []);
    setIsFinished(false);
    setSequenceAnswer([]);
    setSelectedMatchLeft(null);
    setMatchingAnswer({});
    setFillBlankAnswer([]);
    setOxReadySteps([]);
    setOxAnswers({});
    setReflectionText("");
    setRuntimeError(null);
    setIsCompletingMission(false);
  };

  const completeMissionAndReturn = async () => {
    if (!reflectionText.trim() || isCompletingMission) return;

    if (previewMode) {
      router.push(nextHref);
      return;
    }

    if (!scene.contentId) {
      router.push(nextHref);
      return;
    }

    setIsCompletingMission(true);
    setRuntimeError(null);

    try {
      let activeToken = studentAccessToken;
      let activeAttemptId = attemptId;

      if ((!activeToken || !activeAttemptId) && student.accessCode) {
        const access = await studentAccess({ accessCode: student.accessCode });
        const attempt = await startStudentMission(scene.contentId, { token: access.session.accessToken });
        activeToken = access.session.accessToken;
        activeAttemptId = attempt.id;
        setStudentAccessToken(activeToken);
        setAttemptId(activeAttemptId);
      }

      if (!activeToken || !activeAttemptId) {
        throw new Error("runtime_not_ready");
      }

      await flushPendingAnswerSubmissions(scene.contentId, activeAttemptId, activeToken);

      const reflection = reflectionText.trim();
      await saveStudentMissionReflection(
        scene.contentId,
        {
          attemptId: activeAttemptId,
          reflectionChoice: reflection,
          shortText: reflection,
        },
        { token: activeToken },
      );
      await completeStudentMission(scene.contentId, activeAttemptId, { token: activeToken });
    } catch {
      // 기록 저장 실패가 학생의 완료 이동을 막지 않도록 한다.
    } finally {
      router.push(nextHref);
    }
  };

  return (
    <main className="relative grid min-h-screen place-items-center overflow-hidden bg-[#e7edf4] p-4 text-[#1f211d]">
      {!previewMode && (
      <Link
        href="/"
        className="fixed bottom-6 right-6 z-50 rounded-full border border-[#25466f] bg-[#1f3a5f] px-5 py-3 text-base font-black text-white shadow-[0_12px_30px_rgba(31,58,95,0.25)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_34px_rgba(31,58,95,0.32)]"
      >
        홈으로
      </Link>
      )}
      <div
        style={{
          width: isStageFrameReady ? STAGE_FRAME_WIDTH * stageFrameScale : STAGE_FRAME_WIDTH,
          height: isStageFrameReady ? STAGE_FRAME_HEIGHT * stageFrameScale : STAGE_FRAME_HEIGHT,
        }}
      >
        <div
          className="relative origin-top-left rounded-[44px] bg-[#202939] p-4 shadow-[0_30px_90px_rgba(15,23,42,0.28)]"
          style={{
            width: STAGE_FRAME_WIDTH,
            height: STAGE_FRAME_HEIGHT,
            transform: isStageFrameReady ? `scale(${stageFrameScale})` : "scale(1)",
          }}
        >
          <div className="absolute bottom-5 left-1/2 h-1.5 w-24 -translate-x-1/2 rounded-full bg-white/22" />

          <div className="h-full overflow-hidden rounded-[30px] bg-[#fbfaf4]">
            <header className="flex h-[92px] items-center justify-between gap-5 border-b border-[#efe7d7] bg-[#fbfaf4]/95 px-10">
              <div className="flex min-w-0 items-center gap-4">
                {isFinished ? (
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border text-sm font-black shadow-sm"
                    style={{ borderColor: theme.border, backgroundColor: theme.accentPale, color: theme.accentStrong }}
                    aria-hidden="true"
                  >
                    {student.displayName.slice(0, 1)}
                  </div>
                ) : (
                  <Link
                    href={pathHref}
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border text-xl font-black shadow-sm transition duration-200 hover:-translate-y-0.5 hover:scale-105 hover:shadow-[0_12px_26px_rgba(57,78,97,0.16)]"
                    style={{ borderColor: theme.border, backgroundColor: theme.accentPale, color: theme.accent }}
                    aria-label="학생 시작 화면으로 돌아가기"
                  >
                    ←
                  </Link>
                )}
                <div className="min-w-0">
                  <p className="text-xs font-bold text-[#6d746c]">
                    {student.displayName} · {student.grade}
                  </p>
                  <h1 className="truncate text-2xl font-black">{scene.missionTitle}</h1>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span
                  className="rounded-full px-4 py-2 text-sm font-black"
                  style={{ backgroundColor: theme.accentSoft, color: theme.accentStrong }}
                >
                  진행 {progressPercent}%
                </span>
              </div>
            </header>

            <section
              className={`grid h-[calc(100%-92px)] gap-4 px-7 py-5 ${
                ((activeQuestion.kind === "sequence" || activeQuestion.kind === "cardMatching") && !isFinished) || (isRealtimeStage && !isFinished)
                  ? "grid-cols-1"
                  : "grid-cols-[minmax(0,1fr)_minmax(350px,0.58fr)]"
              }`}
            >
              <div
                className={`flex min-h-0 flex-col transition duration-300 ease-out ${
                  isTransitioning ? "opacity-70 blur-[1px]" : "opacity-100 blur-0"
                }`}
              >
                <div className="flex items-center justify-between gap-5">
                  <div>
                    <p className="text-sm font-black" style={{ color: theme.accent }}>
                      스테이지 {activeStage.step} · 시도 {attempts}회
                    </p>
                    <h2 className="mt-1 line-clamp-2 text-3xl font-black leading-tight break-keep">
                      {isFinished ? "훌륭해요!" : activeStage.title}
                    </h2>
                  </div>
                  <ProgressTrail
                    stages={scene.stages}
                    activeStep={activeStage.step}
                    completedSteps={completedSteps}
                    isFinished={isFinished}
                    theme={theme}
                  />
                </div>

                <div
                  key={`stage-board-${activeStage.step}-${activeQuestion.kind}`}
                  className="relative mt-5 min-h-0 flex-1 overflow-hidden animate-[stagePopIn_360ms_cubic-bezier(0.16,1,0.3,1)_both]"
                >
                  {isFinished ? (
                    <div
                      className="grid h-full min-h-[300px] grid-rows-[auto_auto_1fr] rounded-[24px] border p-5 text-center shadow-[inset_0_-12px_0_rgba(39,174,96,0.08)]"
                      style={{ borderColor: theme.border, backgroundColor: theme.accentPale }}
                    >
                      <div className="flex flex-col items-center">
                        <MiniStar />
                        <h3 className="mt-1.5 text-4xl font-black" style={{ color: theme.accentStrong }}>
                          완료!
                        </h3>
                        <p className="mt-2 max-w-[520px] text-lg font-black leading-7 break-keep">
                          오늘의 4단계 미션을 모두 해냈어요.
                        </p>
                      </div>
                      <div className="mt-4 grid w-full grid-cols-4 gap-2">
                        {scene.stages.map((stage) => (
                          <div key={stage.step} className="rounded-[16px] bg-white px-3 py-3 text-center shadow-sm">
                            <p className="text-xs font-black" style={{ color: theme.accentStrong }}>
                              STEP {stage.step}
                            </p>
                            <p className="mt-1 line-clamp-2 min-h-10 text-sm font-black leading-5 break-keep">{stage.title}</p>
                          </div>
                        ))}
                      </div>
                      <div className="mt-5 min-h-0 rounded-[20px] border bg-white/92 p-4 text-left shadow-sm" style={{ borderColor: theme.border }}>
                        <label htmlFor="student-reflection" className="text-sm font-black" style={{ color: theme.accentStrong }}>
                          오늘 한마디
                        </label>
                        <p className="mt-2 text-lg font-black leading-7 break-keep text-[#25312a]">
                          오늘 어땠는지 한 문장으로 남겨볼까요?
                        </p>
                        <textarea
                          id="student-reflection"
                          value={reflectionText}
                          onChange={(event) => setReflectionText(event.target.value)}
                          className="mt-3 h-24 w-full resize-none rounded-[18px] border border-[#dce5ec] bg-[#fbfdff] px-4 py-3 text-base font-bold leading-7 outline-none transition focus:border-[#94d86a] focus:bg-white"
                          placeholder="여기에 내 생각을 적어봐요."
                        />
                        {runtimeError && (
                          <p className="mt-2 text-sm font-black leading-6 text-[#b45309]">
                            {runtimeError}
                          </p>
                        )}
                      </div>
                    </div>
                  ) : (
                    activeQuestion.kind === "sequence" ? (
                      <SequenceStageBoard
                        visual={activeVisual}
                        question={activeQuestion}
                        selected={sequenceAnswer}
                        theme={theme}
                        onPick={pickSequenceItem}
                        onReset={() => {
                          setSequenceAnswer([]);
                          setAnswer(null);
                          setWrongNotice(null);
                        }}
                      />
                    ) : activeQuestion.kind === "cardMatching" ? (
                      <CardMatchingTemplate
                        question={activeQuestion}
                        pairs={matchingAnswer}
                        selectedLeft={selectedMatchLeft}
                        theme={theme}
                        onLeft={(id) => setSelectedMatchLeft(id)}
                        onRight={connectMatchingCard}
                      />
                    ) : isRealtimeStage ? (
                      <RealtimePracticeRoom
                        question={activeQuestion}
                        scene={scene}
                        theme={theme}
                        isComplete={isStageComplete}
                        contentId={scene.contentId}
                        stageId={activeQuestion.stageId}
                        attemptId={attemptId}
                        token={studentAccessToken}
                        accessCode={student.accessCode}
                        onRuntimeReady={(nextToken, nextAttemptId) => {
                          setStudentAccessToken(nextToken);
                          setAttemptId(nextAttemptId);
                          setRuntimeError(null);
                        }}
                        onComplete={completeRealtimePractice}
                        onFinish={goToNextStage}
                      />
                    ) : (
                      <StageVisualBoard visual={activeVisual} question={activeQuestion} theme={theme} />
                    )
                  )}
                </div>

                {activeQuestion.kind !== "sequence" && activeQuestion.kind !== "cardMatching" && !isRealtimeStage && (
                  <div
                    className="mt-3 flex items-center gap-3 rounded-[18px] border px-4 py-3 text-sm font-bold leading-6 shadow-sm"
                    style={{ borderColor: theme.highlight, backgroundColor: `${theme.highlight}99`, color: theme.highlightText }}
                  >
                    <HintStar />
                    <p className="line-clamp-2 break-keep">
                      {isFinished
                        ? "다시 해보거나 학습 길로 돌아갈 수 있어요."
                        : isRealtimeStage
                          ? "4단계에서만 열리는 실시간 발화 연습입니다."
                          : activeQuestion.hint}
                    </p>
                  </div>
                )}

                {(activeQuestion.kind === "sequence" || activeQuestion.kind === "cardMatching") && !isFinished && (
                  <div className="relative mt-3">
                    <FloatingStageFeedback
                      showSuccess={((answer && isCorrect) || isStageComplete) && !isFinished}
                      showWrong={Boolean(wrongNotice) && !isStageComplete && !isFinished}
                      title={activeQuestion.completionTitle}
                      message={activeQuestion.completionMessage}
                      wrongMessage={activeQuestion.wrongFeedback}
                      theme={theme}
                    />
                    <button
                      onClick={goToNextStage}
                      disabled={(!isCorrect && !isStageComplete) || isTransitioning}
                      className={`w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.28)] transition duration-200 ${
                        isCorrect || isStageComplete
                          ? "hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.32)]"
                          : "cursor-not-allowed opacity-45"
                      } disabled:hover:translate-y-0`}
                      style={{ backgroundColor: isCorrect || isStageComplete ? theme.accent : "#9aa39b" }}
                    >
                      다음 스테이지
                    </button>
                  </div>
                )}
              </div>

              <aside
                className={`min-h-0 grid-rows-[minmax(0,1fr)_auto] gap-3 overflow-hidden transition duration-200 ease-out ${
                  ((activeQuestion.kind === "sequence" || activeQuestion.kind === "cardMatching") && !isFinished) || (isRealtimeStage && !isFinished) ? "hidden" : "grid"
                } ${
                  isTransitioning ? "opacity-70 blur-[1px]" : "opacity-100 blur-0"
                }`}
              >
                <div className="relative min-h-0 self-center overflow-y-auto rounded-[24px] border border-[#dce5ec] bg-white p-5 shadow-[0_18px_48px_rgba(57,78,97,0.10)]">
                  <h3 className="text-[1.2rem] font-black leading-snug break-keep">
                    {isFinished
                      ? `${scene.missionTitle}, 모두 완료했어요`
                      : isRealtimeStage
                        ? realtimePracticeCopy?.title
                        : activeQuestion.prompt}
                  </h3>

                  <StageInlineNotice
                    answer={answer}
                    isCorrect={isCorrect}
                    isStageComplete={isStageComplete}
                    isFinished={isFinished}
                    title={activeQuestion.completionTitle}
                    message={activeQuestion.completionMessage}
                    feedback={feedback}
                    theme={theme}
                    wrongNotice={wrongNotice}
                  />

                  <div
                    key={`${activeQuestion.step}-${activeQuestion.kind}-${isOxReady ? "check" : "intro"}`}
                    className="mt-3 animate-[stagePopIn_360ms_cubic-bezier(0.16,1,0.3,1)_both]"
                  >
                  {isFinished ? (
                    <div className="space-y-3">
                      <div
                        className="rounded-[18px] px-4 py-4 text-base font-black leading-7"
                        style={{ backgroundColor: theme.accentSoft, color: theme.accentStrong }}
                      >
                        완료한 스테이지 {completedSteps.length}개
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={resetMission}
                          disabled={isTransitioning}
                          className="rounded-[18px] border bg-white px-4 py-3 text-center text-base font-black shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(57,78,97,0.12)] disabled:opacity-70 disabled:hover:translate-y-0 disabled:hover:shadow-sm"
                          style={{ borderColor: theme.border, color: theme.accentStrong }}
                        >
                          다시 하기
                        </button>
                        <button
                          type="button"
                          disabled={!reflectionText.trim() || isCompletingMission}
                          onClick={completeMissionAndReturn}
                          className={`rounded-[18px] px-4 py-3 text-center text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.28)] transition duration-200 ${
                            reflectionText.trim() && !isCompletingMission
                              ? "hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.32)]"
                              : "cursor-not-allowed opacity-45"
                          }`}
                          style={{ backgroundColor: reflectionText.trim() && !isCompletingMission ? theme.accent : "#9aa39b" }}
                        >
                          {isCompletingMission ? "저장 중" : "학습 길로"}
                        </button>
                      </div>
                    </div>
                  ) : activeQuestion.kind === "ox" ? (
                    isOxReady ? (
                      <OxTemplate
                        question={activeQuestion}
                        answers={oxAnswers}
                        isCorrect={isCorrect}
                        theme={theme}
                        onSelect={selectOxAnswer}
                        showConcept={false}
                      />
                    ) : (
                      <ConceptCards question={activeQuestion} theme={theme} />
                    )
                  ) : activeQuestion.kind === "concept" || activeQuestion.kind === "summary" ? (
                    <ConceptCards question={activeQuestion} theme={theme} />
                  ) : activeQuestion.kind === "sequence" ? (
                    <div className="space-y-3">
                      {activeQuestion.body && (
                        <p className="rounded-[18px] bg-[#fbfdff] px-4 py-4 text-base font-bold leading-7 text-[#4b5563]">
                          {activeQuestion.body}
                        </p>
                      )}
                      <div className="rounded-[18px] border px-4 py-4" style={{ borderColor: theme.border, backgroundColor: theme.accentPale }}>
                        <p className="text-base font-black" style={{ color: theme.accentStrong }}>
                          순서 배열
                        </p>
                        <p className="mt-1 text-sm font-bold leading-6 text-[#596157]">
                          왼쪽 보드에서 카드를 끌어 순서 칸에 놓아보세요.
                        </p>
                      </div>
                    </div>
                  ) : activeQuestion.kind === "cardMatching" ? (
                    <CardMatchingTemplate
                      question={activeQuestion}
                      pairs={matchingAnswer}
                      selectedLeft={selectedMatchLeft}
                      theme={theme}
                      onLeft={(id) => setSelectedMatchLeft(id)}
                      onRight={connectMatchingCard}
                    />
                  ) : isRealtimeStage ? (
                    <div className="rounded-[18px] px-4 py-4 text-sm font-bold leading-6" style={{ backgroundColor: theme.accentSoft, color: theme.accentStrong }}>
                      {realtimePracticeCopy?.sceneLine ?? activeQuestion.prompt}
                    </div>
                  ) : activeQuestion.kind === "fillBlank" ? (
                    <FillBlankTemplate
                      question={activeQuestion}
                      slots={fillBlankAnswer}
                      theme={theme}
                      onPick={fillBlank}
                      onReset={() => {
                        setFillBlankAnswer([]);
                        setAnswer(null);
                        setWrongNotice(null);
                      }}
                    />
                  ) : activeQuestion.kind === "scenario" ? (
                    <div className="space-y-3">
                      <div className="space-y-2 rounded-[18px] bg-[#fbfdff] px-4 py-4">
                        {activeQuestion.scenarioLines?.map((line, index) => (
                          <div key={`${line.speaker}-${line.text}-${index}`} className="leading-6">
                            <p className="text-xs font-black" style={{ color: theme.accentStrong }}>
                              {line.speaker}
                            </p>
                            <p className="text-sm font-bold text-[#4b5563]">{line.text}</p>
                          </div>
                        ))}
                      </div>
                      <div className="grid gap-3">
                        {activeQuestion.choices?.map((choice, index) => (
                          <ChoiceButton
                            key={`${choice}-${index}`}
                            label={choice}
                            prefix={`${index + 1}`}
                            selected={answer === choice}
                            correct={choice === activeQuestion.correctAnswer}
                            disabled={isCorrect}
                            theme={theme}
                            onClick={() => selectAnswer(choice)}
                          />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="grid gap-4 pt-4">
                      {activeQuestion.choices?.map((choice, index) => (
                        <ChoiceButton
                          key={`${choice}-${index}`}
                          label={choice}
                          prefix={`${index + 1}`}
                          selected={answer === choice}
                          correct={choice === activeQuestion.correctAnswer}
                          disabled={isCorrect}
                          theme={theme}
                          onClick={() => selectAnswer(choice)}
                        />
                      ))}
                    </div>
                  )}
                  </div>

                </div>

                {isFinished ? null : isRealtimeStage && !isStageComplete ? (
                  <button
                    onClick={completeRealtimePractice}
                    disabled={isTransitioning}
                    className="w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.28)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.32)] disabled:opacity-70 disabled:hover:translate-y-0"
                    style={{ backgroundColor: theme.accent }}
                  >
                    {activeQuestion.actionLabel ?? "실시간 연습 시작하기"}
                  </button>
                ) : isCorrect || isStageComplete ? (
                  <button
                    onClick={goToNextStage}
                    disabled={isTransitioning}
                    className="w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.28)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.32)] disabled:opacity-70 disabled:hover:translate-y-0"
                    style={{ backgroundColor: theme.accent }}
                  >
                    {isLastStage ? "오늘 학습 완료하기 →" : "다음 스테이지 →"}
                  </button>
                ) : activeQuestion.kind === "ox" && !isOxReady ? (
                  <button
                    onClick={showOxCheck}
                    className="w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.18)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.26)]"
                    style={{ backgroundColor: theme.accent }}
                  >
                    개념 확인하기
                  </button>
                ) : !isChoiceStage && !isStructuredStage ? (
                  <button
                    onClick={completeOpenStage}
                    className="w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.18)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.26)]"
                    style={{ backgroundColor: theme.accent }}
                  >
                    {activeQuestion.actionLabel ?? "확인했어요"}
                  </button>
                ) : (
                  <button
                    className="w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.18)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.26)]"
                    style={{ backgroundColor: `${theme.accent}99` }}
                  >
                    {activeQuestion.kind === "fillBlank"
                      ? "숫자를 골라 빈칸에 넣어볼까요"
                      : isStructuredStage
                        ? "카드를 눌러 완성해볼까요"
                        : answer
                          ? "다시 골라볼까요"
                          : "정답을 찾아볼까요"}
                  </button>
                )}
              </aside>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
