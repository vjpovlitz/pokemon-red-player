"""
Save/Load system using JSON format.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from config import SAVES_PATH


class SaveSystem:
    """Handles saving and loading game state."""

    SAVE_VERSION = 1

    def __init__(self):
        self.save_path = SAVES_PATH
        os.makedirs(self.save_path, exist_ok=True)

    def save(self, game, slot: int = 0) -> bool:
        """
        Save game state to file.

        Args:
            game: Game instance to save
            slot: Save slot number

        Returns:
            True if successful
        """
        try:
            save_data = self._serialize_game(game)
            save_data["save_version"] = self.SAVE_VERSION
            save_data["timestamp"] = datetime.now().isoformat()

            filename = f"save_{slot}.json"
            filepath = os.path.join(self.save_path, filename)

            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)

            return True

        except Exception as e:
            print(f"Save error: {e}")
            return False

    def load(self, slot: int = 0) -> Optional[Dict[str, Any]]:
        """
        Load game state from file.

        Args:
            slot: Save slot number

        Returns:
            Save data dict, or None if load failed
        """
        try:
            filename = f"save_{slot}.json"
            filepath = os.path.join(self.save_path, filename)

            if not os.path.exists(filepath):
                return None

            with open(filepath, 'r') as f:
                save_data = json.load(f)

            # Version check
            if save_data.get("save_version", 0) > self.SAVE_VERSION:
                print("Save file is from a newer version!")
                return None

            return save_data

        except Exception as e:
            print(f"Load error: {e}")
            return None

    def _serialize_game(self, game) -> Dict[str, Any]:
        """Serialize game state to dict."""
        player_data = game.player_data.copy()

        # Convert Pokemon objects to dicts
        party_data = []
        for pokemon in player_data.get("party", []):
            if hasattr(pokemon, 'to_dict'):
                party_data.append(pokemon.to_dict())
            else:
                party_data.append(pokemon)
        player_data["party"] = party_data

        # Convert PC Pokemon
        pc_data = []
        for pokemon in player_data.get("pc_pokemon", []):
            if hasattr(pokemon, 'to_dict'):
                pc_data.append(pokemon.to_dict())
            else:
                pc_data.append(pokemon)
        player_data["pc_pokemon"] = pc_data

        # Convert sets to lists
        if "pokedex" in player_data:
            player_data["pokedex"] = {
                "seen": list(player_data["pokedex"].get("seen", set())),
                "caught": list(player_data["pokedex"].get("caught", set()))
            }

        return {
            "player_data": player_data,
            "flags": game.flags.copy()
        }

    def deserialize_to_game(self, game, save_data: Dict[str, Any]) -> None:
        """Apply save data to game instance."""
        player_data = save_data.get("player_data", {})

        # Convert party dicts to Pokemon objects
        from src.pokemon.pokemon import Pokemon
        party = []
        for pokemon_data in player_data.get("party", []):
            if isinstance(pokemon_data, dict):
                party.append(Pokemon.from_dict(pokemon_data))
            else:
                party.append(pokemon_data)
        player_data["party"] = party

        # Convert PC dicts to Pokemon objects
        pc = []
        for pokemon_data in player_data.get("pc_pokemon", []):
            if isinstance(pokemon_data, dict):
                pc.append(Pokemon.from_dict(pokemon_data))
            else:
                pc.append(pokemon_data)
        player_data["pc_pokemon"] = pc

        # Convert pokedex lists to sets
        if "pokedex" in player_data:
            player_data["pokedex"] = {
                "seen": set(player_data["pokedex"].get("seen", [])),
                "caught": set(player_data["pokedex"].get("caught", []))
            }

        game.player_data = player_data
        game.flags = save_data.get("flags", {})

    def get_save_info(self, slot: int = 0) -> Optional[Dict[str, Any]]:
        """Get basic info about a save file without fully loading it."""
        try:
            filename = f"save_{slot}.json"
            filepath = os.path.join(self.save_path, filename)

            if not os.path.exists(filepath):
                return None

            with open(filepath, 'r') as f:
                save_data = json.load(f)

            player_data = save_data.get("player_data", {})

            return {
                "exists": True,
                "name": player_data.get("name", "???"),
                "badges": len(player_data.get("badges", [])),
                "play_time": player_data.get("play_time", 0),
                "timestamp": save_data.get("timestamp", ""),
                "location": player_data.get("current_map", "Unknown")
            }

        except Exception:
            return None

    def delete_save(self, slot: int = 0) -> bool:
        """Delete a save file."""
        try:
            filename = f"save_{slot}.json"
            filepath = os.path.join(self.save_path, filename)

            if os.path.exists(filepath):
                os.remove(filepath)
                return True

            return False

        except Exception:
            return False

    def has_save(self, slot: int = 0) -> bool:
        """Check if a save file exists."""
        filename = f"save_{slot}.json"
        filepath = os.path.join(self.save_path, filename)
        return os.path.exists(filepath)


def format_play_time(seconds: float) -> str:
    """Format play time as HH:MM."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}:{minutes:02d}"
