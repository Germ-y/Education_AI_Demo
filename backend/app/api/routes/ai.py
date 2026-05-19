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
from app.api.deps import get_agent_run_repository, get_generation_job_repository, get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.domain.enums import MissionStatus
from app.domain.models import GenerationJob
from app.domain.schemas import ContentGenerationRequest, GenerationJobRequest, MissionContent, OrchestratorRunRequest
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.generation_job_repository import GenerationJobRepository
from app.services.content_quality import ContentQualityError, validate_mission_content_quality, validate_orchestrator_plan_quality
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/ai", tags=["ai"])
logger = logging.getLogger(__name__)
_template_random = SystemRandom()
GENERATION_JOB_STALE_AFTER_SECONDS = 45 * 60

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
                "card_match",
                "sequence_ordering",
                "blank_fill",
                "scene_question",
                "clue_question",
            },
        },
        3: {
            "stageRole": "applied_problem",
            "studentTitle": "문제 2",
            "defaultTemplate": "image_quiz",
            "allowedTemplates": {
                "card_match",
                "sequence_ordering",
                "blank_fill",
                "image_quiz",
                "explanation_choice",
                "wrong_explanation_fix",
            },
            "templateAliases": {
                "applied_question": "image_quiz",
                "scene_question": "image_quiz",
                "clue_question": "image_quiz",
                "action_choice": "image_quiz",
                "decision_card": "image_quiz",
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
            "allowedTemplates": {"scene_observation", "highlight_clue", "card_match"},
            "templateAliases": {"scene_question": "highlight_clue", "clue_question": "highlight_clue"},
        },
        3: {
            "stageRole": "action_selection",
            "studentTitle": "행동 고르기",
            "defaultTemplate": "action_choice",
            "allowedTemplates": {"card_match", "sequence_ordering", "action_choice", "decision_card"},
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


@router.post("/generation-jobs")
def create_generation_job(
    payload: GenerationJobRequest,
    background_tasks: BackgroundTasks,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
    generation_jobs: GenerationJobRepository = Depends(get_generation_job_repository),
) -> dict:
    generation_jobs.mark_stale_running_failed(max_age_seconds=GENERATION_JOB_STALE_AFTER_SECONDS)
    case_file = demo_store.get_student_case_file(payload.student_id)
    if case_file is None or case_file["openCase"]["id"] != payload.case_id:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "학생 사례를 찾을 수 없습니다."})
    if principal.role == "teacher" and case_file["openCase"]["ownerTeacherId"] != principal.id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "담당 학생 사례만 생성할 수 있습니다."})

    content_type = str(payload.content_type or case_file["profile"]["studentType"])
    job, created = generation_jobs.create_or_get_active(
        teacher_id=principal.id,
        student_id=payload.student_id,
        case_id=payload.case_id,
        content_type=content_type,
        requested_goal=payload.requested_goal,
    )
    if created:
        background_tasks.add_task(_run_generation_job, job.id, demo_store, agent_runs, generation_jobs)
        logger.info(
            "ai.generation_job.queued job_id=%s student_id=%s case_id=%s content_type=%s",
            job.id,
            payload.student_id,
            payload.case_id,
            content_type,
        )
    return ok({"job": job.model_dump(by_alias=True), "created": created})


@router.get("/generation-jobs")
def list_generation_jobs(
    student_id: str | None = None,
    case_id: str | None = None,
    status: str | None = None,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
    generation_jobs: GenerationJobRepository = Depends(get_generation_job_repository),
) -> dict:
    generation_jobs.mark_stale_running_failed(max_age_seconds=GENERATION_JOB_STALE_AFTER_SECONDS)
    statuses = {item.strip() for item in status.split(",") if item.strip()} if status else None
    jobs = generation_jobs.list_recent(student_id=student_id, case_id=case_id, statuses=statuses, limit=50)
    refreshed = [_refresh_generation_job_state(job, demo_store=demo_store, generation_jobs=generation_jobs) for job in jobs]
    if principal.role == "teacher":
        refreshed = [job for job in refreshed if _teacher_can_read_generation_job(job, principal.id, demo_store)]
    return ok([job.model_dump(by_alias=True) for job in refreshed])


