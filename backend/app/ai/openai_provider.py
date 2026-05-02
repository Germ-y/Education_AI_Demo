import json
from typing import Any

import httpx

from app.ai.provider_errors import ProviderConfigurationError, ProviderOutputError, ProviderRequestError
from app.core.config import Settings


class OpenAiProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_json_response(
        self,
        *,
        model: str,
        instructions: str,
        input_snapshot: dict[str, Any],
        timeout_sec: float = 90,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if not self.settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY_MISSING", "OPENAI_API_KEY가 없어 실제 AI 생성을 실행할 수 없습니다.")

        payload = {
            "model": model,
            "instructions": instructions,
            "input": json.dumps(input_snapshot, ensure_ascii=False),
            "store": True,
        }
        response = self._post("/v1/responses", payload, timeout_sec=timeout_sec)
        output_text = _extract_output_text(response)
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderOutputError("OPENAI_OUTPUT_JSON_PARSE_FAILED", "OpenAI 응답을 JSON으로 파싱할 수 없습니다.") from exc
        if not isinstance(parsed, dict):
            raise ProviderOutputError("OPENAI_OUTPUT_NOT_OBJECT", "OpenAI 응답 JSON 최상위 값은 object여야 합니다.")
        usage = response.get("usage") if isinstance(response.get("usage"), dict) else None
        return parsed, usage

    def create_realtime_client_secret(
        self,
        *,
        instructions: str,
        model: str,
        ttl_seconds: int = 600,
        timeout_sec: float = 30,
    ) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY_MISSING", "OPENAI_API_KEY가 없어 realtime client secret을 발급할 수 없습니다.")

        payload = {
            "expires_after": {"anchor": "created_at", "seconds": ttl_seconds},
            "session": {
                "type": "realtime",
                "model": model,
                "instructions": instructions,
                "output_modalities": ["audio"],
            },
        }
        data = self._post("/v1/realtime/client_secrets", payload, timeout_sec=timeout_sec)
        value = data.get("value") or data.get("client_secret", {}).get("value")
        expires_at = data.get("expires_at") or data.get("client_secret", {}).get("expires_at")
        if not value or not expires_at:
            raise ProviderOutputError("OPENAI_REALTIME_SECRET_INVALID", "OpenAI realtime client secret 응답 형식이 올바르지 않습니다.")
        return {"value": value, "expiresAt": expires_at, "raw": data}

    def _post(self, path: str, payload: dict[str, Any], *, timeout_sec: float) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=timeout_sec) as client:
                response = client.post(
                    f"https://api.openai.com{path}",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ProviderRequestError("OPENAI_REQUEST_FAILED", f"OpenAI 요청 실패: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderRequestError("OPENAI_HTTP_ERROR", f"OpenAI HTTP {response.status_code}: {response.text[:500]}")
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderOutputError("OPENAI_RESPONSE_JSON_PARSE_FAILED", "OpenAI HTTP 응답을 JSON으로 파싱할 수 없습니다.") from exc
        if not isinstance(data, dict):
            raise ProviderOutputError("OPENAI_RESPONSE_NOT_OBJECT", "OpenAI HTTP 응답 최상위 값은 object여야 합니다.")
        return data


def _extract_output_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    chunks: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    text = "".join(chunks).strip()
    if not text:
        raise ProviderOutputError("OPENAI_OUTPUT_TEXT_MISSING", "OpenAI 응답에서 output_text를 찾을 수 없습니다.")
    return text
