"""
Tilemap system for rendering and collision detection.
"""

import pygame
import json
import os
from typing import Dict, List, Optional, Any

from config import TILE_SIZE, TILESETS_PATH, MAPS_PATH, COLOR_LIGHT


class Tile:
    """Represents a single tile type."""

    def __init__(self, tile_id: int, image: pygame.Surface,
                 walkable: bool = True, encounter: bool = False):
        self.id = tile_id
        self.image = image
        self.walkable = walkable
        self.encounter = encounter  # Can trigger wild encounters


class TileSet:
    """A collection of tiles loaded from a tileset image."""

    def __init__(self, image_path: str, tile_size: int = TILE_SIZE):
        self.tile_size = tile_size
        self.tiles: Dict[int, Tile] = {}

        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path).convert_alpha()
            self._load_tiles()
        else:
            # Create placeholder tiles
            self.image = None
            self._create_placeholder_tiles()

    def _load_tiles(self) -> None:
        """Load tiles from the tileset image."""
        if not self.image:
            return

        cols = self.image.get_width() // self.tile_size
        rows = self.image.get_height() // self.tile_size

        tile_id = 0
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(
                    col * self.tile_size,
                    row * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )
                tile_surface = pygame.Surface(
                    (self.tile_size, self.tile_size),
                    pygame.SRCALPHA
                )
                tile_surface.blit(self.image, (0, 0), rect)
                self.tiles[tile_id] = Tile(tile_id, tile_surface)
                tile_id += 1

    def _create_placeholder_tiles(self) -> None:
        """Create basic placeholder tiles when no tileset image exists."""
        # Grass tile (0)
        grass = pygame.Surface((self.tile_size, self.tile_size))
        grass.fill((136, 192, 112))
        self.tiles[0] = Tile(0, grass, walkable=True, encounter=True)

        # Path tile (1)
        path = pygame.Surface((self.tile_size, self.tile_size))
        path.fill((224, 208, 176))
        self.tiles[1] = Tile(1, path, walkable=True)

        # Water tile (2)
        water = pygame.Surface((self.tile_size, self.tile_size))
        water.fill((64, 144, 208))
        self.tiles[2] = Tile(2, water, walkable=False)

        # Wall/solid tile (3)
        wall = pygame.Surface((self.tile_size, self.tile_size))
        wall.fill((104, 88, 112))
        self.tiles[3] = Tile(3, wall, walkable=False)

        # House floor (4)
        floor = pygame.Surface((self.tile_size, self.tile_size))
        floor.fill((248, 232, 200))
        self.tiles[4] = Tile(4, floor, walkable=True)

        # Tree/obstacle (5)
        tree = pygame.Surface((self.tile_size, self.tile_size))
        tree.fill((56, 112, 64))
        self.tiles[5] = Tile(5, tree, walkable=False)

        # Tall grass (6)
        tall_grass = pygame.Surface((self.tile_size, self.tile_size))
        tall_grass.fill((96, 168, 88))
        # Draw grass pattern
        for i in range(0, self.tile_size, 4):
            pygame.draw.line(tall_grass, (56, 128, 56), (i, self.tile_size), (i + 2, self.tile_size - 6), 1)
        self.tiles[6] = Tile(6, tall_grass, walkable=True, encounter=True)

        # Ledge (7) - can only go down
        ledge = pygame.Surface((self.tile_size, self.tile_size))
        ledge.fill((160, 144, 128))
        self.tiles[7] = Tile(7, ledge, walkable=False)

    def get_tile(self, tile_id: int) -> Optional[Tile]:
        """Get a tile by ID."""
        return self.tiles.get(tile_id)


