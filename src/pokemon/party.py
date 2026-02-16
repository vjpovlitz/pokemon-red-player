"""
Party management system.
"""

from typing import List, Optional, Dict, Any

from src.pokemon.pokemon import Pokemon
from config import MAX_PARTY_SIZE


class Party:
    """Manages a party of Pokemon (max 6)."""

    def __init__(self):
        self.pokemon: List[Pokemon] = []

    def add(self, pokemon: Pokemon) -> bool:
        """
        Add a Pokemon to the party.

        Returns True if successful, False if party is full.
        """
        if len(self.pokemon) >= MAX_PARTY_SIZE:
            return False

        self.pokemon.append(pokemon)
        return True

    def remove(self, index: int) -> Optional[Pokemon]:
        """
        Remove a Pokemon from the party by index.

        Returns the removed Pokemon, or None if index invalid.
        """
        if 0 <= index < len(self.pokemon):
            return self.pokemon.pop(index)
        return None

    def swap(self, index1: int, index2: int) -> bool:
        """Swap two Pokemon positions in party."""
        if (0 <= index1 < len(self.pokemon) and
            0 <= index2 < len(self.pokemon)):
            self.pokemon[index1], self.pokemon[index2] = \
                self.pokemon[index2], self.pokemon[index1]
            return True
        return False

    def get_first_able(self) -> Optional[Pokemon]:
        """Get the first non-fainted Pokemon."""
        for pokemon in self.pokemon:
            if not pokemon.is_fainted():
                return pokemon
        return None

    def get_first_able_index(self) -> int:
        """Get index of first non-fainted Pokemon, or -1 if none."""
        for i, pokemon in enumerate(self.pokemon):
            if not pokemon.is_fainted():
                return i
        return -1

    def has_able_pokemon(self) -> bool:
        """Check if any Pokemon can battle."""
        return any(not p.is_fainted() for p in self.pokemon)

    def heal_all(self) -> None:
        """Fully heal all Pokemon in party."""
        for pokemon in self.pokemon:
            pokemon.full_heal()

    def is_full(self) -> bool:
        """Check if party is at max capacity."""
        return len(self.pokemon) >= MAX_PARTY_SIZE

    def is_empty(self) -> bool:
        """Check if party is empty."""
        return len(self.pokemon) == 0

    @property
    def size(self) -> int:
        """Get number of Pokemon in party."""
        return len(self.pokemon)

    def __len__(self) -> int:
        return len(self.pokemon)

    def __getitem__(self, index: int) -> Pokemon:
        return self.pokemon[index]

    def __iter__(self):
        return iter(self.pokemon)

    def to_list(self) -> List[Dict[str, Any]]:
        """Serialize party to list of dicts."""
        return [p.to_dict() for p in self.pokemon]

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> 'Party':
        """Deserialize party from list of dicts."""
        party = cls()
        for pokemon_data in data:
            pokemon = Pokemon.from_dict(pokemon_data)
            party.add(pokemon)
        return party
