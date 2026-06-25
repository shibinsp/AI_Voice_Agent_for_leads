from __future__ import annotations

import httpx

from app.core.config import Settings
from app.providers.llm.base import DialogueCompletion, DialogueProvider


class OpenAICompatibleDialogueProvider(DialogueProvider):
    name = "openai_compatible"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete(self, *, system_prompt: str, user_prompt: str) -> DialogueCompletion:
        if not self.settings.llm_base_url or not self.settings.llm_api_key:
            raise RuntimeError("LLM_BASE_URL and LLM_API_KEY are required")
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        # OpenRouter uses these for attribution/ranking; harmless for other providers.
        if self.settings.llm_referer:
            headers["HTTP-Referer"] = self.settings.llm_referer
        if self.settings.llm_title:
            headers["X-Title"] = self.settings.llm_title
        with httpx.Client(timeout=20) as client:
            response = client.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return DialogueCompletion(text=text, provider_payload=data)

