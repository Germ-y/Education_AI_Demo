import pytest

from app.api.routes.ai import _mission_from_generation
from app.api.routes.contents import (
    _build_image_brief_output,
    _pairs_from_left_right_cards,
)
from app.data.demo_data import create_demo_database
from app.domain.schemas import ContentAsset, ContentStage, MissionContent
from app.services.content_quality import ContentQualityError, validate_mission_content_quality, validate_orchestrator_plan_quality


def test_accepts_demo_4_stage_missions() -> None:
    db = create_demo_database()

    for content in db.mission_contents:
        MissionContent.model_validate(content.model_dump(by_alias=True))
        assert content.total_steps == 4
        assert sorted(stage.step for stage in content.stages) == [1, 2, 3, 4]


def test_image_brief_evidence_reads_card_match_dict_matches() -> None:
    pairs = _pairs_from_left_right_cards(
        {
            "leftCards": [
                {"id": "line_schedule", "text": "매주 화요일 3시에 진행됩니다."},
                {"id": "line_join", "text": "함께해요!"},
            ],
            "rightCards": [
                {"id": "fact", "text": "확인할 수 있는 사실"},
                {"id": "opinion", "text": "권유가 담긴 의견"},
            ],
            "matches": {"line_schedule": "fact", "line_join": "opinion"},
        }
    )

    assert pairs == [
        {"left": "매주 화요일 3시에 진행됩니다.", "right": "확인할 수 있는 사실"},
        {"left": "함께해요!", "right": "권유가 담긴 의견"},
    ]


def test_image_brief_keeps_image_prompt_situational_and_filters_ui_question() -> None:
    mission = MissionContent.model_validate(_generated_life_support_content())
    stage = next(stage for stage in mission.stages if stage.step == 2)
    stage.template_json = {
        **stage.template_json,
        "question": "무엇을 준비해 오나요?",
        "choices": [
            {"id": "a", "text": "운동화와 물통"},
            {"id": "b", "text": "색연필과 가위"},
        ],
        "sourceTextLines": ["체육 행사 안내", "준비물: 운동화, 물통", "장소: 운동장"],
    }
    mission.brief_json = {
        "stageVisualSpecs": [
            {
                "assetRole": "stage_2",
                "visualPurpose": "알림장 원자료에서 준비물을 찾는 근거를 보여줍니다.",
                "sceneSummary": "학교 알림장 본문을 가까이 보여주는 장면",
                "primaryEvidenceObject": "체육 활동 준비 장면",
                "mustShow": ["학교 알림장", "준비물 줄"],
                "allowedSceneText": [],
                "doNotRenderText": [],
                "composition": "책상과 알림장, 준비물 그림이 함께 보이는 교실 장면",
            }
        ]
    }
    asset = next(asset for asset in mission.assets if asset.asset_type == "image" and asset.asset_role == "stage_2")

    output = _build_image_brief_output(mission, [asset])
    prompt = output["imageBriefs"][0]["prompt"]

    assert "무엇을 준비해 오나요?" not in prompt
    assert "준비물: 운동화, 물통" not in prompt
    assert "색연필과 가위" not in prompt
    assert "체육 행사 안내" not in prompt
    assert "장소: 운동장" not in prompt
    assert "worksheet" in prompt
    assert "natural scene or hands-on object setup" in prompt
    assert "not an instructional diagram, notebook page, poster, notice, or source document" in prompt
    assert "sceneTextLines" not in output["imageBriefs"][0]
    assert "learningEvidence" not in output["imageBriefs"][0]
    assert "visualContext" in output["imageBriefs"][0]
    assert output["imageBriefs"][0]["textRenderingPolicy"] == "scene_context_only_no_lesson_text"


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


def test_rejects_answerless_mini_simulation_template() -> None:
    stage = next(stage for stage in create_demo_database().mission_contents[0].stages if stage.step == 3).model_dump(by_alias=True)
    stage["stageRole"] = "applied_problem"
    stage["templateType"] = "mini_simulation"
    stage["templateJson"] = {
        "imageAssetId": "asset_content_fraction_001_stage_3",
        "audioAssetId": "asset_content_fraction_001_stage_3_audio",
        "assetBundle": {
            "imageAssetId": "asset_content_fraction_001_stage_3",
            "audioAssetId": "asset_content_fraction_001_stage_3_audio",
        },
        "situationText": "학생이 조작해 보는 활동 설명입니다.",
        "practicePrompt": "시뮬레이션을 해 보세요.",
        "sourceTextLines": [],
        "sceneTextLines": [],
    }

    with pytest.raises(ValueError, match="stageRole과 templateType"):
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


