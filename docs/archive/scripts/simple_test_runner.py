#!/usr/bin/env python3
"""Simple test runner"""
import subprocess
import sys
import os

os.chdir(r'c:\Users\aboun\Desktop\Logical Version trae')
sys.path.insert(0, r'c:\Users\aboun\Desktop\Logical Version trae')

print("Running tests...")

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/',
     '--tb=no', '-q',
     '--ignore=tests/unit/test_backup_service.py',
     '--ignore=tests/unit/test_api_authenticator.py',
     '--ignore=tests/unit/test_ai_service_ui.py'],
    capture_output=True,
    text=True,
    timeout=300
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")

# Save to file
with open('SIMPLE_TEST_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write(result.stdout)
    f.write("\n")
    f.write(result.stderr)
