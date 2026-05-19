from sqlalchemy import JSON, Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrganizationRow(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    external_key: Mapped[str | None] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    region_code: Mapped[str | None] = mapped_column(String)


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, index=True)
    password_hash: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")


class StudentRow(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    external_key: Mapped[str | None] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    grade: Mapped[str] = mapped_column(String)
    school_code: Mapped[str | None] = mapped_column(String, index=True)
    student_type: Mapped[str] = mapped_column(String, index=True)
    primary_need: Mapped[str] = mapped_column(String)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="active")


class StudentAccountRow(Base):
    __tablename__ = "student_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    access_code: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String, default="active")


class SchoolProfileRow(Base):
    __tablename__ = "school_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    office_code: Mapped[str] = mapped_column(String, index=True)
    school_code: Mapped[str] = mapped_column(String, unique=True)
    school_name: Mapped[str] = mapped_column(String)
    school_kind: Mapped[str] = mapped_column(String)
    region_name: Mapped[str] = mapped_column(String)
    road_address: Mapped[str] = mapped_column(String)
    source_code: Mapped[str] = mapped_column(String, default="neis_open_api")


class SchoolCalendarEventRow(Base):
    __tablename__ = "school_calendar_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    school_code: Mapped[str] = mapped_column(String, index=True)
    office_code: Mapped[str] = mapped_column(String, index=True)
    academic_year: Mapped[str] = mapped_column(String)
    event_date: Mapped[str] = mapped_column(String, index=True)
    event_name: Mapped[str] = mapped_column(String)
    event_content: Mapped[str | None] = mapped_column(Text)
    schedule_type: Mapped[str | None] = mapped_column(String)
    applies_to_grades: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_code: Mapped[str] = mapped_column(String, default="neis_school_schedule")
    retrieved_at: Mapped[str] = mapped_column(String)


class SchoolTimetableSlotRow(Base):
    __tablename__ = "school_timetable_slots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    school_code: Mapped[str] = mapped_column(String, index=True)
    office_code: Mapped[str] = mapped_column(String, index=True)
    academic_year: Mapped[str] = mapped_column(String)
    semester: Mapped[str] = mapped_column(String)
    timetable_date: Mapped[str] = mapped_column(String, index=True)
    grade: Mapped[str] = mapped_column(String, index=True)
    class_name: Mapped[str] = mapped_column(String, index=True)
    period: Mapped[int] = mapped_column(Integer)
    subject_name: Mapped[str | None] = mapped_column(String)
    source_code: Mapped[str] = mapped_column(String)
    retrieved_at: Mapped[str] = mapped_column(String)


class SupportCaseRow(Base):
    __tablename__ = "support_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    owner_teacher_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    case_status: Mapped[str] = mapped_column(String, default="open")
    current_goal: Mapped[str] = mapped_column(Text)
    dashboard_stage: Mapped[str] = mapped_column(String, default="initial_review")
    support_strategy: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[str] = mapped_column(String)


class CaseNoteRow(Base):
    __tablename__ = "case_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    note_type: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String, default="teacher_only")
    created_at: Mapped[str] = mapped_column(String)


class MemoryCardRow(Base):
    __tablename__ = "memory_cards"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    learning_problem_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    recent_4w_response_json: Mapped[dict] = mapped_column(JSON, default=dict)
    emotional_state_note: Mapped[str | None] = mapped_column(Text)
    effective_explanation_styles: Mapped[list[str]] = mapped_column(JSON, default=list)
    frequent_blocking_units: Mapped[list[str]] = mapped_column(JSON, default=list)
    guardian_cooperation_status: Mapped[str | None] = mapped_column(String)
    next_session_cautions: Mapped[list[str]] = mapped_column(JSON, default=list)
    teacher_verified_at: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")


class PlannerItemRow(Base):
    __tablename__ = "planner_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"), index=True)
    period_type: Mapped[str] = mapped_column(String)
    goal_text: Mapped[str] = mapped_column(Text)
    checklist_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="planned")


class MissionContentRow(Base):
    __tablename__ = "mission_contents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    content_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    session_goal: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, index=True)
    total_steps: Mapped[int] = mapped_column(Integer, default=4)
    brief_json: Mapped[dict] = mapped_column(JSON, default=dict)
    teacher_review_summary: Mapped[str | None] = mapped_column(Text)
    approved_by_user_id: Mapped[str | None] = mapped_column(String)
    approved_at: Mapped[str | None] = mapped_column(String)
    published_at: Mapped[str | None] = mapped_column(String)


class ContentStageRow(Base):
    __tablename__ = "content_stages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    step: Mapped[int] = mapped_column(Integer)
    stage_role: Mapped[str] = mapped_column(String)
    template_type: Mapped[str] = mapped_column(String)
    student_title: Mapped[str] = mapped_column(String)
    student_instruction: Mapped[str] = mapped_column(Text)
    template_json: Mapped[dict] = mapped_column(JSON, default=dict)
    realtime_spec_json: Mapped[dict | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(Integer)


class ContentAssetRow(Base):
    __tablename__ = "content_assets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    stage_id: Mapped[str | None] = mapped_column(String, index=True)
    asset_role: Mapped[str] = mapped_column(String, index=True)
    asset_type: Mapped[str] = mapped_column(String)
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    prompt_json: Mapped[dict | None] = mapped_column(JSON)
    source_text: Mapped[str | None] = mapped_column(Text)
    storage_url: Mapped[str] = mapped_column(String)
    preview_url: Mapped[str | None] = mapped_column(String)
    qa_status: Mapped[str] = mapped_column(String)
    approval_status: Mapped[str] = mapped_column(String)


class ContentAttemptRow(Base):
    __tablename__ = "content_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="in_progress")
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String)
    score_json: Mapped[dict | None] = mapped_column(JSON)


