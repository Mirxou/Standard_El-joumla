#!/usr/bin/env python3
"""
Unified project launcher.

Starts the backend API and the Next.js frontend together.
Optionally starts the desktop app too.

Usage:
  python start_all.py
  python start_all.py --desktop
  python start_all.py --backend-only
  python start_all.py --web-only
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
BACKEND_SCRIPT = ROOT / "scripts" / "start-backend.py"
DESKTOP_SCRIPT = ROOT / "main.py"


def _find_npm() -> str:
    return shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def _spawn(name: str, cmd: list[str], cwd: Path) -> subprocess.Popen:
    print(f"[start] {name}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=str(cwd), env=os.environ.copy())


def main() -> int:
    parser = argparse.ArgumentParser(description="Start the whole project")
    parser.add_argument("--desktop", action="store_true", help="Also start the PySide6 desktop app")
    parser.add_argument("--backend-only", action="store_true", help="Start only the backend API")
    parser.add_argument("--web-only", action="store_true", help="Start only the web frontend")
    args = parser.parse_args()

    procs: list[subprocess.Popen] = []

    def stop_all(*_args):
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()

    signal.signal(signal.SIGINT, stop_all)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_all)

    try:
        if not args.web_only:
            if not BACKEND_SCRIPT.exists():
                print(f"[error] Backend script not found: {BACKEND_SCRIPT}")
                return 1
            procs.append(_spawn("backend", [sys.executable, str(BACKEND_SCRIPT)], ROOT))

        if not args.backend_only:
            npm = _find_npm()
            procs.append(_spawn("web", [npm, "run", "dev"], WEB_DIR))

        if args.desktop:
            if not DESKTOP_SCRIPT.exists():
                print(f"[error] Desktop entry not found: {DESKTOP_SCRIPT}")
                return 1
            procs.append(_spawn("desktop", [sys.executable, str(DESKTOP_SCRIPT)], ROOT))

        print("[ready] Services started. Press Ctrl+C to stop.")

        while procs:
            for proc in list(procs):
                code = proc.poll()
                if code is not None:
                    print(f"[exit] A process exited with code {code}")
                    stop_all()
                    return code
            try:
                for proc in procs:
                    proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass

        return 0
    except KeyboardInterrupt:
        stop_all()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
