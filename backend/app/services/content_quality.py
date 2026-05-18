from __future__ import annotations

from collections import Counter
from typing import Any

from app.domain.enums import AssetRole, AssetType, MissionStatus, StageRole, StudentType, TemplateType
from app.domain.schemas import MissionContent

REQUIRED_ASSET_ROLES = [
    AssetRole.HERO,
    AssetRole.STAGE_1,
    AssetRole.STAGE_2,
    AssetRole.STAGE_3,
    AssetRole.STAGE_4_REALTIME,
]

FLOW_RULES: dict[str, dict[int, tuple[str, set[str]]]] = {
    StudentType.LEARNING_FOCUS.value: {
        1: (StageRole.CONCEPT_INTRO.value, {TemplateType.CONCEPT_INTRO.value}),
        2: (
            StageRole.BASIC_PROBLEM.value,
            {
                TemplateType.CARD_MATCH.value,
                TemplateType.SEQUENCE_ORDERING.value,
                TemplateType.BLANK_FILL.value,
                TemplateType.SCENE_QUESTION.value,
                TemplateType.CLUE_QUESTION.value,
            },
        ),
        3: (
            StageRole.APPLIED_PROBLEM.value,
            {
                TemplateType.CARD_MATCH.value,
                TemplateType.SEQUENCE_ORDERING.value,
                TemplateType.BLANK_FILL.value,
                TemplateType.APPLIED_QUESTION.value,
                TemplateType.MINI_SIMULATION.value,
                TemplateType.EXPLANATION_CHOICE.value,
                TemplateType.WRONG_EXPLANATION_FIX.value,
            },
        ),
        4: (StageRole.REALTIME_PRACTICE.value, {TemplateType.REALTIME_TEACH_BACK.value}),
    },
    StudentType.LIFE_SUPPORT.value: {
        1: (StageRole.SCENARIO_INTRO.value, {TemplateType.SCENARIO_INTRO.value}),
        2: (
            StageRole.CLUE_IDENTIFICATION.value,
            {
                TemplateType.SCENE_OBSERVATION.value,
                TemplateType.HIGHLIGHT_CLUE.value,
                TemplateType.CARD_MATCH.value,
            },
        ),
        3: (
            StageRole.ACTION_SELECTION.value,
            {
                TemplateType.CARD_MATCH.value,
                TemplateType.SEQUENCE_ORDERING.value,
                TemplateType.ACTION_CHOICE.value,
                TemplateType.DECISION_CARD.value,
            },
        ),
        4: (StageRole.REALTIME_PRACTICE.value, {TemplateType.REALTIME_ROLEPLAY.value}),
    },
}

STAGE_TITLE_RULES: dict[str, dict[int, str]] = {
    StudentType.LEARNING_FOCUS.value: {
        1: "개념 열기",
        2: "문제 1",
        3: "문제 2",
        4: "설명해보기",
    },
    StudentType.LIFE_SUPPORT.value: {
        1: "상황 만나기",
        2: "단서 찾기",
        3: "행동 고르기",
        4: "한 번 해보기",
    },
}

RAW_ENGLISH_TERMS = (
    "teach-back",
    "teach_back",
    "teach back",
    "realtime",
    "real-time",
    "roleplay",
    "role-play",
    "stage_",
    "template",
)

STIGMATIZING_TERMS = (
    "경계선",
    "저능",
    "지능이 낮",
    "장애",
    "낙오",
    "문제아",
    "못하는 학생",
    "실패한 학생",
)

STRUCTURED_INTERACTION_TEMPLATES = {
    TemplateType.CARD_MATCH.value,
    TemplateType.SEQUENCE_ORDERING.value,
    TemplateType.BLANK_FILL.value,
}

