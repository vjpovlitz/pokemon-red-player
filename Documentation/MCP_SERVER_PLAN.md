# Plan: mGBA Scripting Environment + MCP Server for Pokemon Fire Red

## Context

The user has mGBA running Pokemon Fire Red and wants to programmatically interact with the emulator — reading game state, pressing buttons, taking screenshots, and scripting automation. The goal is to build an MCP server so Claude Code can directly observe and control the game.

## Architecture

```
Claude Code ←(stdio/MCP)→ mcp_server.py ←(TCP JSON)→ mgba_server.lua ←(native API)→ mGBA
```

**Two-layer design:**
1. **Lua TCP server** — runs inside mGBA via its built-in scripting engine. Exposes raw memory read/write, button input, screenshots, and save states over a TCP socket with a simple JSON protocol.
2. **Python MCP server** — connects to the Lua server as a TCP client. Wraps raw memory access into high-level Pokemon Fire Red-specific tools (read party, read position, etc.) and exposes them via the MCP protocol to Claude Code.

This approach uses mGBA's native Lua 5.4 scripting (no building from source, no extra dependencies beyond stock mGBA 0.10+) and FastMCP for the Python MCP server.

## File Structure

```
scripts/
├── mgba_server.lua          # Lua TCP server loaded inside mGBA
├── mcp_server.py            # FastMCP MCP server (entry point)
├── mgba_client.py           # Python TCP client that talks to the Lua server
├── fire_red_memory.py       # Pokemon Fire Red memory map + parsing helpers
└── requirements.txt         # fastmcp, etc.
```

## Implementation Steps

### Step 1: Lua TCP Socket Server (`scripts/mgba_server.lua`)

Runs inside mGBA (Tools > Load Script). Binds to `localhost:5555`. Handles JSON requests/responses.

**Commands to implement:**
- `read8`, `read16`, `read32` — read memory at address
- `readRange` — read N bytes, return as hex string
- `write8`, `write16`, `write32` — write memory
- `press` — hold a button for N frames (A, B, Up, Down, Left, Right, Start, Select, L, R)
- `screenshot` — capture current frame as base64 PNG
- `saveState` / `loadState` — save/load to slot
- `runFrames` — advance N frames
- `getKeys` — read current input state

Protocol: newline-delimited JSON. Request: `{"cmd": "read16", "addr": 33685512}`. Response: `{"ok": true, "value": 42}` or `{"ok": false, "error": "msg"}`.

### Step 2: Python TCP Bridge (`scripts/mgba_client.py`)

A Python class `MGBAClient` that:
- Connects to `localhost:5555`
- Sends JSON commands, receives JSON responses
- Provides typed Python methods: `read8(addr)`, `read16(addr)`, `read_range(addr, length)`, `write8(addr, val)`, `press_button(button, frames)`, `screenshot()`, `save_state(slot)`, `load_state(slot)`, `run_frames(n)`
- Handles reconnection on disconnect

### Step 3: Fire Red Memory Map (`scripts/fire_red_memory.py`)

Pokemon Fire Red (US v1.0) memory addresses and struct parsing:

**Key addresses:**
- Party Pokemon base: `0x02024284` (100 bytes per slot, 6 slots)
- Party count: `0x02024029`
- Player X/Y: read via pointer at `0x03005008` (offsets +0x00, +0x02)
- Player name: via pointer at `0x0300500C` (8 bytes)
- Trainer ID: via pointer at `0x0300500C` + `0x0A`
- Badges: flags in save block
- Money: via save block pointer
- Map bank/number: via pointer at `0x03005008` + offsets

**Parsing functions:**
- `read_party()` — returns list of Pokemon dicts (species, level, HP, moves, etc.)
- `read_player_position()` — returns (map_bank, map_id, x, y)
- `read_player_name()` — returns decoded string
- `read_bag()` — returns inventory items
- `get_game_state()` — snapshot of key state (position, party summary, badges)
- Gen 3 character encoding table (proprietary encoding, not ASCII)

### Step 4: MCP Server (`scripts/mcp_server.py`)

FastMCP server exposing tools to Claude Code:

**High-level game tools:**
- `get_game_state()` — full snapshot: position, party, badges, money
- `get_party()` — detailed party Pokemon info
- `get_position()` — current map and coordinates
- `get_screenshot()` — capture and return current frame as image
- `get_bag()` — inventory contents

**Input tools:**
- `press_button(button, frames=10)` — press a single button
- `press_sequence(buttons)` — press a series of buttons with delays
- `walk(direction, steps)` — walk N tiles in a direction

**Emulator tools:**
- `save_state(slot)` / `load_state(slot)` — save state management
- `run_frames(count)` — advance emulation

**Low-level tools:**
- `read_memory(address, size)` — raw memory read
- `write_memory(address, size, value)` — raw memory write

### Step 5: Claude Code Integration

Register the MCP server with Claude Code:
```bash
claude mcp add pokemon-firered -s user -- python scripts/mcp_server.py
```

This makes all tools available in Claude Code sessions for this project.

## Dependencies

`scripts/requirements.txt`:
```
fastmcp>=2.0.0
```

No additional Python deps needed — uses stdlib `socket`, `json`, `struct`, `base64`.

## Verification

1. **Lua server**: Load `scripts/mgba_server.lua` in mGBA (Tools > Scripting > File > Load Script). Check mGBA scripting console for "Server listening on port 5555".
2. **Python bridge**: Run `python -c "from scripts.mgba_client import MGBAClient; c = MGBAClient(); print(c.read8(0x02024029))"` to read party count.
3. **MCP server**: Run `python scripts/mcp_server.py` to start, then test via Claude Code with `/mcp` to verify "pokemon-firered" shows as connected.
4. **End-to-end**: In Claude Code, call `get_game_state()` tool — should return current position on Route 1 and Charmander in party.
