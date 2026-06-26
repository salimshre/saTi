# Repository file structure
Generated: 2026-06-26T23:05:13+05:45
A cleaner, hierarchical view of the repository. Directories end with '/'.
Cache folders (__pycache__, .pytest_cache, .ruff_cache) are summarised.
Excluded: .git, .agents, FILE_STRUCTURE.md.
## Summary
- Directories: 34
- Files: 110
## Tree
├── .gitattributes (68 B)
├── .gitignore (249 B)
├── __init__.py (46 B)
├── AGENTS.md (1.98 KB)
├── copy_to_tmp.bat (2.07 KB)
├── generate-structure.bat (4.54 KB)
├── main.py (754 B)
├── prompt.md (511 B)
├── pyproject.toml (920 B)
├── README.md (4.62 KB)
├── readme.txt (294 B)
├── sati.spec (830 B)
├── sati-app.bat (32 B)
├── temp_tree.ps1 (3.25 KB)
├── .github/
│   └── workflows/
│       └── ci.yml (578 B)
├── .pytest_cache/ (summary: compiled/pycache)
├── .ruff_cache/ (summary: compiled/pycache)
├── .sati_data/
│   └── sounds/
├── __pycache__/ (summary: compiled/pycache)
├── bak/
│   ├── __init__.py (46 B)
│   ├── main.py (756 B)
│   ├── pyproject.toml (565 B)
│   ├── README.md (3.87 KB)
│   ├── readme.txt (294 B)
│   ├── core/
│   │   ├── __init__.py (303 B)
│   │   ├── config.py (2.02 KB)
│   │   ├── logger.py (1.45 KB)
│   │   ├── notifications.py (413 B)
│   │   ├── persistence.py (1.02 KB)
│   │   └── sound.py (4.42 KB)
│   ├── models/
│   │   ├── __init__.py (232 B)
│   │   ├── alarm.py (8.90 KB)
│   │   ├── settings.py (732 B)
│   │   ├── stopwatch.py (3.93 KB)
│   │   └── timer.py (5.05 KB)
│   ├── tests/
│   │   ├── test_alarm_model.py (2.30 KB)
│   │   ├── test_persistence.py (814 B)
│   │   ├── test_stopwatch_model.py (740 B)
│   │   └── test_timer_model.py (1.25 KB)
│   └── ui/
│       ├── __init__.py (121 B)
│       ├── alarm_popup.py (2.85 KB)
│       ├── app.py (6.69 KB)
│       ├── app_meta.py (72 B)
│       ├── icon.py (735 B)
│       ├── scheduler.py (1.39 KB)
│       ├── themes.py (3.67 KB)
│       ├── tray.py (2.25 KB)
│       ├── dialogs/
│       │   ├── __init__.py (195 B)
│       │   ├── alarm_edit.py (9.83 KB)
│       │   ├── settings_dialog.py (5.93 KB)
│       │   └── timer_edit.py (2.25 KB)
│       ├── floating/
│       │   ├── __init__.py (204 B)
│       │   ├── alarm_window.py (3.34 KB)
│       │   ├── base.py (11.33 KB)
│       │   ├── countdown.py (7.21 KB)
│       │   └── stopwatch_window.py (6.89 KB)
│       └── tabs/
│           ├── __init__.py (158 B)
│           ├── alarm_tab.py (6.03 KB)
│           ├── stopwatch_tab.py (9.44 KB)
│           └── timer_tab.py (8.62 KB)
├── core/
│   ├── __init__.py (335 B)
│   ├── config.py (2.42 KB)
│   ├── logger.py (1.45 KB)
│   ├── notifications.py (413 B)
│   ├── persistence.py (1.02 KB)
│   ├── ring.py (1.59 KB)
│   ├── sound.py (6.07 KB)
│   └── __pycache__/ (summary: compiled/pycache)
├── models/
│   ├── __init__.py (232 B)
│   ├── alarm.py (8.90 KB)
│   ├── settings.py (732 B)
│   ├── stopwatch.py (3.93 KB)
│   ├── timer.py (5.97 KB)
│   └── __pycache__/ (summary: compiled/pycache)
├── sati.egg-info/
│   ├── dependency_links.txt (1 B)
│   ├── entry_points.txt (75 B)
│   ├── PKG-INFO (5.20 KB)
│   ├── requires.txt (115 B)
│   ├── SOURCES.txt (1016 B)
│   └── top_level.txt (23 B)
├── scripts/
│   ├── __init__.py (35 B)
│   └── build_desktop.py (414 B)
├── sounds/
│   ├── ring1.wav (442.40 KB)
│   ├── ring2.wav (1.01 MB)
│   ├── ring3.wav (1.04 MB)
│   ├── ring4.wav (3.03 MB)
│   └── ring5.wav (865.83 KB)
├── tests/
│   ├── test_alarm_model.py (2.30 KB)
│   ├── test_alarm_popup.py (2.30 KB)
│   ├── test_countdown_window.py (766 B)
│   ├── test_persistence.py (814 B)
│   ├── test_stopwatch_model.py (740 B)
│   ├── test_timer_model.py (3.43 KB)
│   ├── test_timer_tab_controller.py (2.24 KB)
│   └── __pycache__/ (summary: compiled/pycache)
├── tmp/
├── trash/
│   └── tmp.py (336 B)
└── ui/
    ├── __init__.py (121 B)
    ├── alarm_popup.py (3.46 KB)
    ├── app.py (6.70 KB)
    ├── app_meta.py (72 B)
    ├── icon.py (802 B)
    ├── scheduler.py (1.79 KB)
    ├── themes.py (3.67 KB)
    ├── tray.py (2.51 KB)
    ├── __pycache__/ (summary: compiled/pycache)
    ├── dialogs/
    │   ├── __init__.py (195 B)
    │   ├── alarm_edit.py (9.83 KB)
    │   ├── settings_dialog.py (9.70 KB)
    │   ├── timer_edit.py (2.25 KB)
    │   └── __pycache__/ (summary: compiled/pycache)
    ├── floating/
    │   ├── __init__.py (204 B)
    │   ├── alarm_window.py (3.34 KB)
    │   ├── base.py (11.36 KB)
    │   ├── countdown.py (10.98 KB)
    │   ├── stopwatch_window.py (6.86 KB)
    │   └── __pycache__/ (summary: compiled/pycache)
    └── tabs/
        ├── __init__.py (158 B)
        ├── alarm_tab.py (7.50 KB)
        ├── stopwatch_tab.py (9.45 KB)
        ├── timer_tab.py (9.28 KB)
        └── __pycache__/ (summary: compiled/pycache)
