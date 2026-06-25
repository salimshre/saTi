"""Alarm data model and persistence manager."""

from __future__ import annotations

import calendar
import datetime
import uuid

from core.config import ALARMS_FILE
from core.persistence import load_json_file, save_json_file


class Alarm:
    def __init__(
        self,
        name: str = "Alarm",
        alarm_type: str = "one-time",
        date_time: datetime.datetime | None = None,
        days_of_week: list[int] | None = None,
        day_of_month: int | None = None,
        month: int | None = None,
        year: int | None = None,
        custom_dates: list[datetime.date] | None = None,
        enabled: bool = True,
        sound_file: str | None = None,
        radio_url: str | None = None,
        actions: list[dict] | None = None,
        snooze_minutes: int = 10,
        repeat_until_dismissed: bool = False,
        advance_warning_days: int = 0,
        id: str | None = None,
        show_floating: bool = False,
        locked: bool = False,
        floating_geometry: str | None = None,
        floating_alpha: float | None = None,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.type = alarm_type
        self.date_time = date_time
        self.days_of_week = days_of_week if days_of_week is not None else []
        self.day_of_month = day_of_month
        self.month = month
        self.year = year
        self.custom_dates = custom_dates if custom_dates is not None else []
        self.enabled = enabled
        self.sound_file = sound_file
        self.radio_url = radio_url
        self.actions = actions if actions is not None else []
        self.snooze_minutes = snooze_minutes
        self.repeat_until_dismissed = repeat_until_dismissed
        self.advance_warning_days = advance_warning_days
        self.next_trigger: datetime.datetime | None = None
        self.show_floating = show_floating
        self.locked = locked
        self.floating_geometry = floating_geometry
        self.floating_alpha = floating_alpha

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "date_time": self.date_time.isoformat() if self.date_time else None,
            "days_of_week": self.days_of_week,
            "day_of_month": self.day_of_month,
            "month": self.month,
            "year": self.year,
            "custom_dates": [day.isoformat() for day in self.custom_dates],
            "enabled": self.enabled,
            "sound_file": self.sound_file,
            "radio_url": self.radio_url,
            "actions": self.actions,
            "snooze_minutes": self.snooze_minutes,
            "repeat_until_dismissed": self.repeat_until_dismissed,
            "advance_warning_days": self.advance_warning_days,
            "show_floating": self.show_floating,
            "locked": self.locked,
            "floating_geometry": self.floating_geometry,
            "floating_alpha": self.floating_alpha,
        }

    @staticmethod
    def from_dict(data: dict) -> Alarm:
        raw_dt = data.get("date_time")
        return Alarm(
            id=data.get("id"),
            name=data.get("name", "Alarm"),
            alarm_type=data.get("type", "one-time"),
            date_time=datetime.datetime.fromisoformat(raw_dt) if raw_dt else None,
            days_of_week=data.get("days_of_week", []),
            day_of_month=data.get("day_of_month"),
            month=data.get("month"),
            year=data.get("year"),
            custom_dates=[datetime.date.fromisoformat(day) for day in data.get("custom_dates", [])],
            enabled=data.get("enabled", True),
            sound_file=data.get("sound_file"),
            radio_url=data.get("radio_url"),
            actions=data.get("actions", []),
            snooze_minutes=data.get("snooze_minutes", 10),
            repeat_until_dismissed=data.get("repeat_until_dismissed", False),
            advance_warning_days=data.get("advance_warning_days", 0),
            show_floating=data.get("show_floating", False),
            locked=data.get("locked", False),
            floating_geometry=data.get("floating_geometry"),
            floating_alpha=data.get("floating_alpha"),
        )


