"""
mgba_client.py — Python TCP client for the mGBA Lua server.

This module provides the MGBAClient class, which connects to the Lua TCP
server running inside mGBA (mgba_server.lua) over localhost:5555. It
translates Python method calls into JSON commands, sends them over the
socket, and returns parsed responses.

Architecture:
    Python (this) ──TCP JSON──> Lua server (mgba_server.lua) ──native API──> mGBA

Protocol:
    - Newline-delimited JSON over TCP
    - Each request gets a monotonically increasing "id" field
    - Responses are matched back to requests by their "id"
    - All responses have {"ok": true/false, ...}

Usage:
    with MGBAClient() as client:
        client.press_button("A", frames=10)
        hp = client.read16(0x02024088)
        screenshot_b64 = client.screenshot()
"""

import json
import socket
from typing import Any


class MGBAClient:
    """TCP client that talks to the mGBA Lua scripting server.

    Provides typed Python methods for every command the Lua server supports:
    memory reads/writes, button presses, screenshots, save states, and
    frame advance. Handles automatic reconnection on disconnect.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5555, timeout: float = 5.0):
        """Initialize the client.

        Args:
            host: Hostname of the mGBA Lua server (default localhost).
            port: TCP port (must match PORT in mgba_server.lua, default 5555).
            timeout: Socket timeout in seconds for reads/connects.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None  # Active TCP socket
        self._buffer = b""                        # Incomplete data from previous reads
        self._request_id = 0                      # Monotonic counter for request correlation

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self):
        """Establish a TCP connection to the mGBA Lua server.

        If a connection already exists, it is closed first. Resets the
        internal read buffer.
        """
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.host, self.port))
        self._buffer = b""

    def disconnect(self):
        """Close the TCP connection."""
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def _ensure_connected(self):
        """Lazily connect if not already connected."""
        if self._sock is None:
            self.connect()

    # ------------------------------------------------------------------
    # Core request/response
    # ------------------------------------------------------------------

    def _send_command(self, cmd: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON command and block until the matching response arrives.

        Each command gets a unique "id" field so we can correlate responses
        even if the server sends them out of order (e.g., deferred runFrames).

        If the send fails (broken pipe), attempts a single reconnect.
        """
        self._ensure_connected()
        self._request_id += 1
        cmd["id"] = self._request_id

        # Serialize to newline-terminated JSON
        data = json.dumps(cmd) + "\n"
        try:
            self._sock.sendall(data.encode("utf-8"))
        except (OSError, BrokenPipeError):
            # Connection dropped — try reconnecting once before giving up
            self.connect()
            self._sock.sendall(data.encode("utf-8"))

        return self._read_response(self._request_id)

    def _read_response(self, request_id: int) -> dict[str, Any]:
        """Read from the socket until we find the response matching our request ID.

        Responses are newline-delimited JSON. We buffer incoming data and
        scan for complete lines. If a response doesn't match our ID (could
        happen if the server sends unsolicited messages), we skip it.
        """
        while True:
            # Check if we already have a complete line in the buffer
            nl = self._buffer.find(b"\n")
            if nl >= 0:
                line = self._buffer[:nl]
                self._buffer = self._buffer[nl + 1:]
                resp = json.loads(line.decode("utf-8"))
                # Match by request ID, or accept responses without an ID
                if resp.get("id") == request_id or "id" not in resp:
                    return resp
                continue  # Not our response; keep reading

            # No complete line yet — read more data from the socket
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("mGBA server closed connection")
            self._buffer += chunk

    # ------------------------------------------------------------------
    # Memory read operations
    # ------------------------------------------------------------------

    def read8(self, addr: int) -> int:
        """Read a single byte (8-bit) from GBA memory."""
        resp = self._send_command({"cmd": "read8", "addr": addr})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "read8 failed"))
        return resp["value"]

    def read16(self, addr: int) -> int:
        """Read a 16-bit little-endian value from GBA memory."""
        resp = self._send_command({"cmd": "read16", "addr": addr})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "read16 failed"))
        return resp["value"]

    def read32(self, addr: int) -> int:
        """Read a 32-bit little-endian value from GBA memory."""
        resp = self._send_command({"cmd": "read32", "addr": addr})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "read32 failed"))
        return resp["value"]

    def read_range(self, addr: int, length: int) -> bytes:
        """Read N contiguous bytes from GBA memory.

        Returns a Python bytes object. The Lua server returns the data as a
        hex string which we decode here.
        """
        resp = self._send_command({"cmd": "readRange", "addr": addr, "length": length})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "readRange failed"))
        return bytes.fromhex(resp["value"])

    # ------------------------------------------------------------------
    # Memory write operations
    # ------------------------------------------------------------------

    def write8(self, addr: int, value: int):
        """Write a single byte to GBA memory."""
        resp = self._send_command({"cmd": "write8", "addr": addr, "value": value})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "write8 failed"))

    def write16(self, addr: int, value: int):
        """Write a 16-bit value to GBA memory (little-endian)."""
        resp = self._send_command({"cmd": "write16", "addr": addr, "value": value})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "write16 failed"))

    def write32(self, addr: int, value: int):
        """Write a 32-bit value to GBA memory (little-endian)."""
        resp = self._send_command({"cmd": "write32", "addr": addr, "value": value})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "write32 failed"))

    # ------------------------------------------------------------------
    # Button input
    # ------------------------------------------------------------------

    def press_button(self, button: str, frames: int = 10):
        """Queue a button press for N frames in the emulator.

        The button is held down for the specified number of frames. This
        returns immediately — the Lua server handles the frame-by-frame
        injection asynchronously.

        Args:
            button: Button name — A, B, START, SELECT, UP, DOWN, LEFT, RIGHT, L, R
            frames: How many frames to hold the button (default 10, ~167ms at 60 FPS)
        """
        resp = self._send_command({"cmd": "press", "button": button, "frames": frames})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "press failed"))

    def get_keys(self) -> list[str]:
        """Get the list of buttons currently held down by the player."""
        resp = self._send_command({"cmd": "getKeys"})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "getKeys failed"))
        return resp["value"]

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    def screenshot(self) -> str:
        """Capture the current emulator frame as a base64-encoded PNG string."""
        resp = self._send_command({"cmd": "screenshot"})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "screenshot failed"))
        return resp["value"]

    # ------------------------------------------------------------------
    # Save states
    # ------------------------------------------------------------------

    def save_state(self, slot: int = 1):
        """Save the emulator state to a numbered slot (1-9)."""
        resp = self._send_command({"cmd": "saveState", "slot": slot})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "saveState failed"))

    def load_state(self, slot: int = 1):
        """Load an emulator state from a numbered slot (1-9)."""
        resp = self._send_command({"cmd": "loadState", "slot": slot})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "loadState failed"))

    # ------------------------------------------------------------------
    # Frame advance
    # ------------------------------------------------------------------

    def run_frames(self, count: int = 1):
        """Advance emulation by N frames, blocking until complete.

        This is a deferred command — the Lua server only sends the response
        after the requested number of frames have actually elapsed. At 60 FPS,
        60 frames ≈ 1 second of game time.
        """
        resp = self._send_command({"cmd": "runFrames", "count": count})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "runFrames failed"))

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def ping(self) -> str:
        """Connectivity check. Returns "pong" if the server is reachable."""
        resp = self._send_command({"cmd": "ping"})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "ping failed"))
        return resp["value"]

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