def test_choice_question_requires_answer_id_from_choices() -> None:
    stage = next(stage for stage in create_demo_database().mission_contents[0].stages if stage.template_type == "scene_question").model_dump(by_alias=True)

    stage["templateJson"].pop("answer")
    with pytest.raises(ValueError, match="answer"):
        ContentStage.model_validate(stage)

    stage["templateJson"]["answer"] = "missing"
    with pytest.raises(ValueError, match="choices"):
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
    base_content = next(content for content in create_demo_database().mission_contents if content.student_id == "student_learning_fraction")
    content = base_content.model_dump(by_alias=True)
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

    mission = _mission_from_generation(content, student_id=base_content.student_id, case_id=base_content.case_id)

    assert mission.id.startswith(f"content_{base_content.student_id}_")
    assert mission.status == "teacher_review"
    assert all(stage.mission_content_id == mission.id for stage in mission.stages)
    assert all(asset.mission_content_id == mission.id for asset in mission.assets)
    assert len([asset for asset in mission.assets if asset.asset_type == "image"]) == 5
    assert len([asset for asset in mission.assets if asset.asset_type == "audio"]) == 5


def test_content_generation_rejects_realtime_reflection_object() -> None:
    base_content = next(content for content in create_demo_database().mission_contents if content.student_id == "student_learning_fraction")
    content = base_content.model_dump(by_alias=True)
    content["id"] = "content_generated_realtime_reflection_check"
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

    realtime_spec = content["stages"][3]["realtimeSpec"]
    realtime_spec["postPracticeReflection"] = {
        "question": "오늘 연습에서 내가 말한 도움 요청 문장을 떠올려볼까요?",
        "choices": ["잘 말했어요.", "조금 더 연습하고 싶어요."],
    }

    with pytest.raises(ValueError, match="postPracticeReflection"):
        _mission_from_generation(content, student_id=base_content.student_id, case_id=base_content.case_id)


def test_content_generation_rejects_realtime_rubric_without_label() -> None:
    base_content = next(content for content in create_demo_database().mission_contents if content.student_id == "student_learning_fraction")
    content = base_content.model_dump(by_alias=True)
    content["id"] = "content_generated_realtime_rubric_check"
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

    realtime_spec = content["stages"][3]["realtimeSpec"]
    realtime_spec["rubric"] = [
        {"id": "r1", "description": "전체를 먼저 확인한다고 말한다.", "required": True},
        {"id": "r2", "description": "부분의 수를 한 문장으로 설명한다.", "required": False},
    ]

    with pytest.raises(ValueError, match="rubric"):
        _mission_from_generation(content, student_id=base_content.student_id, case_id=base_content.case_id)


def test_content_generation_rejects_extra_card_match_fields() -> None:
    base_content = next(content for content in create_demo_database().mission_contents if content.student_id == "student_learning_fraction")
    content = base_content.model_dump(by_alias=True)
    content["id"] = "content_generated_card_match_cleanup"
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

    stage = content["stages"][1]
    stage["templateType"] = "card_match"
    stage["templateJson"] = {
        "imageAssetId": "asset_content_fraction_001_stage_2",
        "audioAssetId": "asset_content_fraction_001_stage_2_audio",
        "question": "같은 양끼리 이어 보세요.",
        "leftCards": [{"id": "left_1", "text": "1/2"}, {"id": "left_2", "text": "1/4"}],
        "rightCards": [{"id": "right_1", "text": "0.5"}, {"id": "right_2", "text": "0.25"}],
        "cards": [
            {"id": "extra_1", "text": "추가 카드 1"},
            {"id": "extra_2", "text": "추가 카드 2"},
            {"id": "extra_3", "text": "추가 카드 3"},
        ],
        "matches": {"left_1": "right_1", "left_2": "right_2"},
        "correctFeedback": "좋아요. 같은 양을 잘 찾았어요.",
        "wrongFeedback": "그림과 값을 다시 비교해 볼까요?",
    }

    with pytest.raises(ValueError, match="card_match"):
        _mission_from_generation(content, student_id=base_content.student_id, case_id=base_content.case_id)


def test_orchestrator_plan_quality_requires_track_matching_four_stage_flow() -> None:
    plan = _valid_learning_plan()

    validate_orchestrator_plan_quality(
        plan,
        student_id="student_learning_fraction",
        case_id="case_learning_fraction",
        content_type="learning_focus",
    )

    plan["stagePlan"][3]["templateType"] = "realtime_roleplay"
    with pytest.raises(ContentQualityError, match="templateType"):
        validate_orchestrator_plan_quality(
            plan,
            student_id="student_learning_fraction",
            case_id="case_learning_fraction",
            content_type="learning_focus",
        )


def test_orchestrator_plan_quality_leaves_prompt_level_design_criteria_to_generation() -> None:
    plan = _valid_learning_plan()
    del plan["scenarioSpine"]["stage2FirstSuccess"]
    del plan["stagePlan"][1]["templateRationale"]

    validate_orchestrator_plan_quality(
        plan,
        student_id="student_learning_fraction",
        case_id="case_learning_fraction",
        content_type="learning_focus",
    )


