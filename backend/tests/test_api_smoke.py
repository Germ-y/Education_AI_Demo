import copy
import os

import pytest
from fastapi.testclient import TestClient

from app.ai.elevenlabs_provider import ElevenLabsProvider
from app.ai.openai_provider import OpenAiProvider
from app.api.deps import get_store_instance
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
    os.environ["NEIS_API_KEY"] = ""
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_maker.cache_clear()
    get_store_instance.cache_clear()
    yield
    get_store_instance.cache_clear()
    get_session_maker.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


def assert_no_teacher_raw_terms(payload: object) -> None:
    forbidden_terms = ("teach-back", "teach_back", "teach back", "realtime", "Realtime", "roleplay", "role-play")
    if isinstance(payload, str):
        for term in forbidden_terms:
            assert term not in payload
        return
    if isinstance(payload, list):
        for item in payload:
            assert_no_teacher_raw_terms(item)
        return
    if isinstance(payload, dict):
        for value in payload.values():
            assert_no_teacher_raw_terms(value)


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
    assert {student["displayName"] for student in students.json()["data"]} == {"김지우", "이민준", "박수민"}
    clock_student = next(student for student in students.json()["data"] if student["studentId"] == "student_learning_clock")
    assert clock_student["displayName"] == "김지우"
    assert clock_student["gradeLabel"] == "초3"
    assert clock_student["trackLabel"] == "저연령 학습지원형"
    assert clock_student["dashboardStageLabel"] == "자료 생성"
    assert clock_student["attendanceLabel"] == "기록 전"
    assert "시간 읽기 기초" in clock_student["primaryNeed"]
    assert "좋겠어요" in clock_student["primaryNeed"]
    assert "시간 읽기 기초" in clock_student["summaryLine"]
    assert clock_student["strengths"][0] == "그림에서 중요한 단서를 먼저 찾으면 바로 반응해요."
    assert clock_student["weaknesses"][0] == "문장이 길어지면 무엇부터 해야 할지 멈칫할 수 있어요."
    assert_no_teacher_raw_terms(
        [
            [
                student["supportStrategy"],
                student["summaryLine"],
                student["aiContextSummary"],
                student["nextSessionSuggestion"],
            ]
            for student in students.json()["data"]
        ]
    )

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
    timetable_cache = client.get(
        "/api/public-data/schools/8811058/timetable?date=2026-05-01&grade=2&className=1",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert timetable_cache.status_code == 200
    assert timetable_cache.json()["data"]["source"]["cacheStatus"] == "cached_snapshot"
    assert timetable_cache.json()["data"]["orchestratorHints"]
    elementary_timetable_cache = client.get(
        "/api/public-data/schools/8811046/timetable?date=2026-05-01&grade=3&className=1",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert elementary_timetable_cache.status_code == 200
    assert [slot["subjectName"] for slot in elementary_timetable_cache.json()["data"]["slots"]] == [
        "국어",
        "수학",
        "사회",
        "과학",
        "창의적체험활동",
    ]
    missing_timetable = client.get(
        "/api/public-data/schools/8811046/timetable?date=2026-05-03&grade=3&className=1&syncIfMissing=false",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert missing_timetable.status_code == 200
    assert missing_timetable.json()["data"]["slots"] == []
    assert missing_timetable.json()["data"]["source"]["cacheStatus"] == "empty"
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
    fraction_case = client.get("/api/teacher/students/student_learning_fraction", headers={"authorization": f"Bearer {teacher_token}"})
    assert fraction_case.status_code == 200
    assert fraction_case.json()["data"]["profile"]["displayName"] == "이민준"
    assert fraction_case.json()["data"]["dashboardProfile"]["headline"] == "영주중학교 · 중2 · 고연령 학습지원형"
    assert fraction_case.json()["data"]["dashboardProfile"]["primaryNeedTitle"] == "분수 개념 보완 수업"
    assert "수업이 좋겠어요" in fraction_case.json()["data"]["dashboardProfile"]["primaryNeedDetail"]
    assert "말로 정리하기" in fraction_case.json()["data"]["dashboardProfile"]["supportStrategyDetail"]
    assert "좋겠어요" in fraction_case.json()["data"]["dashboardProfile"]["supportStrategyDetail"]
    assert fraction_case.json()["data"]["dashboardProfile"]["strengths"][0] == "그림이나 조각 모델을 보면 전체와 부분을 더 쉽게 이해해요."
    assert fraction_case.json()["data"]["dashboardProfile"]["weaknesses"][0] == "분모와 분자가 각각 무엇을 뜻하는지 자주 바꿔 생각해요."
    assert_no_teacher_raw_terms(fraction_case.json()["data"]["dashboardProfile"])
    life_case = client.get("/api/teacher/students/student_life_bus", headers={"authorization": f"Bearer {teacher_token}"})
    assert life_case.status_code == 200
    assert life_case.json()["data"]["dashboardProfile"]["primaryNeedTitle"] == "일상생활 의사소통 수업"
    assert "실시간 역할 발화 연습" in life_case.json()["data"]["dashboardProfile"]["supportStrategyDetail"]
    assert life_case.json()["data"]["dashboardProfile"]["strengths"][0] == "상황 그림을 보면 지금 어디서 무엇을 해야 하는지 잘 파악해요."
    assert life_case.json()["data"]["dashboardProfile"]["weaknesses"][0] == "여러 이동 단계를 한 번에 정리하면 순서가 헷갈릴 수 있어요."
    assert_no_teacher_raw_terms(life_case.json()["data"]["dashboardProfile"])
    context_bundle = client.get(
        "/api/teacher/students/student_learning_fraction/context-bundle",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert context_bundle.status_code == 200
    bundle = context_bundle.json()["data"]
    assert bundle["student"]["gradeLabel"] == "중2"
    assert bundle["student"]["name"] == "이민준"
    assert bundle["student"]["displayName"] == "이민준"
    assert "개념 보완 수업" in bundle["caseSummary"]["primaryNeed"]
    assert bundle["schoolContext"]["timetableSummary"]["todaySubjects"] == ["역사", "동아리활동", "진로와 직업", "국어", "과학", "도덕"]
    assert [item["label"] for item in bundle["autoContext"]] == ["학생 기록", "이전 수업", "학교 시간표", "다음 목표"]
    assert bundle["aiReadyContext"]["evidenceSources"]
    assert_no_teacher_raw_terms(
        [
            bundle["caseSummary"],
            bundle["autoContext"],
            bundle["aiReadyContext"]["summary"],
            bundle["aiReadyContext"]["mustUse"],
        ]
    )
    clock_bundle = client.get(
        "/api/teacher/students/student_learning_clock/context-bundle",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert clock_bundle.status_code == 200
    clock_auto_context = clock_bundle.json()["data"]["autoContext"]
    assert [item["label"] for item in clock_auto_context] == ["학생 기록", "학교 시간표", "다음 목표"]
    assert "이전 수행 기록 없음" not in {item["value"] for item in clock_auto_context}
    life_bundle = client.get(
        "/api/teacher/students/student_life_bus/context-bundle",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert life_bundle.status_code == 200
    assert life_bundle.json()["data"]["schoolContext"]["timetableSummary"]["todaySubjects"] == ["국어", "수학", "사회", "실과", "미술"]
    report = client.get("/api/teacher/students/student_learning_fraction/report", headers={"authorization": f"Bearer {teacher_token}"})
    assert report.status_code == 200
    assert report.json()["data"]["reports"][0]["studentId"] == "student_learning_fraction"
    assert "Completed" not in report.json()["data"]["reports"][0]["shortSummary"]

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
    expected_approved_status = "published" if content_payload["status"] == "published" else "approved"
    assert approve.json()["data"]["status"] == expected_approved_status
    publish = client.post("/api/contents/content_fraction_001/publish", headers={"authorization": f"Bearer {teacher_token}"})
    assert publish.status_code == 200
    assert publish.json()["data"]["status"] == "published"
    reapprove = client.post(
        "/api/contents/content_fraction_001/approve",
        headers={"authorization": f"Bearer {teacher_token}"},
        json={
            "approvedStageIds": [stage["id"] for stage in content_payload["stages"]],
            "approvedAssetIds": [asset["id"] for asset in content_payload["assets"]],
            "reviewNote": "배포 후 재검수",
        },
    )
    assert reapprove.status_code == 200
    assert reapprove.json()["data"]["status"] == "published"
    assert reapprove.json()["data"]["publishedAt"] is not None
    students_after_publish = client.get("/api/teacher/students", headers={"authorization": f"Bearer {teacher_token}"})
    assert students_after_publish.status_code == 200
    fraction_student_after_publish = next(
        item for item in students_after_publish.json()["data"] if item["studentId"] == "student_learning_fraction"
    )
    assert fraction_student_after_publish["dashboardStage"] == "learning"
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
    report_after_complete = client.get(
        "/api/teacher/students/student_learning_fraction/report",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    assert report_after_complete.status_code == 200
    assert report_after_complete.json()["data"]["reports"][0]["attemptId"] == attempt_id
    students_after_complete = client.get("/api/teacher/students", headers={"authorization": f"Bearer {teacher_token}"})
    assert students_after_complete.status_code == 200
    fraction_student_after_complete = next(
        item for item in students_after_complete.json()["data"] if item["studentId"] == "student_learning_fraction"
    )
    assert fraction_student_after_complete["dashboardStage"] == "feedback"

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
    assert agent_run["status"] == "running"

    agent_run_detail = client.get(f"/api/ai/agent-runs/{agent_run['id']}", headers={"authorization": f"Bearer {teacher_token}"})
    assert agent_run_detail.status_code == 200
    agent_run_detail_data = agent_run_detail.json()["data"]
    assert agent_run_detail_data["id"] == agent_run["id"]
    assert agent_run_detail_data["status"] == "failed"
    assert agent_run_detail_data["errorCode"] == "OPENAI_API_KEY_MISSING"
    assert agent_run_detail_data["reviewRequired"] is True
    assert agent_run_detail_data["outputJson"] is None

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


def test_teacher_can_persist_content_review_edits() -> None:
    client = TestClient(create_app())
    teacher_login = client.post(
        "/api/auth/demo-login",
        json={"role": "teacher", "email": "teacher.demo@eduyj.local"},
    )
    teacher_token = teacher_login.json()["data"]["session"]["accessToken"]

    response = client.patch(
        "/api/contents/content_clock_001/review",
        headers={"authorization": f"Bearer {teacher_token}"},
        json={
            "stages": [
                {
                    "stageId": "stage_clock_2",
                    "studentInstruction": "수정된 시계 문제 설명",
                    "question": "수정된 시계 문제를 골라요.",
                    "choices": ["4시", "6시", "9시"],
                }
            ]
        },
    )

    assert response.status_code == 200
    stage = next(stage for stage in response.json()["data"]["stages"] if stage["id"] == "stage_clock_2")
    assert stage["studentInstruction"] == "수정된 시계 문제 설명"
    assert stage["templateJson"]["question"] == "수정된 시계 문제를 골라요."
    assert stage["templateJson"]["choices"][0]["text"] == "4시"
    assert stage["templateJson"]["answer"] == "a"

    persisted = client.get(
        "/api/contents/content_clock_001",
        headers={"authorization": f"Bearer {teacher_token}"},
    )
    persisted_stage = next(stage for stage in persisted.json()["data"]["stages"] if stage["id"] == "stage_clock_2")
    assert persisted_stage["templateJson"]["choices"][0]["text"] == "4시"


def test_completed_mission_stays_completed_after_restart() -> None:
    client = TestClient(create_app())
    student_login = client.post("/api/auth/student-access", json={"accessCode": "STAR-003"})
    student_token = student_login.json()["data"]["session"]["accessToken"]
    content_id = "content_clock_001"

    first_attempt = client.post(
        f"/api/student/missions/{content_id}/start",
        headers={"authorization": f"Bearer {student_token}"},
    ).json()["data"]
    completed = client.post(
        f"/api/student/missions/{content_id}/complete",
        headers={"authorization": f"Bearer {student_token}"},
        json={"attemptId": first_attempt["id"]},
    )
    assert completed.status_code == 200

    restarted = client.post(
        f"/api/student/missions/{content_id}/start",
        headers={"authorization": f"Bearer {student_token}"},
    )
    assert restarted.status_code == 200

    seed_context = client.get("/api/context/seed").json()["data"]
    mapping = next(mapping for mapping in seed_context["missionMappings"] if mapping["contentId"] == content_id)
    assert mapping["latestAttemptStatus"] == "in_progress"
    assert mapping["isCompleted"] is True


def test_ai_generation_workflow_returns_mission_content_and_assets(monkeypatch, tmp_path) -> None:
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["ELEVENLABS_API_KEY"] = "test-elevenlabs-key"
    os.environ["ELEVENLABS_VOICE_ID"] = "test-voice-id"
    os.environ["GENERATED_ASSETS_DIR"] = str(tmp_path / "generated")
    get_settings.cache_clear()

    seed = create_demo_database()
    base_content = next(content for content in seed.mission_contents if content.student_id == "student_learning_fraction")
    generated_content = base_content.model_dump(by_alias=True)
    student_id = base_content.student_id
    case_id = base_content.case_id
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
        stage["templateJson"]["assetBundle"] = {
            "imageAssetId": stage["templateJson"]["imageAssetId"],
            "audioAssetId": stage["templateJson"]["audioAssetId"],
        }
        if stage.get("realtimeSpec"):
            stage["realtimeSpec"]["id"] = "rt_spec_generated_contract_001"
            stage["realtimeSpec"]["stageId"] = stage["id"]
            stage["realtimeSpec"]["imageAssetId"] = stage["templateJson"]["imageAssetId"]
    for asset in generated_content["assets"]:
        asset["missionContentId"] = generated_content["id"]
        asset_step = 4 if asset["assetRole"] == "stage_4_realtime" else asset["assetRole"][-1]
        asset["stageId"] = None if asset["assetRole"] == "hero" else f"stage_generated_contract_{asset_step}"
        asset["id"] = f"asset_{generated_content['id']}_{asset['assetRole']}{'_audio' if asset['assetType'] == 'audio' else ''}"
        asset["promptJson"] = asset.get("promptJson") or {}
        if asset["assetType"] == "image":
            asset["promptJson"] = {
                "prompt": f"{asset['assetRole']} 장면. 따뜻한 교실 느낌의 피자 조각 장면만 보여주고 문제 문장, 선택지, 정답, 힌트 텍스트는 넣지 않습니다.",
                "textRenderingPolicy": "scene_only_no_problem_text",
            }
        asset["storageUrl"] = ""
        asset["previewUrl"] = None
        asset["qaStatus"] = "pending"
        asset["approvalStatus"] = "pending"

    invalid_generated_content = copy.deepcopy(generated_content)
    invalid_generated_content["stages"][3]["studentTitle"] = "realtime practice"
    content_generation_calls = {"count": 0}
    image_brief_calls = {"count": 0}

    def fake_json_response(self, *, model, instructions, input_snapshot, timeout_sec=90):
        if "Image Prompt Builder" in instructions:
            image_brief_calls["count"] += 1
            return (
                {
                    "promptVersion": "image_brief_v1",
                    "contentId": generated_content["id"],
                    "imageBriefs": [
                        {
                            "assetRole": asset["assetRole"],
                            "stageId": asset["stageId"],
                            "prompt": (
                                f"{asset['assetRole']} 전용 장면. 학생이 볼 수 있는 구체적인 피자 조각 상황만 "
                                "고품질 한국 교육 일러스트로 보여주고, 문제 문장, 선택지, 정답, 힌트 텍스트는 넣지 않습니다."
                            ),
                            "negativePromptRules": ["no problem statements", "no answer choices", "no UI cards", "no speech bubbles"],
                            "ocrRequired": False,
                            "qaChecklist": ["scene matches stage purpose", "no UI text embedded", "student-safe tone"],
                        }
                        for asset in generated_content["assets"]
                        if asset["assetType"] == "image"
                    ],
                },
                {"input_tokens": 3, "output_tokens": 5},
            )
        if "Content Quality Critic" in instructions:
            return (
                {
                    "critiqueVersion": "content_quality_critique_v1",
                    "verdict": "pass",
                    "issues": [],
                    "repairInstruction": "",
                },
                {"input_tokens": 4, "output_tokens": 4},
            )
        if "MissionContent" in instructions:
            content_generation_calls["count"] += 1
            if content_generation_calls["count"] == 1:
                assert "qualityRepair" not in input_snapshot
                return invalid_generated_content, {"input_tokens": 10, "output_tokens": 20}
            assert input_snapshot["qualityRepair"]["validationErrors"]
            return generated_content, {"input_tokens": 10, "output_tokens": 20}
        return (
            {
                "planVersion": "orchestrator_plan_v1",
                "studentId": student_id,
                "caseId": case_id,
                "contentType": "learning_focus",
                "sessionGoal": input_snapshot["requestedGoal"],
                "targetSkill": "분모와 분자의 의미 연결",
                "difficultyPolicy": {"level": "easy_success", "reason": "시각 자료로 쉬운 성공 경험부터 시작합니다."},
                "selectedStrategy": ["short visual explanation", "teach-back"],
                "stagePlan": [
                    {
                        "step": 1,
                        "stageRole": "concept_intro",
                        "templateType": "concept_intro",
                        "studentTitle": "개념 열기",
                        "purpose": "전체와 부분을 그림으로 확인합니다.",
                    },
                    {
                        "step": 2,
                        "stageRole": "basic_problem",
                        "templateType": "partition_picker",
                        "studentTitle": "문제 1",
                        "purpose": "전체 조각 수를 먼저 세게 합니다.",
                    },
                    {
                        "step": 3,
                        "stageRole": "applied_problem",
                        "templateType": "blank_fill",
                        "studentTitle": "문제 2",
                        "purpose": "고른 수와 전체 수를 분수 자리에 연결합니다.",
                    },
                    {
                        "step": 4,
                        "stageRole": "realtime_practice",
                        "templateType": "realtime_teach_back",
                        "studentTitle": "설명해보기",
                        "purpose": "왜 1/4인지 짧게 말해봅니다.",
                    },
                ],
                "imagePackageIntent": [
                    {"assetRole": "hero", "scenePurpose": "시작 장면", "mustShow": ["피자 조각"], "mustNotShow": ["problem text"]},
                    {"assetRole": "stage_1", "scenePurpose": "전체 확인", "mustShow": ["전체 피자"], "mustNotShow": ["problem text"]},
                    {"assetRole": "stage_2", "scenePurpose": "조각 세기", "mustShow": ["네 조각"], "mustNotShow": ["problem text"]},
                    {"assetRole": "stage_3", "scenePurpose": "분수 연결", "mustShow": ["한 조각 강조"], "mustNotShow": ["problem text"]},
                    {"assetRole": "stage_4_realtime", "scenePurpose": "설명 상황", "mustShow": ["마스코트"], "mustNotShow": ["problem text"]},
                ],
                "ttsNarrationIntent": [
                    {"assetRole": "hero", "voicePurpose": "시작 안내", "tone": "bright"},
                    {"assetRole": "stage_1", "voicePurpose": "전체 보기", "tone": "calm"},
                    {"assetRole": "stage_2", "voicePurpose": "전체 세기", "tone": "calm"},
                    {"assetRole": "stage_3", "voicePurpose": "분수 넣기", "tone": "calm"},
                    {"assetRole": "stage_4_realtime", "voicePurpose": "말하기 준비", "tone": "reassuring"},
                ],
                "teacherReviewFocus": ["전체를 먼저 세는 흐름이 잘 보이는지 확인합니다."],
                "safetyNotes": ["학생에게 진단 표현을 노출하지 않습니다."],
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
                "studentId": student_id,
                "caseId": case_id,
                "requestedGoal": "[난이도: 기초] 전체 4개 중 1개를 1/4로 표현한다.",
                "contentType": "learning_focus",
            },
    )
    assert orchestrator.status_code == 200
    orchestrator_run = orchestrator.json()["data"]["agentRun"]
    assert orchestrator_run["status"] == "running"
    orchestrator_detail = client.get(f"/api/ai/agent-runs/{orchestrator_run['id']}")
    assert orchestrator_detail.status_code == 200
    orchestrator_run = orchestrator_detail.json()["data"]
    assert orchestrator_run["status"] == "succeeded"

    content_generation = client.post(
            "/api/ai/content-generations",
            json={
                "orchestratorRunId": orchestrator_run["id"],
                "studentId": student_id,
                "caseId": case_id,
            },
    )
    assert content_generation.status_code == 200
    content_generation_data = content_generation.json()["data"]
    assert content_generation_data["content"] is None
    assert content_generation_data["agentRun"]["status"] == "running"
    content_run_detail = client.get(f"/api/ai/agent-runs/{content_generation_data['agentRun']['id']}")
    assert content_run_detail.status_code == 200
    content_generation_run = content_run_detail.json()["data"]
    assert content_generation_run["status"] == "succeeded"
    content_output = content_generation_run["outputJson"]
    content = content_output.get("missionContent", content_output)
    assert content["id"] == "content_generated_contract_001"
    assert content["status"] == "teacher_review"
    assert content["totalSteps"] == 4
    assert content_generation_calls["count"] == 2
    assert [stage["step"] for stage in content["stages"]] == [1, 2, 3, 4]
    assert len([asset for asset in content["assets"] if asset["assetType"] == "image"]) == 5
    assert len([asset for asset in content["assets"] if asset["assetType"] == "audio"]) == 5
    saved_content_response = client.get("/api/contents/content_generated_contract_001")
    assert saved_content_response.status_code == 200
    content = saved_content_response.json()["data"]
    assert content["briefJson"]["generatedAt"]

    latest_seed = client.get("/api/context/seed")
    assert latest_seed.status_code == 200
    latest_fraction_mapping = next(
        mapping for mapping in latest_seed.json()["data"]["missionMappings"] if mapping["studentId"] == student_id
    )
    assert latest_fraction_mapping["contentId"] == "content_generated_contract_001"
    assert latest_fraction_mapping["updatedAt"] == content["briefJson"]["generatedAt"]

    package = client.post("/api/contents/content_generated_contract_001/assets/generate-package")
    assert package.status_code == 200
    package_data = package.json()["data"]
    assert package_data["generatedCount"] == 10
    assert image_brief_calls["count"] == 1
    assert all(asset["storageUrl"].startswith("/generated/assets/content_generated_contract_001/") for asset in package_data["assets"])
    assert all(asset["qaStatus"] == "passed" for asset in package_data["assets"])
    assert all(
        asset["promptJson"].get("promptVersion") == "image_brief_v1"
        for asset in package_data["assets"]
        if asset["assetType"] == "image"
    )

    reviewable = client.get("/api/contents/content_generated_contract_001")
    assert reviewable.status_code == 200
    assert reviewable.json()["data"]["assets"][0]["previewUrl"].startswith("/generated/assets/content_generated_contract_001/")
    assert reviewable.json()["data"]["assets"][0]["qaStatus"] == "passed"
