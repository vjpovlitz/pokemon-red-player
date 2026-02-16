# AI Pokemon Bot — Comprehensive Build Plan

## Evaluation of the Gemini Response

The Gemini response gets the broad strokes right but has several issues worth calling out before we build on it:

**What Gemini got right:**
- PyBoy is the correct emulator choice for Game Boy titles (Red/Blue/Gold/Silver)
- Reading RAM directly is the right approach over pure vision
- The general loop of Read → Decide → Act is correct
- MCP as a connection layer between Claude and the emulator is a valid architecture

**What Gemini got wrong or oversimplified:**

1. **Outdated API calls.** The code uses `pyboy.get_memory_value()` and `PyBoy.BUTTON_A` — both are deprecated. The current PyBoy 2.7.0 API uses `pyboy.memory[address]` for RAM reads and `pyboy.button('a')` for input. The `send_input()` method now uses string-based inputs, not class constants.

2. **Wrong RAM addresses.** The example uses `0xD362` and `0xD361` for player coordinates. The actual WRAM addresses from the PRET disassembly are `0xD361` (Y) and `0xD362` (X) — the labels are swapped. More importantly, Gemini doesn't mention that you need the full PRET symbol table to do this properly, which maps hundreds of meaningful game variables to their addresses.

3. **No mention of Diamond/Pearl complexity.** The response only covers Game Boy titles via PyBoy. Pokemon Diamond/Pearl are Nintendo DS games requiring a completely different emulator (py-desmume or MelonDS), a different memory layout (ARM9 WRAM), and a different control scheme (touchscreen + buttons). This is a major gap.

4. **Naive use of Gemini CLI.** Shelling out to `gemini` CLI per battle screenshot is extremely slow and expensive. A real implementation needs an async decision pipeline with batched API calls, not synchronous subprocess calls per frame.

5. **No mention of existing prior art.** Anthropic literally built and streamed "Claude Plays Pokemon" on Twitch using PyBoy. David Hershey open-sourced a starter implementation (ClaudePlaysPokemonStarter). The PokemonRL project has been training RL agents on Pokemon Red since 2020 and published results in February 2025. These are critical references.

6. **Missing the hard parts.** No discussion of state management across API calls, context window limits, save/load states for recovery, reward shaping, pathfinding algorithms, or the fact that Pokemon has 25+ hours of nonlinear gameplay.

---

## The Two Target Games: Different Beasts

### Pokemon Red (Game Boy, 1996)
- **Emulator:** PyBoy (Python-native, v2.7.0, pip installable)
- **RAM access:** Direct via `pyboy.memory[address]`, well-documented WRAM map from PRET disassembly
- **Input:** 8 buttons (A, B, Start, Select, D-pad)
- **Resolution:** 160×144 pixels
- **Existing AI work:** Extensive — PokemonRL beat the game with RL in 2025, ClaudePlaysPokemonStarter exists, Anthropic streamed it on Twitch
- **Difficulty for AI:** Moderate — linear-ish progression, simple battle system, well-mapped RAM

### Pokemon Diamond/Pearl (Nintendo DS, 2006)
- **Emulator:** py-desmume (Python bindings for DeSmuME, v0.0.9) or MelonDS via Lua scripting
- **RAM access:** Via py-desmume's `emu.memory` accessor with memory hooks, or DeSmuME's Lua scripting interface
- **Input:** 12 buttons + touchscreen (X/Y coordinates for touch)
- **Resolution:** 256×192 pixels per screen (dual screen)
- **Existing AI work:** Very limited — mostly Action Replay cheat code documentation, no known LLM-based agents
- **Difficulty for AI:** Significantly harder — dual screen, touchscreen menus, 3D overworld navigation, more complex battle system, less documented RAM layout

**Recommendation:** Start with Pokemon Red. Get the full pipeline working, then port the architecture to Diamond/Pearl. The core patterns (state reading, decision making, input injection) transfer, but the emulator interface layer changes completely.

---

## Architecture Overview

The system has four layers:

