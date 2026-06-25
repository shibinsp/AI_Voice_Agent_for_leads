from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class DialogueCompletion:
    text: str
    provider_payload: dict


class DialogueProvider(ABC):
    name: str

    @abstractmethod
    def complete(self, *, system_prompt: str, user_prompt: str) -> DialogueCompletion:
        raise NotImplementedError

