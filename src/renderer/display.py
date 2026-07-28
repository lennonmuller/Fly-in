from __future__ import annotations

import sys
from typing import Any, ClassVar

from models.drone import Drone

try:
    import pygame
except ImportError:  # pragma: no cover - depends on runtime environment
    pygame = None  # type: ignore


class Renderer:
    """Graphical renderer for the Fly-in simulation using pygame."""

    COLORS: ClassVar[dict[str, str]] = {
        "red": "\033[91m",
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }

    def __init__(
        self,
        width: int = 1200,  # Aumentei um pouco para caber o HUD lateral confortavelmente
        height: int = 800,
        fps: int = 30,      # Aumentamos o FPS interno para animações fluidas no futuro
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        
        # --- SISTEMA DE CÂMERA ---
        self.zoom = 1.0
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.world_scale = 100 # Distância base em pixels entre um nó e outro
        self.is_camera_initialized = False
        
        self.radius = 25
        self._pygame_available = pygame is not None
        self._screen: Any | None = None
        self._clock: Any | None = None
        self._font: Any | None = None
        self._font_small: Any | None = None
        self._font_title: Any | None = None
        
        self._running = True
        self.auto_play = False
        self.step_requested = False
        self.step_back_requested = False

        if self._pygame_available:
            pygame.init()
            self._screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Fly-in: Advanced Telemetry")
            self._clock = pygame.time.Clock()
            self._font_title = pygame.font.SysFont("segoeui", 32, bold=True)
            self._font = pygame.font.SysFont("segoeui", 24)
            self._font_small = pygame.font.SysFont("segoeui", 14)

    def _world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        """Projeta coordenadas do Mundo 2D para a Tela (Camera System)."""
        # Centraliza baseado na posição da câmera e aplica o zoom
        sx = (wx - self.camera_x) * self.zoom + (self.width / 2)
        sy = (wy - self.camera_y) * self.zoom + (self.height / 2)
        return int(sx), int(sy)

    def _init_camera(self, graph: Any) -> None:
        """Centraliza a câmera no meio do mapa no primeiro frame."""
        if self.is_camera_initialized or not graph.nodes:
            return
        
        xs = [node.x for node in graph.nodes.values()]
        ys = [node.y for node in graph.nodes.values()]
        
        # O centro do mundo é a média dos X e Y multiplicados pela escala
        center_x = ((max(xs) + min(xs)) / 2) * self.world_scale
        center_y = ((max(ys) + min(ys)) / 2) * self.world_scale
        
        self.camera_x = center_x
        self.camera_y = center_y
        self.is_camera_initialized = True

    def render_turn(self, movements: list[dict[str, object]]) -> None:
        """Print a line representing a turn of the simulation."""
        formatted_moves: list[str] = []

        for move in movements:
            drone = move.get("drone")
            target = move.get("target")
            color_key = str(move.get("color", "white")).lower()
            if not isinstance(drone, Drone) or not isinstance(target, str):
                continue

            move_str = f"{drone.name}-{target}"
            color_code = self.COLORS.get(color_key, self.COLORS["white"])
            colored_move = f"{color_code}{move_str}{self.COLORS['reset']}"
            formatted_moves.append(colored_move)

        if formatted_moves:
            print(" ".join(formatted_moves))

    def message(self, text: str, color: str = "white") -> None:
        """Print informative or error messages with color."""
        color_code = self.COLORS.get(color.lower(), self.COLORS["white"])
        print(f"{color_code}{text}{self.COLORS['reset']}")

    def render_state(
        self,
        graph: Any,
        drones: list[Drone],
        moves: list[dict[str, object]] | None = None,
        current_turn: int = 0, # <-- BUG 1 RESOLVIDO: Motor envia o turno real
    ) -> None:
        """Renderiza a simulação separando World e HUD."""
        if not self._pygame_available or self._screen is None:
            return

        self.handle_events()
        if not self._running:
            return

        self._init_camera(graph)

        self._screen.fill((15, 20, 25)) # Fundo Dark
        
        # 1. WORLD LAYER (Sujeito à câmera)
        self.draw_connections(graph)
        self.draw_hubs(graph)
        self.draw_drones(graph, drones)
        
        # 2. HUD / UI LAYER (Absoluto na tela)
        self.draw_hud(current_turn, moves)
        
        pygame.display.flip()
        if self._clock is not None:
            self._clock.tick(self.fps)

    def handle_events(self) -> None:
        """Process keyboard, mouse, and quit events."""
        if not self._pygame_available:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self._running = False
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_SPACE:
                    self.auto_play = not self.auto_play  # Liga/Desliga o play automático
                if event.key == pygame.K_RIGHT:
                    self.step_requested = True
                if event.key == pygame.K_LEFT:
                    self.step_back_requested = True
                    self.auto_play = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.zoom *= 1.1
                elif event.button == 5:
                    self.zoom /= 1.1

    def wait_for_step_and_get_delta(self, graph: Any, drones: list[Drone], current_turn: int) -> int:
        """Trava a execução, renderiza e retorna +1 (avança) ou -1 (volta)."""
        if not self._pygame_available:
            return 1 # Fallback para terminal puro
            
        while self._running:
            # Mantém a tela viva e a câmera funcional
            self.render_state(graph, drones, [], current_turn)
            
            if self.auto_play:
                return 1
            if self.step_requested:
                self.step_requested = False
                return 1
            if self.step_back_requested:
                self.step_back_requested = False
                return -1
        return 0

    def draw_connections(self, graph: Any) -> None:
        """Draw the edges between hubs using the camera projection."""
        if self._screen is None:
            return

        for node_name, neighbors in graph.adj.items():
            node_u = graph.nodes[node_name]
            # Converte a coordenada real para o tamanho do Mundo
            wx_u = node_u.x * self.world_scale
            wy_u = node_u.y * self.world_scale
            # Projeta na tela baseada na câmera
            sx_u, sy_u = self._world_to_screen(wx_u, wy_u)

            for neighbor in neighbors:
                # Desenha cada aresta apenas uma vez (evita redesenhar ida e volta)
                if node_name >= neighbor.destination:
                    continue
                    
                node_v = graph.nodes[neighbor.destination]
                wx_v = node_v.x * self.world_scale
                wy_v = node_v.y * self.world_scale
                sx_v, sy_v = self._world_to_screen(wx_v, wy_v)

                # A espessura da linha escala com o zoom (mínimo de 1 pixel)
                line_width = max(1, int(3 * self.zoom))
                pygame.draw.line(self._screen, (90, 110, 150), (sx_u, sy_u), (sx_v, sy_v), line_width)

    def _draw_node_shape(
        self, 
        color: tuple[int, int, int], 
        sx: int, 
        sy: int, 
        rad: int, 
        node_type: str
    ) -> None:
        """Desenha a forma geométrica correspondente ao tipo de zona."""
        border_color = (220, 220, 220)
        border_width = max(1, int(3 * self.zoom))

        if node_type == "restricted":
            # Quadrado
            rect = pygame.Rect(sx - rad, sy - rad, rad * 2, rad * 2)
            pygame.draw.rect(self._screen, color, rect)
            pygame.draw.rect(self._screen, border_color, rect, border_width)
            
        elif node_type == "priority":
            # Losango / Diamante
            points = [
                (sx, sy - rad - 5), # Topo mais esticado
                (sx + rad + 5, sy), # Direita
                (sx, sy + rad + 5), # Baixo
                (sx - rad - 5, sy)  # Esquerda
            ]
            pygame.draw.polygon(self._screen, color, points)
            pygame.draw.polygon(self._screen, border_color, points, border_width)
            
        else:
            # Círculo (Normal, Start, End)
            pygame.draw.circle(self._screen, color, (sx, sy), rad)
            pygame.draw.circle(self._screen, border_color, (sx, sy), rad, border_width)
            
            # Start e End ganham uma aura pulsante / anel extra
            if node_type in ("start_hub", "end_hub"):
                extra_rad = rad + int(6 * self.zoom)
                pygame.draw.circle(self._screen, (255, 255, 255), (sx, sy), extra_rad, width=2)

    def draw_hubs(self, graph: Any) -> None:
        """Draw the map hubs and their labels matching real coordinates."""
        font = self._font
        if self._screen is None or font is None:
            return

        for node in graph.nodes.values():
            color = self._color_for_node(node)
            wx = node.x * self.world_scale
            wy = node.y * self.world_scale
            sx, sy = self._world_to_screen(wx, wy)
            
            rad = int(self.radius * self.zoom)
            
            # Só desenha se tiver um tamanho visível para não causar erro no Pygame
            if rad > 0:
                self._draw_node_shape(color, sx, sy, rad, node.type)

            # O Texto com fundo preto translúcido para leitura perfeita
            label = font.render(node.name, True, (255, 255, 255))
            
            # Posição do texto sempre abaixo do nó, independente do zoom
            text_x = sx - (label.get_width() // 2)
            text_y = sy + rad + 5
            
            # Desenha uma sombrinha preta atrás do texto para não misturar com as linhas
            bg_rect = pygame.Rect(text_x - 2, text_y - 2, label.get_width() + 4, label.get_height() + 4)
            pygame.draw.rect(self._screen, (20, 20, 20, 180), bg_rect, border_radius=3)
            self._screen.blit(label, (text_x, text_y))

    def draw_drones(self, graph: Any, drones: list[Drone]) -> None:
        """Draw the drones, handling offsets and restricted zones."""
        font = self._font_small
        if self._screen is None or font is None:
            return

        occupancy_count: dict[str, int] = {}

        for drone in drones:
            try:
                hub_name = drone.current_location
            except ValueError:
                continue

            # Identifica a coordenada Mundo (wx, wy) do Drone
            if "-" in hub_name:
                # Se for zona restrita, o drone está exatamente no meio da aresta
                u_name, v_name = hub_name.split("-")
                node_u = graph.nodes.get(u_name)
                node_v = graph.nodes.get(v_name)
                if node_u and node_v:
                    wx = ((node_u.x + node_v.x) / 2) * self.world_scale
                    wy = ((node_u.y + node_v.y) / 2) * self.world_scale
                else:
                    continue
            else:
                # Drone está num hub normal
                node = graph.nodes.get(hub_name)
                if node:
                    wx = node.x * self.world_scale
                    wy = node.y * self.world_scale
                else:
                    continue

            # Lógica de Grid para múltiplos drones no mesmo local não se sobreporem
            count = occupancy_count.get(hub_name, 0)
            occupancy_count[hub_name] = count + 1
            
            # O grid (espalhamento) dos drones também acompanha o zoom
            offset_step = 16 * self.zoom
            offset_x_drone = (count % 3) * offset_step - offset_step
            offset_y_drone = (count // 3) * offset_step - offset_step

            # Projeta para a Tela
            sx, sy = self._world_to_screen(wx, wy)
            
            # Aplica o espaçamento do grid no espaço da tela
            sx_draw = int(sx + offset_x_drone)
            sy_draw = int(sy + offset_y_drone)

            drone_rad = max(2, int(8 * self.zoom))
            pygame.draw.circle(self._screen, (255, 255, 255), (sx_draw, sy_draw), drone_rad)
            
            # Tag com nome do drone
            label = font.render(drone.name, True, (0, 0, 0), (255, 255, 255))
            self._screen.blit(label, (sx_draw + drone_rad + 2, sy_draw - drone_rad - 2))

    def wait_for_exit(self, graph: Any, drones: list[Drone], current_turn: int = 0) -> None:
        """Segura a tela aberta após o fim da simulação."""
        if not self._pygame_available:
            return
        
        # Mostra o status verde no final
        self.message("\nSimulation Complete! Close the window to exit.", "green")
        while self._running:
            # Continua passando o último turno para o HUD não bugar no fim
            self.render_state(graph, drones, [], current_turn)

    def draw_hud(self, current_turn: int, moves: list[dict[str, object]] | None) -> None:
        """Desenha a interface fixada no lado direito, imune ao zoom."""
        font_title = self._font_title
        font = self._font
        font_small = self._font_small
        if self._screen is None or font is None or font_small is None or font_title is None:
            return

        # Fundo semi-transparente para o painel lateral
        panel_rect = pygame.Surface((250, self.height), pygame.SRCALPHA)
        panel_rect.fill((10, 10, 15, 200))
        self._screen.blit(panel_rect, (self.width - 250, 0))

        # Textos fixos (HUD)
        turn_text = font_title.render(f"TURN {current_turn}", True, (255, 255, 255))
        self._screen.blit(turn_text, (self.width - 230, 30))

        play_state = "PLAYING" if self.auto_play else "PAUSED"
        color_state = (100, 255, 100) if self.auto_play else (255, 100, 100)
        status_text = font.render(f"Status: {play_state}", True, color_state)
        self._screen.blit(status_text, (self.width - 230, 80))

        info_lines = [
            "CONTROLS:",
            "[Q] Quit",
            "[SPACE] Auto-play",
            "[RIGHT] Step Forward",
            "[LEFT] Step Backward",
            "[WHEEL] Zoom Camera",
        ]
        for idx, line in enumerate(info_lines):
            label = font_small.render(line, True, (180, 180, 180))
            self._screen.blit(label, (self.width - 230, 150 + idx * 25))

    def render_line(self, line: str) -> None:
        """Print a ready-to-display simulation line."""
        if not line.strip():
            return
        print(line)

    def close(self) -> None:
        """Close the pygame window if it is open."""
        if self._pygame_available and pygame is not None:
            pygame.quit()

    def _color_for_node(self, node: Any) -> tuple[int, int, int]:
        """Defines the node color based on the [color=...] tag or its type."""
        color_map = {
            "red": (255, 70, 70),
            "green": (70, 220, 70),
            "blue": (70, 130, 255),
            "yellow": (255, 220, 50),
            "orange": (255, 150, 0),
            "purple": (150, 70, 200),
            "cyan": (70, 220, 255),
            "magenta": (255, 50, 255),
            "black": (60, 60, 60),
            "brown": (140, 70, 20),
            "maroon": (128, 0, 0),
            "gold": (255, 215, 0),
            "darkred": (140, 0, 0),
            "violet": (238, 130, 238),
            "crimson": (220, 20, 60),
            "lime": (50, 255, 50),
            "gray": (150, 150, 150)
        }
        if hasattr(node, "color") and node.color:
            color_name = str(node.color).lower()
            if color_name in color_map:
                return color_map[color_name]
            if color_name == "rainbow":
                return (255, 255, 255)

        if node.type == "start_hub":
            return (80, 220, 255)
        if node.type == "end_hub":
            return (255, 90, 90)
        if node.type == "restricted":
            return (255, 190, 90)
        return (100, 220, 120)

    def _compute_positions(self, graph: Any) -> dict[str, tuple[int, int]]:
        if not graph.nodes:
            return {}

        coords = list(graph.nodes.values())
        xs = [node.x for node in coords]
        ys = [node.y for node in coords]
        x_min = min(xs)
        x_max = max(xs)
        y_min = min(ys)
        y_max = max(ys)
        x_span = max(x_max - x_min, 1)
        y_span = max(y_max - y_min, 1)

        positions: dict[str, tuple[int, int]] = {}
        for node in coords:
            x_ratio = (node.x - x_min) / x_span
            y_ratio = (node.y - y_min) / y_span
            x_pos = int(60 + x_ratio * (self.width - 120))
            y_pos = int(60 + (1 - y_ratio) * (self.height - 120))
            positions[node.name] = (x_pos, y_pos)

        return positions

    @property
    def running(self) -> bool:
        return self._running
