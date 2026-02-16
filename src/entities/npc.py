"""
NPC base class.
"""

import pygame
import random
from typing import List, Optional

from config import TILE_SIZE, MOVEMENT_FRAMES, PIXELS_PER_FRAME


class NPC:
    """Non-player character base class."""

    def __init__(self, x: int, y: int, name: str = "NPC",
                 dialogue: List[str] = None, facing: str = "down",
                 wanders: bool = False):
        """
        Initialize NPC.

        Args:
            x: Grid X position
            y: Grid Y position
            name: NPC name
            dialogue: List of dialogue lines
            facing: Initial facing direction
            wanders: Whether NPC moves randomly
        """
        self.grid_x = x
        self.grid_y = y
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE

        self.name = name
        self.dialogue = dialogue or ["..."]
        self.dialogue_index = 0
        self.facing = facing
        self.wanders = wanders

        # Movement state
        self.is_moving = False
        self.move_progress = 0
        self.move_dx = 0
        self.move_dy = 0

        # Wander timer
        self.wander_timer = random.uniform(2.0, 5.0)

        # Sprite
        self.sprite = self._create_placeholder_sprite()

    def _create_placeholder_sprite(self) -> pygame.Surface:
        """Create a simple placeholder sprite."""
        sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Body (green)
        pygame.draw.rect(sprite, (56, 168, 56), (4, 6, 8, 10))

        # Head (skin tone)
        pygame.draw.rect(sprite, (248, 208, 176), (4, 2, 8, 6))

        return sprite

    def update(self, dt: float) -> None:
        """Update NPC state."""
        if self.is_moving:
            self.move_progress += 1

            self.x += self.move_dx * PIXELS_PER_FRAME
            self.y += self.move_dy * PIXELS_PER_FRAME

            if self.move_progress >= MOVEMENT_FRAMES:
                self.is_moving = False
                self.grid_x += self.move_dx
                self.grid_y += self.move_dy
                self.x = self.grid_x * TILE_SIZE
                self.y = self.grid_y * TILE_SIZE
                self.move_dx = 0
                self.move_dy = 0

        elif self.wanders:
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(2.0, 5.0)
                self._try_wander()

    def _try_wander(self) -> None:
        """Attempt to move in a random direction."""
        directions = ["up", "down", "left", "right"]
        direction = random.choice(directions)

        # Just turn without moving sometimes
        if random.random() < 0.5:
            self.facing = direction
            return

        # TODO: Check collision before moving
        self._start_move(direction)

    def _start_move(self, direction: str) -> None:
        """Start moving in a direction."""
        self.facing = direction
        self.is_moving = True
        self.move_progress = 0

        if direction == "up":
            self.move_dx = 0
            self.move_dy = -1
        elif direction == "down":
            self.move_dx = 0
            self.move_dy = 1
        elif direction == "left":
            self.move_dx = -1
            self.move_dy = 0
        elif direction == "right":
            self.move_dx = 1
            self.move_dy = 0

    def interact(self, game) -> None:
        """Called when player interacts with this NPC."""
        # Face the player
        player_x = game.player_data["position"]["x"]
        player_y = game.player_data["position"]["y"]

        dx = player_x - self.grid_x
        dy = player_y - self.grid_y

        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        else:
            self.facing = "down" if dy > 0 else "up"

        # Show dialogue
        # TODO: Push dialogue state with current dialogue line
        print(f"{self.name}: {self.dialogue[self.dialogue_index]}")

    def get_current_dialogue(self) -> str:
        """Get the current dialogue line."""
        return self.dialogue[self.dialogue_index]

    def advance_dialogue(self) -> bool:
        """
        Advance to next dialogue line.

        Returns True if there are more lines, False if dialogue is complete.
        """
        self.dialogue_index += 1
        if self.dialogue_index >= len(self.dialogue):
            self.dialogue_index = 0
            return False
        return True

    def render(self, surface: pygame.Surface, camera) -> None:
        """Render the NPC."""
        screen_x, screen_y = camera.apply(self.x, self.y)
        surface.blit(self.sprite, (screen_x, screen_y))
