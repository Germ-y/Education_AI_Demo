import pytest

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


def test_requires_problem_text_in_template_json_not_image() -> None:
    stage = create_demo_database().mission_contents[0].stages[1].model_dump(by_alias=True)
    stage["templateJson"].pop("question")
    stage["templateJson"].pop("instruction", None)

    with pytest.raises(ValueError):
        ContentStage.model_validate(stage)
