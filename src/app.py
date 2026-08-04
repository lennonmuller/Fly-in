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
        """Controla a navegação do Menu usando Máquina de Estados Interna."""
        menu_view = "MAIN"
        cursor = 0

        import pygame
        last_input_time = 0
        debounce_delay = 200
        
        # Listas hardcoded para garantir que funcionem perfeitamente na avaliação
        maps_list = [
            "maps/easy/01_linear_path.txt",
            "maps/easy/02_simple_fork.txt",
            "maps/easy/03_basic_capacity.txt",
            "maps/medium/01_dead_end_trap.txt",
            "maps/medium/02_circular_loop.txt",
            "maps/medium/03_priority_puzzle.txt",
            "maps/hard/01_maze_nightmare.txt",
            "maps/hard/02_capacity_hell.txt",
            "maps/hard/03_ultimate_challenge.txt",
            "maps/challenger/01_the_impossible_dream.txt"
        ]
        themes_list = ["Sky", "War", "TrainStation"]
        
        # Para evitar crash caso o mapa passado por terminal não exista
        if self.map_file not in maps_list and self.map_file is not None:
            maps_list.insert(0, self.map_file)

        while self.state == "MENU" and self.renderer._running:
            # 1. Define as opções de acordo com a tela atual
            if menu_view == "MAIN":
                title = "FLY-IN: MAIN MENU"
                map_name = self.map_file.split('/')[-1] if self.map_file else "None"
                current_theme = self.renderer.theme_manager.current_theme_name
                options = [
                    "START SIMULATION",
                    f"Select Map: [{map_name}]",
                    f"Select Theme: [{current_theme}]", 
                    "Quit"
                ]
            elif menu_view == "MAPS":
                title = "SELECT A MAP"
                options = [m.split('/')[-1] for m in maps_list] + ["Back to Main"]
            elif menu_view == "THEMES":
                title = "SELECT A THEME"
                options = themes_list + ["Back to Main"]

            # 2. Renderiza a tela
            footer = "Use [UP] / [DOWN] to navigate and [ENTER] to select."
            self.renderer.render_menu(title, options, cursor, footer)

            # 3. Lê o Input (Sem Mouse)
            action = self.renderer.get_menu_action()

            current_time = pygame.time.get_ticks()

            if action and (current_time - last_input_time > debounce_delay):
                last_input_time = current_time
            
            if action == "QUIT":
                self.state = "QUIT"
            elif action == "UP":
                cursor = (cursor - 1) % len(options)  # Faz o wrap-around (volta pro final)
            elif action == "DOWN":
                cursor = (cursor + 1) % len(options)  # Faz o wrap-around (volta pro inicio)
            elif action == "ENTER":
                # Lógica de clique baseada na tela atual
                if menu_view == "MAIN":
                    if cursor == 0:  # START
                        if self.map_file:
                            self.state = "SIMULATION"
                    elif cursor == 1:  # MAPS
                        menu_view = "MAPS"
                        cursor = 0
                    elif cursor == 2:  # THEMES
                        menu_view = "THEMES"
                        cursor = 0
                    elif cursor == 3:  # QUIT
                        self.state = "QUIT"

                elif menu_view == "MAPS":
                    if cursor == len(options) - 1:  # Back
                        menu_view = "MAIN"
                        cursor = 1
                    else:
                        self.map_file = maps_list[cursor]
                        menu_view = "MAIN"
                        cursor = 0 # Foca no START após escolher o mapa

                elif menu_view == "THEMES":
                    if cursor == len(options) - 1:  # Back
                        menu_view = "MAIN"
                        cursor = 2
                    else:
                        selected_theme = themes_list[cursor]
                        self.renderer.theme_manager.set_theme(selected_theme)
                        menu_view = "MAIN"
                        cursor = 0

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