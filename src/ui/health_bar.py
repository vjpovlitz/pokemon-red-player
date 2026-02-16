"""
HP bar UI component.
"""

import pygame
from config import COLOR_BLACK


class HealthBar:
    """HP bar with smooth animation."""

    # HP bar colors
    COLOR_GREEN = (0, 248, 0)
    COLOR_YELLOW = (248, 176, 0)
    COLOR_RED = (248, 0, 0)
    COLOR_BG = (64, 64, 64)

    def __init__(self, current_hp: int, max_hp: int):
        """
        Initialize HP bar.

        Args:
            current_hp: Current HP value
            max_hp: Maximum HP value
        """
        self.current_hp = current_hp
        self.max_hp = max(1, max_hp)
        self.displayed_hp = current_hp  # For smooth animation
        self.target_hp = current_hp

        # Animation settings
        self.hp_per_second = 30  # HP change per second

    def set_hp(self, hp: int) -> None:
        """Set target HP (will animate to this value)."""
        self.target_hp = max(0, min(hp, self.max_hp))

    def set_hp_instant(self, hp: int) -> None:
        """Set HP instantly without animation."""
        self.current_hp = max(0, min(hp, self.max_hp))
        self.displayed_hp = self.current_hp
        self.target_hp = self.current_hp

    def update(self, dt: float) -> None:
        """Update HP bar animation."""
        if self.displayed_hp != self.target_hp:
            change = self.hp_per_second * dt

            if self.displayed_hp > self.target_hp:
                self.displayed_hp = max(self.target_hp, self.displayed_hp - change)
            else:
                self.displayed_hp = min(self.target_hp, self.displayed_hp + change)

            self.current_hp = int(self.displayed_hp)

    def is_animating(self) -> bool:
        """Check if HP bar is still animating."""
        return abs(self.displayed_hp - self.target_hp) > 0.1

    def get_color(self) -> tuple:
        """Get HP bar color based on percentage."""
        percent = self.displayed_hp / self.max_hp

        if percent > 0.5:
            return self.COLOR_GREEN
        elif percent > 0.2:
            return self.COLOR_YELLOW
        else:
            return self.COLOR_RED

    def render(self, surface: pygame.Surface, x: int, y: int, width: int = 48, height: int = 4) -> None:
        """
        Render HP bar.

        Args:
            surface: Surface to render to
            x: X position
            y: Y position
            width: Bar width
            height: Bar height
        """
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, self.COLOR_BG, bg_rect)

        # HP fill
        if self.max_hp > 0:
            fill_width = int((self.displayed_hp / self.max_hp) * width)
            fill_width = max(0, min(fill_width, width))

            if fill_width > 0:
                fill_rect = pygame.Rect(x, y, fill_width, height)
                pygame.draw.rect(surface, self.get_color(), fill_rect)

        # Border
        pygame.draw.rect(surface, COLOR_BLACK, bg_rect, 1)


class ExpBar:
    """Experience bar component."""

    COLOR_BLUE = (0, 128, 248)
    COLOR_BG = (64, 64, 64)

    def __init__(self, current_exp: int, exp_to_level: int):
        """
        Initialize EXP bar.

        Args:
            current_exp: Current EXP in level
            exp_to_level: Total EXP needed for next level
        """
        self.current_exp = current_exp
        self.exp_to_level = max(1, exp_to_level)
        self.displayed_exp = current_exp
        self.target_exp = current_exp

        self.exp_per_second = 50

    def set_exp(self, exp: int) -> None:
        """Set target EXP."""
        self.target_exp = max(0, min(exp, self.exp_to_level))

    def update(self, dt: float) -> None:
        """Update EXP bar animation."""
        if self.displayed_exp != self.target_exp:
            change = self.exp_per_second * dt

            if self.displayed_exp > self.target_exp:
                self.displayed_exp = max(self.target_exp, self.displayed_exp - change)
            else:
                self.displayed_exp = min(self.target_exp, self.displayed_exp + change)

            self.current_exp = int(self.displayed_exp)

    def render(self, surface: pygame.Surface, x: int, y: int, width: int = 64, height: int = 2) -> None:
        """Render EXP bar."""
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, self.COLOR_BG, bg_rect)

        # EXP fill
        if self.exp_to_level > 0:
            fill_width = int((self.displayed_exp / self.exp_to_level) * width)
            fill_width = max(0, min(fill_width, width))

            if fill_width > 0:
                fill_rect = pygame.Rect(x, y, fill_width, height)
                pygame.draw.rect(surface, self.COLOR_BLUE, fill_rect)
