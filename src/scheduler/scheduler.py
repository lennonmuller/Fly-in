from __future__ import annotations

from graph.graph_manager import Graph
from models.drone import Drone


class Scheduler:
    """Schedule each move
    based on the plan made by space-time
    dijkstra"""

    def __init__(self, graph: Graph):
        self.graph = graph

    def get_moves_for_turn(self, active_drones: list[Drone]) -> list[dict[str, object]]:
        """Lê a fita de movimentos e retorna apenas quem se moveu de verdade."""
        moves: list[dict[str, object]] = []

        for drone in sorted(active_drones, key=lambda item: item.id):
            if drone.current_index + 1 < len(drone.path):
                curr_loc = drone.path[drone.current_index]
                next_loc = drone.path[drone.current_index + 1]

                if curr_loc != next_loc:
                    node = self.graph.nodes.get(next_loc)
                    color = node.color if node else "white"

                    moves.append({
                        "drone": drone,
                        "target": next_loc,
                        "color": color
                    })

        return moves
