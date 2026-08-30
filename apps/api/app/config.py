from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OncoTwin Sentinel: Living Evidence"
    app_version: str = "13.0.0-m1"
    app_env: str = "development"
    demo_mode: bool = True
    firestore_enabled: bool = False
    firestore_database: str = "(default)"
    google_cloud_project: str = ""
    google_cloud_location: str = "global"
    google_genai_use_vertexai: bool = True
    gemini_model: str = "gemini-3.5-flash"
    governed_voice_enabled: bool = True
    live_voice_model: str = "gemini-3.5-transcribe-live-preview"
    live_voice_location: str = "global"
    adk_enabled: bool = False
    adk_model: str = "gemini-3.5-flash"
    allowed_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.allowed_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