def test_orchestrator_plan_quality_allows_choice_flow_for_very_low_reading_load() -> None:
    plan = _valid_learning_plan()
    plan["stagePlan"][1]["templateType"] = "scene_question"
    plan["stagePlan"][2]["templateType"] = "image_quiz"
    case_file = _fraction_case_file()
    case_file["profile"]["profileJson"]["readingLoad"] = "very_low"
    case_file["profile"]["profileJson"]["choiceCountLimit"] = 2

    validate_orchestrator_plan_quality(
        plan,
        student_id="student_learning_fraction",
        case_id="case_learning_fraction",
        content_type="learning_focus",
        case_file=case_file,
    )


def test_mission_quality_accepts_generated_korean_contract() -> None:
    mission = MissionContent.model_validate(_generated_fraction_content())

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_rejects_raw_internal_terms_in_student_text() -> None:
    content = _generated_fraction_content()
    content["stages"][3]["studentTitle"] = "realtime teach-back practice"
    mission = MissionContent.model_validate(content)

    with pytest.raises(ContentQualityError, match="studentTitle"):
        validate_mission_content_quality(
            mission,
            case_file=_fraction_case_file(),
            orchestrator_plan=_valid_learning_plan(),
        )


def test_mission_quality_leaves_choice_limit_nuance_to_teacher_review() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateType"] = "card_match"
    content["stages"][1]["templateJson"] = {
        "imageAssetId": content["stages"][1]["templateJson"]["imageAssetId"],
        "audioAssetId": content["stages"][1]["templateJson"]["audioAssetId"],
        "assetBundle": content["stages"][1]["templateJson"]["assetBundle"],
        "question": "같은 양끼리 이어 보세요.",
        "leftCards": [{"id": "left_1", "text": "1/2"}, {"id": "left_2", "text": "1/4"}],
        "rightCards": [{"id": "right_1", "text": "0.5"}, {"id": "right_2", "text": "0.25"}],
        "matches": {"left_1": "right_1", "left_2": "right_2"},
        "correctFeedback": "좋아요. 같은 양을 잘 찾았어요.",
        "wrongFeedback": "분수와 소수를 다시 비교해 볼까요?",
    }
    mission = MissionContent.model_validate(content)
    case_file = _fraction_case_file()
    case_file["profile"]["profileJson"]["choiceCountLimit"] = 2

    validate_mission_content_quality(
        mission,
        case_file=case_file,
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_leaves_duplicate_card_match_answer_candidates_to_prompt_review() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateType"] = "card_match"
    content["stages"][1]["templateJson"] = {
        "imageAssetId": content["stages"][1]["templateJson"]["imageAssetId"],
        "audioAssetId": content["stages"][1]["templateJson"]["audioAssetId"],
        "assetBundle": content["stages"][1]["templateJson"]["assetBundle"],
        "question": "각 일정이 가능한지 이어 보세요.",
        "leftCards": [
            {"id": "left_1", "text": "친구 제안"},
            {"id": "left_2", "text": "내 일정"},
        ],
        "rightCards": [
            {"id": "right_1", "text": "겹치는 시간이라 바로 만나기 힘듦"},
            {"id": "right_2", "text": "겹치는 시간이라 바로 만나기 힘듦"},
        ],
        "matches": {"left_1": "right_1", "left_2": "right_2"},
        "correctFeedback": "좋아요. 시간을 비교했어요.",
        "wrongFeedback": "두 시간을 다시 비교해 볼까요?",
    }
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_leaves_overlong_student_problem_text_to_prompt_review() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateJson"]["question"] = (
        "첫 번째 문단 사람들이 가까운 거리를 이동할 때도 자동차를 많이 이용하면서 공기가 점점 더 더러워지고 있습니다. "
        "윗글을 읽고 빈칸에 들어갈 알맞은 근거 문장을 고르세요."
    )
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_leaves_overlong_choice_text_to_prompt_review() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateJson"]["choices"][0]["text"] = "자동차 대신 걸어 다니거나 자전거를 타면 공기를 더럽히는 배기가스를 줄일 수 있습니다."
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_leaves_overlong_source_text_lines_to_prompt_review() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateJson"]["sourceTextLines"] = [
        "사람들이 가까운 거리를 이동할 때 자동차를 많이 이용하면서 공기가 점점 더 더러워지고 있습니다.",
    ]
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_allows_three_sequence_cards_with_two_choice_limit() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateJson"]["choices"] = [{"id": "a", "text": "1조각"}, {"id": "b", "text": "4조각"}]
    content["stages"][2]["templateType"] = "sequence_ordering"
    content["stages"][2]["templateJson"] = {
        "imageAssetId": content["stages"][2]["templateJson"]["imageAssetId"],
        "audioAssetId": content["stages"][2]["templateJson"]["audioAssetId"],
        "assetBundle": content["stages"][2]["templateJson"]["assetBundle"],
        "question": "분수를 읽는 순서를 골라보세요.",
        "cards": [
            {"id": "whole", "text": "전체 세기"},
            {"id": "part", "text": "고른 것 세기"},
            {"id": "fraction", "text": "분수 말하기"},
        ],
        "answerOrder": ["whole", "part", "fraction"],
        "correctFeedback": "좋아요. 전체와 고른 것을 차례대로 봤어요.",
        "wrongFeedback": "먼저 전체를 세는 카드부터 골라볼까요?",
    }
    mission = MissionContent.model_validate(content)
    case_file = _fraction_case_file()
    case_file["profile"]["profileJson"]["choiceCountLimit"] = 2

    validate_mission_content_quality(
        mission,
        case_file=case_file,
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_allows_four_sequence_cards_after_schema_passes() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateJson"]["choices"] = [{"id": "a", "text": "1議곌컖"}, {"id": "b", "text": "4議곌컖"}]
    content["stages"][2]["templateType"] = "sequence_ordering"
    content["stages"][2]["templateJson"] = {
        "imageAssetId": content["stages"][2]["templateJson"]["imageAssetId"],
        "audioAssetId": content["stages"][2]["templateJson"]["audioAssetId"],
        "assetBundle": content["stages"][2]["templateJson"]["assetBundle"],
        "question": "분수를 읽는 순서를 골라보세요.",
        "cards": [
            {"id": "whole", "text": "전체 보기"},
            {"id": "part", "text": "고른 것 보기"},
            {"id": "fraction", "text": "분수 말하기"},
            {"id": "check", "text": "다시 확인하기"},
        ],
        "answerOrder": ["whole", "part", "fraction", "check"],
        "correctFeedback": "좋아요. 차례대로 잘 놓았어요.",
        "wrongFeedback": "먼저 전체를 보는 카드부터 골라볼까요?",
    }
    mission = MissionContent.model_validate(content)
    case_file = _fraction_case_file()
    case_file["profile"]["profileJson"]["choiceCountLimit"] = 2

    validate_mission_content_quality(
        mission,
        case_file=case_file,
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_allows_three_blank_fill_tiles_with_two_choice_limit() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateJson"]["choices"] = [{"id": "a", "text": "1議곌컖"}, {"id": "b", "text": "4議곌컖"}]
    content["stages"][2]["templateJson"]["tiles"] = ["1/4", "1/2", "4/1"]
    mission = MissionContent.model_validate(content)
    case_file = _fraction_case_file()
    case_file["profile"]["profileJson"]["choiceCountLimit"] = 2

    validate_mission_content_quality(
        mission,
        case_file=case_file,
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_allows_four_blank_fill_tiles_after_schema_passes() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["templateJson"]["choices"] = [{"id": "a", "text": "1議곌컖"}, {"id": "b", "text": "4議곌컖"}]
    content["stages"][2]["templateJson"]["tiles"] = ["1/4", "1/2", "3/4", "4/1"]
    mission = MissionContent.model_validate(content)
    case_file = _fraction_case_file()
    case_file["profile"]["profileJson"]["choiceCountLimit"] = 2

    validate_mission_content_quality(
        mission,
        case_file=case_file,
        orchestrator_plan=_valid_learning_plan(),
    )


def test_blank_fill_rejects_generic_image_fill_instruction() -> None:
    content = _generated_fraction_content()
    content["stages"][2]["templateJson"]["sentence"] = "그림을 보고 알맞은 값을 골라 빈칸을 채워 보세요. __"

    with pytest.raises(ValueError, match="blank_fill"):
        MissionContent.model_validate(content)


def test_mission_quality_requires_fixed_student_stage_titles() -> None:
    content = _generated_fraction_content()
    content["stages"][1]["studentTitle"] = "전체 세기"
    mission = MissionContent.model_validate(content)

    with pytest.raises(ContentQualityError, match="studentTitle"):
        validate_mission_content_quality(
            mission,
            case_file=_fraction_case_file(),
            orchestrator_plan=_valid_learning_plan(),
        )


def test_mission_quality_does_not_block_image_prompt_text_with_string_matching() -> None:
    content = _generated_fraction_content()
    content["assets"][1]["promptJson"]["prompt"] += " 전체는 몇 조각인가요?"
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_does_not_block_ui_like_image_prompt_wording() -> None:
    content = _generated_fraction_content()
    content["assets"][1]["promptJson"]["prompt"] += " 빈 카드와 말풍선, 선택지 영역을 함께 배치합니다."
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_allows_real_object_button_word_in_image_prompt() -> None:
    content = _generated_fraction_content()
    content["assets"][1]["promptJson"]["prompt"] += " 안내문 옆 실제 사물의 작은 전원 버튼은 배경 소품으로만 보입니다."
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_allows_notice_or_poster_tasks_without_blocking_generation() -> None:
    content = _generated_fraction_content()
    content["stages"][0]["studentInstruction"] = "포스터 문구를 보고 단서를 찾아봅니다."
    content["stages"][0]["templateJson"]["storyText"] = "교실 게시판에 환경 포스터가 붙어 있어요."
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_allows_source_lines_for_notice_or_poster_tasks() -> None:
    content = _generated_fraction_content()
    content["stages"][0]["studentInstruction"] = "포스터 문구를 보고 단서를 찾아봅니다."
    content["stages"][0]["templateJson"]["storyText"] = "교실 게시판에 환경 포스터가 붙어 있어요."
    content["stages"][0]["templateJson"]["sourceTextLines"] = ["종이컵 20개를 모았어요.", "텀블러를 쓰면 더 멋져요."]
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_fraction_case_file(),
        orchestrator_plan=_valid_learning_plan(),
    )


def test_mission_quality_leaves_life_support_background_nuance_to_teacher_review() -> None:
    content = _generated_life_support_content()
    content["stages"][1]["templateJson"]["question"] = "무엇이 보이나요?"
    content["stages"][1]["templateJson"]["choices"] = [
        {"id": "a", "text": "바닥에 젖은 자국이 보여요."},
        {"id": "b", "text": "천장이나 창문 보기"},
    ]
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_life_support_case_file(),
    )


def test_mission_quality_accepts_life_support_plausible_decision_fork() -> None:
    content = _generated_life_support_content()
    content["stages"][1]["templateJson"]["question"] = "바로 움직이기 전에 무엇을 먼저 확인해야 할까요?"
    content["stages"][1]["templateJson"]["choices"] = [
        {"id": "a", "text": "옆 친구가 지나가고 있는지 보기"},
        {"id": "b", "text": "식판을 들고 바로 자리로 가기"},
    ]
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_life_support_case_file(),
    )


