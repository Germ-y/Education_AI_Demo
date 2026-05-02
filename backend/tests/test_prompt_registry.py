from app.ai.prompt_registry import list_prompt_specs, load_prompt


def test_prompt_registry_loads_all_versioned_prompts() -> None:
    specs = list_prompt_specs()

    assert {spec.key for spec in specs} == {"orchestrator_plan", "mission_content_package", "image_brief", "tts_script"}

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