@router.get("/generation-jobs/{job_id}")
def get_generation_job(
    job_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
    generation_jobs: GenerationJobRepository = Depends(get_generation_job_repository),
) -> dict:
    generation_jobs.mark_stale_running_failed(max_age_seconds=GENERATION_JOB_STALE_AFTER_SECONDS)
    job = generation_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "GENERATION_JOB_NOT_FOUND", "message": "생성 작업을 찾을 수 없습니다."})
    if principal.role == "teacher" and not _teacher_can_read_generation_job(job, principal.id, demo_store):
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "담당 학생 생성 작업만 확인할 수 있습니다."})
    job = _refresh_generation_job_state(job, demo_store=demo_store, generation_jobs=generation_jobs)
    return ok(job.model_dump(by_alias=True))


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

    generating_content = demo_store.get_generating_material_for_case(payload.student_id, payload.case_id)
    if generating_content is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONTENT_ASSET_GENERATION_ALREADY_RUNNING",
                "message": "이미 이미지와 음성 생성이 진행 중인 자료가 있습니다. 완료 후 다시 확인해 주세요.",
                "details": {"contentId": generating_content.id, "status": generating_content.status},
            },
        )

    running_orchestrator = agent_runs.find_running_generation_for_case(
        student_id=payload.student_id,
        case_id=payload.case_id,
        agent_type="orchestrator",
    )
    if running_orchestrator is not None:
        return ok({"agentRun": running_orchestrator.model_dump(by_alias=True)})

    running_content = agent_runs.find_running_generation_for_case(
        student_id=payload.student_id,
        case_id=payload.case_id,
        agent_type="content",
    )
    if running_content is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONTENT_GENERATION_ALREADY_RUNNING",
                "message": "이미 콘텐츠 생성 작업이 진행 중입니다. 완료 후 다시 확인해 주세요.",
                "details": {"agentRunId": running_content.id, "status": running_content.status},
            },
        )

    settings = get_settings()
    spec = PROMPT_SPECS["orchestrator_plan"]
    content_type = str(payload.content_type or case_file["profile"]["studentType"])
    template_randomization = _build_template_randomization(content_type, requested_goal=payload.requested_goal)
    input_snapshot = {
        "teacherId": principal.id,
        "studentId": payload.student_id,
        "caseId": payload.case_id,
        "requestedGoal": payload.requested_goal,
        "contentType": content_type,
        "studentProfile": _minimal_student_profile(case_file),
        "templateRandomization": template_randomization,
        "generationMode": {
            "contextPolicy": "minimal_student_profile_only",
            "memoryUsed": False,
            "caseFileUsedForAi": False,
            "teacherRequestedGoalIsTopicSource": True,
        },
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

    existing_content_run = agent_runs.find_content_generation_for_orchestrator(payload.orchestrator_run_id)
    if existing_content_run is not None:
        return ok(
            {
                "agentRun": existing_content_run.model_dump(by_alias=True),
                "content": _content_from_agent_run(existing_content_run, demo_store, principal.id),
            }
        )

    generating_content = demo_store.get_generating_material_for_case(payload.student_id, payload.case_id)
    if generating_content is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONTENT_ASSET_GENERATION_ALREADY_RUNNING",
                "message": "이미 이미지와 음성 생성이 진행 중인 자료가 있습니다. 완료 후 다시 확인해 주세요.",
                "details": {"contentId": generating_content.id, "status": generating_content.status},
            },
        )

    running_content = agent_runs.find_running_generation_for_case(
        student_id=payload.student_id,
        case_id=payload.case_id,
        agent_type="content",
    )
    if running_content is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONTENT_GENERATION_ALREADY_RUNNING",
                "message": "이미 콘텐츠 생성 작업이 진행 중입니다. 완료 후 다시 확인해 주세요.",
                "details": {"agentRunId": running_content.id, "status": running_content.status},
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
        "studentProfile": _minimal_student_profile(case_file),
        "orchestratorPlan": orchestrator_run.output_json,
        "generationPlan": generation_plan,
        "generationMode": {
            "contextPolicy": "minimal_student_profile_only",
            "memoryUsed": False,
            "caseFileUsedForAi": False,
        },
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


