"""
Menu state - in-game pause menu.
"""

import pygame
from typing import List

from src.core.state_manager import State
from config import (
    NATIVE_WIDTH, NATIVE_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_LIGHT,
    KEY_UP, KEY_DOWN, KEY_A, KEY_B
)


class MenuState(State):
    """In-game menu overlay."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.options = ["POKEMON", "BAG", "SAVE", "EXIT"]
        self.cursor = 0
        self.font = pygame.font.Font(None, 16)

        # Menu dimensions
        self.menu_width = 60
        self.menu_height = len(self.options) * 14 + 8
        self.menu_x = NATIVE_WIDTH - self.menu_width - 4
        self.menu_y = 4

    def handle_event(self, event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False

        action = self.game.input.bindings.get(event.key)

        if action == KEY_UP:
            self.cursor = (self.cursor - 1) % len(self.options)
            return True

        elif action == KEY_DOWN:
            self.cursor = (self.cursor + 1) % len(self.options)
            return True

        elif action == KEY_A:
            self._select_option()
            return True

        elif action == KEY_B or action == "start":
            self.state_manager.pop()
            return True

        return False

    def _select_option(self) -> None:
        """Handle menu selection."""
        option = self.options[self.cursor]

        if option == "POKEMON":
            # TODO: Open party screen
            pass

        elif option == "BAG":
            # TODO: Open bag screen
            pass

        elif option == "SAVE":
            self._save_game()

        elif option == "EXIT":
            self.state_manager.pop()

    def _save_game(self) -> None:
        """Save the current game state."""
        import json
        import os
        from config import SAVES_PATH

        # Ensure saves directory exists
        os.makedirs(SAVES_PATH, exist_ok=True)

        save_data = {
            "player_data": self.game.player_data.copy(),
            "flags": self.game.flags.copy()
        }

        # Convert sets to lists for JSON serialization
        save_data["player_data"]["pokedex"] = {
            "seen": list(save_data["player_data"]["pokedex"]["seen"]),
            "caught": list(save_data["player_data"]["pokedex"]["caught"])
        }

        # Convert party Pokemon to dicts
        save_data["player_data"]["party"] = [
            p.to_dict() if hasattr(p, 'to_dict') else p
            for p in save_data["player_data"]["party"]
        ]

        save_path = os.path.join(SAVES_PATH, "save.json")
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)

        # TODO: Show "Game saved!" message

    def update(self, dt: float) -> None:
        pass

    def render(self, surface) -> None:
        # Semi-transparent overlay (optional, skip for Game Boy style)

        # Draw menu box
        menu_rect = pygame.Rect(
            self.menu_x, self.menu_y,
            self.menu_width, self.menu_height
        )
        pygame.draw.rect(surface, COLOR_WHITE, menu_rect)
        pygame.draw.rect(surface, COLOR_BLACK, menu_rect, 2)

        # Draw options
        for i, option in enumerate(self.options):
            y = self.menu_y + 6 + i * 14
            x = self.menu_x + 14

            # Draw cursor
            if i == self.cursor:
                arrow = self.font.render(">", True, COLOR_BLACK)
                surface.blit(arrow, (self.menu_x + 4, y))

            # Draw option text
            text = self.font.render(option, True, COLOR_BLACK)
            surface.blit(text, (x, y))
