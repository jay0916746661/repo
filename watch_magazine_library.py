from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
WATCH_DIR = Path(os.environ.get("JIM_BOOK_WATCH_DIR", str(Path.home() / "Desktop" / "電子書"))).expanduser()
LOG_FILE = BASE / "magazine_watch.log"
POLL_SECONDS = int(os.environ.get("JIM_BOOK_POLL_SECONDS", "20"))
DEBOUNCE_SECONDS = int(os.environ.get("JIM_BOOK_DEBOUNCE_SECONDS", "25"))
AUTO_PUSH = os.environ.get("JIM_BOOK_AUTO_PUSH", "1") != "0"
WATCH_EXTS = {".pdf", ".epub", ".PDF", ".EPUB"}
IGNORE_PREFIXES = {".", "~$", "._"}


def log(message: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def iter_books() -> list[Path]:
    if not WATCH_DIR.exists():
        return []
    items = []
    for path in WATCH_DIR.iterdir():
        if not path.is_file():
            continue
        if path.suffix not in WATCH_EXTS:
            continue
        if any(path.name.startswith(prefix) for prefix in IGNORE_PREFIXES):
            continue
        items.append(path)
    return sorted(items)


def snapshot() -> dict[str, tuple[int, int]]:
    snap: dict[str, tuple[int, int]] = {}
    for path in iter_books():
        stat = path.stat()
        snap[str(path)] = (int(stat.st_size), int(stat.st_mtime))
    return snap


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    log("▶ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=BASE, text=True, capture_output=True, check=False)


def refresh_library() -> None:
    result = run([sys.executable, str(BASE / "refresh_magazine_library.py")])
    if result.stdout:
        log(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr:
            log(result.stderr.strip())
        raise RuntimeError("refresh_magazine_library.py failed")


def git_autopush() -> None:
    status = run(["git", "status", "--porcelain"])
    if status.returncode != 0:
        raise RuntimeError("git status failed")
    changed = [line for line in status.stdout.splitlines() if line.strip()]
    if not changed:
        log("沒有檔案變更，不需要 push")
        return

    add = run(["git", "add", "data/local_books.json", "data/book_contents", "magazine/library_manifest.js", "magazine/full_reading.js", "magazine/page_images", "data/covers"])
    if add.returncode != 0:
        raise RuntimeError(add.stderr.strip() or "git add failed")

    commit = run(["git", "commit", "-m", "Auto refresh library from watched folder"])
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
        raise RuntimeError(commit.stderr.strip() or "git commit failed")
    if commit.stdout:
        log(commit.stdout.strip())

    push = run(["git", "push", "origin", "main"])
    if push.returncode != 0:
        raise RuntimeError(push.stderr.strip() or "git push failed")
    if push.stdout:
        log(push.stdout.strip())
    if push.stderr:
        log(push.stderr.strip())


def wait_until_stable() -> None:
    first = snapshot()
    time.sleep(max(5, DEBOUNCE_SECONDS))
    second = snapshot()
    if first != second:
        log("偵測到檔案仍在變動，延後再檢查一次")
        time.sleep(max(5, DEBOUNCE_SECONDS))


def main() -> int:
    log(f"開始監看資料夾：{WATCH_DIR}")
    log(f"輪詢秒數：{POLL_SECONDS} / debounce：{DEBOUNCE_SECONDS} / auto_push：{AUTO_PUSH}")
    last_snapshot = snapshot()
    pending_since: float | None = None

    while True:
        time.sleep(POLL_SECONDS)
        current = snapshot()
        if current != last_snapshot:
            pending_since = pending_since or time.time()
            log("偵測到資料夾變更，等待檔案穩定後刷新")
            last_snapshot = current
            continue

        if pending_since and time.time() - pending_since >= DEBOUNCE_SECONDS:
            try:
                wait_until_stable()
                refresh_library()
                if AUTO_PUSH:
                    git_autopush()
                log("書庫自動刷新完成")
            except Exception as exc:
                log(f"自動刷新失敗：{exc}")
            finally:
                pending_since = None


if __name__ == "__main__":
    raise SystemExit(main())