def _content_from_agent_run(agent_run, demo_store: DemoStore, teacher_id: str) -> dict | None:
    output = agent_run.output_json
    if not isinstance(output, dict):
        return None
    candidate = output.get("missionContent") if isinstance(output.get("missionContent"), dict) else output
    content_id = candidate.get("id") if isinstance(candidate, dict) else None
    if not isinstance(content_id, str):
        return None
    content = demo_store.get_mission_for_teacher(content_id, teacher_id=teacher_id)
    return content.model_dump(by_alias=True) if content is not None else None


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


def _run_generation_job(
    job_id: str,
    demo_store: DemoStore,
    agent_runs: AgentRunRepository,
    generation_jobs: GenerationJobRepository,
) -> None:
    job = generation_jobs.get(job_id)
    if job is None:
        return

    settings = get_settings()
    case_file = demo_store.get_student_case_file(job.student_id)
    if case_file is None or case_file["openCase"]["id"] != job.case_id:
        generation_jobs.mark_failed(
            job_id,
            error_code="CASE_NOT_FOUND",
            error_message="학생 사례를 찾을 수 없습니다.",
            message="학생 사례를 찾지 못해 생성 작업을 중단했습니다.",
        )
        return

    content_type = str(job.content_type)
    try:
        template_randomization = _build_template_randomization(content_type, requested_goal=job.requested_goal)
        orchestrator_snapshot = {
            "teacherId": job.teacher_id,
            "studentId": job.student_id,
            "caseId": job.case_id,
            "requestedGoal": job.requested_goal,
            "contentType": content_type,
            "studentProfile": _minimal_student_profile(case_file),
            "templateRandomization": template_randomization,
            "generationMode": {
                "contextPolicy": "minimal_student_profile_only",
                "memoryUsed": False,
                "caseFileUsedForAi": False,
                "teacherRequestedGoalIsTopicSource": True,
            },
        }
        generation_jobs.mark_phase(
            job_id,
            status="orchestrating",
            message="수업 방향을 정리하는 중입니다.",
            progress={"step": "orchestrating"},
        )
        orchestrator_spec = PROMPT_SPECS["orchestrator_plan"]
        orchestrator_run = agent_runs.create_running(
            agent_type="orchestrator",
            prompt_version=orchestrator_spec.version,
            output_schema_name=orchestrator_spec.output_schema_name,
            input_snapshot=orchestrator_snapshot,
            model=settings.openai_orchestrator_model,
        )
        generation_jobs.mark_phase(
            job_id,
            status="orchestrating",
            message="수업 방향을 정리하는 중입니다.",
            progress={"step": "orchestrating", "orchestratorRunId": orchestrator_run.id},
            orchestrator_run_id=orchestrator_run.id,
        )
        _run_orchestrator_agent(
            orchestrator_run.id,
            settings,
            orchestrator_snapshot,
            job.student_id,
            job.case_id,
            content_type,
            agent_runs,
        )
        orchestrator_run = agent_runs.get(orchestrator_run.id)
        if orchestrator_run is None or orchestrator_run.status != "succeeded" or orchestrator_run.output_json is None:
            _fail_generation_job_from_agent_run(
                generation_jobs,
                job_id,
                orchestrator_run,
                fallback_code="ORCHESTRATOR_RUN_FAILED",
                fallback_message="수업 방향 생성에 실패했습니다.",
            )
            return

        generation_plan = _build_generation_plan(orchestrator_run.output_json)
        content_snapshot = {
            "teacherId": job.teacher_id,
            "studentId": job.student_id,
            "caseId": job.case_id,
            "orchestratorRunId": orchestrator_run.id,
            "studentProfile": _minimal_student_profile(case_file),
            "orchestratorPlan": orchestrator_run.output_json,
            "generationPlan": generation_plan,
            "generationMode": {
                "contextPolicy": "minimal_student_profile_only",
                "memoryUsed": False,
                "caseFileUsedForAi": False,
            },
        }
        generation_jobs.mark_phase(
            job_id,
            status="content_generating",
            message="검토할 수업 콘텐츠 구조를 만드는 중입니다.",
            progress={"step": "content_generating", "orchestratorRunId": orchestrator_run.id},
        )
        content_spec = PROMPT_SPECS["mission_content_package"]
        content_run = agent_runs.create_running(
            agent_type="content",
            prompt_version=content_spec.version,
            output_schema_name=content_spec.output_schema_name,
            input_snapshot=content_snapshot,
            model=settings.openai_content_model,
        )
        generation_jobs.mark_phase(
            job_id,
            status="content_generating",
            message="검토할 수업 콘텐츠 구조를 만드는 중입니다.",
            progress={"step": "content_generating", "contentRunId": content_run.id},
            content_run_id=content_run.id,
        )
        _run_content_agent(
            content_run.id,
            settings,
            content_snapshot,
            job.student_id,
            job.case_id,
            case_file,
            orchestrator_run.output_json,
            demo_store,
            agent_runs,
        )
        content_run = agent_runs.get(content_run.id)
        if content_run is None or content_run.status != "succeeded":
            _fail_generation_job_from_agent_run(
                generation_jobs,
                job_id,
                content_run,
                fallback_code="CONTENT_RUN_FAILED",
                fallback_message="콘텐츠 생성에 실패했습니다.",
            )
            return

        content_id = _content_id_from_agent_run(content_run)
        if content_id is None:
            generation_jobs.mark_failed(
                job_id,
                error_code="CONTENT_ID_NOT_FOUND",
                error_message="생성된 콘텐츠 ID를 확인하지 못했습니다.",
                message="수업 구조는 만들어졌지만 콘텐츠 ID를 확인하지 못했습니다.",
            )
            return

        generation_jobs.mark_phase(
            job_id,
            status="asset_generating",
            message="이미지와 음성 asset을 생성하는 중입니다.",
            progress={"step": "asset_generating", "contentId": content_id},
            content_id=content_id,
        )
        asset_job = _run_generation_job_assets(content_id, teacher_id=job.teacher_id, demo_store=demo_store)
        asset_progress = _asset_job_progress(asset_job)
        if asset_job.get("status") == "succeeded":
            generation_jobs.mark_ready(job_id, content_id=content_id, asset_job_id=asset_job.get("jobId"), progress=asset_progress)
            return

        failure_message = str(asset_job.get("errorMessage") or "수업 구조는 만들어졌지만 이미지/음성 생성에 실패했습니다.")
        _close_failed_generation_content(
            demo_store,
            content_id,
            teacher_id=job.teacher_id,
            message=failure_message,
            requested_changes=["이미지와 음성 asset을 다시 생성해 주세요."],
        )
        generation_jobs.mark_failed(
            job_id,
            error_code=str(asset_job.get("errorCode") or "ASSET_GENERATION_FAILED"),
            error_message=str(asset_job.get("errorMessage") or "이미지와 음성 asset 생성에 실패했습니다."),
            message=failure_message,
            content_id=content_id,
            asset_job_id=asset_job.get("jobId") if isinstance(asset_job.get("jobId"), str) else None,
            progress=asset_progress,
        )
    except HTTPException as exc:
        code, message = _error_from_http_exception(exc)
        generation_jobs.mark_failed(job_id, error_code=code, error_message=message, message=message)
    except Exception as exc:  # noqa: BLE001 - background job must finish in DB with a visible failure.
        logger.exception("ai.generation_job.unhandled_failed job_id=%s", job_id)
        generation_jobs.mark_failed(
            job_id,
            error_code="GENERATION_JOB_FAILED",
            error_message=str(exc) or "생성 작업이 실패했습니다.",
            message="자료 생성 중 오류가 발생했습니다. 다시 시도해 주세요.",
        )


