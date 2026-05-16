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
  instructionBurdenText: string;
  communicationNeedText: string;
  calmingSupportsText: string;
  avoidGuidanceText: string;
  guardianShareNote: string;
};

type StudentRegistrationModalProps = {
  open: boolean;
  onClose: () => void;
  onRegistered: (response: StudentRegistrationResponse) => Promise<void>;
  onStartMaterials: (response: StudentRegistrationResponse) => Promise<void> | void;
};

const gradeOptions = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"];

const officeCodeLabels: Record<string, string> = {
  B10: "서울특별시교육청",
  C10: "부산광역시교육청",
  D10: "대구광역시교육청",
  E10: "인천광역시교육청",
  F10: "광주광역시교육청",
  G10: "대전광역시교육청",
  H10: "울산광역시교육청",
  I10: "세종특별자치시교육청",
  J10: "경기도교육청",
  K10: "강원특별자치도교육청",
  M10: "충청북도교육청",
  N10: "충청남도교육청",
  P10: "전북특별자치도교육청",
  Q10: "전라남도교육청",
  R10: "경상북도교육청",
  S10: "경상남도교육청",
  T10: "제주특별자치도교육청",
};

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

type ChecklistField =
  | "strengthsText"
  | "weaknessesText"
  | "preferredSupportsText"
  | "communicationNeedText"
  | "calmingSupportsText"
  | "avoidGuidanceText";

type ChecklistGroupDefinition = {
  key: ChecklistField;
  title: string;
  description: string;
  required?: boolean;
  options: string[];
};

const supportChecklistGroupsByType: Record<ContentType, ChecklistGroupDefinition[]> = {
  learning_focus: [
  {
    key: "strengthsText",
    title: "학습에서 잘 되는 반응",
    description: "개념 학습이나 문제 풀이에서 확인된 시작점",
    required: true,
    options: [
      "짧은 예시를 보고 이해함",
      "그림·표·자료 단서를 먼저 찾음",
      "한 문항씩 끝까지 풂",
      "선택지가 적으면 답을 고름",
      "계산 절차를 따라감",
      "읽은 내용을 짧게 말함",
      "오답 뒤 다시 시도함",
      "선생님 질문에 짧게 답함",
    ],
  },
  {
    key: "weaknessesText",
    title: "학습에서 막히는 지점",
    description: "다음 자료에서 먼저 낮춰야 할 학습 부담",
    required: true,
    options: [
      "긴 문제 조건 이해",
      "여러 조건을 한 번에 처리",
      "문제에서 핵심 단서 찾기",
      "긴 글을 읽고 시작",
      "풀이 순서 유지",
      "개념을 말로 설명하기",
      "응용 문제로 옮기기",
      "오류 후 다시 시도",
    ],
  },
  {
    key: "preferredSupportsText",
    title: "효과가 확인된 학습 지원",
    description: "콘텐츠 생성 때 반영할 설명·문제 제시 방식",
    required: true,
    options: [
      "예시 문제를 먼저 보여줌",
      "핵심 단서를 표시함",
      "지시를 짧게 나눔",
      "선택지를 줄임",
      "풀이 순서를 카드로 보여줌",
      "그림·표와 함께 설명함",
      "빈칸으로 일부만 확인함",
      "말로 설명하기 전에 문장 틀을 줌",
    ],
  },
  {
    key: "communicationNeedText",
    title: "학습 표현·확인 기술",
    description: "문제 풀이 중 키워야 할 말하기와 확인 방식",
    options: [
      "다시 설명해달라고 요청",
      "어디부터 풀지 묻기",
      "핵심 단서 말하기",
      "풀이 순서 말하기",
      "모르는 단어 묻기",
      "정답 이유 짧게 말하기",
      "틀린 부분 다시 확인하기",
    ],
  },
  {
    key: "calmingSupportsText",
    title: "학습 부담을 낮추는 조건",
    description: "수업 진입과 재시도를 안정시키는 조건",
    options: [
      "쉬운 첫 문항이 있을 때 안정됨",
      "예시 풀이를 본 뒤 안정됨",
      "생각할 시간이 있을 때 안정됨",
      "선택지가 적을 때 안정됨",
      "문제량이 나뉘어 있을 때 안정됨",
      "오답 뒤 힌트가 있으면 재시도함",
    ],
  },
  {
    key: "avoidGuidanceText",
    title: "피해야 할 학습 제시 방식",
    description: "학습 시작과 이해를 방해할 수 있는 방식",
    options: [
      "긴 설명부터 시작",
      "긴 지문을 한 번에 제시",
      "조건을 여러 개 한꺼번에 제시",
      "선택지를 많이 제시",
      "풀이 순서 없이 바로 문제 제시",
      "오답 직후 재촉",
      "정답 이유를 길게 요구",
    ],
  },
  ],
  life_support: [
  {
    key: "strengthsText",
    title: "현재 잘 되는 수행",
    description: "관찰된 강점과 독립적으로 가능한 행동",
    required: true,
    options: ["짧은 지시를 이해함", "익숙한 활동을 시작함", "한 활동을 끝까지 해봄", "오류 뒤 다시 시도함", "선생님 질문에 짧게 답함", "또래 활동을 관찰함"],
  },
  {
    key: "weaknessesText",
    title: "지원이 필요한 상황",
    description: "기능평가에서 먼저 확인할 어려움",
    required: true,
    options: [
      "긴 지시 이해",
      "여러 조건을 한 번에 처리",
      "긴 글을 읽고 시작",
      "활동 시작",
      "활동 지속",
      "오류 후 재시도",
      "활동 전환",
      "기다림",
      "낯선 상황",
      "감각·환경 자극",
    ],
  },
  {
    key: "preferredSupportsText",
    title: "효과가 확인된 지원",
    description: "관찰 또는 이전 지원에서 효과가 있었던 조건",
    required: true,
    options: ["지시를 짧게 나눔", "예시를 먼저 보여줌", "선택지를 줄임", "해야 할 순서를 확인함", "기다릴 시간을 줌", "도움 요청 문장을 연습함", "안전 규칙을 먼저 확인함"],
  },
  {
    key: "communicationNeedText",
    title: "의사소통·대체기술",
    description: "키워야 할 요구 표현과 상호작용",
    options: ["도움 요청", "다시 말해달라고 요청", "중단·쉬기 요청", "순서 확인 질문", "거절 표현", "또래에게 먼저 묻기", "상황에 맞게 인사하기"],
  },
  {
    key: "calmingSupportsText",
    title: "정서·행동 안정 조건",
    description: "불안이나 부담을 낮춘 관찰 조건",
    options: ["예고가 있을 때 안정됨", "기다릴 시간이 있을 때 안정됨", "선택권이 있을 때 안정됨", "선생님 예시를 본 뒤 안정됨", "조용한 환경에서 안정됨", "실패 뒤 격려가 필요함"],
  },
  {
    key: "avoidGuidanceText",
    title: "피해야 할 조건",
    description: "문제행동이나 부담을 키울 수 있는 상황",
    options: ["오류 직후 재촉", "틀림을 강조", "갑작스러운 전환", "선택지를 많이 제시", "소음이 큰 자리", "낯선 역할을 바로 요구", "긴 설명부터 시작"],
  },
  ],
};