```
┌─────────────────────────────────────────────┐
│           BRAIN LAYER (Claude API)           │
│  Strategic decisions, battle logic,          │
│  navigation planning, game knowledge         │
├─────────────────────────────────────────────┤1
│           MCP TOOL SERVER                    │
│  Exposes emulator actions as Claude tools:   │
│  press_button, read_party, get_location,     │
│  get_screenshot, save_state, etc.            │
├─────────────────────────────────────────────┤
│           GAME STATE MANAGER                 │
│  Reads RAM, tracks history, detects game     │
│  phase (overworld/battle/menu/dialog),       │
│  computes rewards, manages save states       │
├─────────────────────────────────────────────┤
│           EMULATOR LAYER                     │
│  PyBoy (GB) or py-desmume (NDS)              │
│  Headless or windowed, frame stepping,       │
│  memory access, screenshot capture           │
└─────────────────────────────────────────────┘
```

---

## Phase 1: Pokemon Red — Foundation Build

### 1.1 Environment Setup

**Prerequisites (for your M4 MacBook Pro):**
```bash
# Python environment
python3 -m venv pokemon-ai
source pokemon-ai/bin/activate

# Core dependencies
pip install pyboy anthropic pillow numpy

# Claude Code (for development assistance)
npm install -g @anthropic-ai/claude-code

# MCP SDK (for building the tool server)
pip install mcp
```