def _run_generation_job_assets(content_id: str, *, teacher_id: str, demo_store: DemoStore) -> dict[str, Any]:
    from app.api.routes.contents import run_asset_generation_package_job

    return run_asset_generation_package_job(content_id, teacher_id=teacher_id, demo_store=demo_store)


def _refresh_generation_job_state(
    job: GenerationJob,
    *,
    demo_store: DemoStore,
    generation_jobs: GenerationJobRepository,
) -> GenerationJob:
    if job.status not in {"asset_generating", "failed"} or not job.content_id or not job.asset_job_id:
        return job

    from app.api.routes.contents import get_asset_generation_package_job_snapshot

    asset_job = get_asset_generation_package_job_snapshot(job.content_id, job.asset_job_id, teacher_id=job.teacher_id, demo_store=demo_store)
    if asset_job is None:
        return job

    progress = _asset_job_progress(asset_job)
    if asset_job.get("status") == "succeeded":
        return generation_jobs.mark_ready(job.id, content_id=job.content_id, asset_job_id=job.asset_job_id, progress=progress) or job
    if asset_job.get("status") in {"failed", "partial_failed"}:
        failure_message = str(asset_job.get("errorMessage") or "수업 구조는 만들어졌지만 이미지/음성 생성에 실패했습니다.")
        _close_failed_generation_content(
            demo_store,
            job.content_id,
            teacher_id=job.teacher_id,
            message=failure_message,
            requested_changes=["이미지와 음성 asset을 다시 생성해 주세요."],
        )
        return generation_jobs.mark_failed(
            job.id,
            error_code=str(asset_job.get("errorCode") or "ASSET_GENERATION_FAILED"),
            error_message=str(asset_job.get("errorMessage") or "이미지와 음성 asset 생성에 실패했습니다."),
            message=failure_message,
            content_id=job.content_id,
            asset_job_id=job.asset_job_id,
            progress=progress,
        ) or job

    return (
        generation_jobs.mark_phase(
            job.id,
            status="asset_generating",
            message="이미지와 음성 asset을 생성하는 중입니다.",
            progress=progress,
            content_id=job.content_id,
            asset_job_id=job.asset_job_id,
        )
        or job
    )


