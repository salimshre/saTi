"""
core/data_import_export.py
Export and import all user data (alarms, timers, stopwatches, settings) to/from a single JSON file.
"""

import json
from pathlib import Path

from core.logger import activity_log
from models import Alarm, Timer, Stopwatch


def export_data(alarm_manager, timer_manager, stopwatch_manager, settings_manager, filepath: str) -> bool:
    """
    Export all data to a JSON file.
    Returns True on success, False on failure.
    """
    data = {
        "settings": settings_manager.settings,
        "alarms": [alarm.to_dict() for alarm in alarm_manager.alarms],
        "timers": [timer.to_dict() for timer in timer_manager.timers],
        "stopwatches": [sw.to_dict() for sw in stopwatch_manager.stopwatches],
    }
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        activity_log.log("data_exported", details=filepath)
        return True
    except Exception as e:
        activity_log.log("data_export_failed", details=str(e))
        return False


def import_data(alarm_manager, timer_manager, stopwatch_manager, settings_manager, filepath: str, mode: str = "replace") -> bool:
    """
    Import data from a JSON file.
    mode: "replace" -> replaces all current data with imported data.
          "merge" -> adds items that don't already exist (by ID); settings are updated (overwritten).
    Returns True on success, False on failure.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        activity_log.log("data_import_failed", details=str(e))
        return False

    try:
        if mode == "replace":
            # Replace all data
            alarm_manager.alarms.clear()
            timer_manager.timers.clear()
            stopwatch_manager.stopwatches.clear()

            for alarm_data in data.get("alarms", []):
                alarm = Alarm.from_dict(alarm_data)
                alarm_manager.alarms.append(alarm)
            for timer_data in data.get("timers", []):
                timer = Timer.from_dict(timer_data)
                timer_manager.timers.append(timer)
            for sw_data in data.get("stopwatches", []):
                sw = Stopwatch.from_dict(sw_data)
                stopwatch_manager.stopwatches.append(sw)

            # Overwrite settings
            settings_manager.settings.update(data.get("settings", {}))

            # Save all
            alarm_manager.save()
            timer_manager.save()
            stopwatch_manager.save()
            settings_manager.save()
            activity_log.log("data_import_replace", details=filepath)

        else:  # merge
            existing_alarm_ids = {a.id for a in alarm_manager.alarms}
            for alarm_data in data.get("alarms", []):
                if alarm_data["id"] not in existing_alarm_ids:
                    alarm = Alarm.from_dict(alarm_data)
                    alarm_manager.alarms.append(alarm)

            existing_timer_ids = {t.id for t in timer_manager.timers}
            for timer_data in data.get("timers", []):
                if timer_data["id"] not in existing_timer_ids:
                    timer = Timer.from_dict(timer_data)
                    timer_manager.timers.append(timer)

            existing_sw_ids = {s.id for s in stopwatch_manager.stopwatches}
            for sw_data in data.get("stopwatches", []):
                if sw_data["id"] not in existing_sw_ids:
                    sw = Stopwatch.from_dict(sw_data)
                    stopwatch_manager.stopwatches.append(sw)

            # Merge settings (overwrite with imported)
            settings_manager.settings.update(data.get("settings", {}))

            # Save all
            alarm_manager.save()
            timer_manager.save()
            stopwatch_manager.save()
            settings_manager.save()
            activity_log.log("data_import_merge", details=filepath)

        return True
    except Exception as e:
        activity_log.log("data_import_failed", details=str(e))
        return False