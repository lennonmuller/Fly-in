from __future__ import annotations

from algorithms.pathfinder import PathFinder
from graph.graph_manager import Graph
from graph.reservation import ReservationTable
from models.drone import Drone
from parser.parser import Parser
from renderer.display import Renderer
from scheduler.scheduler import Scheduler
from simulation.engine import Simulator


class AppController:
    """Máquina de Estados Finita (FSM) que orquestra a aplicação."""

    def __init__(self, initial_map: str | None) -> None:
        # FSM States: "MENU", "SIMULATION", "QUIT"
        self.state = "SIMULATION" if initial_map else "MENU"
        self.map_file = initial_map
        
        # O Renderer é persistente. Sobrevive às transições de estado.
        self.renderer = Renderer()

    def run(self) -> None:
        """O Loop Principal da Aplicação."""
        try:
            while self.state != "QUIT" and self.renderer._running:
                if self.state == "MENU":
                    self._run_menu()
                elif self.state == "SIMULATION":
                    self._run_simulation()
        finally:
            self.renderer.close()

    def _run_menu(self) -> None:
        """Mantém a tela viva rodando o estado de Menu."""
        print("Menu Inicial Aberto.")
        
        while self.state == "MENU" and self.renderer._running:
            self.renderer.render_menu()

    def _run_simulation(self) -> None:
        """Lógica do Estado de Simulação (Seu main.py antigo refatorado)."""
        if not self.map_file:
            self.state = "MENU"
            return

        print(f"Loading map: {self.map_file}")
        parser = Parser(self.map_file)
        data = parser.parse()

        graph = Graph()
        graph.build(data)

        if graph.start_hub is None or graph.end_hub is None:
            raise ValueError("O mapa deve definir start e end hub.")

        reservation = ReservationTable()
        pathfinder = PathFinder(graph, reservation)
        
        drones: list[Drone] = []
        for drone_id in range(1, int(data["nb_drones"]) + 1):
            path = pathfinder.get_path(graph.start_hub, graph.end_hub)
            if not path:
                raise ValueError("Nenhum caminho encontrado (deadlock de tráfego).")
            drones.append(Drone(id=drone_id, path=path))

        scheduler = Scheduler(graph)
        
        # Engine agora recebe tudo para rodar até acabar ou pedir pra sair
        engine = Simulator(drones, scheduler, self.renderer, graph)
        engine.run()

        # Quando a simulação acabar (por exemplo, clicou no botão "Voltar ao Menu"):
        # Se a janela não foi fechada no "X", voltamos pro Menu.
        if self.renderer._running:
            self.state = "MENU"
            self.map_file = None # Reseta o mapa para forçar a escolha no menu
        else:
            self.state = "QUIT"