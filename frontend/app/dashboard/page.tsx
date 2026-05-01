"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  reviewItems,
  sessionRecords,
  students,
  supportCases,
  type CaseStatus,
  type SupportCase,
} from "@/lib/demo-data";

type DashboardTab = "info" | "materials" | "records";

const tabs: Array<{ id: DashboardTab; label: string; description: string }> = [
  { id: "info", label: "학생 정보", description: "기본 정보와 현재 학습 상태" },
  { id: "materials", label: "자료 생성·검토", description: "AI 자료를 만들고 수업 전 확인" },
  { id: "records", label: "학습 기록", description: "피드백과 관찰 기록" },
];

const statusTone: Record<CaseStatus, string> = {
  intake: "bg-[#f1f5f9] text-[#475569] border-[#cbd5e1]",
  structured: "bg-[#eff6ff] text-[#1d4ed8] border-[#bfdbfe]",
  goal_set: "bg-[#eff6ff] text-[#1d4ed8] border-[#bfdbfe]",
  scene_review: "bg-[#fff7ed] text-[#9a3412] border-[#fed7aa]",
  follow_up: "bg-[#f0fdf4] text-[#15803d] border-[#bbf7d0]",
};

const learningStatus: Record<CaseStatus, { label: string; progress: number; currentUnit: string; nextLesson: string }> = {
  intake: {
    label: "학습 준비",
    progress: 15,
    currentUnit: "학습 성향 파악",
    nextLesson: "첫 미션 시작",
  },
  structured: {
    label: "기초 확인",
    progress: 35,
    currentUnit: "기초 개념 점검",
    nextLesson: "개념 연결 연습",
  },
  goal_set: {
    label: "수업 진행 중",
    progress: 50,
    currentUnit: "문제 조건 읽기",
    nextLesson: "확인 문항 생성",
  },
  scene_review: {
    label: "AI 자료 확인",
    progress: 63,
    currentUnit: "분수 1/4 이해",
    nextLesson: "빛나는 구역 찾기",
  },
  follow_up: {
    label: "후속 확인",
    progress: 82,
    currentUnit: "반복 학습",
    nextLesson: "보호자 안내",
  },
};

const workflowSteps = ["자료 생성", "자료 검토", "학습", "학습 피드백"];

const reviewStagePreviews = [
  {
    step: 1,
    title: "전체 구역 세기",
    description: "피자 지도가 몇 개의 같은 크기 구역으로 나뉘었는지 먼저 확인합니다.",
    question: "피자 지도는 전체 몇 구역으로 나뉘어 있나요?",
    choices: ["2구역", "3구역", "4구역"],
    imagePrompt: "피자 지도를 4조각으로 명확히 나누고 전체 구역이 잘 보이게 표시",
  },
  {
    step: 2,
    title: "빛나는 구역 찾기",
    description: "전체 중에서 빛나는 한 조각만 찾아 세어봅니다.",
    question: "빛나는 구역은 몇 개인가요?",
    choices: ["1구역", "2구역", "4구역"],
    imagePrompt: "4조각 피자 지도에서 오른쪽 아래 한 조각만 은은하게 빛나게 표시",
  },
  {
    step: 3,
    title: "분수로 문 열기",
    description: "전체 4구역 중 1구역을 분수로 표현합니다.",
    question: "4구역 중 1구역은 몇 분의 몇일까요?",
    choices: ["1/4", "2/4", "4/1"],
    imagePrompt: "4조각 중 1조각이 선택된 장면을 분수 1/4와 연결해 표현",
  },
  {
    step: 4,
    title: "생활 속 분수",
    description: "오늘 배운 표현을 일상 예시와 연결합니다.",
    question: "같은 크기 4조각 중 1조각을 먹었다면 어떻게 표현할까요?",
    choices: ["1/4", "3/4", "4/4"],
    imagePrompt: "생활 속 피자 한 조각 예시를 따뜻하고 단순한 그림으로 표현",
  },
];

const reviewStageReasons: Record<number, string> = {
  1: "분수를 표현하기 전에 전체가 몇 등분인지 확인해 전체-부분 관계의 기준을 세웁니다.",
  2: "전체 중에서 특정 부분만 구분하게 하여 분자의 의미를 시각적으로 연결합니다.",
  3: "앞 단계에서 센 전체와 부분을 실제 분수 기호 1/4로 바꾸는 단계입니다.",
  4: "학습한 분수 표현을 생활 장면에 적용해 개념 전이를 확인합니다.",
};

type ReviewStageDraft = (typeof reviewStagePreviews)[number];

