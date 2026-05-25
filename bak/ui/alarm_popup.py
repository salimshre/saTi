"""Popup shown when an alarm is due."""

from __future__ import annotations

import datetime
import subprocess
import tkinter as tk
import webbrowser
from tkinter import messagebox

from core.logger import activity_log
from core.sound import player


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
        for action in self.alarm.actions:
            action_type = action.get("type")
            if action_type == "play_sound":
                if self.alarm.radio_url:
                    player.play(self.alarm.radio_url, radio=True, volume=self.settings.get("volume", 100))
                else:
                    player.play(self.alarm.sound_file or self.settings.get("alarm_sound"), volume=self.settings.get("volume", 100))
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

    def repeat_sound(self) -> None:
        player.play(self.alarm.sound_file or self.settings.get("alarm_sound"), volume=self.settings.get("volume", 100))
        self.after(3000, self.repeat_sound)

    def snooze(self) -> None:
        player.stop_radio()
        activity_log.log("alarm_snoozed", self.alarm.name, f"snooze_minutes={self.alarm.snooze_minutes}")
        self.alarm.date_time = datetime.datetime.now() + datetime.timedelta(minutes=self.alarm.snooze_minutes)
        self.alarm.type = "one-time"
        self.alarm.enabled = True
        self.destroy()

    def dismiss(self) -> None:
        player.stop_radio()
        activity_log.log("alarm_dismissed", self.alarm.name, "")
        self.destroy()

