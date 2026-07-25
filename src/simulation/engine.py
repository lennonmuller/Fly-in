from __future__ import annotations

from graph.graph_manager import Graph
from models.drone import Drone
from renderer.display import Renderer
from scheduler.scheduler import Scheduler


class Simulator:
    """Central coordinator of the turn-by-turn simulation."""

    def __init__(
        self,
        drones: list[Drone],
        scheduler: Scheduler,
        graph: Graph,
        renderer: Renderer,
    ) -> None:
        self.active_drones = drones
        self.scheduler = scheduler
        self.graph = graph
        self.renderer = renderer
        self.turn_count = 0

    def step(self) -> bool:
        """
        Execute one simulation turn.

        Returns:
            True  -> simulation still running
            False -> simulation finished
        """
        if not self.active_drones:
            return False

        moves = self.scheduler.assign_moves(self.active_drones)

        if not moves:
            return False

        self._process_turn(moves)

        self.active_drones = [
            drone for drone in self.active_drones
            if drone.current_index + 1 < len(drone.path)
        ]

        self.turn_count += 1

        return bool(self.active_drones)

    def _process_turn(self, moves: list[dict[str, object]]) -> None:
        """Apply the authorized moves for the current turn."""
        output_moves: list[str] = []
        for move in moves:
            drone = move.get("drone")
            target = move.get("target")
            if not isinstance(drone, Drone) or not isinstance(target, str):
                continue

            drone.current_index += 1
            output_moves.append(f"{drone.name}-{target}")

        if output_moves:
            self.renderer.render_line(" ".join(output_moves))
