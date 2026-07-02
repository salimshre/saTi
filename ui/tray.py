"""Best-effort system tray integration."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from tkinter import messagebox

from core.logger import activity_log
from ui.app_meta import APP_NAME


class TrayManager:
    """Manage the system tray icon (best-effort). Falls back to window iconify."""

    def __init__(self, app) -> None:
        self.app = app
        self.icon = None
        self._warned_fallback = False

    def minimize(self) -> None:
        if not self.app.settings.get("minimize_to_tray", True):
            self.app.quit_application()
            return

        if self.icon is not None:
            self.app.root.withdraw()
            return

        if not self._create_icon():
            self.app.root.iconify()
            if not self._warned_fallback:
                self._warned_fallback = True
                messagebox.showinfo(
                    APP_NAME,
                    "Tray support is not available because optional dependencies are missing.\n"
                    "The app has been minimized instead.",
                )
            return

        self.app.root.withdraw()

    def stop(self) -> None:
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception as exc:
                activity_log.log("tray_stop_failed", "", str(exc))
            self.icon = None

    def _create_icon(self) -> bool:
        try:
            import pystray
            from PIL import Image
        except Exception as exc:
            activity_log.log("tray_import_failed", "", str(exc))
            return False

        if self.icon is not None:
            return True

        # Load logo from assets folder
        assets_dir = Path(__file__).resolve().parents[1] / "assets"
        logo_path = assets_dir / "logo.png"
        image = None
        if logo_path.exists():
            try:
                image = Image.open(logo_path)
                # Resize to a reasonable tray size (e.g., 64x64)
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
            except Exception as exc:
                activity_log.log("tray_logo_load_failed", "", str(exc))

        if image is None:
            # Fallback: generate a simple icon
            from PIL import ImageDraw
            image = Image.new("RGB", (64, 64), color="#1e1e1e")
            draw = ImageDraw.Draw(image)
            draw.ellipse((10, 10, 54, 54), fill="#00ffcc")
            draw.text((24, 19), "S", fill="#000000")

        menu = pystray.Menu(
            pystray.MenuItem("Show", lambda icon, item: self._show_window()),
            pystray.MenuItem("Restart", lambda icon, item: self._restart_app()),
            pystray.MenuItem("Exit", lambda icon, item: self._exit_app()),
        )
        self.icon = pystray.Icon("sati", image, APP_NAME, menu)
        self.icon.run_detached()
        return True

    def _show_window(self) -> None:
        self.app.root.after(0, self._show_window_on_ui_thread)

    def _show_window_on_ui_thread(self) -> None:
        self.app.root.deiconify()
        self.app.root.lift()

    def _exit_app(self) -> None:
        self.app.root.after(0, self.app.quit_application)

    def _restart_app(self) -> None:
        """Trigger a full application restart."""
        self.app.root.after(0, self.app.restart_application)
        