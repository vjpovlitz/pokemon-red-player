"""
fire_red_memory.py — Pokemon Fire Red (US v1.0) memory map and struct parsing.

This module knows how to read and interpret the in-memory data structures of
Pokemon Fire Red (USA, version 1.0, game code BPRE). It provides:

  - GEN3_CHARSET: The proprietary Gen 3 character encoding table
  - SPECIES_NAMES: National Dex number → name lookup (Gen 1 complete)
  - Memory address constants for party data, save blocks, etc.
  - Struct parsing for Pokemon party data (including decryption)
  - FireRedReader: High-level class that combines the MGBAClient with
    memory-map knowledge to read game state

Architecture:
    FireRedReader uses MGBAClient to issue raw memory reads, then applies
    the Fire Red memory layout to parse those bytes into meaningful game data.

GBA memory regions used:
    0x02000000-0x0203FFFF  EWRAM (256 KB) — party data, save blocks
    0x03000000-0x03007FFF  IWRAM (32 KB)  — save block pointers

Pokemon data structure (100 bytes per party member):
    Bytes 0-3:   Personality Value (PID) — determines nature, gender, ability
    Bytes 4-7:   Original Trainer ID (OTID)
    Bytes 8-17:  Nickname (Gen 3 encoded, 10 bytes)
    Bytes 18-31: Language, OT name, markings
    Bytes 32-79: Encrypted substructures (4 x 12 bytes, XOR'd with PID^OTID)
                 Order determined by PID % 24:
                   G = Growth (species, item, EXP, friendship)
                   A = Attacks (4 move IDs + 4 PP values)
                   E = EVs/Condition (6 EVs + contest stats)
                   M = Miscellaneous (pokerus, met location, origins)
    Bytes 80-99: Battle-calculated stats (only valid in party, not PC)
                 Status, level, current HP, max HP, Atk, Def, Spd, SpA, SpD
"""

from __future__ import annotations

import struct
from typing import Any

from mgba_client import MGBAClient


# ==========================================================================
# GEN 3 CHARACTER ENCODING
# ==========================================================================
# Pokemon Gen 3 games use a proprietary character set (NOT ASCII/Unicode).
# Byte 0xFF is the string terminator. Byte 0x00 is a space.
# This table covers A-Z, a-z, 0-9, and common punctuation/symbols.
# ==========================================================================

GEN3_CHARSET = {
    # Uppercase A-Z (0xBB-0xD4)
    0xBB: "A", 0xBC: "B", 0xBD: "C", 0xBE: "D", 0xBF: "E",
    0xC0: "F", 0xC1: "G", 0xC2: "H", 0xC3: "I", 0xC4: "J",
    0xC5: "K", 0xC6: "L", 0xC7: "M", 0xC8: "N", 0xC9: "O",
    0xCA: "P", 0xCB: "Q", 0xCC: "R", 0xCD: "S", 0xCE: "T",
    0xCF: "U", 0xD0: "V", 0xD1: "W", 0xD2: "X", 0xD3: "Y",
    0xD4: "Z",
    # Lowercase a-z (0xD5-0xEE)
    0xD5: "a", 0xD6: "b", 0xD7: "c", 0xD8: "d", 0xD9: "e",
    0xDA: "f", 0xDB: "g", 0xDC: "h", 0xDD: "i", 0xDE: "j",
    0xDF: "k", 0xE0: "l", 0xE1: "m", 0xE2: "n", 0xE3: "o",
    0xE4: "p", 0xE5: "q", 0xE6: "r", 0xE7: "s", 0xE8: "t",
    0xE9: "u", 0xEA: "v", 0xEB: "w", 0xEC: "x", 0xED: "y",
    0xEE: "z",
    # Digits 0-9 (0xA1-0xAA)
    0xA1: "0", 0xA2: "1", 0xA3: "2", 0xA4: "3", 0xA5: "4",
    0xA6: "5", 0xA7: "6", 0xA8: "7", 0xA9: "8", 0xAA: "9",
    # Punctuation and symbols
    0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-",
    0xB0: "...", 0xB1: "\u201c", 0xB2: "\u201d",  # ellipsis, smart quotes
    0xB3: "\u2018", 0xB4: "\u2019",                # smart single quotes
    0xB5: "\u2642", 0xB6: "\u2640",                # male/female symbols
    0xB8: ",", 0xBA: "/",
    0x00: " ",       # space
    0xFF: "",        # string terminator (produces no character)
}


