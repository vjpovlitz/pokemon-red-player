"""
Gen 1 type effectiveness chart.
"""

from typing import Dict, List

# Type effectiveness multipliers
# 2.0 = super effective
# 0.5 = not very effective
# 0.0 = no effect
# 1.0 = normal (default)

TYPE_CHART: Dict[str, Dict[str, float]] = {
    "normal": {
        "rock": 0.5,
        "ghost": 0.0
    },
    "fire": {
        "fire": 0.5,
        "water": 0.5,
        "grass": 2.0,
        "ice": 2.0,
        "bug": 2.0,
        "rock": 0.5,
        "dragon": 0.5
    },
    "water": {
        "fire": 2.0,
        "water": 0.5,
        "grass": 0.5,
        "ground": 2.0,
        "rock": 2.0,
        "dragon": 0.5
    },
    "electric": {
        "water": 2.0,
        "electric": 0.5,
        "grass": 0.5,
        "ground": 0.0,
        "flying": 2.0,
        "dragon": 0.5
    },
    "grass": {
        "fire": 0.5,
        "water": 2.0,
        "grass": 0.5,
        "poison": 0.5,
        "ground": 2.0,
        "flying": 0.5,
        "bug": 0.5,
        "rock": 2.0,
        "dragon": 0.5
    },
    "ice": {
        "fire": 0.5,
        "water": 0.5,
        "grass": 2.0,
        "ice": 0.5,
        "ground": 2.0,
        "flying": 2.0,
        "dragon": 2.0
    },
    "fighting": {
        "normal": 2.0,
        "ice": 2.0,
        "poison": 0.5,
        "flying": 0.5,
        "psychic": 0.5,
        "bug": 0.5,
        "rock": 2.0,
        "ghost": 0.0
    },
    "poison": {
        "grass": 2.0,
        "poison": 0.5,
        "ground": 0.5,
        "bug": 2.0,
        "rock": 0.5,
        "ghost": 0.5
    },
    "ground": {
        "fire": 2.0,
        "electric": 2.0,
        "grass": 0.5,
        "poison": 2.0,
        "flying": 0.0,
        "bug": 0.5,
        "rock": 2.0
    },
    "flying": {
        "electric": 0.5,
        "grass": 2.0,
        "fighting": 2.0,
        "bug": 2.0,
        "rock": 0.5
    },
    "psychic": {
        "fighting": 2.0,
        "poison": 2.0,
        "psychic": 0.5
    },
    "bug": {
        "fire": 0.5,
        "grass": 2.0,
        "fighting": 0.5,
        "poison": 2.0,
        "flying": 0.5,
        "psychic": 2.0,
        "ghost": 0.5
    },
    "rock": {
        "fire": 2.0,
        "ice": 2.0,
        "fighting": 0.5,
        "ground": 0.5,
        "flying": 2.0,
        "bug": 2.0
    },
    "ghost": {
        "normal": 0.0,
        "ghost": 2.0,
        "psychic": 0.0  # Gen 1 bug: Ghost doesn't affect Psychic
    },
    "dragon": {
        "dragon": 2.0
    }
}

# All types for reference
ALL_TYPES: List[str] = [
    "normal", "fire", "water", "electric", "grass",
    "ice", "fighting", "poison", "ground", "flying",
    "psychic", "bug", "rock", "ghost", "dragon"
]


def get_type_effectiveness(attack_type: str, defend_type: str) -> float:
    """
    Get effectiveness multiplier for attack type vs defense type.

    Args:
        attack_type: The attacking move's type
        defend_type: The defending Pokemon's type

    Returns:
        Effectiveness multiplier (2.0, 1.0, 0.5, or 0.0)
    """
    attack_type = attack_type.lower()
    defend_type = defend_type.lower()

    if attack_type in TYPE_CHART:
        return TYPE_CHART[attack_type].get(defend_type, 1.0)

    return 1.0


def get_all_effectiveness(attack_type: str, defend_types: List[str]) -> float:
    """
    Get combined effectiveness against multiple types.

    Args:
        attack_type: The attacking move's type
        defend_types: List of defending Pokemon's types

    Returns:
        Combined effectiveness multiplier
    """
    multiplier = 1.0
    for defend_type in defend_types:
        multiplier *= get_type_effectiveness(attack_type, defend_type)
    return multiplier


def get_weaknesses(pokemon_types: List[str]) -> List[str]:
    """Get types that are super effective against given types."""
    weaknesses = []
    for attack_type in ALL_TYPES:
        effectiveness = get_all_effectiveness(attack_type, pokemon_types)
        if effectiveness > 1.0:
            weaknesses.append(attack_type)
    return weaknesses


def get_resistances(pokemon_types: List[str]) -> List[str]:
    """Get types that are not very effective against given types."""
    resistances = []
    for attack_type in ALL_TYPES:
        effectiveness = get_all_effectiveness(attack_type, pokemon_types)
        if 0 < effectiveness < 1.0:
            resistances.append(attack_type)
    return resistances


def get_immunities(pokemon_types: List[str]) -> List[str]:
    """Get types that have no effect against given types."""
    immunities = []
    for attack_type in ALL_TYPES:
        effectiveness = get_all_effectiveness(attack_type, pokemon_types)
        if effectiveness == 0:
            immunities.append(attack_type)
    return immunities
