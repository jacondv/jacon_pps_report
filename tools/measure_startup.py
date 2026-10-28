"""
Dev-only: time from process launch to the main window being shown.

Waits for the "Event loop running; window painted" line that main.py logs
after the window's first paint, so it measures what the user sees. For a true cold start (Windows Defender has not
scanned the DLLs yet) run it once right after rebooting the machine.

Usage (repo root):
    .venv\\Scripts\\python tools\\measure_startup.py "dist\\Jacon PPS Report\\Jacon PPS Report.exe" --runs 3
    .venv\\Scripts\\python tools\\measure_startup.py --source --runs 3
"""

import argparse
import os
import statistics
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READY_MARKER = "Event loop running; window painted"
TIMEOUT_S = 900


def log_path() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "TunnelAnalyzer", "logs", "app.log")


def log_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def wait_for_marker(path: str, offset: int, proc: subprocess.Popen) -> bool:
    deadline = time.monotonic() + TIMEOUT_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        # The rotating log may roll over mid-run; then the new file is smaller.
        if log_size(path) < offset:
            offset = 0
        try:
            with open(path, "rb") as f:
                f.seek(offset)
                if READY_MARKER.encode() in f.read():
                    return True
        except OSError:
            pass
        time.sleep(0.05)
    return False


def folder_stats(folder: str):
    total = files = 0
    for root, _, names in os.walk(folder):
        for name in names:
            files += 1
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total / (1024 * 1024), files


def run_once(cmd, cwd) -> float:
    path = log_path()
    offset = log_size(path)
    start = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_for_marker(path, offset, proc):
            raise RuntimeError(f"'{READY_MARKER}' not seen in {path} (exit code {proc.poll()})")
        return time.perf_counter() - start
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("exe", nargs="?", help="path to the built exe")
    parser.add_argument("--source", action="store_true", help="run `python main.py` instead of an exe")
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()

    if args.source:
        cmd = [sys.executable, os.path.join(REPO_ROOT, "main.py")]
        cwd = REPO_ROOT
    elif args.exe:
        exe = os.path.abspath(args.exe)
        cmd = [exe]
        cwd = os.path.dirname(exe)
        size_mb, files = folder_stats(cwd)
        print(f"folder: {cwd}\n  size: {size_mb:.0f} MB, files: {files}")
    else:
        parser.error("give an exe path or --source")

    times = []
    for i in range(args.runs):
        t = run_once(cmd, cwd)
        times.append(t)
        print(f"run {i + 1}: {t:.2f} s")
    if len(times) > 1:
        print(f"median: {statistics.median(times):.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