class AlarmManager:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.alarms: list[Alarm] = []
        self.load()

    def load(self) -> None:
        data = load_json_file(ALARMS_FILE, [], "alarms")
        self.alarms = [Alarm.from_dict(item) for item in data]

    def save(self) -> None:
        save_json_file(ALARMS_FILE, [alarm.to_dict() for alarm in self.alarms], "alarms")

    def add(self, alarm: Alarm) -> None:
        self.alarms.append(alarm)
        self.update()

    def remove(self, alarm_id: str) -> None:
        self.alarms = [alarm for alarm in self.alarms if alarm.id != alarm_id]
        self.save()

    def get(self, alarm_id: str) -> Alarm | None:
        return next((alarm for alarm in self.alarms if alarm.id == alarm_id), None)

    def update(self) -> None:
        now = datetime.datetime.now()
        for alarm in self.alarms:
            alarm.next_trigger = self._get_next_trigger(alarm, now) if alarm.enabled else None
        self.save()

    def _get_next_trigger(self, alarm: Alarm, from_dt: datetime.datetime) -> datetime.datetime | None:
        if alarm.type == "one-time":
            return alarm.date_time if alarm.date_time and alarm.date_time > from_dt else None

        if alarm.type == "birthday":
            birth = alarm.date_time
            if not birth:
                return None
            candidate = datetime.datetime(from_dt.year, birth.month, birth.day, birth.hour, birth.minute)
            if candidate <= from_dt:
                candidate = datetime.datetime(from_dt.year + 1, birth.month, birth.day, birth.hour, birth.minute)
            if alarm.advance_warning_days > 0:
                candidate -= datetime.timedelta(days=alarm.advance_warning_days)
            return candidate

        if alarm.type == "daily":
            alarm_time = alarm.date_time.time() if alarm.date_time else datetime.time(0, 0)
            candidate = datetime.datetime.combine(from_dt.date(), alarm_time)
            return candidate if candidate > from_dt else candidate + datetime.timedelta(days=1)

        if alarm.type == "weekly":
            alarm_time = alarm.date_time.time() if alarm.date_time else datetime.time(0, 0)
            for offset in range(8):
                candidate_date = from_dt.date() + datetime.timedelta(days=offset)
                if candidate_date.weekday() in alarm.days_of_week:
                    candidate = datetime.datetime.combine(candidate_date, alarm_time)
                    if candidate > from_dt:
                        return candidate
            return None

        if alarm.type == "monthly":
            if not alarm.day_of_month:
                return None
            alarm_time = alarm.date_time.time() if alarm.date_time else datetime.time(0, 0)
            for month_offset in range(24):
                year = from_dt.year + ((from_dt.month - 1 + month_offset) // 12)
                month = ((from_dt.month - 1 + month_offset) % 12) + 1
                last_day = calendar.monthrange(year, month)[1]
                day = min(alarm.day_of_month, last_day)
                candidate = datetime.datetime(year, month, day, alarm_time.hour, alarm_time.minute)
                if candidate > from_dt:
                    return candidate
            return None

        if alarm.type == "yearly":
            if not alarm.month or not alarm.day_of_month:
                return None
            alarm_time = alarm.date_time.time() if alarm.date_time else datetime.time(0, 0)
            for year in (from_dt.year, from_dt.year + 1):
                last_day = calendar.monthrange(year, alarm.month)[1]
                day = min(alarm.day_of_month, last_day)
                candidate = datetime.datetime(year, alarm.month, day, alarm_time.hour, alarm_time.minute)
                if candidate > from_dt:
                    return candidate
            return None

        if alarm.type == "custom":
            alarm_time = alarm.date_time.time() if alarm.date_time else datetime.time(0, 0)
            for custom_date in sorted(alarm.custom_dates):
                candidate = datetime.datetime.combine(custom_date, alarm_time)
                if candidate > from_dt:
                    return candidate
            return None

        return None

    def check_due(self) -> list[Alarm]:
        now = datetime.datetime.now()
        due: list[Alarm] = []
        for alarm in self.alarms:
            if alarm.enabled and alarm.next_trigger and alarm.next_trigger <= now:
                due.append(alarm)
                alarm.next_trigger = self._get_next_trigger(alarm, now)
        return due
