"""
Battle manager - coordinates battle logic.
"""

import random
from typing import List, Dict, Any, Optional

from src.pokemon.pokemon import Pokemon
from src.pokemon.stats import get_exp_yield, calculate_exp_yield
from src.battle.damage_calc import calculate_damage
from src.battle.battle_ai import BattleAI


class BattleManager:
    """Manages battle state and logic."""

    def __init__(self, player_party: List, enemy_pokemon: Optional[Dict[str, Any]] = None,
                 enemy_team: Optional[List[Pokemon]] = None, is_wild: bool = True):
        """
        Initialize battle.

        Args:
            player_party: List of player's Pokemon (dicts or Pokemon objects)
            enemy_pokemon: Wild Pokemon data dict
            enemy_team: Trainer's Pokemon team
            is_wild: True for wild battle, False for trainer
        """
        self.is_wild = is_wild
        self.turn_count = 0

        # Convert party to Pokemon objects if needed
        self.player_party: List[Pokemon] = []
        for p in player_party:
            if isinstance(p, Pokemon):
                self.player_party.append(p)
            elif isinstance(p, dict):
                self.player_party.append(Pokemon.from_dict(p))

        # Create starter if player has no Pokemon
        if not self.player_party:
            starter = Pokemon.create("PIKACHU", 5)
            if starter:
                self.player_party.append(starter)

        # Set up enemy
        if enemy_team:
            self.enemy_party = enemy_team
        elif enemy_pokemon:
            # Create wild Pokemon from data
            level = random.randint(
                enemy_pokemon.get("level_min", 3),
                enemy_pokemon.get("level_max", 5)
            )
            wild = Pokemon.create(enemy_pokemon.get("pokemon", "RATTATA"), level)
            self.enemy_party = [wild] if wild else []
        else:
            # Default wild Pokemon
            self.enemy_party = [Pokemon.create("RATTATA", 3)]

        # Current Pokemon indices
        self.player_index = self._get_first_able_index(self.player_party)
        self.enemy_index = self._get_first_able_index(self.enemy_party)

        # AI for enemy
        self.ai = BattleAI()

        # Escape attempts (affects run chance)
        self.escape_attempts = 0

    def _get_first_able_index(self, party: List[Pokemon]) -> int:
        """Get index of first non-fainted Pokemon."""
        for i, p in enumerate(party):
            if p and p.current_hp > 0:
                return i
        return 0

    @property
    def player_pokemon(self) -> Optional[Pokemon]:
        """Get current player Pokemon."""
        if 0 <= self.player_index < len(self.player_party):
            return self.player_party[self.player_index]
        return None

    @property
    def enemy_pokemon(self) -> Optional[Pokemon]:
        """Get current enemy Pokemon."""
        if 0 <= self.enemy_index < len(self.enemy_party):
            return self.enemy_party[self.enemy_index]
        return None

    def is_player_defeated(self) -> bool:
        """Check if all player Pokemon fainted."""
        return all(p.current_hp <= 0 for p in self.player_party if p)

    def is_enemy_defeated(self) -> bool:
        """Check if all enemy Pokemon fainted."""
        return all(p.current_hp <= 0 for p in self.enemy_party if p)

    def switch_player_pokemon(self, index: int) -> bool:
        """
        Switch to a different player Pokemon.

        Returns True if successful.
        """
        if 0 <= index < len(self.player_party):
            pokemon = self.player_party[index]
            if pokemon and pokemon.current_hp > 0:
                self.player_index = index
                return True
        return False

    def switch_enemy_pokemon(self) -> bool:
        """Switch to next available enemy Pokemon."""
        for i, p in enumerate(self.enemy_party):
            if p and p.current_hp > 0 and i != self.enemy_index:
                self.enemy_index = i
                return True
        return False

    def get_enemy_move(self) -> Optional[Dict[str, Any]]:
        """Get the enemy's move choice."""
        enemy = self.enemy_pokemon
        player = self.player_pokemon

        if not enemy or not player:
            return None

        return self.ai.choose_move(enemy, player)

    def calculate_exp_gain(self) -> int:
        """Calculate EXP gained from defeating enemy Pokemon."""
        enemy = self.enemy_pokemon
        if not enemy:
            return 0

        base_exp = get_exp_yield(enemy.species)
        return calculate_exp_yield(base_exp, enemy.level, self.is_wild)

    def try_catch(self, ball_type: str = "pokeball") -> tuple[bool, str]:
        """
        Attempt to catch wild Pokemon.

        Returns (success, message).
        """
        if not self.is_wild:
            return False, "You can't catch a trainer's Pokemon!"

        enemy = self.enemy_pokemon
        if not enemy:
            return False, "No Pokemon to catch!"

        # Gen 1 catch formula (simplified)
        # catch_rate = (max_hp * 255 * 4) / (current_hp * ball_rate)

        # Ball rates (higher = easier to catch)
        ball_rates = {
            "pokeball": 255,
            "greatball": 200,
            "ultraball": 150,
            "masterball": 0  # Always catches
        }

        ball_rate = ball_rates.get(ball_type, 255)

        if ball_type == "masterball":
            return True, f"{enemy.name} was caught!"

        # Calculate catch value
        hp_factor = (enemy.max_hp * 255 * 4) / max(1, enemy.current_hp * ball_rate)

        # Random check
        catch_check = random.randint(0, 255)

        if catch_check < hp_factor:
            # Caught!
            return True, f"Gotcha! {enemy.name} was caught!"
        else:
            # Shake animation count (0-3 shakes before breaking out)
            shakes = 0
            for _ in range(3):
                if random.randint(0, 65535) < hp_factor * 256:
                    shakes += 1
                else:
                    break

            if shakes == 0:
                return False, "Oh no! The Pokemon broke free!"
            elif shakes == 1:
                return False, "Aww! It appeared to be caught!"
            elif shakes == 2:
                return False, "Aargh! Almost had it!"
            else:
                # This shouldn't happen with proper formula, but just in case
                return False, "Shoot! It was so close too!"

    def try_run(self) -> bool:
        """
        Attempt to run from wild battle.

        Returns True if escape successful.
        """
        if not self.is_wild:
            return False

        player = self.player_pokemon
        enemy = self.enemy_pokemon

        if not player or not enemy:
            return True

        self.escape_attempts += 1

        # Gen 1 escape formula
        # escape_chance = (player_speed * 32) / (enemy_speed / 4) + 30 * attempts
        player_speed = player.stats.get("speed", 50)
        enemy_speed = enemy.stats.get("speed", 50)

        escape_odds = (player_speed * 32) / max(1, enemy_speed // 4)
        escape_odds += 30 * self.escape_attempts

        return random.randint(0, 255) < escape_odds
