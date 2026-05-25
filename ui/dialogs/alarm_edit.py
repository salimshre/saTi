"""
ui/dialogs/alarm_edit.py
Dialog for creating / editing an Alarm, plus ask_countdown_duration helper.
"""
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
import uuid

from models.alarm import Alarm


# ── Countdown duration helper ──────────────────────────────────────────────
def ask_countdown_duration(parent) -> int | None:
    dlg = tk.Toplevel(parent)
    dlg.title("Countdown Duration")
    dlg.transient(parent)
    dlg.grab_set()
    dlg.geometry("250x100")

    min_var = tk.IntVar(value=5)
    sec_var = tk.IntVar(value=0)
    result  = [None]

    tk.Label(dlg, text="Minutes:").grid(row=0, column=0)
    tk.Spinbox(dlg, from_=0, to=999, textvariable=min_var, width=5).grid(row=0, column=1)
    tk.Label(dlg, text="Seconds:").grid(row=0, column=2)
    tk.Spinbox(dlg, from_=0, to=59,  textvariable=sec_var, width=5).grid(row=0, column=3)

    def ok():
        total     = min_var.get() * 60 + sec_var.get()
        result[0] = max(1, total)
        dlg.destroy()

    tk.Button(dlg, text="OK", command=ok).grid(row=1, column=0, columnspan=4, pady=10)
    dlg.wait_window()
    return result[0]


