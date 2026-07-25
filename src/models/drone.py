from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Drone:
    """Represent a drone and its movement state."""

    id: int
    path: list[str]
    current_index: int = 0
    transit_timer: int = 0
    target_node: str | None = None

    @property
    def name(self) -> str:
        return f"D{self.id}"

    @property
    def current_hub(self) -> str:
        if not self.path:
            raise ValueError("Drone path is empty")
        return self.path[self.current_index]

    def get_next_hub(self) -> str | None:
        if self.current_index + 1 < len(self.path):
            return self.path[self.current_index + 1]
        return None
