from __future__ import annotations

from graph.graph_manager import Graph
from models.drone import Drone
from renderer.display import Renderer
from scheduler.scheduler import Scheduler


class Simulator:
    """Coordenador central da simulação (Agora gerenciado pela FSM)."""

    def __init__(
        self,
        drones: list[Drone],
        scheduler: Scheduler,
        renderer: Renderer,  # Aqui recebemos a instância viva do Renderer
        graph: Graph,
    ) -> None:
        self.all_drones = drones
        self.scheduler = scheduler
        self.renderer = renderer
        self.graph = graph
        self.turn_count = 0

    def run(self) -> None:
        """Executa a simulação atuando como um Navegador do Tempo."""
        max_turn = max((len(d.path) - 1 for d in self.all_drones), default=0)
        self.turn_count = 0
        max_reached_turn = 0

        # O loop continua enquanto o Pygame estiver aberto (renderer._running)
        # e a flag de saída para o menu (a ser implementada) não for acionada.
        while self.renderer._running:

            for drone in self.all_drones:
                drone.current_index = min(self.turn_count, len(drone.path) - 1)

            moves = self.scheduler.get_moves_for_turn(self.all_drones, self.turn_count)

            if self.turn_count > max_reached_turn:
                self._process_terminal_output(moves)
                max_reached_turn = self.turn_count

            self.renderer.render_state(
                self.graph, self.all_drones, moves, current_turn=self.turn_count
            )

            if self.turn_count >= max_turn and self.renderer.auto_play:
                self.renderer.auto_play = False

            delta = self.renderer.wait_for_step_and_get_delta(
                self.graph, self.all_drones, self.turn_count
            )

            # --- SAÍDA PARA O MENU ---
            # Se o botão de voltar ao menu for apertado, o wait_for_step_and_get_delta
            # pode nos devolver um código especial (ex: -99) para quebrar o loop.
            if delta == -99:
                break
            # Aplica o paradoxo temporal!
            self.turn_count += delta

            # Proteções contraa antes de 0 e depois de max
            self.turn_count = max(self.turn_count, 0)
            self.turn_count = min(self.turn_count, max_turn)

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
