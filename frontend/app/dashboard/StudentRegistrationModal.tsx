"use client";

import { useMemo, useState, type FormEvent } from "react";
import {
  createTeacherStudent,
  searchSchools,
  type ContentType,
  type SchoolProfile,
  type StudentRegistrationResponse,
} from "@/lib/api";

type RegistrationFormState = {
  displayName: string;
  schoolQuery: string;
  officeCode: string;
  grade: string;
  className: string;
  studentType: ContentType;
  currentGoal: string;
  observationNote: string;
  strengthsText: string;
  weaknessesText: string;
  preferredSupportsText: string;
};

type StudentRegistrationModalProps = {
  open: boolean;
  onClose: () => void;
  onRegistered: (response: StudentRegistrationResponse) => Promise<void>;
  onStartMaterials: (response: StudentRegistrationResponse) => Promise<void> | void;
};

const gradeOptions = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"];

const studentTypeOptions: Array<{ value: ContentType; label: string; description: string }> = [
  {
    value: "learning_focus",
    label: "학습지원형",
    description: "개념, 문제 조건, 설명하기 중심 자료를 제안합니다.",
  },
  {
    value: "life_support",
    label: "일상생활 지원형",
    description: "상황 단서와 행동 선택 중심 자료를 제안합니다.",
  },
];

const inputClass =
  "mt-2 w-full rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-bold text-[#172033] outline-none transition placeholder:text-[#94a3b8] focus:border-[#1f3a5f]";
const textareaClass =
  "mt-2 w-full resize-none rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-semibold leading-6 text-[#172033] outline-none transition placeholder:text-[#94a3b8] focus:border-[#1f3a5f]";

function createDefaultRegistrationForm(): RegistrationFormState {
  return {
    displayName: "",
    schoolQuery: "",
    officeCode: "R10",
    grade: "초3",
    className: "",
    studentType: "learning_focus",
    currentGoal: "",
    observationNote: "",
    strengthsText: "",
    weaknessesText: "",
    preferredSupportsText: "",
  };
}

function schoolDisplayName(school: SchoolProfile) {
  return school.schoolName || school.name || "학교명 확인 중";
}

function schoolAddress(school: SchoolProfile) {
  return school.roadAddress || school.address || school.regionName || "주소 정보 확인 중";
}

function splitList(value: string) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 5);
}

function gradeNumberFromGrade(grade: string) {
  const match = grade.match(/\d+/);
  return match ? match[0] : null;
}

function supportIntakeFromForm(form: RegistrationFormState, strengths: string[], weaknesses: string[], preferredSupports: string[]) {
  const choiceCountLimit = preferredSupports.some((support) => support.includes("2")) || form.studentType === "life_support" ? 2 : 3;
  return {
    learningResponse: {
      preferredCues: preferredSupports,
      readingLoad: weaknesses.some((weakness) => weakness.includes("긴 문장") || weakness.includes("읽기")) ? "low" : "medium",
      choiceCountLimit,
      strengths,
    },
    challengeBehaviorPriorities: [],
    behaviorFunctionHypotheses: weaknesses.filter((weakness) => weakness.includes("회피") || weakness.includes("기다림")),
    replacementSkills: form.studentType === "life_support" ? ["도움 요청하기", "순서 확인하기"] : ["다시 말해달라고 하기", "순서 확인하기"],
    recommendedScaffolds: preferredSupports,
    avoidGuidance: weaknesses,
  };
}

function getRequestErrorMessage(error: unknown) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "요청을 처리하지 못했습니다. 입력값을 확인한 뒤 다시 시도해 주세요.";
}