# ==========================================================================
# SPECIES NAMES (National Dex order, Gen 1 complete)
# ==========================================================================
# Maps species ID → display name. Gen 1 (1-151) is complete here.
# For species > 151, the MCP layer will fall back to "Pokemon #N".

SPECIES_NAMES = {
    0: "???",
    1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur",
    4: "Charmander", 5: "Charmeleon", 6: "Charizard",
    7: "Squirtle", 8: "Wartortle", 9: "Blastoise",
    10: "Caterpie", 11: "Metapod", 12: "Butterfree",
    13: "Weedle", 14: "Kakuna", 15: "Beedrill",
    16: "Pidgey", 17: "Pidgeotto", 18: "Pidgeot",
    19: "Rattata", 20: "Raticate",
    21: "Spearow", 22: "Fearow",
    23: "Ekans", 24: "Arbok",
    25: "Pikachu", 26: "Raichu",
    27: "Sandshrew", 28: "Sandslash",
    29: "Nidoran\u2640", 30: "Nidorina", 31: "Nidoqueen",
    32: "Nidoran\u2642", 33: "Nidorino", 34: "Nidoking",
    35: "Clefairy", 36: "Clefable",
    37: "Vulpix", 38: "Ninetales",
    39: "Jigglypuff", 40: "Wigglytuff",
    41: "Zubat", 42: "Golbat",
    43: "Oddish", 44: "Gloom", 45: "Vileplume",
    46: "Paras", 47: "Parasect",
    48: "Venonat", 49: "Venomoth",
    50: "Diglett", 51: "Dugtrio",
    52: "Meowth", 53: "Persian",
    54: "Psyduck", 55: "Golduck",
    56: "Mankey", 57: "Primeape",
    58: "Growlithe", 59: "Arcanine",
    60: "Poliwag", 61: "Poliwhirl", 62: "Poliwrath",
    63: "Abra", 64: "Kadabra", 65: "Alakazam",
    66: "Machop", 67: "Machoke", 68: "Machamp",
    69: "Bellsprout", 70: "Weepinbell", 71: "Victreebel",
    72: "Tentacool", 73: "Tentacruel",
    74: "Geodude", 75: "Graveler", 76: "Golem",
    77: "Ponyta", 78: "Rapidash",
    79: "Slowpoke", 80: "Slowbro",
    81: "Magnemite", 82: "Magneton",
    83: "Farfetch'd", 84: "Doduo", 85: "Dodrio",
    86: "Seel", 87: "Dewgong",
    88: "Grimer", 89: "Muk",
    90: "Shellder", 91: "Cloyster",
    92: "Gastly", 93: "Haunter", 94: "Gengar",
    95: "Onix",
    96: "Drowzee", 97: "Hypno",
    98: "Krabby", 99: "Kingler",
    100: "Voltorb", 101: "Electrode",
    102: "Exeggcute", 103: "Exeggutor",
    104: "Cubone", 105: "Marowak",
    106: "Hitmonlee", 107: "Hitmonchan",
    108: "Lickitung",
    109: "Koffing", 110: "Weezing",
    111: "Rhyhorn", 112: "Rhydon",
    113: "Chansey",
    114: "Tangela",
    115: "Kangaskhan",
    116: "Horsea", 117: "Seadra",
    118: "Goldeen", 119: "Seaking",
    120: "Staryu", 121: "Starmie",
    122: "Mr. Mime",
    123: "Scyther",
    124: "Jynx",
    125: "Electabuzz",
    126: "Magmar",
    127: "Pinsir",
    128: "Tauros",
    129: "Magikarp", 130: "Gyarados",
    131: "Lapras",
    132: "Ditto",
    133: "Eevee", 134: "Vaporeon", 135: "Jolteon", 136: "Flareon",
    137: "Porygon",
    138: "Omanyte", 139: "Omastar",
    140: "Kabuto", 141: "Kabutops",
    142: "Aerodactyl",
    143: "Snorlax",
    144: "Articuno", 145: "Zapdos", 146: "Moltres",
    147: "Dratini", 148: "Dragonair", 149: "Dragonite",
    150: "Mewtwo", 151: "Mew",
}


