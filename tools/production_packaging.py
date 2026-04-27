#!/usr/bin/env python3
"""Production packaging helper"""
import subprocess, sys

def run(cmd: str):
    print(f"$ {cmd}")
    return subprocess.run(cmd, shell=True, check=True)

def main():
    # Update and install production dependencies
    run("python -m pip install --upgrade pip wheel setuptools")
    run("pip install -r api/requirements-prod.txt")
    run("npm ci --prefix web")
    run("npm run build --prefix web")
    # Desktop packaging (PyInstaller) - attempt to create a Windows executable if PyInstaller is available
    try:
        import PyInstaller  # type: ignore
        try:
            import PyInstaller.__main__ as pyinst  # type: ignore
            desktop_launcher = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'desktop_launcher.py'))
            if not os.path.exists(desktop_launcher):
                print("Desktop launcher not found; skipping desktop packaging.")
            else:
                pyinst.run([
                    '--onefile',
                    '--windowed',
                    '--name', 'trae_desktop',
                    desktop_launcher
                ])
                print("Desktop packaging completed: trae_desktop.exe")
        except Exception as e:
            print(f"Desktop packaging failed: {e}")
    except Exception:
        print("PyInstaller not installed; desktop packaging skipped. Install PyInstaller to enable EXE packaging.")

if __name__ == "__main__":
    main()
