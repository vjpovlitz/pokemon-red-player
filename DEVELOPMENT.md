# Development Guide & Next Steps

This document outlines the current implementation status and provides detailed instructions for completing the Pokemon Red clone.

## Current Implementation Status

### Completed (Phase 1-5 Core)

| Component | Status | Notes |
|-----------|--------|-------|
| Project structure | Done | All directories and modules created |
| Game loop | Done | Fixed timestep at 60 FPS |
| State manager | Done | Stack-based with push/pop/replace |
| Input handler | Done | Configurable key mapping |
| Title screen | Done | New Game / Continue menu |
| Camera system | Done | Follows player, respects bounds |
| Tilemap rendering | Done | JSON maps with collision |
| Player movement | Done | Grid-based, 8-frame animation |
| NPC system | Done | Dialogue, wandering behavior |
| Trainer class | Done | Line-of-sight, teams, battles |
| Pokemon class | Done | Gen 1 stats, IVs, EVs, moves |
| Party system | Done | Max 6, switching |
| Battle state | Done | Full turn-based combat |
| Damage calculation | Done | Gen 1 formula with STAB, crits |
| Type chart | Done | All 15 Gen 1 types |
| Battle AI | Done | Easy/normal/hard difficulty |
| HP bars | Done | Animated transitions |
| Text boxes | Done | Typewriter effect |
| Menu system | Done | Battle and pause menus |
| Inventory | Done | Items, key items, balls |
| Save system | Done | JSON serialization |
| Sample maps | Done | Pallet Town, Route 1 |
| Pokemon data | Done | 15 species defined |

### Needs Implementation

| Component | Priority | Difficulty |
|-----------|----------|------------|
| Sprite loading | High | Easy |
| Battle transitions | High | Medium |
| Dialogue state | High | Easy |
| Party screen | High | Medium |
| Bag screen | Medium | Medium |
| Pokemon catching | High | Easy |
| Evolution | Medium | Medium |
| Pokemon Center | Medium | Easy |
| Pokemart | Medium | Medium |
| More maps | Medium | Easy |
| Sound/Music | Low | Medium |

---

## Next Steps (Detailed Instructions)

### Step 1: Add Sprite Loading

The game currently uses placeholder graphics. Add proper sprite loading:

**File: `src/core/sprite_loader.py`**
```python
import pygame
import os
from config import SPRITES_PATH

class SpriteLoader:
    _cache = {}

    @classmethod
    def load(cls, path: str) -> pygame.Surface:
        if path in cls._cache:
            return cls._cache[path]

        full_path = os.path.join(SPRITES_PATH, path)
        if os.path.exists(full_path):
            sprite = pygame.image.load(full_path).convert_alpha()
        else:
            # Return placeholder
            sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
            sprite.fill((255, 0, 255))  # Magenta for missing

        cls._cache[path] = sprite
        return sprite

    @classmethod
    def load_pokemon(cls, species: str, back: bool = False) -> pygame.Surface:
        folder = "back" if back else "front"
        return cls.load(f"pokemon/{folder}/{species.lower()}.png")
```

**Update `src/entities/player.py`:**
```python
from src.core.sprite_loader import SpriteLoader

# In __init__:
self.sprites = {
    "down": SpriteLoader.load("player/walk_down.png"),
    "up": SpriteLoader.load("player/walk_up.png"),
    "left": SpriteLoader.load("player/walk_left.png"),
    "right": SpriteLoader.load("player/walk_right.png"),
}
```

---

### Step 2: Create Dialogue State

Add a dedicated state for NPC dialogue:

**File: `src/states/dialogue_state.py`**
```python
import pygame
from src.core.state_manager import State
from src.ui.text_box import DialogueBox
from config import KEY_A, KEY_B

class DialogueState(State):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.text_box = DialogueBox()
        self.messages = []
        self.current_index = 0
        self.speaker = ""

    def enter(self, params=None):
        params = params or {}
        self.messages = params.get("messages", ["..."])
        self.speaker = params.get("speaker", "")
        self.current_index = 0
        self.text_box.set_speaker(self.speaker)
        self.text_box.set_text(self.messages[0])

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return False

        action = self.game.input.bindings.get(event.key)

        if action in [KEY_A, KEY_B]:
            if not self.text_box.is_complete():
                self.text_box.skip()
            else:
                self.current_index += 1
                if self.current_index >= len(self.messages):
                    self.state_manager.pop()
                else:
                    self.text_box.set_text(self.messages[self.current_index])
            return True

        return False

    def update(self, dt):
        self.text_box.update(dt)

    def render(self, surface):
        # Don't clear - render over current state
        self.text_box.render(surface)
```

**Register in `src/game.py`:**
```python
from src.states.dialogue_state import DialogueState
# In __init__:
self.state_manager.register("dialogue", DialogueState)
```

