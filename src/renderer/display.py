from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, ClassVar

from models.drone import Drone
from renderer.theme_manager import ThemeManager

try:
    import pygame  # type: ignore
except ImportError:
    pygame = None


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
        self.world_scale = 100  # Distância base em pixels entre um nó e outro
        self.is_camera_initialized = False

        self.radius = 25
        self._pygame_available = pygame is not None
        self._screen: Any | None = None
        self._clock: Any | None = None
        self._font: Any | None = None
        self._font_small: Any | None = None
        self._font_title: Any | None = None
        self.theme_manager = ThemeManager()

        assets = Path(__file__).resolve().parent.parent.parent / "assets"

        self._running = True
        self.auto_play = False
        self.step_requested = False
        self.step_back_requested = False

        if self._pygame_available:
            pygame.init()
            self._screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Fly-in")
            self._clock = pygame.time.Clock()
            self._font_title = pygame.font.SysFont("segoeui", 32, bold=True)
            self._font = pygame.font.SysFont("segoeui", 24)
            self._font_small = pygame.font.SysFont("segoeui", 14)

        self.bg_img: Any | None = None
        self.drone_img: Any | None = None
        self.base_drone_size = 45

        self.bg_img = self._load_image(
            str(assets / "background.jpg"),
            alpha=False,
        )
        if self.bg_img:
            self.bg_img = pygame.transform.scale(
                self.bg_img,
                (self.width, self.height),
            )

        self.drone_img = self._load_image(
            str(assets / "drone.png"),
            )

    def _load_image(self, path: str, alpha: bool = True):
        try:
            image = pygame.image.load(path)

            if alpha:
                image = image.convert_alpha()
            else:
                image = image.convert()
            return image

        except Exception as e:
            print(f"[ERROR] Failed to load {path}")
            print(e)
            return None

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
        current_turn: int = 0,
        anim_progress: float = 0.0,
        anim_delta: int = 0
    ) -> None:
        """Renderiza a simulação separando World e HUD."""
        if not self._pygame_available or self._screen is None:
            return

        self.handle_events()
        if not self._running:
            return

        self._init_camera(graph)

        self.bg_img, self.drone_img = self.theme_manager.get_assets(self.width, self.height)

        if self.bg_img:
            self._screen.blit(self.bg_img, (0, 0))
        else:
            self._screen.fill((15, 20, 25))

        self.draw_connections(graph)
        self.draw_hubs(graph)
        self.draw_drones(graph, drones, current_turn, anim_progress, anim_delta)

        self.draw_hud(current_turn, moves)

        pygame.display.flip()
        if self._clock is not None:
            self._clock.tick(self.fps)

    def render_menu(
        self, title: str, options: list[str], cursor_idx: int, footer: str
    ) -> None:
        """Desenha a tela do Menu com a opção selecionada em destaque."""
        if not self._pygame_available or self._screen is None:
            return

        self._screen.fill((20, 25, 35)) # Fundo limpo dark
        
        if self._font_title and self._font and self._font_small:
            # 1. Título
            title_surf = self._font_title.render(title, True, (70, 220, 255))
            self._screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 100))
            
            # 2. Opções Dinâmicas (Navegação por Teclado)
            start_y = 250
            spacing = 40
            
            for i, option_text in enumerate(options):
                if i == cursor_idx:
                    # Opção Selecionada: Amarelo, Maior, com um ">" na frente
                    text = f">  {option_text}  <"
                    color = (255, 220, 50)
                else:
                    # Opção Inativa: Cinza Claro
                    text = option_text
                    color = (180, 180, 180)
                    
                opt_surf = self._font.render(text, True, color)
                self._screen.blit(opt_surf, (self.width // 2 - opt_surf.get_width() // 2, start_y + i * spacing))
            
            # 3. Rodapé (Instruções)
            footer_surf = self._font_small.render(footer, True, (100, 100, 100))
            self._screen.blit(footer_surf, (self.width // 2 - footer_surf.get_width() // 2, self.height - 50))

        pygame.display.flip()
        if self._clock:
            self._clock.tick(self.fps)

    def get_menu_action(self) -> str | None:
        """Captura apenas as teclas de navegação do menu (Sem mouse)."""
        if not self._pygame_available:
            return None
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    return "UP"
                if event.key == pygame.K_DOWN:
                    return "DOWN"
                if event.key == pygame.K_RETURN:
                    return "ENTER"
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return "QUIT"
        return None

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
        """Trava a execução esperando input, e dispara a animação quando avança/volta."""
        if not self._pygame_available:
            return 1  # Fallback pro terminal puro

        target_delta = 0

        while self._running:
            self.handle_events()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_m]:
                return -99

            # Checa se precisamos avançar o tempo
            if self.auto_play:
                target_delta = 1
            elif self.step_requested:
                self.step_requested = False
                target_delta = 1
            elif self.step_back_requested:
                self.step_back_requested = False
                target_delta = -1

            if target_delta != 0:
                # O TEMPO VAI MUDAR! GERA A ANIMAÇÃO!
                progress = 0.0
                anim_speed = 0.15  # Quanto maior, mais rápida a animação (ex: 0.15 = ~7 frames)

                while progress < 1.0 and self._running:
                    self.handle_events()  # Mantém zoom e janela responsivos
                    self.render_state(
                        graph, drones, [], current_turn,
                        anim_progress=progress, anim_delta=target_delta
                    )
                    progress += anim_speed

                return target_delta  # Acabou a animação, libera o Motor!

            self.render_state(graph, drones, [], current_turn)

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
                (sx, sy - rad - 5),  # Topo mais esticado
                (sx + rad + 5, sy),  # Direita
                (sx, sy + rad + 5),  # Baixo
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
        """Desenha os hubs com texto de tamanho fixo e inteligência de visibilidade."""
        # Usamos uma fonte fixa (não escala com o zoom)
        font = self._font_small 
        if self._screen is None or font is None:
            return

        for node in graph.nodes.values():
            # 1. Matemática de Projeção
            wx, wy = node.x * self.world_scale, node.y * self.world_scale
            sx, sy = self._world_to_screen(wx, wy)
            
            # O raio do nó escala com o zoom, mas o texto NÃO.
            rad = int(self.radius * self.zoom)
            
            # 2. Desenha a Forma (Shape) do Nó
            if rad > 0:
                color = self._color_for_node(node)
                self._draw_node_shape(color, sx, sy, rad, node.type)

            # 3. Lógica de "Anti-Poluição" (LOD)
            # Só desenha o nome se o zoom for suficiente para não embolar a tela
            if self.zoom > 0.4:
                # O texto mantém sempre o mesmo tamanho em pixels
                display_name = node.name
                # Abrevia apenas nomes extremos para manter a estética
                if len(display_name) > 12:
                    display_name = display_name[:10] + ".."
                    
                label = font.render(display_name, True, (255, 255, 255))
                
                # Centraliza o texto no ponto exato SX, SY (que se move com a câmera)
                text_rect = label.get_rect(center=(sx, sy))
                
                # Só desenha o texto se ele couber (ou quase couber) dentro do nó
                # Isso evita que o texto fique flutuando sobre um "pontinho" minúsculo
                if rad > label.get_width() / 2.5:
                    # Sombra sutil para leitura em qualquer fundo
                    shadow = font.render(display_name, True, (20, 20, 20))
                    self._screen.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
                    self._screen.blit(label, text_rect)

    def draw_drones(
        self, graph: Any, drones: list[Drone],
        current_turn: int, anim_progress: float, anim_delta: int
    ) -> None:
        """Draws drones using LERP for fluid motion animation and grid collision."""
        font = self._font_small
        if self._screen is None or font is None:
            return

        start_counts: dict[str, int] = {}
        end_counts: dict[str, int] = {}

        for drone in drones:
            # Trava com segurança o índice para não dar IndexError no passado ou futuro
            idx_start = max(0, min(current_turn, len(drone.path) - 1))
            idx_end = max(0, min(current_turn + anim_delta, len(drone.path) - 1))

            loc_start = drone.path[idx_start]
            loc_end = drone.path[idx_end]

            c_start = self._get_world_coords(loc_start, graph)
            c_end = self._get_world_coords(loc_end, graph)
            if not c_start or not c_end:
                continue

            # Calcula a grade de espaçamento na Origem e no Destino
            count_start = start_counts.get(loc_start, 0)
            start_counts[loc_start] = count_start + 1

            count_end = end_counts.get(loc_end, 0)
            end_counts[loc_end] = count_end + 1

            offset_step = 16 * self.zoom
            ox_start = (count_start % 3) * offset_step - offset_step
            oy_start = (count_start // 3) * offset_step - offset_step

            ox_end = (count_end % 3) * offset_step - offset_step
            oy_end = (count_end // 3) * offset_step - offset_step

            # Projeta na Tela
            sx_start, sy_start = self._world_to_screen(c_start[0], c_start[1])
            sx_end, sy_end = self._world_to_screen(c_end[0], c_end[1])

            # Aplica os offsets
            sx_start += ox_start
            sy_start += oy_start
            sx_end += ox_end
            sy_end += oy_end

            # A MÁGICA DO LERP AQUI!
            sx = sx_start + (sx_end - sx_start) * anim_progress
            sy = sy_start + (sy_end - sy_start) * anim_progress

            # SE TEMOS A IMAGEM DO DRONE:
            if self.drone_img:
                # Escala a imagem baseada no zoom atual da câmera
                scaled_size = max(8, int(self.base_drone_size * self.zoom))
                scaled_img = pygame.transform.scale(self.drone_img, (scaled_size, scaled_size))

                # Centraliza a imagem no ponto exato (sx, sy)
                img_rect = scaled_img.get_rect(center=(int(sx), int(sy)))
                self._screen.blit(scaled_img, img_rect)

                # Tag com nome do drone
                label = font.render(drone.name, True, (0, 0, 0), (255, 255, 255))
                self._screen.blit(label, (int(sx) + (scaled_size//2), int(sy) - (scaled_size//2) - 10))

            # SE NÃO TEMOS A IMAGEM (FALLBACK DE SEGURANÇA):
            else:
                drone_rad = max(2, int(8 * self.zoom))
                pygame.draw.circle(self._screen, (255, 255, 255), (int(sx), int(sy)), drone_rad)

                label = font.render(drone.name, True, (0, 0, 0), (255, 255, 255))
                self._screen.blit(label, (int(sx) + drone_rad + 2, int(sy) - drone_rad - 2))

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
            "[M] Back to Menu"
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
                if not self._pygame_available:
                    return (255, 255, 255)

                time_ms = pygame.time.get_ticks()
                # Cria ondas senoidais defasadas para R, G e B
                r = int((math.sin(time_ms * 0.003) + 1) * 127.5)
                g = int((math.sin(time_ms * 0.003 + 2.0) + 1) * 127.5)
                b = int((math.sin(time_ms * 0.003 + 4.0) + 1) * 127.5)
                return (r, g, b)

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

    def _get_world_coords(self, loc: str, graph: Any) -> tuple[float, float] | None:
        """Decodes a route string into real world coordinates."""
        if "-" in loc:
            u, v = loc.split("-")
            n_u, n_v = graph.nodes.get(u), graph.nodes.get(v)
            if n_u and n_v:
                return (
                    ((n_u.x + n_v.x) / 2) * self.world_scale,
                    ((n_u.y + n_v.y) / 2) * self.world_scale
                )
        else:
            node = graph.nodes.get(loc)
            if node:
                return (node.x * self.world_scale, node.y * self.world_scale)
        return None
