"""
mcp_server.py — MCP server for controlling Pokemon Fire Red via mGBA.

This is the entry point for the MCP (Model Context Protocol) server that
Claude Code connects to. It wraps the MGBAClient and FireRedReader into
high-level tools that Claude can call to observe and interact with a running
Pokemon Fire Red game in mGBA.

Architecture:
    Claude Code ←(stdio/MCP)→ this server ←(TCP JSON)→ mgba_server.lua ←(native)→ mGBA

The server uses FastMCP and exposes 16 tools organized into four categories:

    Game State Tools:
        get_game_state   — Full snapshot (position, party, badges, money)
        get_party        — Detailed party Pokemon info (stats, moves, EVs)
        get_position     — Current map coordinates
        get_player_name  — Trainer name
        get_badges       — Earned gym badges
        get_money        — Current money
        get_bag          — All bag pocket contents
        get_screenshot   — Current frame as base64 PNG

    Input Tools:
        press_button     — Press a single button for N frames
        press_sequence   — Press a series of buttons in order
        walk             — Walk N tiles in a direction

    Emulator Tools:
        save_state       — Save emulator state to a slot
        load_state       — Load emulator state from a slot
        run_frames       — Advance emulation by N frames

    Low-Level Tools:
        read_memory      — Raw memory read (1/2/4/N bytes)
        write_memory     — Raw memory write (1/2/4 bytes)

Usage:
    # Start directly (for testing):
    python scripts/mcp_server.py

    # Register with Claude Code (run once):
    claude mcp add pokemon-firered -s user -- python scripts/mcp_server.py

    # Or use .mcp.json in project root (already configured)
"""

from __future__ import annotations

import sys
import os

# Ensure sibling modules (mgba_client, fire_red_memory) are importable
# when this file is run as a script entry point
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP
from mgba_client import MGBAClient
from fire_red_memory import FireRedReader

# Create the MCP server instance with a descriptive name
mcp = FastMCP("pokemon-firered")

# ---------------------------------------------------------------------------
# Lazy-initialized global instances
# ---------------------------------------------------------------------------
# The client and reader are created on first use rather than at import time,
# so the MCP server can start even if mGBA isn't running yet. The connection
# is established when the first tool is called.

_client: MGBAClient | None = None
_reader: FireRedReader | None = None


def _get_client() -> MGBAClient:
    """Get or create the MGBAClient singleton (lazy connect)."""
    global _client
    if _client is None:
        _client = MGBAClient()
        _client.connect()
    return _client


def _get_reader() -> FireRedReader:
    """Get or create the FireRedReader singleton (lazy init)."""
    global _reader
    if _reader is None:
        _reader = FireRedReader(_get_client())
    return _reader


# ==========================================================================
# GAME STATE TOOLS
# ==========================================================================
# These tools read the current state of the game without modifying anything.

@mcp.tool()
def get_game_state() -> dict:
    """Get a full snapshot of the current game state including player name, position, party summary, badges, and money."""
    return _get_reader().get_game_state()


@mcp.tool()
def get_party() -> list[dict]:
    """Get detailed information about all Pokemon in the player's party, including stats, moves, EVs, and status."""
    return _get_reader().read_party()


@mcp.tool()
def get_position() -> dict:
    """Get the player's current map coordinates and map group/number."""
    return _get_reader().read_player_position()


@mcp.tool()
def get_player_name() -> str:
    """Get the player's trainer name."""
    return _get_reader().read_player_name()


@mcp.tool()
def get_badges() -> list[str]:
    """Get a list of earned gym badges."""
    return _get_reader().read_badges()


@mcp.tool()
def get_money() -> int:
    """Get the player's current money."""
    return _get_reader().read_money()


@mcp.tool()
def get_bag() -> dict:
    """Get the contents of all bag pockets (items, key items, pokeballs, TMs/HMs, berries)."""
    return _get_reader().read_bag()


@mcp.tool()
def get_screenshot() -> str:
    """Capture the current frame as a base64-encoded PNG image. Returns a data URI string."""
    b64 = _get_client().screenshot()
    return f"data:image/png;base64,{b64}"


# ==========================================================================
# INPUT TOOLS
# ==========================================================================
# These tools send button inputs to the emulator to control the game.

