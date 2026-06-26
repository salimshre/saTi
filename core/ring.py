"""Shared alarm and timer ringing helpers."""

from __future__ import annotations

from core.logger import activity_log
from core.sound import player


class RingController:
    """Centralize sound start/stop behavior for alarms and countdown timers."""

    def __init__(self) -> None:
        self._active_names: set[str] = set()

    def start(
        self,
        settings,
        source: str | None = None,
        *,
        loop: bool = True,
        radio: bool = False,
        volume: int | None = None,
        use_default_source: bool = True,
        name: str = "",
    ) -> None:
        sound_source = source or (settings.get("alarm_sound") if use_default_source else None)
        sound_volume = settings.get("volume", 100) if volume is None else volume
        try:
            player.play(sound_source, volume=sound_volume, radio=radio, loop=loop)
            if name and (loop or radio):
                self._active_names.add(name)
        except Exception as exc:
            activity_log.log("ring_start_failed", name, str(exc))

    def stop(self, name: str = "") -> None:
        """Stop the sound. If a name is given, stop only if no other named sounds remain."""
        if name:
            self._active_names.discard(name)
            if self._active_names:
                # At least one other named sound is still active -> don't stop player.
                return
        else:
            self._active_names.clear()
        try:
            player.stop()
        except Exception as exc:
            activity_log.log("ring_stop_failed", name, str(exc))


ring_controller = RingController()