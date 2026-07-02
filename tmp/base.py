"""
ui/floating/base.py – docking with guaranteed no-overlap separation.
"""
import math
import tkinter as tk
from tkinter import ttk
from core.logger import activity_log


class FloatingWindow:
    GRIP = 12
    DOCK_THRESHOLD = 40      # pixels to trigger snap (only for separated windows)
    _all_windows = []

    def __init__(self, master, settings, theme_manager,
                 width: int = 160, height: int = 160, title: str = ""):
        self.master        = master
        self.settings      = settings
        self.theme_manager = theme_manager
        self.title_text    = title

        self.top = tk.Toplevel(master)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", settings.get("always_on_top", True))
        self.top.attributes("-alpha",   settings.get("transparency", 0.85))
        self.top.geometry(f"{width}x{height}+100+100")

        canvas_bg = theme_manager.current.get("canvas_bg", "#000000")
        self.top.configure(bg=canvas_bg)

        self.canvas = tk.Canvas(self.top, highlightthickness=0)
        theme_manager.apply(self.canvas)
        self.canvas.pack(expand=True, fill="both")
        self.canvas.bind("<Configure>", lambda e: self._safe_draw())

        self.running     = True
        self.after_id    = None
        self.fullscreen  = False
        self.orig_geom   = ""
        self.resizing    = False
        self.resize_start = (0, 0)
        self.start_size  = (width, height)
        self.drag_start  = (0, 0)
        self.size        = (width, height)
        self.locked      = False
        self.custom_alpha = None
        self._ctx_menu   = None

        self._docking_enabled = False
        self.group = None
        self.group_leader = None

        self.app = None

        FloatingWindow._all_windows.append(self)
        self._bind_events()

        self.top.after(50, self._do_initial_draw)

    def _safe_draw(self):
        try:
            self.draw()
        except AttributeError:
            pass
        except Exception as e:
            activity_log.log("draw_exception", self.title_text, str(e))

    def _bind_events(self) -> None:
        c = self.canvas
        c.bind("<Button-1>",        self._on_press)
        c.bind("<B1-Motion>",       self._on_move)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<Double-Button-1>", self.toggle_fullscreen)
        self.top.bind("<Escape>",   self._on_escape)
        c.bind("<Button-3>",        self._show_context_menu)

    def _on_press(self, event) -> None:
        if self.locked:
            return
        if self._close_click(event):
            self.destroy()
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if not self.fullscreen and event.x > cw - self.GRIP and event.y > ch - self.GRIP:
            self.resizing    = True
            self.resize_start = (event.x_root, event.y_root)
            self.start_size  = (self.top.winfo_width(), self.top.winfo_height())
        else:
            self.drag_start = (event.x, event.y)
            self.resizing   = False

    def _on_move(self, event) -> None:
        if self.locked:
            return
        if self.resizing:
            dx = event.x_root - self.resize_start[0]
            dy = event.y_root - self.resize_start[1]
            nw = max(80, self.start_size[0] + dx)
            nh = max(80, self.start_size[1] + dy)
            self.top.geometry(f"{nw}x{nh}")
        else:
            dx = event.x_root - self.drag_start[0]
            dy = event.y_root - self.drag_start[1]

            if self.group:
                for win in self.group:
                    if win is self:
                        continue
                    x = win.top.winfo_x() + dx
                    y = win.top.winfo_y() + dy
                    win.top.geometry(f"+{x}+{y}")

            x = event.x_root - self.drag_start[0]
            y = event.y_root - self.drag_start[1]
            self.top.geometry(f"+{x}+{y}")

            if self._docking_enabled:
                self._check_docking()

    def _check_docking(self):
        if self.locked or not self._docking_enabled:
            return

        x1, y1 = self.top.winfo_x(), self.top.winfo_y()
        w1, h1 = self.top.winfo_width(), self.top.winfo_height()

        candidates = [w for w in FloatingWindow._all_windows
                      if w is not self and (not self.group or w not in self.group)]

        for other in candidates:
            x2, y2 = other.top.winfo_x(), other.top.winfo_y()
            w2, h2 = other.top.winfo_width(), other.top.winfo_height()

            # Compute overlap and gaps
            # Overlap in x: positive if windows overlap horizontally
            overlap_x = min(x1 + w1, x2 + w2) - max(x1, x2)
            overlap_y = min(y1 + h1, y2 + h2) - max(y1, y2)

            # Gaps: positive if separated, negative if overlapping
            if x1 + w1 <= x2:
                gap_x = x2 - (x1 + w1)   # self is left of other
                side = 'left'
            elif x2 + w2 <= x1:
                gap_x = x1 - (x2 + w2)   # self is right of other
                side = 'right'
            else:
                gap_x = -overlap_x       # overlapping
                side = 'overlap_x'

            if y1 + h1 <= y2:
                gap_y = y2 - (y1 + h1)   # self is above other
                side_y = 'above'
            elif y2 + h2 <= y1:
                gap_y = y1 - (y2 + h2)   # self is below other
                side_y = 'below'
            else:
                gap_y = -overlap_y       # overlapping
                side_y = 'overlap_y'

            # Determine if we should snap
            # If windows are separated by a small gap (≤ threshold) OR if they overlap
            should_snap = (gap_x >= 0 and gap_x <= self.DOCK_THRESHOLD) or \
                          (gap_y >= 0 and gap_y <= self.DOCK_THRESHOLD) or \
                          (overlap_x > 0 and overlap_y > 0)  # overlapping

            if not should_snap:
                continue

            # Decide snap direction: prefer horizontal if overlap_x is larger (i.e., more vertical overlap)
            # That means we should separate horizontally.
            if overlap_x > overlap_y:
                # Separate horizontally
                if gap_x >= 0:
                    # Already separated -> align edges
                    if side == 'left':
                        new_x = x2 - w1
                    else:  # right
                        new_x = x2 + w2
                else:
                    # Overlapping -> push to the side with less overlap
                    overlap_left = (x1 + w1) - x2   # how much self extends to the right of other's left
                    overlap_right = (x2 + w2) - x1  # how much other extends to the right of self's left
                    if overlap_left < overlap_right:
                        # push self to left of other
                        new_x = x2 - w1
                    else:
                        # push self to right of other
                        new_x = x2 + w2
                new_y = y1
            else:
                # Separate vertically
                if gap_y >= 0:
                    if side_y == 'above':
                        new_y = y2 - h1
                    else:  # below
                        new_y = y2 + h2
                else:
                    overlap_above = (y1 + h1) - y2
                    overlap_below = (y2 + h2) - y1
                    if overlap_above < overlap_below:
                        new_y = y2 - h1
                    else:
                        new_y = y2 + h2
                new_x = x1

            # Clamp to screen to prevent off‑screen placement
            screen_w = self.top.winfo_screenwidth()
            screen_h = self.top.winfo_screenheight()
            new_x = max(0, min(new_x, screen_w - w1))
            new_y = max(0, min(new_y, screen_h - h1))

            # Only move if position changed significantly (avoid flicker)
            if abs(new_x - x1) > 1 or abs(new_y - y1) > 1:
                self.top.geometry(f"+{new_x}+{new_y}")
                print(f"[DOCK] Snapped {self.title_text} to ({new_x}, {new_y})")

            self._form_group(other)
            self._flash_snap()
            return

        # Undock if moved far from leader
        if self.group and self.group_leader is not self:
            leader = self.group_leader
            lx, ly = leader.top.winfo_x(), leader.top.winfo_y()
            if math.hypot(x1 - lx, y1 - ly) > 60:  # UNDOCK_THRESHOLD
                self._ungroup()

    def _form_group(self, other):
        if not self.group:
            if not other.group:
                group = [self, other]
                self.group = group
                other.group = group
                self.group_leader = self
                other.group_leader = self
            else:
                other.group.append(self)
                self.group = other.group
                self.group_leader = other.group_leader
        else:
            if not other.group:
                self.group.append(other)
                other.group = self.group
                other.group_leader = self.group_leader
            else:
                if self.group is not other.group:
                    self.group.extend(other.group)
                    for w in other.group:
                        w.group = self.group
                        w.group_leader = self.group_leader
                    other.group = self.group

    def _flash_snap(self):
        orig = self.canvas["bg"]
        self.canvas["bg"] = "#00ffcc"
        self.top.after(200, lambda: self.canvas.config(bg=orig))

    def _ungroup(self):
        if self.group:
            self.group.remove(self)
            self.group = None
            self.group_leader = None
            print(f"[DOCK] Ungrouped {self.title_text}")

    def _on_release(self, event) -> None:
        self.resizing = False
        self.save_geometry()

    def _close_click(self, event) -> bool:
        if self.locked:
            return False
        w = self.canvas.winfo_width()
        return w - 20 <= event.x <= w and 0 <= event.y <= 20

    def _on_escape(self, event=None) -> None:
        if not self.locked:
            self.destroy()

    def toggle_fullscreen(self, event=None) -> None:
        if self.locked:
            return
        if self.fullscreen:
            self.top.geometry(self.orig_geom)
            self.fullscreen = False
        else:
            self.orig_geom = self.top.geometry()
            sw = self.top.winfo_screenwidth()
            sh = self.top.winfo_screenheight()
            self.top.geometry(f"{sw}x{sh}+0+0")
            self.fullscreen = True

    def draw(self) -> None:
        pass

    def _do_initial_draw(self) -> None:
        try:
            self.draw()
        except Exception as e:
            activity_log.log("draw_error", self.title_text, str(e))
        if self.canvas.winfo_width() < 10:
            self.top.after(100, self.draw)

    def _schedule_initial_draw(self) -> None:
        self.top.after(50, self._do_initial_draw)

    def save_geometry(self) -> None:
        geom = self.top.geometry()
        if hasattr(self, "timer") and self.app:
            self.timer.floating_geometry = geom
            self.app.timer_manager.save()
        elif hasattr(self, "alarm") and self.app:
            self.alarm.floating_geometry = geom
            self.app.alarm_manager.save()
        elif hasattr(self, "stopwatch") and self.app:
            self.stopwatch.floating_geometry = geom
            self.app.stopwatch_manager.save()

    def apply_lock_state(self, locked: bool) -> None:
        self.locked = locked
        if locked:
            self.top.attributes("-topmost", True)
        self.draw()

    def destroy(self, event=None) -> None:
        if self.after_id:
            try:
                self.top.after_cancel(self.after_id)
            except Exception:
                pass
        if self in FloatingWindow._all_windows:
            FloatingWindow._all_windows.remove(self)
        if self.group:
            self._ungroup()
        if hasattr(self, "on_destroy"):
            self.on_destroy()
        try:
            self.top.destroy()
        except Exception:
            pass

    def _show_context_menu(self, event) -> None:
        if self._ctx_menu is not None:
            try:
                self._ctx_menu.destroy()
            except Exception as exc:
                activity_log.log("context_menu_cleanup_failed", "", str(exc))
            self._ctx_menu = None

        menu = tk.Menu(self.top, tearoff=0)

        lock_label = "🔒 Lock" if not self.locked else "🔓 Unlock"
        menu.add_command(label=lock_label, command=self._toggle_lock)

        dock_label = "Enable Docking" if not self._docking_enabled else "Disable Docking"
        menu.add_command(label=dock_label, command=self._toggle_docking)

        menu.add_command(label="Transparency…", command=self._open_transparency_dialog)
        menu.add_command(label="Toggle Always on Top", command=self._toggle_topmost)

        self._ctx_menu = menu
        menu.tk_popup(event.x_root, event.y_root)

    def _toggle_docking(self):
        self._docking_enabled = not self._docking_enabled
        activity_log.log("docking_toggle", self.title_text, str(self._docking_enabled))
        print(f"[DOCK] {self.title_text} docking {'enabled' if self._docking_enabled else 'disabled'}")

    def _toggle_topmost(self) -> None:
        cur = bool(self.top.attributes("-topmost"))
        self.top.attributes("-topmost", not cur)

    def _toggle_lock(self) -> None:
        new_locked = not self.locked
        self.apply_lock_state(new_locked)
        if hasattr(self, "timer") and self.app:
            self.timer.locked = new_locked
            self.app.timer_manager.save()
        elif hasattr(self, "alarm") and self.app:
            self.alarm.locked = new_locked
            self.app.alarm_manager.save()
        elif hasattr(self, "stopwatch") and self.app:
            self.stopwatch.locked = new_locked
            self.app.stopwatch_manager.save()

    def _open_transparency_dialog(self) -> None:
        dlg = tk.Toplevel(self.top)
        dlg.title("Transparency")
        dlg.geometry("250x80")
        dlg.transient(self.top)
        dlg.grab_set()
        ttk.Label(dlg, text="Opacity:").pack(pady=5)
        alpha_var = tk.DoubleVar(value=self.top.attributes("-alpha"))
        ttk.Scale(dlg, from_=0.1, to=1.0, variable=alpha_var,
                  orient="horizontal", length=200).pack(pady=5)

        def _apply(*_):
            val = alpha_var.get()
            self.top.attributes("-alpha", val)
            self.custom_alpha = val
            if hasattr(self, "timer") and self.app:
                self.timer.floating_alpha = val
                self.app.timer_manager.save()
            elif hasattr(self, "alarm") and self.app:
                self.alarm.floating_alpha = val
                self.app.alarm_manager.save()
            elif hasattr(self, "stopwatch") and self.app:
                self.stopwatch.floating_alpha = val
                self.app.stopwatch_manager.save()

        alpha_var.trace_add("write", _apply)
        dlg.wait_window()

        