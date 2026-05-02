import pytest

from app.api.routes.ai import _mission_from_generation
from app.data.demo_data import create_demo_database
from app.domain.schemas import ContentAsset, ContentStage, MissionContent
from app.services.content_quality import ContentQualityError, validate_mission_content_quality, validate_orchestrator_plan_quality


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

    assert mission.id == "content_generated_schema_check"
    assert mission.status == "teacher_review"
    assert len([asset for asset in mission.assets if asset.asset_type == "image"]) == 5
    assert len([asset for asset in mission.assets if asset.asset_type == "audio"]) == 5


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

    with pytest.raises(ContentQualityError, match="내부 영문 용어"):
        validate_mission_content_quality(
            mission,
            case_file=_fraction_case_file(),
            orchestrator_plan=_valid_learning_plan(),
        )


def test_mission_quality_respects_student_choice_limit() -> None:
    content = _generated_fraction_content()
    mission = MissionContent.model_validate(content)
    case_file = _fraction_case_file()
    case_file["profile"]["profileJson"]["choiceCountLimit"] = 2

    with pytest.raises(ContentQualityError, match="선택지 제한"):
        validate_mission_content_quality(
            mission,
            case_file=case_file,
            orchestrator_plan=_valid_learning_plan(),
        )


def test_mission_quality_rejects_ui_text_inside_image_prompt() -> None:
    content = _generated_fraction_content()
    content["assets"][1]["promptJson"]["prompt"] += " 전체는 몇 조각인가요?"
    mission = MissionContent.model_validate(content)

    with pytest.raises(ContentQualityError, match="UI 문구"):
        validate_mission_content_quality(
            mission,
            case_file=_fraction_case_file(),
            orchestrator_plan=_valid_learning_plan(),
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
                "studentTitle": "전체 세기",
                "purpose": "전체 조각 수를 먼저 세게 합니다.",
            },
            {
                "step": 3,
                "stageRole": "applied_problem",
                "templateType": "blank_fill",
                "studentTitle": "분수 넣기",
                "purpose": "고른 수와 전체 수를 분수 자리에 연결합니다.",
            },
            {
                "step": 4,
                "stageRole": "realtime_practice",
                "templateType": "realtime_teach_back",
                "studentTitle": "말로 설명하기",
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


def _generated_fraction_content() -> dict:
    base_content = next(content for content in create_demo_database().mission_contents if content.student_id == "student_learning_fraction")
    content = base_content.model_dump(by_alias=True)
    content["id"] = "content_generated_quality_001"
    content["status"] = "teacher_review"
    content["approvedByUserId"] = None
    content["approvedAt"] = None
    content["publishedAt"] = None
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
                "prompt": f"{asset['assetRole']} 장면. 따뜻한 교실 느낌의 피자 조각 장면만 보여주고 문제 문장, 선택지, 정답, 힌트 텍스트는 넣지 않습니다.",
                "textRenderingPolicy": "scene_only_no_problem_text",
            }
        asset["storageUrl"] = ""
        asset["previewUrl"] = None
        asset["qaStatus"] = "pending"
        asset["approvalStatus"] = "pending"
    return content
