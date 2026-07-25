from __future__ import annotations


class ReservationTable:
    """
    Manages node and edge occupancy over time (turns).
    Essential for collision-free Multi-Agent Pathfinding.
    """
    def __init__(self) -> None:
        #  [node_name, turno] -> quantidade de drones
        self._node_occupancy: dict[tuple[str, int], int] = {}

        #  [node_a, node_b, turn] -> quantidade de drones em transito
        self._edge_occupancy: dict[tuple[str, str, int], int] = {}

    def reserve_node(self, node_name: str, turn: int) -> None:
        """
        Records the occupancy of a drone at a node during a specific shift
        """
        key = (node_name, turn)
        self._node_occupancy[key] = self._node_occupancy.get(key, 0) + 1

    def reserve_edge(self, src: str, dst: str, turn: int) -> None:
        """Records the occupancy of an edge during a transit in a shift."""
        u, v = sorted([src, dst])
        key = (u, v, turn)
        self._edge_occupancy[key] = self._edge_occupancy.get(key, 0) + 1

    def get_node_occupancy(self, node_name: str, turn: int) -> int:
        """Returns how many drones will be at the node this shift."""
        return self._node_occupancy.get((node_name, turn), 0)

    def get_edge_occupancy(self, src: str, dst: str, turn: int) -> int:
        """Returns how many drones will be using this connection this shift."""
        u, v = sorted([src, dst])
        return self._edge_occupancy((u, v, turn), 0)

    def clean(self) -> None:
        """Clers the reserve table"""
        self._node_occupancy.clear()
        self._edge_occupancy.clear()
