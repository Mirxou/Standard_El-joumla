"""Script to run pytest and capture errors clearly"""
import subprocess
import sys
import os

os.chdir(r"C:\Users\aboun\Desktop\Logical Version trae")

result = subprocess.run(
    [
        sys.executable, "-m", "pytest",
        "tests/",
        "--co",
        "--tb=long",
        "-s",
        "-q",
        "--no-header",
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    cwd=r"C:\Users\aboun\Desktop\Logical Version trae",
)

print("=== STDOUT ===")
print(result.stdout[-20000:] if len(result.stdout) > 20000 else result.stdout)
print("=== STDERR ===")
print(result.stderr[-20000:] if len(result.stderr) > 20000 else result.stderr)
print(f"=== Return code: {result.returncode} ===")
