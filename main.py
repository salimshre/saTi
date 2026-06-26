"""Runnable entry point for the alarm clock application."""

from __future__ import annotations

import tkinter as tk

from models import AlarmManager, SettingsManager, StopwatchManager, TimerManager
from ui.app import AlarmClockApp
from ui.themes import ThemeManager


def main() -> None:
    root = tk.Tk()
    settings = SettingsManager()
    theme_manager = ThemeManager(settings)
    app = AlarmClockApp(
        root=root,
        settings=settings,
        alarm_manager=AlarmManager(settings),
        timer_manager=TimerManager(),
        stopwatch_manager=StopwatchManager(),
        theme_manager=theme_manager,
    )
    app.theme_manager.apply_all(root)
    root.mainloop()


if __name__ == "__main__":
    main()