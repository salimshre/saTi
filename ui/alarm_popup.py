"""Popup shown when an alarm is due."""

from __future__ import annotations

import datetime
import subprocess
import tkinter as tk
import webbrowser
from tkinter import messagebox

from core.logger import activity_log
from core.ring import ring_controller


class AlarmPopup(tk.Toplevel):
    def __init__(self, master, alarm, settings):
        super().__init__(master)
        self.alarm = alarm
        self.settings = settings
        self.title("Alarm")
        self.geometry("300x150")
        self.attributes("-topmost", True)

        tk.Label(self, text=f"Alarm: {alarm.name}", font=("Arial", 14)).pack(pady=10)
        tk.Label(self, text="Alarm is ringing!").pack()

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Snooze", command=self.snooze).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Dismiss", command=self.dismiss).pack(side=tk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.dismiss)
        activity_log.log("alarm_triggered", alarm.name, f"type={alarm.type}")
        self.run_actions()

    def run_actions(self) -> None:
        has_sound_action = any(action.get("type") == "play_sound" for action in self.alarm.actions)
        if not has_sound_action:
            self._play_alarm_sound()

        for action in self.alarm.actions:
            action_type = action.get("type")
            if action_type == "play_sound":
                self._play_alarm_sound()
            elif action_type == "launch":
                command = action.get("command")
                if command:
                    subprocess.Popen(command, shell=True)
            elif action_type == "open_website":
                url = action.get("url")
                if url:
                    webbrowser.open(url)
            elif action_type == "message":
                messagebox.showinfo("Alarm Message", action.get("text", "Alarm"))

        if self.alarm.repeat_until_dismissed and not self.alarm.radio_url:
            self.repeat_sound()

    def _play_alarm_sound(self) -> None:
        if self.alarm.radio_url:
            ring_controller.start(self.settings, self.alarm.radio_url, radio=True, loop=False, name=self.alarm.name)
        else:
            ring_controller.start(self.settings, self.alarm.sound_file, loop=False, name=self.alarm.name)

    def repeat_sound(self) -> None:
        ring_controller.start(self.settings, self.alarm.sound_file, loop=False, name=self.alarm.name)
        self.after(3000, self.repeat_sound)

    def snooze(self) -> None:
        ring_controller.stop(self.alarm.name)
        activity_log.log("alarm_snoozed", self.alarm.name, f"snooze_minutes={self.alarm.snooze_minutes}")
        self.alarm.date_time = datetime.datetime.now() + datetime.timedelta(minutes=self.alarm.snooze_minutes)
        self.alarm.type = "one-time"
        self.alarm.enabled = True
        self.destroy()

    def dismiss(self) -> None:
        ring_controller.stop(self.alarm.name)
        activity_log.log("alarm_dismissed", self.alarm.name, "")
        self.destroy()

