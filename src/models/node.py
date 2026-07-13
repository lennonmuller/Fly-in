from dataclasses import dataclass
from typing import Optional


@dataclass
class Node:
    """Represents a zone in the map. (Hub)"""
    name: str
    x: int
    y: int
    type: str = "normal"
    max_drones: int = 1
    color: Optional[str] = None
