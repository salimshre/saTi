"""Stopwatch data-model and persistence manager."""

from __future__ import annotations

import time as time_mod
import uuid

from core.config import STOPWATCHES_FILE
from core.persistence import load_json_file, save_json_file


class Stopwatch:
    def __init__(
        self,
        label="Stopwatch",
        id=None,
        show_floating=False,
        locked=False,
        floating_geometry=None,
        floating_alpha=None,
    ):
        self.id               = id or str(uuid.uuid4())
        self.label            = label
        self.status           = "stopped"   # running | paused | stopped
        self.start_time       = 0.0
        self.elapsed_paused   = 0.0
        self.lap_times: list  = []
        self.show_floating    = show_floating
        self.locked           = locked
        self.floating_geometry = floating_geometry
        self.floating_alpha   = floating_alpha

    def elapsed(self, now: float | None = None) -> float:
        now = now if now is not None else time_mod.time()
        if self.status == "running":
            return now - self.start_time + self.elapsed_paused
        return self.elapsed_paused

    def start_or_resume(self, now: float | None = None) -> None:
        now = now if now is not None else time_mod.time()
        self.start_time = now
        self.status = "running"

    def pause(self, now: float | None = None) -> None:
        now = now if now is not None else time_mod.time()
        if self.status == "running":
            self.elapsed_paused = now - self.start_time + self.elapsed_paused
            self.status = "paused"

    def reset(self) -> None:
        self.status = "stopped"
        self.start_time = 0.0
        self.elapsed_paused = 0.0
        self.lap_times = []

    def add_lap(self, now: float | None = None) -> float | None:
        if self.status not in ("running", "paused"):
            return None
        elapsed = self.elapsed(now)
        self.lap_times.append(elapsed)
        return elapsed

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "label":            self.label,
            "status":           self.status,
            "start_time":       self.start_time,
            "elapsed_paused":   self.elapsed_paused,
            "lap_times":        self.lap_times,
            "show_floating":    self.show_floating,
            "locked":           self.locked,
            "floating_geometry": self.floating_geometry,
            "floating_alpha":   self.floating_alpha,
        }

    @staticmethod
    def from_dict(d: dict) -> "Stopwatch":
        sw = Stopwatch(
            id=d["id"],
            label=d["label"],
            show_floating=d.get("show_floating", False),
            locked=d.get("locked", False),
            floating_geometry=d.get("floating_geometry"),
            floating_alpha=d.get("floating_alpha"),
        )
        sw.status         = d.get("status", "stopped")
        sw.start_time     = d.get("start_time", 0.0)
        sw.elapsed_paused = d.get("elapsed_paused", 0.0)
        sw.lap_times      = d.get("lap_times", [])
        return sw


class StopwatchManager:
    def __init__(self):
        self.stopwatches: list[Stopwatch] = []
        self.load()

    def load(self) -> None:
        data = load_json_file(STOPWATCHES_FILE, [], "stopwatches")
        self.stopwatches = [Stopwatch.from_dict(item) for item in data]

    def save(self) -> None:
        save_json_file(STOPWATCHES_FILE, [s.to_dict() for s in self.stopwatches], "stopwatches")

    def add(self, sw: Stopwatch) -> None:
        self.stopwatches.append(sw)
        self.save()

    def remove(self, sw_id: str) -> None:
        self.stopwatches = [s for s in self.stopwatches if s.id != sw_id]
        self.save()

    def get(self, sw_id: str) -> Stopwatch | None:
        return next((s for s in self.stopwatches if s.id == sw_id), None)
