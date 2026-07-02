"""
ui/dialogs/settings_dialog.py
Full settings dialog with Appearance and Behaviour tabs.
"""
import tkinter as tk
from tkinter import filedialog, ttk

from core.config import PROJECT_SOUND_DIR
from core.ring import ring_controller
from ui.themes import THEMES


class SettingsDialog(tk.Toplevel):
    def __init__(self, master, settings, theme_manager,
                 apply_callback=None, app=None):
        super().__init__(master)
        self.title("Settings")
        self.settings       = settings
        self.theme_manager  = theme_manager
        self.apply_callback = apply_callback
        self.app            = app
        self.bundled_sounds = self._load_bundled_sounds()
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # ── Appearance tab ─────────────────────────────────────────────
        appear = ttk.Frame(nb)
        nb.add(appear, text="Appearance")

        ttk.Label(appear, text="Theme:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.theme_var = tk.StringVar(value=settings.get("theme"))
        ttk.Combobox(appear, textvariable=self.theme_var,
                     values=list(THEMES.keys()), state="readonly").grid(
            row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(appear, text="Transparency:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.trans_var = tk.DoubleVar(value=settings.get("transparency"))
        ttk.Scale(appear, from_=0.1, to=1.0, variable=self.trans_var,
                  command=self._on_trans_change).grid(
            row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(appear, text="Font family:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.font_var = tk.StringVar(value=settings.get("font_family"))
        ttk.Entry(appear, textvariable=self.font_var).grid(
            row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(appear, text="Font size:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.font_size_var = tk.IntVar(value=settings.get("font_size"))
        tk.Spinbox(appear, from_=8, to=40, textvariable=self.font_size_var, width=4).grid(
            row=3, column=1, sticky="w", padx=5, pady=5)

        self.always_on_top_var = tk.BooleanVar(value=settings.get("always_on_top"))
        tk.Checkbutton(appear, text="Always on top",
                       variable=self.always_on_top_var).grid(
            row=4, column=0, columnspan=2, pady=10)

        # ── Behaviour tab ──────────────────────────────────────────────
        behave = ttk.Frame(nb)
        nb.add(behave, text="Behaviour")

        ttk.Label(behave, text="Volume:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.vol_var = tk.IntVar(value=settings.get("volume"))
        ttk.Scale(behave, from_=0, to=100, variable=self.vol_var).grid(
            row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(behave, text="Snooze (minutes):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.snooze_var = tk.IntVar(value=settings.get("snooze_minutes"))
        tk.Spinbox(behave, from_=1, to=60, textvariable=self.snooze_var, width=4).grid(
            row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(behave, text="Tick threshold (sec):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.tick_var = tk.IntVar(value=settings.get("tick_threshold"))
        tk.Spinbox(behave, from_=0, to=60, textvariable=self.tick_var, width=4).grid(
            row=2, column=1, sticky="w", padx=5, pady=5)

        self.incr_vol_var = tk.BooleanVar(value=settings.get("increasing_volume"))
        tk.Checkbutton(behave, text="Increasing volume",
                       variable=self.incr_vol_var).grid(row=3, column=0, columnspan=2, pady=10)

        self.notify_var = tk.BooleanVar(value=settings.get("enable_notifications", True))
        tk.Checkbutton(behave, text="Desktop notifications",
                       variable=self.notify_var).grid(row=4, column=0, columnspan=2, pady=4)

        self.tray_var = tk.BooleanVar(value=settings.get("minimize_to_tray", True))
        tk.Checkbutton(behave, text="Minimize to tray on close",
                       variable=self.tray_var).grid(row=5, column=0, columnspan=2, pady=4)

        # ---- Blink settings (new) ----
        # Enable/disable blinking
        self.blink_enabled_var = tk.BooleanVar(value=settings.get("blink_enabled", True))
        tk.Checkbutton(behave, text="Enable blinking for overdue timers",
                       variable=self.blink_enabled_var).grid(
            row=6, column=0, columnspan=2, sticky="w", padx=20, pady=4)

        ttk.Label(behave, text="Blink interval (ms):").grid(
            row=7, column=0, sticky="e", padx=5, pady=5)
        self.blink_interval_var = tk.IntVar(value=settings.get("blink_interval_ms", 500))
        tk.Spinbox(behave, from_=100, to=2000, textvariable=self.blink_interval_var,
                   width=6).grid(row=7, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(behave, text="Blink max duration (seconds):").grid(
            row=8, column=0, sticky="e", padx=5, pady=5)
        self.blink_max_var = tk.IntVar(value=settings.get("blink_max_seconds", 0))
        tk.Spinbox(behave, from_=0, to=3600, textvariable=self.blink_max_var,
                   width=6).grid(row=8, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(behave, text="(0 = infinite)").grid(
            row=8, column=2, sticky="w", padx=5, pady=5)

        behave.columnconfigure(1, weight=1)

        # ── Sound tab ─────────────────────────────────────────────────
        sound_tab = ttk.Frame(nb)
        nb.add(sound_tab, text="Sound")

        ttk.Label(sound_tab, text="Alarm sound:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        sound_frame = ttk.Frame(sound_tab)
        sound_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.sound_var = tk.StringVar(value=settings.get("alarm_sound") or "")
        self.sound_choice_var = tk.StringVar(value=self._sound_choice_label(self.sound_var.get()))
        self.sound_choice = ttk.Combobox(
            sound_frame,
            textvariable=self.sound_choice_var,
            values=["Custom / fallback"] + list(self.bundled_sounds.keys()),
            state="readonly",
            width=18,
        )
        self.sound_choice.pack(side=tk.LEFT, padx=(0, 5))
        self.sound_choice.bind("<<ComboboxSelected>>", self._on_sound_choice)
        ttk.Entry(sound_frame, textvariable=self.sound_var, width=32).pack(side=tk.LEFT, fill="x", expand=True)
        ttk.Button(sound_frame, text="Browse", command=self._browse_sound).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(sound_frame, text="Clear", command=self._clear_sound).pack(side=tk.LEFT, padx=(5, 0))

        sound_buttons = ttk.Frame(sound_tab)
        sound_buttons.grid(row=1, column=0, columnspan=2, pady=(0, 8))
        ttk.Button(sound_buttons, text="Test Sound", command=self._test_sound).pack(side=tk.LEFT, padx=5)
        ttk.Button(sound_buttons, text="Stop Sound", command=ring_controller.stop).pack(side=tk.LEFT, padx=5)

        # --- Ring duration ---
        ttk.Label(sound_tab, text="Ring duration (minutes):").grid(
            row=2, column=0, sticky="e", padx=5, pady=5)
        self.ring_duration_var = tk.IntVar(value=settings.get("ring_duration_minutes", 5))
        tk.Spinbox(
            sound_tab, from_=0, to=60, textvariable=self.ring_duration_var, width=4
        ).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(sound_tab, text="(0 = infinite)").grid(
            row=2, column=2, sticky="w", padx=5, pady=5)

        sound_tab.columnconfigure(1, weight=1)

        # ── Buttons ────────────────────────────────────────────────────
        bf = ttk.Frame(self)
        bf.pack(pady=10, fill="x")
        ttk.Button(bf, text="Save",   command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bf, text="Cancel", command=self._close).pack(side=tk.RIGHT, padx=5)

    def _on_trans_change(self, value) -> None:
        if self.apply_callback:
            self.apply_callback(float(value))

    def _browse_sound(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose Alarm Sound",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.ogg *.flac *.m4a *.aac"),
                ("Wave files", "*.wav"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.sound_var.set(path)
            self.sound_choice_var.set(self._sound_choice_label(path))

    def _load_bundled_sounds(self) -> dict[str, str]:
        if not PROJECT_SOUND_DIR.exists():
            return {}
        sounds = {}
        for path in sorted(PROJECT_SOUND_DIR.glob("*")):
            if path.suffix.lower() in {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}:
                sounds[path.name] = str(path)
        return sounds

    def _sound_choice_label(self, path: str) -> str:
        for label, bundled_path in self.bundled_sounds.items():
            if path == bundled_path:
                return label
        return "Custom / fallback"

    def _on_sound_choice(self, _event=None) -> None:
        label = self.sound_choice_var.get()
        if label in self.bundled_sounds:
            self.sound_var.set(self.bundled_sounds[label])
        else:
            self.sound_var.set("")

    def _clear_sound(self) -> None:
        self.sound_var.set("")
        self.sound_choice_var.set("Custom / fallback")

    def _test_sound(self) -> None:
        ring_controller.stop()
        ring_controller.start(
            self.settings,
            self.sound_var.get() or None,
            loop=True,
            volume=self.vol_var.get(),
            use_default_source=False,
            name="settings_preview",
        )

    def save(self) -> None:
        self.settings.set("theme",            self.theme_var.get())
        self.settings.set("transparency",     self.trans_var.get())
        self.settings.set("volume",           self.vol_var.get())
        self.settings.set("alarm_sound",      self.sound_var.get() or None)
        self.settings.set("snooze_minutes",   self.snooze_var.get())
        self.settings.set("tick_threshold",   self.tick_var.get())
        self.settings.set("increasing_volume", self.incr_vol_var.get())
        self.settings.set("always_on_top",    self.always_on_top_var.get())
        self.settings.set("font_family",      self.font_var.get())
        self.settings.set("font_size",        self.font_size_var.get())
        self.settings.set("enable_notifications", self.notify_var.get())
        self.settings.set("minimize_to_tray", self.tray_var.get())
        self.settings.set("ring_duration_minutes", self.ring_duration_var.get())
        # Blink settings
        self.settings.set("blink_enabled",    self.blink_enabled_var.get())
        self.settings.set("blink_interval_ms", self.blink_interval_var.get())
        self.settings.set("blink_max_seconds", self.blink_max_var.get())

        self.theme_manager.current = THEMES[self.theme_var.get()]
        if self.app:
            self.app.theme_manager.apply_all(self.app.root)
            # Apply new blink settings to all open countdown windows
            self.app.update_all_timer_blink_settings()
        if self.apply_callback:
            self.apply_callback(self.trans_var.get())
        self._close()

    def _close(self) -> None:
        ring_controller.stop()
        self.destroy()

        