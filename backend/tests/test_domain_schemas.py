import pytest

from app.api.routes.ai import _mission_from_generation
from app.data.demo_data import create_demo_database
from app.domain.schemas import ContentAsset, ContentStage, MissionContent


def test_accepts_demo_4_stage_missions() -> None:
    db = create_demo_database()

    for content in db.mission_contents:
        MissionContent.model_validate(content.model_dump(by_alias=True))
        assert content.total_steps == 4
        assert sorted(stage.step for stage in content.stages) == [1, 2, 3, 4]


def test_rejects_fifth_stage() -> None:
    content = create_demo_database().mission_contents[0].model_dump(by_alias=True)
    content["totalSteps"] = 5
    content["stages"].append({**content["stages"][0], "id": "stage_bad_5", "step": 5, "sortOrder": 5})

    with pytest.raises(ValueError):
        MissionContent.model_validate(content)


def test_allows_realtime_templates_only_at_stage_4() -> None:
    stage = create_demo_database().mission_contents[0].stages[0].model_dump(by_alias=True)
    stage["templateType"] = "realtime_teach_back"

    with pytest.raises(ValueError):
        ContentStage.model_validate(stage)


def test_rejects_invalid_stage_template_pair() -> None:
    stage = create_demo_database().mission_contents[0].stages[1].model_dump(by_alias=True)
    stage["stageRole"] = "concept_intro"

    with pytest.raises(ValueError):
        ContentStage.model_validate(stage)


def test_validates_image_quiz_template_shape() -> None:
    stage = create_demo_database().mission_contents[0].stages[1].model_dump(by_alias=True)
    stage["templateType"] = "image_quiz"
    stage["templateJson"] = {
        "imageAssetId": "asset_content_fraction_001_stage_2",
        "question": "빛나는 조각은 전체 중 몇 개인가요?",
        "choices": [
            {"id": "a", "text": "1개"},
            {"id": "b", "text": "2개"},
            {"id": "c", "text": "4개"},
        ],
        "answer": "a",
        "correctFeedback": "좋아요. 빛나는 조각은 1개예요.",
        "wrongFeedback": "빛나는 부분만 다시 세어볼까요?",
    }

    assert ContentStage.model_validate(stage).template_type == "image_quiz"

    stage["templateJson"]["choices"].pop()
    with pytest.raises(ValueError):
        ContentStage.model_validate(stage)


def test_rejects_video_asset_roles() -> None:
    asset = create_demo_database().mission_contents[0].assets[0].model_dump(by_alias=True)
    asset["assetRole"] = "video"

    with pytest.raises(ValueError):
        ContentAsset.model_validate(asset)


def test_requires_stage_images_and_audio_assets() -> None:
    content = create_demo_database().mission_contents[0].model_dump(by_alias=True)
    content["assets"] = [asset for asset in content["assets"] if asset["assetType"] != "audio"]

    with pytest.raises(ValueError):
        MissionContent.model_validate(content)


def test_requires_image_roles_even_when_audio_role_exists() -> None:
    content = create_demo_database().mission_contents[0].model_dump(by_alias=True)
    content["assets"] = [
        asset for asset in content["assets"] if not (asset["assetType"] == "image" and asset["assetRole"] == "stage_2")
    ]

    with pytest.raises(ValueError, match="필수 이미지 asset role"):
        MissionContent.model_validate(content)


def test_rejects_realtime_spec_on_static_stage() -> None:
    stage = create_demo_database().mission_contents[0].stages[0].model_dump(by_alias=True)
    stage["realtimeSpec"] = create_demo_database().mission_contents[0].stages[3].realtime_spec.model_dump(by_alias=True)

    with pytest.raises(ValueError, match="1~3단계에는 realtimeSpec"):
        ContentStage.model_validate(stage)


def test_requires_problem_text_in_template_json_not_image() -> None:
    stage = create_demo_database().mission_contents[0].stages[1].model_dump(by_alias=True)
    stage["templateJson"].pop("question")
    stage["templateJson"].pop("instruction", None)

    with pytest.raises(ValueError):
        ContentStage.model_validate(stage)


def test_content_generation_output_accepts_direct_mission_content_schema() -> None:
    content = create_demo_database().mission_contents[0].model_dump(by_alias=True)
    content["id"] = "content_generated_schema_check"
    content["status"] = "teacher_review"
    content["approvedByUserId"] = None
    content["approvedAt"] = None
    content["publishedAt"] = None
    for stage in content["stages"]:
        stage["missionContentId"] = content["id"]
    for asset in content["assets"]:
        asset["missionContentId"] = content["id"]
        asset["storageUrl"] = ""
        asset["previewUrl"] = None
        asset["qaStatus"] = "pending"
        asset["approvalStatus"] = "pending"

    mission = _mission_from_generation(content, student_id="student_learning_fraction", case_id="case_learning_fraction")

    assert mission.id == "content_generated_schema_check"
    assert mission.status == "teacher_review"
    assert len([asset for asset in mission.assets if asset.asset_type == "image"]) == 5
    assert len([asset for asset in mission.assets if asset.asset_type == "audio"]) == 5
