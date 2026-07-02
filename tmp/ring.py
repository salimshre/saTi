"""Shared alarm and timer ringing helpers."""

from __future__ import annotations

import threading
import time

from core.logger import activity_log
from core.sound import player


class RingController:
    """Centralize sound start/stop behavior for alarms and countdown timers."""

    def __init__(self) -> None:
        self._active_names: set[str] = set()
        self._stop_timers: dict[str, threading.Timer] = {}  # name -> timer

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

                # Schedule auto-stop if loop is True and duration > 0
                if loop and not radio:
                    duration_minutes = settings.get("ring_duration_minutes", 5)
                    if duration_minutes > 0:
                        # Cancel any existing timer for this name
                        self._cancel_timer(name)
                        timer = threading.Timer(
                            duration_minutes * 60,
                            self.stop,
                            args=[name]
                        )
                        timer.daemon = True
                        timer.start()
                        self._stop_timers[name] = timer
                        activity_log.log("ring_auto_stop_scheduled", name, f"in {duration_minutes} min")

        except Exception as exc:
            activity_log.log("ring_start_failed", name, str(exc))

    def stop(self, name: str = "") -> None:
        """Stop the sound. If a name is given, stop only if no other named sounds remain."""
        if name:
            self._active_names.discard(name)
            self._cancel_timer(name)
            if self._active_names:
                # At least one other named sound is still active -> don't stop player.
                return
        else:
            self._active_names.clear()
            # Cancel all timers
            for timer_name in list(self._stop_timers.keys()):
                self._cancel_timer(timer_name)
        try:
            player.stop()
        except Exception as exc:
            activity_log.log("ring_stop_failed", name, str(exc))

    def _cancel_timer(self, name: str) -> None:
        timer = self._stop_timers.pop(name, None)
        if timer:
            try:
                timer.cancel()
            except Exception as exc:
                activity_log.log("ring_timer_cancel_failed", name, str(exc))


ring_controller = RingController()
