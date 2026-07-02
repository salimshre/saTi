from __future__ import annotations

from models.timer import Timer
from ui.floating.countdown import CountdownWindow


class FakeRingController:
    def __init__(self):
        self.stopped = []

    def stop(self, name=""):
        self.stopped.append(name)


def test_countdown_overdue_popup_mute_stops_sound_without_closing(monkeypatch):
    fake_ring = FakeRingController()
    monkeypatch.setattr("ui.floating.countdown.ring_controller", fake_ring)
    popup = object()
    win = CountdownWindow.__new__(CountdownWindow)
    win.timer = Timer(label="Tea", duration=1)
    win.overdue_popup = popup
    win._muted = False

    win._mute_overdue_popup()

    assert win._muted is True
    assert fake_ring.stopped == ["Tea"]
    assert win.overdue_popup is popup