def test_mission_quality_accepts_three_card_life_support_action_sequence() -> None:
    content = _generated_life_support_content()
    stage = content["stages"][2]
    stage["templateType"] = "sequence_ordering"
    stage["templateJson"] = {
        "imageAssetId": stage["templateJson"]["imageAssetId"],
        "audioAssetId": stage["templateJson"]["audioAssetId"],
        "assetBundle": stage["templateJson"]["assetBundle"],
        "sourceTextLines": [],
        "sceneTextLines": [],
        "question": "친구들과 공놀이를 할 때 차례를 지키는 순서로 놓아 보세요.",
        "cards": [
            {"id": "look", "text": "공을 받을 친구를 바라본다."},
            {"id": "ask", "text": "준비됐는지 짧게 물어본다."},
            {"id": "pass", "text": "친구가 준비되면 천천히 공을 준다."},
        ],
        "answerOrder": ["look", "ask", "pass"],
        "correctFeedback": "좋아요. 먼저 보고, 물어보고, 천천히 주는 순서예요.",
        "wrongFeedback": "공을 주기 전에 친구가 준비됐는지 확인하는 순서를 다시 볼까요?",
    }
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_life_support_case_file(),
    )


def test_mission_quality_leaves_four_card_life_support_action_sequence_to_prompt_review() -> None:
    content = _generated_life_support_content()
    stage = content["stages"][2]
    stage["templateType"] = "sequence_ordering"
    stage["templateJson"] = {
        "imageAssetId": stage["templateJson"]["imageAssetId"],
        "audioAssetId": stage["templateJson"]["audioAssetId"],
        "assetBundle": stage["templateJson"]["assetBundle"],
        "sourceTextLines": [],
        "sceneTextLines": [],
        "question": "친구들과 공놀이를 할 때 차례를 지키는 순서로 놓아 보세요.",
        "cards": [
            {"id": "look", "text": "공을 받을 친구를 바라본다."},
            {"id": "ask", "text": "준비됐는지 짧게 물어본다."},
            {"id": "wait", "text": "친구가 대답할 때까지 기다린다."},
            {"id": "pass", "text": "친구가 준비되면 천천히 공을 준다."},
        ],
        "answerOrder": ["look", "ask", "wait", "pass"],
        "correctFeedback": "좋아요. 먼저 보고, 물어보고, 기다린 뒤 천천히 주는 순서예요.",
        "wrongFeedback": "공을 주기 전에 친구가 준비됐는지 확인하는 순서를 다시 볼까요?",
    }
    mission = MissionContent.model_validate(content)

    validate_mission_content_quality(
        mission,
        case_file=_life_support_case_file(),
    )


