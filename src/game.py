"""
Main Game class - orchestrates game loop and systems.
"""

import pygame
from typing import Optional

from config import (
    NATIVE_WIDTH, NATIVE_HEIGHT, SCALE,
    STATE_TITLE, STATE_OVERWORLD, STATE_BATTLE, STATE_MENU
)
from src.core.state_manager import StateManager
from src.core.input_handler import InputHandler
from src.states.title_state import TitleState
from src.states.overworld_state import OverworldState
from src.states.battle_state import BattleState
from src.states.menu_state import MenuState


class Game:
    """Main game class that manages the game loop and systems."""

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the game.

        Args:
            screen: The main display surface
        """
        self.screen = screen
        # Create native resolution surface for pixel-perfect rendering
        self.native_surface = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))

        # Initialize systems
        self.input = InputHandler()
        self.state_manager = StateManager(self)

        # Game data (will be populated as game progresses)
        self.player_data = {
            "name": "RED",
            "money": 3000,
            "badges": [],
            "party": [],
            "pc_pokemon": [],
            "bag": {
                "items": {},
                "key_items": {},
                "pokeballs": {"pokeball": 5},
                "tm_hm": {}
            },
            "pokedex": {
                "seen": set(),
                "caught": set()
            },
            "play_time": 0,
            "current_map": "pallet_town",
            "position": {"x": 5, "y": 6}
        }

        # Flags for game events
        self.flags = {
            "got_starter": False,
            "got_pokedex": False,
            "delivered_parcel": False,
            "defeated_brock": False
        }

        # Register states
        self.state_manager.register(STATE_TITLE, TitleState)
        self.state_manager.register(STATE_OVERWORLD, OverworldState)
        self.state_manager.register(STATE_BATTLE, BattleState)
        self.state_manager.register(STATE_MENU, MenuState)

        # Start with title screen
        self.state_manager.push(STATE_TITLE)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events."""
        # Update input handler
        self.input.handle_event(event)

        # Pass to state manager
        self.state_manager.handle_event(event)

    def update(self, dt: float) -> None:
        """Update game logic."""
        # Track play time
        if self.state_manager.current and not isinstance(self.state_manager.current, TitleState):
            self.player_data["play_time"] += dt

        # Update current state
        self.state_manager.update(dt)

        # Clear input just_pressed flags at end of frame
        self.input.update()

    def render(self) -> None:
        """Render the game."""
        # Clear native surface
        self.native_surface.fill((0, 0, 0))

        # Render current state stack
        self.state_manager.render(self.native_surface)

        # Scale up to screen
        scaled = pygame.transform.scale(
            self.native_surface,
            (NATIVE_WIDTH * SCALE, NATIVE_HEIGHT * SCALE)
        )
        self.screen.blit(scaled, (0, 0))

    def start_new_game(self) -> None:
        """Initialize a new game."""
        self.player_data = {
            "name": "RED",
            "money": 3000,
            "badges": [],
            "party": [],
            "pc_pokemon": [],
            "bag": {
                "items": {},
                "key_items": {},
                "pokeballs": {"pokeball": 5},
                "tm_hm": {}
            },
            "pokedex": {
                "seen": set(),
                "caught": set()
            },
            "play_time": 0,
            "current_map": "pallet_town",
            "position": {"x": 5, "y": 6}
        }

        self.flags = {
            "got_starter": False,
            "got_pokedex": False,
            "delivered_parcel": False,
            "defeated_brock": False
        }

        # Transition to overworld
        self.state_manager.replace(STATE_OVERWORLD)

    def continue_game(self, save_data: dict) -> None:
        """Continue from saved game data."""
        self.player_data = save_data.get("player_data", self.player_data)
        self.flags = save_data.get("flags", self.flags)
        self.state_manager.replace(STATE_OVERWORLD)
