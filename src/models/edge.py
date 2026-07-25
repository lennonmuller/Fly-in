from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    """Represent a bidirectional connection between two hubs."""
    source: str
    destination: str
    max_link_capacity: int = 1