# ==========================================================================
# FIRE RED (US v1.0) MEMORY ADDRESSES
# ==========================================================================
# These addresses are specific to Pokemon Fire Red BPRE (USA, v1.0).
# Other versions or languages will have different addresses.

# Save block pointers live in IWRAM. The game stores pointers to two main
# save data structures that contain most of the player's state:
SAVEBLOCK1_PTR = 0x03005008  # → SaveBlock1 (position, flags, bag, money)
SAVEBLOCK2_PTR = 0x0300500C  # → SaveBlock2 (player name, trainer ID, options)

# Party data is stored directly in EWRAM at fixed addresses:
PARTY_COUNT_ADDR = 0x02024029  # Number of Pokemon in party (0-6)
PARTY_DATA_ADDR = 0x02024284   # Start of party Pokemon array

# Pokemon struct constants
PARTY_MON_SIZE = 100  # Each party Pokemon occupies exactly 100 bytes
PARTY_MAX = 6         # Maximum party size

# ---------------------------------------------------------------------------
# Battle-related addresses (EWRAM + IWRAM)
# ---------------------------------------------------------------------------
# gBattleTypeFlags: 4-byte flags word, non-zero when a battle is active.
# Bit 0 = double, bit 1 = link, bit 3 = trainer, bit 8 = wild.
BATTLE_TYPE_FLAGS_ADDR = 0x02022B4C

# gBattleOutcome: 1 byte set at end of battle.
# 0=unresolved, 1=won, 2=lost, 3=ran, 4=caught, 5=draw, 6=opponent ran.
BATTLE_OUTCOME_ADDR = 0x02023E8A

# gBattleMons: array of 4 BattlePokemon structs (88 bytes each).
# [0]=player slot 0, [1]=opponent slot 0, [2]=player slot 1, [3]=opponent slot 1
BATTLE_MONS_ADDR = 0x02023BE4
BATTLE_MON_SIZE = 88  # sizeof(struct BattlePokemon)

# gBattlersCount: 1 byte — 2 for singles, 4 for doubles
BATTLERS_COUNT_ADDR = 0x02023BCC

# gActiveBattler: 1 byte — index (0-3) of currently processing battler
ACTIVE_BATTLER_ADDR = 0x02023BC4

# Enemy party data (same 100-byte Gen 3 format, 6 slots)
ENEMY_PARTY_ADDR = 0x0202402C

# gMain.callback2: pointer to the active game-loop callback.
# During battle this points to BattleMainCB2 (0x08011101 in Thumb).
GMAIN_CALLBACK2_ADDR = 0x030030F4

# ---------------------------------------------------------------------------
# Start menu addresses (EWRAM)
# ---------------------------------------------------------------------------
# sStartMenuCursorPos: 1 byte, index into the displayed menu list.
# sStartMenuOrder: 9-byte array mapping cursor index → StartMenuOption enum.
# To get the actual selected item: sStartMenuOrder[sStartMenuCursorPos].
START_MENU_CURSOR_POS_ADDR = 0x020370F4
START_MENU_NUM_ITEMS_ADDR = 0x020370F5
START_MENU_ORDER_ADDR = 0x020370F6  # 9 bytes

# StartMenuOption enum values (from pret/pokefirered src/start_menu.c)
START_MENU_OPTIONS = {
    0: "POKEDEX",
    1: "POKEMON",
    2: "BAG",
    3: "PLAYER",     # Trainer card
    4: "SAVE",
    5: "OPTION",
    6: "EXIT",
    7: "RETIRE",     # Safari Zone only
    8: "PLAYER2",    # Link mode variant
}


# ==========================================================================
# STRING DECODING
# ==========================================================================

