#!/usr/bin/env python3
import subprocess, sys, os
os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
print("Running pytest...")
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/test_backup_service.py', '-v'],
    capture_output=True, text=True, timeout=60
)
print("STDOUT:", result.stdout[-2000:])
print("STDERR:", result.stderr[-500:])
print("Return code:", result.returncode)