def _valid_learning_plan() -> dict:
    return {
        "planVersion": "orchestrator_plan_v1",
        "studentId": "student_learning_fraction",
        "caseId": "case_learning_fraction",
        "contentType": "learning_focus",
        "sessionGoal": "전체와 부분을 구분해 1/4를 말로 설명한다.",
        "targetSkill": "분모와 분자의 의미 연결",
        "difficultyPolicy": {"level": "easy_success", "reason": "시각 자료로 쉬운 성공 경험부터 시작합니다."},
        "selectedStrategy": ["short visual explanation", "teach-back"],
        "scenarioSpine": {
            "situation": "피자 조각 그림을 보고 전체와 부분을 구분합니다.",
            "studentTask": "전체 조각 수와 고른 조각 수를 차례로 말합니다.",
            "learningOrBehaviorTarget": "분모와 분자의 의미 연결",
            "evidenceSource": "네 조각으로 나뉜 피자 그림",
            "commonMistakeOrImpulse": "고른 조각만 보고 전체 수를 놓칠 수 있습니다.",
            "whyThisMatters": "전체와 부분을 함께 말해야 분수 의미를 일상 그림에 연결할 수 있습니다.",
            "studentLikelyImpulseOrMisconception": "고른 한 조각만 보고 전체 네 조각을 빠뜨릴 수 있습니다.",
            "stage2FirstSuccess": "전체 네 조각을 먼저 세며 성공 경험을 만듭니다.",
            "stage3Transfer": "고른 한 조각과 전체 네 조각을 빈칸 문장으로 옮깁니다.",
            "stage4Reuse": "왜 1/4인지 전체와 부분을 넣어 설명합니다.",
        },
        "stagePlan": [
            {
                "step": 1,
                "stageRole": "concept_intro",
                "templateType": "concept_intro",
                "studentTitle": "개념 열기",
                "purpose": "전체와 부분을 그림으로 확인합니다.",
                "templateRationale": "개념 소개 화면이 전체와 부분 용어를 부담 없이 열 수 있습니다.",
            },
            {
                "step": 2,
                "stageRole": "basic_problem",
                "templateType": "scene_question",
                "studentTitle": "문제 1",
                "purpose": "전체 조각 수를 먼저 세게 합니다.",
                "templateRationale": "scene_question이 전체 조각 수를 선택형으로 확인하는 기본 문제에 맞습니다.",
            },
            {
                "step": 3,
                "stageRole": "applied_problem",
                "templateType": "blank_fill",
                "studentTitle": "문제 2",
                "purpose": "고른 수와 전체 수를 분수 자리에 연결합니다.",
                "templateRationale": "blank_fill이 전체와 부분을 문장으로 옮기는 전이에 맞습니다.",
            },
            {
                "step": 4,
                "stageRole": "realtime_practice",
                "templateType": "realtime_teach_back",
                "studentTitle": "설명해보기",
                "purpose": "왜 1/4인지 짧게 말해봅니다.",
                "templateRationale": "말로 설명하기 활동이 같은 근거를 다시 사용하게 합니다.",
            },
        ],
        "imagePackageIntent": [
            {"assetRole": "hero", "scenePurpose": "시작 장면", "mustShow": ["피자 조각"], "mustNotShow": ["problem text"]},
            {"assetRole": "stage_1", "scenePurpose": "전체 확인", "mustShow": ["전체 피자"], "mustNotShow": ["problem text"]},
            {"assetRole": "stage_2", "scenePurpose": "조각 세기", "mustShow": ["네 조각"], "mustNotShow": ["problem text"]},
            {"assetRole": "stage_3", "scenePurpose": "분수 연결", "mustShow": ["한 조각과 전체 조각"], "mustNotShow": ["problem text"]},
            {"assetRole": "stage_4_realtime", "scenePurpose": "설명 상황", "mustShow": ["마스코트"], "mustNotShow": ["problem text"]},
        ],
        "stageVisualSpecs": _fraction_stage_visual_specs(),
        "ttsNarrationIntent": [
            {"assetRole": "hero", "voicePurpose": "시작 안내", "tone": "bright"},
            {"assetRole": "stage_1", "voicePurpose": "전체 보기", "tone": "calm"},
            {"assetRole": "stage_2", "voicePurpose": "전체 세기", "tone": "calm"},
            {"assetRole": "stage_3", "voicePurpose": "분수 넣기", "tone": "calm"},
            {"assetRole": "stage_4_realtime", "voicePurpose": "말하기 준비", "tone": "reassuring"},
        ],
        "teacherReviewFocus": ["전체를 먼저 세는 흐름이 잘 보이는지 확인합니다."],
        "safetyNotes": ["학생에게 진단 표현을 노출하지 않습니다."],
    }


