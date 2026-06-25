from app.core.config import Settings
from app.providers.llm.base import DialogueProvider
from app.providers.llm.mock import MockDialogueProvider
from app.providers.llm.openai_compatible import OpenAICompatibleDialogueProvider


def build_dialogue_provider(settings: Settings) -> DialogueProvider:
    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleDialogueProvider(settings)
    return MockDialogueProvider()

