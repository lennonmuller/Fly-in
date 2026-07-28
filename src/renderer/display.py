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
        width: int = 1000,
        height: int = 700,
        fps: int = 8,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.mid_x = width / 2
        self.mid_y = height / 2
        self.zoom = 1.0
        self.scale = 150
        self.radius = 60
        self._pygame_available = pygame is not None
        self._screen: Any | None = None
        self._clock: Any | None = None
        self._font: Any | None = None
        self._font_small: Any | None = None
        self._running = True
        self._turn = 0
        self.auto_play = False
        self.step_requested = False

        if self._pygame_available:
            pygame.init()
            self._screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Fly-in Simulation")
            self._clock = pygame.time.Clock()
            self._font = pygame.font.SysFont("arial", 24)
            self._font_small = pygame.font.SysFont("arial", 18)

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
    ) -> None:
        """Render the current simulation state to a pygame window."""
        if not self._pygame_available or self._screen is None:
            return

        self.handle_events()
        if not self._running:
            return

        self._screen.fill((15, 15, 25))
        self.draw_connections(graph)
        self.draw_hubs(graph)
        self.draw_drones(graph, drones)
        self.draw_info(moves)
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.zoom *= 1.1
                elif event.button == 5:
                    self.zoom /= 1.1

    def wait_for_step(self) -> None:
        if not self._pygame_available:
            return

        while self._running:
            self.handle_events()

            if self.auto_play or self.step_requested:
                self.step_requested = False
                break

            if self._clock:
                self._clock.tick(30)

    def draw_connections(self, graph: Any) -> None:
        """Draw the edges between hubs."""
        if self._screen is None:
            return

        positions = self._compute_positions(graph)

        for node_name, neighbors in graph.adj.items():
            for neighbor in neighbors:
                if node_name >= neighbor.destination:
                    continue
                start = positions[node_name]
                end = positions[neighbor.destination]
                x1 = start[0] * self.zoom
                y1 = start[1] * self.zoom
                x2 = end[0] * self.zoom
                y2 = end[1] * self.zoom
                pygame.draw.line(
                    self._screen,
                    (90, 110, 150),
                    (x1, y1),
                    (x2, y2),
                    3,
                )

    def draw_hubs(self, graph: Any) -> None:
        """Draw the map hubs and their labels."""
        font = self._font
        if self._screen is None or font is None:
            return

        positions = self._compute_positions(graph)
        for node_name, (x_pos, y_pos) in positions.items():
            node = graph.nodes[node_name]
            color = self._color_for_node(node)
            x_draw = int(x_pos * self.zoom)
            y_draw = int(y_pos * self.zoom)
            radius = int(self.radius * self.zoom)

            pygame.draw.circle(self._screen, color, (x_draw, y_draw), radius)
            pygame.draw.circle(
                self._screen,
                (220, 220, 220),
                (x_draw, y_draw),
                radius,
                width=3,
            )

            label = font.render(node_name, True, (255, 255, 255))
            self._screen.blit(
                label,
                (x_draw + radius + 5, y_draw - radius // 2),
            )

    def draw_drones(self, graph: Any, drones: list[Drone]) -> None:
        """Draw the drones positioned on the map with visual offsets."""
        font = self._font_small
        if self._screen is None or font is None:
            return

        positions = self._compute_positions(graph)
        occupancy_count: dict[str, int] = {}

        for drone in drones:
            try:
                hub_name = drone.current_location
            except ValueError:
                continue

            # Lógica para mostrar o drone no meio da aresta (zona restrita)
            if "-" in hub_name:
                u, v = hub_name.split("-")
                pos_u = positions.get(u)
                pos_v = positions.get(v)
                if pos_u and pos_v:
                    base_x = (pos_u[0] + pos_v[0]) / 2
                    base_y = (pos_u[1] + pos_v[1]) / 2
                    base_pos = (base_x, base_y)
                else:
                    continue
            else:
                base_pos = positions.get(hub_name)  # type: ignore

            if not base_pos:
                continue

            # Calcula offset para quando há múltiplos drones no mesmo lugar
            count = occupancy_count.get(hub_name, 0)
            occupancy_count[hub_name] = count + 1

            # Espalha os drones num formato de grid ao redor do centro do nó
            offset_x_drone = (count % 3) * 16 - 16
            offset_y_drone = (count // 3) * 16 - 16

            x_draw = int(base_pos[0] * self.zoom + offset_x_drone)
            y_draw = int(base_pos[1] * self.zoom + offset_y_drone)

            pygame.draw.circle(self._screen, (255, 255, 255), (x_draw, y_draw), 8)
            label = font.render(drone.name, True, (0, 0, 0), (255, 255, 255))
            self._screen.blit(label, (x_draw + 10, y_draw - 10))

    def wait_for_exit(self, graph: Any, drones: list[Drone]) -> None:
        """Segura a tela aberta após o fim da simulação renderizando o estado final."""
        if not self._pygame_available:
            return

        self.message("\nSimulation Complete! Close the window to exit.", "green")
        while self._running:
            # Chama o render_state no loop infinito para o SO não "apagar" a janela
            self.render_state(graph, drones, [])

    def draw_info(self, moves: list[dict[str, object]] | None) -> None:
        """Draw the simulation information panel."""
        font = self._font_small
        if self._screen is None or font is None:
            return

        turn_text = font.render(
            f"Turn {self._turn}",
            True,
            (255, 255, 255),
        )
        self._screen.blit(turn_text, (self.width - 220, 20))

        play_state = "PLAYING" if self.auto_play else "PAUSED"
        color_state = (100, 255, 100) if self.auto_play else (255, 100, 100)
        status_text = font.render(f"Status: {play_state}", True, color_state)
        self._screen.blit(status_text, (self.width - 220, 50))

        info_lines = [
            "Quit (q)",
            "Zoom (mouse wheel)",
            "Advance (right arrow)",
            "Auto step (space)",
        ]
        for idx, line in enumerate(info_lines):
            label = font.render(line, True, (220, 220, 220))
            self._screen.blit(label, (self.width - 220, 70 + idx * 24))

        if moves:
            summary = font.render(
                f"Moves: {len(moves)}",
                True,
                (180, 230, 120),
            )
            self._screen.blit(summary, (self.width - 220, 170))

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
