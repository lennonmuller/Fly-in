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
        self.all_drones = drones
        self.active_drones = list(drones)
        self.scheduler = scheduler
        self.graph = graph
        self.renderer = renderer
        self.turn_count = 0

    def run(self) -> None:
        """Executa a simulação até todos os drones serem entregues."""

        # 1. Renderiza o mapa com os drones na saída antes de fazer qualquer coisa
        self.renderer.render_state(self.graph, self.all_drones, [])

        while self.active_drones:
            # 2. TRAVA a execução aqui esperando o ESPAÇO ou SETA DIREITA
            self.renderer.wait_for_step()
            if not self.renderer._running:  # Se fechar a janela enquanto pausado, sai limpo
                break

            moves = self.scheduler.get_moves_for_turn(self.active_drones)
            self._process_terminal_output(moves)

            for drone in self.active_drones:
                if drone.current_index + 1 < len(drone.path):
                    drone.current_index += 1

            self.active_drones = [
                drone for drone in self.active_drones
                if drone.current_location != self.graph.end_hub
            ]

            self.turn_count += 1

            # 3. Desenha o novo estado e volta para o início do while
            self.renderer.render_state(self.graph, self.all_drones, moves)

        self.renderer.wait_for_exit(self.graph, self.all_drones)

    def _process_terminal_output(self, moves: list[dict[str, object]]) -> None:
        """Apply the authorized moves for the current turn."""
        output_moves: list[str] = []
        for move in moves:
            drone = move.get("drone")
            target = move.get("target")
            if not isinstance(drone, Drone) or not isinstance(target, str):
                continue

            output_moves.append(f"{drone.name}-{target}")

        if output_moves:
            self.renderer.render_line(" ".join(output_moves))