class ActivityEventRow(Base):
    __tablename__ = "activity_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    attempt_id: Mapped[str | None] = mapped_column(ForeignKey("content_attempts.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    stage_id: Mapped[str | None] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[str] = mapped_column(String)


class RealtimePracticeSessionRow(Base):
    __tablename__ = "realtime_practice_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("content_attempts.id"), index=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    stage_id: Mapped[str] = mapped_column(String, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="created")
    spec_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[str | None] = mapped_column(String)
    ended_at: Mapped[str | None] = mapped_column(String)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    rubric_result_json: Mapped[dict | None] = mapped_column(JSON)
    transcript_summary: Mapped[str | None] = mapped_column(Text)


class PublicDataSourceRow(Base):
    __tablename__ = "public_data_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    base_url: Mapped[str | None] = mapped_column(String)
    auth_type: Mapped[str] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ReviewSummaryRow(Base):
    __tablename__ = "review_summaries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("content_attempts.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    completion_rate: Mapped[float] = mapped_column(Numeric)
    accuracy_rate: Mapped[float] = mapped_column(Numeric)
    short_summary: Mapped[str] = mapped_column(Text)
    wrong_pattern_json: Mapped[dict] = mapped_column(JSON, default=dict)
    realtime_result_json: Mapped[dict] = mapped_column(JSON, default=dict)


class StudentSupportIntakeSourceRow(Base):
    __tablename__ = "student_support_intake_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    source_type: Mapped[str] = mapped_column(String, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String)


class StudentSupportProfileRow(Base):
    __tablename__ = "student_support_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    source_intake_id: Mapped[str | None] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True, default="draft")
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_by: Mapped[str] = mapped_column(String, default="local_demo_ai")
    teacher_confirmed_by_user_id: Mapped[str | None] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String)
    confirmed_at: Mapped[str | None] = mapped_column(String)


class StudentContextBriefRow(Base):
    __tablename__ = "student_context_briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    brief_text: Mapped[str] = mapped_column(Text)
    student_type: Mapped[str] = mapped_column(String)
    reading_load: Mapped[str] = mapped_column(String)
    choice_count: Mapped[int] = mapped_column(Integer)
    recent_success_patterns: Mapped[list[str]] = mapped_column(JSON, default=list)
    recent_difficulty_patterns: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_scaffolds: Mapped[list[str]] = mapped_column(JSON, default=list)
    avoid_topic_regression: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_watermark: Mapped[str] = mapped_column(String)
    dirty: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String, index=True, default="dirty")
    source_json: Mapped[dict] = mapped_column(JSON, default=dict)
    model: Mapped[str] = mapped_column(String, default="local_demo_ai")
    refreshed_at: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)


class TeacherReportDraftRow(Base):
    __tablename__ = "teacher_report_drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    review_summary_id: Mapped[str] = mapped_column(ForeignKey("review_summaries.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    status: Mapped[str] = mapped_column(String, index=True, default="completed")
    body_markdown: Mapped[str] = mapped_column(Text)
    next_learning_suggestions: Mapped[list[str]] = mapped_column(JSON, default=list)
    memory_candidates: Mapped[list[str]] = mapped_column(JSON, default=list)
    input_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    model: Mapped[str] = mapped_column(String, default="local_demo_ai")
    created_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String)


class TeacherReportRow(Base):
    __tablename__ = "teacher_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    draft_id: Mapped[str | None] = mapped_column(String, index=True)
    review_summary_id: Mapped[str] = mapped_column(ForeignKey("review_summaries.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    teacher_body: Mapped[str] = mapped_column(Text)
    selected_memory_candidates: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_by_user_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String)


class GenerationJobRow(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"), index=True)
    content_type: Mapped[str] = mapped_column(String, index=True)
    requested_goal: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, index=True)
    phase: Mapped[str] = mapped_column(String, index=True)
    message: Mapped[str] = mapped_column(Text)
    orchestrator_run_id: Mapped[str | None] = mapped_column(String, index=True)
    content_run_id: Mapped[str | None] = mapped_column(String, index=True)
    content_id: Mapped[str | None] = mapped_column(String, index=True)
    asset_job_id: Mapped[str | None] = mapped_column(String, index=True)
    progress_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String)


class AgentRunRow(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    agent_type: Mapped[str] = mapped_column(String, index=True)
    prompt_version: Mapped[str] = mapped_column(String, index=True)
    output_schema_name: Mapped[str] = mapped_column(String)
    input_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_json: Mapped[dict | None] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    token_usage_json: Mapped[dict | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String)


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    actor_user_id: Mapped[str | None] = mapped_column(String, index=True)
    student_id: Mapped[str | None] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    resource_type: Mapped[str] = mapped_column(String, index=True)
    resource_id: Mapped[str | None] = mapped_column(String, index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String)