const checklistIntroByType: Record<ContentType, { title: string; description: string }> = {
  learning_focus: {
    title: "학습 반응 관점으로 빠르게 선택",
    description: "개념 이해, 문제 조건 처리, 읽기 부담, 설명하기 반응을 등록 흐름에 맞게 줄인 항목입니다.",
  },
  life_support: {
    title: "센터 관찰 관점으로 빠르게 선택",
    description: "기능평가, 행동 기능 설문, 도전적 행동 우선순위 관점을 교사용 등록 흐름에 맞게 줄인 항목입니다.",
  },
};

const currentGoalPlaceholderByType: Record<ContentType, string> = {
  learning_focus: "예: 오늘 다룰 개념이나 자료 이해 목표를 적어주세요",
  life_support: "예: 생활 상황에서 필요한 말이나 행동을 짧게 연습하기",
};

const observationPlaceholderByType: Record<ContentType, string> = {
  learning_focus: "예: 그림이나 예시가 먼저 있으면 문제를 시작하고, 긴 조건을 한 번에 읽으면 핵심 단서를 놓칠 수 있음",
  life_support: "예: 수업 관찰에서 확인한 반응이나 조정점",
};

const inputClass =
  "mt-2 w-full rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-bold text-[#172033] outline-none transition placeholder:text-[#94a3b8] focus:border-[#1f3a5f]";
const textareaClass =
  "mt-2 w-full resize-none rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-semibold leading-6 text-[#172033] outline-none transition placeholder:text-[#94a3b8] focus:border-[#1f3a5f]";

function SectionHeading({
  step,
  title,
  description,
  badge,
}: {
  step: string;
  title: string;
  description: string;
  badge?: string;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p className="text-sm font-black text-[#1f3a5f]">{step}</p>
        <h3 className="mt-1 text-xl font-black text-[#172033]">{title}</h3>
        <p className="mt-1 text-sm font-semibold leading-6 text-[#64748b]">{description}</p>
      </div>
      {badge && <span className="rounded-full bg-[#f1f5f9] px-3 py-1 text-xs font-black text-[#64748b]">{badge}</span>}
    </div>
  );
}

