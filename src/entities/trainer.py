"""
Trainer NPC class - extends NPC with battle capabilities.
"""

import pygame
from typing import List, Dict, Any, Optional

from src.entities.npc import NPC
from src.pokemon.pokemon import Pokemon
from config import TILE_SIZE


class Trainer(NPC):
    """A trainer NPC that can battle the player."""

    def __init__(self, x: int, y: int, name: str = "TRAINER",
                 trainer_class: str = "Bug Catcher",
                 dialogue: List[str] = None,
                 defeat_dialogue: List[str] = None,
                 team: List[Dict[str, Any]] = None,
                 facing: str = "down",
                 sight_range: int = 4,
                 prize_money: int = 100):
        """
        Initialize trainer.

        Args:
            x: Grid X position
            y: Grid Y position
            name: Trainer name
            trainer_class: Trainer class (e.g., "Bug Catcher", "Youngster")
            dialogue: Pre-battle dialogue
            defeat_dialogue: Dialogue after being defeated
            team: List of Pokemon data dicts
            facing: Direction trainer faces
            sight_range: How many tiles trainer can see
            prize_money: Money awarded when defeated
        """
        super().__init__(x, y, name, dialogue, facing, wanders=False)

        self.trainer_class = trainer_class
        self.defeat_dialogue = defeat_dialogue or ["..."]
        self.sight_range = sight_range
        self.prize_money = prize_money
        self.defeated = False

        # Build team
        self.team: List[Pokemon] = []
        if team:
            for pokemon_data in team:
                pokemon = Pokemon.create(
                    pokemon_data.get("species", "RATTATA"),
                    pokemon_data.get("level", 5)
                )
                if pokemon:
                    self.team.append(pokemon)

        # Update sprite for trainer
        self.sprite = self._create_trainer_sprite()

    def _create_trainer_sprite(self) -> pygame.Surface:
        """Create a trainer-specific placeholder sprite."""
        sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Body (different colors for trainers)
        pygame.draw.rect(sprite, (168, 80, 80), (4, 6, 8, 10))

        # Head
        pygame.draw.rect(sprite, (248, 208, 176), (4, 2, 8, 6))

        # Hat/hair
        pygame.draw.rect(sprite, (80, 48, 32), (3, 0, 10, 3))

        return sprite

    @property
    def display_name(self) -> str:
        """Get full display name (class + name)."""
        return f"{self.trainer_class} {self.name}"

    def can_see_player(self, player_x: int, player_y: int) -> bool:
        """Check if trainer can see player (in line of sight)."""
        if self.defeated:
            return False

        dx = player_x - self.grid_x
        dy = player_y - self.grid_y

        # Check if player is in facing direction
        if self.facing == "up" and dy < 0 and dx == 0:
            return abs(dy) <= self.sight_range
        elif self.facing == "down" and dy > 0 and dx == 0:
            return abs(dy) <= self.sight_range
        elif self.facing == "left" and dx < 0 and dy == 0:
            return abs(dx) <= self.sight_range
        elif self.facing == "right" and dx > 0 and dy == 0:
            return abs(dx) <= self.sight_range

        return False

    def interact(self, game) -> None:
        """Handle interaction with trainer."""
        if self.defeated:
            # Show defeat dialogue
            dialogue = self.defeat_dialogue
        else:
            # Start trainer battle
            dialogue = self.dialogue

        # Face the player
        player_x = game.player_data["position"]["x"]
        player_y = game.player_data["position"]["y"]

        dx = player_x - self.grid_x
        dy = player_y - self.grid_y

        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        else:
            self.facing = "down" if dy > 0 else "up"

        # TODO: Push dialogue state, then battle state
        print(f"{self.display_name}: {dialogue[0]}")

    def start_battle(self, game) -> Dict[str, Any]:
        """
        Get battle parameters for this trainer.

        Returns dict to pass to battle state.
        """
        return {
            "type": "trainer",
            "trainer_name": self.display_name,
            "team": self.team,
            "prize_money": self.prize_money
        }

    def on_defeat(self, game) -> None:
        """Called when trainer is defeated."""
        self.defeated = True

        # Award prize money
        game.player_data["money"] += self.prize_money

    def get_lead_pokemon(self) -> Optional[Pokemon]:
        """Get the first non-fainted Pokemon."""
        for pokemon in self.team:
            if pokemon.current_hp > 0:
                return pokemon
        return None

    def has_pokemon_remaining(self) -> bool:
        """Check if trainer has any Pokemon left."""
        return any(p.current_hp > 0 for p in self.team)
