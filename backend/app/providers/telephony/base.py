from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CallRequest:
    phone_number: str
    caller_id: str | None
    from_number: str | None
    script_key: str
    language: str
    lead_id: int
    lead_context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CallStartResult:
    provider: str
    provider_call_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class TelephonyProvider(ABC):
    name: str

    @abstractmethod
    async def place_call(self, request: CallRequest) -> CallStartResult:
        raise NotImplementedError

