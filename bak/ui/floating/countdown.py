"""
ui/floating/countdown.py
Floating countdown-timer window.
"""
import time as time_mod
import tkinter as tk
from core.sound import player, metronome_tick
from core.logger import activity_log
from .base import FloatingWindow


class CountdownWindow(FloatingWindow):
    def __init__(self, master, settings, theme_manager, timer_obj,
                 tick_threshold=None, app=None):
        super().__init__(master, settings, theme_manager,
                         width=220, height=200, title=timer_obj.label)
        self.app = app
        self.timer = timer_obj
        self.tick_threshold = tick_threshold or settings.get("tick_threshold", 10)
        self.paused = timer_obj.status in ("paused", "stopped")
        self.time_left = timer_obj.current_remaining()          # float
        self.timer.show_floating = True
        self.locked = timer_obj.locked
        self.custom_alpha = timer_obj.floating_alpha

        if timer_obj.floating_geometry:
            try:
                self.top.geometry(timer_obj.floating_geometry)
            except tk.TclError:
                pass
        if self.custom_alpha is not None:
            self.top.attributes("-alpha", self.custom_alpha)

        self.apply_lock_state(self.locked)
        self._schedule_initial_draw()
        self.update_loop()

    # ── Update loop ────────────────────────────────────────────────────
    def update_loop(self) -> None:
        previous_remaining = self.time_left
        previous_status = self.timer.status
        self.timer.sync_state(time_mod.time())
        self.time_left = self.timer.current_remaining()
        self.paused = self.timer.status != "running"

        if self.timer.status == "running" and 0 < self.time_left <= self.tick_threshold and self.time_left != previous_remaining:
            metronome_tick()

        if previous_status != "completed" and self.timer.status == "completed":
            player.play(self.settings.get("alarm_sound"),
                        volume=self.settings.get("volume", 100))
            activity_log.log("timer_completed", self.timer.label,
                             f"duration={self.timer.duration}s")
            self.flash()
            if self.app:
                self.app.timer_manager.save()

        self.draw()
        self.after_id = self.top.after(1000, self.update_loop)

    # ── Controls ───────────────────────────────────────────────────────
    def toggle_pause(self) -> None:
        if self.timer.status == "running":
            self.timer.pause()
            activity_log.log("timer_paused", self.timer.label,
                             f"remaining={self.time_left}s")
        else:
            self.timer.resume()
            activity_log.log("timer_started", self.timer.label,
                             f"remaining={self.time_left}s")
        self.paused = self.timer.status != "running"
        self.time_left = self.timer.current_remaining()
        if self.app:
            self.app.timer_manager.save()
        self.draw()

    def reset(self) -> None:
        self.timer.reset()
        self.time_left = self.timer.current_remaining()
        self.paused = True
        activity_log.log("timer_reset", self.timer.label,
                         f"duration={self.timer.duration}s")
        if self.app:
            self.app.timer_manager.save()
        self.draw()

    # ── Drawing ────────────────────────────────────────────────────────
    def _draw_button(self, x: int, y: int, w: int, h: int,
                     text: str, command) -> None:
        self.canvas.create_rectangle(x, y, x + w, y + h,
                                     fill="#444", outline="#666", width=1)
        self.canvas.create_text(x + w / 2, y + h / 2, text=text,
                                fill="white",
                                font=("Arial", max(8, int(h * 0.5))))
        tag = self.canvas.create_rectangle(x, y, x + w, y + h,
                                           fill="", outline="")
        self.canvas.tag_bind(tag, "<Button-1>", lambda _e: command())

    def draw(self) -> None:
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        # Close button
        if not self.locked:
            self.canvas.create_text(w - 10, 10, text="✕",
                                    fill="red", font=("Arial", 12, "bold"),
                                    anchor="ne")
        # Label
        if self.timer.label:
            self.canvas.create_text(w // 2, 20, text=self.timer.label,
                                    fill=self.theme_manager.current["fg"],
                                    font=("Arial", 10))
        # Time display – use int() for display only
        mins, secs = divmod(int(self.time_left), 60)
        fs = max(10, int(min(w, h) * 0.18))
        self.canvas.create_text(w // 2, h // 2,
                                text=f"{mins:02d}:{secs:02d}",
                                fill="white",
                                font=("Arial", fs, "bold"))
        # Buttons
        if not self.locked:
            bw = max(40, min(80, int(w * 0.25)))
            bh = max(20, min(30, int(h * 0.1)))
            by = h - bh - 10
            sym = "▶" if self.paused else "⏸"
            self._draw_button(w // 4 - bw // 2,   by, bw, bh, sym,  self.toggle_pause)
            self._draw_button(3 * w // 4 - bw // 2, by, bw, bh, "↺", self.reset)

        # Resize grip
        if not self.fullscreen and not self.locked:
            self.canvas.create_polygon(w, h, w - self.GRIP, h, w, h - self.GRIP,
                                       fill="#555", outline="")

        # Lock icon when locked
        if self.locked:
            self.canvas.create_text(w // 2, h - 15, text="🔒",
                                    fill="#aaa", font=("Arial", 10))

        # Bind right-click on canvas background
        self.canvas.tag_bind("all", "<Button-3>",
                             lambda e: self._show_context_menu(e))

    def flash(self) -> None:
        orig = self.canvas["bg"]

        def _flash(count):
            if count <= 0:
                self.canvas["bg"] = orig
                return
            self.canvas["bg"] = "#ff4444" if count % 2 else orig
            self.top.after(200, lambda: _flash(count - 1))

        _flash(6)

    def on_destroy(self) -> None:
        if self.timer:
            if self.app:
                self.app.open_timer_windows.pop(self.timer.id, None)
            self.timer.show_floating = False
            if self.timer.status == "running":
                self.timer.sync_state(time_mod.time())
            self.save_geometry()
            self.timer.locked = self.locked
            self.timer.floating_alpha = self.custom_alpha
            if self.app:
                self.app.timer_manager.save()