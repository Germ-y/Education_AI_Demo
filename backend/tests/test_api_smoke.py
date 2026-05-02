from fastapi.testclient import TestClient

from app.main import create_app


def test_teacher_and_student_demo_flows() -> None:
    client = TestClient(create_app())

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

    student_login = client.post("/api/auth/student-access", json={"accessCode": "STAR-001"})
    assert student_login.status_code == 200
    student_token = student_login.json()["data"]["session"]["accessToken"]

    today = client.get("/api/student/missions/today", headers={"authorization": f"Bearer {student_token}"})
    assert today.status_code == 200
    assert today.json()["data"][0]["totalSteps"] == 4

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
    assert realtime.status_code == 200
    assert realtime.json()["data"]["practiceSpec"]["maxTurns"] == 6