def decode_gen3_string(data: bytes, max_len: int | None = None) -> str:
    """Decode a Gen 3 encoded byte string into a Python string.

    Args:
        data: Raw bytes from GBA memory.
        max_len: Optional maximum number of bytes to process.

    Returns:
        Decoded string. Unknown bytes become '?'. Stops at 0xFF terminator.
    """
    result = []
    for i, b in enumerate(data):
        if max_len and i >= max_len:
            break
        if b == 0xFF:  # string terminator
            break
        result.append(GEN3_CHARSET.get(b, "?"))
    return "".join(result)


# ==========================================================================
# POKEMON DATA DECRYPTION
# ==========================================================================
# Gen 3 Pokemon data uses a simple encryption scheme to deter casual memory
# editing. The 48 bytes of substructure data (offsets 32-79) are XOR'd with
# a key, and the four 12-byte substructures are shuffled based on PID % 24.

def _decrypt_substructures(data: bytes, pid: int, ot_id: int) -> dict[str, bytes]:
    """Decrypt and re-order the four Pokemon data substructures.

    The encryption key is PID XOR OTID. Each 32-bit word in the 48-byte
    encrypted region is XOR'd with this key. Then the four 12-byte
    substructures are re-mapped to their canonical names (G, A, E, M)
    based on the permutation index PID % 24.

    Args:
        data: Full 100-byte party Pokemon data.
        pid: Personality Value (bytes 0-3).
        ot_id: Original Trainer ID (bytes 4-7).

    Returns:
        Dict mapping substructure letter to its decrypted 12-byte contents:
          "G" = Growth (species, held item, experience, friendship)
          "A" = Attacks (4 moves + 4 PP values)
          "E" = EVs/Condition (6 EV stats + contest conditions)
          "M" = Miscellaneous (pokerus, met location, origin info)
    """
    key = pid ^ ot_id
    encrypted = data[32:80]  # 48 bytes of encrypted substructure data

    # Decrypt: XOR each 32-bit little-endian word with the key
    decrypted = bytearray(48)
    for i in range(0, 48, 4):
        word = struct.unpack_from("<I", encrypted, i)[0]
        word ^= key
        struct.pack_into("<I", decrypted, i, word)

    # The 24 possible orderings of the four substructures.
    # Index is PID % 24. Letters: G=Growth, A=Attacks, E=EVs, M=Misc
    SUBSTRUCTURE_ORDER = [
        "GAEM", "GAME", "GEAM", "GEMA", "GMAE", "GMEA",
        "AGEM", "AGME", "AEGM", "AEMG", "AMGE", "AMEG",
        "EGAM", "EGMA", "EAGM", "EAMG", "EMGA", "EMAG",
        "MGAE", "MGEA", "MAGE", "MAEG", "MEGA", "MEAG",
    ]
    order = SUBSTRUCTURE_ORDER[pid % 24]

    # Map each position in the encrypted data to its substructure letter
    subs = {}
    for i, letter in enumerate(order):
        subs[letter] = decrypted[i * 12:(i + 1) * 12]

    return subs


# ==========================================================================
# POKEMON STRUCT PARSING
# ==========================================================================