STUDENT_INSTRUCTION_MAX_LENGTH = 45
QUESTION_MAX_LENGTH = 80
INTRO_STORY_MAX_LENGTH = 90
INTRO_MISSION_MAX_LENGTH = 60
SOURCE_TEXT_MAX_LINES = 2
SOURCE_TEXT_LINE_MAX_LENGTH = 45
SCENE_TEXT_LINE_MAX_LENGTH = 70
OPTION_TEXT_MAX_LENGTH = 26
SENTENCE_TEXT_MAX_LENGTH = 80
FEEDBACK_TEXT_MAX_LENGTH = 70


class ContentQualityError(ValueError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        preview = "; ".join(issues[:6])
        if len(issues) > 6:
            preview = f"{preview}; 외 {len(issues) - 6}건"
        super().__init__(preview)


def validate_orchestrator_plan_quality(
    plan: dict[str, Any],
    *,
    student_id: str,
    case_id: str,
    content_type: str,
    case_file: dict[str, Any] | None = None,
) -> None:
    issues: list[str] = []
    _expect_equal(plan.get("studentId"), student_id, "orchestrator.studentId", issues)
    _expect_equal(plan.get("caseId"), case_id, "orchestrator.caseId", issues)
    _expect_equal(plan.get("contentType"), content_type, "orchestrator.contentType", issues)

    # 오케스트레이터 검수는 다음 단계 생성에 필요한 구조 계약만 차단한다.
    # 설명 문구의 길이/한국어 여부/비어 있음 같은 품질 판단은 프롬프트와 교사 검토로 넘긴다.
    _validate_stage_plan(plan.get("stagePlan"), content_type, issues)
    _validate_intent_roles(plan.get("imagePackageIntent"), "orchestrator.imagePackageIntent", issues)
    _validate_stage_visual_specs(plan.get("stageVisualSpecs"), "orchestrator.stageVisualSpecs", issues)
    _validate_intent_roles(plan.get("ttsNarrationIntent"), "orchestrator.ttsNarrationIntent", issues)

    if issues:
        raise ContentQualityError(issues)


def validate_mission_content_quality(
    mission: MissionContent,
    *,
    case_file: dict[str, Any],
    orchestrator_plan: dict[str, Any] | None = None,
) -> None:
    issues: list[str] = []
    profile = case_file.get("profile") if isinstance(case_file.get("profile"), dict) else {}
    profile_json = profile.get("profileJson") if isinstance(profile.get("profileJson"), dict) else {}
    expected_content_type = _as_value(profile.get("studentType") or mission.content_type)
    reading_load = str(profile_json.get("readingLoad") or "default")
    choice_limit = _positive_int(profile_json.get("choiceCountLimit"))

    _expect_equal(mission.student_id, profile.get("id"), "mission.studentId", issues)
    _expect_equal(_as_value(mission.content_type), expected_content_type, "mission.contentType", issues)
    if orchestrator_plan:
        _expect_equal(_as_value(mission.content_type), _as_value(orchestrator_plan.get("contentType")), "mission.contentType/orchestrator", issues)
        _expect_equal(mission.student_id, orchestrator_plan.get("studentId"), "mission.studentId/orchestrator", issues)
        _expect_equal(mission.case_id, orchestrator_plan.get("caseId"), "mission.caseId/orchestrator", issues)

    if mission.status != MissionStatus.TEACHER_REVIEW:
        issues.append("mission.status는 teacher_review여야 합니다.")
    if mission.approved_by_user_id or mission.approved_at or mission.published_at:
        issues.append("생성 직후 콘텐츠에는 승인/배포 필드가 없어야 합니다.")

    _validate_mission_stage_flow(mission, expected_content_type, issues)
    _validate_mission_template_variety(mission, issues, reading_load=reading_load, choice_limit=choice_limit)
    _validate_mission_template_interactions(mission, expected_content_type, issues)
    _validate_asset_package(mission, issues)
    _validate_stage_asset_links(mission, issues)
    # 생성 실패를 막는 품질검수는 렌더링/저장 계약 위주로 제한한다.
    # 문장 길이, 문제 뉘앙스, 이미지 프롬프트 표현 같은 내용 품질은
    # 프롬프트와 교사 검토에서 다루고, 여기서 콘텐츠 생성을 차단하지 않는다.
    _validate_mission_visual_brief_contract(mission, orchestrator_plan, issues)

    if issues:
        raise ContentQualityError(issues)


def collect_mission_template_text_quality_issues(mission: MissionContent) -> list[str]:
    issues: list[str] = []
    _validate_mission_template_text_lengths(mission, issues)
    return issues


def _validate_stage_plan(stage_plan: Any, content_type: str, issues: list[str]) -> None:
    if not isinstance(stage_plan, list):
        issues.append("orchestrator.stagePlan은 1~4단계 list여야 합니다.")
        return
    if sorted(item.get("step") for item in stage_plan if isinstance(item, dict)) != [1, 2, 3, 4]:
        issues.append("orchestrator.stagePlan은 정확히 1~4단계를 가져야 합니다.")
        return

    rules = FLOW_RULES.get(content_type)
    if rules is None:
        issues.append(f"지원하지 않는 contentType입니다: {content_type}")
        return

    for item in stage_plan:
        if not isinstance(item, dict):
            issues.append("orchestrator.stagePlan 항목은 object여야 합니다.")
            continue
        step = item.get("step")
        if step not in rules:
            continue
        expected_role, allowed_templates = rules[step]
        _expect_equal(item.get("stageRole"), expected_role, f"orchestrator.stagePlan[{step}].stageRole", issues)
        template_type = item.get("templateType")
        if template_type not in allowed_templates:
            issues.append(f"orchestrator.stagePlan[{step}].templateType이 허용 범위를 벗어났습니다: {template_type}")
        expected_title = STAGE_TITLE_RULES.get(content_type, {}).get(step)
        if expected_title and item.get("studentTitle") != expected_title:
            issues.append(f"orchestrator.stagePlan[{step}].studentTitle은 '{expected_title}'이어야 합니다.")


def _validate_stage_plan_template_variety(stage_plan: Any, issues: list[str], *, reading_load: str = "default", choice_limit: int | None = None) -> None:
    if not isinstance(stage_plan, list):
        return
    if _allows_choice_first_flow(reading_load, choice_limit):
        return

    stage_2_3_templates = [
        item.get("templateType")
        for item in stage_plan
        if isinstance(item, dict) and item.get("step") in {2, 3}
    ]
    if len(stage_2_3_templates) != 2:
        return

    if not any(template in STRUCTURED_INTERACTION_TEMPLATES for template in stage_2_3_templates):
        issues.append("orchestrator.stagePlan 2~3단계 중 최소 1개는 card_match, sequence_ordering, blank_fill 중 하나여야 합니다.")


def _validate_mission_stage_flow(mission: MissionContent, content_type: str, issues: list[str]) -> None:
    rules = FLOW_RULES.get(content_type)
    if rules is None:
        issues.append(f"지원하지 않는 contentType입니다: {content_type}")
        return

    stage_ids = [stage.id for stage in mission.stages]
    if len(stage_ids) != len(set(stage_ids)):
        issues.append("stage.id는 중복될 수 없습니다.")

    for stage in mission.stages:
        if stage.mission_content_id != mission.id:
            issues.append(f"{stage.id}.missionContentId가 콘텐츠 id와 다릅니다.")
        if stage.sort_order != stage.step:
            issues.append(f"{stage.id}.sortOrder는 step과 같아야 합니다.")
        expected_role, allowed_templates = rules[stage.step]
        expected_title = STAGE_TITLE_RULES.get(content_type, {}).get(stage.step)
        if expected_title and stage.student_title != expected_title:
            issues.append(f"{stage.id}.studentTitle은 '{expected_title}'이어야 합니다.")
        if _as_value(stage.stage_role) != expected_role:
            issues.append(f"{stage.id}.stageRole이 {content_type} 흐름과 맞지 않습니다.")
        if _as_value(stage.template_type) not in allowed_templates:
            issues.append(f"{stage.id}.templateType이 {content_type} {stage.step}단계 허용 범위를 벗어났습니다.")
        if stage.step == 4 and stage.realtime_spec:
            if stage.realtime_spec.stage_id != stage.id:
                issues.append(f"{stage.id}.realtimeSpec.stageId가 stage.id와 다릅니다.")
            if _as_value(stage.realtime_spec.template_type) != _as_value(stage.template_type):
                issues.append(f"{stage.id}.realtimeSpec.templateType이 stage.templateType과 다릅니다.")
            if stage.realtime_spec.max_turns > 8:
                issues.append(f"{stage.id}.realtimeSpec.maxTurns는 데모 품질 기준상 8 이하로 제한합니다.")
            if stage.realtime_spec.max_duration_sec > 180:
                issues.append(f"{stage.id}.realtimeSpec.maxDurationSec는 데모 품질 기준상 180초 이하로 제한합니다.")


def _validate_mission_template_variety(mission: MissionContent, issues: list[str], *, reading_load: str = "default", choice_limit: int | None = None) -> None:
    if _allows_choice_first_flow(reading_load, choice_limit):
        return

    stage_2_3_templates = [
        _as_value(stage.template_type)
        for stage in mission.stages
        if stage.step in {2, 3}
    ]
    if len(stage_2_3_templates) != 2:
        return

    if not any(template in STRUCTURED_INTERACTION_TEMPLATES for template in stage_2_3_templates):
        issues.append("mission.stages 2~3단계 중 최소 1개는 card_match, sequence_ordering, blank_fill 중 하나여야 합니다.")


def _validate_mission_template_interactions(mission: MissionContent, content_type: str, issues: list[str]) -> None:
    for stage in mission.stages:
        template_type = _as_value(stage.template_type)
        template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
        if content_type == StudentType.LIFE_SUPPORT.value and stage.step == 3 and template_type == TemplateType.SEQUENCE_ORDERING.value:
            cards = template_json.get("cards")
            answer_order = template_json.get("answerOrder")
            card_count = len(cards) if isinstance(cards, list) else 0
            answer_count = len(answer_order) if isinstance(answer_order, list) else 0
            if card_count != 3 or answer_count != 3:
                issues.append(f"{stage.id}.templateJson은 life_support 3단계 sequence_ordering에서 cards와 answerOrder를 각각 3개로 구성해야 합니다.")


def _validate_mission_template_text_lengths(mission: MissionContent, issues: list[str]) -> None:
    for stage in mission.stages:
        template_json = stage.template_json if isinstance(stage.template_json, dict) else {}
        _validate_short_text(stage.student_instruction, f"{stage.id}.studentInstruction", STUDENT_INSTRUCTION_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("storyText"), f"{stage.id}.templateJson.storyText", INTRO_STORY_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("missionText"), f"{stage.id}.templateJson.missionText", INTRO_MISSION_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("question"), f"{stage.id}.templateJson.question", QUESTION_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("sentence"), f"{stage.id}.templateJson.sentence", SENTENCE_TEXT_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("wrongLine"), f"{stage.id}.templateJson.wrongLine", SENTENCE_TEXT_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("fixedLine"), f"{stage.id}.templateJson.fixedLine", SENTENCE_TEXT_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("correctFeedback"), f"{stage.id}.templateJson.correctFeedback", FEEDBACK_TEXT_MAX_LENGTH, issues)
        _validate_short_text(template_json.get("wrongFeedback"), f"{stage.id}.templateJson.wrongFeedback", FEEDBACK_TEXT_MAX_LENGTH, issues)
        _validate_limited_text_list(
            template_json.get("sourceTextLines"),
            f"{stage.id}.templateJson.sourceTextLines",
            max_items=SOURCE_TEXT_MAX_LINES,
            max_length=SOURCE_TEXT_LINE_MAX_LENGTH,
            issues=issues,
        )
        _validate_limited_text_list(
            template_json.get("sceneTextLines"),
            f"{stage.id}.templateJson.sceneTextLines",
            max_items=SOURCE_TEXT_MAX_LINES,
            max_length=SCENE_TEXT_LINE_MAX_LENGTH,
            issues=issues,
        )
        _validate_choice_like_texts(template_json.get("choices"), f"{stage.id}.templateJson.choices", issues)
        _validate_choice_like_texts(template_json.get("leftCards"), f"{stage.id}.templateJson.leftCards", issues)
        _validate_choice_like_texts(template_json.get("rightCards"), f"{stage.id}.templateJson.rightCards", issues)
        _validate_choice_like_texts(template_json.get("cards"), f"{stage.id}.templateJson.cards", issues)
        _validate_tile_texts(template_json.get("tiles"), f"{stage.id}.templateJson.tiles", issues)


def _validate_short_text(value: Any, path: str, max_length: int, issues: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        return
    if _compact_length(value) > max_length:
        issues.append(f"{path}는 {max_length}자 이하로 짧게 작성해야 합니다.")


def _validate_limited_text_list(
    value: Any,
    path: str,
    *,
    max_items: int,
    max_length: int,
    issues: list[str],
) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        return
    if len(value) > max_items:
        issues.append(f"{path}는 최대 {max_items}줄까지만 사용할 수 있습니다.")
    for index, item in enumerate(value):
        _validate_short_text(item, f"{path}[{index}]", max_length, issues)


def _validate_choice_like_texts(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        if isinstance(item, str):
            _validate_short_text(item, f"{path}[{index}]", OPTION_TEXT_MAX_LENGTH, issues)
            continue
        if not isinstance(item, dict):
            continue
        for key in ("text", "label", "title", "caption"):
            _validate_short_text(item.get(key), f"{path}[{index}].{key}", OPTION_TEXT_MAX_LENGTH, issues)


def _validate_tile_texts(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        _validate_short_text(item, f"{path}[{index}]", OPTION_TEXT_MAX_LENGTH, issues)


def _compact_length(value: str) -> int:
    return len(" ".join(value.strip().split()))


def _validate_asset_package(mission: MissionContent, issues: list[str]) -> None:
    asset_ids = [asset.id for asset in mission.assets]
    if len(asset_ids) != len(set(asset_ids)):
        issues.append("asset.id는 중복될 수 없습니다.")
    if len(mission.assets) != 10:
        issues.append("생성 콘텐츠는 이미지 5개와 오디오 5개, 총 10개 asset만 가져야 합니다.")

    for asset_type in (AssetType.IMAGE, AssetType.AUDIO):
        counts = Counter(asset.asset_role for asset in mission.assets if asset.asset_type == asset_type)
        for role in REQUIRED_ASSET_ROLES:
            if counts[role] != 1:
                issues.append(f"{asset_type.value} asset role {role.value}는 정확히 1개여야 합니다.")

    stage_by_step = {stage.step: stage for stage in mission.stages}
    for asset in mission.assets:
        if asset.mission_content_id != mission.id:
            issues.append(f"{asset.id}.missionContentId가 콘텐츠 id와 다릅니다.")
        expected_stage_id = _stage_id_for_asset_role(asset.asset_role, stage_by_step)
        if asset.stage_id != expected_stage_id:
            issues.append(f"{asset.id}.stageId가 assetRole과 연결된 stageId와 다릅니다.")
        if asset.asset_type == AssetType.AUDIO and not asset.source_text:
            issues.append(f"{asset.id}.sourceText가 필요합니다.")
        if asset.asset_type == AssetType.IMAGE:
            prompt = asset.prompt_json.get("prompt") if isinstance(asset.prompt_json, dict) else None
            if not isinstance(prompt, str) or len(prompt.strip()) < 40:
                issues.append(f"{asset.id}.promptJson.prompt는 이미지 생성을 위한 충분한 장면 설명이어야 합니다.")


def _validate_stage_asset_links(mission: MissionContent, issues: list[str]) -> None:
    image_by_role = {asset.asset_role: asset for asset in mission.assets if asset.asset_type == AssetType.IMAGE}
    audio_by_role = {asset.asset_role: asset for asset in mission.assets if asset.asset_type == AssetType.AUDIO}
    for stage in mission.stages:
        role = _asset_role_for_step(stage.step)
        image_asset = image_by_role.get(role)
        audio_asset = audio_by_role.get(role)
        template_json = stage.template_json
        if image_asset and template_json.get("imageAssetId") != image_asset.id:
            issues.append(f"{stage.id}.templateJson.imageAssetId가 {role.value} 이미지와 다릅니다.")
        if audio_asset and template_json.get("audioAssetId") != audio_asset.id:
            issues.append(f"{stage.id}.templateJson.audioAssetId가 {role.value} 오디오와 다릅니다.")
        bundle = template_json.get("assetBundle")
        if isinstance(bundle, dict):
            if image_asset and bundle.get("imageAssetId") != image_asset.id:
                issues.append(f"{stage.id}.templateJson.assetBundle.imageAssetId가 {role.value} 이미지와 다릅니다.")
            if audio_asset and bundle.get("audioAssetId") != audio_asset.id:
                issues.append(f"{stage.id}.templateJson.assetBundle.audioAssetId가 {role.value} 오디오와 다릅니다.")
        if stage.realtime_spec and image_asset and stage.realtime_spec.image_asset_id != image_asset.id:
            issues.append(f"{stage.id}.realtimeSpec.imageAssetId가 stage_4_realtime 이미지와 다릅니다.")


def _validate_intent_roles(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, list):
        issues.append(f"{path}는 asset role list여야 합니다.")
        return
    roles = [item.get("assetRole") for item in value if isinstance(item, dict)]
    if sorted(roles) != sorted(role.value for role in REQUIRED_ASSET_ROLES):
        issues.append(f"{path}는 hero, stage_1, stage_2, stage_3, stage_4_realtime을 각각 1개씩 가져야 합니다.")


def _validate_stage_visual_specs(value: Any, path: str, issues: list[str]) -> None:
    if value is None:
        issues.append(f"{path}가 필요합니다. 오케스트레이터는 단계별 이미지 제작 지시서를 반환해야 합니다.")
        return
    if not isinstance(value, list):
        issues.append(f"{path}는 asset role list여야 합니다.")
        return
    roles = [item.get("assetRole") for item in value if isinstance(item, dict)]
    if sorted(roles) != sorted(role.value for role in REQUIRED_ASSET_ROLES):
        issues.append(f"{path}는 hero, stage_1, stage_2, stage_3, stage_4_realtime을 각각 1개씩 가져야 합니다.")
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            issues.append(f"{path}[{index}]는 object여야 합니다.")
            continue
        for key in ("mustShow", "allowedSceneText", "doNotRenderText"):
            if not isinstance(item.get(key), list):
                issues.append(f"{path}[{index}].{key}는 list여야 합니다.")
        if item.get("allowedSceneText") != []:
            issues.append(f"{path}[{index}].allowedSceneText는 빈 배열이어야 합니다.")
        if item.get("evidenceLocation") != "problem_ui_only":
            issues.append(f"{path}[{index}].evidenceLocation은 problem_ui_only여야 합니다.")


def _validate_scenario_spine(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, dict):
        issues.append(f"{path}은 object여야 합니다.")
        return
    for key in (
        "whyThisMatters",
        "studentLikelyImpulseOrMisconception",
        "stage2FirstSuccess",
        "stage3Transfer",
        "stage4Reuse",
    ):
        _validate_korean_text(value.get(key), f"{path}.{key}", issues)


def _validate_mission_visual_brief_contract(
    mission: MissionContent,
    orchestrator_plan: dict[str, Any] | None,
    issues: list[str],
) -> None:
    if not orchestrator_plan or not isinstance(orchestrator_plan.get("stageVisualSpecs"), list):
        return
    brief_json = mission.brief_json if isinstance(mission.brief_json, dict) else {}
    if not isinstance(brief_json.get("scenarioSpine"), dict):
        issues.append("mission.briefJson.scenarioSpine은 orchestratorPlan에서 보존되어야 합니다.")
    stage_visual_specs = brief_json.get("stageVisualSpecs")
    if not isinstance(stage_visual_specs, list):
        issues.append("mission.briefJson.stageVisualSpecs는 orchestratorPlan에서 보존되어야 합니다.")
        return
    roles = [item.get("assetRole") for item in stage_visual_specs if isinstance(item, dict)]
    if sorted(roles) != sorted(role.value for role in REQUIRED_ASSET_ROLES):
        issues.append("mission.briefJson.stageVisualSpecs는 5개 이미지 역할별 제작 지시서를 모두 포함해야 합니다.")


def _validate_text_list(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, list) or not value:
        issues.append(f"{path}는 비어 있지 않은 list여야 합니다.")
        return
    for index, item in enumerate(value):
        _validate_korean_text(item, f"{path}[{index}]", issues)


def _validate_korean_text(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{path}는 비어 있지 않은 한국어 문구여야 합니다.")
        return
    text = value.strip()
    if _requires_hangul(text) and not _contains_hangul(text):
        issues.append(f"{path}는 한국어 문구여야 합니다.")
    lowered = text.lower()
    for term in RAW_ENGLISH_TERMS:
        if term in lowered:
            issues.append(f"{path}에 내부 영문 용어가 노출되었습니다: {term}")
            break
    for term in STIGMATIZING_TERMS:
        if term in text:
            issues.append(f"{path}에 학생에게 부적절한 낙인성 표현이 포함되었습니다: {term}")
            break


def _requires_hangul(text: str) -> bool:
    compact = text.strip()
    if not compact:
        return True
    if _contains_hangul(compact):
        return False
    if _is_numeric_symbol_text(compact):
        return False
    return _contains_ascii_word(compact, min_length=2) or len(compact) > 4


def _contains_hangul(text: str) -> bool:
    return any("가" <= character <= "힣" for character in text)


def _contains_ascii_word(text: str, *, min_length: int) -> bool:
    run_length = 0
    for character in text:
        if ("A" <= character <= "Z") or ("a" <= character <= "z"):
            run_length += 1
            if run_length >= min_length:
                return True
        else:
            run_length = 0
    return False


def _is_numeric_symbol_text(text: str) -> bool:
    allowed = set("0123456789 \t\r\n./%()+-")
    return all(character in allowed for character in text)


def _asset_role_for_step(step: int) -> AssetRole:
    return {
        1: AssetRole.STAGE_1,
        2: AssetRole.STAGE_2,
        3: AssetRole.STAGE_3,
        4: AssetRole.STAGE_4_REALTIME,
    }[step]


def _stage_id_for_asset_role(asset_role: AssetRole, stage_by_step: dict[int, Any]) -> str | None:
    if asset_role == AssetRole.HERO:
        return None
    return {
        AssetRole.STAGE_1: stage_by_step.get(1),
        AssetRole.STAGE_2: stage_by_step.get(2),
        AssetRole.STAGE_3: stage_by_step.get(3),
        AssetRole.STAGE_4_REALTIME: stage_by_step.get(4),
    }[asset_role].id


def _expect_equal(actual: Any, expected: Any, path: str, issues: list[str]) -> None:
    if expected is None:
        return
    if _as_value(actual) != _as_value(expected):
        issues.append(f"{path} 값이 요청/맥락과 다릅니다.")


def _nested(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _as_value(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _profile_json_from_case_file(case_file: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(case_file, dict):
        return {}
    profile = case_file.get("profile")
    if not isinstance(profile, dict):
        return {}
    profile_json = profile.get("profileJson")
    return profile_json if isinstance(profile_json, dict) else {}


def _allows_choice_first_flow(reading_load: str, choice_limit: int | None) -> bool:
    return reading_load == "very_low" or (choice_limit is not None and choice_limit <= 2)
