"""Dialogs for creating and editing countdown timers."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


class _BaseTimerDialog(tk.Toplevel):
    def __init__(self, master, title: str, label: str, duration: int):
        super().__init__(master)
        self.title(title)
        self.transient(master)
        self.grab_set()
        self.result = None

        tk.Label(self, text="Label:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.label_var = tk.StringVar(value=label)
        tk.Entry(self, textvariable=self.label_var).grid(row=0, column=1, columnspan=3, padx=6, pady=6, sticky="ew")

        mins, secs = divmod(duration, 60)
        tk.Label(self, text="Minutes:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.min_var = tk.IntVar(value=mins)
        tk.Spinbox(self, from_=0, to=999, textvariable=self.min_var, width=6).grid(row=1, column=1, padx=6, pady=6)

        tk.Label(self, text="Seconds:").grid(row=1, column=2, padx=6, pady=6, sticky="e")
        self.sec_var = tk.IntVar(value=secs)
        tk.Spinbox(self, from_=0, to=59, textvariable=self.sec_var, width=6).grid(row=1, column=3, padx=6, pady=6)

        button_row = tk.Frame(self)
        button_row.grid(row=2, column=0, columnspan=4, pady=10)
        tk.Button(button_row, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=4)
        tk.Button(button_row, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=4)

        self.columnconfigure(1, weight=1)

    def on_save(self) -> None:
        label = self.label_var.get().strip() or "Timer"
        duration = self.min_var.get() * 60 + self.sec_var.get()
        if duration <= 0:
            messagebox.showerror("Invalid", "Duration must be positive.")
            return
        self.result = {"label": label, "duration": duration}
        self.destroy()


class TimerCreateDialog(_BaseTimerDialog):
    def __init__(self, master):
        super().__init__(master, title="New Timer", label="Timer", duration=300)


class TimerEditDialog(_BaseTimerDialog):
    def __init__(self, master, timer):
        self.timer = timer
        super().__init__(master, title="Edit Timer", label=timer.label, duration=timer.duration)