def parse_party_pokemon(data: bytes) -> dict[str, Any] | None:
    """Parse a 100-byte party Pokemon structure into a readable dict.

    Decrypts the substructures and extracts all key fields: species, level,
    HP, stats, moves, EVs, and metadata.

    Args:
        data: Exactly 100 bytes of raw party Pokemon data.

    Returns:
        Dict with all parsed fields, or None if data is too short.
    """
    if len(data) < PARTY_MON_SIZE:
        return None

    # -- Header (unencrypted) --
    pid = struct.unpack_from("<I", data, 0)[0]       # Personality Value
    ot_id = struct.unpack_from("<I", data, 4)[0]     # Original Trainer ID
    nickname_raw = data[8:18]                         # 10 bytes, Gen 3 encoded
    nickname = decode_gen3_string(nickname_raw)

    # -- Decrypt and reorder the four substructures --
    subs = _decrypt_substructures(data, pid, ot_id)

    # Growth substructure (12 bytes): species, held item, EXP, friendship
    growth = subs["G"]
    species = struct.unpack_from("<H", growth, 0)[0]
    held_item = struct.unpack_from("<H", growth, 2)[0]
    experience = struct.unpack_from("<I", growth, 4)[0]
    friendship = growth[9]

    # Attacks substructure (12 bytes): 4 move IDs (2 bytes each) + 4 PP (1 byte each)
    attacks = subs["A"]
    moves = []
    for i in range(4):
        move_id = struct.unpack_from("<H", attacks, i * 2)[0]
        if move_id != 0:
            moves.append({"id": move_id})
    pp = [attacks[8 + i] for i in range(4)]
    for i, m in enumerate(moves):
        m["pp"] = pp[i]

    # EVs/Condition substructure (12 bytes): 6 EV stats + contest conditions
    evs_data = subs["E"]
    evs = {
        "hp": evs_data[0], "attack": evs_data[1], "defense": evs_data[2],
        "speed": evs_data[3], "sp_attack": evs_data[4], "sp_defense": evs_data[5],
    }

    # Misc substructure (12 bytes): pokerus, met location, etc.
    misc = subs["M"]
    pokerus = misc[0]
    met_location = misc[1]

    # -- Battle stats (bytes 80-99) --
    # These are only calculated for party members (not PC-boxed Pokemon).
    status = struct.unpack_from("<I", data, 80)[0]       # Status condition flags
    level = data[84]                                      # Current level
    current_hp = struct.unpack_from("<H", data, 86)[0]   # Current HP
    max_hp = struct.unpack_from("<H", data, 88)[0]       # Max HP
    attack_stat = struct.unpack_from("<H", data, 90)[0]  # Attack
    defense_stat = struct.unpack_from("<H", data, 92)[0] # Defense
    speed_stat = struct.unpack_from("<H", data, 94)[0]   # Speed
    sp_atk_stat = struct.unpack_from("<H", data, 96)[0]  # Sp. Attack
    sp_def_stat = struct.unpack_from("<H", data, 98)[0]  # Sp. Defense

    species_name = SPECIES_NAMES.get(species, f"Pokemon #{species}")

    return {
        "species_id": species,
        "species_name": species_name,
        "nickname": nickname,
        "level": level,
        "hp": current_hp,
        "max_hp": max_hp,
        "attack": attack_stat,
        "defense": defense_stat,
        "speed": speed_stat,
        "sp_attack": sp_atk_stat,
        "sp_defense": sp_def_stat,
        "experience": experience,
        "held_item": held_item,
        "moves": moves,
        "evs": evs,
        "status": status,
        "friendship": friendship,
        "pid": pid,
        "ot_id": ot_id,
    }


# ==========================================================================
# HIGH-LEVEL GAME STATE READER
# ==========================================================================

