"""Stopwatch tab controller."""

from __future__ import annotations

import time as time_mod
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from core.logger import activity_log
from models import Stopwatch
from ui.floating import StopwatchWindow


class StopwatchTab:
    def __init__(self, app, notebook: ttk.Notebook) -> None:
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Stopwatches")
        self.tree = None
        self.lap_list = None
        self.setup()

    def setup(self) -> None:
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", pady=5)
        for text, command in [
            ("New Stopwatch", self.new_item),
            ("Edit Label", self.edit_selected),
            ("Delete Selected", self.delete_selected),
            ("Start/Stop", self.toggle_running),
            ("Reset", self.reset_selected),
            ("Record Lap", self.record_lap),
            ("Toggle Floating", self.toggle_floating),
            ("Refresh", self.load_list),
        ]:
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=5)

        content = ttk.Panedwindow(self.frame, orient=tk.HORIZONTAL)
        content.pack(expand=True, fill="both")

        list_frame = ttk.Frame(content)
        lap_frame = ttk.Frame(content)
        content.add(list_frame, weight=3)
        content.add(lap_frame, weight=2)

        columns = ("label", "elapsed", "status", "show")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        for column, heading in zip(columns, ("Label", "Elapsed", "Status", "Floating"), strict=True):
            self.tree.heading(column, text=heading)
        self.tree.column("show", width=60)
        self.tree.pack(expand=True, fill="both")
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.load_laps())
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected())

        ttk.Label(lap_frame, text="Lap Times").pack(anchor="w", padx=8, pady=(6, 2))
        self.lap_list = tk.Listbox(lap_frame, height=12)
        self.lap_list.pack(expand=True, fill="both", padx=8, pady=(0, 8))

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
        for stopwatch in self.app.stopwatch_manager.stopwatches:
            elapsed = stopwatch.elapsed()
            h, rem = divmod(int(elapsed), 3600)
            m, s = divmod(rem, 60)
            ms = int((elapsed - int(elapsed)) * 100)
            display = f"{h:02d}:{m:02d}:{s:02d}.{ms:02d}" if h > 0 else f"{m:02d}:{s:02d}.{ms:02d}"
            self.tree.insert(
                "",
                "end",
                iid=stopwatch.id,
                values=(stopwatch.label, display, stopwatch.status.capitalize(), "Open" if stopwatch.show_floating else "Close"),
            )
            if stopwatch.id in selected:
                rows_to_reselect.append(stopwatch.id)
        if rows_to_reselect:
            self.tree.selection_set(rows_to_reselect)
        self.load_laps()

    def load_laps(self) -> None:
        self.lap_list.delete(0, tk.END)
        selection = self.selected_ids()
        if not selection:
            return
        stopwatch = self.app.stopwatch_manager.get(selection[0])
        if not stopwatch:
            return
        for index, lap in enumerate(stopwatch.lap_times, start=1):
            h, rem = divmod(int(lap), 3600)
            m, s = divmod(rem, 60)
            ms = int((lap - int(lap)) * 100)
            display = f"{h:02d}:{m:02d}:{s:02d}.{ms:02d}" if h > 0 else f"{m:02d}:{s:02d}.{ms:02d}"
            self.lap_list.insert(tk.END, f"Lap {index}: {display}")

    def selected_ids(self) -> tuple[str, ...]:
        return self.tree.selection()

    def new_item(self) -> None:
        label = simpledialog.askstring("Stopwatch Label", "Label:", parent=self.app.root)
        if label is None:
            return
        self.app.stopwatch_manager.add(Stopwatch(label=label.strip() or "Stopwatch"))
        self.load_list()

    def edit_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            messagebox.showinfo("Edit", "Select a stopwatch to edit its label.")
            return
        stopwatch = self.app.stopwatch_manager.get(selection[0])
        if not stopwatch:
            return
        new_label = simpledialog.askstring("Edit Label", "New label:", initialvalue=stopwatch.label, parent=self.app.root)
        if new_label is not None:
            stopwatch.label = new_label.strip() or stopwatch.label
            self.app.stopwatch_manager.save()
            self.load_list()
            if stopwatch.id in self.app.open_stopwatch_windows:
                self.app.open_stopwatch_windows[stopwatch.id].draw()

    def delete_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        if not messagebox.askyesno("Delete Stopwatch", f"Delete {len(selection)} selected stopwatch(es)?"):
            return
        for stopwatch_id in selection:
            win = self.app.open_stopwatch_windows.pop(stopwatch_id, None)
            if win:
                win.destroy()
            self.app.stopwatch_manager.remove(stopwatch_id)
        self.load_list()

    def toggle_running(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        stopwatch = self.app.stopwatch_manager.get(selection[0])
        if not stopwatch:
            return
        if stopwatch.status == "running":
            stopwatch.pause()
            activity_log.log("stopwatch_stopped", stopwatch.label, f"elapsed={stopwatch.elapsed_paused:.2f}s")
        else:
            stopwatch.start_or_resume()
            activity_log.log("stopwatch_started", stopwatch.label, f"elapsed_before={stopwatch.elapsed_paused:.2f}s")
        self.app.stopwatch_manager.save()
        self.load_list()

    def reset_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        stopwatch = self.app.stopwatch_manager.get(selection[0])
        if not stopwatch:
            return
        stopwatch.reset()
        self.app.stopwatch_manager.save()
        self.load_list()

    def record_lap(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        stopwatch = self.app.stopwatch_manager.get(selection[0])
        if not stopwatch or stopwatch.status not in ("running", "paused"):
            return
        elapsed = stopwatch.add_lap()
        if elapsed is None:
            return
        activity_log.log("stopwatch_lap", stopwatch.label, f"lap={len(stopwatch.lap_times)} elapsed={elapsed:.2f}s")
        self.app.stopwatch_manager.save()
        self.load_laps()
        if stopwatch.id in self.app.open_stopwatch_windows:
            self.app.open_stopwatch_windows[stopwatch.id].draw()

    def toggle_floating(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        stopwatch_id = selection[0]
        win = self.app.open_stopwatch_windows.pop(stopwatch_id, None)
        if win:
            win.destroy()
        else:
            stopwatch = self.app.stopwatch_manager.get(stopwatch_id)
            if stopwatch:
                win = StopwatchWindow(self.app.root, self.app.settings, self.app.theme_manager, stopwatch, app=self.app)
                self.app.open_stopwatch_windows[stopwatch_id] = win
                win.top.protocol("WM_DELETE_WINDOW", lambda _id=stopwatch_id: self.app.on_stopwatch_window_close(_id))
        self.load_list()

    def toggle_floating_for_restore(self, stopwatch) -> None:
        win = StopwatchWindow(self.app.root, self.app.settings, self.app.theme_manager, stopwatch, app=self.app)
        self.app.open_stopwatch_windows[stopwatch.id] = win
        win.top.protocol("WM_DELETE_WINDOW", lambda _id=stopwatch.id: self.app.on_stopwatch_window_close(_id))

    def refresh_runtime_state(self, now: float | None = None) -> None:
        now = now if now is not None else time_mod.time()
        existing = set(self.tree.get_children())
        manager_ids = {stopwatch.id for stopwatch in self.app.stopwatch_manager.stopwatches}
        if existing != manager_ids:
            self.load_list()
            return

        for stopwatch in self.app.stopwatch_manager.stopwatches:
            elapsed = stopwatch.elapsed(now)
            h, rem = divmod(int(elapsed), 3600)
            m, s = divmod(rem, 60)
            ms = int((elapsed - int(elapsed)) * 100)
            display = f"{h:02d}:{m:02d}:{s:02d}.{ms:02d}" if h > 0 else f"{m:02d}:{s:02d}.{ms:02d}"
            self.tree.item(
                stopwatch.id,
                values=(stopwatch.label, display, stopwatch.status.capitalize(), "Open" if stopwatch.show_floating else "Close"),
            )
        self.load_laps()