**Use from overworld:**
```python
# In NPC.interact():
self.state_manager.push("dialogue", {
    "speaker": self.name,
    "messages": self.dialogue
})
```

---

### Step 3: Implement Battle Transitions

Add the classic swirl transition effect:

**File: `src/states/transition_state.py`**
```python
import pygame
import math
from src.core.state_manager import State
from config import NATIVE_WIDTH, NATIVE_HEIGHT, COLOR_BLACK

class BattleTransitionState(State):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.timer = 0
        self.duration = 1.0
        self.next_state = "battle"
        self.next_params = {}
        self.captured_surface = None

    def enter(self, params=None):
        params = params or {}
        self.next_state = params.get("next_state", "battle")
        self.next_params = params.get("next_params", {})
        self.timer = 0

        # Capture current screen
        self.captured_surface = self.game.native_surface.copy()

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.state_manager.replace(self.next_state, self.next_params)

    def render(self, surface):
        progress = self.timer / self.duration

        # Draw captured screen
        surface.blit(self.captured_surface, (0, 0))

        # Draw expanding black rectangles (spiral effect)
        num_rects = 8
        for i in range(num_rects):
            angle = (i / num_rects) * math.pi * 2 + progress * math.pi
            size = progress * max(NATIVE_WIDTH, NATIVE_HEIGHT)
            x = NATIVE_WIDTH // 2 + math.cos(angle) * size * 0.3
            y = NATIVE_HEIGHT // 2 + math.sin(angle) * size * 0.3
            rect_size = size * 0.4
            pygame.draw.rect(surface, COLOR_BLACK,
                (x - rect_size//2, y - rect_size//2, rect_size, rect_size))
```

---

### Step 4: Add Party Screen

**File: `src/states/party_state.py`**
```python
import pygame
from src.core.state_manager import State
from src.ui.health_bar import HealthBar
from config import (
    NATIVE_WIDTH, NATIVE_HEIGHT, COLOR_WHITE, COLOR_BLACK,
    KEY_UP, KEY_DOWN, KEY_A, KEY_B
)

class PartyState(State):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.cursor = 0
        self.font = pygame.font.Font(None, 16)
        self.mode = "view"  # "view", "select", "switch"
        self.switch_from = -1

    def enter(self, params=None):
        params = params or {}
        self.mode = params.get("mode", "view")
        self.cursor = 0
        self.switch_from = -1

    @property
    def party(self):
        return self.game.player_data.get("party", [])

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return False

        action = self.game.input.bindings.get(event.key)

        if action == KEY_UP:
            self.cursor = max(0, self.cursor - 1)
            return True
        elif action == KEY_DOWN:
            self.cursor = min(len(self.party) - 1, self.cursor + 1)
            return True
        elif action == KEY_A:
            self._select_pokemon()
            return True
        elif action == KEY_B:
            if self.mode == "switch" and self.switch_from >= 0:
                self.mode = "view"
                self.switch_from = -1
            else:
                self.state_manager.pop()
            return True

        return False

    def _select_pokemon(self):
        if not self.party:
            return

        if self.mode == "select":
            # Return selected Pokemon for battle switch
            self.state_manager.pop()
            # TODO: Signal selected Pokemon
        elif self.mode == "switch":
            if self.switch_from >= 0:
                # Perform switch
                party = self.party
                party[self.switch_from], party[self.cursor] = \
                    party[self.cursor], party[self.switch_from]
                self.mode = "view"
                self.switch_from = -1
            else:
                self.switch_from = self.cursor
        else:
            # Show Pokemon submenu
            self.mode = "switch"
            self.switch_from = self.cursor

    def render(self, surface):
        surface.fill(COLOR_WHITE)

        if not self.party:
            text = self.font.render("No Pokemon!", True, COLOR_BLACK)
            surface.blit(text, (8, 8))
            return

        for i, pokemon in enumerate(self.party):
            y = 8 + i * 22

            # Selection indicator
            if i == self.cursor:
                pygame.draw.rect(surface, (200, 200, 255), (0, y - 2, NATIVE_WIDTH, 22))
            if i == self.switch_from:
                pygame.draw.rect(surface, (255, 200, 200), (0, y - 2, NATIVE_WIDTH, 22))

            # Pokemon info
            name_text = self.font.render(f"{pokemon.name}", True, COLOR_BLACK)
            surface.blit(name_text, (24, y))

            level_text = self.font.render(f"Lv{pokemon.level}", True, COLOR_BLACK)
            surface.blit(level_text, (100, y))

            # HP bar
            hp_bar = HealthBar(pokemon.current_hp, pokemon.max_hp)
            hp_bar.render(surface, 24, y + 12, 48, 4)

            hp_text = self.font.render(f"{pokemon.current_hp}/{pokemon.max_hp}", True, COLOR_BLACK)
            surface.blit(hp_text, (76, y + 10))

        # Instructions
        if self.mode == "switch":
            inst = "Select Pokemon to switch"
        else:
            inst = "A: Select  B: Back"
        inst_text = self.font.render(inst, True, COLOR_BLACK)
        surface.blit(inst_text, (8, NATIVE_HEIGHT - 14))
```

