from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 4000
    database_url: str = "postgresql+psycopg://eduyj:eduyj@localhost:5432/eduyj"
    openai_api_key: str | None = None
    openai_image_model: str = "gpt-image-2"
    openai_realtime_model: str = "gpt-realtime"
    public_data_sync_enabled: bool = False
    demo_seed_mode: bool = True
    demo_teacher_email: str = "teacher.demo@eduyj.local"
    demo_student_code: str = "STAR-001"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
