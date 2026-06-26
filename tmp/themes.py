"""
ui/themes.py
Theme palette definitions and ThemeManager.
"""
import tkinter as tk
from tkinter import ttk

THEMES: dict[str, dict] = {
    "Dark": {
        "bg": "#1e1e1e", "fg": "#00ffcc", "accent": "#00ffcc",
        "canvas_bg": "#000000",
        "btn_bg": "#333", "btn_fg": "white",
        "list_bg": "#2a2a2a", "list_fg": "white",
    },
    "Light": {
        "bg": "#f0f0f0", "fg": "#007acc", "accent": "#007acc",
        "canvas_bg": "#ffffff",
        "btn_bg": "#ddd", "btn_fg": "black",
        "list_bg": "white", "list_fg": "black",
    },
    "Neon": {
        "bg": "#0f0f23", "fg": "#39ff14", "accent": "#ff00ff",
        "canvas_bg": "#00001a",
        "btn_bg": "#2a0040", "btn_fg": "#39ff14",
        "list_bg": "#1a0025", "list_fg": "#39ff14",
    },
    "Ocean": {
        "bg": "#002b36", "fg": "#2aa198", "accent": "#268bd2",
        "canvas_bg": "#073642",
        "btn_bg": "#073642", "btn_fg": "#93a1a1",
        "list_bg": "#002b36", "list_fg": "#93a1a1",
    },
    "Red": {
        "bg": "#331111", "fg": "#ff4444", "accent": "#ff8888",
        "canvas_bg": "#220000",
        "btn_bg": "#440000", "btn_fg": "#ffaaaa",
        "list_bg": "#331111", "list_fg": "#ff9999",
    },
}


class ThemeManager:
    def __init__(self, settings):
        self.settings = settings
        self.current: dict = THEMES[settings.get("theme", "Dark")]

    # ------------------------------------------------------------------
    def apply(self, widget, item_type: str = "default") -> None:
        """Apply the current theme palette to *widget*."""
        style = ttk.Style()
        style.theme_use("clam")

        bg      = self.current["bg"]
        fg      = self.current["fg"]
        btn_bg  = self.current["btn_bg"]
        btn_fg  = self.current["btn_fg"]
        list_bg = self.current["list_bg"]
        list_fg = self.current["list_fg"]

        _map = {
            "TButton":      lambda: style.configure("TButton", background=btn_bg, foreground=btn_fg),
            "TLabel":       lambda: style.configure("TLabel",  background=bg,     foreground=fg),
            "TFrame":       lambda: style.configure("TFrame",  background=bg),
            "TNotebook":    lambda: (
                style.configure("TNotebook",     background=bg, foreground=fg),
                style.configure("TNotebook.Tab", background=btn_bg, foreground=btn_fg, padding=[10, 4]),
            ),
            "Treeview":     lambda: style.configure("Treeview", background=list_bg,
                                                    foreground=list_fg, fieldbackground=list_bg),
            "TEntry":       lambda: style.configure("TEntry",    fieldbackground=btn_bg, foreground=btn_fg),
            "TScale":       lambda: style.configure("TScale",    background=bg, foreground=fg),
            "TCheckbutton": lambda: style.configure("TCheckbutton", background=bg, foreground=fg),
        }
        if item_type in _map:
            _map[item_type]()

        if isinstance(widget, (tk.Tk, tk.Toplevel)):
            widget.configure(bg=bg)
        if isinstance(widget, tk.Canvas):
            widget.configure(bg=self.current.get("canvas_bg", "black"))

    def apply_all(self, root: tk.Tk) -> None:
        """Re-style the whole app after a theme change."""
        style = ttk.Style()
        style.theme_use("clam")
        for item_type in ("TButton", "TLabel", "TFrame", "TNotebook",
                          "Treeview", "TEntry", "TScale", "TCheckbutton"):
            self.apply(root, item_type)
        for win in root.winfo_children():
            if isinstance(win, (tk.Tk, tk.Toplevel)):
                win.configure(bg=self.current["bg"])