function createDefaultRegistrationForm(): RegistrationFormState {
  return {
    displayName: "",
    schoolQuery: "",
    officeCode: "",
    grade: "초3",
    className: "",
    studentType: "learning_focus",
    currentGoal: "",
    observationNote: "",
    strengthsText: "",
    weaknessesText: "",
    preferredSupportsText: "",
    instructionBurdenText: "",
    communicationNeedText: "",
    calmingSupportsText: "",
    avoidGuidanceText: "",
    guardianShareNote: "",
  };
}

function schoolDisplayName(school: SchoolProfile) {
  return school.schoolName || school.name || "학교명 확인 중";
}

function schoolAddress(school: SchoolProfile) {
  return school.roadAddress || school.address || school.regionName || "주소 정보 확인 중";
}

function officeDisplayName(officeCode: string) {
  if (!officeCode) return "전국 학교 검색";
  return officeCodeLabels[officeCode] ?? "학교 선택 후 자동 확인";
}

function splitList(value: string) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 8);
}

function gradeNumberFromGrade(grade: string) {
  const match = grade.match(/\d+/);
  return match ? match[0] : null;
}

function supportIntakeFromForm(form: RegistrationFormState, strengths: string[], weaknesses: string[], preferredSupports: string[]) {
  const instructionBurdens = splitList(form.instructionBurdenText);
  const communicationNeeds = splitList(form.communicationNeedText);
  const calmingSupports = splitList(form.calmingSupportsText);
  const avoidGuidance = splitList(form.avoidGuidanceText);
  const sourceBasis =
    form.studentType === "learning_focus"
      ? ["기초학력 지원 관찰 관점", "학습 과제 반응 관점", "문제 조건·읽기 부담 조정 관점"]
      : ["센터 관찰 자료의 기능평가 관점", "QABF의 행동 기능 가설 관점", "도전적 행동 우선순위 체크리스트의 지원 우선순위 관점"];

  return {
    sourceBasis,
    learningResponse: {
      observedStrengths: strengths,
      effectiveSupports: preferredSupports,
      readingLoad:
        weaknesses.some((weakness) => weakness.includes("긴 문장") || weakness.includes("읽기")) ||
        instructionBurdens.some((burden) => burden.includes("긴") || burden.includes("읽기") || burden.includes("긴 글"))
          ? "low"
          : "medium",
      instructionBurdens,
      communicationNeeds,
    },
    challengeBehaviorPriorities: weaknesses.map((label, index) => ({
      label,
      priority: index + 1,
    })),
    behaviorFunctionHypotheses: [...weaknesses, ...instructionBurdens].filter(
      (item) => item.includes("회피") || item.includes("기다림") || item.includes("불안") || item.includes("부담"),
    ),
    replacementSkills:
      communicationNeeds.length > 0
        ? communicationNeeds
        : form.studentType === "life_support"
        ? ["도움 요청하기", "순서 확인하기"]
        : ["다시 말해달라고 하기", "순서 확인하기"],
    recommendedScaffolds: [...preferredSupports, ...calmingSupports],
    avoidGuidance: [...weaknesses, ...avoidGuidance],
    teacherObservation: form.observationNote.trim(),
    guardianShareNote: form.guardianShareNote.trim() || null,
    checklistSummary: {
      observedStrengths: strengths,
      hardSituations: weaknesses,
      effectiveSupports: preferredSupports,
      instructionBurdens,
      communicationNeeds,
      calmingSupports,
      avoidGuidance,
    },
  };
}

function getRequestErrorMessage(error: unknown) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "요청을 처리하지 못했습니다. 입력값을 확인한 뒤 다시 시도해 주세요.";
}