def _fraction_case_file() -> dict:
    return {
        "profile": {
            "id": "student_learning_fraction",
            "studentType": "learning_focus",
            "profileJson": {
                "readingLoad": "low",
                "choiceCountLimit": 3,
            },
        }
    }


def _life_support_case_file() -> dict:
    return {
        "profile": {
            "id": "student_life_bus",
            "studentType": "life_support",
            "profileJson": {
                "readingLoad": "very_low",
                "choiceCountLimit": 2,
            },
        }
    }


def _fraction_stage_visual_specs() -> list[dict]:
    return [
        {
            "assetRole": "hero",
            "step": 0,
            "visualPurpose": "전체와 부분을 배울 피자 조각 장면을 소개합니다.",
            "sceneSummary": "네 조각 피자가 놓인 책상 장면",
            "primaryEvidenceObject": "네 조각 피자",
            "evidenceLocation": "problem_ui_only",
            "mustShow": ["네 조각 피자"],
            "allowedSceneText": [],
            "doNotRenderText": ["문제", "선택지", "정답", "힌트"],
            "composition": "피자 조각이 자연스럽게 놓여 있습니다.",
        },
        {
            "assetRole": "stage_1",
            "step": 1,
            "visualPurpose": "전체 피자가 몇 조각인지 확인하게 합니다.",
            "sceneSummary": "네 조각으로 나뉜 피자 전체",
            "primaryEvidenceObject": "전체 피자",
            "evidenceLocation": "problem_ui_only",
            "mustShow": ["네 조각", "전체 피자"],
            "allowedSceneText": [],
            "doNotRenderText": ["문제", "선택지", "정답", "힌트"],
            "composition": "전체와 부분 관계를 떠올릴 수 있는 장면입니다.",
        },
        {
            "assetRole": "stage_2",
            "step": 2,
            "visualPurpose": "전체 조각 수를 세는 근거를 보여줍니다.",
            "sceneSummary": "네 조각 피자 중 한 조각이 옆에 따로 놓인 장면",
            "primaryEvidenceObject": "네 조각 피자",
            "evidenceLocation": "problem_ui_only",
            "mustShow": ["네 조각", "한 조각과 전체 조각"],
            "allowedSceneText": [],
            "doNotRenderText": ["전체는 몇 조각인가요?", "1개", "2개", "4개", "정답"],
            "composition": "조작물이 자연스럽게 배치되어 있습니다.",
        },
        {
            "assetRole": "stage_3",
            "step": 3,
            "visualPurpose": "고른 조각과 전체 조각을 연결해 분수로 말하게 합니다.",
            "sceneSummary": "고른 한 조각과 전체 네 조각이 함께 보이는 장면",
            "primaryEvidenceObject": "따로 놓인 한 조각",
            "evidenceLocation": "problem_ui_only",
            "mustShow": ["한 조각", "네 조각 전체"],
            "allowedSceneText": [],
            "doNotRenderText": ["분수", "빈칸", "정답", "힌트"],
            "composition": "한 조각과 전체가 같은 책상 위에 놓입니다.",
        },
        {
            "assetRole": "stage_4_realtime",
            "step": 4,
            "visualPurpose": "학생이 전체와 부분을 말로 설명하는 상황을 준비합니다.",
            "sceneSummary": "피자 조각을 보며 설명을 준비하는 책상 장면",
            "primaryEvidenceObject": "피자 조각 그림",
            "evidenceLocation": "problem_ui_only",
            "mustShow": ["피자 조각 그림"],
            "allowedSceneText": [],
            "doNotRenderText": ["말하기 정답", "힌트", "채점"],
            "composition": "설명할 그림이 중심에 있고 사람은 손 정도만 보입니다.",
        },
    ]