def _asset_job_progress(asset_job: dict[str, Any]) -> dict[str, Any]:
    assets = asset_job.get("assets") if isinstance(asset_job.get("assets"), list) else []
    return {
        "step": "asset_generating",
        "assetJobId": asset_job.get("jobId"),
        "assetStatus": asset_job.get("status"),
        "totalCount": asset_job.get("totalCount"),
        "completedCount": asset_job.get("completedCount"),
        "failedCount": asset_job.get("failedCount"),
        "generatedCount": asset_job.get("generatedCount"),
        "assets": [
            {
                "assetId": item.get("assetId"),
                "assetRole": item.get("assetRole"),
                "assetType": item.get("assetType"),
                "status": item.get("status"),
                "errorCode": item.get("errorCode"),
                "errorMessage": item.get("errorMessage"),
            }
            for item in assets
            if isinstance(item, dict)
        ],
    }


def _close_failed_generation_content(
    demo_store: DemoStore,
    content_id: str,
    *,
    teacher_id: str,
    message: str,
    requested_changes: list[str],
) -> None:
    demo_store.close_generation_failed_mission_content(
        content_id,
        teacher_id,
        reason=message,
        requested_changes=requested_changes,
    )


def _content_id_from_agent_run(agent_run) -> str | None:
    output = agent_run.output_json
    if not isinstance(output, dict):
        return None
    candidate = output.get("missionContent") if isinstance(output.get("missionContent"), dict) else output
    content_id = candidate.get("id") if isinstance(candidate, dict) else None
    return content_id if isinstance(content_id, str) else None


def _fail_generation_job_from_agent_run(
    generation_jobs: GenerationJobRepository,
    job_id: str,
    agent_run,
    *,
    fallback_code: str,
    fallback_message: str,
) -> None:
    code = agent_run.error_code if agent_run is not None and agent_run.error_code else fallback_code
    message = agent_run.error_message if agent_run is not None and agent_run.error_message else fallback_message
    generation_jobs.mark_failed(job_id, error_code=code, error_message=message, message=fallback_message)


def _teacher_can_read_generation_job(job: GenerationJob, teacher_id: str, demo_store: DemoStore) -> bool:
    if job.teacher_id == teacher_id:
        return True
    case_file = demo_store.get_student_case_file(job.student_id)
    return bool(case_file and case_file["openCase"]["id"] == job.case_id and case_file["openCase"]["ownerTeacherId"] == teacher_id)


def _error_from_http_exception(exc: HTTPException) -> tuple[str, str]:
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code") if isinstance(detail.get("code"), str) else "HTTP_ERROR"
        message = detail.get("message") if isinstance(detail.get("message"), str) else str(detail)
        return code, message
    if isinstance(detail, str):
        return "HTTP_ERROR", detail
    return "HTTP_ERROR", str(exc)


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
            case_file=None,
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


