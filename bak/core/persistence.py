"""Helpers for safer JSON persistence."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def load_json_file(path: str, default: Any, label: str) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[SaTi] Failed to load {label} from {file_path}: {exc}")
        return default


def save_json_file(path: str, data: Any, label: str) -> None:
    file_path = Path(path)
    if file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        try:
            shutil.copy2(file_path, backup_path)
        except OSError as exc:
            print(f"[SaTi] Failed to back up {label} to {backup_path}: {exc}")

    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
