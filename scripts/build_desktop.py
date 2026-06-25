"""Build a desktop executable with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    spec = root / "sati.spec"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec)]
    return subprocess.call(cmd, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
