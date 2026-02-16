"""
Inventory/Bag system.
"""

from typing import Dict, List, Optional, Any


class Inventory:
    """Player's bag/inventory system."""

    # Item categories
    CATEGORY_ITEMS = "items"
    CATEGORY_KEY_ITEMS = "key_items"
    CATEGORY_POKEBALLS = "pokeballs"
    CATEGORY_TM_HM = "tm_hm"

    def __init__(self):
        self.pockets: Dict[str, Dict[str, int]] = {
            self.CATEGORY_ITEMS: {},
            self.CATEGORY_KEY_ITEMS: {},
            self.CATEGORY_POKEBALLS: {},
            self.CATEGORY_TM_HM: {}
        }

    def add_item(self, item_id: str, quantity: int = 1, category: str = CATEGORY_ITEMS) -> bool:
        """
        Add item(s) to inventory.

        Args:
            item_id: Item identifier
            quantity: Number to add
            category: Item category

        Returns:
            True if successful
        """
        if category not in self.pockets:
            return False

        if item_id in self.pockets[category]:
            self.pockets[category][item_id] += quantity
        else:
            self.pockets[category][item_id] = quantity

        # Cap at 99 for regular items
        if category != self.CATEGORY_KEY_ITEMS:
            self.pockets[category][item_id] = min(99, self.pockets[category][item_id])

        return True

    def remove_item(self, item_id: str, quantity: int = 1, category: str = CATEGORY_ITEMS) -> bool:
        """
        Remove item(s) from inventory.

        Returns True if successful, False if not enough items.
        """
        if category not in self.pockets:
            return False

        if item_id not in self.pockets[category]:
            return False

        if self.pockets[category][item_id] < quantity:
            return False

        self.pockets[category][item_id] -= quantity

        # Remove entry if zero
        if self.pockets[category][item_id] <= 0:
            del self.pockets[category][item_id]

        return True

    def has_item(self, item_id: str, quantity: int = 1, category: Optional[str] = None) -> bool:
        """Check if player has enough of an item."""
        if category:
            return self.pockets.get(category, {}).get(item_id, 0) >= quantity

        # Search all categories
        for pocket in self.pockets.values():
            if pocket.get(item_id, 0) >= quantity:
                return True

        return False

    def get_quantity(self, item_id: str, category: str = CATEGORY_ITEMS) -> int:
        """Get quantity of an item."""
        return self.pockets.get(category, {}).get(item_id, 0)

    def get_pocket(self, category: str) -> Dict[str, int]:
        """Get all items in a category."""
        return self.pockets.get(category, {}).copy()

    def get_all_items(self) -> List[tuple[str, str, int]]:
        """Get all items as list of (category, item_id, quantity)."""
        items = []
        for category, pocket in self.pockets.items():
            for item_id, quantity in pocket.items():
                items.append((category, item_id, quantity))
        return items

    def to_dict(self) -> Dict[str, Dict[str, int]]:
        """Serialize inventory."""
        return {cat: pocket.copy() for cat, pocket in self.pockets.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, int]]) -> 'Inventory':
        """Deserialize inventory."""
        inv = cls()
        for category, pocket in data.items():
            if category in inv.pockets:
                inv.pockets[category] = pocket.copy()
        return inv


# Item definitions
ITEMS = {
    # Healing items
    "potion": {
        "name": "Potion",
        "category": "items",
        "effect": "heal",
        "value": 20,
        "price": 300,
        "description": "Restores 20 HP."
    },
    "super_potion": {
        "name": "Super Potion",
        "category": "items",
        "effect": "heal",
        "value": 50,
        "price": 700,
        "description": "Restores 50 HP."
    },
    "antidote": {
        "name": "Antidote",
        "category": "items",
        "effect": "cure_poison",
        "price": 100,
        "description": "Cures poison."
    },
    "parlyz_heal": {
        "name": "Parlyz Heal",
        "category": "items",
        "effect": "cure_paralysis",
        "price": 200,
        "description": "Cures paralysis."
    },
    "awakening": {
        "name": "Awakening",
        "category": "items",
        "effect": "cure_sleep",
        "price": 250,
        "description": "Wakes up a Pokemon."
    },

    # Pokeballs
    "pokeball": {
        "name": "Poke Ball",
        "category": "pokeballs",
        "catch_rate": 255,
        "price": 200,
        "description": "A ball for catching Pokemon."
    },
    "greatball": {
        "name": "Great Ball",
        "category": "pokeballs",
        "catch_rate": 200,
        "price": 600,
        "description": "A good ball with a higher catch rate."
    },

    # Key items
    "oaks_parcel": {
        "name": "Oak's Parcel",
        "category": "key_items",
        "description": "A parcel for Prof. Oak."
    },
    "pokedex": {
        "name": "Pokedex",
        "category": "key_items",
        "description": "A device for recording Pokemon data."
    },
    "town_map": {
        "name": "Town Map",
        "category": "key_items",
        "description": "A map of the region."
    },
    "boulder_badge": {
        "name": "Boulder Badge",
        "category": "key_items",
        "description": "Badge from Pewter Gym."
    }
}


def get_item_data(item_id: str) -> Optional[Dict[str, Any]]:
    """Get item data by ID."""
    return ITEMS.get(item_id)


def use_item(item_id: str, target_pokemon) -> tuple[bool, str]:
    """
    Use an item on a Pokemon.

    Returns (success, message).
    """
    item = get_item_data(item_id)
    if not item:
        return False, "Invalid item!"

    effect = item.get("effect")

    if effect == "heal":
        if target_pokemon.current_hp >= target_pokemon.max_hp:
            return False, f"{target_pokemon.name}'s HP is full!"

        heal_amount = item.get("value", 20)
        target_pokemon.heal(heal_amount)
        return True, f"{target_pokemon.name} recovered {heal_amount} HP!"

    elif effect == "cure_poison":
        if target_pokemon.status != "poisoned":
            return False, f"{target_pokemon.name} isn't poisoned!"
        target_pokemon.status = None
        return True, f"{target_pokemon.name} was cured of poison!"

    elif effect == "cure_paralysis":
        if target_pokemon.status != "paralyzed":
            return False, f"{target_pokemon.name} isn't paralyzed!"
        target_pokemon.status = None
        return True, f"{target_pokemon.name} was cured of paralysis!"

    elif effect == "cure_sleep":
        if target_pokemon.status != "asleep":
            return False, f"{target_pokemon.name} isn't asleep!"
        target_pokemon.status = None
        return True, f"{target_pokemon.name} woke up!"

    return False, "This item can't be used here."
