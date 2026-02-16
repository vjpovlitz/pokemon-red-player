"""
Player character entity.
"""

import pygame
from typing import Optional

from config import TILE_SIZE, MOVEMENT_FRAMES, PIXELS_PER_FRAME, COLOR_WHITE


class Player:
    """The player character."""

    def __init__(self, x: int, y: int):
        """
        Initialize player.

        Args:
            x: Starting X position in pixels
            y: Starting Y position in pixels
        """
        # Position in pixels
        self.x = x
        self.y = y

        # Grid position (tile coordinates)
        self.grid_x = x // TILE_SIZE
        self.grid_y = y // TILE_SIZE

        # Movement state
        self.is_moving = False
        self.move_progress = 0  # 0 to MOVEMENT_FRAMES
        self.move_dx = 0
        self.move_dy = 0
        self.facing = "down"

        # Track if movement just finished (for encounter checks)
        self.just_finished_moving = False

        # Sprite
        self.sprite = self._create_placeholder_sprite()
        self.width = TILE_SIZE
        self.height = TILE_SIZE

    def _create_placeholder_sprite(self) -> pygame.Surface:
        """Create a simple placeholder sprite."""
        sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Body (blue)
        pygame.draw.rect(sprite, (0, 112, 248), (4, 6, 8, 10))

        # Head (skin tone)
        pygame.draw.rect(sprite, (248, 208, 176), (4, 2, 8, 6))

        # Hat (red)
        pygame.draw.rect(sprite, (248, 56, 0), (3, 0, 10, 4))

        return sprite

    def start_move(self, direction: str) -> None:
        """Start moving in a direction."""
        if self.is_moving:
            return

        self.facing = direction
        self.is_moving = True
        self.move_progress = 0
        self.just_finished_moving = False

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

    def update(self, dt: float) -> None:
        """Update player state."""
        self.just_finished_moving = False

        if self.is_moving:
            self.move_progress += 1

            # Update pixel position
            self.x += self.move_dx * PIXELS_PER_FRAME
            self.y += self.move_dy * PIXELS_PER_FRAME

            # Check if movement complete
            if self.move_progress >= MOVEMENT_FRAMES:
                self.is_moving = False
                self.just_finished_moving = True

                # Snap to grid
                self.grid_x += self.move_dx
                self.grid_y += self.move_dy
                self.x = self.grid_x * TILE_SIZE
                self.y = self.grid_y * TILE_SIZE

                self.move_dx = 0
                self.move_dy = 0

    def render(self, surface: pygame.Surface, camera) -> None:
        """Render the player."""
        screen_x, screen_y = camera.apply(self.x, self.y)
        surface.blit(self.sprite, (screen_x, screen_y))

    def set_position(self, grid_x: int, grid_y: int) -> None:
        """Set player position by grid coordinates."""
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.x = grid_x * TILE_SIZE
        self.y = grid_y * TILE_SIZE
        self.is_moving = False
        self.move_progress = 0

    @property
    def center_x(self) -> int:
        """Get center X position."""
        return self.x + TILE_SIZE // 2

    @property
    def center_y(self) -> int:
        """Get center Y position."""
        return self.y + TILE_SIZE // 2
