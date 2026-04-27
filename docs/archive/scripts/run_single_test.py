#!/usr/bin/env python3
"""تشغيل pytest على ملف واحد والحصول على النتائج"""
import subprocess
import sys
import os

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("=" * 80)
print("🧪 تشغيل pytest على tests/unit/test_backup_service.py")
print("=" * 80)
print()

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/test_backup_service.py', '-v', '--tb=short'],
    capture_output=True,
    text=True,
    timeout=60
)

# حفظ النتائج
with open('BACKUP_SERVICE_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("PYTEST RESULTS - test_backup_service.py\n")
    f.write("=" * 80 + "\n\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("STDERR:\n")
    f.write(result.stderr)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write(f"Return code: {result.returncode}\n")

# عرض النتائج
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)

print()
print("=" * 80)
print(f"📊 Return code: {result.returncode}")
print("=" * 80)

# عد الأخطاء
failed = result.stdout.count('FAILED')
errors = result.stdout.count('ERROR')
passed = result.stdout.count('PASSED')

print(f"✅ PASSED: {passed}")
print(f"❌ FAILED: {failed}")
print(f"💥 ERRORS: {errors}")
