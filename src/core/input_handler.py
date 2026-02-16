"""
Input handler with configurable key mapping.
Maps pygame keys to game actions.
"""

import pygame
from typing import Dict, Set, Optional
from config import (
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
    KEY_A, KEY_B, KEY_START, KEY_SELECT
)


class InputHandler:
    """Handles keyboard input with configurable key bindings."""

    # Default key mappings
    DEFAULT_BINDINGS = {
        pygame.K_UP: KEY_UP,
        pygame.K_w: KEY_UP,
        pygame.K_DOWN: KEY_DOWN,
        pygame.K_s: KEY_DOWN,
        pygame.K_LEFT: KEY_LEFT,
        pygame.K_a: KEY_LEFT,
        pygame.K_RIGHT: KEY_RIGHT,
        pygame.K_d: KEY_RIGHT,
        pygame.K_z: KEY_A,
        pygame.K_RETURN: KEY_A,
        pygame.K_x: KEY_B,
        pygame.K_BACKSPACE: KEY_B,
        pygame.K_ESCAPE: KEY_START,
        pygame.K_LSHIFT: KEY_SELECT,
        pygame.K_RSHIFT: KEY_SELECT,
    }

    def __init__(self):
        self.bindings: Dict[int, str] = self.DEFAULT_BINDINGS.copy()
        self.keys_pressed: Set[str] = set()
        self.keys_just_pressed: Set[str] = set()
        self.keys_just_released: Set[str] = set()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Process a pygame event and return the action if a key was pressed.
        Returns None if the event wasn't a key event or wasn't mapped.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in self.bindings:
                action = self.bindings[event.key]
                self.keys_pressed.add(action)
                self.keys_just_pressed.add(action)
                return action

        elif event.type == pygame.KEYUP:
            if event.key in self.bindings:
                action = self.bindings[event.key]
                self.keys_pressed.discard(action)
                self.keys_just_released.add(action)
                return action

        return None

    def update(self) -> None:
        """Clear just_pressed and just_released for next frame."""
        self.keys_just_pressed.clear()
        self.keys_just_released.clear()

    def is_pressed(self, action: str) -> bool:
        """Check if an action key is currently held down."""
        return action in self.keys_pressed

    def is_just_pressed(self, action: str) -> bool:
        """Check if an action key was just pressed this frame."""
        return action in self.keys_just_pressed

    def is_just_released(self, action: str) -> bool:
        """Check if an action key was just released this frame."""
        return action in self.keys_just_released

    def get_direction(self) -> Optional[str]:
        """
        Get the current direction being pressed.
        Returns None if no direction, or the most recent if multiple.
        Priority: up, down, left, right
        """
        for direction in [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]:
            if direction in self.keys_pressed:
                return direction
        return None

    def get_just_pressed_direction(self) -> Optional[str]:
        """Get direction that was just pressed this frame."""
        for direction in [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]:
            if direction in self.keys_just_pressed:
                return direction
        return None

    def bind_key(self, pygame_key: int, action: str) -> None:
        """Bind a pygame key to an action."""
        self.bindings[pygame_key] = action

    def unbind_key(self, pygame_key: int) -> None:
        """Remove a key binding."""
        self.bindings.pop(pygame_key, None)

    def reset_bindings(self) -> None:
        """Reset to default key bindings."""
        self.bindings = self.DEFAULT_BINDINGS.copy()
