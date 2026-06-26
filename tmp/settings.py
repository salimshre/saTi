"""
models/settings.py
Persistent settings manager backed by a JSON file.
"""
from core.config import DEFAULT_SETTINGS, SETTINGS_FILE
from core.persistence import load_json_file, save_json_file


class SettingsManager:
    def __init__(self):
        self.settings: dict = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self) -> None:
        self.settings.update(load_json_file(SETTINGS_FILE, {}, "settings"))

    def save(self) -> None:
        save_json_file(SETTINGS_FILE, self.settings, "settings")

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key: str, value) -> None:
        self.settings[key] = value
        self.save()
