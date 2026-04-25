from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PYTHON = sys.executable


def run(cmd: list[str]) -> None:
    print(f"▶ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=BASE, check=True)


def maybe_push() -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=BASE,
        text=True,
        capture_output=True,
        check=True,
    )
    changed = [line for line in status.stdout.splitlines() if line.strip()]
    if not changed:
        print("沒有新的 Drive 書籍變更")
        return
    run(["git", "add", "data/books.json", "magazine/library_manifest.js"])
    commit = subprocess.run(
        ["git", "commit", "-m", "Auto sync Google Drive books"],
        cwd=BASE,
        text=True,
        capture_output=True,
        check=False,
    )
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
        raise RuntimeError(commit.stderr.strip() or "git commit failed")
    if commit.stdout.strip():
        print(commit.stdout.strip())
    run(["git", "push", "origin", "main"])


def main() -> int:
    print("☁️ 開始同步 Google Drive 書庫…")
    run([PYTHON, "sync_books.py"])
    run([PYTHON, "generate_library_manifest.py"])
    maybe_push()
    print("✅ Google Drive 書庫同步完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
