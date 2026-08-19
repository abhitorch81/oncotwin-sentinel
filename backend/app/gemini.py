import json
from typing import Any

from google import genai

from .config import Settings


class GeminiNarrator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _client(self) -> genai.Client:
        if self.settings.google_genai_use_vertexai:
            return genai.Client(
                vertexai=True,
                project=self.settings.google_cloud_project,
                location=self.settings.google_cloud_location,
            )
        return genai.Client(api_key=self.settings.google_api_key)

    async def summarize(self, question: str, evidence: Any) -> str:
        prompt = f"""
You are OncoTwin's cancer data reliability narrator.
Answer the question using only the DataHub evidence below.
Clearly separate metadata confidence from clinical conclusions.
Never provide medical advice. Mention the dataset URN when present.
Return at most 130 words.

Question: {question}
DataHub evidence: {json.dumps(evidence, default=str)[:15000]}
"""
        response = await self._client().aio.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
        )
        return response.text or "No grounded summary was produced."

