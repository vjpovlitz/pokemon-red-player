"""
Map manager for loading and switching between maps.
"""

import os
import json
from typing import Dict, Optional

from config import MAPS_PATH, TILESETS_PATH
from src.world.tilemap import TileMap, TileSet
from src.entities.npc import NPC


class MapManager:
    """Manages map loading, caching, and transitions."""

    def __init__(self):
        self.maps: Dict[str, TileMap] = {}
        self.tilesets: Dict[str, TileSet] = {}
        self.current_map: Optional[TileMap] = None
        self.current_map_name = ""

    def load_map(self, map_name: str) -> Optional[TileMap]:
        """Load a map by name, using cache if available."""
        # Check cache first
        if map_name in self.maps:
            self.current_map = self.maps[map_name]
            self.current_map_name = map_name
            return self.current_map

        # Try to load from file
        map_path = os.path.join(MAPS_PATH, f"{map_name}.json")

        tilemap = TileMap()

        if os.path.exists(map_path):
            # Load map data
            with open(map_path, 'r') as f:
                map_data = json.load(f)

            # Load or get tileset
            tileset_name = map_data.get("tileset", "overworld")
            tileset = self._get_tileset(tileset_name)

            tilemap.load_from_json(map_path, tileset)

            # Load NPCs for this map
            self._load_npcs(tilemap, map_data.get("npcs", []))
        else:
            # Create default map for testing
            tilemap.create_default()

        # Cache and set as current
        self.maps[map_name] = tilemap
        self.current_map = tilemap
        self.current_map_name = map_name

        return tilemap

    def _get_tileset(self, tileset_name: str) -> TileSet:
        """Get or load a tileset."""
        if tileset_name in self.tilesets:
            return self.tilesets[tileset_name]

        tileset_path = os.path.join(TILESETS_PATH, f"{tileset_name}.png")
        tileset = TileSet(tileset_path)
        self.tilesets[tileset_name] = tileset

        return tileset

    def _load_npcs(self, tilemap: TileMap, npc_data: list) -> None:
        """Load NPCs for a map."""
        tilemap.npcs = []

        for data in npc_data:
            npc = NPC(
                x=data.get("x", 0),
                y=data.get("y", 0),
                name=data.get("name", "NPC"),
                dialogue=data.get("dialogue", ["..."]),
                facing=data.get("facing", "down"),
                wanders=data.get("wanders", False)
            )
            tilemap.npcs.append(npc)

    def unload_map(self, map_name: str) -> None:
        """Remove a map from cache to free memory."""
        if map_name in self.maps:
            del self.maps[map_name]

    def clear_cache(self) -> None:
        """Clear all cached maps."""
        self.maps.clear()
        self.current_map = None
        self.current_map_name = ""

    def get_warp_at(self, x: int, y: int) -> Optional[dict]:
        """Get warp data at position if exists."""
        if not self.current_map:
            return None

        for warp in self.current_map.warps:
            if warp["x"] == x and warp["y"] == y:
                return warp

        return None
