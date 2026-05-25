import datetime

import models.alarm as alarm_module


class DummySettings:
    def get(self, *_args, **_kwargs):
        return None


def make_manager(tmp_path, monkeypatch):
    monkeypatch.setattr(alarm_module, "ALARMS_FILE", str(tmp_path / "alarms.json"))
    return alarm_module.AlarmManager(DummySettings())


def test_weekly_alarm_picks_next_selected_weekday(tmp_path, monkeypatch):
    manager = make_manager(tmp_path, monkeypatch)
    alarm = alarm_module.Alarm(
        alarm_type="weekly",
        date_time=datetime.datetime(2026, 1, 1, 9, 30),
        days_of_week=[2],
    )
    current = datetime.datetime(2026, 5, 11, 10, 0)  # Monday

    next_trigger = manager._get_next_trigger(alarm, current)

    assert next_trigger == datetime.datetime(2026, 5, 13, 9, 30)


def test_monthly_alarm_clamps_to_last_day_of_month(tmp_path, monkeypatch):
    manager = make_manager(tmp_path, monkeypatch)
    alarm = alarm_module.Alarm(
        alarm_type="monthly",
        date_time=datetime.datetime(2026, 1, 31, 8, 15),
        day_of_month=31,
    )
    current = datetime.datetime(2026, 2, 1, 12, 0)

    next_trigger = manager._get_next_trigger(alarm, current)

    assert next_trigger == datetime.datetime(2026, 2, 28, 8, 15)


def test_birthday_advance_warning_moves_trigger_earlier(tmp_path, monkeypatch):
    manager = make_manager(tmp_path, monkeypatch)
    alarm = alarm_module.Alarm(
        alarm_type="birthday",
        date_time=datetime.datetime(2000, 5, 20, 7, 0),
        advance_warning_days=3,
    )
    current = datetime.datetime(2026, 5, 1, 8, 0)

    next_trigger = manager._get_next_trigger(alarm, current)

    assert next_trigger == datetime.datetime(2026, 5, 17, 7, 0)


def test_check_due_returns_and_reschedules_daily_alarm(tmp_path, monkeypatch):
    manager = make_manager(tmp_path, monkeypatch)
    alarm = alarm_module.Alarm(
        alarm_type="daily",
        date_time=datetime.datetime.now().replace(hour=9, minute=0, second=0, microsecond=0),
    )
    alarm.enabled = True
    alarm.next_trigger = datetime.datetime.now() - datetime.timedelta(seconds=1)
    manager.alarms = [alarm]

    due = manager.check_due()

    assert due == [alarm]
    assert alarm.next_trigger is not None
    assert alarm.next_trigger > datetime.datetime.now()
