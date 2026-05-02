from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import AssetRole, AssetType, MissionStatus, StageRole, StudentType, TemplateType, UserRole

REALTIME_TEMPLATE_TYPES = {TemplateType.REALTIME_ROLEPLAY, TemplateType.REALTIME_TEACH_BACK}
REQUIRED_ASSET_ROLES = {
    AssetRole.HERO,
    AssetRole.STAGE_1,
    AssetRole.STAGE_2,
    AssetRole.STAGE_3,
    AssetRole.STAGE_4_REALTIME,
}


class ApiMeta(BaseModel):
    request_id: str = Field(alias="requestId")

    model_config = ConfigDict(populate_by_name=True)


class ApiResponse(BaseModel):
    data: Any
    meta: ApiMeta


class Choice(BaseModel):
    id: str
    text: str


class RubricItem(BaseModel):
    id: str
    label: str
    required: bool


class RealtimePracticeSpec(BaseModel):
    id: str
    stage_id: str = Field(alias="stageId")
    template_type: Literal[TemplateType.REALTIME_ROLEPLAY, TemplateType.REALTIME_TEACH_BACK] = Field(alias="templateType")
    image_asset_id: str = Field(alias="imageAssetId")
    mode: Literal["voice_or_text", "voice", "text"] = "voice_or_text"
    practice_title: str = Field(alias="practiceTitle")
    situation_text: str = Field(alias="situationText")
    ai_role: str = Field(alias="aiRole")
    opening_line: str = Field(alias="openingLine")
    student_goal: str = Field(alias="studentGoal")
    rubric: list[RubricItem]
    allowed_feedback: list[str] = Field(alias="allowedFeedback")
    forbidden: list[str]
    max_turns: int = Field(alias="maxTurns", gt=0, le=12)
    max_duration_sec: int = Field(alias="maxDurationSec", gt=0, le=300)
    post_practice_reflection: list[str] = Field(alias="postPracticeReflection")

    model_config = ConfigDict(populate_by_name=True)


class ContentStage(BaseModel):
    id: str
    mission_content_id: str = Field(alias="missionContentId")
    step: int = Field(ge=1, le=4)
    stage_role: StageRole = Field(alias="stageRole")
    template_type: TemplateType = Field(alias="templateType")
    student_title: str = Field(alias="studentTitle")
    student_instruction: str = Field(alias="studentInstruction")
    template_json: dict[str, Any] = Field(default_factory=dict, alias="templateJson")
    realtime_spec: RealtimePracticeSpec | None = Field(default=None, alias="realtimeSpec")
    sort_order: int = Field(alias="sortOrder", ge=1, le=4)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_realtime_contract(self) -> "ContentStage":
        is_realtime = self.template_type in REALTIME_TEMPLATE_TYPES
        if self.step == 4 and not is_realtime:
            raise ValueError("4단계는 realtime_roleplay 또는 realtime_teach_back 템플릿이어야 합니다.")
        if self.step != 4 and is_realtime:
            raise ValueError("Realtime 템플릿은 4단계에서만 사용할 수 있습니다.")
        if self.step == 4 and self.realtime_spec is None:
            raise ValueError("4단계에는 승인 대상 RealtimePracticeSpec이 필요합니다.")
        return self


class ContentAsset(BaseModel):
    id: str
    mission_content_id: str = Field(alias="missionContentId")
    stage_id: str | None = Field(default=None, alias="stageId")
    asset_role: AssetRole = Field(alias="assetRole")
    asset_type: AssetType = Field(alias="assetType")
    provider: str
    model: str
    prompt_json: dict[str, Any] | None = Field(default=None, alias="promptJson")
    source_text: str | None = Field(default=None, alias="sourceText")
    storage_url: str = Field(alias="storageUrl")
    preview_url: str | None = Field(default=None, alias="previewUrl")
    qa_status: Literal["pending", "passed", "failed"] = Field(alias="qaStatus")
    approval_status: Literal["pending", "approved", "rejected"] = Field(alias="approvalStatus")

    model_config = ConfigDict(populate_by_name=True)


class MissionContent(BaseModel):
    id: str
    case_id: str = Field(alias="caseId")
    student_id: str = Field(alias="studentId")
    content_type: StudentType = Field(alias="contentType")
    title: str
    session_goal: str = Field(alias="sessionGoal")
    status: MissionStatus
    total_steps: Literal[4] = Field(alias="totalSteps")
    stages: list[ContentStage]
    assets: list[ContentAsset]
    brief_json: dict[str, Any] = Field(default_factory=dict, alias="briefJson")
    teacher_review_summary: str | None = Field(default=None, alias="teacherReviewSummary")
    approved_by_user_id: str | None = Field(default=None, alias="approvedByUserId")
    approved_at: str | None = Field(default=None, alias="approvedAt")
    published_at: str | None = Field(default=None, alias="publishedAt")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("stages")
    @classmethod
    def validate_four_stages(cls, stages: list[ContentStage]) -> list[ContentStage]:
        if sorted(stage.step for stage in stages) != [1, 2, 3, 4]:
            raise ValueError("MissionContent는 정확히 1~4단계를 가져야 합니다.")
        return stages

    @field_validator("assets")
    @classmethod
    def validate_required_assets(cls, assets: list[ContentAsset]) -> list[ContentAsset]:
        roles = {asset.asset_role for asset in assets}
        missing = REQUIRED_ASSET_ROLES - roles
        if missing:
            missing_labels = ", ".join(sorted(role.value for role in missing))
            raise ValueError(f"필수 이미지 asset role이 없습니다: {missing_labels}")
        return assets


class DemoLoginRequest(BaseModel):
    role: Literal[UserRole.CENTER_ADMIN, UserRole.TEACHER, UserRole.CONTENT_REVIEWER, UserRole.GUARDIAN]
    email: str | None = None


class StudentAccessRequest(BaseModel):
    access_code: str = Field(alias="accessCode")

    model_config = ConfigDict(populate_by_name=True)


class MemoryCardPatch(BaseModel):
    emotional_state_note: str | None = Field(default=None, alias="emotionalStateNote")
    effective_explanation_styles: list[str] | None = Field(default=None, alias="effectiveExplanationStyles")
    frequent_blocking_units: list[str] | None = Field(default=None, alias="frequentBlockingUnits")
    guardian_cooperation_status: str | None = Field(default=None, alias="guardianCooperationStatus")
    next_session_cautions: list[str] | None = Field(default=None, alias="nextSessionCautions")

    model_config = ConfigDict(populate_by_name=True)


class CaseNoteCreate(BaseModel):
    note_type: Literal["consultation", "session", "teacher_comment", "guardian"] = Field(alias="noteType")
    body: str
    visibility: Literal["teacher_only", "center", "guardian_summary"] = "teacher_only"

    model_config = ConfigDict(populate_by_name=True)


class StageSubmitRequest(BaseModel):
    attempt_id: str = Field(alias="attemptId")
    answer: dict[str, Any]
    client_event_id: str | None = Field(default=None, alias="clientEventId")

    model_config = ConfigDict(populate_by_name=True)


class AttemptRequest(BaseModel):
    attempt_id: str = Field(alias="attemptId")

    model_config = ConfigDict(populate_by_name=True)


class ReflectionRequest(BaseModel):
    attempt_id: str = Field(alias="attemptId")
    reflection_choice: str = Field(alias="reflectionChoice")
    short_text: str | None = Field(default=None, alias="shortText")

    model_config = ConfigDict(populate_by_name=True)
