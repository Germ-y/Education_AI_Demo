import logging
import time
from random import SystemRandom
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import ValidationError

from app.ai.openai_provider import OpenAiProvider
from app.ai.output_schemas import output_json_schema
from app.ai.prompt_registry import PROMPT_SPECS, load_prompt
from app.ai.provider_errors import AiProviderError
from app.api.deps import get_agent_run_repository, get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.domain.schemas import ContentGenerationRequest, MissionContent, OrchestratorRunRequest
from app.repositories.agent_run_repository import AgentRunRepository
from app.services.content_quality import ContentQualityError, validate_mission_content_quality, validate_orchestrator_plan_quality
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/ai", tags=["ai"])
logger = logging.getLogger(__name__)
_template_random = SystemRandom()

ORCHESTRATOR_STAGE_CONTRACTS: dict[str, dict[int, dict[str, Any]]] = {
    "learning_focus": {
        1: {
            "stageRole": "concept_intro",
            "studentTitle": "개념 열기",
            "defaultTemplate": "concept_intro",
            "allowedTemplates": {"concept_intro"},
        },
        2: {
            "stageRole": "basic_problem",
            "studentTitle": "문제 1",
            "defaultTemplate": "scene_question",
            "allowedTemplates": {
                "image_quiz",
                "card_match",
                "sequence_ordering",
                "blank_fill",
                "scene_question",
                "clue_question",
                "partition_picker",
            },
        },
        3: {
            "stageRole": "applied_problem",
            "studentTitle": "문제 2",
            "defaultTemplate": "applied_question",
            "allowedTemplates": {
                "image_quiz",
                "card_match",
                "sequence_ordering",
                "blank_fill",
                "applied_question",
                "mini_simulation",
                "explanation_choice",
                "wrong_explanation_fix",
            },
            "templateAliases": {
                "scene_question": "applied_question",
                "clue_question": "applied_question",
                "action_choice": "applied_question",
                "decision_card": "applied_question",
            },
        },
        4: {
            "stageRole": "realtime_practice",
            "studentTitle": "설명해보기",
            "defaultTemplate": "realtime_teach_back",
            "allowedTemplates": {"realtime_teach_back"},
            "templateAliases": {"realtime_roleplay": "realtime_teach_back"},
        },
    },
    "life_support": {
        1: {
            "stageRole": "scenario_intro",
            "studentTitle": "상황 만나기",
            "defaultTemplate": "scenario_intro",
            "allowedTemplates": {"scenario_intro"},
        },
        2: {
            "stageRole": "clue_identification",
            "studentTitle": "단서 찾기",
            "defaultTemplate": "highlight_clue",
            "allowedTemplates": {"scene_observation", "highlight_clue", "image_quiz", "card_match"},
            "templateAliases": {"scene_question": "highlight_clue", "clue_question": "highlight_clue"},
        },
        3: {
            "stageRole": "action_selection",
            "studentTitle": "행동 고르기",
            "defaultTemplate": "action_choice",
            "allowedTemplates": {"image_quiz", "card_match", "sequence_ordering", "action_choice", "decision_card"},
            "templateAliases": {
                "scene_question": "action_choice",
                "clue_question": "action_choice",
                "applied_question": "action_choice",
            },
        },
        4: {
            "stageRole": "realtime_practice",
            "studentTitle": "한 번 해보기",
            "defaultTemplate": "realtime_roleplay",
            "allowedTemplates": {"realtime_roleplay"},
            "templateAliases": {"realtime_teach_back": "realtime_roleplay"},
        },
    },
}


@router.post("/orchestrator-runs")
def create_orchestrator_run(
    payload: OrchestratorRunRequest,
    background_tasks: BackgroundTasks,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
) -> dict:
    case_file = demo_store.get_student_case_file(payload.student_id)
    if case_file is None or case_file["openCase"]["id"] != payload.case_id:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "학생 사례를 찾을 수 없습니다."})
    if principal.role == "teacher" and case_file["openCase"]["ownerTeacherId"] != principal.id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "담당 학생 사례만 생성할 수 있습니다."})

    settings = get_settings()
    spec = PROMPT_SPECS["orchestrator_plan"]
    context_brief = demo_store.get_student_context_brief(payload.student_id)
    if context_brief is None or context_brief.dirty:
        context_brief = (
            demo_store.refresh_student_context_brief(
                payload.student_id,
                teacher_id=principal.id if principal.role == "teacher" else None,
            )
            or context_brief
        )
        case_file = demo_store.get_student_case_file(payload.student_id) or case_file
    content_type = str(payload.content_type or case_file["profile"]["studentType"])
    template_randomization = _build_template_randomization(content_type, case_file=case_file)
    input_snapshot = {
        "teacherId": principal.id,
        "studentId": payload.student_id,
        "caseId": payload.case_id,
        "requestedGoal": payload.requested_goal,
        "contentType": payload.content_type,
        "templateRandomization": template_randomization,
        "studentContextBrief": context_brief.model_dump(by_alias=True) if context_brief else None,
        "generationContext": {
            "teacherRequestedGoal": payload.requested_goal,
            "contextBriefPriority": "use_context_brief_for_scaffolding_not_topic_override",
            "contextBriefDirty": context_brief.dirty if context_brief else True,
            "templateSelectionPolicy": "use_backend_randomized_stage_templates_exactly",
            "topicPolicy": (
                "requestedGoal is the source of truth for subject/topic. "
                "caseFile.openCase.currentGoal and contextBrief examples are support-pattern history only; "
                "do not reuse their concrete scenario unless requestedGoal explicitly asks for it."
            ),
        },
        "caseFile": case_file,
    }
    agent_run = agent_runs.create_running(
        agent_type="orchestrator",
        prompt_version=spec.version,
        output_schema_name=spec.output_schema_name,
        input_snapshot=input_snapshot,
        model=settings.openai_orchestrator_model,
    )
    logger.info(
        "ai.orchestrator.queued run_id=%s student_id=%s case_id=%s content_type=%s goal=%r",
        agent_run.id,
        payload.student_id,
        payload.case_id,
        payload.content_type,
        payload.requested_goal,
    )

    background_tasks.add_task(
        _run_orchestrator_agent,
        agent_run.id,
        settings,
        input_snapshot,
        payload.student_id,
        payload.case_id,
        content_type,
        agent_runs,
    )
    return ok({"agentRun": agent_run.model_dump(by_alias=True)})


