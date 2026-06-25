from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CrmSyncResult:
    synced: bool
    provider_payload: dict[str, Any]


class CrmProvider(ABC):
    name: str

    @abstractmethod
    def sync_qualification(self, payload: dict[str, Any]) -> CrmSyncResult:
        raise NotImplementedError

