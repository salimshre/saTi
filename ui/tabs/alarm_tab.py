"""Alarm tab controller."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ui.dialogs import AlarmEditDialog
from ui.floating import FloatingAlarmWindow


class AlarmTab:
    def __init__(self, app, notebook: ttk.Notebook) -> None:
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Alarms")
        self.tree = None
        self.setup()

    def setup(self) -> None:
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", pady=5)
        for text, command in [
            ("New Alarm", self.new_item),
            ("Edit Selected", self.edit_selected),
            ("Delete Selected", self.delete_selected),
            ("Toggle Floating", self.toggle_floating),
            ("Refresh", self.load_list),
        ]:
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=5)

        columns = ("name", "type", "next_trigger", "enabled", "show")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings")
        for column, heading in zip(columns, ("Name", "Type", "Next Trigger", "Enabled", "Floating"), strict=True):
            self.tree.heading(column, text=heading)
        self.tree.column("show", width=60)
        self.tree.pack(expand=True, fill="both")
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected())

    def _on_tree_click(self, event) -> None:
        if self.tree.identify_region(event.x, event.y) == "cell" and self.tree.identify_column(event.x) == "#5":
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.toggle_floating()

    def load_list(self) -> None:
        selected = set(self.tree.selection())
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows_to_reselect = []
        self.app.alarm_manager.update()
        for alarm in self.app.alarm_manager.alarms:
            nxt = alarm.next_trigger.strftime("%Y-%m-%d %H:%M") if alarm.next_trigger else "N/A"
            self.tree.insert(
                "",
                "end",
                iid=alarm.id,
                values=(alarm.name, alarm.type, nxt, "Yes" if alarm.enabled else "No", "Open" if alarm.show_floating else "Close"),
            )
            if alarm.id in selected:
                rows_to_reselect.append(alarm.id)
        if rows_to_reselect:
            self.tree.selection_set(rows_to_reselect)

    def selected_ids(self) -> tuple[str, ...]:
        return self.tree.selection()

    def new_item(self) -> None:
        dialog = AlarmEditDialog(self.app.root, self.app.settings, self.app.theme_manager)
        self.app.root.wait_window(dialog)
        if dialog.result:
            self.app.alarm_manager.add(dialog.result)
            self.load_list()

    def edit_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            messagebox.showinfo("Edit", "Select an alarm to edit.")
            return
        alarm = self.app.alarm_manager.get(selection[0])
        if not alarm:
            return
        dialog = AlarmEditDialog(self.app.root, self.app.settings, self.app.theme_manager, alarm=alarm)
        self.app.root.wait_window(dialog)
        if not dialog.result:
            return

        updated = dialog.result
        preserved = {
            "id": alarm.id,
            "next_trigger": alarm.next_trigger,
            "show_floating": alarm.show_floating,
            "locked": alarm.locked,
            "floating_geometry": alarm.floating_geometry,
            "floating_alpha": alarm.floating_alpha,
        }
        alarm.__dict__.update(updated.__dict__)
        alarm.__dict__.update(preserved)
        self.app.alarm_manager.update()
        self.load_list()
        self._refresh_floating_window(alarm.id)

    def _refresh_floating_window(self, alarm_id: str) -> None:
        if alarm_id not in self.app.open_alarm_windows:
            return
        self.app.open_alarm_windows[alarm_id].destroy()
        del self.app.open_alarm_windows[alarm_id]
        alarm = self.app.alarm_manager.get(alarm_id)
        if alarm:
            win = FloatingAlarmWindow(self.app.root, self.app.settings, self.app.theme_manager, alarm, app=self.app)
            self.app.open_alarm_windows[alarm_id] = win
            win.top.protocol("WM_DELETE_WINDOW", lambda _id=alarm_id: self.app.on_alarm_window_close(_id))

    def delete_selected(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        if not messagebox.askyesno("Delete Alarm", f"Delete {len(selection)} selected alarm(s)?"):
            return
        for alarm_id in selection:
            win = self.app.open_alarm_windows.pop(alarm_id, None)
            if win:
                win.destroy()
            self.app.alarm_manager.remove(alarm_id)
        self.load_list()

    def toggle_floating(self) -> None:
        selection = self.selected_ids()
        if not selection:
            return
        alarm_id = selection[0]
        win = self.app.open_alarm_windows.pop(alarm_id, None)
        if win:
            win.destroy()
        else:
            alarm = self.app.alarm_manager.get(alarm_id)
            if alarm:
                win = FloatingAlarmWindow(self.app.root, self.app.settings, self.app.theme_manager, alarm, app=self.app)
                self.app.open_alarm_windows[alarm_id] = win
                win.top.protocol("WM_DELETE_WINDOW", lambda _id=alarm_id: self.app.on_alarm_window_close(_id))
        self.load_list()

    def toggle_floating_for_restore(self, alarm) -> None:
        win = FloatingAlarmWindow(self.app.root, self.app.settings, self.app.theme_manager, alarm, app=self.app)
        self.app.open_alarm_windows[alarm.id] = win
        win.top.protocol("WM_DELETE_WINDOW", lambda _id=alarm.id: self.app.on_alarm_window_close(_id))