@mcp.tool()
def press_button(button: str, frames: int = 10) -> str:
    """Press a single button for N frames. Valid buttons: A, B, START, SELECT, UP, DOWN, LEFT, RIGHT, L, R."""
    _get_client().press_button(button, frames)
    # Wait for the press to complete plus a small buffer for the game to react
    _get_client().run_frames(frames + 2)
    return f"Pressed {button} for {frames} frames"


@mcp.tool()
def press_sequence(buttons: list[str], frame_delay: int = 12) -> str:
    """Press a series of buttons in sequence. Each button is held for 10 frames with a delay between presses.

    Args:
        buttons: List of button names (e.g. ["A", "UP", "UP", "A"])
        frame_delay: Frames to wait between button presses (default 12)
    """
    client = _get_client()
    for button in buttons:
        client.press_button(button, 10)
        client.run_frames(frame_delay)
    return f"Pressed sequence: {', '.join(buttons)}"


@mcp.tool()
def walk(direction: str, steps: int = 1) -> str:
    """Walk the player N tiles in a direction. Direction must be UP, DOWN, LEFT, or RIGHT.

    Args:
        direction: Direction to walk (UP, DOWN, LEFT, RIGHT)
        steps: Number of tiles to walk (default 1)
    """
    direction = direction.upper()
    if direction not in ("UP", "DOWN", "LEFT", "RIGHT"):
        return f"Invalid direction: {direction}. Use UP, DOWN, LEFT, or RIGHT."

    client = _get_client()
    # The player moves at 1 tile per 16 frames when walking.
    # We hold the direction for 16 frames, then wait 2 extra for the step to register.
    for _ in range(steps):
        client.press_button(direction, 16)
        client.run_frames(18)
    return f"Walked {direction} {steps} step(s)"


# ==========================================================================
# EMULATOR TOOLS
# ==========================================================================
# These tools control the emulator itself (save states, frame advance).

@mcp.tool()
def save_state(slot: int = 1) -> str:
    """Save the emulator state to a slot (1-9)."""
    _get_client().save_state(slot)
    return f"Saved state to slot {slot}"


@mcp.tool()
def load_state(slot: int = 1) -> str:
    """Load an emulator save state from a slot (1-9)."""
    _get_client().load_state(slot)
    return f"Loaded state from slot {slot}"


@mcp.tool()
def run_frames(count: int = 60) -> str:
    """Advance emulation by N frames (60 frames = ~1 second at 60 FPS).

    Args:
        count: Number of frames to advance (default 60)
    """
    _get_client().run_frames(count)
    return f"Advanced {count} frames"


# ==========================================================================
# LOW-LEVEL MEMORY TOOLS
# ==========================================================================
# Direct memory access for advanced use or debugging.

@mcp.tool()
def read_memory(address: int, size: int = 1) -> dict:
    """Read raw memory from the GBA. Size must be 1, 2, or 4 bytes, or use 'range' for arbitrary lengths.

    Args:
        address: Memory address (e.g. 0x02024029)
        size: Number of bytes to read (1, 2, or 4 for typed reads)
    """
    client = _get_client()
    if size == 1:
        return {"address": hex(address), "value": client.read8(address)}
    elif size == 2:
        return {"address": hex(address), "value": client.read16(address)}
    elif size == 4:
        return {"address": hex(address), "value": client.read32(address)}
    else:
        # For arbitrary sizes, read as a byte range and return both hex and list
        data = client.read_range(address, size)
        return {"address": hex(address), "hex": data.hex(), "bytes": list(data)}


@mcp.tool()
def write_memory(address: int, value: int, size: int = 1) -> str:
    """Write a value to GBA memory. Size must be 1, 2, or 4 bytes.

    Args:
        address: Memory address to write to
        value: Value to write
        size: Number of bytes (1, 2, or 4)
    """
    client = _get_client()
    if size == 1:
        client.write8(address, value)
    elif size == 2:
        client.write16(address, value)
    elif size == 4:
        client.write32(address, value)
    else:
        return f"Invalid size: {size}. Use 1, 2, or 4."
    return f"Wrote {value} ({size} byte(s)) to {hex(address)}"


# ==========================================================================
# ENTRY POINT
# ==========================================================================

if __name__ == "__main__":
    mcp.run()
