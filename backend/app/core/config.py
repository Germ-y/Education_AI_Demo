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
    openai_reasoning_model: str = "gpt-5.5"
    openai_response_timeout_sec: float = 180
    openai_image_model: str = "gpt-image-2"
    openai_image_timeout_sec: float = 360
    openai_realtime_model: str = "gpt-realtime-1.5"
    openai_realtime_voice: str = "marin"
    openai_realtime_voice_speed: float = 0.92
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_v3"
    elevenlabs_stability: float = 0.42
    elevenlabs_similarity_boost: float = 0.82
    elevenlabs_style: float = 0.32
    elevenlabs_speed: float = 1.03
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

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
