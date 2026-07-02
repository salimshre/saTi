# SaTi

SaTi is a desktop alarm clock app built with Python and `tkinter`. It includes:

- alarms
- countdown timers with overdue companion popups
- stopwatches
- floating mini windows
- local JSON-based data storage
- platform-aware config storage with safe fallback
- optional tray and desktop notification support
- bundled alarm sounds with preview controls

## Project Structure

- [main.py](/C:/Users/StudyAcer/Downloads/new/SaTi/main.py): app entry point
- [core](/C:/Users/StudyAcer/Downloads/new/SaTi/core): config, logging, sound helpers
- [models](/C:/Users/StudyAcer/Downloads/new/SaTi/models): alarms, timers, stopwatches, settings
- [ui](/C:/Users/StudyAcer/Downloads/new/SaTi/ui): main window, dialogs, floating windows
- [tests](/C:/Users/StudyAcer/Downloads/new/SaTi/tests): model and persistence tests
- [pyproject.toml](/C:/Users/StudyAcer/Downloads/new/SaTi/pyproject.toml): package metadata and dependencies
- [sounds](/C:/Users/StudyAcer/Downloads/new/SaTi/sounds): bundled alarm/ring tracks
- [scripts/build_desktop.py](/C:/Users/StudyAcer/Downloads/new/SaTi/scripts/build_desktop.py): PyInstaller build helper

## Requirements

- Python 3.10 or newer recommended
- `tkinter` available in your Python installation
- `platformdirs` for platform-native config storage

Optional features:

- `plyer` for desktop notifications
- `pystray` and `pillow` for system tray support
- `pyinstaller` for desktop packaging

## Run On Windows

1. Open PowerShell in the project folder:

```powershell
cd C:\Users\StudyAcer\Downloads\new\SaTi
```

2. Check Python:

```powershell
python --version
```

3. Install the base dependency:

```powershell
python -m pip install -e .
```

4. Start the app:

```powershell
sati
```

If `python` does not work, try:

```powershell
py -m pip install -e .
py main.py
```

Optional desktop extras:

```powershell
python -m pip install -e .[desktop]
```

## Run On Kali Linux

1. Open a terminal and go to the project folder:

```bash
cd /path/to/SaTi
```

2. Make sure Python and `tkinter` are installed:

```bash
sudo apt update
sudo apt install -y python3 python3-tk
```

3. Install the base dependency:

```bash
python3 -m pip install -e .
```

4. Start the app:

```bash
sati
```

Optional desktop extras:

```bash
python3 -m pip install -e .[desktop]
```

## Notes

- App data is stored in the platform config directory when available.
- If SaTi cannot write there, it falls back to a local `.sati_data/` folder in the project directory.
- On Linux, optional audio players such as `ffplay`, `mpv`, `mpg123`, or `cvlc` can improve sound playback.
- If no sound backend is available, SaTi falls back to a simple beep when possible.
- Closing the main window minimizes SaTi to the tray when tray dependencies are installed.
- Timers continue running even if their floating window is closed, and they resume correctly after app restart.
- When a countdown timer reaches zero, SaTi opens a small topmost overdue popup, starts the configured ring, and counts upward from the completion time.
- Change the countdown/alarm ring from `File > Settings > Sound` or the `Sound Settings` button on the Countdown Timers dashboard.

## Troubleshooting

### `tkinter` import errors

Windows:

- reinstall Python and make sure Tcl/Tk is included

Kali Linux:

```bash
sudo apt install -y python3-tk
```

### No alarm sound

Linux:

```bash
sudo apt install -y ffmpeg mpv mpg123 vlc
```

Windows:

- `.wav` playback should work with the built-in fallback
- other formats may need a player such as VLC or FFmpeg installed and available in `PATH`

### App does not start

- make sure you are running from the folder that contains `main.py`
- check that your Python version is modern enough
- run:

```bash
python3 -m pip install -e .
sati
```

or on Windows:

```powershell
python -m pip install -e .
sati
```

### Run tests

Install pytest:

```bash
python3 -m pip install -e .[dev]
```

or on Windows:

```powershell
python -m pip install -e .[dev]
```

Then run:

```bash
python3 -m pytest
```

## Build Desktop Package

With the optional desktop tools installed:

```bash
python3 -m pip install -e .[desktop]
```

or on Windows:

```powershell
python -m pip install -e .[desktop]
```

Build with the included PyInstaller spec:

```bash
python3 scripts/build_desktop.py
```

or on Windows:

```powershell
python scripts\build_desktop.py
```

After installing with `python -m pip install -e .[desktop]`, you can also run:

```bash
sati-build
```

The build includes bundled files from the `sounds/` directory.
