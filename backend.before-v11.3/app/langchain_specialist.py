from typing import Any

from datahub.sdk.main_client import DataHubClient
from datahub_agent_context.langchain_tools import build_langchain_tools
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import Settings


class DataHubLangChainSpecialist:
    """Official Agent Context Kit tools wired to a Gemini LangChain specialist."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def _agent(self):
        datahub_client = DataHubClient.from_env()
        tools = build_langchain_tools(datahub_client, include_mutations=False)
        model_options: dict[str, Any] = {
            "model": self.settings.gemini_model,
            "temperature": 0,
            "vertexai": self.settings.google_genai_use_vertexai,
            "location": self.settings.google_cloud_location,
        }
        if self.settings.google_cloud_project:
            model_options["project"] = self.settings.google_cloud_project
        if self.settings.google_api_key and not self.settings.google_genai_use_vertexai:
            model_options["google_api_key"] = self.settings.google_api_key
        model = ChatGoogleGenerativeAI(**model_options)
        return create_agent(
            model,
            tools=tools,
            system_prompt=(
                "You are OncoTwin's cancer-data reliability specialist. Always use DataHub tools before answering. "
                "Inspect the asset, schema, ownership and lineage. Include exact DataHub URNs. "
                "Discuss research-data reliability only; never provide diagnosis or medical advice."
            ),
        )

    async def ask(self, question: str, asset_urn: str) -> dict[str, Any]:
        prompt = f"{question}\nStart with this candidate asset when relevant: {asset_urn}"
        result = await self._agent().ainvoke({"messages": [{"role": "user", "content": prompt}]})
        final_message = result["messages"][-1]
        content = getattr(final_message, "content", str(final_message))
        return {"answer": content, "message_count": len(result["messages"])}
