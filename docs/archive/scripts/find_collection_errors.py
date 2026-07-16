"""Find which test files cause collection errors by testing imports individually"""
import subprocess
import sys
import os
import glob

project_dir = r"C:\Users\aboun\Desktop\Logical Version trae"
test_dirs = [
    "tests/services",
    "tests/unit",
    "tests/models",
    "tests/integration",
    "tests/performance",
    "tests/utils",
    "tests/api",
    "tests/core",
]

errors = []

for test_dir in test_dirs:
    full_dir = os.path.join(project_dir, test_dir)
    if not os.path.exists(full_dir):
        continue
    test_files = glob.glob(os.path.join(full_dir, "test_*.py"))
    for test_file in test_files:
        rel_path = os.path.relpath(test_file, project_dir)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", rel_path, "--co", "-q", "--tb=short", "--no-header", "-x"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=project_dir,
            timeout=30
        )
        combined = result.stdout + result.stderr
        if "error" in combined.lower() and "collected" in combined.lower() and "0/" in combined:
            print(f"ERROR in: {rel_path}")
            # Extract error lines
            lines = combined.split("\n")
            for i, line in enumerate(lines):
                if "ERROR" in line or "Error" in line or "error" in line.lower():
                    print(f"  {line}")
            errors.append((rel_path, combined))
        elif result.returncode != 0 and "error" in combined.lower():
            # Check if it's just a collection error
            if "ImportError" in combined or "ModuleNotFoundError" in combined or "NameError" in combined or "SyntaxError" in combined:
                print(f"IMPORT ERROR in: {rel_path}")
                lines = combined.split("\n")
                for line in lines:
                    if any(e in line for e in ["Error", "error", "import", "Import"]):
                        print(f"  {line}")
                errors.append((rel_path, combined))

print(f"\n\nTotal files with errors: {len(errors)}")
