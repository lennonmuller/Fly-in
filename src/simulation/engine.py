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
        """Executa a simulação atuando como um Navegador do Tempo."""
        # Descobre qual é o turno máximo onde o último drone chega ao destino
        max_turn = max((len(d.path) - 1 for d in self.all_drones), default=0)
        
        self.turn_count = 0
        max_reached_turn = 0  # Controle para não floodar o terminal ao fazer rewind

        # O loop agora é eterno, ditado pelo usuário ou auto_play
        while self.renderer._running:
            
            # Sincroniza a posição atual de TODOS os drones para o turno exato
            for drone in self.all_drones:
                # O índice é travado no fim da rota se o tempo passar do limite dele
                drone.current_index = min(self.turn_count, len(drone.path) - 1)

            # Extrai os movimentos deste turno para pintar no HUD (Opcional)
            moves = self.scheduler.get_moves_for_turn(self.all_drones, self.turn_count)
            
            # --- TERMINAL (PDF Strict Rule) ---
            # Se avançamos para um turno no futuro inédito, printamos no terminal
            if self.turn_count > max_reached_turn:
                self._process_terminal_output(moves)
                max_reached_turn = self.turn_count

            # Renderiza o estado exato
            self.renderer.render_state(
                self.graph, self.all_drones, moves, current_turn=self.turn_count
            )

            # Se chegamos ao fim do filme, desliga o auto-play (mas deixa a tela aberta)
            if self.turn_count >= max_turn and self.renderer.auto_play:
                self.renderer.auto_play = False

            # Trava o tempo e aguarda a decisão do usuário (+1, -1 ou 0)
            delta = self.renderer.wait_for_step_and_get_delta(
                self.graph, self.all_drones, self.turn_count
            )
            
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
