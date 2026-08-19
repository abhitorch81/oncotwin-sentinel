from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    demo_mode: bool = True
    app_name: str = "OncoTwin Sentinel: Living Evidence"
    app_version: str = "12.0.0"
    app_edition: str = "agentic-multimodal"
    medical_use: str = "synthetic_research_only"
    human_approval_required: bool = True
    allowed_origins: str = "http://localhost:8080"

    datahub_gms_url: str = "http://127.0.0.1:8080"
    datahub_gms_token: str = ""
    datahub_admin_token: str = ""
    datahub_mcp_command: str = "uvx"
    datahub_mcp_package: str = "mcp-server-datahub@latest"
    tools_is_mutation_enabled: bool = False

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

    # OncoTwin MemoryMesh: AWS Lambda + Gemini vectors
    memory_vectorizer_url: str = ""
    memory_vectorizer_token: str = ""
    memory_vectorizer_timeout_seconds: float = 60.0

    # CockroachDB Operations Agent: official MCP server + ccloud + Agent Skills.
    # MCP write tools are deliberately never enabled by the application.
    cockroach_mcp_enabled: bool = False
    cockroach_mcp_transport: str = "cloud_http"
    cockroach_mcp_url: str = "https://cockroachlabs.cloud/mcp"
    cockroach_mcp_api_key: str = ""
    cockroach_mcp_cluster_id: str = ""
    cockroach_mcp_command: str = "cockroachdb-mcp-server"
    cockroach_mcp_args_json: str = "[]"
    cockroach_mcp_timeout_seconds: float = 30.0
    cockroach_skill_path: str = ".agents/skills/reviewing-cluster-health/SKILL.md"
    ccloud_command: str = "ccloud"
    ccloud_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