def _minimal_student_profile(case_file: dict[str, Any]) -> dict[str, Any]:
    profile = case_file.get("profile") if isinstance(case_file.get("profile"), dict) else {}
    return {
        "id": profile.get("id"),
        "displayName": profile.get("displayName") or profile.get("name"),
        "grade": profile.get("grade"),
        "gradeLabel": profile.get("gradeLabel"),
        "studentType": profile.get("studentType"),
        "studentTypeLabel": profile.get("studentTypeLabel"),
    }


def _build_template_randomization(content_type: str, *, requested_goal: str | None = None) -> dict[str, Any]:
    contracts = ORCHESTRATOR_STAGE_CONTRACTS.get(content_type, {})
    forced_stage_templates: list[dict[str, Any]] = []
    candidate_templates: dict[str, list[str]] = {}
    goal_text = str(requested_goal or "")
    for step in (2, 3):
        contract = contracts.get(step)
        if not contract:
            continue
        all_candidates = sorted(str(template) for template in contract["allowedTemplates"])
        candidate_templates[str(step)] = list(all_candidates)
        preferred = _preferred_templates_for_goal(content_type, step, goal_text)
        chosen_template = _choose_goal_aligned_template(preferred, all_candidates)
        if chosen_template:
            forced_stage_templates.append({"step": step, "templateType": chosen_template})

    return {
        "mode": "intent_weighted_per_generation",
        "randomId": uuid4().hex,
        "policy": "2~3단계 템플릿은 선생님 요청의 사고 유형을 먼저 보고, 같은 유형 안에서만 변주합니다.",
        "candidateTemplates": candidate_templates,
        "forcedStageTemplates": forced_stage_templates,
    }


def _choose_goal_aligned_template(preferred_templates: list[str], allowed_templates: list[str]) -> str | None:
    allowed = [template for template in preferred_templates if template in allowed_templates]
    if allowed:
        return _template_random.choice(allowed)
    if allowed_templates:
        return _template_random.choice(allowed_templates)
    return None


def _preferred_templates_for_goal(content_type: str, step: int, goal_text: str) -> list[str]:
    text = goal_text.replace(" ", "")
    if content_type == "learning_focus":
        return _preferred_learning_templates(step, text)
    if content_type == "life_support":
        return _preferred_life_templates(step, text)
    return []


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _preferred_learning_templates(step: int, text: str) -> list[str]:
    reason_keywords = ("이유", "근거", "주장", "설명", "판단", "왜", "오류", "틀린", "고치")
    compare_keywords = ("비교", "차이", "가장", "크다", "작다", "많다", "적다", "순서", "절차", "차례")
    connect_keywords = ("짝", "연결", "분류", "기준", "예시", "개념", "뜻", "단위")
    fill_keywords = ("빈칸", "식", "계산", "문장", "조건", "비율", "비례", "분수", "소수")

    if _has_any(text, reason_keywords):
        return ["clue_question", "card_match", "scene_question"] if step == 2 else ["explanation_choice", "wrong_explanation_fix"]
    if _has_any(text, compare_keywords):
        return ["sequence_ordering", "card_match", "scene_question"] if step == 2 else ["sequence_ordering", "explanation_choice"]
    if _has_any(text, connect_keywords):
        return ["card_match", "blank_fill", "scene_question"] if step == 2 else ["explanation_choice", "card_match", "blank_fill"]
    if _has_any(text, fill_keywords):
        return ["blank_fill", "scene_question"] if step == 2 else ["blank_fill", "explanation_choice"]
    return ["scene_question", "card_match", "blank_fill"] if step == 2 else ["explanation_choice", "blank_fill", "wrong_explanation_fix"]


