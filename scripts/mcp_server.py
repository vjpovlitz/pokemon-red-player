"""
mcp_server.py — MCP server for controlling Pokemon Fire Red via mGBA.

This is the entry point for the MCP (Model Context Protocol) server that
Claude Code connects to. It wraps the MGBAClient and FireRedReader into
high-level tools that Claude can call to observe and interact with a running
Pokemon Fire Red game in mGBA.

Architecture:
    Claude Code ←(stdio/MCP)→ this server ←(TCP JSON)→ mgba_server.lua ←(native)→ mGBA

The server uses FastMCP and exposes 21 tools organized into six categories:

    Game State Tools (8):
        get_game_state   — Full snapshot (position, party, badges, money)
        get_party        — Detailed party Pokemon info (stats, moves, EVs)
        get_position     — Current map coordinates
        get_player_name  — Trainer name
        get_badges       — Earned gym badges
        get_money        — Current money
        get_bag          — All bag pocket contents
        get_screenshot   — Capture frame, save to disk as labeled PNG

    Battle Tools (3):
        get_battle_state    — Detect if in battle, get battle type/outcome
        get_opponent_pokemon — Active opponent Pokemon stats during battle
        get_opponent_party   — Full opponent trainer party during battle

    Menu Tools (2):
        get_start_menu_state — Read START menu cursor position and items
        save_game            — Navigate in-game menu to save the game

    Input Tools (3):
        press_button     — Press a single button for N frames
        press_sequence   — Press a series of buttons in order
        walk             — Walk N tiles in a direction

    Emulator Tools (3):
        save_state       — Save emulator state to a slot
        load_state       — Load emulator state from a slot
        run_frames       — Advance emulation by N frames

    Low-Level Tools (2):
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
from save_screenshot import ScreenshotManager

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
# Screenshot manager is created once per MCP server lifetime (= one Claude Code session).
# All screenshots within a session share the same session ID prefix.
_screenshot_mgr: ScreenshotManager | None = None


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


def _get_screenshot_mgr() -> ScreenshotManager:
    """Get or create the ScreenshotManager singleton (lazy init).

    Created once per MCP server lifetime. The session ID is set at creation
    time, so all screenshots within a Claude Code session share the same
    session prefix for easy grouping.
    """
    global _screenshot_mgr
    if _screenshot_mgr is None:
        _screenshot_mgr = ScreenshotManager()
    return _screenshot_mgr


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
def get_screenshot(label: str = "screenshot") -> str:
    """Capture the current frame and save it as a PNG file to screenshots/.

    The saved file can be viewed natively by Claude Code using the Read tool.
    Screenshots are named with the session ID, sequence number, and label
    for easy identification and chronological ordering.

    Args:
        label: Descriptive label for this screenshot (e.g. "battle_start",
               "menu_open", "route_1"). Default is "screenshot".

    Returns:
        Absolute file path to the saved PNG. Use the Read tool to view it.
    """
    b64 = _get_client().screenshot()
    path = _get_screenshot_mgr().save(b64, label=label)
    return path


# ==========================================================================
# BATTLE TOOLS
# ==========================================================================
# Tools for detecting and interacting with the battle system.

@mcp.tool()
def get_battle_state() -> dict:
    """Check if the player is currently in a battle and get battle details.

    Returns battle status including:
      - in_battle: whether a battle is active
      - battle_type: "wild", "trainer", "double", "link", or "none"
      - battle_outcome: result if battle has ended ("won", "lost", "ran", etc.)
      - battlers_count: number of active combatants (2 singles, 4 doubles)
    """
    return _get_reader().read_battle_state()


@mcp.tool()
def get_opponent_pokemon() -> list[dict]:
    """Get the opponent's active Pokemon data during a battle.

    Reads from the gBattleMons array for live in-battle stats. Returns
    the opponent's active Pokemon (slot 1) in singles, or both opponent
    slots (1 and 3) in doubles. Only meaningful when in_battle is true.

    Returns:
        List of dicts with species, level, HP, stats, moves, and status
        for each opponent Pokemon currently in battle.
    """
    battle = _get_reader().read_battle_state()
    if not battle["in_battle"]:
        return []

    result = []
    # In singles, opponent is slot 1. In doubles, also slot 3.
    opponent_slots = [1]
    if battle["battlers_count"] >= 4:
        opponent_slots.append(3)

    for slot in opponent_slots:
        mon = _get_reader().read_battle_pokemon(slot)
        if mon and mon["species_id"] != 0:
            result.append(mon)
    return result


@mcp.tool()
def get_opponent_party() -> list[dict]:
    """Get the opponent trainer's full party during a trainer battle.

    Reads the enemy party data area (all 6 slots). Useful for scouting
    what Pokemon a trainer has beyond the one currently in battle.
    Only meaningful during trainer battles.

    Returns:
        List of parsed Pokemon dicts with species, level, HP, stats, moves.
    """
    return _get_reader().read_opponent_party()


# ==========================================================================
# MENU TOOLS
# ==========================================================================
# Tools for reading and navigating the START menu.

@mcp.tool()
def get_start_menu_state() -> dict:
    """Get the current START menu cursor position and displayed items.

    The start menu remembers cursor position between opens. This tool
    reads the cursor position and the displayed menu order so you know
    exactly which option is highlighted and how to navigate to any target.

    Returns:
        Dict with cursor_pos, num_items, menu_order (list of option names
        like "POKEDEX", "POKEMON", "BAG", etc.), and selected_item.
    """
    return _get_reader().read_start_menu_state()


@mcp.tool()
def save_game() -> str:
    """Perform an in-game save by navigating the START menu.

    This navigates the in-game menu to Save (not an emulator save state).
    It opens the START menu, resets cursor to the top, navigates down to
    Save, and confirms the save dialog. Takes ~5 seconds of game time.

    The menu order is: Pokedex(0), Pokemon(1), Bag(2), Player(3), Save(4), Option(5), Exit(6).
    To reliably reach Save, we reset to top first then press DOWN 4 times.

    Returns:
        Status message indicating save was initiated.
    """
    client = _get_client()

    # Step 1: Open the START menu
    client.press_button("START", 10)
    client.run_frames(30)  # Wait for menu animation

    # Step 2: Reset cursor to top by pressing UP enough times (max 8 items)
    for _ in range(8):
        client.press_button("UP", 6)
        client.run_frames(8)

    # Step 3: Navigate down to Save (index 4 in standard menu order)
    for _ in range(4):
        client.press_button("DOWN", 6)
        client.run_frames(8)

    # Step 4: Press A to select Save
    client.press_button("A", 10)
    client.run_frames(60)  # Wait for "Would you like to save?" dialog

    # Step 5: Press A to confirm save
    client.press_button("A", 10)
    client.run_frames(120)  # Wait for save to write (~2 seconds)

    # Step 6: Press A to confirm overwrite (if previous save exists)
    client.press_button("A", 10)
    client.run_frames(120)  # Wait for save completion

    # Step 7: Press A to dismiss "saved the game" message
    client.press_button("A", 10)
    client.run_frames(30)

    # Step 8: Press B to close any remaining menu
    client.press_button("B", 10)
    client.run_frames(20)

    return "In-game save completed. Use get_screenshot to verify the save was successful."


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
