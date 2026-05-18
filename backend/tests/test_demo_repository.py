from sqlalchemy.orm import sessionmaker

from app.core.config import BACKEND_DIR
from app.data.demo_data import create_demo_database
from app.db.session import create_database_engine, create_schema, normalize_database_url
from app.domain import db_models as rows
from app.domain.enums import MissionStatus
from app.domain.models import ActivityEvent, ContentAttempt, ReviewSummary
from app.domain.schemas import MissionContent
from app.repositories.demo_repository import DemoRepository
from app.services.store import DemoStore


def test_relative_sqlite_database_url_resolves_from_backend_dir() -> None:
    expected_path = (BACKEND_DIR / "data" / "eduyj_demo.db").resolve().as_posix()

    assert normalize_database_url("sqlite:///./data/eduyj_demo.db") == f"sqlite:///{expected_path}"


def test_repository_round_trips_seed_database() -> None:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    repository = DemoRepository(sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True))

    repository.replace_database(create_demo_database())
    loaded = repository.load_database()

    assert len(loaded.users) == 1
    assert len(loaded.students) == 3
    assert len(loaded.schools) == 3
    assert len(loaded.mission_contents) == 3
    assert len(loaded.review_summaries) == 2
    assert loaded.review_summaries[0].short_summary
    assert "Completed" not in loaded.review_summaries[0].short_summary
    assert loaded.mission_contents[0].total_steps == 4
    assert {stage.step for stage in loaded.mission_contents[0].stages} == {1, 2, 3, 4}


def test_repository_drops_unsupported_mini_simulation_contents_on_load() -> None:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    repository = DemoRepository(session_factory)
    db = create_demo_database()
    unsupported_content = db.mission_contents[0]

    repository.replace_database(db)
    with session_factory() as session:
        stage = (
            session.query(rows.ContentStageRow)
            .filter(
                rows.ContentStageRow.mission_content_id == unsupported_content.id,
                rows.ContentStageRow.step == 3,
            )
            .one()
        )
        stage.template_type = "mini_simulation"
        stage.template_json = {
            "imageAssetId": "asset_bad_stage_3",
            "audioAssetId": "asset_bad_stage_3_audio",
            "assetBundle": {"imageAssetId": "asset_bad_stage_3", "audioAssetId": "asset_bad_stage_3_audio"},
            "situationText": "채점할 수 없는 시뮬레이션입니다.",
            "practicePrompt": "움직여 보세요.",
            "sourceTextLines": [],
            "sceneTextLines": [],
        }
        session.commit()

    loaded = repository.load_database()

    assert unsupported_content.id not in {content.id for content in loaded.mission_contents}


def test_review_summary_prefers_latest_completed_attempt() -> None:
    db = create_demo_database()
    content = next(item for item in db.mission_contents if item.id == "content_fraction_001")
    student_id = content.student_id
    completed_attempt = ContentAttempt(
        id="attempt_completed_for_review",
        missionContentId=content.id,
        studentId=student_id,
        status="completed",
        currentStep=4,
        startedAt="2026-05-07T01:00:00+00:00",
        completedAt="2026-05-07T01:05:00+00:00",
        scoreJson={"completionRate": 1},
    )
    newer_in_progress_attempt = ContentAttempt(
        id="attempt_newer_in_progress",
        missionContentId=content.id,
        studentId=student_id,
        status="in_progress",
        currentStep=1,
        startedAt="2026-05-07T01:10:00+00:00",
        completedAt=None,
        scoreJson=None,
    )
    db.attempts.extend([completed_attempt, newer_in_progress_attempt])
    db.activity_events.append(
        ActivityEvent(
            id="event_completed_answer",
            attemptId=completed_attempt.id,
            studentId=student_id,
            stageId=content.stages[1].id,
            eventType="answer_submitted",
            payloadJson={"isCorrect": True},
            occurredAt="2026-05-07T01:02:00+00:00",
        )
    )
    store = DemoStore(seed=db)

    summary = store.create_review_summary_for_content(content.id)

    assert summary is not None
    assert summary.attempt_id == completed_attempt.id
    assert summary.completion_rate == 1


def test_student_report_hides_in_progress_attempt_summaries() -> None:
    db = create_demo_database()
    content = next(item for item in db.mission_contents if item.id == "content_fraction_001")
    student_id = content.student_id
    in_progress_attempt = ContentAttempt(
        id="attempt_in_progress_for_report",
        missionContentId=content.id,
        studentId=student_id,
        status="in_progress",
        currentStep=1,
        startedAt="2026-05-07T01:10:00+00:00",
        completedAt=None,
        scoreJson=None,
    )
    db.attempts.append(in_progress_attempt)
    db.review_summaries.append(
        ReviewSummary(
            id="review_in_progress_should_hide",
            attemptId=in_progress_attempt.id,
            studentId=student_id,
            completionRate=0.25,
            accuracyRate=0,
            shortSummary="완료율 25% / 정답률 0%",
            wrongPatternJson={},
            realtimeResultJson={},
        )
    )
    store = DemoStore(seed=db)

    report = store.get_student_report(student_id)

    assert report is not None
    assert all(item["id"] != "review_in_progress_should_hide" for item in report["reports"])


def test_publish_archives_previous_student_deployment_with_history() -> None:
    db = create_demo_database()
    original = next(item for item in db.mission_contents if item.id == "content_fraction_001")
    replacement_payload = original.model_dump(by_alias=True)
    replacement_payload.update(
        {
            "id": "content_fraction_replacement",
            "title": "Replacement fraction lesson",
            "status": "approved",
            "approvedByUserId": "user_teacher_demo",
            "approvedAt": "2026-05-17T00:00:00+00:00",
            "publishedAt": None,
        }
    )
    for stage in replacement_payload["stages"]:
        stage["id"] = f"{stage['id']}_replacement"
        stage["missionContentId"] = replacement_payload["id"]
    for asset in replacement_payload["assets"]:
        asset["id"] = f"{asset['id']}_replacement"
        asset["missionContentId"] = replacement_payload["id"]
        asset["storageUrl"] = f"https://assets.example.test/{asset['id']}"
        asset["previewUrl"] = asset["storageUrl"]

    replacement = MissionContent.model_validate(replacement_payload)
    db.mission_contents.append(replacement)
    store = DemoStore(seed=db)

    published = store.publish_mission_content(replacement.id, "user_teacher_demo")

    assert published is not None
    assert published.status == MissionStatus.PUBLISHED
    assert published.published_at is not None
    assert published.brief_json["deploymentHistory"][-1]["event"] == "published"
    assert published.brief_json["deploymentHistory"][-1]["replacedContentIds"] == [original.id]

    archived = next(item for item in store.db.mission_contents if item.id == original.id)
    assert archived.status == MissionStatus.ARCHIVED
    assert archived.published_at is not None
    assert archived.brief_json["deploymentHistory"][-1]["event"] == "superseded"
    assert archived.brief_json["deploymentHistory"][-1]["replacedByContentId"] == replacement.id

    active_missions = store.list_published_missions_for_student(original.student_id)
    assert [mission.id for mission in active_missions if mission.case_id == original.case_id] == [replacement.id]
    assert store.get_published_mission_for_student(original.student_id, original.id) is not None
