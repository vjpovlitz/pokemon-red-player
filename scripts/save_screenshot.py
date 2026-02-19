"""
save_screenshot.py — Screenshot saving with session-based labeling and timestamps.

This module manages saving mGBA screenshots to disk in a structured way:
  - Each Claude Code session gets a unique session ID (timestamp-based)
  - Screenshots are saved with the pattern: {session_id}_{sequence}_{label}.png
  - A monotonic counter ensures ordering within a session
  - All screenshots go to the project's screenshots/ directory

The saved PNG files can be read natively by Claude Code using the Read tool,
which supports image viewing. This solves the timeout issue that occurs when
trying to pass large base64 data URIs directly through MCP.

Usage as a module:
    from save_screenshot import ScreenshotManager
    mgr = ScreenshotManager()
    path = mgr.save(b64_data, label="battle_start")

Usage from CLI:
    python save_screenshot.py <base64_data_uri> [label]
"""

import base64
import os
import sys
from datetime import datetime


# Default directory for all screenshots (project_root/screenshots/)
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")


class ScreenshotManager:
    """Manages screenshot saving with session-scoped naming and sequencing.

    Each instance represents a single session. Screenshots are numbered
    sequentially within the session for easy chronological ordering.

    Naming format: {session_id}_{sequence:03d}_{label}.png
    Example:       20260218_143052_001_battle_start.png

    Attributes:
        session_id: Timestamp string identifying this session (YYYYMMDD_HHMMSS).
        screenshots_dir: Absolute path to the screenshots output directory.
        _counter: Monotonically increasing sequence number within this session.
    """

    def __init__(self, screenshots_dir: str | None = None):
        """Initialize a new screenshot session.

        Args:
            screenshots_dir: Override the default screenshots directory.
                             Defaults to project_root/screenshots/.
        """
        # Session ID is set once at creation time — all screenshots in this
        # session share the same prefix for easy grouping/filtering
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshots_dir = os.path.abspath(screenshots_dir or SCREENSHOTS_DIR)
        self._counter = 0

        # Ensure the output directory exists
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def save(self, b64_data: str, label: str = "screenshot") -> str:
        """Save a base64-encoded PNG screenshot to disk.

        Args:
            b64_data: Base64 string of the PNG image. May optionally include
                      a data URI prefix (data:image/png;base64,...) which will
                      be stripped automatically.
            label: Descriptive label for this screenshot (e.g. "battle_start",
                   "menu_open", "route_1"). Spaces are converted to underscores.
                   Default is "screenshot".

        Returns:
            Absolute file path to the saved PNG file. This path can be passed
            directly to Claude Code's Read tool for native image viewing.
        """
        self._counter += 1

        # Sanitize the label: lowercase, replace spaces with underscores,
        # remove any characters that aren't alphanumeric or underscore
        safe_label = label.lower().replace(" ", "_")
        safe_label = "".join(c for c in safe_label if c.isalnum() or c == "_")

        # Build filename: session_sequence_label.png
        filename = f"{self.session_id}_{self._counter:03d}_{safe_label}.png"
        filepath = os.path.join(self.screenshots_dir, filename)

        # Strip the data URI prefix if present (e.g. "data:image/png;base64,")
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]

        # Decode and write the PNG binary data
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(b64_data))

        return os.path.abspath(filepath)


# ---------------------------------------------------------------------------
# CLI entry point (for standalone testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python save_screenshot.py <base64_data_uri> [label]")
        sys.exit(1)

    data = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else "screenshot"
    mgr = ScreenshotManager()
    path = mgr.save(data, label)
    print(f"Saved: {path}")
