import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import ValidationError

from app.ai.openai_provider import OpenAiProvider
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
MAX_CONTENT_GENERATION_ATTEMPTS = 2
logger = logging.getLogger(__name__)

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
    input_snapshot = {
        "teacherId": principal.id,
        "studentId": payload.student_id,
        "caseId": payload.case_id,
        "requestedGoal": payload.requested_goal,
        "contentType": payload.content_type,
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

    content_type = str(payload.content_type or case_file["profile"]["studentType"])

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
            timeout_sec=settings.openai_orchestrator_timeout_sec,
        )
        output_json = _normalize_orchestrator_plan_candidate(output_json, content_type=content_type)
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


def _normalize_orchestrator_plan_candidate(plan: Any, *, content_type: str) -> dict:
    if not isinstance(plan, dict):
        return plan

    normalized = dict(plan)
    contracts = ORCHESTRATOR_STAGE_CONTRACTS.get(content_type)
    if not contracts:
        return normalized

    stage_plan = normalized.get("stagePlan")
    if not isinstance(stage_plan, list):
        return normalized

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
            }
        )
    return plans


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
    attempt_usages: list[dict | None] = []
    previous_output: dict | None = None
    validation_errors: list[str] = []

    for attempt in range(1, MAX_CONTENT_GENERATION_ATTEMPTS + 1):
        attempt_started_at = time.perf_counter()
        generation_snapshot = input_snapshot
        if attempt > 1:
            stage_repair_targets = _stage_repair_targets_from_errors(validation_errors, previous_output)
            generation_snapshot = {
                **input_snapshot,
                "qualityRepair": {
                    "attempt": attempt,
                    "repairMode": "targeted_stage_or_visual_repair",
                    "instruction": (
                        "validationErrors와 stageRepairTargets에 해당하는 stage/visual unit만 고치고 "
                        "나머지 stageContentDrafts는 그대로 보존한 완전한 MissionContent JSON을 반환하세요."
                    ),
                    "validationErrors": validation_errors,
                    "stageRepairTargets": stage_repair_targets,
                    "stageContentDrafts": _stage_content_drafts_from_output(previous_output, orchestrator_plan),
                    "visualSpecDrafts": _visual_spec_drafts_from_orchestrator(orchestrator_plan),
                    "previousOutput": previous_output,
                },
            }

        logger.info(
            "ai.content.attempt_started student_id=%s case_id=%s attempt=%s/%s",
            student_id,
            case_id,
            attempt,
            MAX_CONTENT_GENERATION_ATTEMPTS,
        )
        output_json, token_usage = provider.create_json_response(
            model=settings.openai_content_model,
            instructions=instructions,
            input_snapshot=generation_snapshot,
            timeout_sec=settings.openai_content_timeout_sec,
        )
        logger.info(
            "ai.content.attempt_model_returned student_id=%s case_id=%s attempt=%s elapsed_sec=%.1f",
            student_id,
            case_id,
            attempt,
            time.perf_counter() - attempt_started_at,
        )
        attempt_usages.append(token_usage)
        previous_output = output_json
        try:
            mission = _mission_from_generation(output_json, student_id=student_id, case_id=case_id)
            mission = _attach_generation_units(mission, orchestrator_plan=orchestrator_plan)
            validate_mission_content_quality(mission, case_file=case_file, orchestrator_plan=orchestrator_plan)
            if settings.openai_content_critique_enabled:
                critique = _critique_mission_content_quality(
                    provider=provider,
                    settings=settings,
                    case_file=case_file,
                    orchestrator_plan=orchestrator_plan,
                    mission=mission,
                )
                if critique["verdict"] != "pass":
                    raise ContentQualityError(_critique_issues(critique))
            output_json = _replace_output_mission_content(output_json, mission)
            logger.info(
                "ai.content.attempt_validated student_id=%s case_id=%s attempt=%s content_id=%s",
                student_id,
                case_id,
                attempt,
                mission.id,
            )
            return mission, output_json, _merge_token_usage(attempt_usages)
        except ContentQualityError as exc:
            validation_errors = exc.issues
            logger.warning(
                "ai.content.attempt_quality_invalid student_id=%s case_id=%s attempt=%s issues=%s",
                student_id,
                case_id,
                attempt,
                validation_errors,
            )
            if attempt == MAX_CONTENT_GENERATION_ATTEMPTS:
                raise
            logger.info(
                "ai.content.retrying_after_quality_invalid student_id=%s case_id=%s next_attempt=%s/%s",
                student_id,
                case_id,
                attempt + 1,
                MAX_CONTENT_GENERATION_ATTEMPTS,
            )
        except ValueError as exc:
            validation_errors = [str(exc)]
            logger.warning(
                "ai.content.attempt_schema_invalid student_id=%s case_id=%s attempt=%s error=%s",
                student_id,
                case_id,
                attempt,
                exc,
            )
            if attempt == MAX_CONTENT_GENERATION_ATTEMPTS:
                raise
            logger.info(
                "ai.content.retrying_after_schema_invalid student_id=%s case_id=%s next_attempt=%s/%s",
                student_id,
                case_id,
                attempt + 1,
                MAX_CONTENT_GENERATION_ATTEMPTS,
            )

    raise ContentQualityError(["콘텐츠 생성 품질 재시도 흐름이 예기치 않게 종료되었습니다."])


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
        timeout_sec=settings.openai_critique_timeout_sec,
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


def _merge_token_usage(attempt_usages: list[dict | None]) -> dict | None:
    if len(attempt_usages) == 1:
        return attempt_usages[0]
    return {"attempts": [{"attempt": index + 1, "tokenUsage": usage} for index, usage in enumerate(attempt_usages)]}
