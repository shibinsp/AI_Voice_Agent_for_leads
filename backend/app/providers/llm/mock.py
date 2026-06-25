from app.providers.llm.base import DialogueCompletion, DialogueProvider


class MockDialogueProvider(DialogueProvider):
    name = "mock"

    def complete(self, *, system_prompt: str, user_prompt: str) -> DialogueCompletion:
        return DialogueCompletion(
            text="Understood. I will capture the qualification details and route this for follow-up.",
            provider_payload={"mock": True, "system_prompt": system_prompt[:120], "input_size": len(user_prompt)},
        )

