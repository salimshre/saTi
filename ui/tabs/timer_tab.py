"""Timer tab controller."""

from __future__ import annotations

import time as time_mod
import tkinter as tk
from tkinter import messagebox, ttk

from core.logger import activity_log
from models import Timer
from ui.dialogs import TimerCreateDialog, TimerEditDialog
from ui.floating import CountdownWindow


class TimerTab:
    def __init__(self, app, notebook: ttk.Notebook) -> None:
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Timers")
        self.tree = None
        self.setup()

    def setup(self) -> None:
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", pady=5)
        for text, command in [
            ("New Countdown", self.new_item),
            ("Edit Selected", self.edit_selected),
            ("Delete Selected", self.delete_selected),
            ("Pause/Resume", self.toggle_pause),
            ("Reset", self.reset_selected),
            ("Toggle Floating", self.toggle_floating),
            ("Refresh", self.load_list),
        ]:
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=5)

        columns = ("label", "remaining", "status", "show")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings")
        for column, heading in zip(columns, ("Label", "Remaining", "Status", "Floating")):
            self.tree.heading(column, text=heading)
        self.tree.column("show", width=60)
        self.tree.pack(expand=True, fill="both")
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected())

    def _on_tree_click(self, event) -> None:
        if self.tree.identify_region(event.x, event.y) == "cell" and self.tree.identify_column(event.x) == "#4":
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.toggle_floating()

    def load_list(self) -> None:
        selected = set(self.tree.selection())
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows_to_reselect = []
        for timer in self.app.timer_manager.timers:
            timer.sync_state()
            rem = self._format_remaining(timer.current_remaining())
            self.tree.insert(
                "",
                "end",
                iid=timer.id,
                values=(timer.label, rem, timer.status.capitalize(), "Open" if timer.show_floating else "Close"),
            )
            if timer.id in selected:
                rows_to_reselect.append(timer.id)
        if rows_to_reselect:
            self.tree.selection_set(rows_to_reselect)

    def selected_ids(self) -> tuple[str, ...]:
        return self.tree.selection()

    def new_item(self) -> None:
        dialog = TimerCreateDialog(self.app.root)
        self.app.root.wait_window(dialog)
        if dialog.result:
            timer = Timer(label=dialog.result["label"], duration=dialog.result["duration"])
            self.app.timer_manager.add(timer)
            activity_log.log("timer_created", timer.label, f"duration={timer.duration}s")
            self.load_list()

    def edit_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            messagebox.showinfo("Edit", "Select a timer to edit.")
            return
        timer = self.app.timer_manager.get(selection[0])
        if not timer:
            return
        dialog = TimerEditDialog(self.app.root, timer)
        self.app.root.wait_window(dialog)
        if dialog.result:
            timer.label = dialog.result["label"]
            timer.duration = float(dialog.result["duration"])
            if timer.remaining > timer.duration:
                timer.remaining = timer.duration
            if timer.status == "running":
                timer.last_started_at = time_mod.time()
            self.app.timer_manager.save()
            self.load_list()
            if timer.id in self.app.open_timer_windows:
                win = self.app.open_timer_windows[timer.id]
                win.time_left = timer.current_remaining()
                win.draw()

    def delete_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        if not messagebox.askyesno("Delete Timer", f"Delete {len(selection)} selected timer(s)?"):
            return
        for timer_id in selection:
            win = self.app.open_timer_windows.pop(timer_id, None)
            if win:
                win.destroy()
            self.app.timer_manager.remove(timer_id)
        self.load_list()

    def toggle_pause(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        timer = self.app.timer_manager.get(selection[0])
        if not timer or timer.status not in ("running", "paused"):
            return
        if timer.status == "running":
            timer.pause()
        else:
            timer.resume()
        self.app.timer_manager.save()
        if timer.id in self.app.open_timer_windows:
            self.app.open_timer_windows[timer.id].paused = timer.status != "running"
            self.app.open_timer_windows[timer.id].time_left = timer.current_remaining()
        self.load_list()

    def reset_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        timer = self.app.timer_manager.get(selection[0])
        if not timer:
            return
        timer.reset()
        self.app.timer_manager.save()
        if timer.id in self.app.open_timer_windows:
            win = self.app.open_timer_windows[timer.id]
            win.time_left = timer.remaining
            win.paused = True
            win.draw()
        self.load_list()

    def toggle_floating(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        timer_id = selection[0]
        win = self.app.open_timer_windows.pop(timer_id, None)
        if win:
            win.destroy()
        else:
            timer = self.app.timer_manager.get(timer_id)
            if timer:
                win = CountdownWindow(
                    self.app.root,
                    self.app.settings,
                    self.app.theme_manager,
                    timer,
                    self.app.settings.get("tick_threshold", 10),
                    app=self.app,
                )
                self.app.open_timer_windows[timer_id] = win
                win.top.protocol("WM_DELETE_WINDOW", lambda _id=timer_id: self.app.on_timer_window_close(_id))
        self.load_list()

    def toggle_floating_for_restore(self, timer) -> None:
        win = CountdownWindow(
            self.app.root,
            self.app.settings,
            self.app.theme_manager,
            timer,
            self.app.settings.get("tick_threshold", 10),
            app=self.app,
        )
        self.app.open_timer_windows[timer.id] = win
        win.top.protocol("WM_DELETE_WINDOW", lambda _id=timer.id: self.app.on_timer_window_close(_id))

    def refresh_runtime_state(self, now: float | None = None) -> None:
        now = now if now is not None else time_mod.time()
        existing = set(self.tree.get_children())
        manager_ids = {timer.id for timer in self.app.timer_manager.timers}
        if existing != manager_ids:
            self.load_list()
            return

        completed_ids = []
        for timer in self.app.timer_manager.timers:
            previous_status = timer.status
            timer.sync_state(now)
            if previous_status != "completed" and timer.status == "completed":
                completed_ids.append(timer.id)
            self.tree.item(
                timer.id,
                values=(
                    timer.label,
                    self._format_remaining(timer.current_remaining(now)),
                    timer.status.capitalize(),
                    "Open" if timer.show_floating else "Close",
                ),
            )
            if timer.id in self.app.open_timer_windows:
                self.app.open_timer_windows[timer.id].time_left = timer.current_remaining(now)
                self.app.open_timer_windows[timer.id].paused = timer.status != "running"
        if completed_ids:
            self.app.timer_manager.save()

    @staticmethod
    def _format_remaining(remaining: float) -> str:
        if remaining <= 0:
            return "00:00"
        total_secs = int(remaining)
        return f"{total_secs // 60:02d}:{total_secs % 60:02d}"