function StatusBadge({ supportCase }: { supportCase: SupportCase }) {
  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-bold ${statusTone[supportCase.status]}`}>
      {learningStatus[supportCase.status].label}
    </span>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-[#f8fafc] p-4">
      <p className="text-sm font-bold text-[#64748b]">{label}</p>
      <p className="mt-2 text-lg font-black leading-7 text-[#172033]">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const [selectedStudentId, setSelectedStudentId] = useState(students[0].id);
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState<DashboardTab>("info");
  const [openReportId, setOpenReportId] = useState<string | null>(null);
  const [openReviewId, setOpenReviewId] = useState<string | null>(null);
  const [selectedFeedbackId, setSelectedFeedbackId] = useState<string | null>(null);
  const [approvedMaterialIds, setApprovedMaterialIds] = useState<string[]>([]);
  const [appliedMaterialIds, setAppliedMaterialIds] = useState<string[]>([]);
  const [revisionMaterialIds, setRevisionMaterialIds] = useState<string[]>([]);
  const [rejectedMaterialIds, setRejectedMaterialIds] = useState<string[]>([]);
  const [editingReviewIds, setEditingReviewIds] = useState<string[]>([]);
  const [editingImageKey, setEditingImageKey] = useState<string | null>(null);
  const [reviewPreviewStep, setReviewPreviewStep] = useState(1);
  const [reviewPreviewScale, setReviewPreviewScale] = useState(1);
  const reviewPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reportPreviewScale, setReportPreviewScale] = useState(1);
  const reportPreviewFrameRef = useRef<HTMLDivElement>(null);
  const [reviewStageDrafts, setReviewStageDrafts] = useState<Record<string, ReviewStageDraft[]>>({});
  const [memoDrafts, setMemoDrafts] = useState<Record<string, string>>({});
  const [savedMemos, setSavedMemos] = useState<Record<string, string>>({});
  const [feedbackDrafts, setFeedbackDrafts] = useState<Record<string, string>>({});
  const [savedFeedbackRecords, setSavedFeedbackRecords] = useState<
    Array<{ id: string; recordId: string; feedback: string; savedAt: string }>
  >([]);

  const filteredStudents = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return students;

    return students.filter((student) => {
      const supportCase = supportCases.find((item) => item.studentId === student.id);
      return [student.name, student.school, student.grade, supportCase?.primaryNeed, supportCase?.caseType]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(normalized));
    });
  }, [query]);

  const selectedStudent = students.find((student) => student.id === selectedStudentId) ?? students[0];
  const selectedCase =
    supportCases.find((supportCase) => supportCase.studentId === selectedStudent.id) ?? supportCases[0];
  const selectedReviewItems = reviewItems.filter((item) => item.caseId === selectedCase.id);
  const selectedRecords = sessionRecords.filter((record) => record.caseId === selectedCase.id);
  const currentWorkflowStep = selectedCase.status === "follow_up" ? 4 : selectedCase.status === "scene_review" ? 2 : 3;
  const sessionLogs = selectedRecords.map((record, index) => {
    const attemptCount = index === 0 ? 9 : 7;
    const wrongCount = index === 0 ? 4 : 2;
    const averageResponseSeconds = index === 0 ? 42 : 55;
    const completionRate = index === 0 ? 75 : 68;

    return {
      ...record,
      attemptCount,
      wrongCount,
      averageResponseSeconds,
      completionRate,
      secondsPerQuestion: Math.round((record.durationMinutes * 60) / attemptCount),
      accuracyRate: Math.round(((attemptCount - wrongCount) / attemptCount) * 100),
    };
  });
  const feedbackQueue = sessionLogs.slice(0, 2);
  const pendingFeedbackQueue = feedbackQueue.filter(
    (record) => !savedFeedbackRecords.some((feedback) => feedback.recordId === record.id),
  );
  const feedbackTarget =
    feedbackQueue.find((record) => record.id === selectedFeedbackId) ?? feedbackQueue[0] ?? sessionLogs[0];
  const openReport = sessionLogs.find((record) => record.id === openReportId);
  const openReportStageStep = openReport
    ? Math.min(Math.max(sessionLogs.findIndex((record) => record.id === openReport.id) + 1, 1), reviewStagePreviews.length)
    : 1;
  const openReview = selectedReviewItems.find((item) => item.id === openReviewId);
  const openReviewStages = openReview ? (reviewStageDrafts[openReview.id] ?? reviewStagePreviews) : reviewStagePreviews;
  const isReviewEditing = openReview ? editingReviewIds.includes(openReview.id) : false;
  const savedMemo = savedMemos[selectedCase.id] ?? selectedCase.riskNote;
  const memoValue = memoDrafts[selectedCase.id] ?? savedMemo;
  const isMemoDirty = memoValue !== savedMemo;

  const updateReviewStageDraft = (
    reviewId: string,
    step: number,
    updater: (stage: ReviewStageDraft) => ReviewStageDraft,
  ) => {
    setReviewStageDrafts((current) => {
      const stages = current[reviewId] ?? reviewStagePreviews;
      return {
        ...current,
        [reviewId]: stages.map((stage) => (stage.step === step ? updater(stage) : stage)),
      };
    });
  };

  useEffect(() => {
    if (!openReview) return;
    const frame = reviewPreviewFrameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const { width, height } = frame.getBoundingClientRect();
      setReviewPreviewScale(Math.min(width / 1024, height / 768) + 0.004);
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [openReview]);

  useEffect(() => {
    if (!openReport) return;
    const frame = reportPreviewFrameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const { width, height } = frame.getBoundingClientRect();
      setReportPreviewScale(Math.min(width / 1024, height / 768) + 0.004);
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [openReport]);

  return (
    <main className="relative min-h-screen bg-[#f5f7fa] text-[#172033]">
      <Link
        href="/"
        className="fixed bottom-6 right-6 z-50 rounded-full border border-[#25466f] bg-[#1f3a5f] px-5 py-3 text-base font-black text-white shadow-[0_12px_30px_rgba(31,58,95,0.25)]"
      >
        데모 홈
      </Link>
      <div className="grid min-h-screen xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside className="sticky top-0 flex h-screen flex-col border-r border-[#d8dee8] bg-white">
          <div className="border-b border-[#e5e9f0] p-6">
            <p className="text-sm font-bold text-[#1f3a5f]">배움동행 교사용</p>
            <h1 className="mt-2 text-2xl font-black">학생 관리</h1>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#64748b]">
              학생을 검색하고, 오늘 수업에 필요한 상태와 자료를 확인합니다.
            </p>
          </div>

          <div className="space-y-3 border-b border-[#e5e9f0] p-4">
            <label className="block">
              <span className="sr-only">학생 검색</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="w-full rounded-md border border-[#cbd5e1] bg-white px-4 py-3 text-sm font-bold outline-none placeholder:text-[#94a3b8] focus:border-[#1f3a5f]"
                placeholder="학생 이름, 학교, 학습 이슈 검색"
              />
            </label>
            <button className="w-full rounded-md bg-[#1f3a5f] px-4 py-3 text-sm font-bold text-white">
              학생 등록
            </button>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto divide-y divide-[#e5e9f0]">
            {filteredStudents.map((student) => {
              const supportCase = supportCases.find((item) => item.studentId === student.id) ?? supportCases[0];

              return (
                <button
                  key={student.id}
                  onClick={() => {
                    setSelectedStudentId(student.id);
                    setActiveTab("info");
                  }}
                  className={`w-full p-5 text-left transition ${
                    selectedStudentId === student.id ? "bg-[#eef4fb]" : "bg-white hover:bg-[#f8fafc]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-lg font-black">{student.name}</p>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        {student.school} · {student.grade}
                      </p>
                    </div>
                    <StatusBadge supportCase={supportCase} />
                  </div>
                  <p className="mt-4 text-sm font-semibold leading-6 text-[#334155]">
                    {supportCase.primaryNeed}
                  </p>
                </button>
              );
            })}
            {filteredStudents.length === 0 && (
              <div className="p-6 text-sm font-bold leading-6 text-[#64748b]">검색 결과가 없습니다.</div>
            )}
          </div>
        </aside>

        <section className="min-w-0 px-5 py-5 lg:px-8">
          <article className="overflow-hidden rounded-xl border border-[#d8dee8] bg-white">
            <section className="border-b border-[#e5e9f0] bg-[#fbfcfe] p-6">
              <div className="flex flex-wrap items-start justify-between gap-5">
                <div className="flex items-start gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#dfe8f4] text-2xl font-black text-[#1f3a5f]">
                    {selectedStudent.name.slice(0, 1)}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-3xl font-black">{selectedStudent.name}</h3>
                      <StatusBadge supportCase={selectedCase} />
                    </div>
                    <p className="mt-2 font-semibold text-[#64748b]">
                      {selectedStudent.school} · {selectedStudent.grade} · {selectedCase.caseType}
                    </p>
                    <p className="mt-3 max-w-2xl text-sm font-semibold leading-6 text-[#334155]">
                      {selectedCase.primaryNeed}
                    </p>
                  </div>
                </div>
                <div className="min-w-[440px] rounded-lg bg-[#f8fafc] p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-bold text-[#64748b]">현재 단계</p>
                      <p className="mt-1 text-lg font-black text-[#172033]">{workflowSteps[currentWorkflowStep - 1]}</p>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#64748b]">출석</p>
                      <p className="mt-1 text-lg font-black text-[#172033]">{selectedStudent.attendanceRate}%</p>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-4 gap-3">
                    {workflowSteps.map((step, index) => {
                      const isDone = index + 1 <= currentWorkflowStep;

                      return (
                        <div key={step}>
                          <div className={`h-3 rounded-full ${isDone ? "bg-[#1f3a5f]" : "bg-[#dbe3ee]"}`} />
                          <p className={`mt-2 text-sm font-black ${isDone ? "text-[#1f3a5f]" : "text-[#94a3b8]"}`}>
                            {step}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </section>

            <nav className="grid border-b border-[#e5e9f0] bg-white md:grid-cols-3">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`border-b-2 px-6 py-4 text-left transition md:border-b-0 md:border-r md:last:border-r-0 ${
                    activeTab === tab.id
                      ? "border-[#1f3a5f] bg-[#eef4fb]"
                      : "border-transparent bg-white hover:bg-[#f8fafc]"
                  }`}
                >
                  <p className="font-black">{tab.label}</p>
                  <p className="mt-1 text-sm font-semibold text-[#64748b]">{tab.description}</p>
                </button>
              ))}
            </nav>

            <div className="min-h-[560px]">
            {activeTab === "info" && (
              <section className="space-y-6 p-6">
                <section className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
                  <InfoBlock label="핵심 어려움" value={selectedCase.primaryNeed} />
                  <InfoBlock label="지원 전략" value={selectedCase.supportStrategy} />
                </section>

                <section className="grid gap-5 lg:grid-cols-2">
                  <div className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                    <h3 className="text-xl font-black">강점</h3>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {selectedStudent.strengths.map((strength) => (
                        <span
                          key={strength}
                          className="rounded-full bg-[#eef4fb] px-3 py-1 text-sm font-bold text-[#1f3a5f]"
                        >
                          {strength}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                    <h3 className="text-xl font-black">약점</h3>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {selectedCase.challengeTags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-[#fff7ed] px-3 py-1 text-sm font-bold text-[#9a3412]"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </section>

                <section className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                  <h3 className="text-xl font-black">추가 메모</h3>
                  <textarea
                    value={memoValue}
                    onChange={(event) =>
                      setMemoDrafts((current) => ({
                        ...current,
                        [selectedCase.id]: event.target.value,
                      }))
                    }
                    className="mt-4 h-32 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-4 text-sm font-semibold leading-6 outline-none focus:border-[#1f3a5f]"
                  />
                  <div className="mt-3 flex justify-end">
                    <button className="hidden">
                      수정
                    </button>
                    <button
                      disabled={!isMemoDirty}
                      onClick={() => {
                        setSavedMemos((current) => ({
                          ...current,
                          [selectedCase.id]: memoValue,
                        }));
                      }}
                      className={`rounded-md px-4 py-2 text-sm font-bold transition ${
                        isMemoDirty
                          ? "bg-[#1f3a5f] text-white shadow-[0_8px_18px_rgba(31,58,95,0.18)]"
                          : "cursor-not-allowed bg-[#e2e8f0] text-[#94a3b8]"
                      }`}
                    >
                      저장
                    </button>
                  </div>
                </section>
              </section>
            )}

            {activeTab === "materials" && (
              <section className="grid min-h-[calc(100vh-430px)] gap-5 p-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                <section className="rounded-lg border border-[#e5e9f0] bg-white p-5">
                  <div className="flex h-full flex-col">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-xl font-black">자료 만들기</h3>
                        <p className="mt-1 text-sm font-semibold text-[#64748b]">
                          수업 내용과 난이도를 정하면 학생 정보는 자동으로 반영됩니다.
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 space-y-4">
                      <label className="block">
                        <span className="text-sm font-bold text-[#64748b]">수업 내용</span>
                        <textarea
                          className="mt-2 h-36 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-4 text-sm font-semibold outline-none focus:border-[#1f3a5f]"
                          defaultValue="분수의 전체-부분 관계를 시각 자료로 설명하고 1/4을 표현한다."
                        />
                      </label>

                      <label className="block">
                        <span className="text-sm font-bold text-[#64748b]">난이도</span>
                        <select className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-bold outline-none focus:border-[#1f3a5f]">
                          <option>기초</option>
                          <option>보통</option>
                          <option>도전</option>
                        </select>
                      </label>

                      <div className="rounded-md bg-[#f8fafc] p-3">
                        <p className="text-sm font-bold text-[#64748b]">자동 반영 정보</p>
                        <p className="mt-1 text-sm font-semibold leading-6 text-[#334155]">
                          핵심 어려움, 강점, 약점, 최근 학습 기록
                        </p>
                      </div>

                      <button className="w-full rounded-md bg-[#1f3a5f] px-4 py-3 text-sm font-bold text-white">
                        AI 자료 생성하기
                      </button>
                    </div>
                  </div>
                </section>

                <div className="space-y-4">
                  <section className="space-y-3">
                    <div>
                      <h3 className="text-xl font-black">생성된 자료</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        검토가 끝난 자료는 학생 화면으로 보낼 수 있습니다.
                      </p>
                    </div>
                    {selectedReviewItems.map((item) => (
                      <div key={item.id} className="rounded-md border border-[#e5e9f0] bg-white p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate text-base font-black">{item.title}</p>
                            <p className="mt-1 truncate text-sm font-semibold text-[#64748b]">{item.type}</p>
                          </div>
                          <span
                            className={`shrink-0 rounded-full border px-3 py-1 text-xs font-bold ${
                              appliedMaterialIds.includes(item.id)
                                ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                : approvedMaterialIds.includes(item.id)
                                  ? "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]"
                                  : rejectedMaterialIds.includes(item.id)
                                    ? "border-[#fecaca] bg-[#fef2f2] text-[#991b1b]"
                                    : revisionMaterialIds.includes(item.id)
                                      ? "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]"
                                      : "border-[#cbd5e1] bg-[#f8fafc] text-[#475569]"
                            }`}
                          >
                            {appliedMaterialIds.includes(item.id)
                              ? "적용 완료"
                              : approvedMaterialIds.includes(item.id)
                                ? "검토 완료"
                                : rejectedMaterialIds.includes(item.id)
                                  ? "사용 안 함"
                                  : revisionMaterialIds.includes(item.id)
                                    ? "수정 중"
                                    : item.state}
                          </span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <button
                            onClick={() => {
                              setReviewPreviewStep(1);
                              setOpenReviewId(item.id);
                            }}
                            className="rounded-md border border-[#cbd5e1] bg-white px-3 py-2 text-sm font-bold text-[#334155]"
                          >
                            검토하기
                          </button>
                          <button
                            onClick={() => {
                              if (!approvedMaterialIds.includes(item.id) || rejectedMaterialIds.includes(item.id)) return;
                              setAppliedMaterialIds((current) =>
                                current.includes(item.id) ? current : [...current, item.id],
                              );
                            }}
                            className={`rounded-md px-3 py-2 text-sm font-bold ${
                              appliedMaterialIds.includes(item.id)
                                ? "bg-[#dcfce7] text-[#15803d]"
                                : approvedMaterialIds.includes(item.id)
                                  ? "bg-[#1f3a5f] text-white"
                                  : "bg-[#e2e8f0] text-[#64748b]"
                            }`}
                          >
                            {appliedMaterialIds.includes(item.id) ? "적용됨" : "수업에 적용하기"}
                          </button>
                        </div>
                      </div>
                    ))}
                  </section>
                </div>
              </section>
            )}

            {activeTab === "records" && (
              <section className="space-y-6 p-6">
                <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
                  <div className="hidden">
                    <div>
                      <h3 className="text-xl font-black">피드백 대기</h3>
                      <p className="mt-1 text-sm font-semibold text-[#64748b]">
                        피드백을 남겨야 하는 학습 기록입니다.
                      </p>
                    </div>
                    {feedbackQueue.map((record) => (
                      <button
                        key={record.id}
                        onClick={() => setSelectedFeedbackId(record.id)}
                        className={`w-full rounded-lg border p-4 text-left transition ${
                          feedbackTarget?.id === record.id
                            ? "border-[#1f3a5f] bg-[#eef4fb]"
                            : "border-[#e5e9f0] bg-white hover:bg-[#f8fafc]"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-black">
                              {record.session} · {record.date}
                            </p>
                            <p className="mt-1 text-sm font-bold text-[#64748b]">
                              이해도 {record.understanding} · 집중도 {record.focus}
                            </p>
                          </div>
                          <span className="rounded-full bg-[#fff7ed] px-3 py-1 text-xs font-bold text-[#9a3412]">
                            작성 필요
                          </span>
                        </div>
	                        <div className="hidden">
                          <InfoBlock label="걸린 시간" value={`${record.durationMinutes}분`} />
                          <InfoBlock label="오답 횟수" value={`${record.wrongCount}회`} />
                          <InfoBlock label="정답률" value={`${record.accuracyRate}%`} />
                        </div>
                      </button>
                    ))}
                  </div>

                  <div className="rounded-lg border border-[#e5e9f0] bg-white p-5 xl:order-1">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-xl font-black">교육 피드백 작성</h3>
                        <p className="mt-1 text-sm font-semibold text-[#64748b]">
                          선택한 학습 기록에 대한 피드백을 남깁니다.
                        </p>
                      </div>
                      <span className="rounded-full bg-[#eef4fb] px-3 py-1 text-xs font-black text-[#1f3a5f]">
                        {pendingFeedbackQueue.length}개 작성 대상
                      </span>
                    </div>
                    <div className="mt-5 space-y-4">
                      {pendingFeedbackQueue.length === 0 && (
                        <div className="rounded-lg border border-[#bbf7d0] bg-[#f0fdf4] p-4 text-sm font-bold text-[#15803d]">
                          모든 차시 피드백이 최근 기록에 저장되었습니다.
                        </div>
                      )}
                      {pendingFeedbackQueue.map((record) => (
                        <section key={record.id} className="rounded-lg border border-[#e5e9f0] bg-[#f8fafc] p-4">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <p className="text-sm font-bold text-[#64748b]">피드백 작성 대상</p>
                              <p className="mt-1 text-base font-black text-[#172033]">
                                {record.session} · {record.date}
                              </p>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <Link
                                href="/student/stage?preview=1"
                                target="_blank"
                                className="rounded-md border border-[#cbd5e1] bg-white px-3 py-2 text-xs font-black text-[#334155]"
                              >
                                학습 자료 보기
                              </Link>
                              <span className="rounded-full bg-[#fff7ed] px-3 py-1 text-xs font-bold text-[#9a3412]">
                                작성 필요
                              </span>
                            </div>
                          </div>
                          <div className="mt-4 grid gap-2 md:grid-cols-3">
                            <InfoBlock label="걸린 시간" value={`${record.durationMinutes}분`} />
                            <InfoBlock label="오답 횟수" value={`${record.wrongCount}회`} />
                            <InfoBlock label="정답률" value={`${record.accuracyRate}%`} />
                          </div>
                          <textarea
                            value={feedbackDrafts[record.id] ?? ""}
                            onChange={(event) => {
                              setFeedbackDrafts((current) => ({
                                ...current,
                                [record.id]: event.target.value,
                              }));
                            }}
                            className="mt-4 h-40 w-full resize-none rounded-md border border-[#cbd5e1] bg-white p-4 outline-none focus:border-[#1f3a5f]"
                            placeholder="학생 반응, 이해도 변화, 다음 수업에서 반영할 피드백을 기록하세요."
                          />
                          <div className="mt-3 flex justify-end">
                            <button
                              onClick={() => {
                                const feedback = feedbackDrafts[record.id]?.trim();
                                if (!feedback) return;

                                setSavedFeedbackRecords((current) => [
                                  {
                                    id: `feedback-${record.id}-${Date.now()}`,
                                    recordId: record.id,
                                    feedback,
                                    savedAt: "방금 저장",
                                  },
                                  ...current.filter((item) => item.recordId !== record.id),
                                ]);
                              }}
                              disabled={!feedbackDrafts[record.id]?.trim()}
                              className="rounded-md bg-[#1f3a5f] px-4 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
                            >
                              저장
                            </button>
                          </div>
                        </section>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-4 rounded-lg border border-[#e5e9f0] bg-white p-5 xl:order-2">
                    <h3 className="text-xl font-black">최근 기록</h3>
                    {savedFeedbackRecords.map((feedbackRecord) => {
                      const sourceRecord = sessionLogs.find((record) => record.id === feedbackRecord.recordId);
                      if (!sourceRecord) return null;

                      return (
                        <button
                          key={feedbackRecord.id}
                          onClick={() => setOpenReportId(sourceRecord.id)}
                          className="w-full rounded-md bg-[#f8fafc] p-4 text-left transition hover:bg-[#eef4fb]"
                        >
                          <p className="font-black">
                            {sourceRecord.session} · {sourceRecord.date}
                          </p>
                          <p className="mt-1 text-sm font-bold text-[#64748b]">
                            교육 피드백 · {feedbackRecord.savedAt}
                          </p>
                          <p className="mt-2 text-sm leading-6">{feedbackRecord.feedback}</p>
                          <p className="mt-3 text-sm font-black text-[#1f3a5f]">리포트 보기</p>
                        </button>
                      );
                    })}
                    {sessionLogs.map((record) => (
                      <button
                        key={record.id}
                        onClick={() => setOpenReportId(record.id)}
                        className="w-full rounded-md bg-[#f8fafc] p-4 text-left transition hover:bg-[#eef4fb]"
                      >
                        <p className="font-black">
                          {record.session} · {record.date}
                        </p>
                        <p className="mt-1 text-sm font-bold text-[#64748b]">
                          {record.durationMinutes}분 · 이해도 {record.understanding} · 집중도 {record.focus}
                        </p>
                        <p className="mt-2 text-sm leading-6">{record.note}</p>
                        <p className="mt-3 text-sm font-black text-[#1f3a5f]">리포트 보기</p>
                      </button>
                    ))}
                  </div>
                </section>
              </section>
            )}
            </div>
          </article>
        </section>
      </div>
      {openReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-6">
          <section className="flex max-h-[88vh] w-full max-w-5xl flex-col rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e5e9f0] px-6 py-4">
              <div>
                <p className="text-sm font-bold text-[#64748b]">학습 리포트</p>
                <h3 className="mt-1 text-2xl font-black">
                  {openReport.session} · {openReport.date}
                </h3>
              </div>
              <button
                onClick={() => setOpenReportId(null)}
                aria-label="닫기"
                className="flex h-11 w-11 items-center justify-center rounded-md border border-[#cbd5e1] bg-white text-2xl font-bold leading-none text-[#334155]"
              >
                ×
              </button>
            </div>

            <div className="min-h-0 flex-1 px-6 py-4">
              <section className="rounded-lg border border-[#d8dee8] bg-[#e7edf4] p-3">
                <div className="mb-2">
                  <div>
                    <p className="text-xs font-black text-[#64748b]">차시 자료</p>
                    <p className="mt-1 text-base font-black text-[#172033]">스테이지 {openReportStageStep} 학습 화면</p>
                  </div>
                </div>
                <div
                  ref={reportPreviewFrameRef}
                  className="relative mx-auto aspect-[4/3] max-h-[40vh] max-w-[560px] overflow-hidden rounded-md bg-[#e7edf4]"
                >
                  <iframe
                    title={`학습 리포트 자료 스테이지 ${openReportStageStep}`}
                    src={`/student/stage?step=${openReportStageStep}&preview=1`}
                    className="absolute left-0 top-0 h-[768px] w-[1024px] origin-top-left border-0"
                    style={{ transform: `scale(${reportPreviewScale})` }}
                  />
                </div>
              </section>

              <div className="mt-3 grid gap-2 md:grid-cols-6">
                <InfoBlock label="걸린 시간" value={`${openReport.durationMinutes}분`} />
                <InfoBlock label="평균 응답" value={`${openReport.averageResponseSeconds}초`} />
                <InfoBlock label="문제당 시간" value={`${openReport.secondsPerQuestion}초`} />
                <InfoBlock label="시도 횟수" value={`${openReport.attemptCount}회`} />
                <InfoBlock label="오답 횟수" value={`${openReport.wrongCount}회`} />
                <InfoBlock label="정답률" value={`${openReport.accuracyRate}%`} />
              </div>

              <div className="mt-3 rounded-lg bg-[#f8fafc] p-4">
                <p className="text-sm font-bold text-[#64748b]">기록 요약</p>
                <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">{openReport.note}</p>
              </div>
            </div>
          </section>
        </div>
      )}
      {openReview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-5">
          <section className="flex max-h-[90vh] w-full max-w-[1240px] flex-col rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
            <div className="flex items-start justify-between gap-4 border-b border-[#e5e9f0] px-6 py-5">
              <div>
                <p className="text-sm font-bold text-[#64748b]">자료 검토</p>
                <h3 className="mt-1 text-2xl font-black">{openReview.title}</h3>
                <p className="mt-1 text-sm font-semibold text-[#64748b]">
                  4개 스테이지를 확인하고 필요한 부분만 수정합니다.
                </p>
              </div>
              <button
                onClick={() => {
                  setOpenReviewId(null);
                  setEditingImageKey(null);
                }}
                aria-label="닫기"
                className="flex h-11 w-11 items-center justify-center rounded-md border border-[#cbd5e1] bg-white text-2xl font-bold leading-none text-[#334155]"
              >
                ×
              </button>
            </div>

            <div className="grid min-h-0 flex-1 gap-5 px-7 py-5 lg:grid-cols-[minmax(560px,620px)_minmax(460px,1fr)]">
              <section className="min-h-0 rounded-lg border border-[#d8dee8] bg-[#e7edf4] p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-black text-[#64748b]">학생 화면 미리보기</p>
                    <p className="mt-1 text-lg font-black text-[#172033]">스테이지 {reviewPreviewStep}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {openReviewStages.map((stage) => (
                      <button
                        key={stage.step}
                        onClick={() => setReviewPreviewStep(stage.step)}
                        className={`rounded-full px-3 py-1 text-xs font-black ${
                          reviewPreviewStep === stage.step ? "bg-[#1f3a5f] text-white" : "bg-white text-[#475569]"
                        }`}
                      >
                        {stage.step}
                      </button>
                    ))}
                  </div>
                </div>
                <div
                  ref={reviewPreviewFrameRef}
                  className="relative aspect-[4/3] max-h-[min(58vh,560px)] overflow-hidden rounded-md border border-[#cbd5e1] bg-[#e7edf4]"
                >
                  <iframe
                    key={`${openReview.id}-${reviewPreviewStep}`}
                    title={`학생 화면 스테이지 ${reviewPreviewStep}`}
                    src={`/student/stage?step=${reviewPreviewStep}&preview=1`}
                    className="absolute left-0 top-0 h-[768px] w-[1024px] origin-top-left border-0"
                    style={{ transform: `scale(${reviewPreviewScale})` }}
                  />
                </div>
              </section>
              <div className="min-h-0 space-y-4 overflow-y-auto pr-2">
                {openReviewStages.map((stage, index) => {
                  const imageKey = `${openReview.id}-${stage.step}`;
                  const isImageEditing = editingImageKey === imageKey;

                  return (
                    <section key={stage.step} className="rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-5">
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="rounded-full bg-[#1f3a5f] px-3 py-1 text-xs font-black text-white">
                            스테이지 {stage.step}
                          </span>
                          <h4 className="text-lg font-black text-[#172033]">{stage.title}</h4>
                        </div>
                        {index === 0 && (
                          <span className="rounded-full border border-[#bbf7d0] bg-[#f0fdf4] px-3 py-1 text-xs font-bold text-[#15803d]">
                            정답 포함
                          </span>
                        )}
                      </div>

                      <div className="grid gap-4">
                        <div className="hidden">
                          <div className="relative aspect-[4/3] overflow-hidden rounded-lg border border-[#d8dee8] bg-[#e7edf4]">
                            <button
                              onClick={() => setEditingImageKey(isImageEditing ? null : imageKey)}
                              className="absolute right-2 top-2 z-10 rounded-full border border-[#cbd5e1] bg-white/95 px-3 py-1 text-xs font-black text-[#334155] shadow-sm"
                            >
                              화면 수정
                            </button>
                            <iframe
                              title={`학생 화면 스테이지 ${stage.step}`}
                              src={`/student/stage?step=${stage.step}&preview=1`}
                              className="absolute left-0 top-0 h-[768px] w-[1024px] origin-top-left scale-[0.205] border-0"
                            />
                          </div>
                          {isImageEditing && (
                            <div className="absolute left-[calc(100%+12px)] top-1 z-30 w-72 rounded-lg border border-[#fed7aa] bg-[#fff7ed] p-3 shadow-[0_18px_45px_rgba(154,52,18,0.18)] before:absolute before:left-[-7px] before:top-8 before:h-3 before:w-3 before:rotate-45 before:border-b before:border-l before:border-[#fed7aa] before:bg-[#fff7ed] max-lg:left-0 max-lg:top-[calc(100%+10px)] max-lg:w-full max-lg:before:left-8 max-lg:before:top-[-7px] max-lg:before:border-b-0 max-lg:before:border-l-0 max-lg:before:border-r max-lg:before:border-t">
                              <label className="text-xs font-black text-[#9a3412]" htmlFor={`image-prompt-${stage.step}`}>
                                화면 수정 프롬프트
                              </label>
                              <textarea
                                id={`image-prompt-${stage.step}`}
                                className="mt-2 h-20 w-full resize-none rounded-md border border-[#fdba74] bg-white p-3 text-xs font-semibold leading-5 outline-none focus:border-[#ea580c]"
                                value={stage.imagePrompt}
                                onChange={(event) =>
                                  updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                    ...currentStage,
                                    imagePrompt: event.target.value,
                                  }))
                                }
                              />
                              <button
                                onClick={() => {
                                  setRevisionMaterialIds((current) =>
                                    current.includes(openReview.id) ? current : [...current, openReview.id],
                                  );
                                  setEditingImageKey(null);
                                }}
                                className="mt-2 w-full rounded-md bg-[#9a3412] px-3 py-2 text-xs font-black text-white"
                              >
                                화면 재생성
                              </button>
                            </div>
                          )}
                        </div>

                        <div className="grid gap-3">
                          <div className="rounded-md bg-white p-4">
                            <p className="text-xs font-black text-[#64748b]">내용</p>
                            {isReviewEditing ? (
                              <textarea
                                className="mt-2 h-20 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-3 text-sm font-semibold leading-6 outline-none focus:border-[#1f3a5f]"
                                value={stage.description}
                                onChange={(event) =>
                                  updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                    ...currentStage,
                                    description: event.target.value,
                                  }))
                                }
                              />
                            ) : (
                              <>
                                <p className="mt-2 text-sm font-semibold leading-6 text-[#334155]">{stage.description}</p>
                                <div className="mt-4 border-l-4 border-[#1f3a5f] bg-[#f2f6fb] px-4 py-3">
                                  <p className="text-xs font-black uppercase tracking-[0.08em] text-[#1f3a5f]">
                                    설계 의도
                                  </p>
                                  <p className="mt-2 text-sm font-bold leading-6 text-[#26364d]">
                                    {reviewStageReasons[stage.step]}
                                  </p>
                                </div>
                              </>
                            )}

                            <p className="mt-4 text-xs font-black text-[#64748b]">문제</p>
                            {isReviewEditing ? (
                              <input
                                className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-[#fbfcfe] px-3 py-2 text-sm font-black outline-none focus:border-[#1f3a5f]"
                                value={stage.question}
                                onChange={(event) =>
                                  updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                    ...currentStage,
                                    question: event.target.value,
                                  }))
                                }
                              />
                            ) : (
                              <p className="mt-2 text-base font-black leading-7 text-[#172033]">{stage.question}</p>
                            )}
                          </div>

                          <div className="rounded-md bg-white p-4">
                            <p className="text-xs font-black text-[#64748b]">선택지</p>
                            <div className="mt-2 space-y-2">
                              {stage.choices.map((choice, choiceIndex) =>
                                isReviewEditing ? (
                                  <input
                                    key={`${stage.step}-${choiceIndex}`}
                                    className="w-full rounded-md border border-[#cbd5e1] bg-[#fbfcfe] px-3 py-2 text-sm font-bold outline-none focus:border-[#1f3a5f]"
                                    value={choice}
                                    onChange={(event) =>
                                      updateReviewStageDraft(openReview.id, stage.step, (currentStage) => ({
                                        ...currentStage,
                                        choices: currentStage.choices.map((currentChoice, currentChoiceIndex) =>
                                          currentChoiceIndex === choiceIndex ? event.target.value : currentChoice,
                                        ),
                                      }))
                                    }
                                  />
                                ) : (
                                  <div
                                    key={choice}
                                    className={`rounded-md border px-3 py-2 text-sm font-black ${
                                      choiceIndex === 0
                                        ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                                        : "border-[#e5e9f0] bg-[#f8fafc] text-[#334155]"
                                    }`}
                                  >
                                    {choice}
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </section>
                  );
                })}
              </div>
            </div>

            <div className="flex flex-wrap justify-end gap-3 border-t border-[#e5e9f0] px-6 py-4">
              <button
                onClick={() => {
                  setRejectedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingImageKey(null);
                  setOpenReviewId(null);
                }}
                className="rounded-md border border-[#fecaca] bg-[#fef2f2] px-5 py-3 text-sm font-bold text-[#991b1b]"
              >
                사용 안 함
              </button>
              <button
                onClick={() => {
	                  if (isReviewEditing) {
	                    setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
	                    setEditingImageKey(null);
	                    return;
	                  }

	                  setEditingReviewIds((current) => [...current, openReview.id]);
                  setRevisionMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                }}
	                className={`rounded-md border px-5 py-3 text-sm font-bold ${
	                  isReviewEditing
	                    ? "border-[#1f3a5f] bg-[#1f3a5f] text-white"
	                    : "border-[#cbd5e1] bg-white text-[#334155]"
	                }`}
              >
                {isReviewEditing ? "수정 저장" : "직접 수정"}
              </button>
              <button
                onClick={() => {
                  setApprovedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingReviewIds((current) => current.filter((id) => id !== openReview.id));
                  setEditingImageKey(null);
                  setOpenReviewId(null);
                }}
                className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white"
              >
                사용 승인
              </button>
            </div>
          </section>
        </div>
      )}
      {/* Legacy review modal removed after stage-by-stage review redesign.
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-6">
          <section className="w-full max-w-3xl rounded-xl bg-white p-6 shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e5e9f0] pb-4">
              <div>
                <p className="text-sm font-bold text-[#64748b]">자료 검토</p>
                <h3 className="mt-1 text-2xl font-black">{openReview.title}</h3>
                <p className="mt-2 text-sm font-semibold text-[#64748b]">{openReview.type}</p>
              </div>
              <button
                onClick={() => setOpenReviewId(null)}
                className="rounded-md border border-[#cbd5e1] bg-white px-4 py-2 text-sm font-bold text-[#334155]"
              >
                닫기
              </button>
            </div>

            <div className="mt-5 rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-5">
              <p className="text-sm font-bold text-[#64748b]">생성 자료 미리보기</p>
              <div className="mt-4 grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
                <section className="rounded-lg bg-white p-5">
                  <h4 className="text-xl font-black">빛나는 구역 찾기</h4>
                  <p className="mt-3 text-sm font-semibold leading-6 text-[#334155]">
                    4조각으로 나뉜 피자 지도에서 빛나는 한 조각을 찾고, 전체 중 일부를 1/4로 표현하는
                    학생용 미션입니다.
                  </p>
                  <div className="mt-5 aspect-[16/9] rounded-lg border border-[#ecd27a] bg-[#f6df7d] p-4">
                    <div className="grid h-full grid-cols-2 gap-1 rounded-md border-4 border-[#e4bd4e] bg-[#f8e48f]">
                      <div className="border-r border-b border-[#e4bd4e]" />
                      <div className="border-b border-[#e4bd4e]" />
                      <div className="border-r border-[#e4bd4e]" />
                      <div className="ring-4 ring-[#fff176]" />
                    </div>
                  </div>
                </section>

                <section className="space-y-4">
                  <div className="rounded-lg bg-white p-5">
                    <p className="text-sm font-bold text-[#64748b]">학생 질문</p>
                    <input
                      className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-[#fbfcfe] px-4 py-3 text-xl font-black outline-none focus:border-[#1f3a5f]"
                      defaultValue="4구역 중 1구역은 몇 분의 몇일까요?"
                    />
                  </div>
                  <div className="rounded-lg bg-white p-5">
                    <p className="text-sm font-bold text-[#64748b]">선택지</p>
                    <div className="mt-3 grid gap-2">
                      {["1/4", "2/4", "4/1"].map((choice, index) => (
                        <div
                          key={choice}
                          className={`rounded-md border px-4 py-3 text-lg font-black ${
                            index === 0
                              ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#15803d]"
                              : "border-[#e5e9f0] bg-[#f8fafc] text-[#334155]"
                          }`}
                        >
                          {choice}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-lg bg-white p-5">
                    <p className="text-sm font-bold text-[#64748b]">이미지 재생성 프롬프트</p>
                    <textarea
                      className="mt-2 h-24 w-full resize-none rounded-md border border-[#cbd5e1] bg-[#fbfcfe] p-4 text-sm font-semibold outline-none focus:border-[#1f3a5f]"
                      placeholder="이미지를 다시 만들 때 반영할 내용을 적어주세요."
                      defaultValue="피자 지도를 4조각으로 명확히 나누고, 오른쪽 아래 한 조각만 빛나게 표시"
                    />
                  </div>
                </section>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <button
                onClick={() => {
                  setRejectedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setOpenReviewId(null);
                }}
                className="rounded-md border border-[#fecaca] bg-[#fef2f2] px-5 py-3 text-sm font-bold text-[#991b1b]"
              >
                사용 안 함
              </button>
              <button
                onClick={() => {
                  setRevisionMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                }}
                className="rounded-md border border-[#cbd5e1] bg-white px-5 py-3 text-sm font-bold text-[#334155]"
              >
                직접 수정
              </button>
              <button
                onClick={() => {
                  setRevisionMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setApprovedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setAppliedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                }}
                className="rounded-md border border-[#fed7aa] bg-[#fff7ed] px-5 py-3 text-sm font-bold text-[#9a3412]"
              >
                이미지 재생성
              </button>
              <button
                onClick={() => {
                  setApprovedMaterialIds((current) =>
                    current.includes(openReview.id) ? current : [...current, openReview.id],
                  );
                  setRevisionMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setRejectedMaterialIds((current) => current.filter((id) => id !== openReview.id));
                  setOpenReviewId(null);
                }}
                className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white"
              >
                사용 승인
              </button>
            </div>
          </section>
        </div>
      */}
    </main>
  );
}
