from __future__ import annotations

from models.alarm import Alarm
from ui.alarm_popup import AlarmPopup


class FakeSettings:
    def get(self, key, default=None):
        if key == "alarm_sound":
            return "default.wav"
        if key == "volume":
            return 100
        return default


class FakeRingController:
    def __init__(self):
        self.started = []
        self.stopped = []

    def start(self, settings, source=None, **kwargs):
        self.started.append((settings, source, kwargs))

    def stop(self, name=""):
        self.stopped.append(name)


def test_alarm_without_actions_still_starts_default_sound(monkeypatch):
    fake_ring = FakeRingController()
    monkeypatch.setattr("ui.alarm_popup.ring_controller", fake_ring)
    popup = AlarmPopup.__new__(AlarmPopup)
    popup.alarm = Alarm(name="Wake", actions=[])
    popup.settings = FakeSettings()

    popup.run_actions()

    assert len(fake_ring.started) == 1
    _settings, source, kwargs = fake_ring.started[0]
    assert source is None
    assert kwargs == {"loop": False, "name": "Wake"}


def test_alarm_with_play_sound_action_does_not_double_start(monkeypatch):
    fake_ring = FakeRingController()
    monkeypatch.setattr("ui.alarm_popup.ring_controller", fake_ring)
    popup = AlarmPopup.__new__(AlarmPopup)
    popup.alarm = Alarm(name="Wake", sound_file="custom.wav", actions=[{"type": "play_sound"}])
    popup.settings = FakeSettings()

    popup.run_actions()

    assert len(fake_ring.started) == 1
    _settings, source, kwargs = fake_ring.started[0]
    assert source == "custom.wav"
    assert kwargs == {"loop": False, "name": "Wake"}


def test_alarm_mute_stops_sound_without_dismissal(monkeypatch):
    fake_ring = FakeRingController()
    monkeypatch.setattr("ui.alarm_popup.ring_controller", fake_ring)
    popup = AlarmPopup.__new__(AlarmPopup)
    popup.alarm = Alarm(name="Wake")

    popup.mute()

    assert popup._muted is True
    assert fake_ring.stopped == ["Wake"]


def test_muted_repeating_alarm_does_not_start_again(monkeypatch):
    fake_ring = FakeRingController()
    monkeypatch.setattr("ui.alarm_popup.ring_controller", fake_ring)
    popup = AlarmPopup.__new__(AlarmPopup)
    popup.alarm = Alarm(name="Wake", sound_file="custom.wav")
    popup._muted = True

    popup.repeat_sound()

    assert fake_ring.started == []