@router.post("/content-generations")
def create_content_generation(
    payload: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
) -> dict:
    case_file = demo_store.get_student_case_file(payload.student_id)
    if case_file is None or case_file["openCase"]["id"] != payload.case_id:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "학생 사례를 찾을 수 없습니다."})
    if principal.role == "teacher" and case_file["openCase"]["ownerTeacherId"] != principal.id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "담당 학생 사례만 생성할 수 있습니다."})

    orchestrator_run = agent_runs.get(payload.orchestrator_run_id)
    if orchestrator_run is None:
        raise HTTPException(status_code=404, detail={"code": "ORCHESTRATOR_RUN_NOT_FOUND", "message": "오케스트레이터 실행 기록을 찾을 수 없습니다."})
    if orchestrator_run.status != "succeeded" or orchestrator_run.output_json is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ORCHESTRATOR_RUN_NOT_READY",
                "message": "성공한 오케스트레이터 실행만 콘텐츠 생성에 사용할 수 있습니다.",
                "details": {"reviewRequired": orchestrator_run.review_required, "errorCode": orchestrator_run.error_code},
            },
        )

    settings = get_settings()
    spec = PROMPT_SPECS["mission_content_package"]
    generation_plan = _build_generation_plan(orchestrator_run.output_json)
    input_snapshot = {
        "teacherId": principal.id,
        "studentId": payload.student_id,
        "caseId": payload.case_id,
        "orchestratorRunId": payload.orchestrator_run_id,
        "orchestratorPlan": orchestrator_run.output_json,
        "generationPlan": generation_plan,
        "caseFile": case_file,
    }
    agent_run = agent_runs.create_running(
        agent_type="content",
        prompt_version=spec.version,
        output_schema_name=spec.output_schema_name,
        input_snapshot=input_snapshot,
        model=settings.openai_content_model,
    )
    logger.info(
        "ai.content.queued run_id=%s student_id=%s case_id=%s orchestrator_run_id=%s",
        agent_run.id,
        payload.student_id,
        payload.case_id,
        payload.orchestrator_run_id,
    )

    background_tasks.add_task(
        _run_content_agent,
        agent_run.id,
        settings,
        input_snapshot,
        payload.student_id,
        payload.case_id,
        case_file,
        orchestrator_run.output_json,
        demo_store,
        agent_runs,
    )
    return ok({"agentRun": agent_run.model_dump(by_alias=True), "content": None})


@router.get("/agent-runs")
def list_agent_runs(
    student_id: str | None = None,
    case_id: str | None = None,
    status: str | None = None,
    _: SessionPrincipal = Depends(require_teacher),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
) -> dict:
    recent_runs = agent_runs.list_recent(limit=50)
    filtered_runs = []
    for agent_run in recent_runs:
        snapshot = agent_run.input_snapshot_json
        if student_id and snapshot.get("studentId") != student_id:
            continue
        if case_id and snapshot.get("caseId") != case_id:
            continue
        if status and agent_run.status != status:
            continue
        filtered_runs.append(agent_run.model_dump(by_alias=True))
    return ok(filtered_runs)


@router.get("/agent-runs/{agent_run_id}")
def get_agent_run(
    agent_run_id: str,
    _: SessionPrincipal = Depends(require_teacher),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
) -> dict:
    agent_run = agent_runs.get(agent_run_id)
    if agent_run is None:
        raise HTTPException(status_code=404, detail={"code": "AGENT_RUN_NOT_FOUND", "message": "AI 실행 기록을 찾을 수 없습니다."})
    return ok(agent_run.model_dump(by_alias=True))


def _run_orchestrator_agent(
    agent_run_id: str,
    settings,
    input_snapshot: dict,
    student_id: str,
    case_id: str,
    content_type: str,
    agent_runs: AgentRunRepository,
) -> None:
    started_at = time.perf_counter()
    logger.info(
        "ai.orchestrator.started run_id=%s student_id=%s case_id=%s content_type=%s",
        agent_run_id,
        student_id,
        case_id,
        content_type,
    )
    try:
        output_json, token_usage = OpenAiProvider(settings).create_json_response(
            model=settings.openai_orchestrator_model,
            instructions=load_prompt("orchestrator_plan"),
            input_snapshot=input_snapshot,
            output_schema_name=PROMPT_SPECS["orchestrator_plan"].output_schema_name,
            output_json_schema=output_json_schema(PROMPT_SPECS["orchestrator_plan"].output_schema_name),
            timeout_sec=settings.openai_orchestrator_timeout_sec,
            max_output_tokens=settings.openai_orchestrator_max_output_tokens,
        )
        output_json = _normalize_orchestrator_plan_candidate(
            output_json,
            content_type=content_type,
            template_randomization=input_snapshot.get("templateRandomization"),
        )
        validate_orchestrator_plan_quality(
            output_json,
            student_id=student_id,
            case_id=case_id,
            content_type=content_type,
            case_file=input_snapshot.get("caseFile") if isinstance(input_snapshot.get("caseFile"), dict) else None,
        )
    except AiProviderError as exc:
        logger.warning(
            "ai.orchestrator.failed run_id=%s code=%s elapsed_sec=%.1f message=%s",
            agent_run_id,
            exc.code,
            time.perf_counter() - started_at,
            exc.message,
        )
        agent_runs.mark_failed(agent_run_id, error_code=exc.code, error_message=exc.message, review_required=True)
        return
    except ContentQualityError as exc:
        logger.warning(
            "ai.orchestrator.quality_failed run_id=%s elapsed_sec=%.1f issues=%s",
            agent_run_id,
            time.perf_counter() - started_at,
            exc.issues,
        )
        agent_runs.mark_failed(
            agent_run_id,
            error_code="ORCHESTRATOR_PLAN_QUALITY_INVALID",
            error_message=str(exc),
            review_required=True,
        )
        return

    agent_runs.mark_succeeded(agent_run_id, output_json=output_json, token_usage=token_usage)
    logger.info(
        "ai.orchestrator.succeeded run_id=%s elapsed_sec=%.1f",
        agent_run_id,
        time.perf_counter() - started_at,
    )