def _generated_fraction_content() -> dict:
    base_content = next(content for content in create_demo_database().mission_contents if content.student_id == "student_learning_fraction")
    content = base_content.model_dump(by_alias=True)
    content["id"] = "content_generated_quality_001"
    content["status"] = "teacher_review"
    content["approvedByUserId"] = None
    content["approvedAt"] = None
    content["publishedAt"] = None
    content["briefJson"] = {
        **content.get("briefJson", {}),
        "scenarioSpine": _valid_learning_plan()["scenarioSpine"],
        "stageVisualSpecs": _fraction_stage_visual_specs(),
    }
    for stage in content["stages"]:
        stage["id"] = f"stage_generated_quality_{stage['step']}"
        stage["missionContentId"] = content["id"]
        image_role = "stage_4_realtime" if stage["step"] == 4 else f"stage_{stage['step']}"
        stage["templateJson"]["imageAssetId"] = f"asset_{content['id']}_{image_role}"
        stage["templateJson"]["audioAssetId"] = f"asset_{content['id']}_{image_role}_audio"
        stage["templateJson"]["assetBundle"] = {
            "imageAssetId": stage["templateJson"]["imageAssetId"],
            "audioAssetId": stage["templateJson"]["audioAssetId"],
        }
        if stage.get("realtimeSpec"):
            stage["realtimeSpec"]["id"] = "rt_spec_generated_quality_001"
            stage["realtimeSpec"]["stageId"] = stage["id"]
            stage["realtimeSpec"]["imageAssetId"] = stage["templateJson"]["imageAssetId"]
    for asset in content["assets"]:
        asset["missionContentId"] = content["id"]
        asset_step = 4 if asset["assetRole"] == "stage_4_realtime" else asset["assetRole"][-1]
        asset["stageId"] = None if asset["assetRole"] == "hero" else f"stage_generated_quality_{asset_step}"
        asset["id"] = f"asset_{content['id']}_{asset['assetRole']}{'_audio' if asset['assetType'] == 'audio' else ''}"
        if asset["assetType"] == "image":
            asset["promptJson"] = {
                "prompt": f"{asset['assetRole']} 장면. 따뜻한 교실 느낌의 피자 조각 장면만 보여주고 no app UI, no answer panels, no readable lesson text.",
                "textRenderingPolicy": "scene_only_no_problem_text",
            }
        asset["storageUrl"] = ""
        asset["previewUrl"] = None
        asset["qaStatus"] = "pending"
        asset["approvalStatus"] = "pending"
    return content


