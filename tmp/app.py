"""Main application window for SaTi."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from core.ring import ring_controller
from models import AlarmManager, StopwatchManager, TimerManager
from ui.app_meta import APP_NAME, APP_VERSION
from ui.icon import apply_app_icon
from ui.scheduler import AppScheduler
from ui.tabs import AlarmTab, StopwatchTab, TimerTab
from ui.tray import TrayManager

from .themes import ThemeManager


class AlarmClockApp:
    def __init__(
        self,
        root: tk.Tk,
        settings,
        alarm_manager: AlarmManager,
        timer_manager: TimerManager,
        stopwatch_manager: StopwatchManager,
        theme_manager: ThemeManager,
    ):
        self.root = root
        self.settings = settings
        self.alarm_manager = alarm_manager
        self.timer_manager = timer_manager
        self.stopwatch_manager = stopwatch_manager
        self.theme_manager = theme_manager

        self.open_alarm_windows = {}
        self.open_timer_windows = {}
        self.open_stopwatch_windows = {}

        self.scheduler = AppScheduler(self)
        self.tray = TrayManager(self)

        root.title(APP_NAME)
        root.geometry("960x640")
        apply_app_icon(root)

        self._create_menu()
        self._create_notebook()
        self._create_status_bar()
        self._bind_shortcuts()
        self.load_all_lists()
        self.scheduler.start()
        self._restore_open_windows()
        root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

    def _create_menu(self) -> None:
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Settings", command=self.open_settings)
        file_menu.add_command(label="Minimize to Tray", command=self.minimize_to_tray)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data...", command=self.export_data)
        file_menu.add_command(label="Import Data...", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application)
        menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def _create_notebook(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.alarm_tab = AlarmTab(self, self.notebook)
        self.timer_tab = TimerTab(self, self.notebook)
        self.stopwatch_tab = StopwatchTab(self, self.notebook)

    def _create_status_bar(self) -> None:
        self.status_var = tk.StringVar(value=f"{APP_NAME} v{APP_VERSION}")
        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w")
        status.pack(fill="x", padx=8, pady=(0, 6))

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-n>", self._shortcut_new)
        self.root.bind("<Delete>", self._shortcut_delete)
        self.root.bind("<space>", self._shortcut_space)

    def _shortcut_new(self, _event=None):
        self._active_tab_controller().new_item()
        return "break"

    def _shortcut_delete(self, _event=None):
        self._active_tab_controller().delete_selected()
        return "break"

    def _shortcut_space(self, _event=None):
        if self._active_tab_controller() is self.stopwatch_tab:
            self.stopwatch_tab.toggle_running()
            return "break"
        return None

    def _active_tab_controller(self):
        current = self.notebook.nametowidget(self.notebook.select())
        if current is self.alarm_tab.frame:
            return self.alarm_tab
        if current is self.timer_tab.frame:
            return self.timer_tab
        return self.stopwatch_tab

    def load_all_lists(self) -> None:
        self.alarm_tab.load_list()
        self.timer_tab.load_list()
        self.stopwatch_tab.load_list()

    def _restore_open_windows(self) -> None:
        for alarm in self.alarm_manager.alarms:
            if alarm.show_floating and alarm.id not in self.open_alarm_windows:
                self.alarm_tab.toggle_floating_for_restore(alarm)
        for timer in self.timer_manager.timers:
            if timer.show_floating and timer.id not in self.open_timer_windows:
                self.timer_tab.toggle_floating_for_restore(timer)
        for stopwatch in self.stopwatch_manager.stopwatches:
            if stopwatch.show_floating and stopwatch.id not in self.open_stopwatch_windows:
                self.stopwatch_tab.toggle_floating_for_restore(stopwatch)

    def update_all_windows_alpha(self, alpha: float) -> None:
        for win_dict in (self.open_alarm_windows, self.open_timer_windows, self.open_stopwatch_windows):
            for win in win_dict.values():
                if win.custom_alpha is None:
                    win.top.attributes("-alpha", alpha)
        self.settings.set("transparency", alpha)

    def open_settings(self) -> None:
        from ui.dialogs import SettingsDialog

        dialog = SettingsDialog(self.root, self.settings, self.theme_manager, self.update_all_windows_alpha, self)
        self.root.wait_window(dialog)

    def minimize_to_tray(self) -> None:
        self.tray.minimize()

    def _show_about(self) -> None:
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n"
            "Cross-platform alarm, countdown, and stopwatch app\n"
            "Built with Python and tkinter.",
        )

    def export_data(self) -> None:
        from tkinter import filedialog
        from core.data_import_export import export_data

        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export SaTi Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return
        success = export_data(
            self.alarm_manager,
            self.timer_manager,
            self.stopwatch_manager,
            self.settings,
            filepath
        )
        if success:
            messagebox.showinfo("Export Successful", f"Data exported to:\n{filepath}")
        else:
            messagebox.showerror("Export Failed", "An error occurred during export. Check the log for details.")

    def import_data(self) -> None:
        from tkinter import filedialog, messagebox
        from core.data_import_export import import_data
        from ui.dialogs import ask_import_mode

        filepath = filedialog.askopenfilename(
            parent=self.root,
            title="Import SaTi Data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return

        mode = ask_import_mode(self.root)
        if mode is None:
            return

        if mode == "replace":
            if not messagebox.askyesno(
                "Confirm Replace",
                "This will REPLACE all your current data (alarms, timers, stopwatches, settings) with the imported data.\n\nAre you sure you want to continue?"
            ):
                return

        success = import_data(
            self.alarm_manager,
            self.timer_manager,
            self.stopwatch_manager,
            self.settings,
            filepath,
            mode
        )
        if success:
            # Refresh all tabs
            self.load_all_lists()
            # Reload theme
            self.theme_manager.current = self.settings.get("theme", "Dark")
            self.theme_manager.apply_all(self.root)
            messagebox.showinfo("Import Successful", f"Data imported from:\n{filepath}\nMode: {mode.capitalize()}")
        else:
            messagebox.showerror("Import Failed", "An error occurred during import. Check the log for details.")

    def on_alarm_window_close(self, alarm_id: str) -> None:
        win = self.open_alarm_windows.pop(alarm_id, None)
        if win:
            win.destroy()
        self.alarm_tab.load_list()

    def on_timer_window_close(self, timer_id: str) -> None:
        win = self.open_timer_windows.pop(timer_id, None)
        if win:
            win.destroy()
        self.timer_tab.load_list()

    def on_stopwatch_window_close(self, stopwatch_id: str) -> None:
        win = self.open_stopwatch_windows.pop(stopwatch_id, None)
        if win:
            win.destroy()
        self.stopwatch_tab.load_list()

    def quit_application(self) -> None:
        self.scheduler.stop()
        self.tray.stop()
        self.alarm_manager.save()
        self.timer_manager.save()
        self.stopwatch_manager.save()
        self.settings.save()
        ring_controller.stop()
        for win in list(self.open_alarm_windows.values()):
            win.destroy()
        for win in list(self.open_timer_windows.values()):
            win.destroy()
        for win in list(self.open_stopwatch_windows.values()):
            win.destroy()
        self.root.destroy()

    def on_close(self) -> None:
        self.quit_application()
        