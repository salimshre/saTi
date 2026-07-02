"""
ui/floating/base.py – Floating window with docking support.
"""

import math
import tkinter as tk
from tkinter import ttk
import time

from core.logger import activity_log
from ui.icon import get_logo_photoimage
from ui.floating.dock_manager import dock_manager, DockGroup


class FloatingWindow:
    GRIP = 12
    DOCK_THRESHOLD = 30          # pixels to trigger snap
    UNDOCK_THRESHOLD = 80        # pixels away to break group
    _all_windows = []

    def __init__(self, master, settings, theme_manager,
                 width: int = 160, height: int = 160, title: str = ""):
        self.master = master
        self.settings = settings
        self.theme_manager = theme_manager
        self.title_text = title

        # ---- Toplevel window ----
        self.top = tk.Toplevel(master)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", settings.get("always_on_top", True))
        self.top.attributes("-alpha", settings.get("transparency", 0.85))
        self.top.geometry(f"{width}x{height}+100+100")

        # Set custom icon
        logo = get_logo_photoimage()
        if logo:
            self.top.iconphoto(False, logo)

        canvas_bg = theme_manager.current.get("canvas_bg", "#000000")
        self.top.configure(bg=canvas_bg)

        self.canvas = tk.Canvas(self.top, highlightthickness=0)
        theme_manager.apply(self.canvas)
        self.canvas.pack(expand=True, fill="both")
        self.canvas.bind("<Configure>", lambda e: self._safe_draw())

        # ---- state ----
        self.running = True
        self.after_id = None
        self.fullscreen = False
        self.orig_geom = ""
        self.resizing = False
        self.resize_start = (0, 0)
        self.start_size = (width, height)
        self.drag_start = (0, 0)          # mouse offset inside window
        self.size = (width, height)
        self.locked = False
        self.custom_alpha = None
        self._ctx_menu = None

        # ---- drag origin for correct delta calculation ----
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._leader_start_x = 0
        self._leader_start_y = 0

        # ---- docking (managed by DockManager) ----
        self._docking_enabled = False
        self.group = None          # will reference a DockGroup
        self.group_leader = None   # the window that leads the group
        self._preserve_on_destroy = False  # used during restart
        self._preview_target = None  # window currently highlighted as a live snap candidate

        self.app = None

        # Register with the dock manager
        FloatingWindow._all_windows.append(self)
        dock_manager.register(self)

        self._bind_events()
        self.top.after(50, self._do_initial_draw)

    # ------------------------------------------------------------------
    # Event binding
    # ------------------------------------------------------------------
    def _bind_events(self) -> None:
        c = self.canvas
        c.bind("<Button-1>", self._on_press)
        c.bind("<B1-Motion>", self._on_move)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<Double-Button-1>", self.toggle_fullscreen)
        self.top.bind("<Escape>", self._on_escape)
        c.bind("<Button-3>", self._show_context_menu)

    def _safe_draw(self):
        try:
            self.draw()
        except Exception as e:
            activity_log.log("draw_exception", self.title_text, str(e))

    # ------------------------------------------------------------------
    # Mouse handling
    # ------------------------------------------------------------------
    def _on_press(self, event) -> None:
        if self.locked:
            return
        if self._close_click(event):
            self.destroy()
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if not self.fullscreen and event.x > cw - self.GRIP and event.y > ch - self.GRIP:
            self.resizing = True
            self.resize_start = (event.x_root, event.y_root)
            self.start_size = (self.top.winfo_width(), self.top.winfo_height())
        else:
            # Store drag origin for correct delta calculation
            self._drag_start_x = event.x_root
            self._drag_start_y = event.y_root
            self._leader_start_x = self.top.winfo_x()
            self._leader_start_y = self.top.winfo_y()
            self.drag_start = (event.x, event.y)  # may be used by subclasses
            self.resizing = False

    def _on_move(self, event) -> None:
        if self.locked:
            return
        if self.resizing:
            dx = event.x_root - self.resize_start[0]
            dy = event.y_root - self.resize_start[1]
            nw = max(80, self.start_size[0] + dx)
            nh = max(80, self.start_size[1] + dy)
            self.top.geometry(f"{nw}x{nh}")
            return

        # Compute delta from the original click position
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y

        # Determine the new leader position
        new_leader_x = self._leader_start_x + dx
        new_leader_y = self._leader_start_y + dy

        if self.group:
            # Move the whole group via the manager
            if isinstance(self.group, DockGroup):
                # Compute delta from leader's current position to avoid accumulation
                current_x, current_y = self.top.winfo_x(), self.top.winfo_y()
                delta_x = new_leader_x - current_x
                delta_y = new_leader_y - current_y
                self.group.move_by(delta_x, delta_y)
        else:
            # Move the single window
            self.top.geometry(f"+{new_leader_x}+{new_leader_y}")

        self._update_snap_preview()

    def _on_release(self, event) -> None:
        self.resizing = False
        self.save_geometry()
        self._clear_snap_preview()

        if not self.locked and self._docking_enabled:
            # If we're a non-leader member, check whether this drag pulled
            # us far enough from our leader to break free of the group.
            # This is independent of group size -- belonging to a group
            # should never by itself prevent us from *also* trying to dock
            # onto a new window below (that's exactly how a group grows
            # past 2 members).
            if self.group and self.group_leader is not self:
                leader = self.group_leader
                lx, ly = leader.top.winfo_x(), leader.top.winfo_y()
                x, y = self.top.winfo_x(), self.top.winfo_y()
                if math.hypot(x - lx, y - ly) > self.UNDOCK_THRESHOLD:
                    dock_manager.undock(self)
                    return

            # Try to dock with another window, or -- if we're already in a
            # group -- extend that group with a new neighbor. This must
            # run even when the group already has 2+ members: that's
            # exactly the case of dragging an existing pair/cluster over
            # to pick up a third window. Skipping it here silently
            # disabled docking for anything past the first two windows.
            docked = dock_manager.try_dock(self)
            if docked:
                self._flash_snap()

    def _close_click(self, event) -> bool:
        if self.locked:
            return False
        w = self.canvas.winfo_width()
        return w - 20 <= event.x <= w and 0 <= event.y <= 20

    def _on_escape(self, event=None) -> None:
        if not self.locked:
            self.destroy()

    # ------------------------------------------------------------------
    # Docking feedback
    # ------------------------------------------------------------------
    def _flash_snap(self):
        orig = self.canvas["bg"]
        self.canvas["bg"] = "#00ffcc"
        self.top.after(200, lambda: self.canvas.config(bg=orig))

    SNAP_PREVIEW_COLOR = "#00ffcc"  # matches _flash_snap's confirm color

    def _update_snap_preview(self) -> None:
        """Called on every drag-move: highlight the window we'd dock to
        if released right now, so the user gets feedback before committing
        instead of only finding out at release time."""
        if self.locked or not self._docking_enabled:
            self._clear_snap_preview()
            return

        others = [w for w in FloatingWindow._all_windows if w is not self]
        target = dock_manager.preview_snap_target(self, others)

        if target is self._preview_target:
            return  # unchanged since last event, nothing to redraw

        self._clear_snap_preview()
        if target is not None:
            self._set_preview_highlight(self.canvas)
            self._set_preview_highlight(target.canvas)
            self._preview_target = target

    def _set_preview_highlight(self, canvas) -> None:
        try:
            canvas.configure(
                highlightthickness=3,
                highlightbackground=self.SNAP_PREVIEW_COLOR,
                highlightcolor=self.SNAP_PREVIEW_COLOR,
            )
        except Exception:
            pass

    def _clear_snap_preview(self) -> None:
        try:
            self.canvas.configure(highlightthickness=0)
        except Exception:
            pass
        if self._preview_target is not None:
            try:
                self._preview_target.canvas.configure(highlightthickness=0)
            except Exception:
                pass
            self._preview_target = None

    # ------------------------------------------------------------------
    # Toggle fullscreen
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Drawing and updates
    # ------------------------------------------------------------------
    def draw(self) -> None:
        """Override in subclasses."""
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

        self._clear_snap_preview()
        # If another window is currently highlighting *this* one as its
        # live snap-preview target, clear that too, or it'd keep pointing
        # at a widget that no longer exists.
        for w in FloatingWindow._all_windows:
            if w is not self and w._preview_target is self:
                w._clear_snap_preview()

        # Unregister from dock manager
        dock_manager.unregister(self)

        if self in FloatingWindow._all_windows:
            FloatingWindow._all_windows.remove(self)

        if hasattr(self, "on_destroy"):
            self.on_destroy()
        try:
            self.top.destroy()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------
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
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            # tk_popup() grabs the pointer but never releases it on its
            # own. Without releasing here, the first click on a menu item
            # (on X11 especially) just dismisses the menu instead of
            # firing its command -- you'd have to open the menu and click
            # the item a second time for it to actually take effect.
            menu.grab_release()

    def _toggle_docking(self):
        self._docking_enabled = not self._docking_enabled
        activity_log.log("docking_toggle", self.title_text, str(self._docking_enabled))
        if not self._docking_enabled:
            self._clear_snap_preview()
            if self.group:
                # Disabling docking: break the group
                dock_manager.undock(self)

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