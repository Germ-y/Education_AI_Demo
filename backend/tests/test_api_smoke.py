import os

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_store_instance
from app.ai.elevenlabs_provider import ElevenLabsProvider
from app.ai.openai_provider import OpenAiProvider
from app.core.config import get_settings
from app.data.demo_data import create_demo_database
from app.db.session import get_engine, get_session_maker
from app.main import create_app


@pytest.fixture(autouse=True)
def use_sqlite_demo_db(tmp_path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{tmp_path / 'eduyj-test.db'}"
    os.environ["DEMO_SEED_MODE"] = "true"
    os.environ["DEMO_SEED_RESET"] = "true"
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["ELEVENLABS_API_KEY"] = ""
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_maker.cache_clear()
    get_store_instance.cache_clear()
    yield
    get_store_instance.cache_clear()
    get_session_maker.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


def test_teacher_and_student_demo_flows() -> None:
    client = TestClient(create_app())

    seed_context = client.get("/api/context/seed")
    assert seed_context.status_code == 200
    assert seed_context.json()["data"]["teacher"]["id"] == "user_teacher_demo"
    assert len(seed_context.json()["data"]["students"]) == 3
    assert {mapping["studentId"] for mapping in seed_context.json()["data"]["assignments"]} == {
        "student_learning_clock",
        "student_learning_fraction",
        "student_life_bus",
    }

    teacher_login = client.post(
        "/api/auth/demo-login",
        json={"role": "teacher", "email": "teacher.demo@eduyj.local"},
    )
    assert teacher_login.status_code == 200
    teacher_token = teacher_login.json()["data"]["session"]["accessToken"]

    students = client.get("/api/teacher/students", headers={"authorization": f"Bearer {teacher_token}"})
    assert students.status_code == 200
    assert len(students.json()["data"]) == 3
    assert {student["schoolName"] for student in students.json()["data"]} == {"영주중앙초등학교", "영주중학교", "영주가흥초등학교"}

    no_token_students = client.get("/api/teacher/students")
    assert no_token_students.status_code == 200
    assert len(no_token_students.json()["data"]) == 3

    school_context = client.get("/api/public-data/schools/8811058/context", headers={"authorization": f"Bearer {teacher_token}"})
    assert school_context.status_code == 200
    assert school_context.json()["data"]["school"]["schoolName"] == "영주중학교"
    assert school_context.json()["data"]["calendar"]

    timetable_context = client.get(
        "/api/public-data/schools/8811058/context?timetableDate=2026-05-01&grade=2&className=1",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert timetable_context.status_code == 200
    timetable = timetable_context.json()["data"]["timetableSummary"]
    assert [slot["subjectName"] for slot in timetable] == ["역사", "동아리활동", "진로와 직업", "국어", "과학", "도덕"]
    public_sync = client.post(
        "/api/public-data/sources/neis_open_api/sync",
        headers={"authorization": f"Bearer {teacher_token}"},
        json={"officeCode": "R10", "schoolCode": "8811058", "fromDate": "2026-05-01", "toDate": "2026-05-15"},
    )
    assert public_sync.status_code == 424
    assert public_sync.json()["error"]["code"] == "NEIS_API_KEY_MISSING"
    assert public_sync.json()["error"]["details"] == {"reviewRequired": True, "fallbackPolicy": "disabled"}

    history = client.get("/api/teacher/students/student_learning_fraction/history", headers={"authorization": f"Bearer {teacher_token}"})
    assert history.status_code == 200
    assert history.json()["data"]["missionContents"][0]["studentId"] == "student_learning_fraction"

    teacher_content = client.get("/api/contents/content_fraction_001", headers={"authorization": f"Bearer {teacher_token}"})
    assert teacher_content.status_code == 200
    content_payload = teacher_content.json()["data"]
    asset_generation = client.post(
        "/api/contents/content_fraction_001/assets/asset_content_fraction_001_stage_2_audio/generate",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert asset_generation.status_code == 424
    assert asset_generation.json()["error"]["code"] == "ELEVENLABS_API_KEY_MISSING"
    package_generation = client.post(
        "/api/contents/content_fraction_001/assets/generate-package",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert package_generation.status_code == 424
    assert package_generation.json()["error"]["code"] == "OPENAI_API_KEY_MISSING"
    assert package_generation.json()["error"]["details"] == {"reviewRequired": True, "fallbackPolicy": "disabled"}
    approve = client.post(
        "/api/contents/content_fraction_001/approve",
        headers={"authorization": f"Bearer {teacher_token}"},
        json={
            "approvedStageIds": [stage["id"] for stage in content_payload["stages"]],
            "approvedAssetIds": [asset["id"] for asset in content_payload["assets"]],
            "reviewNote": "데모 검수 완료",
        },
    )
    assert approve.status_code == 200
    assert approve.json()["data"]["status"] == "approved"
    publish = client.post("/api/contents/content_fraction_001/publish", headers={"authorization": f"Bearer {teacher_token}"})
    assert publish.status_code == 200
    assert publish.json()["data"]["status"] == "published"
    content_audit = client.get(
        "/api/audit-logs?studentId=student_learning_fraction",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert content_audit.status_code == 200
    assert {"approve_content", "publish_content"}.issubset({log["action"] for log in content_audit.json()["data"]})

    note = client.post(
        "/api/teacher/students/student_learning_fraction/notes",
        headers={"authorization": f"Bearer {teacher_token}"},
        json={"noteType": "teacher_comment", "body": "다음 회기에는 전체 수 먼저 세기.", "visibility": "teacher_only"},
    )
    assert note.status_code == 200
    assert note.json()["data"]["caseId"] == "case_learning_fraction"

    student_login = client.post("/api/auth/student-access", json={"accessCode": "STAR-001"})
    assert student_login.status_code == 200
    student_token = student_login.json()["data"]["session"]["accessToken"]

    today = client.get("/api/student/missions/today", headers={"authorization": f"Bearer {student_token}"})
    assert today.status_code == 200
    assert today.json()["data"][0]["totalSteps"] == 4
    assert today.json()["data"][0]["heroAudioUrl"].endswith("/hero.mp3")

    mission_detail = client.get("/api/student/missions/content_fraction_001", headers={"authorization": f"Bearer {student_token}"})
    assert mission_detail.status_code == 200
    assets = mission_detail.json()["data"]["assets"]
    assert len([asset for asset in assets if asset["assetType"] == "image"]) == 5
    assert len([asset for asset in assets if asset["assetType"] == "audio"]) == 5
    assert mission_detail.json()["data"]["stages"][0]["templateJson"]["assetBundle"]["audioAssetId"].endswith("_audio")

    start = client.post(
        "/api/student/missions/content_fraction_001/start",
        headers={"authorization": f"Bearer {student_token}"},
    )
    assert start.status_code == 200
    attempt_id = start.json()["data"]["id"]

    event = client.post(
        "/api/student/missions/content_fraction_001/events",
        headers={"authorization": f"Bearer {student_token}"},
        json={
            "attemptId": attempt_id,
            "stageId": "stage_fraction_1",
            "eventType": "stage_entered",
            "payloadJson": {"step": 1},
        },
    )
    assert event.status_code == 200
    assert event.json()["data"]["eventType"] == "stage_entered"

    submit = client.post(
        "/api/student/missions/content_fraction_001/stages/stage_fraction_2/submit",
        headers={"authorization": f"Bearer {student_token}"},
        json={"attemptId": attempt_id, "answer": {"choiceId": "b"}},
    )
    assert submit.status_code == 200
    assert submit.json()["data"]["isCorrect"] is True

    realtime = client.post(
        "/api/student/missions/content_fraction_001/stages/stage_fraction_4/realtime-session",
        headers={"authorization": f"Bearer {student_token}"},
        json={"attemptId": attempt_id},
    )
    assert realtime.status_code == 424
    assert realtime.json()["error"]["code"] == "OPENAI_API_KEY_MISSING"
    assert realtime.json()["error"]["details"] == {"reviewRequired": True, "fallbackPolicy": "disabled"}

    reflection = client.post(
        "/api/student/missions/content_fraction_001/post-practice-reflection",
        headers={"authorization": f"Bearer {student_token}"},
        json={"attemptId": attempt_id, "reflectionChoice": "조금 헷갈렸어요", "shortText": "아래 숫자가 전체인 게 헷갈렸어요."},
    )
    assert reflection.status_code == 200
    complete = client.post(
        "/api/student/missions/content_fraction_001/complete",
        headers={"authorization": f"Bearer {student_token}"},
        json={"attemptId": attempt_id},
    )
    assert complete.status_code == 200

    review_summary = client.post("/api/contents/content_fraction_001/review-summary", headers={"authorization": f"Bearer {teacher_token}"})
    assert review_summary.status_code == 200
    assert review_summary.json()["data"]["studentId"] == "student_learning_fraction"
    assert review_summary.json()["data"]["accuracyRate"] == 1
    latest_review_summary = client.get("/api/contents/content_fraction_001/review-summary", headers={"authorization": f"Bearer {teacher_token}"})
    assert latest_review_summary.status_code == 200
    assert latest_review_summary.json()["data"]["id"] == review_summary.json()["data"]["id"]
    applied_memory = client.post(
        f"/api/review-summaries/{review_summary.json()['data']['id']}/apply-to-memory",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert applied_memory.status_code == 200
    assert applied_memory.json()["data"]["recent4wResponseJson"]["latestReviewSummaryId"] == review_summary.json()["data"]["id"]
    memory_audit = client.get(
        "/api/audit-logs?action=apply_review_to_memory",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert memory_audit.status_code == 200
    assert memory_audit.json()["data"][0]["resourceId"] == review_summary.json()["data"]["id"]

    orchestrator = client.post(
        "/api/ai/orchestrator-runs",
        headers={"authorization": f"Bearer {teacher_token}"},
        json={
            "studentId": "student_learning_fraction",
            "caseId": "case_learning_fraction",
            "requestedGoal": "분수의 전체-부분 관계를 이해한다.",
            "contentType": "learning_focus",
        },
    )
    assert orchestrator.status_code == 200
    agent_run = orchestrator.json()["data"]["agentRun"]
    assert agent_run["status"] == "failed"
    assert agent_run["errorCode"] == "OPENAI_API_KEY_MISSING"
    assert agent_run["reviewRequired"] is True
    assert agent_run["outputJson"] is None

    agent_run_detail = client.get(f"/api/ai/agent-runs/{agent_run['id']}", headers={"authorization": f"Bearer {teacher_token}"})
    assert agent_run_detail.status_code == 200
    assert agent_run_detail.json()["data"]["id"] == agent_run["id"]

    content_generation = client.post(
        "/api/ai/content-generations",
        headers={"authorization": f"Bearer {teacher_token}"},
        json={
            "orchestratorRunId": agent_run["id"],
            "studentId": "student_learning_fraction",
            "caseId": "case_learning_fraction",
        },
    )
    assert content_generation.status_code == 409
    assert content_generation.json()["error"]["code"] == "ORCHESTRATOR_RUN_NOT_READY"


def test_http_errors_use_contract_envelope() -> None:
    client = TestClient(create_app())

    response = client.get("/api/teacher/students", headers={"authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "UNAUTHORIZED",
            "message": "로그인이 필요합니다.",
            "details": {},
        }
    }


def test_ai_generation_workflow_returns_mission_content_and_assets(monkeypatch, tmp_path) -> None:
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["ELEVENLABS_API_KEY"] = "test-elevenlabs-key"
    os.environ["ELEVENLABS_VOICE_ID"] = "test-voice-id"
    os.environ["GENERATED_ASSETS_DIR"] = str(tmp_path / "generated")
    get_settings.cache_clear()

    generated_content = create_demo_database().mission_contents[0].model_dump(by_alias=True)
    generated_content["id"] = "content_generated_contract_001"
    generated_content["status"] = "teacher_review"
    generated_content["approvedByUserId"] = None
    generated_content["approvedAt"] = None
    generated_content["publishedAt"] = None
    generated_content["briefJson"]["difficulty"] = "기초"
    for stage in generated_content["stages"]:
        stage["id"] = f"stage_generated_contract_{stage['step']}"
        stage["missionContentId"] = generated_content["id"]
        image_role = "stage_4_realtime" if stage["step"] == 4 else f"stage_{stage['step']}"
        stage["templateJson"]["imageAssetId"] = f"asset_{generated_content['id']}_{image_role}"
        stage["templateJson"]["audioAssetId"] = f"asset_{generated_content['id']}_{image_role}_audio"
        if stage.get("realtimeSpec"):
            stage["realtimeSpec"]["id"] = "rt_spec_generated_contract_001"
            stage["realtimeSpec"]["stageId"] = stage["id"]
            stage["realtimeSpec"]["imageAssetId"] = stage["templateJson"]["imageAssetId"]
    for asset in generated_content["assets"]:
        asset["missionContentId"] = generated_content["id"]
        asset["stageId"] = None if asset["assetRole"] == "hero" else f"stage_generated_contract_{4 if asset['assetRole'] == 'stage_4_realtime' else asset['assetRole'][-1]}"
        asset["id"] = f"asset_{generated_content['id']}_{asset['assetRole']}{'_audio' if asset['assetType'] == 'audio' else ''}"
        asset["promptJson"] = asset.get("promptJson") or {}
        if asset["assetType"] == "image":
            asset["promptJson"]["prompt"] = f"{asset['assetRole']} scene only, no problem text"
        asset["storageUrl"] = ""
        asset["previewUrl"] = None
        asset["qaStatus"] = "pending"
        asset["approvalStatus"] = "pending"

    def fake_json_response(self, *, model, instructions, input_snapshot, timeout_sec=90):
        if "MissionContent" in instructions:
            return generated_content, {"input_tokens": 10, "output_tokens": 20}
        return (
            {
                "sessionGoal": input_snapshot["requestedGoal"],
                "selectedFlow": ["concept_intro", "image_quiz", "blank_fill", "realtime_teach_back"],
                "teacherSummary": "테스트 오케스트레이터 계획",
            },
            {"input_tokens": 5, "output_tokens": 8},
        )

    def fake_image_file(self, *, prompt, output_path, model, size="1536x1024", timeout_sec=180):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"png")
        return output_path

    def fake_speech_file(self, *, source_text, output_path, timeout_sec=60):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"mp3")
        return output_path

    monkeypatch.setattr(OpenAiProvider, "create_json_response", fake_json_response)
    monkeypatch.setattr(OpenAiProvider, "create_image_file", fake_image_file)
    monkeypatch.setattr(ElevenLabsProvider, "create_speech_file", fake_speech_file)

    client = TestClient(create_app())

    orchestrator = client.post(
        "/api/ai/orchestrator-runs",
        json={
            "studentId": "student_learning_fraction",
            "caseId": "case_learning_fraction",
            "requestedGoal": "[난이도: 기초] 전체 4개 중 1개를 1/4로 표현한다.",
            "contentType": "learning_focus",
        },
    )
    assert orchestrator.status_code == 200
    orchestrator_run = orchestrator.json()["data"]["agentRun"]
    assert orchestrator_run["status"] == "succeeded"

    content_generation = client.post(
        "/api/ai/content-generations",
        json={
            "orchestratorRunId": orchestrator_run["id"],
            "studentId": "student_learning_fraction",
            "caseId": "case_learning_fraction",
        },
    )
    assert content_generation.status_code == 200
    content = content_generation.json()["data"]["content"]
    assert content["id"] == "content_generated_contract_001"
    assert content["status"] == "teacher_review"
    assert content["totalSteps"] == 4
    assert [stage["step"] for stage in content["stages"]] == [1, 2, 3, 4]
    assert len([asset for asset in content["assets"] if asset["assetType"] == "image"]) == 5
    assert len([asset for asset in content["assets"] if asset["assetType"] == "audio"]) == 5

    package = client.post("/api/contents/content_generated_contract_001/assets/generate-package")
    assert package.status_code == 200
    package_data = package.json()["data"]
    assert package_data["generatedCount"] == 10
    assert all(asset["storageUrl"].startswith("/generated/assets/content_generated_contract_001/") for asset in package_data["assets"])

    reviewable = client.get("/api/contents/content_generated_contract_001")
    assert reviewable.status_code == 200
    assert reviewable.json()["data"]["assets"][0]["previewUrl"].startswith("/generated/assets/content_generated_contract_001/")