export function StudentRegistrationModal({
  open,
  onClose,
  onRegistered,
  onStartMaterials,
}: StudentRegistrationModalProps) {
  const [form, setForm] = useState<RegistrationFormState>(createDefaultRegistrationForm);
  const [schoolResults, setSchoolResults] = useState<SchoolProfile[]>([]);
  const [selectedSchool, setSelectedSchool] = useState<SchoolProfile | null>(null);
  const [schoolSearchMessage, setSchoolSearchMessage] = useState("");
  const [schoolSearchError, setSchoolSearchError] = useState("");
  const [isSearchingSchools, setIsSearchingSchools] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdResponse, setCreatedResponse] = useState<StudentRegistrationResponse | null>(null);

  const strengths = useMemo(() => splitList(form.strengthsText), [form.strengthsText]);
  const weaknesses = useMemo(() => splitList(form.weaknessesText), [form.weaknessesText]);
  const preferredSupports = useMemo(() => splitList(form.preferredSupportsText), [form.preferredSupportsText]);
  const canSubmit =
    Boolean(form.displayName.trim()) &&
    Boolean(selectedSchool?.schoolCode) &&
    Boolean(form.grade.trim()) &&
    Boolean(form.className.trim()) &&
    Boolean(form.currentGoal.trim()) &&
    Boolean(form.observationNote.trim()) &&
    strengths.length > 0 &&
    weaknesses.length > 0 &&
    preferredSupports.length > 0 &&
    !isSubmitting;

  if (!open) return null;

  const updateForm = <Key extends keyof RegistrationFormState>(key: Key, value: RegistrationFormState[Key]) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleSearchSchools = async () => {
    const query = form.schoolQuery.trim();
    if (query.length < 2) {
      setSchoolSearchError("학교명은 두 글자 이상 입력해 주세요.");
      setSchoolSearchMessage("");
      setSchoolResults([]);
      return;
    }

    setIsSearchingSchools(true);
    setSchoolSearchError("");
    setSchoolSearchMessage("");
    setSelectedSchool(null);
    try {
      const result = await searchSchools({
        q: query,
        officeCode: form.officeCode.trim() || "R10",
        syncIfMissing: true,
      });
      setSchoolResults(result.schools);
      setSchoolSearchMessage(
        result.schools.length > 0
          ? `${result.schools.length}개 학교를 찾았습니다. 등록할 학교를 선택해 주세요.`
          : "검색 결과가 없습니다. 학교명을 더 정확히 입력해 주세요.",
      );
    } catch (error) {
      setSchoolResults([]);
      setSchoolSearchError(getRequestErrorMessage(error));
    } finally {
      setIsSearchingSchools(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit || !selectedSchool) return;

    setIsSubmitting(true);
    setSubmitError("");
    try {
      const response = await createTeacherStudent({
        displayName: form.displayName.trim(),
        schoolCode: selectedSchool.schoolCode,
        schoolName: schoolDisplayName(selectedSchool),
        officeCode: selectedSchool.officeCode || form.officeCode.trim() || "R10",
        grade: form.grade,
        gradeNumber: gradeNumberFromGrade(form.grade),
        className: form.className.trim(),
        studentType: form.studentType,
        currentGoal: form.currentGoal.trim(),
        observationNote: form.observationNote.trim(),
        strengths,
        weaknesses,
        preferredSupports,
        supportIntake: supportIntakeFromForm(form, strengths, weaknesses, preferredSupports),
      });
      setCreatedResponse(response);
      try {
        await onRegistered(response);
      } catch {
        setSubmitError("학생은 등록되었지만 목록을 새로고침하지 못했습니다. 새로고침 후 확인해 주세요.");
      }
    } catch (error) {
      setSubmitError(getRequestErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartMaterials = async () => {
    if (!createdResponse) return;
    await onStartMaterials(createdResponse);
    onClose();
  };

  if (createdResponse) {
    const registeredStudentName = createdResponse.student?.profile.displayName ?? form.displayName.trim();
    const accessCode = createdResponse.accessCode ?? createdResponse.student?.profile.accessCode ?? "확인 필요";

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-5">
        <section
          role="dialog"
          aria-modal="true"
          aria-labelledby="student-registration-success-title"
          className="w-[min(94vw,640px)] rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]"
        >
          <div className="border-b border-[#e5e9f0] px-6 py-5">
            <p className="text-sm font-bold text-[#1f3a5f]">학생 등록 완료</p>
            <h2 id="student-registration-success-title" className="mt-1 text-2xl font-black text-[#172033]">
              {registeredStudentName}
            </h2>
          </div>
          <div className="space-y-4 px-6 py-5">
            <div className="rounded-lg border border-[#bbf7d0] bg-[#f0fdf4] p-4">
              <p className="text-sm font-bold text-[#15803d]">학생 접속 코드</p>
              <p className="mt-2 text-3xl font-black tracking-[0.08em] text-[#172033]">{accessCode}</p>
            </div>
            <p className="text-sm font-semibold leading-6 text-[#475569]">
              학생 목록과 상세 정보를 새로 읽었습니다. 이 학생으로 바로 수업 자료 제안 흐름을 시작할 수 있습니다.
            </p>
            {submitError && <p className="rounded-md bg-[#fff7ed] px-4 py-3 text-sm font-bold text-[#9a3412]">{submitError}</p>}
          </div>
          <div className="flex flex-wrap justify-end gap-3 border-t border-[#e5e9f0] px-6 py-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-[#cbd5e1] bg-white px-5 py-3 text-sm font-bold text-[#334155]"
            >
              학생 정보 보기
            </button>
            <button
              type="button"
              onClick={() => void handleStartMaterials()}
              className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white"
            >
              자료 생성 시작
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f172a]/45 p-4">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="student-registration-title"
        className="flex max-h-[92vh] w-[min(96vw,980px)] flex-col overflow-hidden rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]"
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#e5e9f0] px-6 py-5">
          <div>
            <p className="text-sm font-bold text-[#1f3a5f]">교사 대시보드</p>
            <h2 id="student-registration-title" className="mt-1 text-2xl font-black text-[#172033]">
              학생 등록
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="닫기"
            className="flex h-11 w-11 items-center justify-center rounded-md border border-[#cbd5e1] bg-white text-2xl font-bold leading-none text-[#334155] disabled:cursor-not-allowed disabled:opacity-60"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.8fr)]">
            <section className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_120px]">
                <label className="block">
                  <span className="text-sm font-bold text-[#64748b]">이름</span>
                  <input
                    value={form.displayName}
                    onChange={(event) => updateForm("displayName", event.target.value)}
                    className={inputClass}
                    placeholder="예: 최하늘"
                    required
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-bold text-[#64748b]">교육청</span>
                  <input
                    value={form.officeCode}
                    onChange={(event) => updateForm("officeCode", event.target.value)}
                    className={inputClass}
                    placeholder="R10"
                    required
                  />
                </label>
              </div>

              <section className="rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-4">
                <label className="block">
                  <span className="text-sm font-bold text-[#64748b]">학교검색</span>
                  <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                    <input
                      value={form.schoolQuery}
                      onChange={(event) => {
                        updateForm("schoolQuery", event.target.value);
                        setSelectedSchool(null);
                      }}
                      className="w-full rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-bold text-[#172033] outline-none transition placeholder:text-[#94a3b8] focus:border-[#1f3a5f]"
                      placeholder="학교명을 입력하세요"
                    />
                    <button
                      type="button"
                      onClick={() => void handleSearchSchools()}
                      disabled={isSearchingSchools}
                      className="shrink-0 rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
                    >
                      {isSearchingSchools ? "검색 중" : "검색"}
                    </button>
                  </div>
                </label>
                {schoolSearchError && <p className="mt-3 text-sm font-bold text-[#b42318]">{schoolSearchError}</p>}
                {schoolSearchMessage && <p className="mt-3 text-sm font-bold text-[#1d4ed8]">{schoolSearchMessage}</p>}
                <div className="mt-3 max-h-52 space-y-2 overflow-y-auto">
                  {schoolResults.map((school) => {
                    const selected = selectedSchool?.schoolCode === school.schoolCode;

                    return (
                      <button
                        key={`${school.officeCode}-${school.schoolCode}`}
                        type="button"
                        onClick={() => {
                          setSelectedSchool(school);
                          updateForm("schoolQuery", schoolDisplayName(school));
                        }}
                        className={`w-full rounded-md border px-4 py-3 text-left transition ${
                          selected
                            ? "border-[#1f3a5f] bg-[#eef4fb]"
                            : "border-[#e5e9f0] bg-white hover:border-[#bfdbfe]"
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="font-black text-[#172033]">{schoolDisplayName(school)}</p>
                          <span className="rounded-full bg-[#f1f5f9] px-3 py-1 text-xs font-black text-[#475569]">
                            {school.schoolCode}
                          </span>
                        </div>
                        <p className="mt-1 text-sm font-semibold leading-6 text-[#64748b]">{schoolAddress(school)}</p>
                      </button>
                    );
                  })}
                </div>
                {selectedSchool && (
                  <p className="mt-3 rounded-md border border-[#bbf7d0] bg-[#f0fdf4] px-3 py-2 text-sm font-bold text-[#15803d]">
                    {schoolDisplayName(selectedSchool)} 선택됨
                  </p>
                )}
              </section>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-sm font-bold text-[#64748b]">학년</span>
                  <select
                    value={form.grade}
                    onChange={(event) => updateForm("grade", event.target.value)}
                    className={inputClass}
                  >
                    {gradeOptions.map((grade) => (
                      <option key={grade} value={grade}>
                        {grade}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-sm font-bold text-[#64748b]">반</span>
                  <input
                    value={form.className}
                    onChange={(event) => updateForm("className", event.target.value)}
                    className={inputClass}
                    placeholder="예: 1"
                    required
                  />
                </label>
              </div>

              <fieldset>
                <legend className="text-sm font-bold text-[#64748b]">학생 유형</legend>
                <div className="mt-2 grid gap-3 sm:grid-cols-2">
                  {studentTypeOptions.map((option) => {
                    const selected = form.studentType === option.value;

                    return (
                      <label
                        key={option.value}
                        className={`block rounded-lg border p-4 transition ${
                          selected ? "border-[#1f3a5f] bg-[#eef4fb]" : "border-[#e5e9f0] bg-white"
                        }`}
                      >
                        <input
                          type="radio"
                          name="studentType"
                          value={option.value}
                          checked={selected}
                          onChange={() => updateForm("studentType", option.value)}
                          className="sr-only"
                        />
                        <span className="block text-base font-black text-[#172033]">{option.label}</span>
                        <span className="mt-1 block text-sm font-semibold leading-6 text-[#64748b]">
                          {option.description}
                        </span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>
            </section>

            <aside className="space-y-4">
              <label className="block">
                <span className="text-sm font-bold text-[#64748b]">현재 목표</span>
                <textarea
                  value={form.currentGoal}
                  onChange={(event) => updateForm("currentGoal", event.target.value)}
                  className={`${textareaClass} h-24`}
                  placeholder="예: 분수의 1/4을 그림에서 찾기"
                  required
                />
              </label>
              <label className="block">
                <span className="text-sm font-bold text-[#64748b]">관찰 메모</span>
                <textarea
                  value={form.observationNote}
                  onChange={(event) => updateForm("observationNote", event.target.value)}
                  className={`${textareaClass} h-28`}
                  placeholder="수업 중 보인 반응이나 조정이 필요한 점"
                  required
                />
              </label>
              <label className="block">
                <span className="text-sm font-bold text-[#64748b]">강점</span>
                <textarea
                  value={form.strengthsText}
                  onChange={(event) => updateForm("strengthsText", event.target.value)}
                  className={`${textareaClass} h-24`}
                  placeholder="쉼표나 줄바꿈으로 입력"
                  required
                />
              </label>
              <label className="block">
                <span className="text-sm font-bold text-[#64748b]">약점</span>
                <textarea
                  value={form.weaknessesText}
                  onChange={(event) => updateForm("weaknessesText", event.target.value)}
                  className={`${textareaClass} h-24`}
                  placeholder="쉼표나 줄바꿈으로 입력"
                  required
                />
              </label>
              <label className="block">
                <span className="text-sm font-bold text-[#64748b]">선호 지원</span>
                <textarea
                  value={form.preferredSupportsText}
                  onChange={(event) => updateForm("preferredSupportsText", event.target.value)}
                  className={`${textareaClass} h-24`}
                  placeholder="예: 그림 카드, 2개 선택지, 짧은 음성 안내"
                  required
                />
              </label>
            </aside>
          </div>

          {submitError && <p className="mt-5 rounded-md bg-[#fff7ed] px-4 py-3 text-sm font-bold text-[#9a3412]">{submitError}</p>}

          <div className="mt-6 flex flex-wrap justify-end gap-3 border-t border-[#e5e9f0] pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-md border border-[#cbd5e1] bg-white px-5 py-3 text-sm font-bold text-[#334155] disabled:cursor-not-allowed disabled:opacity-60"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="rounded-md bg-[#1f3a5f] px-5 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
            >
              {isSubmitting ? "등록 중" : "학생 등록"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
