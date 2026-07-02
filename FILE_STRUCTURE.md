# Repository file structure
Generated: 2026-07-02T09:06:05+05:45
A cleaner, hierarchical view of the repository. Directories end with '/'.
Cache folders (__pycache__, .pytest_cache, .ruff_cache) are summarised.
Excluded: .git, .agents, FILE_STRUCTURE.md.
## Summary
- Directories: 19
- Files: 67
## Tree
├── .gitattributes (68 B)
├── .gitignore (273 B)
├── __init__.py (46 B)
├── AGENTS.md (1.98 KB)
├── copy_to_tmp.bat (2.07 KB)
├── generate-structure.bat (4.54 KB)
├── main.py (754 B)
├── prompt.md (511 B)
├── pyproject.toml (944 B)
├── README.md (4.65 KB)
├── readme.txt (3.40 KB)
├── saTi.lnk (1.39 KB)
├── sati.spec (876 B)
├── sati-app.bat (32 B)
├── temp_tree.ps1 (3.25 KB)
├── .github/
│   └── workflows/
│       └── ci.yml (604 B)
├── archive/
│   ├── saTiexp.json (2.50 KB)
│   └── tmp.py (336 B)
├── core/
│   ├── __init__.py (338 B)
│   ├── config.py (2.47 KB)
│   ├── data_import_export.py (4.12 KB)
│   ├── logger.py (1.45 KB)
│   ├── notifications.py (413 B)
│   ├── persistence.py (1.02 KB)
│   ├── ring.py (3.00 KB)
│   ├── sound.py (6.07 KB)
│   └── __pycache__/ (summary: compiled/pycache)
├── models/
│   ├── __init__.py (232 B)
│   ├── alarm.py (8.90 KB)
│   ├── settings.py (732 B)
│   ├── stopwatch.py (3.93 KB)
│   ├── timer.py (6.04 KB)
│   └── __pycache__/ (summary: compiled/pycache)
├── scripts/
│   ├── __init__.py (36 B)
│   └── build_desktop.py (432 B)
├── sounds/
│   ├── ring1.wav (442.40 KB)
│   ├── ring2.wav (1.01 MB)
│   ├── ring3.wav (1.04 MB)
│   ├── ring4.wav (3.03 MB)
│   └── ring5.wav (865.83 KB)
├── tests/
│   ├── test_alarm_model.py (2.30 KB)
│   ├── test_alarm_popup.py (2.38 KB)
│   ├── test_countdown_window.py (794 B)
│   ├── test_persistence.py (814 B)
│   ├── test_stopwatch_model.py (740 B)
│   ├── test_timer_model.py (3.53 KB)
│   └── test_timer_tab_controller.py (2.32 KB)
├── tmp/
└── ui/
    ├── __init__.py (121 B)
    ├── alarm_popup.py (3.51 KB)
    ├── app.py (9.29 KB)
    ├── app_meta.py (72 B)
    ├── icon.py (802 B)
    ├── scheduler.py (1.84 KB)
    ├── themes.py (3.67 KB)
    ├── tray.py (2.51 KB)
    ├── __pycache__/ (summary: compiled/pycache)
    ├── dialogs/
    │   ├── __init__.py (413 B)
    │   ├── alarm_edit.py (9.83 KB)
    │   ├── import_dialog.py (1.08 KB)
    │   ├── settings_dialog.py (10.43 KB)
    │   ├── timer_edit.py (2.25 KB)
    │   └── __pycache__/ (summary: compiled/pycache)
    ├── floating/
    │   ├── __init__.py (204 B)
    │   ├── alarm_window.py (3.34 KB)
    │   ├── base.py (15.40 KB)
    │   ├── countdown.py (10.98 KB)
    │   ├── stopwatch_window.py (6.86 KB)
    │   └── __pycache__/ (summary: compiled/pycache)
    └── tabs/
        ├── __init__.py (158 B)
        ├── alarm_tab.py (7.50 KB)
        ├── stopwatch_tab.py (9.45 KB)
        ├── timer_tab.py (9.28 KB)
        └── __pycache__/ (summary: compiled/pycache)