def _normalize_orchestrator_plan_candidate(
    plan: Any,
    *,
    content_type: str,
    template_randomization: Any = None,
) -> dict:
    if not isinstance(plan, dict):
        return plan

    normalized = dict(plan)
    contracts = ORCHESTRATOR_STAGE_CONTRACTS.get(content_type)
    if not contracts:
        return normalized

    stage_plan = normalized.get("stagePlan")
    if not isinstance(stage_plan, list):
        return normalized

    forced_templates = _forced_templates_from_randomization(template_randomization)
    normalized_stages: list[Any] = []
    changes: list[dict[str, Any]] = []
    for item in stage_plan:
        if not isinstance(item, dict):
            normalized_stages.append(item)
            continue
        stage = dict(item)
        step = stage.get("step")
        contract = contracts.get(step)
        if not contract:
            normalized_stages.append(stage)
            continue

        before = {
            "stageRole": stage.get("stageRole"),
            "studentTitle": stage.get("studentTitle"),
            "templateType": stage.get("templateType"),
        }
        stage["stageRole"] = contract["stageRole"]
        stage["studentTitle"] = contract["studentTitle"]

        template_type = str(stage.get("templateType") or "")
        allowed_templates = contract["allowedTemplates"]
        template_aliases = contract.get("templateAliases", {})
        if template_type not in allowed_templates:
            template_type = template_aliases.get(template_type, contract["defaultTemplate"])
        forced_template = forced_templates.get(step)
        if forced_template in allowed_templates:
            template_type = forced_template
        stage["templateType"] = template_type

        after = {
            "stageRole": stage.get("stageRole"),
            "studentTitle": stage.get("studentTitle"),
            "templateType": stage.get("templateType"),
        }
        if before != after:
            changes.append({"step": step, "before": before, "after": after})
        normalized_stages.append(stage)

    normalized["stagePlan"] = normalized_stages
    if changes:
        normalized["normalizationNotes"] = [
            "오케스트레이터 단계 라벨/템플릿 값을 제품 계약에 맞게 자동 정규화했습니다.",
            *[f"{change['step']}단계: {change['before']} -> {change['after']}" for change in changes],
        ]
        logger.info("ai.orchestrator.normalized content_type=%s changes=%s", content_type, changes)
    return normalized


def _build_template_randomization(content_type: str, *, case_file: dict[str, Any]) -> dict[str, Any]:
    contracts = ORCHESTRATOR_STAGE_CONTRACTS.get(content_type, {})
    recent_templates = _recent_template_types_by_step(case_file)
    forced_stage_templates: list[dict[str, Any]] = []
    candidate_templates: dict[str, list[str]] = {}
    avoided_recent_templates: dict[str, list[str]] = {}
    for step in (2, 3):
        contract = contracts.get(step)
        if not contract:
            continue
        all_candidates = sorted(str(template) for template in contract["allowedTemplates"])
        candidates = _template_candidates_for_case(
            all_candidates,
            step=step,
            case_file=case_file,
            recent_templates=recent_templates,
        )
        candidate_templates[str(step)] = candidates
        avoided = [template for template in recent_templates.get(step, []) if template in all_candidates and template not in candidates]
        if avoided:
            avoided_recent_templates[str(step)] = avoided
        if candidates:
            forced_stage_templates.append({"step": step, "templateType": _template_random.choice(candidates)})

    _ensure_randomized_template_quality(content_type, forced_stage_templates, case_file=case_file)
    return {
        "mode": "random_per_generation",
        "randomId": uuid4().hex,
        "policy": "2~3단계 템플릿은 매 생성마다 후보 중 랜덤으로 정하고 오케스트레이터가 그대로 사용합니다.",
        "candidateTemplates": candidate_templates,
        "recentTemplates": {str(step): templates for step, templates in recent_templates.items()},
        "avoidedRecentTemplates": avoided_recent_templates,
        "forcedStageTemplates": forced_stage_templates,
    }


def _template_candidates_for_case(
    candidates: list[str],
    *,
    step: int,
    case_file: dict[str, Any],
    recent_templates: dict[int, list[str]],
) -> list[str]:
    filtered = list(candidates)
    choice_count = _choice_count_limit_from_case_file(case_file)
    if choice_count is not None and choice_count < 3:
        filtered = [template for template in filtered if template != "image_quiz"] or filtered

    recent = recent_templates.get(step, [])[:2]
    without_recent = [template for template in filtered if template not in recent]
    return without_recent or filtered


