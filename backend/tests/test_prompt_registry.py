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
        "support_profile_draft",
        "student_memory_brief",
    }

    for spec in specs:
        prompt = load_prompt(spec.key)
        assert spec.version in prompt
        if spec.key != "teacher_report_draft":
            assert spec.output_schema_name


def test_prompts_keep_image_text_and_ui_text_separate() -> None:
    content_prompt = load_prompt("mission_content_package")
    image_prompt = load_prompt("image_brief")

    assert "문제를 푸는 데 필요한 식, 문장, 표 값, 카드 문구, 선택지, 빈칸, 정답 후보는 `templateJson`에 넣습니다." in content_prompt
    assert '"assets"' in content_prompt
    assert "assetPlaceholders" not in content_prompt
    assert '"contentId"' not in content_prompt
    assert "문제 문장, 보기, 정답, 피드백은 앱 UI가 보여줍니다." in image_prompt
    assert "학생이 읽고 판단할 정확한 자료와 문항은 앱 UI가 보여줍니다." in image_prompt
    assert "이미지는 목적 있는 수업 장면을 보여줍니다." in image_prompt
    assert "사람은 필요할 때만 보조 맥락으로 둡니다." in image_prompt


def test_generation_prompts_lock_stage_labels_and_randomized_templates() -> None:
    orchestrator_prompt = load_prompt("orchestrator_plan")
    content_prompt = load_prompt("mission_content_package")

    assert "templateRandomization.forcedStageTemplates" in orchestrator_prompt
    assert "2~3단계 `templateType`은 그 값을 그대로 사용합니다." in orchestrator_prompt
    assert "오케스트레이터의 `scenarioSpine`이 시나리오 source of truth입니다." in content_prompt

    for label in ["상황 만나기", "단서 찾기", "행동 고르기", "한 번 해보기", "개념 열기", "문제 1", "문제 2", "설명해보기"]:
        assert label in orchestrator_prompt
        assert label in content_prompt


def test_generation_prompts_require_concrete_playable_micro_scenarios() -> None:
    orchestrator_prompt = load_prompt("orchestrator_plan")
    content_prompt = load_prompt("mission_content_package")
    critique_prompt = load_prompt("content_quality_critique")

    assert "선생님 요청이 있으면 최우선입니다." in orchestrator_prompt
    assert "학생 기억장치, 이전 수업, 지원 프로필, 학교 시간표, 사례 목표는 이번 생성 입력에 없다고 가정합니다." in orchestrator_prompt
    assert "정답은 이미지 안에 있지 않습니다." in orchestrator_prompt
    assert "목표는 학년 수준의 학습 콘텐츠입니다." in orchestrator_prompt
    assert "목표는 실제 생활 장면에서 다음 행동이나 말을 고르는 시나리오입니다." in orchestrator_prompt
    assert "문제는 UI가 풀고, 이미지는 맥락만 보여준다" in content_prompt
    assert "답은 개념, 조건 비교, 자료 해석, 문장 이해, 수량 관계, 계산 과정, 설명 논리 중 하나" in content_prompt
    assert "답은 실제 다음 행동, 물어볼 말, 도움 요청, 순서 확인, 선택 전 확인으로 이어져야 합니다." in content_prompt
    assert "구체적으로 플레이 가능한 4단계 수업" in critique_prompt
    assert "실제 학습 판단을 요구합니다." in critique_prompt
    assert "실제 다음 행동이나 말을 고르게 합니다." in critique_prompt
    assert "source of truth" in critique_prompt
    assert "이미지는 문제를 대신 풀어 주지 않고" in critique_prompt
    assert "학년에 맞는 자료 길이, 어휘, 추론 수준, 보기 수" in orchestrator_prompt
    assert "초등 고학년과 중학생은 문장을 짧게 하더라도 소재와 표현을 유치하게 낮추지 않습니다." in content_prompt
    assert "학년 존중감을 지킵니다." in critique_prompt
    assert "2단계는 기본 문제입니다." in content_prompt
    assert "3단계는 응용 예제입니다." in content_prompt
    assert "초등 저학년은 문장과 선택지를 줄이되 사고 자체를 지나치게 낮추지 않습니다." in content_prompt
    assert "색/물건 이름만 묻는 단순 회상" in critique_prompt


def test_generation_prompts_require_teacher_like_audio_and_core_realtime_rubric() -> None:
    content_prompt = load_prompt("mission_content_package")

    assert "차분한 선생님이 옆에서 말하듯" in content_prompt
    assert "오디오 asset의 `sourceText`는 단계 도입 내레이션입니다." in content_prompt
    assert "정답을 말하지 말고" in content_prompt
    assert "`postPracticeReflection`은 문자열 배열입니다." in content_prompt
    assert "`rubric` 항목은" in content_prompt
    assert "learning_focus`는 풀이 기준이나 설명을 말하게 합니다." in content_prompt
