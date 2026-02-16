"""
Sprite animation system.
Handles frame-based animations for characters and effects.
"""

import pygame
from typing import Dict, List, Optional


class Animation:
    """A single animation sequence."""

    def __init__(self, frames: List[pygame.Surface], frame_duration: float, loop: bool = True):
        """
        Initialize animation.

        Args:
            frames: List of pygame surfaces for each frame
            frame_duration: Duration of each frame in seconds
            loop: Whether the animation loops
        """
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.finished = False

    def update(self, dt: float) -> None:
        """Update animation timing."""
        if self.finished:
            return

        self.elapsed_time += dt

        while self.elapsed_time >= self.frame_duration:
            self.elapsed_time -= self.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True

    def reset(self) -> None:
        """Reset animation to beginning."""
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.finished = False

    @property
    def image(self) -> pygame.Surface:
        """Get the current frame image."""
        return self.frames[self.current_frame]


class AnimationController:
    """Manages multiple animations for an entity."""

    def __init__(self):
        self.animations: Dict[str, Animation] = {}
        self.current_animation: Optional[str] = None
        self._cached_image: Optional[pygame.Surface] = None

    def add(self, name: str, animation: Animation) -> None:
        """Add an animation."""
        self.animations[name] = animation

    def play(self, name: str, reset: bool = True) -> None:
        """
        Play an animation.

        Args:
            name: Animation name
            reset: Whether to reset the animation if already playing
        """
        if name not in self.animations:
            return

        if self.current_animation != name or reset:
            self.current_animation = name
            self.animations[name].reset()

    def update(self, dt: float) -> None:
        """Update the current animation."""
        if self.current_animation and self.current_animation in self.animations:
            self.animations[self.current_animation].update(dt)

    @property
    def image(self) -> Optional[pygame.Surface]:
        """Get the current animation frame."""
        if self.current_animation and self.current_animation in self.animations:
            return self.animations[self.current_animation].image
        return self._cached_image

    @property
    def is_finished(self) -> bool:
        """Check if current animation has finished (for non-looping)."""
        if self.current_animation and self.current_animation in self.animations:
            return self.animations[self.current_animation].finished
        return True


class SpriteSheet:
    """Utility for loading sprites from a sprite sheet."""

    def __init__(self, image: pygame.Surface, sprite_width: int, sprite_height: int):
        """
        Initialize sprite sheet.

        Args:
            image: The full sprite sheet surface
            sprite_width: Width of each sprite
            sprite_height: Height of each sprite
        """
        self.image = image
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.cols = image.get_width() // sprite_width
        self.rows = image.get_height() // sprite_height

    def get_sprite(self, col: int, row: int) -> pygame.Surface:
        """Get a single sprite at the given grid position."""
        rect = pygame.Rect(
            col * self.sprite_width,
            row * self.sprite_height,
            self.sprite_width,
            self.sprite_height
        )
        sprite = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
        sprite.blit(self.image, (0, 0), rect)
        return sprite

    def get_sprites(self, positions: List[tuple[int, int]]) -> List[pygame.Surface]:
        """Get multiple sprites at the given positions."""
        return [self.get_sprite(col, row) for col, row in positions]

    def get_row(self, row: int, start_col: int = 0, count: Optional[int] = None) -> List[pygame.Surface]:
        """Get a row of sprites for an animation."""
        if count is None:
            count = self.cols - start_col
        return [self.get_sprite(start_col + i, row) for i in range(count)]
