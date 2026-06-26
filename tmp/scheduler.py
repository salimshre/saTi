"""Background refresh and alarm scheduling."""

from __future__ import annotations

import time as time_mod

from core.logger import activity_log
from core.notifications import notify
from ui.alarm_popup import AlarmPopup


class AppScheduler:
    def __init__(self, app) -> None:
        self.app = app
        self._alarm_after_id = None
        self._runtime_after_id = None

    def start(self) -> None:
        self._check_alarms()
        self._tick_runtime_state()

    def stop(self) -> None:
        for after_id in (self._alarm_after_id, self._runtime_after_id):
            if after_id is not None:
                try:
                    self.app.root.after_cancel(after_id)
                except Exception:
                    pass

    def _check_alarms(self) -> None:
        try:
            for alarm in self.app.alarm_manager.check_due():
                notify("SaTi Alarm", f"{alarm.name} is ringing.", enabled=self.app.settings.get("enable_notifications", True))
                AlarmPopup(self.app.root, alarm, self.app.settings)
            self.app.alarm_manager.update()
        except Exception as exc:
            activity_log.log("scheduler_alarm_error", details=str(exc))
        self._alarm_after_id = self.app.root.after(1000, self._check_alarms)

    def _tick_runtime_state(self) -> None:
        try:
            now = time_mod.time()
            self.app.timer_tab.refresh_runtime_state(now)
            self.app.stopwatch_tab.refresh_runtime_state(now)
        except Exception as exc:
            activity_log.log("scheduler_runtime_error", details=str(exc))
        self._runtime_after_id = self.app.root.after(250, self._tick_runtime_state)
