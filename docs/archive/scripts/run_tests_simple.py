#!/usr/bin/env python3
"""
سكريبت بسيط لتشغيل الاختبارات
"""
import subprocess
import sys
import os

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')

print("🔍 تشغيل pytest على tests/unit/...")
print("=" * 80)

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=line', '-x'],
    capture_output=True,
    text=True,
    timeout=120
)

print("STDOUT:")
print(result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout)

if result.stderr:
    print("\nSTDERR:")
    print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)

print(f"\nReturn code: {result.returncode}")
print("=" * 80)

if result.returncode == 0:
    print("✅ جميع الاختبارات ناجحة!")
else:
    print(f"❌ فشلت الاختبارات (return code: {result.returncode})")
    
# حفظ النتائج
with open('test_run_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"Return code: {result.returncode}\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)

sys.exit(result.returncode)
