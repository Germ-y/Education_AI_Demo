from fastapi import APIRouter, Depends, HTTPException

from app.ai.openai_provider import OpenAiProvider
from app.ai.prompt_registry import PROMPT_SPECS, load_prompt
from app.ai.provider_errors import AiProviderError
from app.api.deps import get_agent_run_repository, get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.domain.schemas import OrchestratorRunRequest
from app.repositories.agent_run_repository import AgentRunRepository
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/orchestrator-runs")
def create_orchestrator_run(
    payload: OrchestratorRunRequest,
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

    try:
        output_json, token_usage = OpenAiProvider(settings).create_json_response(
            model=settings.openai_reasoning_model,
            instructions=load_prompt("orchestrator_plan"),
            input_snapshot=input_snapshot,
        )
    except AiProviderError as exc:
        failed = agent_runs.mark_failed(agent_run.id, error_code=exc.code, error_message=exc.message, review_required=True)
        return ok({"agentRun": failed.model_dump(by_alias=True) if failed else None})

    succeeded = agent_runs.mark_succeeded(agent_run.id, output_json=output_json, token_usage=token_usage)
    return ok({"agentRun": succeeded.model_dump(by_alias=True) if succeeded else None})


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