def _recent_template_types_by_step(case_file: dict[str, Any]) -> dict[int, list[str]]:
    contents = case_file.get("recentContents") if isinstance(case_file.get("recentContents"), list) else []
    result: dict[int, list[str]] = {2: [], 3: []}
    for content in reversed(contents[-6:]):
        stages = content.get("stages") if isinstance(content, dict) and isinstance(content.get("stages"), list) else []
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            step = stage.get("step")
            template_type = stage.get("templateType") or stage.get("template_type")
            if step in result and isinstance(template_type, str) and template_type not in result[step]:
                result[step].append(template_type)
    return result


def _ensure_randomized_template_quality(content_type: str, forced_stage_templates: list[dict[str, Any]], *, case_file: dict[str, Any]) -> None:
    if _allows_choice_first_case_file(case_file):
        return
    structured_templates = {"card_match", "sequence_ordering", "blank_fill"}
    if any(item.get("templateType") in structured_templates for item in forced_stage_templates):
        return

    replaceable = [item for item in forced_stage_templates if item.get("step") in {2, 3}]
    if not replaceable:
        return
    target = _template_random.choice(replaceable)
    allowed = ORCHESTRATOR_STAGE_CONTRACTS.get(content_type, {}).get(target["step"], {}).get("allowedTemplates", set())
    structured_allowed = sorted(template for template in allowed if template in structured_templates)
    if structured_allowed:
        target["templateType"] = _template_random.choice(structured_allowed)


def _allows_choice_first_case_file(case_file: dict[str, Any]) -> bool:
    choice_count = _choice_count_limit_from_case_file(case_file)
    profile = case_file.get("profile") if isinstance(case_file.get("profile"), dict) else {}
    profile_json = profile.get("profileJson") if isinstance(profile.get("profileJson"), dict) else {}
    reading_load = str(profile_json.get("readingLoad") or "")
    return reading_load == "very_low" or (choice_count is not None and choice_count <= 2)


def _choice_count_limit_from_case_file(case_file: dict[str, Any]) -> int | None:
    profile = case_file.get("profile") if isinstance(case_file.get("profile"), dict) else {}
    profile_json = profile.get("profileJson") if isinstance(profile.get("profileJson"), dict) else {}
    choice_count_value = profile_json.get("choiceCountLimit")
    try:
        return int(choice_count_value)
    except (TypeError, ValueError):
        return None


def _forced_templates_from_randomization(template_randomization: Any) -> dict[int, str]:
    if not isinstance(template_randomization, dict):
        return {}
    forced = template_randomization.get("forcedStageTemplates")
    if not isinstance(forced, list):
        return {}
    result: dict[int, str] = {}
    for item in forced:
        if not isinstance(item, dict):
            continue
        step = item.get("step")
        template_type = item.get("templateType")
        if isinstance(step, int) and isinstance(template_type, str):
            result[step] = template_type
    return result


def _build_generation_plan(orchestrator_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "unitVersion": "content_generation_units_v1",
        "scenarioPlan": _scenario_plan_from_orchestrator(orchestrator_plan),
        "stagePlans": _stage_plans_from_orchestrator(orchestrator_plan),
        "visualSpecDrafts": _visual_spec_drafts_from_orchestrator(orchestrator_plan),
        "assetIntent": {
            "imagePackageIntent": orchestrator_plan.get("imagePackageIntent") if isinstance(orchestrator_plan, dict) else None,
            "ttsNarrationIntent": orchestrator_plan.get("ttsNarrationIntent") if isinstance(orchestrator_plan, dict) else None,
        },
        "assemblyPolicy": {
            "contentId": "backend_generated",
            "stageIds": "backend_generated_by_step",
            "assetIds": "backend_generated_by_role",
            "finalPackage": "MissionContent",
        },
    }


def _scenario_plan_from_orchestrator(orchestrator_plan: dict[str, Any]) -> dict[str, Any]:
    scenario = orchestrator_plan.get("scenarioSpine") if isinstance(orchestrator_plan, dict) else None
    return {
        "unitId": "scenario",
        "scenarioSpine": scenario if isinstance(scenario, dict) else {},
        "sessionGoal": orchestrator_plan.get("sessionGoal") if isinstance(orchestrator_plan, dict) else None,
        "targetSkill": orchestrator_plan.get("targetSkill") if isinstance(orchestrator_plan, dict) else None,
        "contentType": orchestrator_plan.get("contentType") if isinstance(orchestrator_plan, dict) else None,
    }


def _stage_plans_from_orchestrator(orchestrator_plan: dict[str, Any]) -> list[dict[str, Any]]:
    stage_plan = orchestrator_plan.get("stagePlan") if isinstance(orchestrator_plan, dict) else None
    if not isinstance(stage_plan, list):
        return []
    plans = []
    for item in stage_plan:
        if not isinstance(item, dict):
            continue
        step = item.get("step")
        plans.append(
            {
                "unitId": f"stage_{step}",
                "step": step,
                "stageRole": item.get("stageRole"),
                "templateType": item.get("templateType"),
                "studentTitle": item.get("studentTitle"),
                "purpose": item.get("purpose"),
                "templateRationale": item.get("templateRationale") or item.get("reason"),
                "templateJsonContract": _template_json_contract(item.get("templateType")),
            }
        )
    return plans


