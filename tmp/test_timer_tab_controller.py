from __future__ import annotations

from models import Timer
from ui.tabs.timer_tab import TimerTab


class FakeSettings:
    def get(self, key, default=None):
        if key == "tick_threshold":
            return 10
        return default


class FakeTimerManager:
    def __init__(self, timers):
        self.timers = timers
        self.save_count = 0

    def get(self, timer_id):
        return next((timer for timer in self.timers if timer.id == timer_id), None)

    def save(self):
        self.save_count += 1


class FakeTree:
    def __init__(self, ids):
        self.ids = list(ids)
        self.items = {}

    def get_children(self):
        return tuple(self.ids)

    def item(self, item_id, values):
        self.items[item_id] = values


class FakeWindow:
    def __init__(self, timer):
        self.timer = timer
        self.handled = []
        self.time_left = None
        self.paused = None

    def _handle_completion(self, completed_at=None):
        self.handled.append(completed_at)


class FakeApp:
    def __init__(self, timers):
        self.root = object()
        self.settings = FakeSettings()
        self.theme_manager = object()
        self.timer_manager = FakeTimerManager(timers)
        self.open_timer_windows = {}


def make_timer_tab(app):
    tab = TimerTab.__new__(TimerTab)
    tab.app = app
    tab.tree = FakeTree(timer.id for timer in app.timer_manager.timers)
    return tab


def test_refresh_runtime_state_opens_completion_window_once(monkeypatch):
    timer = Timer(id="timer-1", label="Tea", duration=30, last_started_at=100.0)
    timer.remaining = 5
    timer.status = "running"
    app = FakeApp([timer])
    tab = make_timer_tab(app)
    opened = []

    def fake_open(self, timer_obj):
        win = FakeWindow(timer_obj)
        self.app.open_timer_windows[timer_obj.id] = win
        opened.append(win)
        return win

    monkeypatch.setattr(TimerTab, "_open_countdown_window", fake_open)

    tab.refresh_runtime_state(110.0)
    tab.refresh_runtime_state(120.0)

    assert timer.status == "completed"
    assert timer.completed_at == 105.0
    assert len(opened) == 1
    assert opened[0].handled == [105.0]
    assert app.timer_manager.save_count == 1
    assert tab.tree.items[timer.id][1:3] == ("00:00", "Completed")
