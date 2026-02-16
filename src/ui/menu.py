"""
Menu UI components for battles and general use.
"""

import pygame
from typing import List, Dict, Any, Optional

from config import (
    NATIVE_WIDTH, NATIVE_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_LIGHT,
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT
)


class Menu:
    """Base menu class."""

    def __init__(self, options: List[str], x: int = 0, y: int = 0,
                 width: int = 80, columns: int = 1):
        """
        Initialize menu.

        Args:
            options: List of option strings
            x: X position
            y: Y position
            width: Menu width
            columns: Number of columns (1 or 2)
        """
        self.options = options
        self.x = x
        self.y = y
        self.width = width
        self.columns = columns
        self.cursor = 0

        self.font = pygame.font.Font(None, 16)
        self.line_height = 16
        self.padding = 8

        self._calculate_height()

    def _calculate_height(self) -> None:
        """Calculate menu height based on options."""
        rows = (len(self.options) + self.columns - 1) // self.columns
        self.height = rows * self.line_height + self.padding * 2

    def move_cursor(self, direction: str) -> None:
        """Move cursor in given direction."""
        if direction == KEY_UP:
            if self.columns == 1:
                self.cursor = (self.cursor - 1) % len(self.options)
            else:
                # Move up in grid
                if self.cursor >= self.columns:
                    self.cursor -= self.columns

        elif direction == KEY_DOWN:
            if self.columns == 1:
                self.cursor = (self.cursor + 1) % len(self.options)
            else:
                # Move down in grid
                if self.cursor + self.columns < len(self.options):
                    self.cursor += self.columns

        elif direction == KEY_LEFT and self.columns > 1:
            if self.cursor % self.columns > 0:
                self.cursor -= 1

        elif direction == KEY_RIGHT and self.columns > 1:
            if self.cursor % self.columns < self.columns - 1:
                if self.cursor + 1 < len(self.options):
                    self.cursor += 1

    def get_selected(self) -> str:
        """Get currently selected option."""
        if 0 <= self.cursor < len(self.options):
            return self.options[self.cursor]
        return ""

    def render(self, surface: pygame.Surface) -> None:
        """Render the menu."""
        # Draw background
        menu_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, COLOR_WHITE, menu_rect)
        pygame.draw.rect(surface, COLOR_BLACK, menu_rect, 2)

        # Draw options
        col_width = (self.width - self.padding * 2) // self.columns

        for i, option in enumerate(self.options):
            col = i % self.columns
            row = i // self.columns

            text_x = self.x + self.padding + col * col_width + 10
            text_y = self.y + self.padding + row * self.line_height

            # Draw cursor
            if i == self.cursor:
                arrow = self.font.render(">", True, COLOR_BLACK)
                surface.blit(arrow, (text_x - 10, text_y))

            # Draw option text
            text = self.font.render(option, True, COLOR_BLACK)
            surface.blit(text, (text_x, text_y))


