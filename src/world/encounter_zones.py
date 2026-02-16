"""
Wild Pokemon encounter system.
"""

import random
from typing import Dict, List, Optional, Any

from src.pokemon.pokemon import Pokemon


class EncounterZone:
    """Defines wild Pokemon encounters for an area."""

    def __init__(self, zone_data: Dict[str, Any]):
        self.name = zone_data.get("name", "Unknown")
        self.encounter_rate = zone_data.get("encounter_rate", 10)  # % chance per step
        self.pokemon: List[Dict[str, Any]] = zone_data.get("pokemon", [])

    def check_encounter(self) -> bool:
        """Roll for a random encounter."""
        return random.randint(1, 100) <= self.encounter_rate

    def generate_encounter(self) -> Optional[Pokemon]:
        """Generate a wild Pokemon based on zone probabilities."""
        if not self.pokemon:
            return None

        # Calculate total rate
        total_rate = sum(p.get("rate", 0) for p in self.pokemon)
        if total_rate <= 0:
            return None

        # Roll for Pokemon
        roll = random.randint(1, total_rate)
        cumulative = 0

        for pokemon_data in self.pokemon:
            cumulative += pokemon_data.get("rate", 0)
            if roll <= cumulative:
                # Generate this Pokemon
                level = random.randint(
                    pokemon_data.get("level_min", 2),
                    pokemon_data.get("level_max", 5)
                )
                return Pokemon.create(
                    pokemon_data.get("pokemon", "RATTATA"),
                    level
                )

        return None


class EncounterManager:
    """Manages encounter zones and wild battles."""

    # Default encounter data for demo areas
    DEFAULT_ENCOUNTERS = {
        "route_1": {
            "name": "Route 1",
            "encounter_rate": 20,
            "pokemon": [
                {"pokemon": "RATTATA", "level_min": 2, "level_max": 4, "rate": 50},
                {"pokemon": "PIDGEY", "level_min": 2, "level_max": 5, "rate": 50}
            ]
        },
        "route_2": {
            "name": "Route 2",
            "encounter_rate": 20,
            "pokemon": [
                {"pokemon": "RATTATA", "level_min": 3, "level_max": 5, "rate": 45},
                {"pokemon": "PIDGEY", "level_min": 3, "level_max": 6, "rate": 45},
                {"pokemon": "CATERPIE", "level_min": 3, "level_max": 5, "rate": 10}
            ]
        },
        "viridian_forest": {
            "name": "Viridian Forest",
            "encounter_rate": 25,
            "pokemon": [
                {"pokemon": "CATERPIE", "level_min": 3, "level_max": 5, "rate": 35},
                {"pokemon": "WEEDLE", "level_min": 3, "level_max": 5, "rate": 35},
                {"pokemon": "KAKUNA", "level_min": 4, "level_max": 6, "rate": 10},
                {"pokemon": "METAPOD", "level_min": 4, "level_max": 6, "rate": 10},
                {"pokemon": "PIKACHU", "level_min": 3, "level_max": 5, "rate": 10}
            ]
        },
        "pallet_town": {
            "name": "Pallet Town",
            "encounter_rate": 15,
            "pokemon": [
                {"pokemon": "RATTATA", "level_min": 2, "level_max": 4, "rate": 60},
                {"pokemon": "PIDGEY", "level_min": 2, "level_max": 4, "rate": 40}
            ]
        }
    }

    def __init__(self):
        self.zones: Dict[str, EncounterZone] = {}
        self._load_default_zones()

    def _load_default_zones(self) -> None:
        """Load default encounter zones."""
        for zone_id, zone_data in self.DEFAULT_ENCOUNTERS.items():
            self.zones[zone_id] = EncounterZone(zone_data)

    def get_zone(self, zone_id: str) -> Optional[EncounterZone]:
        """Get an encounter zone by ID."""
        return self.zones.get(zone_id)

    def check_encounter(self, zone_id: str) -> Optional[Pokemon]:
        """
        Check for and potentially generate a wild encounter.

        Returns Pokemon if encounter triggered, None otherwise.
        """
        zone = self.zones.get(zone_id)
        if not zone:
            return None

        if zone.check_encounter():
            return zone.generate_encounter()

        return None
