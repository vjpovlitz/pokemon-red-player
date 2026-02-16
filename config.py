# Game constants and settings

# Display settings
NATIVE_WIDTH = 160
NATIVE_HEIGHT = 144
SCALE = 3
WINDOW_WIDTH = NATIVE_WIDTH * SCALE
WINDOW_HEIGHT = NATIVE_HEIGHT * SCALE
FPS = 60
TICK_RATE = 1 / FPS

# Tile settings
TILE_SIZE = 16
TILES_X = NATIVE_WIDTH // TILE_SIZE  # 10 tiles wide
TILES_Y = NATIVE_HEIGHT // TILE_SIZE  # 9 tiles tall

# Movement settings
MOVEMENT_FRAMES = 8  # Frames to cross one tile
PIXELS_PER_FRAME = TILE_SIZE // MOVEMENT_FRAMES  # 2 pixels per frame

# Colors (Game Boy palette)
COLOR_WHITE = (224, 248, 208)
COLOR_LIGHT = (136, 192, 112)
COLOR_DARK = (52, 104, 86)
COLOR_BLACK = (8, 24, 32)

# Alternative colors for UI
COLOR_RED = (248, 56, 0)
COLOR_BLUE = (0, 112, 248)
COLOR_YELLOW = (248, 224, 56)

# Battle settings
MAX_PARTY_SIZE = 6
MAX_LEVEL = 100
MAX_PP = 99
CRIT_RATE = 1 / 16  # Base crit rate in Gen 1

# File paths
ASSETS_PATH = "assets"
DATA_PATH = "data"
SAVES_PATH = "saves"
SPRITES_PATH = f"{ASSETS_PATH}/sprites"
TILESETS_PATH = f"{ASSETS_PATH}/tilesets"
MAPS_PATH = f"{ASSETS_PATH}/maps"
UI_PATH = f"{ASSETS_PATH}/ui"

# Input key mapping
KEY_UP = "up"
KEY_DOWN = "down"
KEY_LEFT = "left"
KEY_RIGHT = "right"
KEY_A = "a"  # Confirm/interact
KEY_B = "b"  # Cancel/run
KEY_START = "start"  # Menu
KEY_SELECT = "select"  # Secondary menu

# Game states
STATE_TITLE = "title"
STATE_OVERWORLD = "overworld"
STATE_BATTLE = "battle"
STATE_MENU = "menu"
STATE_DIALOGUE = "dialogue"
STATE_TRANSITION = "transition"

# Type chart indices
TYPES = [
    "normal", "fire", "water", "electric", "grass",
    "ice", "fighting", "poison", "ground", "flying",
    "psychic", "bug", "rock", "ghost", "dragon"
]

# Experience groups
EXP_GROUPS = ["fast", "medium_fast", "medium_slow", "slow"]