def _template_json_contract(template_type: Any) -> dict[str, Any]:
    common_fields = ["imageAssetId", "audioAssetId", "assetBundle", "sourceTextLines", "sceneTextLines"]
    contracts: dict[str, dict[str, Any]] = {
        "blank_fill": {
            "requiredFields": [
                *common_fields,
                "question",
                "sentence",
                "tiles",
                "acceptedAnswers",
                "correctFeedback",
                "wrongFeedback",
            ],
            "hardRules": [
                "sentence must include exactly one blank marker: __, [A], or [B].",
                "question asks what to fill; sentence is the complete sentence with the blank marker.",
                "acceptedAnswers is an array of objects shaped {\"answer\":\"...\"}.",
                "each accepted answer must match a value in tiles.",
            ],
            "minimalExample": {
                "question": "빈칸에 들어갈 수를 골라 보세요.",
                "sentence": "처음 12개에서 5개를 나누어 주면 남은 수는 __개입니다.",
                "tiles": ["7", "12", "17"],
                "acceptedAnswers": [{"answer": "7"}],
            },
        },
        "card_match": {
            "requiredFields": [*common_fields, "question", "leftCards", "rightCards", "matches", "correctFeedback", "wrongFeedback"],
            "hardRules": [
                "leftCards ids are left_1 and left_2.",
                "rightCards ids are right_1 and right_2.",
                "matches is shaped {\"left_1\":\"right_1\",\"left_2\":\"right_2\"}.",
                "do not include choices, cards, or tiles.",
            ],
        },
        "sequence_ordering": {
            "requiredFields": [*common_fields, "question", "cards", "answerOrder", "correctFeedback", "wrongFeedback"],
            "hardRules": ["answerOrder contains the card ids in the correct order."],
        },
    }
    return contracts.get(str(template_type or ""), {"requiredFields": common_fields, "hardRules": []})


def _visual_spec_drafts_from_orchestrator(orchestrator_plan: dict[str, Any]) -> list[dict[str, Any]]:
    specs = orchestrator_plan.get("stageVisualSpecs") if isinstance(orchestrator_plan, dict) else None
    if not isinstance(specs, list):
        return []
    drafts = []
    for item in specs:
        if not isinstance(item, dict):
            continue
        role = str(item.get("assetRole") or item.get("role") or "")
        drafts.append({"unitId": f"visual_{role or len(drafts) + 1}", **item})
    return drafts


def _run_content_agent(
    agent_run_id: str,
    settings,
    input_snapshot: dict,
    student_id: str,
    case_id: str,
    case_file: dict,
    orchestrator_plan: dict,
    demo_store: DemoStore,
    agent_runs: AgentRunRepository,
) -> None:
    started_at = time.perf_counter()
    logger.info(
        "ai.content.started run_id=%s student_id=%s case_id=%s",
        agent_run_id,
        student_id,
        case_id,
    )
    try:
        mission, output_json, token_usage = _generate_valid_mission_content(
            settings=settings,
            input_snapshot=input_snapshot,
            student_id=student_id,
            case_id=case_id,
            case_file=case_file,
            orchestrator_plan=orchestrator_plan,
        )
    except AiProviderError as exc:
        logger.warning(
            "ai.content.failed run_id=%s code=%s elapsed_sec=%.1f message=%s",
            agent_run_id,
            exc.code,
            time.perf_counter() - started_at,
            exc.message,
        )
        agent_runs.mark_failed(agent_run_id, error_code=exc.code, error_message=exc.message, review_required=True)
        return
    except ContentQualityError as exc:
        logger.warning(
            "ai.content.quality_failed run_id=%s elapsed_sec=%.1f issues=%s",
            agent_run_id,
            time.perf_counter() - started_at,
            exc.issues,
        )
        agent_runs.mark_failed(
            agent_run_id,
            error_code="MISSION_CONTENT_QUALITY_INVALID",
            error_message=str(exc),
            review_required=True,
        )
        return
    except ValueError as exc:
        logger.warning(
            "ai.content.schema_failed run_id=%s elapsed_sec=%.1f error=%s",
            agent_run_id,
            time.perf_counter() - started_at,
            exc,
        )
        agent_runs.mark_failed(agent_run_id, error_code="MISSION_CONTENT_SCHEMA_INVALID", error_message=str(exc), review_required=True)
        return

    demo_store.save_generated_mission_content(mission)
    agent_runs.mark_succeeded(agent_run_id, output_json=output_json, token_usage=token_usage)
    logger.info(
        "ai.content.succeeded run_id=%s content_id=%s elapsed_sec=%.1f",
        agent_run_id,
        mission.id,
        time.perf_counter() - started_at,
    )


def _mission_from_generation(output_json: dict, *, student_id: str, case_id: str) -> MissionContent:
    candidate = output_json.get("missionContent") if isinstance(output_json.get("missionContent"), dict) else output_json
    candidate = _normalize_generated_mission_candidate(candidate)
    try:
        mission = MissionContent.model_validate(candidate)
    except ValidationError as exc:
        raise ValueError(f"MissionContent schema validation failed: {exc}") from exc
    if mission.student_id != student_id:
        raise ValueError("생성된 MissionContent.studentId가 요청 학생과 다릅니다.")
    if mission.case_id != case_id:
        raise ValueError("생성된 MissionContent.caseId가 요청 사례와 다릅니다.")
    if mission.status != "teacher_review":
        raise ValueError("생성된 MissionContent.status는 teacher_review여야 합니다.")
    return mission


def _normalize_generated_mission_candidate(candidate: Any) -> Any:
    if not isinstance(candidate, dict):
        return candidate

    normalized = dict(candidate)
    _rewrite_generated_mission_ids(normalized)
    stages = normalized.get("stages")
    if not isinstance(stages, list):
        return normalized

    normalized["stages"] = [_normalize_generated_stage(stage) for stage in stages]
    return normalized


def _replace_output_mission_content(output_json: dict, mission: MissionContent) -> dict:
    mission_payload = mission.model_dump(by_alias=True)
    if isinstance(output_json, dict) and isinstance(output_json.get("missionContent"), dict):
        return {**output_json, "missionContent": mission_payload}
    return mission_payload


