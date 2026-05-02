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


class SupportCase(BaseModel):
    id: str
    student_id: str = Field(alias="studentId")
    owner_teacher_id: str = Field(alias="ownerTeacherId")
    case_status: Literal["open", "paused", "closed"] = Field(default="open", alias="caseStatus")
    current_goal: str = Field(alias="currentGoal")
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


class DemoDatabase(BaseModel):
    organizations: list[Organization]
    users: list[User]
    students: list[Student]
    student_accounts: list[StudentAccount] = Field(alias="studentAccounts")
    support_cases: list[SupportCase] = Field(alias="supportCases")
    case_notes: list[CaseNote] = Field(alias="caseNotes")
    memory_cards: list[MemoryCard] = Field(alias="memoryCards")
    planner_items: list[PlannerItem] = Field(alias="plannerItems")
    mission_contents: list[MissionContent] = Field(alias="missionContents")
    attempts: list[ContentAttempt] = Field(default_factory=list)
    activity_events: list[ActivityEvent] = Field(default_factory=list, alias="activityEvents")
    realtime_sessions: list[RealtimePracticeSession] = Field(default_factory=list, alias="realtimeSessions")
    public_data_sources: list[PublicDataSource] = Field(alias="publicDataSources")

    model_config = ConfigDict(populate_by_name=True)
