"""Runtime-generated app icon helpers."""

from __future__ import annotations

import tkinter as tk


def apply_app_icon(root: tk.Tk) -> None:
    """Create a simple 16x16 icon and set it as the window icon."""
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