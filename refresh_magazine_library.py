from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PYTHON = sys.executable

STEPS = [
    [PYTHON, "extract_covers.py"],
    [PYTHON, "extract_books.py"],
    [PYTHON, "generate_full_reading.py"],
    [PYTHON, "generate_library_manifest.py"],
]


def run_step(cmd: list[str]) -> None:
    print(f"\n▶ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=BASE, check=True)


def main() -> int:
    print("📚 開始刷新 Jim 書庫資料…")
    for step in STEPS:
      run_step(step)
    print("\n✅ 書庫刷新完成")
    print(f"下一步：重新整理 {BASE / 'magazine' / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
