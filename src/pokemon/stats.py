"""
Gen 1 stat calculation formulas.
"""

import math


def calculate_stat(base: int, iv: int, ev: int, level: int) -> int:
    """
    Calculate a non-HP stat using Gen 1 formula.

    Formula: ((Base + IV) * 2 + sqrt(EV) / 4) * Level / 100 + 5

    Args:
        base: Base stat value
        iv: Individual value (0-15)
        ev: Effort value (stat experience, 0-65535)
        level: Pokemon level (1-100)

    Returns:
        Calculated stat value
    """
    ev_bonus = math.floor(math.sqrt(ev) / 4)
    stat = math.floor(((base + iv) * 2 + ev_bonus) * level / 100) + 5
    return max(1, stat)


def calculate_hp(base: int, iv: int, ev: int, level: int) -> int:
    """
    Calculate HP stat using Gen 1 formula.

    Formula: ((Base + IV) * 2 + sqrt(EV) / 4) * Level / 100 + Level + 10

    Args:
        base: Base HP value
        iv: Individual value (0-15)
        ev: Effort value (0-65535)
        level: Pokemon level (1-100)

    Returns:
        Calculated HP value
    """
    ev_bonus = math.floor(math.sqrt(ev) / 4)
    hp = math.floor(((base + iv) * 2 + ev_bonus) * level / 100) + level + 10
    return max(1, hp)


def calculate_exp_yield(base_exp: int, level: int, is_wild: bool = True,
                        traded: bool = False) -> int:
    """
    Calculate experience gained from defeating a Pokemon.

    Gen 1 formula: (a * b * L) / (7 * s)
    Where:
        a = 1 if wild, 1.5 if trainer
        b = base exp yield
        L = defeated Pokemon's level
        s = number of Pokemon that participated (simplified to 1)

    Args:
        base_exp: Base experience yield of defeated Pokemon
        level: Level of defeated Pokemon
        is_wild: True if wild, False if trainer
        traded: True if Pokemon receiving exp was traded

    Returns:
        Experience points gained
    """
    a = 1.0 if is_wild else 1.5
    exp = (a * base_exp * level) / 7

    if traded:
        exp *= 1.5

    return int(exp)


# Base experience yields for demo Pokemon
BASE_EXP_YIELDS = {
    "BULBASAUR": 64,
    "IVYSAUR": 141,
    "VENUSAUR": 208,
    "CHARMANDER": 65,
    "CHARMELEON": 142,
    "CHARIZARD": 209,
    "SQUIRTLE": 66,
    "WARTORTLE": 143,
    "BLASTOISE": 210,
    "CATERPIE": 53,
    "METAPOD": 72,
    "BUTTERFREE": 160,
    "WEEDLE": 52,
    "KAKUNA": 71,
    "BEEDRILL": 159,
    "PIDGEY": 55,
    "PIDGEOTTO": 113,
    "PIDGEOT": 172,
    "RATTATA": 57,
    "RATICATE": 116,
    "PIKACHU": 82,
    "RAICHU": 122,
    "GEODUDE": 73,
    "GRAVELER": 134,
    "ONIX": 108,
}


def get_exp_yield(species: str) -> int:
    """Get base experience yield for a species."""
    return BASE_EXP_YIELDS.get(species.upper(), 50)
