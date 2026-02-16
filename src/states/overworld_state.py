"""
Overworld state - main gameplay state for exploring the world.
"""

import pygame
from typing import Optional

from src.core.state_manager import State
from src.core.camera import Camera
from src.world.tilemap import TileMap
from src.world.map_manager import MapManager
from src.entities.player import Player
from config import (
    NATIVE_WIDTH, NATIVE_HEIGHT, TILE_SIZE,
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_A, KEY_B,
    STATE_MENU, STATE_BATTLE, COLOR_BLACK
)


class OverworldState(State):
    """Main gameplay state for exploring the overworld."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.map_manager: Optional[MapManager] = None
        self.player: Optional[Player] = None
        self.camera: Optional[Camera] = None
        self.transition_timer = 0
        self.is_transitioning = False

    def enter(self, params=None) -> None:
        """Initialize the overworld."""
        # Create map manager and load initial map
        self.map_manager = MapManager()

        # Get starting position from game data
        start_map = self.game.player_data.get("current_map", "pallet_town")
        start_pos = self.game.player_data.get("position", {"x": 5, "y": 6})

        # Load the map
        self.map_manager.load_map(start_map)
        current_map = self.map_manager.current_map

        # Create player
        self.player = Player(
            start_pos["x"] * TILE_SIZE,
            start_pos["y"] * TILE_SIZE
        )

        # Create camera
        if current_map:
            self.camera = Camera(
                current_map.width * TILE_SIZE,
                current_map.height * TILE_SIZE
            )
        else:
            # Fallback for when map doesn't load
            self.camera = Camera(
                NATIVE_WIDTH * 2,
                NATIVE_HEIGHT * 2
            )

    def exit(self) -> None:
        """Save position when leaving."""
        if self.player:
            self.game.player_data["position"] = {
                "x": self.player.grid_x,
                "y": self.player.grid_y
            }

    def handle_event(self, event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False

        action = self.game.input.bindings.get(event.key)

        # Open menu with start
        if action == "start":
            self.state_manager.push(STATE_MENU)
            return True

        # Interact with A button
        if action == KEY_A and self.player and not self.player.is_moving:
            self._try_interact()
            return True

        return False

    def _try_interact(self) -> None:
        """Try to interact with whatever is in front of the player."""
        if not self.player or not self.map_manager.current_map:
            return

        # Get tile in front of player
        dx, dy = 0, 0
        if self.player.facing == "up":
            dy = -1
        elif self.player.facing == "down":
            dy = 1
        elif self.player.facing == "left":
            dx = -1
        elif self.player.facing == "right":
            dx = 1

        target_x = self.player.grid_x + dx
        target_y = self.player.grid_y + dy

        # Check for NPCs at target position
        for npc in self.map_manager.current_map.npcs:
            if npc.grid_x == target_x and npc.grid_y == target_y:
                npc.interact(self.game)
                return

        # Check for signs/objects
        # TODO: Implement sign reading

    def update(self, dt: float) -> None:
        if self.is_transitioning:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.is_transitioning = False
            return

        if not self.player:
            return

        # Handle movement input
        if not self.player.is_moving:
            direction = None
            if self.game.input.is_pressed(KEY_UP):
                direction = "up"
            elif self.game.input.is_pressed(KEY_DOWN):
                direction = "down"
            elif self.game.input.is_pressed(KEY_LEFT):
                direction = "left"
            elif self.game.input.is_pressed(KEY_RIGHT):
                direction = "right"

            if direction:
                self._try_move(direction)

        # Update player
        self.player.update(dt)

        # Update camera
        if self.camera:
            self.camera.update(self.player.x, self.player.y)

        # Update NPCs
        if self.map_manager.current_map:
            for npc in self.map_manager.current_map.npcs:
                npc.update(dt)

        # Check for wild encounters after movement completes
        if self.player.just_finished_moving:
            self._check_wild_encounter()
            self._check_warps()

    def _try_move(self, direction: str) -> None:
        """Try to move player in given direction."""
        if not self.player or not self.map_manager.current_map:
            return

        self.player.facing = direction

        dx, dy = 0, 0
        if direction == "up":
            dy = -1
        elif direction == "down":
            dy = 1
        elif direction == "left":
            dx = -1
        elif direction == "right":
            dx = 1

        target_x = self.player.grid_x + dx
        target_y = self.player.grid_y + dy

        # Check collision
        if self.map_manager.current_map.is_walkable(target_x, target_y):
            # Check for NPC collision
            for npc in self.map_manager.current_map.npcs:
                if npc.grid_x == target_x and npc.grid_y == target_y:
                    return  # Blocked by NPC

            self.player.start_move(direction)

    def _check_wild_encounter(self) -> None:
        """Check if player triggered a wild encounter."""
        if not self.map_manager.current_map:
            return

        # Check if current tile is grass
        tile = self.map_manager.current_map.get_tile(
            self.player.grid_x, self.player.grid_y
        )

        if tile and tile.get("encounter"):
            # Random encounter check (approximately 1 in 10 steps in grass)
            import random
            if random.random() < 0.1:
                self._start_wild_battle()

    def _start_wild_battle(self) -> None:
        """Start a wild Pokemon battle."""
        # Get encounter data for current area
        encounters = self.map_manager.current_map.encounters if self.map_manager.current_map else []

        if encounters:
            import random
            encounter = random.choice(encounters)
            self.state_manager.push(STATE_BATTLE, {
                "type": "wild",
                "pokemon": encounter
            })

    def _check_warps(self) -> None:
        """Check if player stepped on a warp tile."""
        if not self.map_manager.current_map:
            return

        warps = self.map_manager.current_map.warps
        player_pos = (self.player.grid_x, self.player.grid_y)

        for warp in warps:
            if (warp["x"], warp["y"]) == player_pos:
                self._do_warp(warp)
                break

    def _do_warp(self, warp: dict) -> None:
        """Execute a map warp."""
        self.is_transitioning = True
        self.transition_timer = 0.3

        # Load new map
        self.map_manager.load_map(warp["target_map"])

        # Position player
        self.player.x = warp["target_x"] * TILE_SIZE
        self.player.y = warp["target_y"] * TILE_SIZE
        self.player.grid_x = warp["target_x"]
        self.player.grid_y = warp["target_y"]

        # Update camera bounds
        if self.map_manager.current_map:
            self.camera.set_map_size(
                self.map_manager.current_map.width * TILE_SIZE,
                self.map_manager.current_map.height * TILE_SIZE
            )

        # Update game data
        self.game.player_data["current_map"] = warp["target_map"]

    def render(self, surface) -> None:
        # Clear with black
        surface.fill(COLOR_BLACK)

        if not self.map_manager.current_map or not self.camera:
            return

        # Render map layers
        self.map_manager.current_map.render(surface, self.camera)

        # Render NPCs
        for npc in self.map_manager.current_map.npcs:
            npc.render(surface, self.camera)

        # Render player
        if self.player:
            self.player.render(surface, self.camera)

        # Render map foreground (trees, roofs, etc)
        self.map_manager.current_map.render_foreground(surface, self.camera)

        # Transition fade
        if self.is_transitioning:
            alpha = int(255 * (self.transition_timer / 0.3))
            fade = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
            fade.fill(COLOR_BLACK)
            fade.set_alpha(alpha)
            surface.blit(fade, (0, 0))
