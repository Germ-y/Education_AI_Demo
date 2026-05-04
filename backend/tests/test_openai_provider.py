from app.ai.openai_provider import OpenAiProvider
from app.core.config import Settings


def test_realtime_client_secret_uses_configured_voice(monkeypatch) -> None:
    captured: dict = {}
    settings = Settings(openai_api_key="test-key", openai_realtime_voice="marin", openai_realtime_voice_speed=0.92)
    provider = OpenAiProvider(settings)

    def fake_post(path: str, payload: dict, *, timeout_sec: float) -> dict:
        captured["path"] = path
        captured["payload"] = payload
        captured["timeout_sec"] = timeout_sec
        return {"value": "secret", "expires_at": 1_800_000_000}

    monkeypatch.setattr(provider, "_post", fake_post)

    secret = provider.create_realtime_client_secret(instructions="짧게 한국어로 말합니다.", model="gpt-realtime-1.5")

    assert secret["value"] == "secret"
    assert captured["path"] == "/v1/realtime/client_secrets"
    session = captured["payload"]["session"]
    assert session["model"] == "gpt-realtime-1.5"
    assert session["audio"]["output"] == {"voice": "marin", "speed": 0.92}
