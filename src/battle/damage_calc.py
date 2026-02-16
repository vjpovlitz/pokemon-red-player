"""
Gen 1 damage calculation.
"""

import random
from typing import Dict, Any, Tuple, Optional

from src.battle.type_chart import get_type_effectiveness


def calculate_damage(attacker, defender, move: Dict[str, Any]) -> Tuple[int, float]:
    """
    Calculate damage using Gen 1 formula.

    Formula: ((2*Level/5+2) * Power * A/D / 50 + 2) * Modifiers

    Args:
        attacker: Attacking Pokemon
        defender: Defending Pokemon
        move: Move data dict

    Returns:
        Tuple of (damage, effectiveness_multiplier)
    """
    power = move.get("power", 0)

    # Non-damaging moves
    if power == 0:
        return 0, 1.0

    level = attacker.level
    move_type = move.get("type", "normal")

    # Determine if physical or special (Gen 1 uses type to determine)
    special_types = ["fire", "water", "electric", "grass", "ice", "psychic", "dragon"]

    if move_type in special_types:
        attack = attacker.stats.get("special", 50)
        defense = defender.stats.get("special", 50)
    else:
        attack = attacker.stats.get("attack", 50)
        defense = defender.stats.get("defense", 50)

    # Base damage calculation
    damage = ((2 * level / 5 + 2) * power * attack / defense) / 50 + 2

    # Critical hit check
    critical = 1.0
    base_speed = attacker.base_stats.get("speed", 50)
    crit_chance = base_speed / 512  # Gen 1 crit rate based on speed

    if random.random() < crit_chance:
        critical = 2.0
        # In Gen 1, crits ignore stat modifiers - simplified here

    damage *= critical

    # STAB (Same Type Attack Bonus)
    stab = 1.0
    if move_type in attacker.types:
        stab = 1.5

    damage *= stab

    # Type effectiveness
    effectiveness = 1.0
    for defender_type in defender.types:
        effectiveness *= get_type_effectiveness(move_type, defender_type)

    damage *= effectiveness

    # Random factor (0.85 to 1.0)
    random_factor = random.randint(217, 255) / 255
    damage *= random_factor

    # Minimum 1 damage if the move can deal damage
    final_damage = max(1, int(damage)) if effectiveness > 0 else 0

    return final_damage, effectiveness


def calculate_accuracy(move: Dict[str, Any], attacker, defender) -> bool:
    """
    Calculate if a move hits.

    Args:
        move: Move data dict
        attacker: Attacking Pokemon
        defender: Defending Pokemon

    Returns:
        True if move hits, False if misses
    """
    accuracy = move.get("accuracy", 100)

    # Always hit
    if accuracy >= 100:
        return True

    # Calculate hit chance (Gen 1 formula simplified)
    # In Gen 1, accuracy/evasion stages modify this
    hit_chance = accuracy

    return random.randint(1, 100) <= hit_chance


def is_critical_hit(attacker) -> bool:
    """
    Check for critical hit.

    Gen 1: Crit rate based on speed stat.
    """
    base_speed = attacker.base_stats.get("speed", 50)
    crit_threshold = base_speed // 2

    return random.randint(0, 255) < crit_threshold
