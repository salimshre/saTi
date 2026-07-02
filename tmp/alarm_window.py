"""
ui/floating/alarm_window.py
Floating window that shows countdown to the next alarm trigger.
"""
import datetime
import tkinter as tk

from .base import FloatingWindow


class FloatingAlarmWindow(FloatingWindow):
    def __init__(self, master, settings, theme_manager, alarm, app=None):
        super().__init__(master, settings, theme_manager, title=alarm.name)
        self.app          = app
        self.alarm        = alarm
        self.alarm.show_floating = True
        self.locked       = alarm.locked
        self.custom_alpha = alarm.floating_alpha
        self.time_left    = 0

        if alarm.floating_geometry:
            try:
                self.top.geometry(alarm.floating_geometry)
            except tk.TclError:
                pass
        if self.custom_alpha is not None:
            self.top.attributes("-alpha", self.custom_alpha)

        self.apply_lock_state(self.locked)
        self._schedule_initial_draw()
        self.update_loop()

    def update_loop(self) -> None:
        if self.alarm and self.alarm.next_trigger:
            delta = (self.alarm.next_trigger - datetime.datetime.now()).total_seconds()
            self.time_left = max(0, int(delta))
        else:
            self.time_left = 0
        self.draw()
        self.after_id = self.top.after(1000, self.update_loop)

    def draw(self) -> None:
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        if not self.locked:
            self.canvas.create_text(w - 10, 10, text="✕",
                                    fill="red", font=("Arial", 12, "bold"),
                                    anchor="ne")
        self.canvas.create_text(w // 2, 20, text=self.alarm.name,
                                fill=self.theme_manager.current["fg"],
                                font=("Arial", 10))
        if self.alarm and self.alarm.next_trigger:
            mins, secs = divmod(self.time_left, 60)
            hours, mins = divmod(mins, 60)
            ts = (f"{hours:02d}:{mins:02d}:{secs:02d}"
                  if hours > 0 else f"{mins:02d}:{secs:02d}")
            fs = max(10, int(min(w, h) * 0.18))
            self.canvas.create_text(w // 2, h // 2, text=ts,
                                    fill="white", font=("Arial", fs, "bold"))
        else:
            self.canvas.create_text(w // 2, h // 2, text="N/A", fill="gray")

        if not self.fullscreen and not self.locked:
            self.canvas.create_polygon(w, h, w - self.GRIP, h, w, h - self.GRIP,
                                       fill="#555", outline="")
        if self.locked:
            self.canvas.create_text(w // 2, h - 15, text="🔒",
                                    fill="#aaa", font=("Arial", 10))

        self.canvas.tag_bind("all", "<Button-3>",
                             lambda e: self._show_context_menu(e))

    def on_destroy(self) -> None:
        if self.alarm:
            if self.app:
                self.app.open_alarm_windows.pop(self.alarm.id, None)
            self.alarm.show_floating  = False
            self.save_geometry()
            self.alarm.locked         = self.locked
            self.alarm.floating_alpha = self.custom_alpha
            if self.app:
                self.app.alarm_manager.save()
