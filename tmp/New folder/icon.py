"""Runtime-generated app icon helpers."""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
_logo_image = None  # cache

def get_logo_photoimage() -> tk.PhotoImage | None:
    """Load and return a PhotoImage of the logo, or None if not available."""
    global _logo_image
    if _logo_image is not None:
        return _logo_image
    logo_path = ASSETS_DIR / "logo.png"
    if logo_path.exists():
        try:
            _logo_image = tk.PhotoImage(file=str(logo_path))
            return _logo_image
        except Exception:
            pass
    return None

def apply_app_icon(root: tk.Tk) -> None:
    """Set the window icon using a custom logo if available, else fallback to generated icon."""
    image = get_logo_photoimage()
    if image is None:
        # Fallback: generate a simple icon
        image = tk.PhotoImage(width=16, height=16)
        for x in range(16):
            for y in range(16):
                image.put("#1e1e1e", (x, y))
        for x in range(2, 14):
            for y in range(2, 14):
                if (x - 8) ** 2 + (y - 8) ** 2 <= 34:
                    image.put("#00ffcc", (x, y))
        for i in range(4, 13):
            image.put("#001b18", (8, i))
        for i in range(8, 12):
            image.put("#001b18", (i, 8))

    root._sati_icon = image  # type: ignore[attr-defined]
    try:
        root.iconphoto(True, image)
    except Exception:
        pass
        