class TileMap:
    """A map made up of tiles."""

    def __init__(self):
        self.width = 0  # In tiles
        self.height = 0
        self.layers: List[List[List[int]]] = []  # [layer][y][x]
        self.collision_layer: List[List[int]] = []
        self.tileset: Optional[TileSet] = None
        self.warps: List[Dict[str, Any]] = []
        self.npcs: List[Any] = []
        self.encounters: List[Dict[str, Any]] = []
        self.name = ""

    def load_from_json(self, map_path: str, tileset: TileSet) -> bool:
        """Load map from JSON file."""
        if not os.path.exists(map_path):
            return False

        with open(map_path, 'r') as f:
            data = json.load(f)

        self.name = data.get("name", "Unknown")
        self.width = data.get("width", 10)
        self.height = data.get("height", 9)
        self.tileset = tileset

        # Load layers
        self.layers = data.get("layers", [])
        if not self.layers:
            # Create default empty layer
            self.layers = [[[0 for _ in range(self.width)] for _ in range(self.height)]]

        # Load collision layer
        self.collision_layer = data.get("collision", [])
        if not self.collision_layer:
            # Generate collision from tileset walkability
            self._generate_collision()

        # Load warps
        self.warps = data.get("warps", [])

        # Load encounters
        self.encounters = data.get("encounters", [])

        return True

    def _generate_collision(self) -> None:
        """Generate collision layer from tile walkability."""
        self.collision_layer = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Check bottom layer for collision
                if self.layers and y < len(self.layers[0]) and x < len(self.layers[0][y]):
                    tile_id = self.layers[0][y][x]
                    tile = self.tileset.get_tile(tile_id) if self.tileset else None
                    row.append(0 if tile and tile.walkable else 1)
                else:
                    row.append(1)  # Out of bounds = collision
            self.collision_layer.append(row)

    def create_default(self, width: int = 20, height: int = 18) -> None:
        """Create a default test map."""
        self.width = width
        self.height = height
        self.name = "pallet_town"

        # Create a simple tileset
        self.tileset = TileSet("", TILE_SIZE)  # Uses placeholder tiles

        # Create base layer (grass with path)
        base_layer = []
        for y in range(height):
            row = []
            for x in range(width):
                # Border of trees
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    row.append(5)  # Tree
                # Horizontal path in middle
                elif y == height // 2 and 3 <= x <= width - 4:
                    row.append(1)  # Path
                # Vertical path
                elif x == width // 2 and 3 <= y <= height - 4:
                    row.append(1)  # Path
                # Some tall grass patches
                elif 2 <= x <= 5 and 2 <= y <= 5:
                    row.append(6)  # Tall grass
                elif width - 6 <= x <= width - 3 and height - 6 <= y <= height - 3:
                    row.append(6)  # Tall grass
                else:
                    row.append(0)  # Regular grass
            base_layer.append(row)

        self.layers = [base_layer]
        self._generate_collision()

        # Add a warp to Route 1 (north exit)
        self.warps = [
            {
                "x": width // 2,
                "y": 1,
                "target_map": "route_1",
                "target_x": 5,
                "target_y": 17
            }
        ]

        # Add encounter data
        self.encounters = [
            {"pokemon": "RATTATA", "level_min": 2, "level_max": 4, "rate": 40},
            {"pokemon": "PIDGEY", "level_min": 2, "level_max": 5, "rate": 60}
        ]

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile position is walkable."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False

        if self.collision_layer and y < len(self.collision_layer) and x < len(self.collision_layer[y]):
            return self.collision_layer[y][x] == 0

        return True

    def get_tile(self, x: int, y: int, layer: int = 0) -> Optional[Dict[str, Any]]:
        """Get tile data at position."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None

        if layer < len(self.layers) and y < len(self.layers[layer]) and x < len(self.layers[layer][y]):
            tile_id = self.layers[layer][y][x]
            tile = self.tileset.get_tile(tile_id) if self.tileset else None
            if tile:
                return {
                    "id": tile_id,
                    "walkable": tile.walkable,
                    "encounter": tile.encounter
                }

        return None

    def render(self, surface: pygame.Surface, camera) -> None:
        """Render visible tiles to surface."""
        if not self.tileset:
            return

        start_x, start_y, end_x, end_y = camera.get_visible_tile_range()

        # Clamp to map bounds
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.width, end_x)
        end_y = min(self.height, end_y)

        # Render each layer
        for layer in self.layers:
            for y in range(start_y, end_y):
                if y >= len(layer):
                    continue
                for x in range(start_x, end_x):
                    if x >= len(layer[y]):
                        continue

                    tile_id = layer[y][x]
                    tile = self.tileset.get_tile(tile_id)

                    if tile and tile.image:
                        screen_x, screen_y = camera.apply(
                            x * TILE_SIZE,
                            y * TILE_SIZE
                        )
                        surface.blit(tile.image, (screen_x, screen_y))

    def render_foreground(self, surface: pygame.Surface, camera) -> None:
        """Render foreground elements (over player)."""
        # TODO: Implement foreground layer rendering (tree tops, roofs, etc.)
        pass
