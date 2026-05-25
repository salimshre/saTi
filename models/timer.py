"""Timer data model and persistence manager."""

from __future__ import annotations

import time as time_mod
import uuid

from core.config import TIMERS_FILE
from core.persistence import load_json_file, save_json_file


class Timer:
    def __init__(
        self,
        label: str = "Timer",
        duration: float = 300.0,
        id: str | None = None,
        show_floating: bool = False,
        locked: bool = False,
        floating_geometry: str | None = None,
        floating_alpha: float | None = None,
        last_started_at: float | None = None,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.label = label
        self.duration = float(duration)
        self.remaining = self.duration
        self.status = "stopped"
        self.show_floating = show_floating
        self.locked = locked
        self.floating_geometry = floating_geometry
        self.floating_alpha = floating_alpha
        self.last_started_at = last_started_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "duration": self.duration,
            "remaining": self.remaining,
            "status": self.status,
            "show_floating": self.show_floating,
            "locked": self.locked,
            "floating_geometry": self.floating_geometry,
            "floating_alpha": self.floating_alpha,
            "last_started_at": self.last_started_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "Timer":
        timer = Timer(
            id=data.get("id"),
            label=data.get("label", "Timer"),
            duration=float(data.get("duration", 300)),
            show_floating=data.get("show_floating", False),
            locked=data.get("locked", False),
            floating_geometry=data.get("floating_geometry"),
            floating_alpha=data.get("floating_alpha"),
            last_started_at=data.get("last_started_at"),
        )
        timer.remaining = float(data.get("remaining", timer.duration))
        timer.status = data.get("status", "stopped")
        timer.sync_state()
        return timer

    def current_remaining(self, now: float | None = None) -> float:
        """Return remaining seconds as a float (always >= 0)."""
        now = now if now is not None else time_mod.time()
        if self.status != "running" or self.last_started_at is None:
            return max(0.0, self.remaining)
        elapsed = now - self.last_started_at
        return max(0.0, self.remaining - elapsed)

    def sync_state(self, now: float | None = None) -> None:
        """Update remaining and keep last_started_at in sync."""
        now = now if now is not None else time_mod.time()
        if self.status == "running":
            # Update remaining based on elapsed time
            self.remaining = self.current_remaining(now)
            # IMPORTANT: set last_started_at to now to keep the pair consistent
            self.last_started_at = now
            if self.remaining <= 0.0:
                self.remaining = 0.0
                self.status = "completed"
                self.last_started_at = None
        elif self.status == "completed":
            self.remaining = 0.0
            self.last_started_at = None
        else:
            # paused or stopped: remaining is already correct
            self.remaining = max(0.0, self.remaining)
            self.last_started_at = None

    def resume(self, now: float | None = None) -> None:
        """Start or resume the timer."""
        self.sync_state(now)
        if self.remaining <= 0.0:
            self.status = "completed"
            self.remaining = 0.0
            self.last_started_at = None
            return
        self.status = "running"
        self.last_started_at = now if now is not None else time_mod.time()

    def pause(self, now: float | None = None) -> None:
        """Pause the running timer."""
        self.sync_state(now)
        if self.status != "completed":
            self.status = "paused"
        self.last_started_at = None

    def reset(self) -> None:
        self.remaining = self.duration
        self.status = "stopped"
        self.last_started_at = None


class TimerManager:
    def __init__(self) -> None:
        self.timers: list[Timer] = []
        self.load()

    def load(self) -> None:
        data = load_json_file(TIMERS_FILE, [], "timers")
        self.timers = [Timer.from_dict(item) for item in data]

    def save(self) -> None:
        save_json_file(TIMERS_FILE, [timer.to_dict() for timer in self.timers], "timers")

    def add(self, timer: Timer) -> None:
        self.timers.append(timer)
        self.save()

    def remove(self, timer_id: str) -> None:
        self.timers = [timer for timer in self.timers if timer.id != timer_id]
        self.save()

    def get(self, timer_id: str) -> Timer | None:
        return next((timer for timer in self.timers if timer.id == timer_id), None)

    def update(self, _timer: Timer | None = None) -> None:
        self.save()