"""Centralise file paths and application-wide constants."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _workspace_fallback_dir() -> Path:
    return Path(__file__).resolve().parents[1] / ".sati_data"


def _platform_config_dir() -> Path:
    try:
        from platformdirs import user_config_dir

        return Path(user_config_dir("SaTi", appauthor=False))
    except Exception:
        home = Path.home()
        if os.name == "nt":
            appdata = os.environ.get("APPDATA")
            base = Path(appdata) if appdata else home / "AppData" / "Roaming"
            return base / "SaTi"
        return home / ".config" / "sati"


def _ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _default_config_dir() -> str:
    preferred = _platform_config_dir()
    if _ensure_dir(preferred):
        return str(preferred)

    fallback = _workspace_fallback_dir()
    _ensure_dir(fallback)
    return str(fallback)


CONFIG_DIR       = _default_config_dir()
SETTINGS_FILE    = os.path.join(CONFIG_DIR, "settings.json")
ALARMS_FILE      = os.path.join(CONFIG_DIR, "alarms.json")
TIMERS_FILE      = os.path.join(CONFIG_DIR, "timers.json")
STOPWATCHES_FILE = os.path.join(CONFIG_DIR, "stopwatches.json")
SOUND_DIR        = os.path.join(CONFIG_DIR, "sounds")


def _project_sound_dir() -> Path:
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir) / "sounds"
    return Path(__file__).resolve().parents[1] / "sounds"


PROJECT_SOUND_DIR = _project_sound_dir()
DEFAULT_ALARM_SOUND = PROJECT_SOUND_DIR / "ring1.wav"

# Create directories on first import
for _d in (CONFIG_DIR, SOUND_DIR):
    os.makedirs(_d, exist_ok=True)

DEFAULT_SETTINGS = {
    "theme":             "Dark",
    "transparency":      0.85,
    "volume":            100,
    "alarm_sound":       str(DEFAULT_ALARM_SOUND) if DEFAULT_ALARM_SOUND.exists() else None,
    "increasing_volume": False,
    "snooze_minutes":    10,
    "tick_threshold":    10,
    "always_on_top":     True,
    "font_family":       "Arial",
    "font_size":         12,
    "enable_notifications": True,
    "minimize_to_tray":  True,
    "ring_duration_minutes": 5,   # <--- NEW
}
