from dataclasses import dataclass


@dataclass
class Egde:
    """Represents a bidiretional conexion between two hubs."""
    source: str
    destination: str
    max_link_capacity: int = 1
