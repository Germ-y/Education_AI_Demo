from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.domain.enums import AssetRole, AssetType, MissionStatus, StageRole, StudentType, TemplateType
from app.domain.schemas import MissionContent

HANGUL_RE = re.compile(r"[가-힣]")
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")

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
                TemplateType.IMAGE_QUIZ.value,
                TemplateType.CARD_MATCH.value,
                TemplateType.SEQUENCE_ORDERING.value,
                TemplateType.BLANK_FILL.value,
                TemplateType.SCENE_QUESTION.value,
                TemplateType.CLUE_QUESTION.value,
                TemplateType.PARTITION_PICKER.value,
            },
        ),
        3: (
            StageRole.APPLIED_PROBLEM.value,
            {
                TemplateType.IMAGE_QUIZ.value,
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
                TemplateType.IMAGE_QUIZ.value,
                TemplateType.CARD_MATCH.value,
            },
        ),
        3: (
            StageRole.ACTION_SELECTION.value,
            {
                TemplateType.IMAGE_QUIZ.value,
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

VISIBLE_TEMPLATE_TEXT_KEYS = {
    "question",
    "storyText",
    "missionText",
    "instruction",
    "correctFeedback",
    "wrongFeedback",
    "text",
    "label",
    "sentence",
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

PROPOSAL_PHRASES = (
    "수업이 좋겠어요",
    "콘텐츠가 좋겠어요",
    "하면 좋겠어요",
)

TEXT_LIMITS = {
    "very_low": {"instruction": 60, "question": 52, "choice": 24, "audio": 95},
    "low": {"instruction": 90, "question": 80, "choice": 32, "audio": 125},
    "default": {"instruction": 120, "question": 100, "choice": 42, "audio": 150},
}

STRUCTURED_INTERACTION_TEMPLATES = {
    TemplateType.CARD_MATCH.value,
    TemplateType.SEQUENCE_ORDERING.value,
    TemplateType.BLANK_FILL.value,
}


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
) -> None:
    issues: list[str] = []

    _expect_equal(plan.get("studentId"), student_id, "orchestrator.studentId", issues)
    _expect_equal(plan.get("caseId"), case_id, "orchestrator.caseId", issues)
    _expect_equal(plan.get("contentType"), content_type, "orchestrator.contentType", issues)

    _validate_korean_text(plan.get("sessionGoal"), "orchestrator.sessionGoal", issues)
    _validate_korean_text(plan.get("targetSkill"), "orchestrator.targetSkill", issues)
    _validate_korean_text(_nested(plan, "difficultyPolicy", "reason"), "orchestrator.difficultyPolicy.reason", issues)
    _validate_text_list(plan.get("teacherReviewFocus"), "orchestrator.teacherReviewFocus", issues)
    _validate_stage_plan(plan.get("stagePlan"), content_type, issues)
    _validate_stage_plan_template_variety(plan.get("stagePlan"), issues)
    _validate_intent_roles(plan.get("imagePackageIntent"), "orchestrator.imagePackageIntent", issues)
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
    _validate_mission_template_variety(mission, issues)
    _validate_asset_package(mission, issues)
    _validate_stage_asset_links(mission, issues)
    _validate_visible_content_text(mission, reading_load, choice_limit, issues)
    _validate_image_prompt_policy(mission, issues)

    if issues:
        raise ContentQualityError(issues)


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
        _validate_korean_text(item.get("studentTitle"), f"orchestrator.stagePlan[{step}].studentTitle", issues)
        expected_title = STAGE_TITLE_RULES.get(content_type, {}).get(step)
        if expected_title and item.get("studentTitle") != expected_title:
            issues.append(f"orchestrator.stagePlan[{step}].studentTitle은 '{expected_title}'이어야 합니다.")
        _validate_korean_text(item.get("purpose"), f"orchestrator.stagePlan[{step}].purpose", issues)


def _validate_stage_plan_template_variety(stage_plan: Any, issues: list[str]) -> None:
    if not isinstance(stage_plan, list):
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


def _validate_mission_template_variety(mission: MissionContent, issues: list[str]) -> None:
    stage_2_3_templates = [
        _as_value(stage.template_type)
        for stage in mission.stages
        if stage.step in {2, 3}
    ]
    if len(stage_2_3_templates) != 2:
        return

    if not any(template in STRUCTURED_INTERACTION_TEMPLATES for template in stage_2_3_templates):
        issues.append("mission.stages 2~3단계 중 최소 1개는 card_match, sequence_ordering, blank_fill 중 하나여야 합니다.")


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


def _validate_visible_content_text(
    mission: MissionContent,
    reading_load: str,
    choice_limit: int | None,
    issues: list[str],
) -> None:
    limits = TEXT_LIMITS.get(reading_load, TEXT_LIMITS["default"])
    _validate_korean_text(mission.title, "mission.title", issues)
    _validate_korean_text(mission.session_goal, "mission.sessionGoal", issues)
    if mission.teacher_review_summary:
        _validate_korean_text(mission.teacher_review_summary, "mission.teacherReviewSummary", issues)

    for stage in mission.stages:
        _validate_korean_text(stage.student_title, f"{stage.id}.studentTitle", issues)
        _validate_korean_text(stage.student_instruction, f"{stage.id}.studentInstruction", issues)
        if len(stage.student_instruction) > limits["instruction"]:
            issues.append(f"{stage.id}.studentInstruction이 학생 읽기 부담 기준보다 깁니다.")
        for path, text in _iter_template_visible_text(stage.template_json, stage.id):
            _validate_korean_text(text, path, issues)
            if path.endswith(".question") and len(text) > limits["question"]:
                issues.append(f"{path}이 학생 읽기 부담 기준보다 깁니다.")
            if path.endswith(".text") and len(text) > limits["choice"]:
                issues.append(f"{path} 선택지 문구가 학생 읽기 부담 기준보다 깁니다.")
        if choice_limit is not None:
            _validate_choice_limit(stage.template_json, stage.template_type.value, choice_limit, f"{stage.id}.templateJson", issues)
        if _has_student_proposal_phrase(stage.student_title) or _has_student_proposal_phrase(stage.student_instruction):
            issues.append(f"{stage.id} 학생 문구에 교사용 제안 말투가 섞였습니다.")

        if stage.realtime_spec:
            spec = stage.realtime_spec
            realtime_texts = {
                "practiceTitle": spec.practice_title,
                "situationText": spec.situation_text,
                "aiRole": spec.ai_role,
                "openingLine": spec.opening_line,
                "studentGoal": spec.student_goal,
                "allowedFeedback": spec.allowed_feedback,
                "forbidden": spec.forbidden,
                "postPracticeReflection": spec.post_practice_reflection,
                "rubric": [item.label for item in spec.rubric],
            }
            for path, text in _iter_named_visible_text(realtime_texts, f"{stage.id}.realtimeSpec"):
                _validate_korean_text(text, path, issues)
            if not (2 <= len(spec.post_practice_reflection) <= 4):
                issues.append(f"{stage.id}.realtimeSpec.postPracticeReflection은 2~4개 선택지여야 합니다.")

    for asset in mission.assets:
        if asset.asset_type != AssetType.AUDIO or not asset.source_text:
            continue
        _validate_korean_text(asset.source_text, f"{asset.id}.sourceText", issues)
        if len(asset.source_text) > limits["audio"]:
            issues.append(f"{asset.id}.sourceText가 학생 듣기 부담 기준보다 깁니다.")


def _validate_image_prompt_policy(mission: MissionContent, issues: list[str]) -> None:
    visible_texts = [
        text
        for stage in mission.stages
        for _, text in _iter_template_visible_text(stage.template_json, stage.id)
        if _meaningful_prompt_overlap_text(text)
    ]
    for asset in mission.assets:
        if asset.asset_type != AssetType.IMAGE:
            continue
        prompt_json = asset.prompt_json if isinstance(asset.prompt_json, dict) else {}
        prompt = prompt_json.get("prompt")
        if not isinstance(prompt, str):
            continue
        text_policy = str(prompt_json.get("textRenderingPolicy") or prompt_json.get("ocrPolicy") or "")
        if "scene_only" not in text_policy and "no_problem_text" not in text_policy:
            issues.append(f"{asset.id}.promptJson에는 이미지 안에 문제/선택지/정답을 넣지 않는 정책이 필요합니다.")
        for text in visible_texts:
            if text and text in prompt:
                issues.append(f"{asset.id}.promptJson.prompt에 UI 문구가 그대로 들어갔습니다: {text[:20]}")
                break


def _iter_template_visible_text(value: Any, prefix: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []

    def walk(current: Any, path: str, key: str | None = None) -> None:
        if isinstance(current, str):
            if key in VISIBLE_TEMPLATE_TEXT_KEYS:
                items.append((path, current))
            return
        if isinstance(current, list):
            for index, item in enumerate(current):
                walk(item, f"{path}[{index}]", key)
            return
        if isinstance(current, dict):
            for child_key, child_value in current.items():
                walk(child_value, f"{path}.{child_key}", child_key)

    walk(value, f"{prefix}.templateJson")
    return items


def _iter_named_visible_text(value: Any, prefix: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []

    def walk(current: Any, path: str) -> None:
        if isinstance(current, str):
            items.append((path, current))
            return
        if isinstance(current, list):
            for index, item in enumerate(current):
                walk(item, f"{path}[{index}]")
            return
        if isinstance(current, dict):
            for key, child_value in current.items():
                walk(child_value, f"{path}.{key}")

    walk(value, prefix)
    return items


def _validate_choice_limit(template_json: dict[str, Any], template_type: str, limit: int, path: str, issues: list[str]) -> None:
    if template_type == TemplateType.CARD_MATCH.value:
        _validate_array_limit(template_json, "leftCards", limit, path, issues)
        _validate_array_limit(template_json, "rightCards", limit, path, issues)
        matches = template_json.get("matches")
        if isinstance(matches, dict) and len(matches) > limit:
            issues.append(f"{path}.matches는 학생 선택지 제한 {limit}개를 넘을 수 없습니다.")
        return

    if template_type == TemplateType.IMAGE_QUIZ.value:
        _validate_array_limit(template_json, "choices", 3, path, issues)
        return

    if template_type == TemplateType.SEQUENCE_ORDERING.value:
        _validate_array_limit(template_json, "cards", 3, path, issues)
        return

    if template_type == TemplateType.BLANK_FILL.value:
        _validate_array_limit(template_json, "choices", 3, path, issues)
        _validate_array_limit(template_json, "tiles", 3, path, issues)
        return

    for key in ("choices", "tiles"):
        _validate_array_limit(template_json, key, max(limit, 3), path, issues)


def _validate_array_limit(template_json: dict[str, Any], key: str, limit: int, path: str, issues: list[str]) -> None:
    value = template_json.get(key)
    if isinstance(value, list) and len(value) > limit:
        issues.append(f"{path}.{key}는 학생 선택지 제한 {limit}개를 넘을 수 없습니다.")


def _validate_intent_roles(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, list):
        issues.append(f"{path}는 asset role list여야 합니다.")
        return
    roles = [item.get("assetRole") for item in value if isinstance(item, dict)]
    if sorted(roles) != sorted(role.value for role in REQUIRED_ASSET_ROLES):
        issues.append(f"{path}는 hero, stage_1, stage_2, stage_3, stage_4_realtime을 각각 1개씩 가져야 합니다.")


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
    if _requires_hangul(text) and not HANGUL_RE.search(text):
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
    if HANGUL_RE.search(compact):
        return False
    if re.fullmatch(r"[\d\s./%()+\-]+", compact):
        return False
    return bool(ASCII_WORD_RE.search(compact)) or len(compact) > 4


def _has_student_proposal_phrase(text: str) -> bool:
    return any(phrase in text for phrase in PROPOSAL_PHRASES)


def _meaningful_prompt_overlap_text(text: str) -> bool:
    stripped = text.strip()
    return len(stripped) >= 8 and bool(HANGUL_RE.search(stripped))


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