# ── Alarm edit dialog ──────────────────────────────────────────────────────
class AlarmEditDialog(tk.Toplevel):
    def __init__(self, master, settings, theme_manager, alarm: Alarm | None = None):
        super().__init__(master)
        self.title("Alarm Setup" if alarm is None else "Edit Alarm")
        self.transient(master)
        self.grab_set()
        self.settings = settings
        self.result: Alarm | None = None
        self.alarm = alarm

        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="e")
        self.name_var = tk.StringVar(value=alarm.name if alarm else "Alarm")
        tk.Entry(self, textvariable=self.name_var).grid(row=0, column=1, columnspan=2)

        tk.Label(self, text="Type:").grid(row=1, column=0, sticky="e")
        self.type_var = tk.StringVar(value=alarm.type if alarm else "one-time")
        types = ["one-time", "daily", "weekly", "monthly", "yearly", "custom", "birthday"]
        tk.OptionMenu(self, self.type_var, *types,
                      command=self._on_type_change).grid(row=1, column=1, columnspan=2)

        tk.Label(self, text="Hour (0-23):").grid(row=2, column=0, sticky="e")
        self.hour_var = tk.IntVar(value=alarm.date_time.hour if alarm and alarm.date_time else 12)
        tk.Spinbox(self, from_=0, to=23, textvariable=self.hour_var, width=3).grid(row=2, column=1)
        tk.Label(self, text="Minute:").grid(row=2, column=2)
        self.min_var = tk.IntVar(value=alarm.date_time.minute if alarm and alarm.date_time else 0)
        tk.Spinbox(self, from_=0, to=59, textvariable=self.min_var, width=3).grid(row=2, column=3)

        tk.Label(self, text="Date (YYYY-MM-DD):").grid(row=3, column=0, sticky="e")
        default_date = alarm.date_time.strftime("%Y-%m-%d") if alarm and alarm.date_time else ""
        self.date_var = tk.StringVar(value=default_date)
        tk.Entry(self, textvariable=self.date_var).grid(row=3, column=1, columnspan=2)

        # Weekly
        self.weekly_frame = tk.Frame(self)
        self.weekly_frame.grid(row=4, column=0, columnspan=4, pady=5)
        self.day_vars: dict[int, tk.BooleanVar] = {}
        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            var = tk.BooleanVar(value=(i in alarm.days_of_week) if alarm else False)
            self.day_vars[i] = var
            tk.Checkbutton(self.weekly_frame, text=day, variable=var).pack(side=tk.LEFT)

        # Monthly
        self.monthly_frame = tk.Frame(self)
        self.monthly_frame.grid(row=5, column=0, columnspan=4, pady=5)
        tk.Label(self.monthly_frame, text="Day of month:").pack(side=tk.LEFT)
        self.day_month_var = tk.IntVar(value=alarm.day_of_month if alarm else 1)
        tk.Spinbox(self.monthly_frame, from_=1, to=31,
                   textvariable=self.day_month_var, width=3).pack(side=tk.LEFT)

        # Yearly
        self.yearly_frame = tk.Frame(self)
        self.yearly_frame.grid(row=6, column=0, columnspan=4, pady=5)
        tk.Label(self.yearly_frame, text="Month (1-12):").pack(side=tk.LEFT)
        self.month_var = tk.IntVar(value=alarm.month if alarm else 1)
        tk.Spinbox(self.yearly_frame, from_=1, to=12,
                   textvariable=self.month_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.yearly_frame, text="Day:").pack(side=tk.LEFT)
        self.day_yearly_var = tk.IntVar(value=alarm.day_of_month if alarm else 1)
        tk.Spinbox(self.yearly_frame, from_=1, to=31,
                   textvariable=self.day_yearly_var, width=3).pack(side=tk.LEFT)

        # Custom dates
        self.custom_frame = tk.Frame(self)
        self.custom_frame.grid(row=7, column=0, columnspan=4, pady=5)
        self.custom_listbox = tk.Listbox(self.custom_frame, height=4, width=20)
        self.custom_listbox.pack(side=tk.LEFT)
        for d in (alarm.custom_dates if alarm else []):
            self.custom_listbox.insert(tk.END, d.isoformat())
        btn_f = tk.Frame(self.custom_frame)
        btn_f.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="Add",    command=self._add_custom_date).pack(fill="x")
        tk.Button(btn_f, text="Remove", command=self._remove_custom_date).pack(fill="x")

        # Birthday advance warning
        self.birthday_frame = tk.Frame(self)
        self.birthday_frame.grid(row=8, column=0, columnspan=4, pady=5)
        tk.Label(self.birthday_frame, text="Advance warning (days):").pack(side=tk.LEFT)
        self.adv_warn_var = tk.IntVar(value=alarm.advance_warning_days if alarm else 0)
        tk.Spinbox(self.birthday_frame, from_=0, to=30,
                   textvariable=self.adv_warn_var, width=3).pack(side=tk.LEFT)

        tk.Label(self, text="Repeat until dismissed:").grid(row=9,  column=0, sticky="e")
        self.repeat_var = tk.BooleanVar(value=alarm.repeat_until_dismissed if alarm else False)
        tk.Checkbutton(self, variable=self.repeat_var).grid(row=9, column=1)

        tk.Label(self, text="Snooze (min):").grid(row=10, column=0, sticky="e")
        self.snooze_var = tk.IntVar(value=alarm.snooze_minutes if alarm else 10)
        tk.Spinbox(self, from_=1, to=60, textvariable=self.snooze_var, width=3).grid(row=10, column=1)

        tk.Label(self, text="Enabled:").grid(row=11, column=0, sticky="e")
        self.enabled_var = tk.BooleanVar(value=alarm.enabled if alarm else True)
        tk.Checkbutton(self, variable=self.enabled_var).grid(row=11, column=1)

        tk.Button(self, text="Save", command=self.on_save).grid(
            row=12, column=0, columnspan=4, pady=10)
        self._on_type_change()

    # ------------------------------------------------------------------
    def _on_type_change(self, *_) -> None:
        t = self.type_var.get()
        for frame in (self.weekly_frame, self.monthly_frame,
                      self.yearly_frame, self.custom_frame, self.birthday_frame):
            frame.grid_remove()
        {
            "weekly":   self.weekly_frame,
            "monthly":  self.monthly_frame,
            "yearly":   self.yearly_frame,
            "custom":   self.custom_frame,
            "birthday": self.birthday_frame,
        }.get(t, tk.Frame()).grid() if t in ("weekly", "monthly", "yearly", "custom", "birthday") else None

    def _add_custom_date(self) -> None:
        d = simpledialog.askstring("Add Date", "Enter date (YYYY-MM-DD):", parent=self)
        if d:
            try:
                datetime.date.fromisoformat(d)
                self.custom_listbox.insert(tk.END, d)
            except ValueError:
                messagebox.showerror("Invalid", "Invalid date format.")

    def _remove_custom_date(self) -> None:
        sel = self.custom_listbox.curselection()
        if sel:
            self.custom_listbox.delete(sel[0])

    def on_save(self) -> None:
        name       = self.name_var.get().strip() or "Alarm"
        alarm_type = self.type_var.get()
        date_str   = self.date_var.get().strip()
        if date_str:
            try:
                date_time = datetime.datetime.strptime(
                    f"{date_str} {self.hour_var.get()}:{self.min_var.get()}", "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Invalid date/time format.")
                return
        else:
            date_time = datetime.datetime.now().replace(
                hour=self.hour_var.get(), minute=self.min_var.get(), second=0)

        days_of_week = [i for i, v in self.day_vars.items() if v.get()]
        custom_dates = [datetime.date.fromisoformat(self.custom_listbox.get(i))
                        for i in range(self.custom_listbox.size())]

        self.result = Alarm(
            id=self.alarm.id if self.alarm else str(uuid.uuid4()),
            name=name,
            alarm_type=alarm_type,
            date_time=date_time,
            days_of_week=days_of_week,
            day_of_month=(self.day_month_var.get() if alarm_type == "monthly"
                          else (self.day_yearly_var.get() if alarm_type == "yearly" else None)),
            month=self.month_var.get() if alarm_type == "yearly" else None,
            year=None,
            custom_dates=custom_dates,
            enabled=self.enabled_var.get(),
            snooze_minutes=self.snooze_var.get(),
            repeat_until_dismissed=self.repeat_var.get(),
            advance_warning_days=self.adv_warn_var.get() if alarm_type == "birthday" else 0,
            show_floating=self.alarm.show_floating if self.alarm else False,
        )
        self.destroy()
