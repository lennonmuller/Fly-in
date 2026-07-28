from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Drone:
    """Represent a drone and its movement state."""

    id: int
    path: list[str]
    current_index: int = 0

    @property
    def name(self) -> str:
        return f"D{self.id}"

    @property
    def current_location(self) -> str:
        """Retorna onde o drone está neste exato turno."""
        if not self.path or self.current_index >= len(self.path):
            raise ValueError("Drone path is exhausted or empty")
        return self.path[self.current_index]
