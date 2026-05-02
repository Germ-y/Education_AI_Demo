from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import AssetRole, AssetType, MissionStatus, StageRole, StudentType, TemplateType, UserRole

REALTIME_TEMPLATE_TYPES = {TemplateType.REALTIME_ROLEPLAY, TemplateType.REALTIME_TEACH_BACK}
CHOICE_TEMPLATE_TYPES = {
    TemplateType.SCENE_OBSERVATION,
    TemplateType.HIGHLIGHT_CLUE,
    TemplateType.SCENE_QUESTION,
    TemplateType.CLUE_QUESTION,
    TemplateType.APPLIED_QUESTION,
    TemplateType.ACTION_CHOICE,
    TemplateType.DECISION_CARD,
    TemplateType.EXPLANATION_CHOICE,
    TemplateType.WRONG_EXPLANATION_FIX,
}
REQUIRED_ASSET_ROLES = {
    AssetRole.HERO,
    AssetRole.STAGE_1,
    AssetRole.STAGE_2,
    AssetRole.STAGE_3,
    AssetRole.STAGE_4_REALTIME,
}
STATIC_STAGE_TEMPLATE_TYPES = {
    StageRole.SCENARIO_INTRO: {TemplateType.SCENARIO_INTRO},
    StageRole.CONCEPT_INTRO: {TemplateType.CONCEPT_INTRO},
    StageRole.CLUE_IDENTIFICATION: {
        TemplateType.SCENE_OBSERVATION,
        TemplateType.HIGHLIGHT_CLUE,
        TemplateType.CARD_MATCH,
        TemplateType.IMAGE_QUIZ,
    },
    StageRole.BASIC_PROBLEM: {
        TemplateType.SCENE_QUESTION,
        TemplateType.CLUE_QUESTION,
        TemplateType.IMAGE_QUIZ,
        TemplateType.CARD_MATCH,
        TemplateType.SEQUENCE_ORDERING,
        TemplateType.BLANK_FILL,
        TemplateType.PARTITION_PICKER,
    },
    StageRole.ACTION_SELECTION: {
        TemplateType.ACTION_CHOICE,
        TemplateType.SEQUENCE_ORDERING,
        TemplateType.CARD_MATCH,
        TemplateType.DECISION_CARD,
        TemplateType.IMAGE_QUIZ,
    },
    StageRole.APPLIED_PROBLEM: {
        TemplateType.APPLIED_QUESTION,
        TemplateType.MINI_SIMULATION,
        TemplateType.CARD_MATCH,
        TemplateType.SEQUENCE_ORDERING,
        TemplateType.BLANK_FILL,
        TemplateType.IMAGE_QUIZ,
        TemplateType.EXPLANATION_CHOICE,
        TemplateType.WRONG_EXPLANATION_FIX,
    },
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
        if self.step != 4 and self.realtime_spec is not None:
            raise ValueError("1~3단계에는 realtimeSpec을 넣을 수 없습니다.")
        if self.step != 4 and self.template_type not in STATIC_STAGE_TEMPLATE_TYPES.get(self.stage_role, set()):
            raise ValueError("stageRole과 templateType 조합이 허용되지 않습니다.")
        _validate_template_json(self.template_type, self.template_json)
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


def _validate_template_json(template_type: TemplateType, template_json: dict[str, Any]) -> None:
    if template_type == TemplateType.IMAGE_QUIZ:
        _require_keys(template_json, ["imageAssetId", "question", "choices", "answer", "correctFeedback", "wrongFeedback"], "image_quiz")
        choices = template_json.get("choices")
        if not isinstance(choices, list) or len(choices) != 3:
            raise ValueError("image_quiz는 정확히 3개의 choices를 가져야 합니다.")
        choice_ids = [choice.get("id") for choice in choices if isinstance(choice, dict)]
        if len(choice_ids) != 3 or template_json["answer"] not in choice_ids:
            raise ValueError("image_quiz.answer는 choices의 id 중 하나여야 합니다.")
    if template_type == TemplateType.CARD_MATCH:
        _require_keys(template_json, ["leftCards", "rightCards", "matches", "correctFeedback", "wrongFeedback"], "card_match")
    if template_type == TemplateType.SEQUENCE_ORDERING:
        _require_keys(template_json, ["cards", "answerOrder", "correctFeedback", "wrongFeedback"], "sequence_ordering")
    if template_type == TemplateType.BLANK_FILL:
        if "acceptedAnswers" not in template_json and "answers" not in template_json:
            raise ValueError("blank_fill은 acceptedAnswers 또는 answers를 가져야 합니다.")
        _require_any_key(template_json, ["question", "sentence"], "blank_fill")
    if template_type in CHOICE_TEMPLATE_TYPES:
        _require_keys(template_json, ["question", "choices", "answer", "correctFeedback", "wrongFeedback"], template_type.value)
        _validate_choice_answer(template_json, template_type.value)
    if template_type == TemplateType.PARTITION_PICKER:
        _require_any_key(template_json, ["question", "instruction"], "partition_picker")
        _require_any_key(template_json, ["choices", "visual"], "partition_picker")


def _require_keys(template_json: dict[str, Any], keys: list[str], template_type: str) -> None:
    missing = [key for key in keys if key not in template_json]
    if missing:
        raise ValueError(f"{template_type} templateJson 필수 필드가 없습니다: {', '.join(missing)}")


def _require_any_key(template_json: dict[str, Any], keys: list[str], template_type: str) -> None:
    if not any(key in template_json for key in keys):
        raise ValueError(f"{template_type} templateJson에는 다음 중 하나가 필요합니다: {', '.join(keys)}")


def _validate_choice_answer(template_json: dict[str, Any], template_type: str) -> None:
    choices = template_json.get("choices")
    if not isinstance(choices, list) or len(choices) < 2:
        raise ValueError(f"{template_type}.choices는 2개 이상이어야 합니다.")
    choice_ids = [choice.get("id") for choice in choices if isinstance(choice, dict)]
    if len(choice_ids) != len(choices) or template_json["answer"] not in choice_ids:
        raise ValueError(f"{template_type}.answer는 choices의 id 중 하나여야 합니다.")


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

    @model_validator(mode="after")
    def attach_stage_asset_bundles(self) -> "MissionContent":
        image_by_role = {asset.asset_role: asset.id for asset in self.assets if asset.asset_type == AssetType.IMAGE}
        audio_by_role = {asset.asset_role: asset.id for asset in self.assets if asset.asset_type == AssetType.AUDIO}
        for stage in self.stages:
            role = _asset_role_for_step(stage.step)
            stage.template_json.setdefault("imageAssetId", image_by_role.get(role))
            stage.template_json.setdefault("audioAssetId", audio_by_role.get(role))
            stage.template_json.setdefault(
                "assetBundle",
                {
                    "imageAssetId": image_by_role.get(role),
                    "audioAssetId": audio_by_role.get(role),
                },
            )
        return self

    @field_validator("stages")
    @classmethod
    def validate_four_stages(cls, stages: list[ContentStage]) -> list[ContentStage]:
        if sorted(stage.step for stage in stages) != [1, 2, 3, 4]:
            raise ValueError("MissionContent는 정확히 1~4단계를 가져야 합니다.")
        return stages

    @field_validator("assets")
    @classmethod
    def validate_required_assets(cls, assets: list[ContentAsset]) -> list[ContentAsset]:
        image_roles = {asset.asset_role for asset in assets if asset.asset_type == AssetType.IMAGE}
        missing_images = REQUIRED_ASSET_ROLES - image_roles
        if missing_images:
            missing_labels = ", ".join(sorted(role.value for role in missing_images))
            raise ValueError(f"필수 이미지 asset role이 없습니다: {missing_labels}")
        audio_roles = {asset.asset_role for asset in assets if asset.asset_type == AssetType.AUDIO}
        missing_audio = REQUIRED_ASSET_ROLES - audio_roles
        if missing_audio:
            missing_audio_labels = ", ".join(sorted(role.value for role in missing_audio))
            raise ValueError(f"필수 오디오 asset role이 없습니다: {missing_audio_labels}")
        return assets


def _asset_role_for_step(step: int) -> AssetRole:
    return {
        1: AssetRole.STAGE_1,
        2: AssetRole.STAGE_2,
        3: AssetRole.STAGE_3,
        4: AssetRole.STAGE_4_REALTIME,
    }[step]


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


class OrchestratorRunRequest(BaseModel):
    student_id: str = Field(alias="studentId")
    case_id: str = Field(alias="caseId")
    requested_goal: str | None = Field(default=None, alias="requestedGoal")
    content_type: Literal[StudentType.LIFE_SUPPORT, StudentType.LEARNING_FOCUS] | None = Field(default=None, alias="contentType")

    model_config = ConfigDict(populate_by_name=True)


class ContentGenerationRequest(BaseModel):
    orchestrator_run_id: str = Field(alias="orchestratorRunId")
    student_id: str = Field(alias="studentId")
    case_id: str = Field(alias="caseId")

    model_config = ConfigDict(populate_by_name=True)


class ContentApprovalRequest(BaseModel):
    approved_stage_ids: list[str] = Field(alias="approvedStageIds")
    approved_asset_ids: list[str] = Field(alias="approvedAssetIds")
    review_note: str | None = Field(default=None, alias="reviewNote")

    model_config = ConfigDict(populate_by_name=True)


class ContentRejectRequest(BaseModel):
    reason: str
    requested_changes: list[str] = Field(default_factory=list, alias="requestedChanges")

    model_config = ConfigDict(populate_by_name=True)


class StudentActivityEventRequest(BaseModel):
    attempt_id: str | None = Field(default=None, alias="attemptId")
    stage_id: str | None = Field(default=None, alias="stageId")
    event_type: str = Field(alias="eventType")
    payload_json: dict[str, Any] = Field(default_factory=dict, alias="payloadJson")

    model_config = ConfigDict(populate_by_name=True)


class RealtimeSessionEventRequest(BaseModel):
    event_type: str = Field(alias="eventType")
    payload_json: dict[str, Any] = Field(default_factory=dict, alias="payloadJson")

    model_config = ConfigDict(populate_by_name=True)


class RealtimeSessionCompleteRequest(BaseModel):
    turn_count: int = Field(alias="turnCount", ge=0)
    duration_sec: int = Field(alias="durationSec", ge=0)
    rubric_result: dict[str, Any] = Field(default_factory=dict, alias="rubricResult")
    transcript_summary: str | None = Field(default=None, alias="transcriptSummary")

    model_config = ConfigDict(populate_by_name=True)


class PublicDataSyncRequest(BaseModel):
    region_code: str | None = Field(default=None, alias="regionCode")
    office_code: str = Field(default="R10", alias="officeCode")
    school_code: str | None = Field(default=None, alias="schoolCode")
    from_date: str | None = Field(default=None, alias="fromDate")
    to_date: str | None = Field(default=None, alias="toDate")
    timetable_date: str | None = Field(default=None, alias="timetableDate")
    grade: str | None = None
    class_name: str | None = Field(default=None, alias="className")

    model_config = ConfigDict(populate_by_name=True)
