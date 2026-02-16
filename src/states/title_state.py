"""
Title screen state.
"""

import pygame
from src.core.state_manager import State
from config import (
    NATIVE_WIDTH, NATIVE_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_LIGHT, COLOR_DARK,
    KEY_A, KEY_UP, KEY_DOWN, STATE_OVERWORLD
)


class TitleState(State):
    """Title screen with new game / continue options."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.menu_options = ["NEW GAME", "CONTINUE", "OPTIONS"]
        self.selected = 0
        self.blink_timer = 0
        self.show_press_start = True

        # State: "press_start" or "menu"
        self.mode = "press_start"

        # Create fonts
        self.title_font = pygame.font.Font(None, 24)
        self.menu_font = pygame.font.Font(None, 16)

    def handle_event(self, event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False

        action = self.game.input.bindings.get(event.key)

        if self.mode == "press_start":
            if action in [KEY_A, "start"]:
                self.mode = "menu"
                return True

        elif self.mode == "menu":
            if action == KEY_UP:
                self.selected = (self.selected - 1) % len(self.menu_options)
                return True
            elif action == KEY_DOWN:
                self.selected = (self.selected + 1) % len(self.menu_options)
                return True
            elif action == KEY_A:
                self._select_option()
                return True

        return False

    def _select_option(self):
        option = self.menu_options[self.selected]
        if option == "NEW GAME":
            self.game.start_new_game()
        elif option == "CONTINUE":
            # TODO: Load save and continue
            self.game.start_new_game()  # For now, just start new
        elif option == "OPTIONS":
            pass  # TODO: Options menu

    def update(self, dt: float) -> None:
        self.blink_timer += dt
        if self.blink_timer >= 0.5:
            self.blink_timer = 0
            self.show_press_start = not self.show_press_start

    def render(self, surface) -> None:
        # Fill background with dark color
        surface.fill(COLOR_BLACK)

        # Draw title
        title_text = self.title_font.render("POKEMON", True, COLOR_WHITE)
        title_rect = title_text.get_rect(centerx=NATIVE_WIDTH // 2, y=20)
        surface.blit(title_text, title_rect)

        subtitle = self.title_font.render("RED VERSION", True, (248, 56, 0))
        sub_rect = subtitle.get_rect(centerx=NATIVE_WIDTH // 2, y=44)
        surface.blit(subtitle, sub_rect)

        if self.mode == "press_start":
            # Draw "Press Start" blinking text
            if self.show_press_start:
                press_text = self.menu_font.render("PRESS START", True, COLOR_WHITE)
                press_rect = press_text.get_rect(centerx=NATIVE_WIDTH // 2, y=100)
                surface.blit(press_text, press_rect)
        else:
            # Draw menu options
            for i, option in enumerate(self.menu_options):
                color = COLOR_WHITE if i == self.selected else COLOR_LIGHT
                text = self.menu_font.render(option, True, color)
                y = 80 + i * 16
                rect = text.get_rect(centerx=NATIVE_WIDTH // 2, y=y)
                surface.blit(text, rect)

                # Draw selector arrow
                if i == self.selected:
                    arrow = self.menu_font.render(">", True, COLOR_WHITE)
                    surface.blit(arrow, (rect.x - 12, y))

        # Copyright notice
        copy_text = self.menu_font.render("2024 DEMO", True, COLOR_DARK)
        copy_rect = copy_text.get_rect(centerx=NATIVE_WIDTH // 2, y=130)
        surface.blit(copy_text, copy_rect)
