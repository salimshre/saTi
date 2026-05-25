"""
ui/floating/base.py
FloatingWindow – borderless, draggable, resizable Toplevel.

BUG FIXES applied here
-----------------------
1. White window on launch
   • self.top is now themed (bg set to canvas_bg) immediately.
   • Subclasses call _schedule_initial_draw() instead of draw() directly;
     this waits 80 ms so the canvas has real pixel dimensions before painting.

2. Lock toggle not working
   • The old code bound <Unmap> → menu.destroy() which on Linux/X11 runs
     *before* the selected command callback, cancelling _toggle_lock.
   • Fix: use menu.tk_popup() (proper grab-aware popup) and never call
     menu.destroy() from inside an event handler.  The previous menu is
     destroyed only at the *start* of the next right-click.
"""
import tkinter as tk
from tkinter import ttk


class FloatingWindow:
    GRIP = 12  # resize-grip size in pixels

    def __init__(self, master, settings, theme_manager,
                 width: int = 160, height: int = 160, title: str = ""):
        self.master        = master
        self.settings      = settings
        self.theme_manager = theme_manager
        self.title_text    = title

        # ── Toplevel setup ─────────────────────────────────────────────
        self.top = tk.Toplevel(master)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", settings.get("always_on_top", True))
        self.top.attributes("-alpha",   settings.get("transparency", 0.85))
        self.top.geometry(f"{width}x{height}+100+100")

        # FIX 1a – theme the Toplevel background so no white flash appears
        canvas_bg = theme_manager.current.get("canvas_bg", "#000000")
        self.top.configure(bg=canvas_bg)

        # ── Canvas ─────────────────────────────────────────────────────
        self.canvas = tk.Canvas(self.top, highlightthickness=0)
        theme_manager.apply(self.canvas)         # sets canvas bg
        self.canvas.pack(expand=True, fill="both")
        # <Configure> fires whenever the canvas gets a new size (e.g. on
        # first show or after a resize).  It ensures painting happens even
        # if the scheduled initial draw fires too early.
        self.canvas.bind("<Configure>", lambda e: self.draw())

        # ── State ──────────────────────────────────────────────────────
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
        self._ctx_menu   = None    # track open context menu (prevents stacking)

        # Back-reference to the owning app (set by subclasses)
        self.app = None

        self._bind_events()

    # ── Event binding ──────────────────────────────────────────────────
    def _bind_events(self) -> None:
        c = self.canvas
        c.bind("<Button-1>",        self._on_press)
        c.bind("<B1-Motion>",       self._on_move)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<Double-Button-1>", self.toggle_fullscreen)
        self.top.bind("<Escape>",   self._on_escape)
        c.bind("<Button-3>",        self._show_context_menu)

    # ── Drag / resize ──────────────────────────────────────────────────
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
            x = event.x_root - self.drag_start[0]
            y = event.y_root - self.drag_start[1]
            self.top.geometry(f"+{x}+{y}")

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

    # ── Fullscreen ─────────────────────────────────────────────────────
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

    # ── Drawing (override in subclass) ─────────────────────────────────
    def draw(self) -> None:
        pass

    # FIX 1b – defer initial draw until the canvas has real dimensions
    def _schedule_initial_draw(self) -> None:
        """Call this from subclass __init__ instead of draw() directly."""
        self.top.after(80, self._do_initial_draw)

    def _do_initial_draw(self) -> None:
        self.draw()
        # If dimensions are still tiny, retry once more after another tick
        if self.canvas.winfo_width() < 10:
            self.top.after(100, self.draw)

    # ── Persistence helpers ─────────────────────────────────────────────
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

    # ── Lock ───────────────────────────────────────────────────────────
    def apply_lock_state(self, locked: bool) -> None:
        self.locked = locked
        if locked:
            self.top.attributes("-topmost", True)
        self.draw()

    # ── Destroy ────────────────────────────────────────────────────────
    def destroy(self, event=None) -> None:
        if self.after_id:
            try:
                self.top.after_cancel(self.after_id)
            except Exception:
                pass
        if hasattr(self, "on_destroy"):
            self.on_destroy()
        try:
            self.top.destroy()
        except Exception:
            pass

    # ── Context menu (right-click) ─────────────────────────────────────
    # FIX 2 – Use tk_popup (proper grab + cleanup) and never call
    #          menu.destroy() from inside an event handler.
    def _show_context_menu(self, event) -> None:
        # Destroy any leftover menu from a previous right-click
        if self._ctx_menu is not None:
            try:
                self._ctx_menu.destroy()
            except Exception:
                pass
            self._ctx_menu = None

        menu = tk.Menu(self.top, tearoff=0)

        lock_label = "🔒 Lock" if not self.locked else "🔓 Unlock"
        menu.add_command(label=lock_label, command=self._toggle_lock)
        menu.add_command(label="Transparency…", command=self._open_transparency_dialog)
        menu.add_command(label="Toggle Always on Top", command=self._toggle_topmost)

        self._ctx_menu = menu
        # tk_popup handles the X11 grab correctly and does NOT call destroy()
        # before the selected command runs – unlike menu.post() + <Unmap> destroy.
        menu.tk_popup(event.x_root, event.y_root)

    def _toggle_topmost(self) -> None:
        cur = bool(self.top.attributes("-topmost"))
        self.top.attributes("-topmost", not cur)

    def _toggle_lock(self) -> None:
        new_locked = not self.locked
        self.apply_lock_state(new_locked)
        # Persist to model
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
