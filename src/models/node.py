from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Node:
    """Represent a zone in the map."""

    name: str
    x: int
    y: int
    type: str = "normal"
    max_drones: int = 1
    color: str | None = None

    @property
    def cost(self) -> int:
        """Return cost between turns to entry in restricted"""
        if self.type == "restricted":
            return 2
        return 1