function ChecklistGroup({
  title,
  description,
  required,
  options,
  values,
  onToggle,
}: {
  title: string;
  description: string;
  required?: boolean;
  options: string[];
  values: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <section className="rounded-lg border border-[#d8dee8] bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-black text-[#172033]">{title}</h3>
          <p className="mt-1 text-xs font-bold leading-5 text-[#64748b]">{description}</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {required && <span className="rounded-full bg-[#eef4fb] px-2 py-1 text-[11px] font-black text-[#1f3a5f]">필수</span>}
          <span className="rounded-full bg-[#f8fafc] px-2 py-1 text-[11px] font-black text-[#64748b]">{values.length}개 선택</span>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {options.map((option) => {
          const selected = values.includes(option);

          return (
            <button
              key={option}
              type="button"
              onClick={() => onToggle(option)}
              className={`rounded-full border px-3 py-2 text-xs font-black transition ${
                selected
                  ? "border-[#1f3a5f] bg-[#1f3a5f] text-white shadow-[0_8px_18px_rgba(31,58,95,0.16)]"
                  : "border-[#d8dee8] bg-[#f8fafc] text-[#475569] hover:border-[#94a3b8]"
              }`}
            >
              {option}
            </button>
          );
        })}
      </div>
    </section>
  );
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
  const activeChecklistGroups = supportChecklistGroupsByType[form.studentType];
  const checklistIntro = checklistIntroByType[form.studentType];
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

  const toggleChecklistValue = (key: ChecklistField, value: string) => {
    setForm((current) => {
      const currentValues = splitList(current[key]);
      const nextValues = currentValues.includes(value)
        ? currentValues.filter((item) => item !== value)
        : [...currentValues, value];
      return {
        ...current,
        [key]: nextValues.join("\n"),
      };
    });
  };

  const handleStudentTypeChange = (studentType: ContentType) => {
    setForm((current) => ({
      ...current,
      studentType,
      strengthsText: "",
      weaknessesText: "",
      preferredSupportsText: "",
      instructionBurdenText: "",
      communicationNeedText: "",
      calmingSupportsText: "",
      avoidGuidanceText: "",
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
        officeCode: form.officeCode.trim() || undefined,
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
        className="flex max-h-[92vh] w-[min(96vw,1180px)] flex-col overflow-hidden rounded-xl bg-white shadow-[0_30px_90px_rgba(15,23,42,0.28)]"
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
          <div className="space-y-5">
            <section className="rounded-lg border border-[#d8dee8] bg-white p-5">
              <SectionHeading
                step="1 기본 정보"
                title="학생과 학교 확인"
                description="학생 기본 정보와 학교를 먼저 확인합니다. 학교를 선택하면 교육청 정보가 자동으로 반영됩니다."
                badge="필수 정보"
              />

              <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(220px,1fr)_120px_minmax(180px,240px)_minmax(120px,1fr)]">
              <div>
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
              </div>
              <div>
                <span className="block text-sm font-bold text-[#64748b]">교육청</span>
                <div className="mt-2 rounded-md border border-[#cbd5e1] bg-[#f8fafc] px-3 py-3 text-sm font-black text-[#334155]">
                  {officeDisplayName(selectedSchool?.officeCode || form.officeCode)}
                </div>
              </div>

              <div>
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
              </div>
              <div>
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

              <section className="rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-4 lg:col-span-4">
                <div className="grid gap-3 lg:grid-cols-[170px_minmax(260px,420px)_88px_minmax(220px,1fr)] lg:items-end">
                  <div className="lg:self-center">
                    <p className="text-sm font-black text-[#172033]">학교 선택</p>
                    <p className="mt-1 text-xs font-semibold leading-5 text-[#64748b]">
                      학교명 일부로 검색한 뒤 선택합니다.
                    </p>
                  </div>

                  <label className="block">
                    <span className="text-sm font-bold text-[#64748b]">학교명</span>
                    <input
                      value={form.schoolQuery}
                      onChange={(event) => {
                        updateForm("schoolQuery", event.target.value);
                        setSelectedSchool(null);
                      }}
                      className="mt-2 w-full rounded-md border border-[#cbd5e1] bg-white px-3 py-3 text-sm font-bold text-[#172033] outline-none transition placeholder:text-[#94a3b8] focus:border-[#1f3a5f]"
                      placeholder="학교명을 입력하세요"
                    />
                  </label>

                  <button
                    type="button"
                    onClick={() => void handleSearchSchools()}
                    disabled={isSearchingSchools}
                    className="h-[46px] rounded-md bg-[#1f3a5f] px-5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-[#94a3b8]"
                  >
                    {isSearchingSchools ? "검색 중" : "검색"}
                  </button>

                  <div className="min-h-[46px] rounded-md border border-[#d8dee8] bg-white px-3 py-2">
                    {selectedSchool ? (
                      <>
                        <p className="text-xs font-black text-[#15803d]">선택된 학교</p>
                        <p className="mt-0.5 truncate text-sm font-black text-[#172033]">
                          {schoolDisplayName(selectedSchool)}
                        </p>
                      </>
                    ) : (
                      <p className="text-sm font-semibold leading-6 text-[#94a3b8]">
                        검색 후 등록할 학교를 선택하세요.
                      </p>
                    )}
                  </div>
                </div>
                {schoolSearchError && <p className="mt-3 text-sm font-bold text-[#b42318]">{schoolSearchError}</p>}
                {schoolSearchMessage && <p className="mt-3 text-sm font-bold text-[#1d4ed8]">{schoolSearchMessage}</p>}
                <div className="mt-3 grid max-h-52 gap-2 overflow-y-auto md:grid-cols-2">
                  {schoolResults.map((school) => {
                    const selected = selectedSchool?.schoolCode === school.schoolCode;

                    return (
                      <button
                        key={`${school.officeCode}-${school.schoolCode}`}
                        type="button"
                        onClick={() => {
                          setSelectedSchool(school);
                          updateForm("schoolQuery", schoolDisplayName(school));
                          updateForm("officeCode", school.officeCode || "R10");
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
              </section>

              <div className="flex items-center gap-3 pt-2 lg:col-span-4">
                <p className="text-sm font-black text-[#1f3a5f]">2 지원 방향</p>
                <div className="h-px flex-1 bg-[#edf2f7]" />
              </div>

              <fieldset className="rounded-lg border border-[#e5e9f0] bg-[#fbfcfe] p-4 lg:col-span-2 lg:row-span-2">
                <legend className="px-1 text-sm font-bold text-[#64748b]">학생 유형</legend>
                <p className="mt-1 text-xs font-semibold leading-5 text-[#64748b]">
                  자료를 어떤 관점으로 만들지 먼저 정합니다.
                </p>
                <div className="mt-3 grid gap-2">
                  {studentTypeOptions.map((option) => {
                    const selected = form.studentType === option.value;

                    return (
                      <label
                        key={option.value}
                        className={`block cursor-pointer rounded-md border p-4 transition ${
                          selected
                            ? "border-[#1f3a5f] bg-[#eef4fb] shadow-[0_8px_18px_rgba(31,58,95,0.08)]"
                            : "border-[#d8dee8] bg-white hover:border-[#94a3b8]"
                        }`}
                      >
                        <input
                          type="radio"
                          name="studentType"
                          value={option.value}
                          checked={selected}
                          onChange={() => handleStudentTypeChange(option.value)}
                          className="sr-only"
                        />
                        <span className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-base font-black text-[#172033]">{option.label}</span>
                          {selected && (
                            <span className="rounded-full bg-[#1f3a5f] px-2.5 py-1 text-[11px] font-black text-white">
                              선택됨
                            </span>
                          )}
                        </span>
                        <span className="mt-1 block text-sm font-semibold leading-6 text-[#64748b]">
                          {option.description}
                        </span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              <label className="block lg:col-span-2">
                <span className="text-sm font-bold text-[#64748b]">현재 지원 목표</span>
                <textarea
                  value={form.currentGoal}
                  onChange={(event) => updateForm("currentGoal", event.target.value)}
                  className={`${textareaClass} h-20`}
                  placeholder={currentGoalPlaceholderByType[form.studentType]}
                  required
                />
              </label>
              <label className="block lg:col-span-2">
                <span className="text-sm font-bold text-[#64748b]">기초 관찰 메모</span>
                <textarea
                  value={form.observationNote}
                  onChange={(event) => updateForm("observationNote", event.target.value)}
                  className={`${textareaClass} h-20`}
                  placeholder={observationPlaceholderByType[form.studentType]}
                  required
                />
              </label>
              </div>
            </section>

            <section className="space-y-4">
              <section className="rounded-lg border border-[#d8dee8] bg-[#fbfcfe] p-5">
                <SectionHeading
                  step="3 지원 체크리스트"
                  title={checklistIntro.title}
                  description={checklistIntro.description}
                  badge="필수 3개 영역"
                />
              </section>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {activeChecklistGroups.map((group) => (
                  <ChecklistGroup
                    key={group.key}
                    title={group.title}
                    description={group.description}
                    required={group.required}
                    options={group.options}
                    values={splitList(form[group.key])}
                    onToggle={(value) => toggleChecklistValue(group.key, value)}
                  />
                ))}
              </div>

              <section className="rounded-lg border border-[#e5e9f0] bg-white p-4">
                <label className="block">
                  <span className="text-sm font-bold text-[#64748b]">보호자·센터 공유 참고사항</span>
                  <textarea
                    value={form.guardianShareNote}
                    onChange={(event) => updateForm("guardianShareNote", event.target.value)}
                    className={`${textareaClass} h-20`}
                    placeholder="공유 전 확인할 내용이나 가정 연계 시 주의할 점"
                  />
                </label>
              </section>
            </section>
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