---

### Step 5: Implement Pokemon Catching

Update `src/battle/battle_manager.py` `try_catch` method to integrate with battle flow:

**In `src/states/battle_state.py`, add bag handling:**
```python
def _handle_bag_select(self, action: str) -> bool:
    # When Pokeball is selected:
    if selected_item in ["pokeball", "greatball", "ultraball"]:
        success, message = self.battle_manager.try_catch(selected_item)
        self.message_queue.append(message)

        if success:
            # Add Pokemon to party or PC
            caught = self.battle_manager.enemy_pokemon
            if len(self.game.player_data["party"]) < 6:
                self.game.player_data["party"].append(caught)
                self.message_queue.append(f"{caught.name} was added to your party!")
            else:
                self.game.player_data["pc_pokemon"].append(caught)
                self.message_queue.append(f"{caught.name} was sent to the PC!")

            # Update Pokedex
            self.game.player_data["pokedex"]["caught"].add(caught.species)

            self.phase = self.PHASE_VICTORY

        # Remove Pokeball from inventory
        self.game.player_data["bag"]["pokeballs"][selected_item] -= 1

        self._next_message()
        return True
```

---

### Step 6: Add Pokemon Center Healing

**File: `src/states/pokecenter_state.py`**
```python
import pygame
from src.core.state_manager import State
from config import COLOR_WHITE, COLOR_BLACK, KEY_A

class PokeCenterState(State):
    """Handles Pokemon Center healing sequence."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.phase = "greeting"
        self.timer = 0
        self.font = pygame.font.Font(None, 16)

    def enter(self, params=None):
        self.phase = "greeting"
        self.timer = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            action = self.game.input.bindings.get(event.key)
            if action == KEY_A:
                if self.phase == "greeting":
                    self.phase = "healing"
                    self.timer = 0
                elif self.phase == "done":
                    self.state_manager.pop()
                return True
        return False

    def update(self, dt):
        if self.phase == "healing":
            self.timer += dt
            if self.timer >= 2.0:  # Healing animation duration
                # Heal all Pokemon
                for pokemon in self.game.player_data.get("party", []):
                    if hasattr(pokemon, 'full_heal'):
                        pokemon.full_heal()
                self.phase = "done"

    def render(self, surface):
        surface.fill(COLOR_WHITE)

        if self.phase == "greeting":
            lines = [
                "Welcome to the Pokemon Center!",
                "We heal your Pokemon to full health.",
                "Shall we heal your Pokemon?"
            ]
        elif self.phase == "healing":
            lines = ["Healing your Pokemon...", "", "Please wait."]
        else:
            lines = [
                "Your Pokemon are fully healed!",
                "We hope to see you again!"
            ]

        for i, line in enumerate(lines):
            text = self.font.render(line, True, COLOR_BLACK)
            surface.blit(text, (8, 40 + i * 16))
```

---

### Step 7: Create Additional Maps

Create these maps following the `pallet_town.json` format:

1. **`assets/maps/player_house.json`** - Interior of player's home
2. **`assets/maps/oak_lab.json`** - Professor Oak's laboratory
3. **`assets/maps/viridian_city.json`** - Second town
4. **`assets/maps/route_2.json`** - Route to Viridian Forest
5. **`assets/maps/viridian_forest.json`** - Forest dungeon
6. **`assets/maps/pewter_city.json`** - City with first gym
7. **`assets/maps/pewter_gym.json`** - Brock's gym interior

**Map Template:**
```json
{
  "name": "Location Name",
  "width": 20,
  "height": 18,
  "tileset": "overworld",
  "layers": [
    [[tile_ids...]]
  ],
  "collision": [[0_or_1...]],
  "warps": [
    {"x": 5, "y": 0, "target_map": "other_map", "target_x": 5, "target_y": 17}
  ],
  "npcs": [
    {"name": "NPC Name", "x": 5, "y": 5, "facing": "down", "dialogue": ["Hello!"]}
  ],
  "encounters": []
}
```

**Tile IDs (placeholder tileset):**
- 0 = Grass (walkable)
- 1 = Path (walkable)
- 2 = Water (blocked)
- 3 = Wall (blocked)
- 4 = Floor (walkable, indoor)
- 5 = Tree (blocked)
- 6 = Tall grass (walkable, encounters)
- 7 = Ledge (blocked)

