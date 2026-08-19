from copy import deepcopy
from threading import RLock

from .models import Mission


class InMemoryMissionRepository:
    """Demo fallback implementing the same boundary as the Cockroach repository."""

    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}
        self._lock = RLock()

    def save(self, mission: Mission) -> Mission:
        with self._lock:
            self._missions[mission.id] = deepcopy(mission)
            return deepcopy(mission)

    def get(self, mission_id: str) -> Mission | None:
        with self._lock:
            mission = self._missions.get(mission_id)
            return deepcopy(mission) if mission else None

    def relevant_receipts(self, limit: int = 3) -> list[str]:
        with self._lock:
            receipts = [m.receipt.receipt_sha256[:12] for m in self._missions.values() if m.receipt]
            return receipts[-limit:]

