"use client";

import Link from "next/link";
import type { DragEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { SceneTheme, SceneVisual, StageQuestion, StudentContext } from "@/lib/demo-data";

function MiniStar() {
  return (
    <div className="relative h-16 w-16 shrink-0">
      <div
        className="absolute left-2 top-1 z-10 h-12 w-12 bg-[#ffd84d] shadow-[inset_0_-5px_0_rgba(184,122,0,0.16),0_10px_20px_rgba(184,122,0,0.14)]"
        style={{
          clipPath:
            "polygon(50% 0%, 61% 34%, 97% 35%, 68% 55%, 79% 91%, 50% 69%, 21% 91%, 32% 55%, 3% 35%, 39% 34%)",
        }}
      />
      <div className="absolute left-[23px] top-[21px] z-20 h-1.5 w-1.5 rounded-full bg-[#25312a]" />
      <div className="absolute left-[37px] top-[21px] z-20 h-1.5 w-1.5 rounded-full bg-[#25312a]" />
      <div className="absolute left-[28px] top-[30px] z-20 h-2.5 w-4 rounded-b-full bg-[#25312a]" />
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

function LearningVisual({ visual, compact = false }: { visual: SceneVisual; compact?: boolean }) {
  if (visual.kind === "emotion") return <EmotionVisual visual={visual} />;
  if (visual.kind === "planner") return <PlannerVisual visual={visual} />;
  return <FractionVisual visual={visual} compact={compact} />;
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
    <div className="pointer-events-none absolute inset-x-0 bottom-[calc(100%+10px)] z-40 grid place-items-center">
      <div
        className={`animate-[stageToastIn_220ms_ease-out_both] rounded-[18px] px-5 py-3 text-center text-sm font-bold leading-6 shadow-[0_18px_42px_rgba(31,41,55,0.18)] ${
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
        {question.conceptCards?.map((card) => (
          <div key={card.title} className="rounded-[18px] border px-4 py-3" style={{ borderColor: theme.border, backgroundColor: theme.accentPale }}>
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
          <div key={item.statement} className="rounded-[18px] bg-white/82 p-3 shadow-sm">
            <p className="text-base font-black leading-7 break-keep">
              <span className="mr-2" style={{ color: theme.accentStrong }}>
                {itemIndex + 1}.
              </span>
              {item.statement}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3">
              {(question.choices ?? ["O", "X"]).map((choice) => {
                const selected = answers[itemIndex] === choice;
                const isItemCorrect = choice === item.correctAnswer;

                return (
                  <button
                    key={`${item.statement}-${choice}`}
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
  onPlace,
  onReset,
}: {
  question: StageQuestion;
  selected: string[];
  theme: SceneTheme;
  onPick: (id: string) => void;
  onPlace: (id: string, index: number) => void;
  onReset: () => void;
}) {
  const items = question.sequenceItems ?? [];
  const slots = Array.from({ length: items.length }, (_, index) => selected[index] ?? "");
  const selectedIds = slots.filter(Boolean);
  const availableItems = items.filter((item) => !selectedIds.includes(item.id));

  const startDrag = (event: DragEvent<HTMLButtonElement>, id: string) => {
    event.dataTransfer.setData("text/plain", id);
    event.dataTransfer.effectAllowed = "move";
  };

  const dropOnSlot = (event: DragEvent<HTMLDivElement>, index: number) => {
    event.preventDefault();
    const id = event.dataTransfer.getData("text/plain");
    if (id) onPlace(id, index);
  };

  return (
    <div className="grid h-full min-h-0 grid-rows-[auto_auto_auto] gap-3 rounded-[22px] border border-[#d9ebc9] bg-[#fbfff7] p-4 shadow-[inset_0_-10px_0_rgba(39,174,96,0.05)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-lg font-black leading-6">분수를 알아보는 순서를 맞춰보세요</p>
          <p className="mt-1 text-xs font-bold leading-5 text-[#596157]">{question.body ?? "카드를 끌어 올바른 순서대로 놓아보세요."}</p>
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

      <div className="rounded-[18px] border border-dashed border-[#cfd8cf] bg-white/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-xs font-black" style={{ color: theme.accentStrong }}>
            순서 칸
          </p>
          <p className="text-[11px] font-bold text-[#8a5a00]">드래그해서 놓기</p>
        </div>
        <div className="mt-2 grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.max(items.length, 1)}, minmax(0, 1fr))` }}>
          {slots.map((id, index) => {
            const item = items.find((candidate) => candidate.id === id);

          return (
            <div
              key={index}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => dropOnSlot(event, index)}
              className={`flex h-[76px] flex-col items-center justify-center rounded-[16px] border-2 border-dashed px-2 py-2 text-center transition ${
                item ? "border-solid bg-white shadow-[0_10px_24px_rgba(57,78,97,0.10)]" : "bg-white/55"
              }`}
              style={{ borderColor: item ? theme.accent : "#cfd8cf" }}
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-black text-white" style={{ backgroundColor: theme.accent }}>
                {index + 1}
              </span>
              <span className={`mt-1 line-clamp-1 text-sm font-black leading-5 break-keep ${item ? "text-[#1f211d]" : "text-[#9aa39b]"}`}>
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

      <div className="rounded-[18px] border border-[#f0dfb4] bg-[#fff9e8] p-3">
        <div className="flex items-center justify-between">
          <p className="text-xs font-black text-[#8a5a00]">카드 트레이</p>
          {availableItems.length > 0 && <p className="text-[11px] font-bold text-[#8a5a00]">클릭해도 배치돼요</p>}
        </div>
        <div className="mt-2 grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.max(items.length, 1)}, minmax(0, 1fr))` }}>
          {items.map((item) => {
            const picked = selectedIds.includes(item.id);

            return (
            <button
              key={item.id}
              draggable={!picked}
              onDragStart={(event) => startDrag(event, item.id)}
              onClick={() => onPick(item.id)}
              disabled={picked}
              className="min-h-[58px] cursor-grab rounded-[16px] border bg-white px-3 py-2 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-[0_12px_24px_rgba(57,78,97,0.12)] active:cursor-grabbing disabled:cursor-default disabled:opacity-35 disabled:hover:translate-y-0 disabled:hover:shadow-sm"
              style={{ borderColor: picked ? theme.accent : "#dde6ee" }}
            >
              <p className="text-sm font-black leading-5 break-keep">{item.label}</p>
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
  onPlace,
  onReset,
}: {
  visual: SceneVisual;
  question: StageQuestion;
  selected: string[];
  theme: SceneTheme;
  onPick: (id: string) => void;
  onPlace: (id: string, index: number) => void;
  onReset: () => void;
}) {
  return (
    <div className="grid h-full min-h-[300px] grid-rows-[minmax(112px,0.32fr)_minmax(330px,1fr)] gap-3">
      <div className="min-h-0 overflow-hidden">
        <LearningVisual visual={visual} compact />
      </div>
      <div className="min-h-0 overflow-hidden">
        <SequenceTemplate question={question} selected={selected} theme={theme} onPick={onPick} onPlace={onPlace} onReset={onReset} />
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
    <div className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-4 rounded-[22px] border border-[#d9ebc9] bg-[#fbfff7] p-5 shadow-[inset_0_-10px_0_rgba(39,174,96,0.05)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-2xl font-black leading-8">서로 맞는 카드를 연결해보세요</p>
          <p className="mt-1 text-sm font-bold leading-6 text-[#596157]">{question.body ?? "왼쪽 카드를 누르고 맞는 오른쪽 카드를 눌러요."}</p>
        </div>
        <div className="rounded-full bg-white px-4 py-2 text-sm font-black shadow-sm" style={{ color: theme.accentStrong }}>
          {matchedCount} / {items.length}
        </div>
      </div>

      <div className="grid min-h-0 grid-cols-[minmax(240px,1fr)_minmax(260px,0.66fr)_minmax(240px,1fr)] items-stretch gap-4">
        <div className="grid min-h-0 gap-3">
          {items.map((item) => {
            const picked = selectedLeft === item.leftId;
            const matched = Boolean(pairs[item.leftId]);
            return (
              <button
                key={item.leftId}
                onClick={() => onLeft(item.leftId)}
                disabled={matched}
                className={`relative z-10 flex min-h-20 items-center rounded-[18px] border bg-white px-5 text-left text-lg font-black shadow-sm transition-all duration-200 ease-out hover:-translate-y-0.5 disabled:hover:translate-y-0 ${
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

        <div className="relative min-h-0 overflow-hidden rounded-[20px] border border-dashed border-[#cfd8cf] bg-white/65 px-4 py-4 text-center">
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
            <div className="mt-4 w-full rounded-[18px] bg-white/90 px-4 py-3 shadow-[0_12px_26px_rgba(57,78,97,0.10)]">
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

        <div className="grid min-h-0 gap-3">
          {rightItems.map((item) => {
            const used = Object.values(pairs).includes(item.rightId);
            return (
              <button
                key={item.rightId}
                onClick={() => onRight(item.rightId)}
                disabled={!selectedLeft || used}
                className="relative z-10 flex min-h-20 items-center rounded-[18px] border bg-white px-5 text-left text-lg font-black shadow-sm transition-all duration-200 ease-out hover:-translate-y-0.5 disabled:opacity-45 disabled:hover:translate-y-0"
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

  return (
    <div className="grid min-h-[360px] grid-rows-[auto_1fr_auto] gap-4 rounded-[22px] border border-[#d9ebc9] bg-[#fbfff7] p-5 shadow-[inset_0_-10px_0_rgba(39,174,96,0.05)]">
      <div className="flex items-start justify-between gap-4">
        {question.body && <p className="min-w-0 text-sm font-bold leading-6 text-[#596157]">{question.body}</p>}
        <button
          onClick={onReset}
          disabled={!hasSlots}
          className="shrink-0 rounded-full border bg-white px-4 py-2 text-sm font-black shadow-sm transition disabled:opacity-35"
          style={{ borderColor: theme.border, color: theme.accentStrong }}
        >
          다시 채우기
        </button>
      </div>

      <div className="flex items-center justify-center rounded-[20px] border border-[#dde6ee] bg-white px-4 py-6 text-center text-2xl font-black leading-[3rem] break-keep">
        <div>
        {question.fillBlankText?.map((part, index) => {
          if (part.kind === "text") return <span key={`${part.value}-${index}`}>{part.value}</span>;
          const value = slots[blankIndex++];
          return (
            <span key={part.value} className="mx-1 inline-flex h-12 min-w-16 items-center justify-center rounded-[14px] border-2 border-dashed align-middle" style={{ borderColor: theme.accent, color: theme.accentStrong }}>
              {value || ""}
            </span>
          );
        })}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 rounded-[20px] border border-[#f0dfb4] bg-[#fff9e8] p-3">
        {question.fillOptions?.map((option) => (
          <button
            key={option.id}
            onClick={() => onPick(option.id)}
            className="h-16 rounded-[18px] border bg-white text-2xl font-black shadow-sm transition hover:-translate-y-0.5"
            style={{ borderColor: slots.includes(option.id) ? theme.accent : "#dde6ee" }}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function StudentStageExperience({
  context,
  initialStep = context.scene.currentStep,
  initialMode = "stage",
  nextHref,
  previewMode = false,
}: {
  context: StudentContext;
  initialStep?: number;
  initialMode?: "stage" | "complete";
  nextHref: string;
  previewMode?: boolean;
}) {
  const { student, scene } = context;
  const theme = scene.theme;
  const initialStageIndex = Math.max(
    0,
    scene.stages.findIndex((stage) => stage.step === initialStep),
  );
  const initialCompletedSteps =
    initialMode === "complete"
      ? scene.stages.map((stage) => stage.step)
      : scene.stages.filter((stage) => stage.step < initialStep).map((stage) => stage.step);
  const [activeStageIndex, setActiveStageIndex] = useState(initialMode === "complete" ? scene.stages.length - 1 : initialStageIndex);
  const [answer, setAnswer] = useState<string | null>(null);
  const [wrongNotice, setWrongNotice] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>(initialCompletedSteps);
  const [isFinished, setIsFinished] = useState(initialMode === "complete");
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [sequenceAnswer, setSequenceAnswer] = useState<string[]>([]);
  const [selectedMatchLeft, setSelectedMatchLeft] = useState<string | null>(null);
  const [matchingAnswer, setMatchingAnswer] = useState<Record<string, string>>({});
  const [fillBlankAnswer, setFillBlankAnswer] = useState<string[]>([]);
  const [oxReadySteps, setOxReadySteps] = useState<number[]>([]);
  const [oxAnswers, setOxAnswers] = useState<Record<number, string>>({});
  const noticeCounter = useRef(0);

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
  const isChoiceStage = activeQuestion.kind === "quiz" || activeQuestion.kind === "scenario" || isOxReady;
  const isStructuredStage = activeQuestion.kind === "sequence" || activeQuestion.kind === "cardMatching" || activeQuestion.kind === "fillBlank";
  const isCorrect = (isChoiceStage || isStructuredStage) && answer === activeQuestion.correctAnswer;
  const isStageComplete = completedSteps.includes(activeStage.step);
  const isLastStage = activeStageIndex === scene.stages.length - 1;

  useEffect(() => {
    if (!previewMode) return;
    window.parent.postMessage({ type: "student-preview-stage", step: activeStage.step }, window.location.origin);
  }, [activeStage.step, previewMode]);

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

  const selectAnswer = (choice: string) => {
    if (!activeQuestion.correctAnswer) return;

    setAnswer(choice);
    setAttempts((value) => value + 1);

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

  const placeSequenceItem = (id: string, index: number) => {
    if (isStageComplete) return;

    const itemCount = activeQuestion.sequenceItems?.length ?? 0;
    const nextAnswer = Array.from({ length: itemCount }, (_, slotIndex) => sequenceAnswer[slotIndex] ?? "");
    const previousIndex = nextAnswer.indexOf(id);

    if (previousIndex >= 0) {
      nextAnswer[previousIndex] = "";
    }

    nextAnswer[index] = id;
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
      setAnswer(finalAnswer);
      setWrongNotice(null);
      setCompletedSteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
    }
  };

  const fillBlank = (id: string) => {
    if (isStageComplete) return;

    const blankCount = activeQuestion.fillBlankText?.filter((part) => part.kind === "blank").length ?? 0;
    const nextAnswer = [...fillBlankAnswer, id].slice(0, blankCount);
    setFillBlankAnswer(nextAnswer);

    if (nextAnswer.length === blankCount) {
      markStructuredAnswer(nextAnswer.join("|"));
    }
  };

  const completeOpenStage = () => {
    setCompletedSteps((steps) => (steps.includes(activeStage.step) ? steps : [...steps, activeStage.step]));
    setAnswer("completed");
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
      } else {
        setActiveStageIndex((index) => index + 1);
      }

      setAnswer(null);
      setWrongNotice(null);
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
    setCompletedSteps([]);
    setIsFinished(false);
    setSequenceAnswer([]);
    setSelectedMatchLeft(null);
    setMatchingAnswer({});
    setFillBlankAnswer([]);
    setOxReadySteps([]);
    setOxAnswers({});
  };

  return (
    <main className="relative flex h-screen overflow-hidden bg-[#e7edf4] p-4 text-[#1f211d]">
      {!previewMode && (
      <Link
        href="/"
        className="fixed bottom-6 right-6 z-50 rounded-full border border-[#25466f] bg-[#1f3a5f] px-5 py-3 text-base font-black text-white shadow-[0_12px_30px_rgba(31,58,95,0.25)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_34px_rgba(31,58,95,0.32)]"
      >
        데모 홈
      </Link>
      )}
      <div className="m-auto">
        <div className="relative aspect-[4/3] h-[min(calc(100vh-32px),820px)] rounded-[44px] bg-[#202939] p-4 shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
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
                    href="/student/path"
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
              className={`grid h-[calc(100%-92px)] gap-5 px-8 py-6 ${
                (activeQuestion.kind === "sequence" || activeQuestion.kind === "cardMatching") && !isFinished
                  ? "grid-cols-1"
                  : "grid-cols-[minmax(0,1fr)_minmax(380px,0.62fr)]"
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
                    <h2 className="mt-1 text-3xl font-black leading-tight">
                      {isFinished ? "오늘 학습을 끝냈어요" : activeStage.title}
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
                  className="mt-5 min-h-0 flex-1 animate-[stagePopIn_360ms_cubic-bezier(0.16,1,0.3,1)_both]"
                >
                  {isFinished ? (
                    <div
                      className="flex h-full min-h-[300px] flex-col items-center justify-center rounded-[24px] border p-6 text-center shadow-[inset_0_-12px_0_rgba(39,174,96,0.08)]"
                      style={{ borderColor: theme.border, backgroundColor: theme.accentPale }}
                    >
                      <MiniStar />
                      <h3 className="mt-4 text-4xl font-black" style={{ color: theme.accentStrong }}>
                        완료!
                      </h3>
                      <p className="mt-3 max-w-[520px] text-lg font-black leading-7">
                        전체, 부분, 분수 표현, 생활 연결까지 모두 해냈어요.
                      </p>
                      <div className="mt-6 grid w-full max-w-[560px] grid-cols-2 gap-3">
                        {scene.stages.map((stage) => (
                          <div key={stage.step} className="rounded-[18px] bg-white px-5 py-4 text-center shadow-sm">
                            <p className="text-sm font-black" style={{ color: theme.accentStrong }}>
                              STEP {stage.step}
                            </p>
                            <p className="mt-1 text-lg font-black leading-snug break-keep">{stage.title}</p>
                          </div>
                        ))}
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
                        onPlace={placeSequenceItem}
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
                    ) : (
                      <LearningVisual visual={activeVisual} />
                    )
                  )}
                </div>

                {activeQuestion.kind !== "sequence" && activeQuestion.kind !== "cardMatching" && (
                  <div
                    className="mt-3 flex items-center gap-3 rounded-[18px] border px-4 py-3 text-sm font-bold leading-6 shadow-sm"
                    style={{ borderColor: theme.highlight, backgroundColor: `${theme.highlight}99`, color: theme.highlightText }}
                  >
                    <MiniStar />
                    <p>{isFinished ? "다시 해보거나 학습 길로 돌아갈 수 있어요." : activeQuestion.hint}</p>
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
                    {isCorrect || isStageComplete ? (
                      <button
                        onClick={goToNextStage}
                        disabled={isTransitioning}
                        className="w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.28)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.32)] disabled:opacity-70 disabled:hover:translate-y-0"
                        style={{ backgroundColor: theme.accent }}
                      >
                        다음 스테이지 →
                      </button>
                    ) : (
                      <button
                        className="w-full rounded-[18px] px-5 py-3 text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.18)]"
                        style={{ backgroundColor: `${theme.accent}99` }}
                      >
                        {activeQuestion.kind === "cardMatching" ? "카드를 연결해볼까요" : "카드를 순서 칸에 놓아볼까요"}
                      </button>
                    )}
                  </div>
                )}
              </div>

              <aside
                className={`min-h-0 grid-rows-[minmax(0,1fr)_auto] gap-3 overflow-hidden transition duration-200 ease-out ${
                  (activeQuestion.kind === "sequence" || activeQuestion.kind === "cardMatching") && !isFinished ? "hidden" : "grid"
                } ${
                  isTransitioning ? "opacity-70 blur-[1px]" : "opacity-100 blur-0"
                }`}
              >
                <div className="relative self-center rounded-[24px] border border-[#dce5ec] bg-white p-5 shadow-[0_18px_48px_rgba(57,78,97,0.10)]">
                  <h3 className="text-[1.35rem] font-black leading-snug break-keep">
                    {isFinished ? `${scene.missionTitle}, 모두 완료했어요` : activeQuestion.prompt}
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
                    <div
                      className="rounded-[18px] px-4 py-4 text-base font-black leading-7"
                      style={{ backgroundColor: theme.accentSoft, color: theme.accentStrong }}
                    >
                      완료한 스테이지 {completedSteps.length}개
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
                        {activeQuestion.scenarioLines?.map((line) => (
                          <div key={`${line.speaker}-${line.text}`} className="leading-6">
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
                            key={choice}
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
                          key={choice}
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

                {isFinished ? (
                  <div className="-mt-1 grid grid-cols-2 gap-3 self-start">
                    <button
                      onClick={resetMission}
                      disabled={isTransitioning}
                      className="rounded-[18px] border bg-white px-4 py-3 text-center text-base font-black shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(57,78,97,0.12)] disabled:opacity-70 disabled:hover:translate-y-0 disabled:hover:shadow-sm"
                      style={{ borderColor: theme.border, color: theme.accentStrong }}
                    >
                      다시 하기
                    </button>
                    <Link
                      href={nextHref}
                      className="rounded-[18px] px-4 py-3 text-center text-base font-black text-white shadow-[0_14px_30px_rgba(39,174,96,0.28)] transition duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_18px_34px_rgba(39,174,96,0.32)]"
                      style={{ backgroundColor: theme.accent }}
                    >
                      학습 길로
                    </Link>
                  </div>
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
                    {isStructuredStage ? "카드를 눌러 완성해볼까요" : answer ? "다시 골라볼까요" : "정답을 찾아볼까요"}
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
