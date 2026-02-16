"""
Pokemon class with Gen 1 mechanics.
"""

import random
import math
from typing import Dict, List, Optional, Any

from src.pokemon.stats import calculate_stat, calculate_hp


class Pokemon:
    """Represents a single Pokemon instance."""

    # Base stats for demo Pokemon (HP, Attack, Defense, Speed, Special)
    BASE_STATS = {
        "BULBASAUR": {"hp": 45, "attack": 49, "defense": 49, "speed": 45, "special": 65, "types": ["grass", "poison"]},
        "IVYSAUR": {"hp": 60, "attack": 62, "defense": 63, "speed": 60, "special": 80, "types": ["grass", "poison"]},
        "VENUSAUR": {"hp": 80, "attack": 82, "defense": 83, "speed": 80, "special": 100, "types": ["grass", "poison"]},
        "CHARMANDER": {"hp": 39, "attack": 52, "defense": 43, "speed": 65, "special": 50, "types": ["fire"]},
        "CHARMELEON": {"hp": 58, "attack": 64, "defense": 58, "speed": 80, "special": 65, "types": ["fire"]},
        "CHARIZARD": {"hp": 78, "attack": 84, "defense": 78, "speed": 100, "special": 85, "types": ["fire", "flying"]},
        "SQUIRTLE": {"hp": 44, "attack": 48, "defense": 65, "speed": 43, "special": 50, "types": ["water"]},
        "WARTORTLE": {"hp": 59, "attack": 63, "defense": 80, "speed": 58, "special": 65, "types": ["water"]},
        "BLASTOISE": {"hp": 79, "attack": 83, "defense": 100, "speed": 78, "special": 85, "types": ["water"]},
        "CATERPIE": {"hp": 45, "attack": 30, "defense": 35, "speed": 45, "special": 20, "types": ["bug"]},
        "METAPOD": {"hp": 50, "attack": 20, "defense": 55, "speed": 30, "special": 25, "types": ["bug"]},
        "BUTTERFREE": {"hp": 60, "attack": 45, "defense": 50, "speed": 70, "special": 80, "types": ["bug", "flying"]},
        "WEEDLE": {"hp": 40, "attack": 35, "defense": 30, "speed": 50, "special": 20, "types": ["bug", "poison"]},
        "KAKUNA": {"hp": 45, "attack": 25, "defense": 50, "speed": 35, "special": 25, "types": ["bug", "poison"]},
        "BEEDRILL": {"hp": 65, "attack": 80, "defense": 40, "speed": 75, "special": 45, "types": ["bug", "poison"]},
        "PIDGEY": {"hp": 40, "attack": 45, "defense": 40, "speed": 56, "special": 35, "types": ["normal", "flying"]},
        "PIDGEOTTO": {"hp": 63, "attack": 60, "defense": 55, "speed": 71, "special": 50, "types": ["normal", "flying"]},
        "PIDGEOT": {"hp": 83, "attack": 80, "defense": 75, "speed": 91, "special": 70, "types": ["normal", "flying"]},
        "RATTATA": {"hp": 30, "attack": 56, "defense": 35, "speed": 72, "special": 25, "types": ["normal"]},
        "RATICATE": {"hp": 55, "attack": 81, "defense": 60, "speed": 97, "special": 50, "types": ["normal"]},
        "PIKACHU": {"hp": 35, "attack": 55, "defense": 30, "speed": 90, "special": 50, "types": ["electric"]},
        "RAICHU": {"hp": 60, "attack": 90, "defense": 55, "speed": 100, "special": 90, "types": ["electric"]},
        "GEODUDE": {"hp": 40, "attack": 80, "defense": 100, "speed": 20, "special": 30, "types": ["rock", "ground"]},
        "GRAVELER": {"hp": 55, "attack": 95, "defense": 115, "speed": 35, "special": 45, "types": ["rock", "ground"]},
        "ONIX": {"hp": 35, "attack": 45, "defense": 160, "speed": 70, "special": 30, "types": ["rock", "ground"]},
    }

    # Default moves by Pokemon
    DEFAULT_MOVES = {
        "BULBASAUR": [{"name": "TACKLE", "power": 40, "type": "normal", "pp": 35},
                      {"name": "GROWL", "power": 0, "type": "normal", "pp": 40}],
        "CHARMANDER": [{"name": "SCRATCH", "power": 40, "type": "normal", "pp": 35},
                       {"name": "GROWL", "power": 0, "type": "normal", "pp": 40}],
        "SQUIRTLE": [{"name": "TACKLE", "power": 40, "type": "normal", "pp": 35},
                     {"name": "TAIL WHIP", "power": 0, "type": "normal", "pp": 30}],
        "PIDGEY": [{"name": "TACKLE", "power": 40, "type": "normal", "pp": 35},
                   {"name": "SAND ATTACK", "power": 0, "type": "ground", "pp": 15}],
        "RATTATA": [{"name": "TACKLE", "power": 40, "type": "normal", "pp": 35},
                    {"name": "TAIL WHIP", "power": 0, "type": "normal", "pp": 30}],
        "CATERPIE": [{"name": "TACKLE", "power": 40, "type": "normal", "pp": 35},
                     {"name": "STRING SHOT", "power": 0, "type": "bug", "pp": 40}],
        "WEEDLE": [{"name": "POISON STING", "power": 15, "type": "poison", "pp": 35},
                   {"name": "STRING SHOT", "power": 0, "type": "bug", "pp": 40}],
        "PIKACHU": [{"name": "THUNDER SHOCK", "power": 40, "type": "electric", "pp": 30},
                    {"name": "GROWL", "power": 0, "type": "normal", "pp": 40}],
        "GEODUDE": [{"name": "TACKLE", "power": 40, "type": "normal", "pp": 35},
                    {"name": "DEFENSE CURL", "power": 0, "type": "normal", "pp": 40}],
        "ONIX": [{"name": "TACKLE", "power": 40, "type": "normal", "pp": 35},
                 {"name": "SCREECH", "power": 0, "type": "normal", "pp": 40},
                 {"name": "ROCK THROW", "power": 50, "type": "rock", "pp": 15}],
    }

    def __init__(self, species: str, level: int, nickname: Optional[str] = None):
        """
        Initialize a Pokemon.

        Args:
            species: Pokemon species name (e.g., "PIKACHU")
            level: Pokemon level (1-100)
            nickname: Optional nickname
        """
        self.species = species.upper()
        self.name = nickname or self.species
        self.level = max(1, min(100, level))

        # Get base stats
        base = self.BASE_STATS.get(self.species, {
            "hp": 50, "attack": 50, "defense": 50, "speed": 50, "special": 50,
            "types": ["normal"]
        })

        self.types: List[str] = base.get("types", ["normal"])

        # Generate IVs (0-15 in Gen 1)
        self.ivs = {
            "attack": random.randint(0, 15),
            "defense": random.randint(0, 15),
            "speed": random.randint(0, 15),
            "special": random.randint(0, 15)
        }
        # HP IV is derived from other IVs in Gen 1
        self.ivs["hp"] = (
            (self.ivs["attack"] & 1) << 3 |
            (self.ivs["defense"] & 1) << 2 |
            (self.ivs["speed"] & 1) << 1 |
            (self.ivs["special"] & 1)
        )

        # EVs (stat experience in Gen 1, starts at 0)
        self.evs = {
            "hp": 0,
            "attack": 0,
            "defense": 0,
            "speed": 0,
            "special": 0
        }

        # Calculate stats
        self.base_stats = {
            "hp": base["hp"],
            "attack": base["attack"],
            "defense": base["defense"],
            "speed": base["speed"],
            "special": base["special"]
        }

        self.stats = self._calculate_stats()
        self.max_hp = self.stats["hp"]
        self.current_hp = self.max_hp

        # Experience
        self.exp = self._exp_for_level(self.level)
        self.exp_group = "medium_slow"  # Most Pokemon use this

        # Moves (max 4)
        self.moves: List[Dict[str, Any]] = []
        self._learn_default_moves()

        # Status condition
        self.status: Optional[str] = None  # None, "paralyzed", "burned", "poisoned", "asleep", "frozen"
        self.status_turns = 0

    def _calculate_stats(self) -> Dict[str, int]:
        """Calculate all stats based on level, IVs, and EVs."""
        stats = {}

        # HP calculation (different formula)
        stats["hp"] = calculate_hp(
            self.base_stats["hp"],
            self.ivs["hp"],
            self.evs["hp"],
            self.level
        )

        # Other stats
        for stat in ["attack", "defense", "speed", "special"]:
            stats[stat] = calculate_stat(
                self.base_stats[stat],
                self.ivs[stat],
                self.evs[stat],
                self.level
            )

        return stats

    def _learn_default_moves(self) -> None:
        """Learn default moves for species."""
        default = self.DEFAULT_MOVES.get(self.species, [
            {"name": "TACKLE", "power": 40, "type": "normal", "pp": 35}
        ])

        for move_data in default[:4]:
            self.moves.append({
                "name": move_data["name"],
                "power": move_data["power"],
                "type": move_data["type"],
                "pp": move_data["pp"],
                "current_pp": move_data["pp"],
                "accuracy": move_data.get("accuracy", 100)
            })

    def _exp_for_level(self, level: int) -> int:
        """Calculate total EXP needed for a level (medium slow group)."""
        # Medium Slow: 6/5 * n^3 - 15*n^2 + 100*n - 140
        n = level
        return int(1.2 * (n ** 3) - 15 * (n ** 2) + 100 * n - 140)

    def exp_to_next_level(self) -> int:
        """Get EXP needed to reach next level."""
        if self.level >= 100:
            return 0
        return self._exp_for_level(self.level + 1) - self.exp

    def gain_exp(self, amount: int) -> bool:
        """
        Gain experience points.

        Returns True if leveled up.
        """
        if self.level >= 100:
            return False

        self.exp += amount
        leveled_up = False

        while self.level < 100 and self.exp >= self._exp_for_level(self.level + 1):
            self._level_up()
            leveled_up = True

        return leveled_up

    def _level_up(self) -> None:
        """Handle level up."""
        self.level += 1

        # Recalculate stats
        old_max_hp = self.max_hp
        self.stats = self._calculate_stats()
        self.max_hp = self.stats["hp"]

        # Heal the HP gained from level up
        hp_gain = self.max_hp - old_max_hp
        self.current_hp = min(self.max_hp, self.current_hp + hp_gain)

        # TODO: Check for new moves to learn

    def take_damage(self, damage: int) -> None:
        """Take damage."""
        self.current_hp = max(0, self.current_hp - damage)

    def heal(self, amount: int) -> None:
        """Heal HP."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def full_heal(self) -> None:
        """Fully restore HP and PP, cure status."""
        self.current_hp = self.max_hp
        self.status = None
        self.status_turns = 0

        for move in self.moves:
            move["current_pp"] = move["pp"]

    def is_fainted(self) -> bool:
        """Check if Pokemon has fainted."""
        return self.current_hp <= 0

    def use_move(self, move_index: int) -> Optional[Dict[str, Any]]:
        """
        Use a move by index.

        Returns move data if successful, None if no PP.
        """
        if move_index >= len(self.moves):
            return None

        move = self.moves[move_index]
        if move["current_pp"] <= 0:
            return None

        move["current_pp"] -= 1
        return move

    @classmethod
    def create(cls, species: str, level: int, nickname: Optional[str] = None) -> Optional['Pokemon']:
        """Create a Pokemon of the given species and level."""
        return cls(species, level, nickname)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Pokemon to dictionary for saving."""
        return {
            "species": self.species,
            "name": self.name,
            "level": self.level,
            "current_hp": self.current_hp,
            "exp": self.exp,
            "ivs": self.ivs.copy(),
            "evs": self.evs.copy(),
            "moves": [m.copy() for m in self.moves],
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pokemon':
        """Deserialize Pokemon from dictionary."""
        pokemon = cls(data["species"], data["level"], data.get("name"))
        pokemon.current_hp = data.get("current_hp", pokemon.max_hp)
        pokemon.exp = data.get("exp", pokemon.exp)
        pokemon.ivs = data.get("ivs", pokemon.ivs)
        pokemon.evs = data.get("evs", pokemon.evs)
        pokemon.status = data.get("status")

        if "moves" in data:
            pokemon.moves = data["moves"]

        # Recalculate stats with loaded IVs/EVs
        pokemon.stats = pokemon._calculate_stats()
        pokemon.max_hp = pokemon.stats["hp"]

        return pokemon
