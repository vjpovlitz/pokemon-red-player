# Pokemon Fire Red MCP Server

An MCP (Model Context Protocol) server that lets Claude Code programmatically observe and control Pokemon Fire Red running in the mGBA emulator. Read game state, press buttons, take screenshots, and automate gameplay — all through natural language.

## Architecture

```
Claude Code <--(stdio/MCP)--> mcp_server.py <--(TCP JSON)--> mgba_server.lua <--(native API)--> mGBA
```

**Two-layer design:**

1. **Lua TCP server** (`mgba_server.lua`) — Runs inside mGBA via its built-in scripting engine. Exposes raw memory read/write, button input, screenshots, and save states over a TCP socket with a newline-delimited JSON protocol on port 5555.

2. **Python MCP server** (`mcp_server.py`) — Connects to the Lua server as a TCP client. Wraps raw memory access into high-level Pokemon Fire Red-specific tools and exposes them via MCP to Claude Code.

## Prerequisites

- **mGBA 0.10+** with scripting enabled ([download](https://mgba.io/downloads.html))
- **Python 3.10+**
- **Pokemon Fire Red ROM** (USA, v1.0 — game code BPRE)
- **Claude Code** CLI

## Setup

### 1. Install Python dependencies

```bash
pip install -r scripts/requirements.txt
```

### 2. Load the Lua server in mGBA

1. Open mGBA and load your Pokemon Fire Red ROM
2. Go to **Tools > Scripting** (or press Ctrl+Shift+S)
3. In the scripting window, go to **File > Load Script**
4. Select `scripts/mgba_server.lua`
5. You should see `mGBA TCP server listening on port 5555` in the scripting console

### 3. Register the MCP server with Claude Code

The project includes a `.mcp.json` file that auto-registers the server. Just restart Claude Code in this project directory and approve the MCP server when prompted.

Alternatively, register manually:

```bash
claude mcp add pokemon-firered -s user -- python scripts/mcp_server.py
```

### 4. Verify the connection

In Claude Code, the `pokemon-firered` MCP server should appear as connected. Try calling `get_game_state` to see your current position and party.

## Available Tools (16 total)

### Game State (read-only)

| Tool | Description |
|------|-------------|
| `get_game_state` | Full snapshot: position, party summary, badges, money |
| `get_party` | Detailed party Pokemon info (stats, moves, EVs) |
| `get_position` | Current map coordinates and map group/number |
| `get_player_name` | Trainer name |
| `get_badges` | List of earned gym badges |
| `get_money` | Current money |
| `get_bag` | All bag pocket contents |
| `get_screenshot` | Current frame as base64 PNG |

### Input (game control)

| Tool | Description |
|------|-------------|
| `press_button` | Press A, B, START, SELECT, directions, L, R for N frames |
| `press_sequence` | Press a series of buttons in order |
| `walk` | Walk N tiles in a direction (UP/DOWN/LEFT/RIGHT) |

### Emulator

| Tool | Description |
|------|-------------|
| `save_state` | Save emulator state to slot 1-9 |
| `load_state` | Load emulator state from slot 1-9 |
| `run_frames` | Advance emulation by N frames (60 = ~1 second) |

### Low-Level

| Tool | Description |
|------|-------------|
| `read_memory` | Raw memory read (1/2/4/N bytes) |
| `write_memory` | Raw memory write (1/2/4 bytes) |

## Project Structure

```
scripts/
├── mgba_server.lua       # Lua TCP server (runs inside mGBA)
├── mcp_server.py          # FastMCP server (Claude Code entry point)
├── mgba_client.py         # Python TCP client for the Lua server
├── fire_red_memory.py     # Fire Red memory map + struct parsing
└── requirements.txt       # Python dependencies (fastmcp)
.mcp.json                  # Claude Code MCP server registration
```

## Troubleshooting

### "Connection refused" when calling tools

The Lua server isn't running. Make sure you:
1. Have mGBA open with a ROM loaded
2. Loaded `mgba_server.lua` via Tools > Scripting > File > Load Script
3. See "Server listening on port 5555" in the scripting console

### MCP server not showing in Claude Code

- Restart Claude Code in the project directory
- Check that `.mcp.json` exists in the project root
- Try manual registration: `claude mcp add pokemon-firered -s user -- python scripts/mcp_server.py`

### Wrong memory values / garbled data

The memory addresses are for **Pokemon Fire Red USA v1.0** only. Other versions (v1.1, European, Japanese) have different memory layouts.

### Port 5555 already in use

If another instance of the Lua server is running, close mGBA and reopen it. Only one instance of the server can bind to port 5555 at a time.

## Supported Game Version

**Pokemon Fire Red (USA, v1.0)** — Game code `BPRE`, revision 0.

Memory addresses, struct layouts, and encryption keys are all specific to this version. Supporting other versions would require updating the addresses in `fire_red_memory.py`.

## License

This is a fan project for educational purposes. Pokemon is a trademark of Nintendo/Game Freak/The Pokemon Company.
