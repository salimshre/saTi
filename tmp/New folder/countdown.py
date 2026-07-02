"""
ui/floating/countdown.py
Floating countdown-timer window.
"""
import time as time_mod
import tkinter as tk

from core.logger import activity_log
from core.ring import ring_controller
from core.sound import metronome_tick

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
        self.time_left = timer_obj.current_remaining()
        self.timer.show_floating = True
        self.locked = timer_obj.locked
        self.custom_alpha = timer_obj.floating_alpha
        self.overdue_popup = None
        self._overdue_label = None
        self._overdue_after_id = None
        self._muted = False
        self.completed_at = timer_obj.completed_at
        self._completion_handled = False
        self._preserve_on_destroy = False

        # ---- blink state ----
        self._blinking = False
        self._blink_after_id = None
        self._blink_original_bg = self.canvas["bg"]  # store original background
        self._blink_enabled = settings.get("blink_enabled", True)
        self._blink_interval = settings.get("blink_interval_ms", 500)
        self._blink_max_seconds = settings.get("blink_max_seconds", 0)
        self._blink_start_time = 0.0

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

    def update_blink_settings(self, enabled: bool, interval_ms: int, max_seconds: int) -> None:
        """Update the blink settings while the window is open."""
        self._blink_enabled = enabled
        self._blink_interval = interval_ms
        self._blink_max_seconds = max_seconds

        # If currently blinking and blinking is disabled, stop it
        if self._blinking and not enabled:
            self._stop_blinking()
        # If blinking is enabled and we're in a completed state but not blinking, restart
        elif enabled and self.timer.status == "completed" and not self._blinking and not self._muted:
            self._start_blinking()
        # If already blinking, restart the cycle to apply new interval
        elif self._blinking and enabled:
            # Restart the blink loop with new interval
            self._stop_blinking()
            self._start_blinking()

    def update_loop(self) -> None:
        now = time_mod.time()
        previous_remaining = self.time_left
        self.timer.sync_state(now)
        self.time_left = self.timer.current_remaining()
        self.paused = self.timer.status != "running"

        if self.timer.status == "running" and 0 < self.time_left <= self.tick_threshold and self.time_left != previous_remaining:
            metronome_tick()

        if self.timer.status == "completed" and not self._completion_handled:
            self._handle_completion(now)

        self.draw()
        self.after_id = self.top.after(1000, self.update_loop)

    def toggle_pause(self) -> None:
        if self.timer.status == "running":
            self.timer.pause()
            activity_log.log("timer_paused", self.timer.label,
                             f"remaining={self.time_left}s")
        else:
            self.timer.resume()
            self._completion_handled = False
            self.completed_at = None
            self._muted = False
            self._stop_blinking()  # stop blinking when resumed
            activity_log.log("timer_started", self.timer.label,
                             f"remaining={self.time_left}s")
        self.paused = self.timer.status != "running"
        self.time_left = self.timer.current_remaining()
        if self.app:
            self.app.timer_manager.save()
        self.draw()

    def reset(self) -> None:
        self.timer.reset()
        try:
            if self.overdue_popup:
                self._close_overdue_popup()
        except Exception:
            pass
        self._completion_handled = False
        self.completed_at = None
        self._muted = False
        self.time_left = self.timer.current_remaining()
        self.paused = True
        self._stop_blinking()
        activity_log.log("timer_reset", self.timer.label,
                         f"duration={self.timer.duration}s")
        if self.app:
            self.app.timer_manager.save()
        self.draw()

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

        if not self.locked:
            self.canvas.create_text(w - 10, 10, text="✕",
                                    fill="red", font=("Arial", 12, "bold"),
                                    anchor="ne")
        if self.timer.label:
            self.canvas.create_text(w // 2, 20, text=self.timer.label,
                                    fill=self.theme_manager.current["fg"],
                                    font=("Arial", 10))
        mins, secs = divmod(int(self.time_left), 60)
        fs = max(10, int(min(w, h) * 0.18))
        self.canvas.create_text(w // 2, h // 2,
                                text=f"{mins:02d}:{secs:02d}",
                                fill="white",
                                font=("Arial", fs, "bold"))
        if not self.locked:
            bw = max(40, min(80, int(w * 0.25)))
            bh = max(20, min(30, int(h * 0.1)))
            by = h - bh - 10
            sym = "▶" if self.paused else "⏸"
            self._draw_button(w // 4 - bw // 2,   by, bw, bh, sym,  self.toggle_pause)
            self._draw_button(3 * w // 4 - bw // 2, by, bw, bh, "↺", self.reset)

        if not self.fullscreen and not self.locked:
            self.canvas.create_polygon(w, h, w - self.GRIP, h, w, h - self.GRIP,
                                       fill="#555", outline="")

        if self.locked:
            self.canvas.create_text(w // 2, h - 15, text="🔒",
                                    fill="#aaa", font=("Arial", 10))

        self.canvas.tag_bind("all", "<Button-3>",
                             lambda e: self._show_context_menu(e))

    def flash(self) -> None:
        # Kept for compatibility but replaced by persistent blinking
        self._start_blinking()

    # ---------- Persistent Blinking ----------
    def _start_blinking(self) -> None:
        """Start the persistent red blink cycle if blinking is enabled."""
        if not self._blink_enabled:
            return
        if self._blinking:
            return
        if self._muted:
            return
        self._blinking = True
        self._blink_start_time = time_mod.time()
        self._blink_original_bg = self.canvas["bg"]  # capture current background
        self._blink_step()

    def _blink_step(self) -> None:
        """Toggle canvas background and schedule next step."""
        if not self._blinking:
            return

        # Check if we have exceeded max duration (if set)
        if self._blink_max_seconds > 0:
            elapsed = time_mod.time() - self._blink_start_time
            if elapsed >= self._blink_max_seconds:
                self._stop_blinking()
                return

        # Toggle background between red and original
        current_bg = self.canvas["bg"]
        if current_bg == "#ff0000" or current_bg == "red":
            self.canvas["bg"] = self._blink_original_bg
        else:
            self.canvas["bg"] = "#ff0000"

        # Schedule next toggle
        self._blink_after_id = self.top.after(
            self._blink_interval, self._blink_step
        )

    def _stop_blinking(self) -> None:
        """Stop the blink cycle and restore original background."""
        self._blinking = False
        if self._blink_after_id:
            try:
                self.top.after_cancel(self._blink_after_id)
            except Exception:
                pass
            self._blink_after_id = None
        # Restore original background
        try:
            self.canvas["bg"] = self._blink_original_bg
        except Exception:
            pass

    # ---------- Completion handling ----------
    def _handle_completion(self, completed_at: float | None = None) -> None:
        if self._completion_handled:
            self._show_overdue_popup()
            return
        self._completion_handled = True
        self._muted = False
        self.completed_at = self.timer.completed_at or completed_at or time_mod.time()
        self.timer.completed_at = self.completed_at
        ring_controller.start(self.settings, loop=True, name=self.timer.label)
        activity_log.log("timer_completed", self.timer.label,
                         f"duration={self.timer.duration}s")
        # Start persistent blinking (only if enabled)
        self._start_blinking()
        self._show_overdue_popup()
        if self.app:
            self.app.timer_manager.save()

    def _show_overdue_popup(self) -> None:
        if self.overdue_popup:
            return
        top = tk.Toplevel(self.top)
        top.title("Overdue")
        top.attributes("-topmost", True)
        top.resizable(False, False)
        top.protocol("WM_DELETE_WINDOW", self._close_overdue_popup)
        try:
            top.attributes("-toolwindow", True)
        except Exception:
            pass
        label = tk.Label(top, text="Time's Up", font=("Arial", 10, "bold"))
        label.pack(padx=8, pady=(8, 2))
        self._overdue_label = tk.Label(top, text="+00:00", font=("Arial", 12))
        self._overdue_label.pack(padx=8, pady=2)
        button_frame = tk.Frame(top)
        button_frame.pack(padx=8, pady=(2, 8))
        mute_btn = tk.Button(button_frame, text="Mute", command=self._mute_overdue_popup)
        mute_btn.pack(side=tk.LEFT, padx=(0, 5))
        close_btn = tk.Button(button_frame, text="Close", command=self._close_overdue_popup)
        close_btn.pack(side=tk.LEFT)
        self.overdue_popup = top
        self._update_overdue_popup()

    def _update_overdue_popup(self) -> None:
        if not self.overdue_popup or not self._overdue_label:
            return
        overdue = int(self.timer.overdue_elapsed(time_mod.time()))
        mins, secs = divmod(overdue, 60)
        try:
            self._overdue_label.config(text=f"+{mins:02d}:{secs:02d}")
        except Exception:
            pass
        try:
            self._overdue_after_id = self.overdue_popup.after(1000, self._update_overdue_popup)
        except Exception:
            pass

    def _mute_overdue_popup(self) -> None:
        self._muted = True
        self._stop_blinking()  # stop blinking when muted
        try:
            ring_controller.stop(self.timer.label)
            activity_log.log("timer_muted", self.timer.label, "")
        except Exception:
            pass

    def _close_overdue_popup(self) -> None:
        if self.overdue_popup:
            try:
                if self._overdue_after_id:
                    self.overdue_popup.after_cancel(self._overdue_after_id)
                    self._overdue_after_id = None
            except Exception:
                pass
            try:
                ring_controller.stop(self.timer.label)
            except Exception:
                pass
            try:
                self.overdue_popup.destroy()
            except Exception:
                pass
            self.overdue_popup = None
            self._overdue_label = None
        self._stop_blinking()  # stop blinking when popup is closed

    def on_destroy(self) -> None:
        self._stop_blinking()  # ensure blinking stops
        if self._preserve_on_destroy:
            return

        if self.timer:
            try:
                self._close_overdue_popup()
            except Exception:
                pass
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

                