class FireRedReader:
    """Reads Pokemon Fire Red game state by combining MGBAClient memory
    access with knowledge of the Fire Red memory layout.

    All methods issue raw memory reads via the client and return parsed
    Python data structures. The client must be connected before calling
    any read method.
    """

    def __init__(self, client: MGBAClient):
        self.client = client

    # -- Party --

    def read_party_count(self) -> int:
        """Read how many Pokemon are in the player's party (0-6)."""
        return self.client.read8(PARTY_COUNT_ADDR)

    def read_party(self) -> list[dict[str, Any]]:
        """Read all Pokemon in the player's party with full details.

        Returns a list of dicts, one per party member, containing species,
        level, HP, stats, moves, EVs, and more. Empty party returns [].
        """
        count = self.read_party_count()
        if count == 0 or count > PARTY_MAX:
            return []

        party = []
        for i in range(count):
            addr = PARTY_DATA_ADDR + i * PARTY_MON_SIZE
            data = self.client.read_range(addr, PARTY_MON_SIZE)
            mon = parse_party_pokemon(data)
            if mon:
                party.append(mon)
        return party

    # -- Player position --

    def read_player_position(self) -> dict[str, int]:
        """Read the player's current position from SaveBlock1.

        Returns dict with x, y coordinates and map_group/map_num identifiers.
        Map group + map number together identify which map the player is on.
        """
        sb1 = self.client.read32(SAVEBLOCK1_PTR)
        x = self.client.read16(sb1 + 0x00)
        y = self.client.read16(sb1 + 0x02)
        map_group = self.client.read8(sb1 + 0x04)
        map_num = self.client.read8(sb1 + 0x05)
        return {
            "x": x,
            "y": y,
            "map_group": map_group,
            "map_num": map_num,
        }

    # -- Player identity --

    def read_player_name(self) -> str:
        """Read the player's trainer name from SaveBlock2."""
        sb2 = self.client.read32(SAVEBLOCK2_PTR)
        name_data = self.client.read_range(sb2, 8)  # name is max 7 chars + terminator
        return decode_gen3_string(name_data)

    def read_trainer_id(self) -> dict[str, int]:
        """Read the player's public and secret trainer IDs from SaveBlock2."""
        sb2 = self.client.read32(SAVEBLOCK2_PTR)
        trainer_id_full = self.client.read32(sb2 + 0x0A)
        public_id = trainer_id_full & 0xFFFF
        secret_id = (trainer_id_full >> 16) & 0xFFFF
        return {"public_id": public_id, "secret_id": secret_id}

    # -- Money --

    def read_money(self) -> int:
        """Read the player's money from SaveBlock1.

        Money in Fire Red is stored XOR'd with a security key to prevent
        simple memory editing. We read both the encrypted value and the
        key, then XOR them to get the real amount.
        """
        sb1 = self.client.read32(SAVEBLOCK1_PTR)
        money_raw = self.client.read32(sb1 + 0x0290)  # encrypted money
        money_key = self.client.read32(sb1 + 0x0294)  # XOR key
        return money_raw ^ money_key

    # -- Badges --

    def read_badges(self) -> list[str]:
        """Read which gym badges the player has earned.

        Badges are stored as individual flag bits in the game's flags array.
        Fire Red badge flags start at flag 0x820 (8 badges total).
        """
        sb1 = self.client.read32(SAVEBLOCK1_PTR)
        # The flags array starts at offset 0x0EE0 in SaveBlock1
        flags_base = sb1 + 0x0EE0
        badge_flag_start = 0x820
        byte_offset = badge_flag_start // 8
        bit_offset = badge_flag_start % 8

        # Read two bytes to cover all 8 badge bits (they may span a byte boundary)
        badge_byte = self.client.read8(flags_base + byte_offset)
        badge_byte2 = self.client.read8(flags_base + byte_offset + 1)
        badge_bits = (badge_byte >> bit_offset) | ((badge_byte2 << (8 - bit_offset)) & 0xFF)

        badge_names = [
            "Boulder", "Cascade", "Thunder", "Rainbow",
            "Soul", "Marsh", "Volcano", "Earth",
        ]
        earned = []
        for i, name in enumerate(badge_names):
            if badge_bits & (1 << i):
                earned.append(name)
        return earned

    # -- Bag / Inventory --

    def read_bag_pocket(self, pocket_addr: int, capacity: int) -> list[dict[str, int]]:
        """Read items from a single bag pocket.

        Each item slot is 4 bytes: 2-byte item ID + 2-byte quantity.
        Empty slots have item ID 0 and are skipped.
        """
        items = []
        for i in range(capacity):
            item_id = self.client.read16(pocket_addr + i * 4)
            quantity = self.client.read16(pocket_addr + i * 4 + 2)
            if item_id != 0:
                items.append({"id": item_id, "quantity": quantity})
        return items

    def read_bag(self) -> dict[str, list[dict[str, int]]]:
        """Read the contents of all five bag pockets.

        Fire Red bag layout (at offset 0x0310 in SaveBlock1):
          - Items:     42 slots (general consumables, held items)
          - Key Items: 30 slots (quest items, bike, etc.)
          - Pokeballs: 16 slots (all ball types)
          - TMs/HMs:   64 slots (technical/hidden machines)
          - Berries:   46 slots (berry items)
        """
        sb1 = self.client.read32(SAVEBLOCK1_PTR)
        bag_offset = 0x0310  # start of bag data in SaveBlock1

        pockets = {}
        pocket_info = [
            ("items", 0, 42),
            ("key_items", 42 * 4, 30),
            ("pokeballs", (42 + 30) * 4, 16),
            ("tms_hms", (42 + 30 + 16) * 4, 64),
            ("berries", (42 + 30 + 16 + 64) * 4, 46),
        ]
        for name, offset, capacity in pocket_info:
            pocket_addr = sb1 + bag_offset + offset
            pockets[name] = self.read_bag_pocket(pocket_addr, capacity)
        return pockets

    # -- Battle state --

    def read_battle_state(self) -> dict[str, Any]:
        """Read the current battle state from memory.

        Returns a dict with:
          - in_battle: bool — whether a battle is currently active
          - battle_type: str — "wild", "trainer", "double", "link", or "none"
          - battle_outcome: str — "unresolved", "won", "lost", "ran", etc.
          - battlers_count: int — number of active battlers (2 singles, 4 doubles)

        The primary detection is gBattleTypeFlags (0x02022B4C) — non-zero
        means a battle is in progress. The individual bits encode the type.
        """
        flags = self.client.read32(BATTLE_TYPE_FLAGS_ADDR)
        outcome_byte = self.client.read8(BATTLE_OUTCOME_ADDR)

        # Determine battle type from flags
        in_battle = flags != 0
        if not in_battle:
            battle_type = "none"
        elif flags & (1 << 0):
            battle_type = "double"
        elif flags & (1 << 1):
            battle_type = "link"
        elif flags & (1 << 3):
            battle_type = "trainer"
        elif flags & (1 << 8):
            battle_type = "wild"
        else:
            battle_type = "unknown"

        # Map outcome byte to human-readable string
        outcome_map = {
            0: "unresolved", 1: "won", 2: "lost",
            3: "ran", 4: "caught", 5: "draw", 6: "opponent_ran",
        }
        outcome = outcome_map.get(outcome_byte, f"unknown({outcome_byte})")

        battlers_count = self.client.read8(BATTLERS_COUNT_ADDR) if in_battle else 0

        return {
            "in_battle": in_battle,
            "battle_type": battle_type,
            "battle_type_flags": flags,
            "battle_outcome": outcome,
            "battlers_count": battlers_count,
        }

    def read_battle_pokemon(self, battler_index: int) -> dict[str, Any] | None:
        """Read a BattlePokemon struct from the gBattleMons array.

        The in-battle struct is 88 bytes with a different layout from the
        100-byte party struct. It contains live battle stats (including
        stat stages, status, and current HP) but is NOT encrypted.

        Args:
            battler_index: 0=player slot 0, 1=opponent slot 0,
                          2=player slot 1 (doubles), 3=opponent slot 1.

        Returns:
            Dict with species, level, HP, stats, moves, and status.
            None if the read fails or data is empty.
        """
        addr = BATTLE_MONS_ADDR + battler_index * BATTLE_MON_SIZE
        data = self.client.read_range(addr, BATTLE_MON_SIZE)

        if len(data) < BATTLE_MON_SIZE:
            return None

        # BattlePokemon struct layout (from pret/pokefirered include/pokemon.h):
        # Offsets are from the struct's pokefirered decomp:
        #   u16 species          @ 0x00
        #   u16 attack           @ 0x02
        #   u16 defense          @ 0x04
        #   u16 speed            @ 0x06
        #   u16 spAttack         @ 0x08
        #   u16 spDefense        @ 0x0A
        #   u16 moves[4]         @ 0x0C-0x13
        #   u32 pp[4] (packed)   @ 0x14-0x17 (1 byte each)
        #   ...
        #   u16 hp               @ 0x28
        #   u8  level            @ 0x2A
        #   ...
        #   u16 maxHP            @ 0x2C
        #   ...
        #   u32 status1          @ 0x4C  (primary status: burn, poison, etc.)
        #   u32 status2          @ 0x50  (volatile: confused, flinch, etc.)

        species = struct.unpack_from("<H", data, 0x00)[0]
        attack = struct.unpack_from("<H", data, 0x02)[0]
        defense = struct.unpack_from("<H", data, 0x04)[0]
        speed = struct.unpack_from("<H", data, 0x06)[0]
        sp_attack = struct.unpack_from("<H", data, 0x08)[0]
        sp_defense = struct.unpack_from("<H", data, 0x0A)[0]

        # 4 move IDs (2 bytes each)
        moves = []
        for i in range(4):
            move_id = struct.unpack_from("<H", data, 0x0C + i * 2)[0]
            if move_id != 0:
                moves.append({"id": move_id, "pp": data[0x14 + i]})

        hp = struct.unpack_from("<H", data, 0x28)[0]
        level = data[0x2A]
        max_hp = struct.unpack_from("<H", data, 0x2C)[0]

        status1 = struct.unpack_from("<I", data, 0x4C)[0]
        status2 = struct.unpack_from("<I", data, 0x50)[0]

        species_name = SPECIES_NAMES.get(species, f"Pokemon #{species}")

        return {
            "species_id": species,
            "species_name": species_name,
            "level": level,
            "hp": hp,
            "max_hp": max_hp,
            "attack": attack,
            "defense": defense,
            "speed": speed,
            "sp_attack": sp_attack,
            "sp_defense": sp_defense,
            "moves": moves,
            "status1": status1,
            "status2": status2,
        }

    def read_opponent_party(self) -> list[dict[str, Any]]:
        """Read the enemy trainer's full party during a battle.

        Uses the enemy party data area (same 100-byte encrypted format as
        the player's party). Only meaningful during trainer battles.

        Returns:
            List of parsed Pokemon dicts (same format as read_party).
        """
        # Enemy party count is at ENEMY_PARTY_ADDR - 3 (mirroring player layout)
        # But we can also just read all 6 slots and skip empty ones
        party = []
        for i in range(PARTY_MAX):
            addr = ENEMY_PARTY_ADDR + i * PARTY_MON_SIZE
            data = self.client.read_range(addr, PARTY_MON_SIZE)
            mon = parse_party_pokemon(data)
            if mon and mon["species_id"] != 0:
                party.append(mon)
        return party

    # -- Start menu --

    def read_start_menu_state(self) -> dict[str, Any]:
        """Read the current START menu cursor position and displayed items.

        The start menu uses two-level indirection:
          - sStartMenuCursorPos is the cursor index into the display list
          - sStartMenuOrder maps display positions to StartMenuOption enum values

        Returns:
            Dict with cursor_pos, num_items, menu_order (list of option names),
            and selected_item (the option name the cursor is currently on).
        """
        cursor_pos = self.client.read8(START_MENU_CURSOR_POS_ADDR)
        num_items = self.client.read8(START_MENU_NUM_ITEMS_ADDR)

        # Read the order array (up to 9 bytes, but only num_items are valid)
        order_data = self.client.read_range(START_MENU_ORDER_ADDR, 9)

        # Build the display list of option names
        menu_order = []
        for i in range(min(num_items, 9)):
            option_id = order_data[i]
            menu_order.append(START_MENU_OPTIONS.get(option_id, f"unknown({option_id})"))

        # What option is the cursor currently on?
        selected_item = "unknown"
        if cursor_pos < len(menu_order):
            selected_item = menu_order[cursor_pos]

        return {
            "cursor_pos": cursor_pos,
            "num_items": num_items,
            "menu_order": menu_order,
            "selected_item": selected_item,
        }

    # -- Combined snapshot --

    def get_game_state(self) -> dict[str, Any]:
        """Get a summary snapshot of the current game state.

        Returns player name, position, badges, money, and a condensed
        party summary (species + level + HP). Useful for quick status checks.
        """
        party = self.read_party()
        party_summary = []
        for mon in party:
            party_summary.append({
                "species": mon["species_name"],
                "level": mon["level"],
                "hp": f"{mon['hp']}/{mon['max_hp']}",
            })

        return {
            "player_name": self.read_player_name(),
            "position": self.read_player_position(),
            "badges": self.read_badges(),
            "money": self.read_money(),
            "party_count": len(party),
            "party": party_summary,
        }
