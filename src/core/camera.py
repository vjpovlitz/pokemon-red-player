"""
Camera/viewport system for scrolling maps.
Centers on the player while respecting map boundaries.
"""

from config import NATIVE_WIDTH, NATIVE_HEIGHT, TILE_SIZE


class Camera:
    """Viewport that follows a target (usually the player)."""

    def __init__(self, map_width: int, map_height: int):
        """
        Initialize camera.

        Args:
            map_width: Map width in pixels
            map_height: Map height in pixels
        """
        self.x = 0
        self.y = 0
        self.map_width = map_width
        self.map_height = map_height
        self.viewport_width = NATIVE_WIDTH
        self.viewport_height = NATIVE_HEIGHT

    def update(self, target_x: int, target_y: int) -> None:
        """
        Center camera on target position while respecting bounds.

        Args:
            target_x: Target center X in pixels
            target_y: Target center Y in pixels
        """
        # Calculate ideal camera position (centered on target)
        ideal_x = target_x - self.viewport_width // 2 + TILE_SIZE // 2
        ideal_y = target_y - self.viewport_height // 2 + TILE_SIZE // 2

        # Clamp to map boundaries
        max_x = max(0, self.map_width - self.viewport_width)
        max_y = max(0, self.map_height - self.viewport_height)

        self.x = max(0, min(ideal_x, max_x))
        self.y = max(0, min(ideal_y, max_y))

    def set_map_size(self, width: int, height: int) -> None:
        """Update map dimensions (when switching maps)."""
        self.map_width = width
        self.map_height = height

    def apply(self, world_x: int, world_y: int) -> tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.

        Args:
            world_x: X position in world/map space
            world_y: Y position in world/map space

        Returns:
            Tuple of (screen_x, screen_y)
        """
        return (world_x - self.x, world_y - self.y)

    def reverse(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        """
        Convert screen coordinates to world coordinates.

        Args:
            screen_x: X position on screen
            screen_y: Y position on screen

        Returns:
            Tuple of (world_x, world_y)
        """
        return (screen_x + self.x, screen_y + self.y)

    def is_visible(self, world_x: int, world_y: int,
                   width: int = TILE_SIZE, height: int = TILE_SIZE) -> bool:
        """
        Check if a rectangle is visible in the viewport.

        Args:
            world_x: X position in world space
            world_y: Y position in world space
            width: Object width
            height: Object height

        Returns:
            True if any part of the object is visible
        """
        return (world_x + width > self.x and
                world_x < self.x + self.viewport_width and
                world_y + height > self.y and
                world_y < self.y + self.viewport_height)

    @property
    def rect(self) -> tuple[int, int, int, int]:
        """Get camera bounds as (x, y, width, height)."""
        return (self.x, self.y, self.viewport_width, self.viewport_height)

    def get_visible_tile_range(self) -> tuple[int, int, int, int]:
        """
        Get the range of tiles visible in the viewport.

        Returns:
            Tuple of (start_tile_x, start_tile_y, end_tile_x, end_tile_y)
        """
        start_x = self.x // TILE_SIZE
        start_y = self.y // TILE_SIZE
        # Add 1 to include partially visible tiles
        end_x = (self.x + self.viewport_width) // TILE_SIZE + 1
        end_y = (self.y + self.viewport_height) // TILE_SIZE + 1

        return (start_x, start_y, end_x, end_y)
