"""Optional desktop notifications."""

from __future__ import annotations


def notify(title: str, message: str, enabled: bool = True) -> None:
    if not enabled:
        return
    try:
        from plyer import notification

        notification.notify(title=title, message=message, app_name="SaTi", timeout=10)
    except Exception:
        # Notifications are best-effort only.
        return
