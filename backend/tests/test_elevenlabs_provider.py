from app.ai.elevenlabs_provider import ElevenLabsProvider, build_teacher_narration_text
from app.core.config import Settings


def test_teacher_narration_text_adds_tags_for_eleven_v3() -> None:
    text = build_teacher_narration_text(
        "  천천히 단서를 확인해 보세요.  ",
        model_id="eleven_v3",
        enable_audio_tags=True,
    )

    assert text == "[warmly] 천천히 단서를 확인해 보세요."


def test_teacher_narration_text_keeps_plain_text_for_v2() -> None:
    text = build_teacher_narration_text(
        "천천히 단서를 확인해 보세요.",
        model_id="eleven_multilingual_v2",
        enable_audio_tags=True,
    )

    assert text == "천천히 단서를 확인해 보세요."


def test_elevenlabs_payload_uses_configured_teacher_voice_settings() -> None:
    provider = ElevenLabsProvider(
        Settings(
            elevenlabs_api_key="test-key",
            elevenlabs_voice_id="test-voice",
            elevenlabs_model_id="eleven_v3",
            elevenlabs_stability=0.42,
            elevenlabs_similarity_boost=0.82,
            elevenlabs_style=0.32,
            elevenlabs_speed=1.03,
            elevenlabs_use_speaker_boost=True,
            elevenlabs_enable_audio_tags=True,
        )
    )

    payload = provider.build_payload("좋아요. 천천히 말해볼까요?")

    assert payload["model_id"] == "eleven_v3"
    assert payload["text"].startswith("[warmly]")
    assert "[slowly]" not in payload["text"]
    assert "[short pause]" not in payload["text"]
    assert payload["voice_settings"] == {
        "stability": 0.42,
        "similarity_boost": 0.82,
        "style": 0.32,
        "speed": 1.03,
        "use_speaker_boost": True,
    }
