from __future__ import annotations

from graph.graph_manager import Graph
from models.drone import Drone


class Scheduler:
    """Schedule each move
    based on the available
    capacities."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def _get_initial_occupancy(
        self,
        active_drones: list[Drone],
    ) -> dict[str, int]:
        """Map how many drones are in each hub at the start of the turn."""
        occupancy = {name: 0 for name in self.graph.nodes}
        for drone in active_drones:
            occupancy[drone.current_hub] += 1
        return occupancy

    def assign_moves(
        self,
        active_drones: list[Drone],
    ) -> list[dict[str, object]]:
        """Return the set of moves authorized for this turn."""
        occupancy = self._get_initial_occupancy(active_drones)
        link_occupancy: dict[tuple[str, str], int] = {}
        moves: list[dict[str, object]] = []

        for drone in sorted(active_drones, key=lambda item: item.id):
            next_hub = drone.get_next_hub()
            if not next_hub or drone.transit_timer > 0:
                continue

            edge = self.graph.get_edge(drone.current_hub, next_hub)
            if edge is None:
                continue

            link_key = tuple(sorted((drone.current_hub, next_hub)))
            target_node = self.graph.nodes.get(next_hub)
            if target_node is None:
                continue

            if (
                link_occupancy.get(link_key, 0) < edge.max_link_capacity
                and occupancy[next_hub] < target_node.max_drones
            ):
                occupancy[drone.current_hub] -= 1
                occupancy[next_hub] += 1
                link_occupancy[link_key] = link_occupancy.get(link_key, 0) + 1
                moves.append(
                    {"drone": drone, "target": next_hub, "edge": edge}
                )

        return moves
