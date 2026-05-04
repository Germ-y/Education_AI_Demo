from app.ai.prompt_registry import list_prompt_specs, load_prompt


def test_prompt_registry_loads_all_versioned_prompts() -> None:
    specs = list_prompt_specs()

    assert {spec.key for spec in specs} == {
        "orchestrator_plan",
        "mission_content_package",
        "content_quality_critique",
        "image_brief",
        "tts_script",
    }

    for spec in specs:
        prompt = load_prompt(spec.key)
        assert spec.version in prompt
        assert spec.output_schema_name


def test_prompts_keep_image_text_and_ui_text_separate() -> None:
    content_prompt = load_prompt("mission_content_package")
    image_prompt = load_prompt("image_brief")

    assert "All problem text lines must live in `templateJson`" in content_prompt
    assert '"assets"' in content_prompt
    assert "assetPlaceholders" not in content_prompt
    assert '"contentId"' not in content_prompt
    assert "The frontend renders all text from `templateJson`" in image_prompt
    assert "Do not ask the image model to render" in image_prompt


def test_generation_prompts_lock_stage_labels_and_profile_based_templates() -> None:
    orchestrator_prompt = load_prompt("orchestrator_plan")
    content_prompt = load_prompt("mission_content_package")

    assert "Template selection is profile-based, not random" in orchestrator_prompt
    assert "Template selection must be based on the orchestrator plan and student context, never arbitrary randomness." in content_prompt

    for label in ["상황 만나기", "단서 찾기", "행동 고르기", "한 번 해보기", "개념 열기", "문제 1", "문제 2", "설명해보기"]:
        assert label in orchestrator_prompt
        assert label in content_prompt


def test_generation_prompts_require_concrete_playable_micro_scenarios() -> None:
    orchestrator_prompt = load_prompt("orchestrator_plan")
    content_prompt = load_prompt("mission_content_package")
    critique_prompt = load_prompt("content_quality_critique")

    assert "Honor the teacher requested topic" in orchestrator_prompt
    assert "concrete playable micro-scenario" in content_prompt
    assert "concrete playable micro-scenario" in critique_prompt
    assert "Stage 2 must be the easiest success step" in content_prompt
    assert "Stage 3 must be a meaningful transfer" in content_prompt
    assert "very low reading load or a 2-choice limit" in orchestrator_prompt