def _rewrite_generated_mission_ids(mission: dict[str, Any]) -> None:
    student_id = str(mission.get("studentId") or mission.get("student_id") or "student")
    content_id = f"content_{_safe_generated_id_segment(student_id)}_{int(time.time())}_{uuid4().hex[:8]}"
    mission["id"] = content_id

    stages = mission.get("stages")
    if not isinstance(stages, list):
        stages = []
    stage_id_by_step: dict[int, str] = {}
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        step = stage.get("step")
        if isinstance(step, int):
            stage_id = f"stage_{content_id}_{step}"
            stage["id"] = stage_id
            stage["missionContentId"] = content_id
            stage_id_by_step[step] = stage_id

    assets = mission.get("assets")
    if not isinstance(assets, list):
        assets = []
    image_asset_by_role: dict[str, str] = {}
    audio_asset_by_role: dict[str, str] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        role = str(asset.get("assetRole") or "")
        asset_type = str(asset.get("assetType") or "")
        if not role or not asset_type:
            continue
        suffix = "_audio" if asset_type == "audio" else ""
        asset_id = f"asset_{content_id}_{role}{suffix}"
        asset["id"] = asset_id
        asset["missionContentId"] = content_id
        asset["stageId"] = _stage_id_for_generated_asset_role(role, stage_id_by_step)
        if asset_type == "image":
            image_asset_by_role[role] = asset_id
        elif asset_type == "audio":
            audio_asset_by_role[role] = asset_id

    for stage in stages:
        if not isinstance(stage, dict):
            continue
        step = stage.get("step")
        role = "stage_4_realtime" if step == 4 else f"stage_{step}"
        template_json = stage.get("templateJson")
        if isinstance(template_json, dict):
            image_asset_id = image_asset_by_role.get(role)
            audio_asset_id = audio_asset_by_role.get(role)
            if image_asset_id:
                template_json["imageAssetId"] = image_asset_id
            if audio_asset_id:
                template_json["audioAssetId"] = audio_asset_id
            template_json["assetBundle"] = {"imageAssetId": image_asset_id, "audioAssetId": audio_asset_id}
        realtime_spec = stage.get("realtimeSpec")
        if isinstance(realtime_spec, dict):
            realtime_spec["id"] = f"rt_spec_{content_id}"
            realtime_spec["stageId"] = stage.get("id")
            if image_asset_by_role.get(role):
                realtime_spec["imageAssetId"] = image_asset_by_role[role]


def _stage_id_for_generated_asset_role(role: str, stage_id_by_step: dict[int, str]) -> str | None:
    if role == "hero":
        return None
    if role == "stage_4_realtime":
        return stage_id_by_step.get(4)
    if role.startswith("stage_"):
        try:
            return stage_id_by_step.get(int(role.removeprefix("stage_")))
        except ValueError:
            return None
    return None


def _safe_generated_id_segment(value: str) -> str:
    return "".join(character if character.isalnum() or character in {"_", "-"} else "_" for character in value)[:48]


def _normalize_generated_stage(stage: Any) -> Any:
    if not isinstance(stage, dict):
        return stage

    normalized = dict(stage)
    template_type = normalized.get("templateType")
    template_json = normalized.get("templateJson")
    if template_type == "card_match" and isinstance(template_json, dict):
        normalized_template_json = dict(template_json)
        for unsupported_key in ("cards", "choices", "tiles"):
            normalized_template_json.pop(unsupported_key, None)
        normalized["templateJson"] = normalized_template_json
    realtime_spec = normalized.get("realtimeSpec")
    if isinstance(realtime_spec, dict):
        normalized["realtimeSpec"] = _normalize_generated_realtime_spec(realtime_spec, stage=normalized)
    return normalized


