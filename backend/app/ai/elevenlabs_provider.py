import logging
import time
from pathlib import Path

import httpx

from app.ai.provider_errors import ProviderConfigurationError, ProviderOutputError, ProviderRequestError
from app.core.config import Settings

logger = logging.getLogger(__name__)


def build_teacher_narration_text(source_text: str, *, model_id: str, enable_audio_tags: bool) -> str:
    text = " ".join(source_text.strip().split())
    if not text or not enable_audio_tags or not model_id.startswith("eleven_v3"):
        return text
    if text.startswith("["):
        return text
    return f"[warmly] [slowly] {text} [short pause]"


class ElevenLabsProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_payload(self, source_text: str) -> dict:
        source_text_for_provider = build_teacher_narration_text(
            source_text,
            model_id=self.settings.elevenlabs_model_id,
            enable_audio_tags=self.settings.elevenlabs_enable_audio_tags,
        )
        return {
            "text": source_text_for_provider,
            "model_id": self.settings.elevenlabs_model_id,
            "voice_settings": {
                "stability": self.settings.elevenlabs_stability,
                "similarity_boost": self.settings.elevenlabs_similarity_boost,
                "style": self.settings.elevenlabs_style,
                "speed": self.settings.elevenlabs_speed,
                "use_speaker_boost": self.settings.elevenlabs_use_speaker_boost,
            },
        }

    def create_speech_file(self, *, source_text: str, output_path: Path, timeout_sec: float = 60) -> Path:
        if not self.settings.elevenlabs_api_key:
            raise ProviderConfigurationError("ELEVENLABS_API_KEY_MISSING", "ELEVENLABS_API_KEY가 없어 TTS 생성을 실행할 수 없습니다.")
        if not self.settings.elevenlabs_voice_id:
            raise ProviderConfigurationError("ELEVENLABS_VOICE_ID_MISSING", "ELEVENLABS_VOICE_ID가 없어 TTS 생성을 실행할 수 없습니다.")

        payload = self.build_payload(source_text)
        started_at = time.perf_counter()
        logger.info(
            "elevenlabs.speech.started output_path=%s text_length=%s model=%s tags=%s timeout_sec=%s",
            output_path,
            len(payload["text"]),
            self.settings.elevenlabs_model_id,
            self.settings.elevenlabs_enable_audio_tags,
            timeout_sec,
        )
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.settings.elevenlabs_voice_id}"
        try:
            with httpx.Client(timeout=timeout_sec) as client:
                response = client.post(
                    url,
                    headers={"xi-api-key": self.settings.elevenlabs_api_key, "Content-Type": "application/json"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise ProviderRequestError("ELEVENLABS_REQUEST_FAILED", f"ElevenLabs 요청 실패: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderRequestError("ELEVENLABS_HTTP_ERROR", f"ElevenLabs HTTP {response.status_code}: {response.text[:500]}")
        if not response.content:
            raise ProviderOutputError("ELEVENLABS_AUDIO_EMPTY", "ElevenLabs 응답 오디오가 비어 있습니다.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        logger.info(
            "elevenlabs.speech.returned output_path=%s bytes=%s elapsed_sec=%.1f",
            output_path,
            len(response.content),
            time.perf_counter() - started_at,
        )
        return output_path
