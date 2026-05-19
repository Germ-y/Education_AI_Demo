from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 4000
    database_url: str = "postgresql+psycopg://eduyj:eduyj@localhost:5432/eduyj"
    cors_origins: str = "http://localhost:3000"
    openai_api_key: str | None = None
    openai_reasoning_model: str = "gpt-5.1"
    openai_orchestrator_model: str = "gpt-5.1"
    openai_content_model: str = "gpt-5.1"
    openai_critique_model: str = "gpt-5.1"
    openai_image_brief_model: str = "gpt-5.1"
    openai_report_model: str = "gpt-5.1"
    openai_support_profile_model: str = "gpt-5.1"
    openai_memory_model: str = "gpt-5.1"
    openai_reasoning_effort: str | None = "none"
    openai_text_verbosity: str | None = "low"
    openai_orchestrator_max_output_tokens: int = 6000
    openai_content_max_output_tokens: int = 0
    openai_critique_max_output_tokens: int = 4000
    openai_response_timeout_sec: float = 300
    openai_orchestrator_timeout_sec: float = 240
    openai_content_timeout_sec: float = 300
    openai_critique_timeout_sec: float = 240
    openai_report_timeout_sec: float = 180
    openai_support_profile_timeout_sec: float = 180
    openai_memory_timeout_sec: float = 180
    openai_content_critique_enabled: bool = False
    openai_image_model: str = "gpt-image-2"
    openai_image_timeout_sec: float = 420
    openai_realtime_model: str = "gpt-realtime-1.5"
    openai_realtime_voice: str = "marin"
    openai_realtime_voice_speed: float = 0.92
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_v3"
    elevenlabs_stability: float = 0.42
    elevenlabs_similarity_boost: float = 0.82
    elevenlabs_style: float = 0.32
    elevenlabs_speed: float = 1.08
    elevenlabs_use_speaker_boost: bool = True
    elevenlabs_enable_audio_tags: bool = False
    neis_api_key: str | None = None
    public_data_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PUBLIC_DATA_API_KEY", "DATA_GO_KR_API_KEY"),
    )
    schoolinfo_api_key: str | None = None
    public_data_sync_enabled: bool = False
    generated_assets_dir: str = str(BACKEND_DIR / "generated")
    generation_log_file: str = str(BACKEND_DIR / "logs" / "generation.log")
    demo_seed_mode: bool = True
    demo_seed_reset: bool = False
    demo_blank_start: bool = True

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