def _preferred_life_templates(step: int, text: str) -> list[str]:
    sequence_keywords = ("순서", "절차", "차례", "먼저", "다음", "이후", "정리")
    expression_keywords = ("도움", "요청", "말", "표현", "묻", "물어", "거절", "인사", "대화")
    clue_keywords = ("단서", "확인", "찾", "살펴", "기다", "멈추")

    if _has_any(text, sequence_keywords):
        return ["scene_observation", "card_match"] if step == 2 else ["sequence_ordering", "decision_card"]
    if _has_any(text, expression_keywords):
        return ["scene_observation", "highlight_clue"] if step == 2 else ["decision_card", "action_choice"]
    if _has_any(text, clue_keywords):
        return ["highlight_clue", "scene_observation"] if step == 2 else ["action_choice", "decision_card"]
    return ["scene_observation", "highlight_clue", "card_match"] if step == 2 else ["decision_card", "action_choice", "sequence_ordering"]


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
    template_type_value = str(template_type or "")
    if template_type_value in {"realtime_roleplay", "realtime_teach_back"}:
        return {
            "requiredFields": common_fields,
            "hardRules": [
                f"stage.templateType must be exactly {template_type_value}.",
                "stage.stageRole must be realtime_practice.",
                "stage.step must be 4.",
                "stage.realtimeSpec is required.",
                "stage.realtimeSpec.stageId must equal stage.id.",
                f"stage.realtimeSpec.templateType must be exactly {template_type_value}.",
                "stage.realtimeSpec.rubric is an array of objects shaped {\"id\":\"r1\",\"label\":\"...\",\"required\":true}.",
                "stage.realtimeSpec.postPracticeReflection is an array of strings.",
                "stage.templateJson must include only the common asset fields plus empty sourceTextLines and sceneTextLines.",
            ],
        }
    choice_contract = {
        "requiredFields": [*common_fields, "question", "choices", "answer", "correctFeedback", "wrongFeedback"],
        "hardRules": [
            "choices is an array of objects shaped {\"id\":\"a\",\"text\":\"...\"}.",
            "answer is exactly one choice id from choices.",
            "the correct answer must be determined from question and choices, not from the image.",
            "answer, the selected choice text, correctFeedback, and wrongFeedback must all describe the same correct solution.",
            "For quantity, math, ratio, time, length, or condition-comparison questions, silently solve the problem "
            "before writing JSON and ensure the selected answer is mathematically consistent.",
        ],
    }
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
                "leftCards must not repeat the same meaning.",
                "rightCards are answer candidates; rightCards must not repeat the same answer, category, or conclusion.",
                "rightCards should be contrasting criteria or outcomes, such as 만날 수 있는 시간 vs 겹쳐서 어려운 시간.",
                "If a card refers to a visible person, use an observable descriptor such as clothing, position, gender presentation, or current action.",
                "Do not use hidden personal names like 민수 or 영희 unless the story text explicitly introduced the names.",
            ],
        },
        "sequence_ordering": {
            "requiredFields": [*common_fields, "question", "cards", "answerOrder", "correctFeedback", "wrongFeedback"],
            "hardRules": [
                "answerOrder contains the card ids in the correct order.",
                "answerOrder must follow the semantic order requested by question, not the display order of cards; for example, 더 단단한 것부터 means the hardest card id comes first.",
                "Generated student missions should use exactly 3 cards unless the teacher explicitly requested a longer procedure.",
                "For life_support step 3 action_selection, cards and answerOrder must contain exactly 3 items.",
            ],
        },
        "scene_question": choice_contract,
        "clue_question": choice_contract,
        "image_quiz": choice_contract,
        "applied_question": choice_contract,
        "action_choice": choice_contract,
        "explanation_choice": choice_contract,
        "decision_card": choice_contract,
        "scene_observation": choice_contract,
        "highlight_clue": choice_contract,
        "wrong_explanation_fix": {
            "requiredFields": [
                *common_fields,
                "question",
                "wrongLine",
                "choices",
                "answer",
                "fixedLine",
                "correctFeedback",
                "wrongFeedback",
            ],
            "hardRules": [
                "choices is an array of objects shaped {\"id\":\"a\",\"text\":\"...\"}.",
                "answer is exactly one choice id from choices.",
                "wrongLine is a plausible misconception and fixedLine explains the corrected idea.",
                "fixedLine must be the actually correct explanation, and answer must point to the choice that means the same corrected idea.",
                "If the task uses division with quotient and remainder, check divisor × quotient + remainder = dividend "
                "and remainder < divisor before choosing answer.",
                "wrongLine must stay wrong; fixedLine, selected choice, and correctFeedback must not contradict each other.",
            ],
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

    mission.status = MissionStatus.GENERATING
    output_json = _replace_output_mission_content(output_json, mission)
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

    normalized["stages"] = stages
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
            "studentProfile": _minimal_student_profile(case_file),
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
