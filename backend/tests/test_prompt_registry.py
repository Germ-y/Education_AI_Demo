from app.ai.prompt_registry import list_prompt_specs, load_prompt


def test_prompt_registry_loads_all_versioned_prompts() -> None:
    specs = list_prompt_specs()

    assert {spec.key for spec in specs} == {
        "orchestrator_plan",
        "mission_content_package",
        "content_quality_critique",
        "image_brief",
        "tts_script",
        "teacher_report_draft",
    }

    for spec in specs:
        prompt = load_prompt(spec.key)
        assert spec.version in prompt
        if spec.key != "teacher_report_draft":
            assert spec.output_schema_name


def test_prompts_keep_image_text_and_ui_text_separate() -> None:
    content_prompt = load_prompt("mission_content_package")
    image_prompt = load_prompt("image_brief")

    assert "모든 문제 텍스트는 `templateJson`에 넣습니다." in content_prompt
    assert '"assets"' in content_prompt
    assert "assetPlaceholders" not in content_prompt
    assert '"contentId"' not in content_prompt
    assert "프론트엔드는 문제 UI 텍스트를 모두 `templateJson`에서 렌더링합니다." in image_prompt
    assert "문제 UI를 이미지에 그리라고 요청하지 않습니다." in image_prompt
    assert "학습 근거 사물이 화면의 주인공이어야 합니다." in image_prompt
    assert "사람은 필요할 때만 보조 맥락으로 둡니다." in image_prompt


def test_generation_prompts_lock_stage_labels_and_randomized_templates() -> None:
    orchestrator_prompt = load_prompt("orchestrator_plan")
    content_prompt = load_prompt("mission_content_package")

    assert "templateRandomization.forcedStageTemplates" in orchestrator_prompt
    assert "백엔드가 매 생성마다 후보 중 랜덤으로 정합니다." in orchestrator_prompt
    assert "오케스트레이터 계획과 학생 맥락에 근거" in content_prompt

    for label in ["상황 만나기", "단서 찾기", "행동 고르기", "한 번 해보기", "개념 열기", "문제 1", "문제 2", "설명해보기"]:
        assert label in orchestrator_prompt
        assert label in content_prompt


def test_generation_prompts_require_concrete_playable_micro_scenarios() -> None:
    orchestrator_prompt = load_prompt("orchestrator_plan")
    content_prompt = load_prompt("mission_content_package")
    critique_prompt = load_prompt("content_quality_critique")

    assert "선생님 요청 주제를 최우선으로 둡니다." in orchestrator_prompt
    assert "새 요청 주제가 저장된 사례 목표와 다르면" in orchestrator_prompt
    assert "하나의 감정적으로 연결된 작은 시나리오" in content_prompt
    assert "구체적으로 플레이 가능한 작은 시나리오" in critique_prompt
    assert "source of truth" in critique_prompt
    assert "학습 근거가 시각적으로 충분히 크게 보입니다." in critique_prompt
    assert "학년 존중감" in orchestrator_prompt
    assert "고학년 학생에게 지나치게 유치한 상황" in content_prompt
    assert "학년 존중감" in critique_prompt
    assert "읽기 부담은 낮추되 학년 존중감을 지킵니다." in critique_prompt
    assert "2단계는 같은 anchor를 이용한 가장 쉬운 성공입니다." in content_prompt
    assert "3단계는 한 단계 깊어진 전이입니다." in content_prompt
    assert "`readingLoad`가 `very_low`이거나 `choiceCountLimit`이 2" in orchestrator_prompt
    assert "색/물건 이름만 묻는 단순 회상" in critique_prompt


def test_generation_prompts_require_teacher_like_audio_and_core_realtime_rubric() -> None:
    content_prompt = load_prompt("mission_content_package")

    assert "차분한 선생님이 옆에서 말하듯" in content_prompt
    assert "시스템 알림처럼 들리면 안 됩니다." in content_prompt
    assert "45~90자" in content_prompt
    assert "오디오는 장면, 이유, 다음 시도를 연결" in content_prompt
    assert "단일 핵심 목표 행동" in content_prompt
    assert "찾는 자료 단서를 말하며 도움을 요청한다" in content_prompt
