"""
core/logger.py
Daily CSV activity logger shared across the whole application.
"""
import csv
import datetime
import os

from .config import CONFIG_DIR


class CSVLogger:
    """Appends timestamped activity events to a per-day CSV file."""

    FIELDS = ["timestamp", "event_type", "name", "details"]

    def __init__(self, log_dir: str = CONFIG_DIR):
        self.log_dir = log_dir

    # ------------------------------------------------------------------
    def _log_path(self) -> str:
        today = datetime.date.today().isoformat()
        return os.path.join(self.log_dir, f"activity_{today}.csv")

    def log(self, event_type: str, name: str = "", details: str = "") -> None:
        path = self._log_path()
        write_header = not os.path.exists(path)
        try:
            with open(path, "a", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=self.FIELDS)
                if write_header:
                    writer.writeheader()
                writer.writerow({
                    "timestamp":  datetime.datetime.now().isoformat(timespec="seconds"),
                    "event_type": event_type,
                    "name":       name,
                    "details":    details,
                })
        except Exception as exc:
            print(f"[CSVLogger] Failed to write log: {exc}")


# Module-level singleton – import and use directly
activity_log = CSVLogger()