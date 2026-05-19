from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import StudentType
from app.domain.schemas import MissionContent


class Organization(BaseModel):
    id: str
    external_key: str = Field(alias="externalKey")
    name: str
    type: Literal["learning_support_center", "school", "demo"]
    region_code: str | None = Field(default=None, alias="regionCode")

    model_config = ConfigDict(populate_by_name=True)


class User(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    email: str
    display_name: str = Field(alias="displayName")
    role: Literal["center_admin", "teacher", "content_reviewer", "guardian"]
    status: Literal["active", "invited", "disabled"] = "active"

    model_config = ConfigDict(populate_by_name=True)


class Student(BaseModel):
    id: str
    organization_id: str = Field(alias="organizationId")
    external_key: str = Field(alias="externalKey")
    display_name: str = Field(alias="displayName")
    grade: str
    school_code: str | None = Field(default=None, alias="schoolCode")
    student_type: StudentType = Field(alias="studentType")
    primary_need: str = Field(alias="primaryNeed")
    profile_json: dict[str, Any] = Field(default_factory=dict, alias="profileJson")
    status: Literal["active", "archived"] = "active"

    model_config = ConfigDict(populate_by_name=True)


class StudentAccount(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    access_code: str = Field(alias="accessCode")
    status: Literal["active", "disabled"] = "active"

    model_config = ConfigDict(populate_by_name=True)


class SchoolProfile(BaseModel):
    id: str
    office_code: str = Field(alias="officeCode")
    school_code: str = Field(alias="schoolCode")
    school_name: str = Field(alias="schoolName")
    school_kind: str = Field(alias="schoolKind")
    region_name: str = Field(alias="regionName")
    road_address: str = Field(alias="roadAddress")
    source_code: str = Field(default="neis_open_api", alias="sourceCode")

    model_config = ConfigDict(populate_by_name=True)


class SchoolCalendarEvent(BaseModel):
    id: str
    school_code: str = Field(alias="schoolCode")
    office_code: str = Field(alias="officeCode")
    academic_year: str = Field(alias="academicYear")
    event_date: str = Field(alias="eventDate")
    event_name: str = Field(alias="eventName")
    event_content: str | None = Field(default=None, alias="eventContent")
    schedule_type: str | None = Field(default=None, alias="scheduleType")
    applies_to_grades: list[str] = Field(default_factory=list, alias="appliesToGrades")
    source_code: str = Field(default="neis_school_schedule", alias="sourceCode")
    retrieved_at: str = Field(alias="retrievedAt")

    model_config = ConfigDict(populate_by_name=True)


class SchoolTimetableSlot(BaseModel):
    id: str
    school_code: str = Field(alias="schoolCode")
    office_code: str = Field(alias="officeCode")
    academic_year: str = Field(alias="academicYear")
    semester: str
    timetable_date: str = Field(alias="timetableDate")
    grade: str
    class_name: str = Field(alias="className")
    period: int
    subject_name: str | None = Field(default=None, alias="subjectName")
    source_code: str = Field(alias="sourceCode")
    retrieved_at: str = Field(alias="retrievedAt")

    model_config = ConfigDict(populate_by_name=True)


class SupportCase(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    owner_teacher_id: str = Field(alias="ownerTeacherId")
    case_status: Literal["open", "paused", "closed"] = Field(default="open", alias="caseStatus")
    current_goal: str = Field(alias="currentGoal")
    dashboard_stage: Literal["initial_review", "material_generation", "material_review", "learning", "feedback"] = Field(
        default="initial_review",
        alias="dashboardStage",
    )
    support_strategy: str | None = Field(default=None, alias="supportStrategy")
    opened_at: str = Field(alias="openedAt")

    model_config = ConfigDict(populate_by_name=True)


class CaseNote(BaseModel):
    id: str
    case_id: str = Field(alias="caseId")
    author_id: str = Field(alias="authorId")
    note_type: Literal["consultation", "session", "teacher_comment", "guardian"] = Field(alias="noteType")
    body: str
    visibility: Literal["teacher_only", "center", "guardian_summary"] = "teacher_only"
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class MemoryCard(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    case_id: str = Field(alias="caseId")
    version: int
    learning_problem_types: list[str] = Field(alias="learningProblemTypes")
    recent_4w_response_json: dict[str, Any] = Field(default_factory=dict, alias="recent4wResponseJson")
    emotional_state_note: str | None = Field(default=None, alias="emotionalStateNote")
    effective_explanation_styles: list[str] = Field(alias="effectiveExplanationStyles")
    frequent_blocking_units: list[str] = Field(alias="frequentBlockingUnits")
    guardian_cooperation_status: str | None = Field(default=None, alias="guardianCooperationStatus")
    next_session_cautions: list[str] = Field(alias="nextSessionCautions")
    teacher_verified_at: str | None = Field(default=None, alias="teacherVerifiedAt")
    status: Literal["active", "superseded"] = "active"

    model_config = ConfigDict(populate_by_name=True)


class PlannerItem(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    case_id: str = Field(alias="caseId")
    period_type: Literal["weekly", "monthly", "next_session"] = Field(alias="periodType")
    goal_text: str = Field(alias="goalText")
    checklist_json: dict[str, Any] = Field(default_factory=dict, alias="checklistJson")
    status: Literal["planned", "done", "skipped"] = "planned"

    model_config = ConfigDict(populate_by_name=True)


class ContentAttempt(BaseModel):
    id: str
    mission_content_id: str = Field(alias="missionContentId")
    student_id: str = Field(alias="studentId")
    status: Literal["in_progress", "completed", "abandoned"] = "in_progress"
    current_step: int = Field(default=1, alias="currentStep")
    started_at: str = Field(alias="startedAt")
    completed_at: str | None = Field(default=None, alias="completedAt")
    score_json: dict[str, Any] | None = Field(default=None, alias="scoreJson")

    model_config = ConfigDict(populate_by_name=True)


class ActivityEvent(BaseModel):
    id: str
    attempt_id: str | None = Field(default=None, alias="attemptId")
    student_id: str = Field(alias="studentId")
    stage_id: str | None = Field(default=None, alias="stageId")
    event_type: str = Field(alias="eventType")
    payload_json: dict[str, Any] = Field(default_factory=dict, alias="payloadJson")
    occurred_at: str = Field(alias="occurredAt")

    model_config = ConfigDict(populate_by_name=True)


class RealtimePracticeSession(BaseModel):
    id: str
    attempt_id: str = Field(alias="attemptId")
    mission_content_id: str = Field(alias="missionContentId")
    stage_id: str = Field(alias="stageId")
    student_id: str = Field(alias="studentId")
    provider: Literal["openai"] = "openai"
    model: str
    status: Literal["created", "active", "completed", "failed", "expired"] = "created"
    spec_snapshot_json: dict[str, Any] = Field(default_factory=dict, alias="specSnapshotJson")
    started_at: str | None = Field(default=None, alias="startedAt")
    ended_at: str | None = Field(default=None, alias="endedAt")
    turn_count: int = Field(default=0, alias="turnCount")
    duration_sec: int = Field(default=0, alias="durationSec")
    rubric_result_json: dict[str, Any] | None = Field(default=None, alias="rubricResultJson")
    transcript_summary: str | None = Field(default=None, alias="transcriptSummary")

    model_config = ConfigDict(populate_by_name=True)


class PublicDataSource(BaseModel):
    id: str
    source_code: str = Field(alias="sourceCode")
    name: str
    base_url: str | None = Field(default=None, alias="baseUrl")
    auth_type: Literal["api_key", "none", "manual_seed"] = Field(alias="authType")
    enabled: bool

    model_config = ConfigDict(populate_by_name=True)


class AgentRun(BaseModel):
    id: str
    agent_type: str = Field(alias="agentType")
    prompt_version: str = Field(alias="promptVersion")
    output_schema_name: str = Field(alias="outputSchemaName")
    input_snapshot_json: dict[str, Any] = Field(default_factory=dict, alias="inputSnapshotJson")
    output_json: dict[str, Any] | None = Field(default=None, alias="outputJson")
    model: str
    status: Literal["running", "succeeded", "failed"] = "running"
    token_usage_json: dict[str, Any] | None = Field(default=None, alias="tokenUsageJson")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")
    review_required: bool = Field(default=False, alias="reviewRequired")
    created_at: str = Field(alias="createdAt")
    completed_at: str | None = Field(default=None, alias="completedAt")

    model_config = ConfigDict(populate_by_name=True)


class ReviewSummary(BaseModel):
    id: str
    attempt_id: str = Field(alias="attemptId")
    student_id: str = Field(alias="studentId")
    completion_rate: float = Field(alias="completionRate")
    accuracy_rate: float = Field(alias="accuracyRate")
    short_summary: str = Field(alias="shortSummary")
    wrong_pattern_json: dict[str, Any] = Field(default_factory=dict, alias="wrongPatternJson")
    realtime_result_json: dict[str, Any] = Field(default_factory=dict, alias="realtimeResultJson")

    model_config = ConfigDict(populate_by_name=True)


class StudentSupportIntakeSource(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    source_type: Literal["teacher_registration", "teacher_update", "center_summary"] = Field(alias="sourceType")
    payload_json: dict[str, Any] = Field(default_factory=dict, alias="payloadJson")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class StudentSupportProfile(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    source_intake_id: str | None = Field(default=None, alias="sourceIntakeId")
    status: Literal["draft", "confirmed", "superseded"] = "draft"
    profile_json: dict[str, Any] = Field(default_factory=dict, alias="profileJson")
    generated_by: str = Field(default="local_demo_ai", alias="generatedBy")
    teacher_confirmed_by_user_id: str | None = Field(default=None, alias="teacherConfirmedByUserId")
    created_at: str = Field(alias="createdAt")
    confirmed_at: str | None = Field(default=None, alias="confirmedAt")

    model_config = ConfigDict(populate_by_name=True)


class StudentContextBrief(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    brief_text: str = Field(alias="briefText")
    student_type: str = Field(alias="studentType")
    reading_load: str = Field(alias="readingLoad")
    choice_count: int = Field(alias="choiceCount")
    recent_success_patterns: list[str] = Field(default_factory=list, alias="recentSuccessPatterns")
    recent_difficulty_patterns: list[str] = Field(default_factory=list, alias="recentDifficultyPatterns")
    recommended_scaffolds: list[str] = Field(default_factory=list, alias="recommendedScaffolds")
    avoid_topic_regression: list[str] = Field(default_factory=list, alias="avoidTopicRegression")
    source_watermark: str = Field(alias="sourceWatermark")
    dirty: bool = True
    status: Literal["dirty", "refreshed"] = "dirty"
    source_json: dict[str, Any] = Field(default_factory=dict, alias="sourceJson")
    model: str = "local_demo_ai"
    refreshed_at: str | None = Field(default=None, alias="refreshedAt")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class TeacherReportDraft(BaseModel):
    id: str
    review_summary_id: str = Field(alias="reviewSummaryId")
    student_id: str = Field(alias="studentId")
    content_id: str = Field(alias="contentId")
    status: Literal["streaming", "completed", "failed"] = "completed"
    body_markdown: str = Field(alias="bodyMarkdown")
    next_learning_suggestions: list[str] = Field(default_factory=list, alias="nextLearningSuggestions")
    memory_candidates: list[str] = Field(default_factory=list, alias="memoryCandidates")
    input_snapshot_json: dict[str, Any] = Field(default_factory=dict, alias="inputSnapshotJson")
    model: str = "local_demo_ai"
    created_at: str = Field(alias="createdAt")
    completed_at: str | None = Field(default=None, alias="completedAt")

    model_config = ConfigDict(populate_by_name=True)


class TeacherReport(BaseModel):
    id: str
    draft_id: str | None = Field(default=None, alias="draftId")
    review_summary_id: str = Field(alias="reviewSummaryId")
    student_id: str = Field(alias="studentId")
    content_id: str = Field(alias="contentId")
    teacher_body: str = Field(alias="teacherBody")
    selected_memory_candidates: list[str] = Field(default_factory=list, alias="selectedMemoryCandidates")
    created_by_user_id: str = Field(alias="createdByUserId")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


GenerationJobStatus = Literal[
    "queued",
    "orchestrating",
    "content_generating",
    "asset_generating",
    "ready_for_review",
    "failed",
    "cancelled",
]


class GenerationJob(BaseModel):
    id: str
    teacher_id: str = Field(alias="teacherId")
    student_id: str = Field(alias="studentId")
    case_id: str = Field(alias="caseId")
    content_type: StudentType = Field(alias="contentType")
    requested_goal: str | None = Field(default=None, alias="requestedGoal")
    status: GenerationJobStatus
    phase: GenerationJobStatus
    message: str
    orchestrator_run_id: str | None = Field(default=None, alias="orchestratorRunId")
    content_run_id: str | None = Field(default=None, alias="contentRunId")
    content_id: str | None = Field(default=None, alias="contentId")
    asset_job_id: str | None = Field(default=None, alias="assetJobId")
    progress_json: dict[str, Any] = Field(default_factory=dict, alias="progressJson")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    completed_at: str | None = Field(default=None, alias="completedAt")

    model_config = ConfigDict(populate_by_name=True)


class AuditLog(BaseModel):
    id: str
    actor_user_id: str | None = Field(default=None, alias="actorUserId")
    student_id: str | None = Field(default=None, alias="studentId")
    action: str
    resource_type: str = Field(alias="resourceType")
    resource_id: str | None = Field(default=None, alias="resourceId")
    payload_json: dict[str, Any] | None = Field(default=None, alias="payloadJson")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class DemoDatabase(BaseModel):
    organizations: list[Organization]
    users: list[User]
    students: list[Student]
    student_accounts: list[StudentAccount] = Field(alias="studentAccounts")
    schools: list[SchoolProfile] = Field(default_factory=list)
    school_calendar_events: list[SchoolCalendarEvent] = Field(default_factory=list, alias="schoolCalendarEvents")
    school_timetable_slots: list[SchoolTimetableSlot] = Field(default_factory=list, alias="schoolTimetableSlots")
    support_cases: list[SupportCase] = Field(alias="supportCases")
    case_notes: list[CaseNote] = Field(alias="caseNotes")
    memory_cards: list[MemoryCard] = Field(alias="memoryCards")
    planner_items: list[PlannerItem] = Field(alias="plannerItems")
    mission_contents: list[MissionContent] = Field(alias="missionContents")
    attempts: list[ContentAttempt] = Field(default_factory=list)
    activity_events: list[ActivityEvent] = Field(default_factory=list, alias="activityEvents")
    realtime_sessions: list[RealtimePracticeSession] = Field(default_factory=list, alias="realtimeSessions")
    public_data_sources: list[PublicDataSource] = Field(alias="publicDataSources")
    review_summaries: list[ReviewSummary] = Field(default_factory=list, alias="reviewSummaries")
    student_support_intake_sources: list[StudentSupportIntakeSource] = Field(default_factory=list, alias="studentSupportIntakeSources")
    student_support_profiles: list[StudentSupportProfile] = Field(default_factory=list, alias="studentSupportProfiles")
    student_context_briefs: list[StudentContextBrief] = Field(default_factory=list, alias="studentContextBriefs")
    teacher_report_drafts: list[TeacherReportDraft] = Field(default_factory=list, alias="teacherReportDrafts")
    teacher_reports: list[TeacherReport] = Field(default_factory=list, alias="teacherReports")
    audit_logs: list[AuditLog] = Field(default_factory=list, alias="auditLogs")

    model_config = ConfigDict(populate_by_name=True)