def _generated_life_support_content() -> dict:
    base_content = next(content for content in create_demo_database().mission_contents if content.student_id == "student_life_bus")
    content = base_content.model_dump(by_alias=True)
    content["id"] = "content_generated_life_quality_001"
    content["status"] = "teacher_review"
    content["approvedByUserId"] = None
    content["approvedAt"] = None
    content["publishedAt"] = None
    content["teacherReviewSummary"] = "버스를 타기 전에 확인할 단서와 도움 요청 순서를 연습합니다."
    for stage in content["stages"]:
        stage["id"] = f"stage_generated_life_quality_{stage['step']}"
        stage["missionContentId"] = content["id"]
        image_role = "stage_4_realtime" if stage["step"] == 4 else f"stage_{stage['step']}"
        stage["templateJson"]["imageAssetId"] = f"asset_{content['id']}_{image_role}"
        stage["templateJson"]["audioAssetId"] = f"asset_{content['id']}_{image_role}_audio"
        stage["templateJson"]["assetBundle"] = {
            "imageAssetId": stage["templateJson"]["imageAssetId"],
            "audioAssetId": stage["templateJson"]["audioAssetId"],
        }
        if stage["step"] == 2:
            stage["templateJson"]["question"] = "버스를 타기 전에 무엇을 먼저 확인해야 할까요?"
            stage["templateJson"]["choices"] = [
                {"id": "a", "text": "센터로 가는 버스 번호 확인하기"},
                {"id": "b", "text": "버스가 오면 바로 타기"},
            ]
        if stage["step"] == 3:
            stage["templateType"] = "sequence_ordering"
            stage["templateJson"] = {
                "imageAssetId": stage["templateJson"]["imageAssetId"],
                "audioAssetId": stage["templateJson"]["audioAssetId"],
                "assetBundle": stage["templateJson"]["assetBundle"],
                "sourceTextLines": [],
                "sceneTextLines": [],
                "question": "버스를 타기 전에 안전하게 확인하는 순서로 놓아 보세요.",
                "cards": [
                    {"id": "look", "text": "버스 번호를 먼저 본다."},
                    {"id": "ask", "text": "헷갈리면 짧게 물어본다."},
                    {"id": "ride", "text": "맞는 버스이면 천천히 탄다."},
                ],
                "answerOrder": ["look", "ask", "ride"],
                "correctFeedback": "좋아요. 번호를 보고, 물어보고, 맞을 때 타는 순서예요.",
                "wrongFeedback": "버스를 타기 전에 번호를 먼저 확인하는 순서를 다시 볼까요?",
            }
        if stage.get("realtimeSpec"):
            stage["realtimeSpec"]["id"] = "rt_spec_generated_life_quality_001"
            stage["realtimeSpec"]["stageId"] = stage["id"]
            stage["realtimeSpec"]["imageAssetId"] = stage["templateJson"]["imageAssetId"]
    for asset in content["assets"]:
        asset["missionContentId"] = content["id"]
        asset_step = 4 if asset["assetRole"] == "stage_4_realtime" else asset["assetRole"][-1]
        asset["stageId"] = None if asset["assetRole"] == "hero" else f"stage_generated_life_quality_{asset_step}"
        asset["id"] = f"asset_{content['id']}_{asset['assetRole']}{'_audio' if asset['assetType'] == 'audio' else ''}"
        if asset["assetType"] == "image":
            asset["promptJson"] = {
                "prompt": (
                    f"{asset['assetRole']} 장면. 버스 정류장에서 센터행 버스 번호를 확인하는 실제 생활 장면을 보여주고 "
                    "no app UI, no answer panels, no readable lesson text."
                ),
                "textRenderingPolicy": "scene_only_no_problem_text",
            }
        if asset["assetType"] == "audio":
            asset["sourceText"] = "버스를 타기 전에 번호를 먼저 확인해요. 헷갈리면 선생님이나 기사님께 짧게 물어볼 수 있어요."
        asset["storageUrl"] = ""
        asset["previewUrl"] = None
        asset["qaStatus"] = "pending"
        asset["approvalStatus"] = "pending"
    return content
