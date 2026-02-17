"""Helper to save a base64 screenshot from mGBA MCP to disk."""
import base64
import sys
import os
from datetime import datetime

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")

def save(data_uri: str, name: str | None = None) -> str:
    """Save a data:image/png;base64,... string to screenshots/ and return the path."""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    if name is None:
        name = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    # Strip data URI prefix
    b64 = data_uri.split(",", 1)[1] if "," in data_uri else data_uri
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    return os.path.abspath(path)

if __name__ == "__main__":
    # Usage: python save_screenshot.py <base64_data_uri> [name]
    data = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    print(save(data, name))
