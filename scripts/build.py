#!/usr/bin/env python3
"""
Standard El-Joumla ERP — Nuitka Build Script
Builds the desktop application into a standalone executable.

Usage:
    python scripts/build.py --mode=standalone    # Folder with exe + deps (recommended)
    python scripts/build.py --mode=onefile       # Single .exe (slower startup)
    python scripts/build.py --mode=standalone --platform=windows
    python scripts/build.py --mode=standalone --platform=linux
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"


def get_version() -> str:
    """Read version from VERSION.txt."""
    version_file = ROOT / "VERSION.txt"
    if version_file.exists():
        first_line = version_file.read_text(encoding="utf-8").strip().split("\n")[0]
        return first_line.strip()
    return "6.0.0"


def clean_build_dirs():
    """Remove previous build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            print(f"🧹 Cleaned {d}")


def build_nuitka(mode: str, plat: str, version: str):
    """Execute Nuitka build command."""
    is_windows = plat == "windows" or (plat == "auto" and platform.system() == "Windows")
    is_linux = plat == "linux" or (plat == "auto" and platform.system() == "Linux")

    cmd = [
        sys.executable, "-m", "nuitka",
        "--assume-yes-for-downloads",
        "--python-flag=no_site",
        f"--output-dir={DIST_DIR}",
        f"--output-filename=StandardElJoumla-{version}",
    ]

    # Build mode
    if mode == "onefile":
        cmd.append("--onefile")
    else:
        cmd.append("--standalone")

    # Qt support
    cmd.append("--enable-qt=pyside6")

    # Platform-specific options
    if is_windows:
        cmd.extend([
            "--windows-disable-console",
            "--windows-icon-from-ico=assets/icons/app_icon.ico",
        ])
    elif is_linux:
        icon_path = ROOT / "assets" / "icons" / "app_icon.png"
        if icon_path.exists():
            cmd.append(f"--linux-icon={icon_path}")

    # Include data directories
    data_dirs = ["assets", "config", "locales"]
    for d in data_dirs:
        data_path = ROOT / d
        if data_path.exists():
            cmd.append(f"--include-data-dir={d}={d}")

    # Include data files
    data_files = [
        ("requirements.txt", "requirements.txt"),
        ("VERSION.txt", "VERSION.txt"),
    ]
    for src, dst in data_files:
        if (ROOT / src).exists():
            cmd.append(f"--include-data-file={src}={dst}")

    # Performance: enable C acceleration for hot modules
    hot_modules = [
        "src.core.database_manager",
        "src.core.local_database_manager",
        "src.services.sales_service",
        "src.services.inventory_service",
        "src.services.accounting_service",
        "src.services.payment_service",
    ]
    for mod in hot_modules:
        cmd.append(f"--module={mod}")

    # Anti-bloat: remove unnecessary modules
    no_follow = [
        "tkinter", "unittest", "test", "tests",
        "setuptools", "pip", "wheel",
        "PyQt5", "PyQt6",  # We use PySide6 only
        "IPython", "notebook", "jupyter",
        "sphinx", "docutils",
    ]
    for mod in no_follow:
        cmd.append(f"--nofollow-import-to={mod}")

    # Main entry point
    cmd.append(str(ROOT / "main.py"))

    print("🔨 Building with Nuitka...")
    print(f"   Mode: {mode}")
    print(f"   Platform: {plat}")
    print(f"   Version: {version}")
    print(f"   Command: {' '.join(cmd[:8])}...")
    print()

    try:
        result = subprocess.run(cmd, cwd=ROOT, check=True)
        print(f"\n✅ Build successful! Output in: {DIST_DIR}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with exit code: {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ Nuitka not found. Install with: pip install nuitka")
        return 1


def create_installer(version: str, plat: str):
    """Create platform-specific installer (Windows: InnoSetup, Linux: AppImage)."""
    is_windows = plat == "windows" or platform.system() == "Windows"

    if is_windows:
        iss_path = ROOT / "installer.iss"
        if not iss_path.exists():
            print("⚠️  InnoSetup script not found — skipping installer creation")
            return

        print("📦 Creating Windows installer with InnoSetup...")
        try:
            subprocess.run(
                ["iscc", str(iss_path), f"/DAppVersion={version}"],
                cwd=ROOT, check=True
            )
            print("✅ Installer created")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"⚠️  Installer creation failed: {e}")

    else:
        print("📦 Creating Linux AppImage...")
        appdir = DIST_DIR / "AppDir"
        appdir.mkdir(exist_ok=True)

        # Create AppImage structure
        (appdir / "usr" / "bin").mkdir(parents=True, exist_ok=True)
        (appdir / "usr" / "share" / "applications").mkdir(parents=True, exist_ok=True)
        (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True, exist_ok=True)

        desktop_entry = f"""[Desktop Entry]
Name=Standard El-Joumla ERP
Comment=Enterprise Resource Planning System
Exec=StandardElJoumla
Icon=standard-eljoumla
Type=Application
Categories=Office;Business;Qt;
Version={version}
"""
        (appdir / "usr" / "share" / "applications" / "standard-eljoumla.desktop").write_text(desktop_entry)

        try:
            subprocess.run(
                ["appimagetool", str(appdir), f"StandardElJoumla-{version}-x86_64.AppImage"],
                cwd=DIST_DIR, check=True
            )
            print("✅ AppImage created")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  AppImage creation failed — appimagetool not installed")


def main():
    parser = argparse.ArgumentParser(description="Build Standard El-Joumla ERP")
    parser.add_argument("--mode", choices=["standalone", "onefile"], default="standalone",
                        help="Build mode (default: standalone)")
    parser.add_argument("--platform", choices=["auto", "windows", "linux"], default="auto",
                        help="Target platform (default: auto-detect)")
    parser.add_argument("--clean", action="store_true", help="Clean build dirs first")
    parser.add_argument("--installer", action="store_true", help="Create installer after build")
    parser.add_argument("--version", default=None, help="Override version number")
    args = parser.parse_args()

    version = args.version or get_version()
    plat = args.platform
    if plat == "auto":
        plat = "windows" if platform.system() == "Windows" else "linux"

    print(f"""
╔══════════════════════════════════════════════════════╗
║     Standard El-Joumla ERP — Build System            ║
║     Version: {version:<40}║
║     Mode: {args.mode:<44}║
║     Platform: {plat:<41}║
╚══════════════════════════════════════════════════════╝
""")

    if args.clean:
        clean_build_dirs()

    rc = build_nuitka(args.mode, plat, version)
    if rc != 0:
        sys.exit(rc)

    if args.installer:
        create_installer(version, plat)

    print(f"\n🎉 Build complete! Version {version}")


if __name__ == "__main__":
    main()
