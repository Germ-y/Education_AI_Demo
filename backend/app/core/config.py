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
    openai_image_model: str = "gpt-image-2"
    openai_realtime_model: str = "gpt-realtime"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    neis_api_key: str | None = None
    public_data_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PUBLIC_DATA_API_KEY", "DATA_GO_KR_API_KEY"),
    )
    schoolinfo_api_key: str | None = None
    public_data_sync_enabled: bool = False
    generated_assets_dir: str = str(BACKEND_DIR / "generated")
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
