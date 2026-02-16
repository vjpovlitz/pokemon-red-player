# Pokemon Red Clone

A faithful recreation of Pokemon Red using Python and Pygame, featuring Gen 1 battle mechanics, grid-based movement, and the classic Game Boy aesthetic.

## Features

- **Authentic Gen 1 Mechanics**: Damage formulas, type chart, stat calculations, and catch rates match the original
- **Stack-Based State System**: Seamless transitions between overworld, battles, menus, and dialogue
- **Grid-Based Movement**: 16x16 pixel tiles with smooth 8-frame movement animation
- **Full Battle System**: Turn-based combat with moves, type effectiveness, PP tracking, and AI
- **Wild Encounters**: Random Pokemon encounters in tall grass
- **Trainer Battles**: Line-of-sight detection and trainer AI
- **Save System**: JSON-based save/load functionality

## Requirements

- Python 3.10+
- Pygame 2.5+

## Installation

```bash
# Clone or download the project
cd C:\Users\vjpov\Codebase\Poke

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## Controls

| Action | Keys |
|--------|------|
| Move | Arrow Keys / WASD |
| Confirm / Interact | Z / Enter |
| Cancel / Run | X / Backspace |
| Open Menu | Escape |
| Select (Secondary) | Shift |

## Project Structure

```
Poke/
├── main.py                 # Entry point
├── config.py               # Game constants and settings
├── requirements.txt        # Python dependencies
│
├── src/
│   ├── game.py             # Main Game class, orchestrates systems
│   │
│   ├── core/               # Engine systems
│   │   ├── state_manager.py    # Stack-based state machine
│   │   ├── input_handler.py    # Keyboard input mapping
│   │   ├── camera.py           # Viewport/scrolling
│   │   └── animation.py        # Sprite animation
│   │
│   ├── states/             # Game states
│   │   ├── title_state.py      # Title screen
│   │   ├── overworld_state.py  # Main exploration
│   │   ├── battle_state.py     # Pokemon battles
│   │   └── menu_state.py       # Pause menu
│   │
│   ├── entities/           # Game entities
│   │   ├── player.py           # Player character
│   │   ├── npc.py              # NPC base class
│   │   └── trainer.py          # Trainer NPCs
│   │
│   ├── world/              # Map systems
│   │   ├── tilemap.py          # Tile rendering/collision
│   │   ├── map_manager.py      # Map loading/switching
│   │   └── encounter_zones.py  # Wild encounters
│   │
│   ├── battle/             # Battle system
│   │   ├── battle_manager.py   # Battle coordination
│   │   ├── damage_calc.py      # Gen 1 damage formula
│   │   ├── type_chart.py       # Type effectiveness
│   │   └── battle_ai.py        # Enemy AI
│   │
│   ├── pokemon/            # Pokemon systems
│   │   ├── pokemon.py          # Pokemon class
│   │   ├── stats.py            # Stat calculations
│   │   └── party.py            # Party management
│   │
│   ├── ui/                 # User interface
│   │   ├── text_box.py         # Dialogue rendering
│   │   ├── menu.py             # Menu system
│   │   └── health_bar.py       # HP/EXP bars
│   │
│   └── systems/            # Game systems
│       ├── inventory.py        # Items/bag
│       ├── dialogue.py         # Dialogue trees
│       └── save_system.py      # Save/load
│
├── data/                   # Game data (JSON)
│   ├── pokemon.json            # Pokemon stats
│   ├── moves.json              # Move definitions
│   ├── items.json              # Item definitions
│   ├── type_chart.json         # Type effectiveness
│   ├── wild_encounters.json    # Encounter tables
│   └── trainers.json           # Trainer data
│
├── assets/
│   ├── maps/               # Map JSON files
│   ├── sprites/            # Character/Pokemon sprites
│   ├── tilesets/           # Map tiles
│   └── ui/                 # UI graphics
│
└── saves/                  # Save files
```

## Architecture

### State Machine

The game uses a stack-based state machine allowing states to overlay each other:

```
[OverworldState] <- Base exploration
    └── [MenuState] <- Pause menu overlay
        └── [BattleState] <- Battle takes over
```

States implement these methods:
- `enter(params)` - Initialize when becoming active
- `exit()` - Cleanup when removed
- `pause()` / `resume()` - Handle being covered/uncovered
- `handle_event(event)` - Process input
- `update(dt)` - Game logic
- `render(surface)` - Drawing

### Pokemon System

Pokemon use Gen 1 formulas:

**Stat Calculation:**
```
Stat = ((Base + IV) * 2 + sqrt(EV) / 4) * Level / 100 + 5
HP = ((Base + IV) * 2 + sqrt(EV) / 4) * Level / 100 + Level + 10
```

**Damage Formula:**
```
Damage = ((2*Level/5+2) * Power * Attack/Defense / 50 + 2) * Modifiers
Modifiers = STAB(1.5) * TypeEffectiveness * Random(0.85-1.0) * Critical(2.0)
```

### Map System

Maps are JSON files compatible with Tiled editor exports:
- Multiple tile layers
- Collision layer (0 = walkable, 1 = solid)
- Warp definitions for map transitions
- NPC placements
- Encounter zone data

## Configuration

Edit `config.py` to adjust:

```python
# Display
NATIVE_WIDTH = 160      # Game Boy resolution
NATIVE_HEIGHT = 144
SCALE = 3               # Window scaling

# Gameplay
TILE_SIZE = 16
MOVEMENT_FRAMES = 8     # Frames to cross one tile
FPS = 60
```

## Adding Content

### New Pokemon

Add to `data/pokemon.json`:
```json
"POKEMON_NAME": {
  "id": 999,
  "types": ["type1", "type2"],
  "base_stats": {
    "hp": 50, "attack": 50, "defense": 50,
    "speed": 50, "special": 50
  },
  "exp_yield": 100,
  "catch_rate": 45,
  "learnset": { "1": ["tackle"] },
  "evolution": { "into": "EVOLVED_FORM", "level": 16 }
}
```

Also add to `src/pokemon/pokemon.py` BASE_STATS dict.

### New Maps

Create `assets/maps/map_name.json`:
```json
{
  "name": "Map Name",
  "width": 20,
  "height": 18,
  "tileset": "overworld",
  "layers": [[[0, 0, ...]]],
  "collision": [[0, 1, ...]],
  "warps": [{"x": 5, "y": 0, "target_map": "other_map", "target_x": 5, "target_y": 17}],
  "npcs": [{"name": "NPC", "x": 5, "y": 5, "dialogue": ["Hello!"]}],
  "encounters": [{"pokemon": "RATTATA", "level_min": 2, "level_max": 5, "rate": 50}]
}
```

### New Trainers

Add to `data/trainers.json`:
```json
"trainer_id": {
  "name": "JOEY",
  "class": "Youngster",
  "dialogue": ["Pre-battle text"],
  "defeat_dialogue": ["After defeat text"],
  "team": [{"species": "RATTATA", "level": 5}],
  "prize_money": 100,
  "sight_range": 4
}
```

## Extracting Original Assets

The game includes placeholder graphics. For authentic sprites:

1. Clone the PRET pokered disassembly:
   ```bash
   git clone https://github.com/pret/pokered
   ```

2. Copy sprites from `pokered/gfx/`:
   - Pokemon sprites: `gfx/pokemon/`
   - Overworld sprites: `gfx/overworld/`
   - Tilesets: `gfx/tilesets/`

3. Place in corresponding `assets/` directories

## License

This is a fan project for educational purposes. Pokemon is a trademark of Nintendo/Game Freak/The Pokemon Company.
