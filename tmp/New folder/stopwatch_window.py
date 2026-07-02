"""
ui/floating/stopwatch_window.py
Floating stopwatch window with lap display.
"""
import tkinter as tk

from core.logger import activity_log

from .base import FloatingWindow


class StopwatchWindow(FloatingWindow):
    def __init__(self, master, settings, theme_manager, stopwatch, app=None):
        super().__init__(master, settings, theme_manager,
                         width=220, height=180, title=stopwatch.label)
        self.app       = app
        self.stopwatch = stopwatch
        self.stopwatch.show_floating = True
        self.locked       = stopwatch.locked
        self.custom_alpha = stopwatch.floating_alpha
        self._preserve_on_destroy = False   # <-- NEW

        if stopwatch.floating_geometry:
            try:
                self.top.geometry(stopwatch.floating_geometry)
            except tk.TclError:
                pass
        if self.custom_alpha is not None:
            self.top.attributes("-alpha", self.custom_alpha)

        self.apply_lock_state(self.locked)
        self._schedule_initial_draw()
        self._start_updater()

    def _start_updater(self) -> None:
        self.draw()
        self.after_id = self.top.after(50, self._start_updater)

    def _elapsed(self) -> float:
        return self.stopwatch.elapsed()

    def _toggle_start_stop(self) -> None:
        sw = self.stopwatch
        if sw.status == "running":
            sw.pause()
            activity_log.log("stopwatch_stopped", sw.label,
                             f"elapsed={sw.elapsed_paused:.2f}s")
        else:
            sw.start_or_resume()
            activity_log.log("stopwatch_started", sw.label,
                             f"elapsed_before={sw.elapsed_paused:.2f}s")
        if self.app:
            self.app.stopwatch_manager.save()

    def _reset(self) -> None:
        sw = self.stopwatch
        activity_log.log("stopwatch_reset", sw.label,
                         f"elapsed={self._elapsed():.2f}s")
        sw.reset()
        if self.app:
            self.app.stopwatch_manager.save()

    def _lap(self) -> None:
        sw = self.stopwatch
        elapsed = sw.add_lap()
        if elapsed is not None:
            activity_log.log("stopwatch_lap", sw.label,
                             f"lap={len(sw.lap_times)} elapsed={elapsed:.2f}s")
            if self.app:
                self.app.stopwatch_manager.save()

    def _draw_button(self, x, y, w, h, text, command) -> None:
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
        self.canvas.create_text(w // 2, 15, text=self.stopwatch.label,
                                fill=self.theme_manager.current["fg"],
                                font=("Arial", 10))

        elapsed = self._elapsed()
        h_part, rem = divmod(int(elapsed), 3600)
        m_part, s_part = divmod(rem, 60)
        ms = int((elapsed - int(elapsed)) * 100)
        ts = (f"{h_part:02d}:{m_part:02d}:{s_part:02d}.{ms:02d}"
              if h_part > 0 else f"{m_part:02d}:{s_part:02d}.{ms:02d}")
        fs = max(10, int(min(w, h) * 0.14))
        self.canvas.create_text(w // 2, h // 2 - 10, text=ts,
                                fill="white", font=("Arial", fs, "bold"))

        if not self.locked:
            n  = 3
            bw = max(40, min(70, int(w * 0.22)))
            bh = max(20, min(30, int(h * 0.1)))
            by = h - bh - 10
            sp = (w - n * bw) // (n + 1)
            sym = "⏹" if self.stopwatch.status == "running" else "▶"
            for i, (text, cmd) in enumerate([
                (sym,          self._toggle_start_stop),
                ("↺",          self._reset),
                ("⏱",          self._lap),
            ]):
                self._draw_button(sp + i * (bw + sp), by, bw, bh, text, cmd)

        if not self.fullscreen and not self.locked:
            self.canvas.create_polygon(w, h, w - self.GRIP, h, w, h - self.GRIP,
                                       fill="#555", outline="")
        if self.locked:
            self.canvas.create_text(w // 2, h - 15, text="🔒",
                                    fill="#aaa", font=("Arial", 10))

        if self.stopwatch.lap_times:
            lap_y = h // 2 + 25
            for i, lap in enumerate(self.stopwatch.lap_times[-5:]):
                lh, lr = divmod(int(lap), 3600)
                lm, ls = divmod(lr, 60)
                lms = int((lap - int(lap)) * 100)
                idx = len(self.stopwatch.lap_times) - 5 + i + 1
                label = f"Lap {idx}: {lh:02d}:{lm:02d}:{ls:02d}.{lms:02d}"
                self.canvas.create_text(w // 2, lap_y + i * 15,
                                        text=label, fill="gray",
                                        font=("Arial", 8))

        self.canvas.tag_bind("all", "<Button-3>",
                             lambda e: self._show_context_menu(e))

    def on_destroy(self) -> None:
        if self._preserve_on_destroy:
            # Preserve the window state for restart – do not clear floating flag
            return

        sw = self.stopwatch
        if sw:
            if self.app:
                self.app.open_stopwatch_windows.pop(sw.id, None)
            if sw.status == "running":
                sw.pause()
            sw.show_floating    = False
            self.save_geometry()
            sw.locked        = self.locked
            sw.floating_alpha = self.custom_alpha
            if self.app:
                self.app.stopwatch_manager.save()
                