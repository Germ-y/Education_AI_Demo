import os

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_store_instance
from app.core.config import get_settings
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

    history = client.get("/api/teacher/students/student_learning_fraction/history", headers={"authorization": f"Bearer {teacher_token}"})
    assert history.status_code == 200
    assert history.json()["data"]["missionContents"][0]["studentId"] == "student_learning_fraction"

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


def test_http_errors_use_contract_envelope() -> None:
    client = TestClient(create_app())

    response = client.get("/api/teacher/students")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "UNAUTHORIZED",
            "message": "로그인이 필요합니다.",
            "details": {},
        }
    }