def _normalize_generated_realtime_spec(realtime_spec: dict[str, Any], *, stage: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = dict(realtime_spec)
    stage = stage or {}
    stage_template_type = stage.get("templateType")
    template_type = normalized.get("templateType") or stage_template_type
    if template_type not in {"realtime_roleplay", "realtime_teach_back"}:
        template_type = "realtime_roleplay"
    normalized["templateType"] = template_type

    _set_string_default(normalized, "practiceTitle", stage.get("studentTitle") or "한 번 해보기")
    _set_string_default(
        normalized,
        "situationText",
        normalized.get("situation") or normalized.get("scenario") or stage.get("studentInstruction") or "지금 상황에서 한 번 말해봅니다.",
    )
    _set_string_default(normalized, "aiRole", normalized.get("role") or "연습 상대")
    _set_string_default(normalized, "openingLine", normalized.get("intro") or "준비되면 한 문장으로 말해볼까요?")
    _set_string_default(
        normalized,
        "studentGoal",
        normalized.get("goal") or stage.get("studentInstruction") or "상황에 맞는 말을 짧게 시도합니다.",
    )

    allowed_feedback = normalized.get("allowedFeedback") or normalized.get("feedback")
    if not isinstance(allowed_feedback, list) or not allowed_feedback:
        normalized["allowedFeedback"] = ["학생의 시도를 먼저 인정하고, 다음에 말할 쉬운 한 문장을 제안합니다."]

    forbidden = normalized.get("forbidden")
    if not isinstance(forbidden, list) or not forbidden:
        normalized["forbidden"] = ["정답을 대신 말하지 않기", "학생을 재촉하지 않기", "틀렸다고 단정하지 않기"]

    max_turns = normalized.get("maxTurns") or normalized.get("turnLimit")
    normalized["maxTurns"] = _coerce_bounded_int(max_turns, default=6, minimum=1, maximum=12)
    max_duration_sec = normalized.get("maxDurationSec") or normalized.get("timeLimitSec") or normalized.get("durationSec")
    normalized["maxDurationSec"] = _coerce_bounded_int(max_duration_sec, default=180, minimum=1, maximum=300)

    rubric = normalized.get("rubric")
    if isinstance(rubric, list):
        normalized["rubric"] = [_normalize_generated_rubric_item(item, index) for index, item in enumerate(rubric, start=1)]
    else:
        normalized["rubric"] = [
            {"id": "r1", "label": "핵심 말을 한 번 시도한다", "required": True},
            {"id": "r2", "label": "상황에 맞게 차분히 대답한다", "required": False},
        ]
    reflection = normalized.get("postPracticeReflection")
    if isinstance(reflection, dict):
        candidates: list[str] = []
        question = reflection.get("question")
        if isinstance(question, str) and question.strip():
            candidates.append(question.strip())
        prompts = reflection.get("questions") or reflection.get("prompts")
        if isinstance(prompts, list):
            candidates.extend(str(item).strip() for item in prompts if str(item).strip())
        if candidates:
            normalized["postPracticeReflection"] = candidates
        else:
            normalized["postPracticeReflection"] = ["오늘 연습에서 잘 된 점을 한 문장으로 말해볼까요?"]
    elif isinstance(reflection, str):
        normalized["postPracticeReflection"] = [reflection.strip()] if reflection.strip() else []
    if not isinstance(normalized.get("postPracticeReflection"), list) or not normalized["postPracticeReflection"]:
        normalized["postPracticeReflection"] = ["오늘 연습에서 잘 된 점을 한 문장으로 말해볼까요?"]
    return normalized


def _set_string_default(target: dict[str, Any], key: str, default: Any) -> None:
    value = target.get(key)
    if isinstance(value, str) and value.strip():
        target[key] = value.strip()
        return
    target[key] = str(default).strip() if str(default).strip() else "한 번 해보기"


def _coerce_bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _normalize_generated_rubric_item(item: Any, index: int) -> Any:
    if not isinstance(item, dict):
        return item
    normalized = dict(item)
    label = normalized.get("label")
    if not isinstance(label, str) or not label.strip():
        for fallback_key in ("description", "criterion", "text", "name"):
            fallback = normalized.get(fallback_key)
            if isinstance(fallback, str) and fallback.strip():
                normalized["label"] = fallback.strip()
                break
    if not isinstance(normalized.get("id"), str) or not normalized["id"].strip():
        normalized["id"] = f"r{index}"
    if "required" not in normalized:
        normalized["required"] = index == 1
    return normalized


def _attach_generation_units(mission: MissionContent, *, orchestrator_plan: dict[str, Any]) -> MissionContent:
    generation_plan = _build_generation_plan(orchestrator_plan)
    brief_json = dict(mission.brief_json)
    if isinstance(orchestrator_plan.get("scenarioSpine"), dict):
        brief_json["scenarioSpine"] = orchestrator_plan["scenarioSpine"]
    if isinstance(orchestrator_plan.get("stageVisualSpecs"), list):
        brief_json["stageVisualSpecs"] = orchestrator_plan["stageVisualSpecs"]
    brief_json["generationUnits"] = {
        **generation_plan,
        "stageContentDrafts": _stage_content_drafts_from_mission(mission, orchestrator_plan),
        "assemblyNotes": [
            "백엔드가 content/stage/asset id를 결정적으로 재작성했습니다.",
            "이미지 provider prompt는 stageVisualSpecs와 templateJson을 조합해 별도 생성합니다.",
        ],
    }
    return mission.model_copy(update={"brief_json": brief_json})


def _stage_content_drafts_from_mission(mission: MissionContent, orchestrator_plan: dict[str, Any]) -> list[dict[str, Any]]:
    visual_specs_by_role = {
        str(spec.get("assetRole") or spec.get("role") or ""): spec
        for spec in _visual_spec_drafts_from_orchestrator(orchestrator_plan)
    }
    assets_by_role_type = {
        (_enum_value(asset.asset_role), _enum_value(asset.asset_type)): asset.id
        for asset in mission.assets
    }
    drafts = []
    for stage in sorted(mission.stages, key=lambda item: item.step):
        role = "stage_4_realtime" if stage.step == 4 else f"stage_{stage.step}"
        drafts.append(
            {
                "unitId": f"stage_{stage.step}",
                "step": stage.step,
                "stageId": stage.id,
                "stageRole": _enum_value(stage.stage_role),
                "templateType": _enum_value(stage.template_type),
                "studentTitle": stage.student_title,
                "studentInstruction": stage.student_instruction,
                "templateJson": stage.template_json,
                "realtimeSpec": stage.realtime_spec.model_dump(by_alias=True) if stage.realtime_spec else None,
                "imageAssetId": assets_by_role_type.get((role, "image")),
                "audioAssetId": assets_by_role_type.get((role, "audio")),
                "visualSpec": visual_specs_by_role.get(role),
            }
        )
    return drafts


def _stage_content_drafts_from_output(output_json: dict | None, orchestrator_plan: dict[str, Any]) -> list[dict[str, Any]]:
    candidate = _mission_candidate_from_output(output_json)
    if not isinstance(candidate, dict):
        return []
    stages = candidate.get("stages")
    if not isinstance(stages, list):
        return []
    visual_specs_by_role = {
        str(spec.get("assetRole") or spec.get("role") or ""): spec
        for spec in _visual_spec_drafts_from_orchestrator(orchestrator_plan)
    }
    drafts = []
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        step = stage.get("step")
        role = "stage_4_realtime" if step == 4 else f"stage_{step}"
        template_json = stage.get("templateJson") if isinstance(stage.get("templateJson"), dict) else {}
        drafts.append(
            {
                "unitId": f"stage_{step}",
                "step": step,
                "stageId": stage.get("id"),
                "stageRole": stage.get("stageRole"),
                "templateType": stage.get("templateType"),
                "studentTitle": stage.get("studentTitle"),
                "studentInstruction": stage.get("studentInstruction"),
                "templateJson": template_json,
                "realtimeSpec": stage.get("realtimeSpec") if isinstance(stage.get("realtimeSpec"), dict) else None,
                "imageAssetId": template_json.get("imageAssetId"),
                "audioAssetId": template_json.get("audioAssetId"),
                "visualSpec": visual_specs_by_role.get(role),
            }
        )
    return drafts


def _stage_repair_targets_from_errors(validation_errors: list[str], previous_output: dict | None) -> list[dict[str, Any]]:
    candidate = _mission_candidate_from_output(previous_output)
    stages = candidate.get("stages") if isinstance(candidate, dict) else None
    stage_refs = {}
    if isinstance(stages, list):
        for stage in stages:
            if isinstance(stage, dict) and isinstance(stage.get("step"), int):
                stage_refs[stage["step"]] = str(stage.get("id") or "")

    targets = []
    for step in (1, 2, 3, 4):
        reasons = []
        markers = [f"{step}단계", f"stagePlan[{step}]", f"step {step}", f"step={step}", f"stage_{step}"]
        if stage_refs.get(step):
            markers.append(stage_refs[step])
        for error in validation_errors:
            if any(marker and marker in error for marker in markers):
                reasons.append(error)
        if reasons:
            targets.append({"unitId": f"stage_{step}", "step": step, "stageId": stage_refs.get(step), "reasons": reasons})
    if targets:
        return targets
    return [{"unitId": "package", "step": None, "stageId": None, "reasons": validation_errors}]


def _mission_candidate_from_output(output_json: dict | None) -> Any:
    if not isinstance(output_json, dict):
        return None
    return output_json.get("missionContent") if isinstance(output_json.get("missionContent"), dict) else output_json


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _generate_valid_mission_content(
    *,
    settings,
    input_snapshot: dict,
    student_id: str,
    case_id: str,
    case_file: dict,
    orchestrator_plan: dict,
) -> tuple[MissionContent, dict, dict | None]:
    provider = OpenAiProvider(settings)
    instructions = load_prompt("mission_content_package")
    generation_started_at = time.perf_counter()
    logger.info("ai.content.generation_started student_id=%s case_id=%s", student_id, case_id)
    output_json, token_usage = provider.create_json_response(
        model=settings.openai_content_model,
        instructions=instructions,
        input_snapshot=input_snapshot,
        output_schema_name=PROMPT_SPECS["mission_content_package"].output_schema_name,
        output_json_schema=output_json_schema(PROMPT_SPECS["mission_content_package"].output_schema_name),
        timeout_sec=settings.openai_content_timeout_sec,
        max_output_tokens=settings.openai_content_max_output_tokens,
    )
    logger.info(
        "ai.content.model_returned student_id=%s case_id=%s elapsed_sec=%.1f",
        student_id,
        case_id,
        time.perf_counter() - generation_started_at,
    )

    try:
        mission = _mission_from_generation(output_json, student_id=student_id, case_id=case_id)
        mission = _attach_generation_units(mission, orchestrator_plan=orchestrator_plan)
        validate_mission_content_quality(mission, case_file=case_file, orchestrator_plan=orchestrator_plan)
    except ContentQualityError as exc:
        logger.warning(
            "ai.content.quality_invalid student_id=%s case_id=%s issues=%s",
            student_id,
            case_id,
            exc.issues,
        )
        raise
    except ValueError as exc:
        logger.warning(
            "ai.content.schema_invalid student_id=%s case_id=%s error=%s",
            student_id,
            case_id,
            exc,
        )
        raise

    output_json = _replace_output_mission_content(output_json, mission)
    logger.info(
        "ai.content.validated student_id=%s case_id=%s content_id=%s",
        student_id,
        case_id,
        mission.id,
    )
    return mission, output_json, token_usage


def _critique_mission_content_quality(
    *,
    provider: OpenAiProvider,
    settings,
    case_file: dict,
    orchestrator_plan: dict,
    mission: MissionContent,
) -> dict[str, Any]:
    output_json, _ = provider.create_json_response(
        model=settings.openai_critique_model,
        instructions=load_prompt("content_quality_critique"),
        input_snapshot={
            "caseFile": case_file,
            "orchestratorPlan": orchestrator_plan,
            "missionContent": mission.model_dump(by_alias=True),
        },
        output_schema_name=PROMPT_SPECS["content_quality_critique"].output_schema_name,
        output_json_schema=output_json_schema(PROMPT_SPECS["content_quality_critique"].output_schema_name),
        timeout_sec=settings.openai_critique_timeout_sec,
        max_output_tokens=settings.openai_critique_max_output_tokens,
    )
    verdict = output_json.get("verdict")
    if verdict not in {"pass", "repair"}:
        raise ContentQualityError(["content quality critique verdict는 pass 또는 repair여야 합니다."])
    issues = output_json.get("issues")
    if verdict == "repair" and not isinstance(issues, list):
        raise ContentQualityError(["content quality critique repair에는 issues list가 필요합니다."])
    return output_json


def _critique_issues(critique: dict[str, Any]) -> list[str]:
    issues = [str(issue) for issue in critique.get("issues", []) if str(issue).strip()]
    repair_instruction = critique.get("repairInstruction")
    if isinstance(repair_instruction, str) and repair_instruction.strip():
        issues.append(repair_instruction.strip())
    return issues or ["콘텐츠 품질 비평 단계에서 수정이 필요하다고 판단했습니다."]