---

### Step 8: Add Starter Selection

Create a special event for choosing your starter Pokemon:

**File: `src/events/starter_selection.py`**
```python
from src.pokemon.pokemon import Pokemon

STARTERS = ["BULBASAUR", "CHARMANDER", "SQUIRTLE"]

def create_starter_dialogue(game, choice_callback):
    """Create dialogue tree for starter selection."""
    return {
        "messages": [
            "Hello there! Welcome to the world of POKEMON!",
            "My name is OAK! People call me the POKEMON PROF!",
            "This world is inhabited by creatures called POKEMON!",
            "Now, choose your partner!"
        ],
        "choices": STARTERS,
        "on_choice": choice_callback
    }

def give_starter(game, choice: str):
    """Give the player their starter Pokemon."""
    starter = Pokemon.create(choice, 5)
    if starter:
        game.player_data["party"].append(starter)
        game.player_data["pokedex"]["seen"].add(choice)
        game.player_data["pokedex"]["caught"].add(choice)
        game.flags["got_starter"] = True
        return True
    return False
```

---

### Step 9: Add Sound System

**File: `src/core/sound_manager.py`**
```python
import pygame
import os
from config import ASSETS_PATH

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.current_music = None

    def load_sound(self, name: str, path: str):
        full_path = os.path.join(ASSETS_PATH, "sounds", path)
        if os.path.exists(full_path):
            self.sounds[name] = pygame.mixer.Sound(full_path)
            self.sounds[name].set_volume(self.sfx_volume)

    def play_sound(self, name: str):
        if name in self.sounds:
            self.sounds[name].play()

    def play_music(self, path: str, loop: bool = True):
        full_path = os.path.join(ASSETS_PATH, "music", path)
        if os.path.exists(full_path):
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music = path

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None

    def pause_music(self):
        pygame.mixer.music.pause()

    def resume_music(self):
        pygame.mixer.music.unpause()
```

---

### Step 10: Polish and Testing

1. **Add unit tests:**
   ```bash
   mkdir tests
   # Create test files for each module
   ```

2. **Test battle mechanics:**
   - Verify damage calculation matches Gen 1
   - Test type effectiveness edge cases
   - Verify catch rate formula

3. **Playtest the full demo:**
   - Start new game
   - Get starter Pokemon
   - Battle wild Pokemon on Route 1
   - Catch Pokemon
   - Fight trainers
   - Navigate to Pewter City
   - Defeat Brock

4. **Balance adjustments:**
   - Trainer levels
   - Wild Pokemon levels
   - Item availability
   - Experience curves

---

## File Checklist for Full Demo

### Must Have
- [ ] All maps: Pallet Town, Route 1, Viridian City, Route 2, Viridian Forest, Pewter City, Pewter Gym
- [ ] Interior maps: Player House, Oak Lab, Pokemon Center, Pokemart
- [ ] Working NPC dialogue
- [ ] Starter selection event
- [ ] Wild encounters working
- [ ] Trainer battles working
- [ ] Brock gym battle
- [ ] Pokemon Center healing
- [ ] Save/Load working

### Nice to Have
- [ ] Authentic sprites
- [ ] Battle transition effects
- [ ] Sound effects
- [ ] Background music
- [ ] Evolution animations
- [ ] Status condition visuals

---

## Testing Commands

```bash
# Run the game
python main.py

# Test imports
python -c "from src.game import Game; print('OK')"

# Test Pokemon creation
python -c "
from src.pokemon.pokemon import Pokemon
p = Pokemon.create('PIKACHU', 10)
print(f'{p.name} Lv.{p.level} HP:{p.current_hp}')
"

# Test battle damage
python -c "
from src.pokemon.pokemon import Pokemon
from src.battle.damage_calc import calculate_damage
a = Pokemon.create('CHARMANDER', 10)
b = Pokemon.create('BULBASAUR', 10)
move = {'name': 'EMBER', 'power': 40, 'type': 'fire'}
dmg, eff = calculate_damage(a, b, move)
print(f'Damage: {dmg}, Effectiveness: {eff}x')
"

# Run with debug output
python -c "
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
from src.game import Game
import pygame
pygame.init()
screen = pygame.display.set_mode((480, 432))
game = Game(screen)
for i in range(60):
    game.update(1/60)
print('60 frames simulated OK')
"
```

---

## Resources

- **PRET pokered**: https://github.com/pret/pokered - Original game disassembly with sprites
- **Bulbapedia**: https://bulbapedia.bulbagarden.net - Pokemon data reference
- **Gen 1 Mechanics**: https://bulbapedia.bulbagarden.net/wiki/Damage#Generation_I
- **Pygame Docs**: https://www.pygame.org/docs/