class BattleMenu:
    """Battle action/move selection menu."""

    def __init__(self):
        self.mode = "main"  # "main", "moves", "pokemon", "bag"
        self.cursor = 0
        self.font = pygame.font.Font(None, 16)

        # Main menu options
        self.main_options = ["FIGHT", "BAG", "POKEMON", "RUN"]

        # Move list (set when showing moves)
        self.moves: List[Dict[str, Any]] = []

    def show_main_menu(self) -> None:
        """Show the main battle menu."""
        self.mode = "main"
        self.cursor = 0

    def show_move_menu(self, moves: List[Dict[str, Any]]) -> None:
        """Show move selection menu."""
        self.mode = "moves"
        self.moves = moves
        self.cursor = 0

    def move_cursor(self, direction: str) -> None:
        """Move cursor based on direction."""
        if self.mode == "main":
            # 2x2 grid
            if direction == KEY_UP and self.cursor >= 2:
                self.cursor -= 2
            elif direction == KEY_DOWN and self.cursor < 2:
                self.cursor += 2
            elif direction == KEY_LEFT and self.cursor % 2 == 1:
                self.cursor -= 1
            elif direction == KEY_RIGHT and self.cursor % 2 == 0:
                self.cursor += 1

        elif self.mode == "moves":
            # 2x2 grid for moves
            max_cursor = len(self.moves) - 1
            if direction == KEY_UP and self.cursor >= 2:
                self.cursor -= 2
            elif direction == KEY_DOWN and self.cursor + 2 <= max_cursor:
                self.cursor += 2
            elif direction == KEY_LEFT and self.cursor % 2 == 1:
                self.cursor -= 1
            elif direction == KEY_RIGHT and self.cursor % 2 == 0 and self.cursor + 1 <= max_cursor:
                self.cursor += 1

    def get_selected(self) -> str:
        """Get selected option name."""
        if self.mode == "main":
            return self.main_options[self.cursor]
        elif self.mode == "moves" and self.cursor < len(self.moves):
            return self.moves[self.cursor].get("name", "")
        return ""

    def render(self, surface: pygame.Surface) -> None:
        """Render battle menu."""
        # Menu box at bottom right
        menu_x = NATIVE_WIDTH - 80
        menu_y = NATIVE_HEIGHT - 48
        menu_width = 80
        menu_height = 48

        # Draw box
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(surface, COLOR_WHITE, menu_rect)
        pygame.draw.rect(surface, COLOR_BLACK, menu_rect, 2)

        if self.mode == "main":
            self._render_main_menu(surface, menu_x, menu_y)
        elif self.mode == "moves":
            self._render_move_menu(surface)

    def _render_main_menu(self, surface: pygame.Surface, x: int, y: int) -> None:
        """Render main action menu."""
        positions = [
            (x + 8, y + 8),    # FIGHT
            (x + 44, y + 8),   # BAG
            (x + 8, y + 24),   # POKEMON
            (x + 44, y + 24)   # RUN
        ]

        for i, option in enumerate(self.main_options):
            # Truncate long options
            display_text = option[:6]
            pos = positions[i]

            # Draw cursor
            if i == self.cursor:
                arrow = self.font.render(">", True, COLOR_BLACK)
                surface.blit(arrow, (pos[0] - 8, pos[1]))

            text = self.font.render(display_text, True, COLOR_BLACK)
            surface.blit(text, pos)

    def _render_move_menu(self, surface: pygame.Surface) -> None:
        """Render move selection menu."""
        # Full width for moves
        menu_x = 0
        menu_y = NATIVE_HEIGHT - 48
        menu_width = NATIVE_WIDTH
        menu_height = 48

        # Draw box
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(surface, COLOR_WHITE, menu_rect)
        pygame.draw.rect(surface, COLOR_BLACK, menu_rect, 2)

        positions = [
            (8, menu_y + 6),
            (84, menu_y + 6),
            (8, menu_y + 22),
            (84, menu_y + 22)
        ]

        for i, move in enumerate(self.moves[:4]):
            pos = positions[i]
            move_name = move.get("name", "---")[:10]

            # Draw cursor
            if i == self.cursor:
                arrow = self.font.render(">", True, COLOR_BLACK)
                surface.blit(arrow, (pos[0] - 8, pos[1]))

            text = self.font.render(move_name, True, COLOR_BLACK)
            surface.blit(text, pos)

        # Show PP for selected move
        if self.cursor < len(self.moves):
            move = self.moves[self.cursor]
            pp_text = f"PP {move.get('current_pp', 0)}/{move.get('pp', 0)}"
            pp_surface = self.font.render(pp_text, True, COLOR_BLACK)
            surface.blit(pp_surface, (menu_x + 8, menu_y + 38))

            # Show type
            type_text = move.get("type", "normal").upper()
            type_surface = self.font.render(type_text, True, COLOR_BLACK)
            surface.blit(type_surface, (menu_x + 100, menu_y + 38))
