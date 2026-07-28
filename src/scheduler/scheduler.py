from __future__ import annotations

from graph.graph_manager import Graph
from models.drone import Drone


class Scheduler:
    """Schedule each move
    based on the plan made by space-time
    dijkstra"""

    def __init__(self, graph: Graph):
        self.graph = graph

    def get_moves_for_turn(self, drones: list[Drone], target_turn: int) -> list[dict[str, object]]:
        """Lê a fita de movimentos e retorna apenas quem se moveu no turno exato."""
        if target_turn == 0:
            return [] # No turno 0 ninguém se moveu, eles acabaram de nascer
            
        moves: list[dict[str, object]] = []

        for drone in sorted(drones, key=lambda item: item.id):
            # Se o turno alvo existir na fita de gravação deste drone
            if target_turn < len(drone.path):
                prev_loc = drone.path[target_turn - 1]
                curr_loc = drone.path[target_turn]

                # Se ele andou (não ficou parado fazendo Wait)
                if prev_loc != curr_loc:
                    node = self.graph.nodes.get(curr_loc)
                    color = node.color if node else "white"

                    moves.append({
                        "drone": drone,
                        "target": curr_loc,
                        "color": color
                    })

        return moves
