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
        model=settings.openai_reasoning_model,
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
    input_snapshot = {
        "teacherId": principal.id,
        "studentId": payload.student_id,
        "caseId": payload.case_id,
        "orchestratorRunId": payload.orchestrator_run_id,
        "orchestratorPlan": orchestrator_run.output_json,
        "caseFile": case_file,
    }
    agent_run = agent_runs.create_running(
        agent_type="content",
        prompt_version=spec.version,
        output_schema_name=spec.output_schema_name,
        input_snapshot=input_snapshot,
        model=settings.openai_reasoning_model,
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
    try:
        output_json, token_usage = OpenAiProvider(settings).create_json_response(
            model=settings.openai_reasoning_model,
            instructions=load_prompt("orchestrator_plan"),
            input_snapshot=input_snapshot,
        )
        validate_orchestrator_plan_quality(
            output_json,
            student_id=student_id,
            case_id=case_id,
            content_type=content_type,
        )
    except AiProviderError as exc:
        agent_runs.mark_failed(agent_run_id, error_code=exc.code, error_message=exc.message, review_required=True)
        return
    except ContentQualityError as exc:
        agent_runs.mark_failed(
            agent_run_id,
            error_code="ORCHESTRATOR_PLAN_QUALITY_INVALID",
            error_message=str(exc),
            review_required=True,
        )
        return

    agent_runs.mark_succeeded(agent_run_id, output_json=output_json, token_usage=token_usage)


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
        agent_runs.mark_failed(agent_run_id, error_code=exc.code, error_message=exc.message, review_required=True)
        return
    except ContentQualityError as exc:
        agent_runs.mark_failed(
            agent_run_id,
            error_code="MISSION_CONTENT_QUALITY_INVALID",
            error_message=str(exc),
            review_required=True,
        )
        return
    except ValueError as exc:
        agent_runs.mark_failed(agent_run_id, error_code="MISSION_CONTENT_SCHEMA_INVALID", error_message=str(exc), review_required=True)
        return

    demo_store.save_generated_mission_content(mission)
    agent_runs.mark_succeeded(agent_run_id, output_json=output_json, token_usage=token_usage)


def _mission_from_generation(output_json: dict, *, student_id: str, case_id: str) -> MissionContent:
    candidate = output_json.get("missionContent") if isinstance(output_json.get("missionContent"), dict) else output_json
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
        generation_snapshot = input_snapshot
        if attempt > 1:
            generation_snapshot = {
                **input_snapshot,
                "qualityRepair": {
                    "attempt": attempt,
                    "instruction": "이전 출력은 저장되지 않았습니다. validationErrors를 모두 반영해 완전한 MissionContent JSON 전체를 다시 반환하세요.",
                    "validationErrors": validation_errors,
                    "previousOutput": previous_output,
                },
            }

        output_json, token_usage = provider.create_json_response(
            model=settings.openai_reasoning_model,
            instructions=instructions,
            input_snapshot=generation_snapshot,
        )
        attempt_usages.append(token_usage)
        previous_output = output_json
        try:
            mission = _mission_from_generation(output_json, student_id=student_id, case_id=case_id)
            validate_mission_content_quality(mission, case_file=case_file, orchestrator_plan=orchestrator_plan)
            return mission, output_json, _merge_token_usage(attempt_usages)
        except ContentQualityError as exc:
            validation_errors = exc.issues
            if attempt == MAX_CONTENT_GENERATION_ATTEMPTS:
                raise
        except ValueError as exc:
            validation_errors = [str(exc)]
            if attempt == MAX_CONTENT_GENERATION_ATTEMPTS:
                raise

    raise ContentQualityError(["콘텐츠 생성 품질 재시도 흐름이 예기치 않게 종료되었습니다."])


def _merge_token_usage(attempt_usages: list[dict | None]) -> dict | None:
    if len(attempt_usages) == 1:
        return attempt_usages[0]
    return {"attempts": [{"attempt": index + 1, "tokenUsage": usage} for index, usage in enumerate(attempt_usages)]}
