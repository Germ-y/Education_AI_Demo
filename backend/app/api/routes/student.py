from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_store, require_student
from app.api.response import ok
from app.core.config import get_settings
from app.domain.schemas import AttemptRequest, ReflectionRequest, StageSubmitRequest
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/missions/today")
def today_missions(principal: SessionPrincipal = Depends(require_student), demo_store: DemoStore = Depends(get_store)) -> dict:
    student_id = _student_id(principal)
    missions = demo_store.list_published_missions_for_student(student_id)
    return ok(
        [
            {
                "contentId": mission.id,
                "title": mission.title,
                "contentType": mission.content_type,
                "totalSteps": mission.total_steps,
                "heroImageUrl": next((asset.preview_url for asset in mission.assets if asset.asset_role == "hero"), None),
                "heroAudioUrl": next((asset.preview_url for asset in mission.assets if asset.asset_role == "hero" and asset.asset_type == "audio"), None),
                "status": mission.status,
            }
            for mission in missions
        ]
    )


@router.get("/missions/{content_id}")
def get_mission(content_id: str, principal: SessionPrincipal = Depends(require_student), demo_store: DemoStore = Depends(get_store)) -> dict:
    mission = demo_store.get_published_mission_for_student(_student_id(principal), content_id)
    if mission is None:
        raise HTTPException(status_code=404, detail={"code": "MISSION_NOT_FOUND", "message": "배포된 미션을 찾을 수 없습니다."})
    return ok(mission.model_dump(by_alias=True))


@router.post("/missions/{content_id}/start")
def start_mission(content_id: str, principal: SessionPrincipal = Depends(require_student), demo_store: DemoStore = Depends(get_store)) -> dict:
    student_id = _student_id(principal)
    mission = demo_store.get_published_mission_for_student(student_id, content_id)
    if mission is None:
        raise HTTPException(status_code=404, detail={"code": "MISSION_NOT_FOUND", "message": "배포된 미션을 찾을 수 없습니다."})
    return ok(demo_store.create_attempt(student_id, content_id).model_dump(by_alias=True))


@router.post("/missions/{content_id}/stages/{stage_id}/submit")
def submit_stage(
    content_id: str,
    stage_id: str,
    payload: StageSubmitRequest,
    principal: SessionPrincipal = Depends(require_student),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    result = demo_store.submit_stage(_student_id(principal), content_id, stage_id, payload.attempt_id, payload.answer)
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "STAGE_NOT_FOUND", "message": "제출할 단계를 찾을 수 없습니다."})
    if result.get("isRealtimeStage"):
        raise HTTPException(status_code=400, detail={"code": "REALTIME_STAGE_SUBMIT_BLOCKED", "message": "4단계는 realtime-session API를 사용해야 합니다."})
    return ok(result)


@router.post("/missions/{content_id}/stages/{stage_id}/realtime-session")
def create_realtime_session(
    content_id: str,
    stage_id: str,
    payload: AttemptRequest,
    principal: SessionPrincipal = Depends(require_student),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    student_id = _student_id(principal)
    session = demo_store.create_realtime_session(student_id, content_id, stage_id, payload.attempt_id)
    if session is None:
        raise HTTPException(status_code=400, detail={"code": "REALTIME_SESSION_NOT_ALLOWED", "message": "승인된 4단계 realtime 스펙이 필요합니다."})
    mission = demo_store.get_published_mission_for_student(student_id, content_id)
    spec = session.spec_snapshot_json
    image_asset = next((asset for asset in mission.assets if asset.id == spec.get("imageAssetId")), None) if mission else None
    audio_asset = (
        next((asset for asset in mission.assets if asset.asset_role == "stage_4_realtime" and asset.asset_type == "audio"), None) if mission else None
    )
    settings = get_settings()
    return ok(
        {
            "sessionId": session.id,
            "provider": session.provider,
            "model": session.model,
            "clientSecret": f"server-issued-{session.id}" if settings.openai_api_key else f"demo-client-secret-{session.id}",
            "expiresAt": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
            "webrtcUrl": "https://api.openai.com/v1/realtime/calls",
            "practiceSpec": {
                "practiceTitle": spec.get("practiceTitle"),
                "imageAssetUrl": image_asset.preview_url if image_asset else None,
                "openingAudioUrl": audio_asset.preview_url if audio_asset else None,
                "openingLine": spec.get("openingLine"),
                "maxTurns": spec.get("maxTurns"),
                "maxDurationSec": spec.get("maxDurationSec"),
            },
        }
    )


@router.post("/missions/{content_id}/post-practice-reflection")
def save_reflection(
    content_id: str,
    payload: ReflectionRequest,
    principal: SessionPrincipal = Depends(require_student),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    saved = demo_store.save_reflection(
        _student_id(principal), content_id, payload.attempt_id, payload.reflection_choice, payload.short_text
    )
    if saved is None:
        raise HTTPException(status_code=404, detail={"code": "ATTEMPT_NOT_FOUND", "message": "진행 중인 시도를 찾을 수 없습니다."})
    return ok(saved)


@router.post("/missions/{content_id}/complete")
def complete_mission(
    content_id: str,
    payload: AttemptRequest,
    principal: SessionPrincipal = Depends(require_student),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    completed = demo_store.complete_attempt(_student_id(principal), content_id, payload.attempt_id)
    if completed is None:
        raise HTTPException(status_code=404, detail={"code": "ATTEMPT_NOT_FOUND", "message": "진행 중인 시도를 찾을 수 없습니다."})
    return ok(completed.model_dump(by_alias=True))


def _student_id(principal: SessionPrincipal) -> str:
    if principal.student_id is None:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "학생 권한이 필요합니다."})
    return principal.student_id
