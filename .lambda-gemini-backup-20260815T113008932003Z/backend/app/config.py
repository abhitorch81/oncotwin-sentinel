from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    demo_mode: bool = True
    allowed_origins: str = "http://localhost:8080"

    datahub_gms_url: str = "http://127.0.0.1:8080"
    datahub_gms_token: str = ""
    datahub_admin_token: str = ""
    datahub_mcp_command: str = "uvx"
    datahub_mcp_package: str = "mcp-server-datahub@latest"
    tools_is_mutation_enabled: bool = True

    google_genai_use_vertexai: bool = True
    google_cloud_project: str = ""
    # Vertex AI's global endpoint avoids the regional model-availability loop
    # that Gemini CLI can hit when a preview/default model is not in one region.
    google_cloud_location: str = "global"
    bigquery_location: str = "asia-south1"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    writeback_approval_secret: str = "change-me"
    analytics_agent_url: str = "http://localhost:8100"
    mission_store_path: str = "/tmp/oncotwin-missions"

    # OncoTwin MemoryMesh: CockroachDB agent memory
    database_url: str = ""
    memory_tenant_id: str = "11111111-1111-1111-1111-111111111111"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
