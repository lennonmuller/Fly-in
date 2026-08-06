from __future__ import annotations

from typing import Any

try:
    import pygame
except ImportError:
    pygame = None  # type: ignore


class ThemeManager:
    """Gerencia os assets visuais (Fundo e Sprites) garantindo fallbacks seguros."""

    def __init__(self) -> None:
        self.themes = {
            "Sky": {"bg": "assets/background.jpg", "sprite": "assets/drone.png"},
            "War": {"bg": "assets/destroyed-city.jpg", "sprite": "assets/supermissel.gif"},
            "TrainStation": {"bg": "assets/station2.jpg", "sprite": "assets/train.png"}
        }
        self.current_theme_name = "Sky"
        self._bg_cache: Any | None = None
        self._sprite_cache: Any | None = None

    def set_theme(self, theme_name: str) -> None:
        """Altera o tema atual e limpa o cache para forçar recarregamento."""
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self._bg_cache = None
            self._sprite_cache = None

    def get_assets(self, screen_width: int, screen_height: int) -> tuple[Any | None, Any | None]:
        """Retorna (Background, Sprite). Tenta carregar sob demanda e faz cache."""
        if not pygame:
            return None, None

        theme = self.themes[self.current_theme_name]

        # Carrega Background
        if self._bg_cache is None:
            try:
                img = pygame.image.load(theme["bg"]).convert()
                self._bg_cache = pygame.transform.smoothscale(img, (screen_width, screen_height))
            except (FileNotFoundError, pygame.error):
                self._bg_cache = None

        # Carrega Sprite
        if self._sprite_cache is None:
            try:
                self._sprite_cache = pygame.image.load(theme["sprite"]).convert_alpha()
            except (FileNotFoundError, pygame.error):
                self._sprite_cache = None

        return self._bg_cache, self._sprite_cache
