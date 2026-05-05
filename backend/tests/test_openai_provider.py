from app.ai.openai_provider import OpenAiProvider
from app.core.config import Settings


def test_post_retries_transient_openai_502(monkeypatch) -> None:
    import app.ai.openai_provider as openai_provider

    calls = {"count": 0}

    class FakeResponse:
        def __init__(self, status_code: int, data: dict | None = None, text: str = "") -> None:
            self.status_code = status_code
            self._data = data or {}
            self.text = text

        def json(self) -> dict:
            return self._data

    class FakeClient:
        def __init__(self, *, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, *args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                return FakeResponse(502, text="<html>Bad gateway</html>")
            return FakeResponse(200, {"output_text": "{\"ok\": true}"})

    monkeypatch.setattr(openai_provider.httpx, "Client", FakeClient)
    monkeypatch.setattr(openai_provider, "_sleep_before_retry", lambda *args, **kwargs: None)

    provider = OpenAiProvider(Settings(openai_api_key="test-key"))

    data = provider._post("/v1/responses", {"model": "gpt-5-nano"}, timeout_sec=10)

    assert calls["count"] == 2
    assert data == {"output_text": "{\"ok\": true}"}


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


def test_json_response_disables_reasoning_for_gpt_5_1(monkeypatch) -> None:
    captured: dict = {}
    settings = Settings(openai_api_key="test-key", openai_reasoning_effort="none", openai_text_verbosity="low")
    provider = OpenAiProvider(settings)

    def fake_post(path: str, payload: dict, *, timeout_sec: float) -> dict:
        captured["path"] = path
        captured["payload"] = payload
        captured["timeout_sec"] = timeout_sec
        return {"output_text": "{\"ok\": true}", "usage": {"output_tokens_details": {"reasoning_tokens": 0}}}

    monkeypatch.setattr(provider, "_post", fake_post)

    data, usage = provider.create_json_response(
        model="gpt-5.1",
        instructions="JSON만 반환합니다.",
        input_snapshot={"topic": "테스트"},
        timeout_sec=10,
        max_output_tokens=1200,
    )

    assert data == {"ok": True}
    assert usage == {"output_tokens_details": {"reasoning_tokens": 0}}
    assert captured["path"] == "/v1/responses"
    assert captured["payload"]["reasoning"] == {"effort": "none"}
    assert captured["payload"]["text"] == {"verbosity": "low"}
    assert captured["payload"]["max_output_tokens"] == 1200


def test_json_response_downgrades_none_reasoning_for_older_gpt_5_models(monkeypatch) -> None:
    captured: dict = {}
    provider = OpenAiProvider(Settings(openai_api_key="test-key", openai_reasoning_effort="none"))

    def fake_post(path: str, payload: dict, *, timeout_sec: float) -> dict:
        captured["payload"] = payload
        return {"output_text": "{\"ok\": true}"}

    monkeypatch.setattr(provider, "_post", fake_post)

    provider.create_json_response(
        model="gpt-5-nano",
        instructions="JSON만 반환합니다.",
        input_snapshot={"topic": "테스트"},
        timeout_sec=10,
    )

    assert captured["payload"]["reasoning"] == {"effort": "minimal"}