**ROM and Symbol Table:**
- You need a Pokemon Red `.gb` ROM file (legally dump your own cartridge)
- Download the PRET symbol table from the pokered disassembly project (https://github.com/pret/pokered) — this maps assembly labels like `wPlayerXCoord` to RAM addresses like `0xD362`

### 1.2 Game State Reader Module

This is the foundation. Build a Python class that reads all critical game state from RAM using the PRET symbol table.

**Critical RAM addresses for Pokemon Red (from PRET disassembly + Data Crystal):**

| Variable | Address | Description |
|----------|---------|-------------|
| `wXCoord` | `0xD362` | Player X position on map |
| `wYCoord` | `0xD361` | Player Y position on map |
| `wCurMap` | `0xD35E` | Current map ID |
| `wIsInBattle` | `0xD057` | 0 = overworld, 1 = wild, 2 = trainer |
| `wPartyCount` | `0xD163` | Number of Pokemon in party |
| `wPartyMon1HP` | `0xD16C` | Lead Pokemon current HP (2 bytes) |
| `wPartyMon1MaxHP` | `0xD18D` | Lead Pokemon max HP (2 bytes) |
| `wPartyMon1Level` | `0xD18C` | Lead Pokemon level |
| `wBagItemCount` | `0xD31D` | Number of items in bag |
| `wObtainedBadges` | `0xD356` | Bitfield of gym badges |
| `wPlayerMoney` | `0xD347` | Player money (3 bytes BCD) |
| `wEnemyMonHP` | `0xCFE6` | Enemy Pokemon HP in battle (2 bytes) |
| `wEnemyMonLevel` | `0xCFF3` | Enemy Pokemon level |
| `wCurEnemySpecies` | `0xCFE5` | Enemy Pokemon species ID |
| `wBattleMonMoves` | `0xD01C` | Player's available moves in battle |
| `wEventFlags` | `0xD747` | Game progression event flags |
| `wTextBoxID` | `0xFF8C` | Identifies active text/menu |

**Key architecture decision:** Read RAM, not screenshots, for structured state. Use screenshots only for debugging and for situations where RAM doesn't capture what you need (rare).

### 1.3 Emulator Control Module

```python
# Conceptual structure — build this with Claude Code
class EmulatorController:
    def __init__(self, rom_path, headless=True):
        window = "null" if headless else "SDL2"
        self.pyboy = PyBoy(rom_path, window=window)
        self.pyboy.set_emulation_speed(0)  # Max speed
    
    def press_button(self, button, hold_frames=1):
        """Press a button and advance frames."""
        self.pyboy.button(button)          # 'a','b','up','down','left','right','start','select'
        self.pyboy.tick(hold_frames)       # Advance frames while held
        self.pyboy.button_release(button)
        self.pyboy.tick(10)                # Let game process input
    
    def press_sequence(self, buttons, delay=8):
        """Press a sequence of buttons with delays."""
        for btn in buttons:
            self.press_button(btn, hold_frames=delay)
    
    def advance_frames(self, n, render=False):
        """Advance n frames without input."""
        self.pyboy.tick(n, render)
    
    def get_screenshot(self):
        """Capture current screen as PIL Image."""
        return self.pyboy.screen.image
    
    def read_memory(self, address):
        """Read a single byte from RAM."""
        return self.pyboy.memory[address]
    
    def read_memory_word(self, address):
        """Read a 16-bit value (little-endian)."""
        return self.pyboy.memory[address] | (self.pyboy.memory[address + 1] << 8)
    
    def save_state(self, path):
        """Save emulator state for recovery."""
        with open(path, 'wb') as f:
            self.pyboy.save_state(f)
    
    def load_state(self, path):
        """Load a saved state."""
        with open(path, 'rb') as f:
            self.pyboy.load_state(f)
```

### 1.4 MCP Tool Server

Build an MCP server that exposes the emulator as tools Claude can call. This is the bridge between the LLM and the game.

**Tools to expose:**

| Tool Name | Parameters | Returns |
|-----------|------------|---------|
| `press_button` | button name, hold duration | confirmation |
| `press_sequence` | list of buttons | confirmation |
| `get_game_state` | none | full structured state (location, party, battle status, badges, items) |
| `get_screenshot` | none | base64 PNG of current screen |
| `get_battle_state` | none | detailed battle info (your moves, HP, enemy species/HP/type) |
| `save_game` | slot name | confirmation |
| `load_game` | slot name | confirmation |
| `walk_to` | direction, steps | result after walking |
| `navigate_menu` | sequence of menu actions | result |

**MCP server implementation approach:**
Use the `mcp` Python SDK to create a stdio-based server. Register each tool with its schema. The server maintains a single PyBoy instance and processes tool calls sequentially.

```bash
# Register with Claude Code
claude mcp add --transport stdio pokemon-emulator -- \
    python /path/to/pokemon_mcp_server.py
```

### 1.5 Claude Agent Loop

The agent operates in a loop with different strategies based on game phase:

**Phase Detection (from RAM):**
- `wIsInBattle == 0` → Overworld navigation mode
- `wIsInBattle == 1` → Wild battle mode
- `wIsInBattle == 2` → Trainer battle mode  
- Text box active → Dialog/menu mode

**Overworld Strategy:**
Claude receives: current map, coordinates, badge count, party info, and the current objective (derived from game progression flags). It outputs a sequence of directional inputs to navigate. For complex pathfinding, pre-compute routes between key locations using the map data from the PRET disassembly rather than asking Claude to figure out every step.

**Battle Strategy:**
Claude receives: your active Pokemon (species, level, HP, moves, types), enemy Pokemon (species, level, HP, types), and the available actions (fight/bag/pokemon/run). It decides the optimal move using its knowledge of the Pokemon type chart and game mechanics.

**Dialog Strategy:**
For text boxes and menus, Claude reads the current context and decides whether to press A (advance), B (cancel), or navigate to a specific menu option.

### 1.6 Development Workflow with Claude Code

Use Claude Code as your pair programmer throughout:

```bash
cd pokemon-ai-project
claude

# Example prompts:
# "Set up the project structure with a game_state module, emulator module, 
#  mcp_server module, and agent module"
# "Write the GameStateReader class using these RAM addresses from the PRET 
#  symbol table"
# "Create the MCP server with tools for press_button, get_game_state, 
#  get_screenshot, and get_battle_state"
# "Write battle logic that uses the Pokemon type effectiveness chart"
# "Debug why the agent gets stuck in Viridian Forest — add logging for 
#  map transitions and trainer encounters"
```

---

## Phase 2: Pokemon Diamond/Pearl — NDS Adaptation

### 2.1 Emulator Switch

Replace PyBoy with py-desmume:

```bash
pip install py-desmume
```

**Key differences:**
- Dual screen (top 256×192 + bottom 256×192 touchscreen)
- Touchscreen input via `emu.input.touch_set_pos(x, y)` and `emu.input.touch_release()`
- Memory hooks for event-driven state reading: `emu.memory.register_exec(address, callback)`
- Frame cycle via `emu.cycle()` instead of `tick()`
- Different button constants via `desmume.controls.Keys`

### 2.2 Memory Mapping for Diamond/Pearl

The NDS memory space is more complex than Game Boy. Key regions:
- Main RAM: 4MB starting at `0x02000000`
- ARM7 WRAM: starting at `0x03800000`

Diamond/Pearl RAM addresses are less comprehensively documented than Gen 1, but the community has mapped the critical ones through Action Replay research and the pret/pokediamond disassembly project. Party data, map coordinates, battle state, and item data all have known offsets.

The py-desmume `MemoryAccessor` provides `read_byte()`, `read_short()`, `read_long()` for reading these addresses during emulation.

### 2.3 Touchscreen Handling

Diamond/Pearl heavily uses the touchscreen for menus, Pokemon selection, and battle moves. Your MCP server needs touch-specific tools:

| Tool | Parameters | Purpose |
|------|------------|---------|
| `touch_tap` | x, y coordinates | Tap a point on bottom screen |
| `touch_drag` | start_x, start_y, end_x, end_y | Drag gesture |
| `get_bottom_screen` | none | Screenshot of touchscreen |

Map menu button positions to coordinate regions so Claude can say "select Move 1" and the system translates that to the correct touch coordinates.

### 2.4 NDS-Specific Challenges

- **3D overworld:** Diamond/Pearl has a pseudo-3D world. RAM-based position tracking is essential since vision-based navigation would be unreliable.
- **Real-time clock:** The game uses the DS clock for time-of-day events. You may need to manipulate this.
- **Wi-Fi features:** Some evolutions require trading. You'll need to either skip these Pokemon or use memory manipulation.
- **Touchscreen menus:** Battle menus, PC boxes, and the Poketch are all touch-based. Pre-map the UI coordinate regions.

---

## Phase 3: Advanced Features

### 3.1 Hybrid AI Architecture

For the most capable bot, combine deterministic scripting with LLM reasoning:

**Deterministic layer (fast, cheap, reliable):**
- Pathfinding between known locations using pre-computed map graphs
- Type effectiveness calculations
- Menu navigation sequences
- Healing at Pokemon Centers (always the same button sequence)

**LLM layer (slow, expensive, flexible):**
- Strategic battle decisions (when to switch Pokemon, when to use items)
- Handling novel situations (stuck, lost, unexpected game state)
- Team composition decisions
- Adaptive difficulty handling (grinding decisions)

### 3.2 Memory and Context Management

Claude's context window is finite. For a 25-hour game, you need a summarization strategy:

- Maintain a rolling **game journal** — after every major event (badge earned, new area entered, Pokemon caught), append a one-line summary
- Keep the **current objective** and **immediate game state** in every prompt
- Periodically summarize and compress the journal
- Use save states as checkpoints — if something goes wrong, roll back

### 3.3 PyBoy Hook System for Advanced State Tracking

PyBoy supports injecting Python callbacks at specific ROM addresses:

```python
# Example: Hook the "battle won" routine to track victories
def on_battle_won(context):
    print("Battle won!")
    
pyboy.hook_register(
    bank=0,
    addr=0x3A57,  # Address of battle victory routine
    callback=on_battle_won,
    context=None
)
```

The PokemonRL project used this extensively to detect events like "CUT was used successfully" that have no direct WRAM flag. The PRET disassembly is your roadmap for finding these hook points.

---

## Key Reference Projects

1. **ClaudePlaysPokemonStarter** (https://github.com/davidhershey/ClaudePlaysPokemonStarter) — Anthropic engineer David Hershey's minimal implementation. Uses Claude API with function calling, PyBoy, and RAM reading. This is your best starting template.

2. **ClaudePlayer** (https://github.com/jmurth1234/ClaudePlayer) — Community implementation with turn-based and continuous modes, configurable models, screenshot history management, and memory tools. More feature-complete than the starter.

3. **PokemonRedExperiments** (https://github.com/PWhiddy/PokemonRedExperiments) — Peter Whidden's RL approach. Published as an arXiv paper in February 2025. Uses PyBoy with Gymnasium wrapper, deep Q-learning. Demonstrates that Pokemon Red is solvable by AI. Great reference for reward shaping and the Gymnasium environment setup.

4. **PokemonRL** (https://drubinstein.github.io/pokerl/) — David Rubinstein's team. Beat Pokemon Red with a sub-10M parameter RL policy. Excellent documentation on RAM reading, hook systems, and the PRET symbol table integration.

5. **PRET pokered disassembly** (https://github.com/pret/pokered) — The complete reverse-engineered source code of Pokemon Red. The symbol table (`pokered.sym`) is the single most important file for RAM-based state reading.

6. **Anthropic Desktop Extensions / PyBoy MCP** — Anthropic themselves packaged a PyBoy MCP extension as a Desktop Extension (.mcpb). This proves the MCP-to-emulator pattern is the intended architecture.

---

## Recommended Build Order

| Step | Task | Time Estimate | Tools |
|------|------|---------------|-------|
| 1 | Clone ClaudePlaysPokemonStarter, get it running with your ROM | 1-2 hours | PyBoy, Python, Anthropic API key |
| 2 | Extend the GameStateReader with full PRET symbol table | 3-4 hours | Claude Code to write the reader |
| 3 | Build the MCP tool server wrapping the emulator | 4-6 hours | MCP Python SDK, Claude Code |
| 4 | Implement phase detection (overworld/battle/menu) | 2-3 hours | RAM address analysis |
| 5 | Build battle strategy with type effectiveness | 3-4 hours | Claude API, Pokemon data tables |
| 6 | Implement basic pathfinding for key routes | 4-6 hours | Map data from PRET, A* algorithm |
| 7 | Add save state management and crash recovery | 2-3 hours | PyBoy save/load API |
| 8 | Build the summarization pipeline for long-term memory | 3-4 hours | Claude API for summarization |
| 9 | Test end-to-end through first gym (Brock) | 4-8 hours | Integration testing, debugging |
| 10 | Iterate through remaining gyms and Elite Four | Ongoing | Patience, API credits |
| 11 | Port architecture to py-desmume for Diamond/Pearl | 8-16 hours | py-desmume, NDS RAM research |

---

## Cost Considerations

Running Claude API calls for every decision in a 25-hour game adds up. Rough estimates:

- **Battle decisions:** ~500 battles × ~3 API calls each = 1,500 calls
- **Navigation decisions:** Thousands of directional choices, but most can be scripted
- **Menu/dialog:** Mostly scripted, occasional LLM calls for novel situations

**Optimization strategies:**
- Use Claude Haiku 4.5 for simple decisions (menu navigation, basic battles)
- Use Claude Sonnet 4.5 for complex decisions (gym battles, team strategy)
- Script deterministic actions (walking known paths, healing, buying items) without API calls
- Batch game state reads to minimize round trips
- Use the `pyboy.tick(count, render=False)` pattern to skip rendering for speed

---

## Project Structure

```
pokemon-ai-bot/
├── README.md
├── requirements.txt
├── config.py                  # API keys, ROM paths, settings
├── main.py                    # Entry point and main game loop
├── emulator/
│   ├── pyboy_controller.py    # PyBoy wrapper for Game Boy
│   ├── desmume_controller.py  # py-desmume wrapper for NDS
│   └── base_controller.py     # Abstract interface both implement
├── state/
│   ├── game_state_reader.py   # RAM reading and state parsing
│   ├── ram_addresses.py       # PRET symbol table mappings
│   ├── battle_state.py        # Battle-specific state parsing
│   └── progression.py         # Event flag tracking and objectives
├── agent/
│   ├── brain.py               # Claude API integration
│   ├── battle_agent.py        # Battle decision making
│   ├── navigation_agent.py    # Overworld movement
│   ├── menu_agent.py          # Menu and dialog handling
│   └── memory.py              # Long-term game journal and summarization
├── mcp_server/
│   ├── server.py              # MCP tool server implementation
│   └── tools.py               # Tool definitions and handlers
├── data/
│   ├── type_chart.json        # Pokemon type effectiveness
│   ├── maps/                  # Pre-computed map graphs
│   ├── pokemon_data.json      # Species, base stats, learnsets
│   └── routes.json            # Key navigation routes
├── saves/                     # Save states directory
└── logs/                      # Game journal and debug logs
```

This structure cleanly separates concerns and makes it straightforward to swap the emulator layer when moving from Red to Diamond/Pearl.