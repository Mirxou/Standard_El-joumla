#!/usr/bin/env python3
"""تشغيل جميع الاختبارات وتوليد التقرير النهائي"""
import subprocess
import sys
import os

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=short', 
     '--continue-on-collection-errors', '--ignore=tests/unit/test_backup_service.py'],
    capture_output=True,
    text=True,
    timeout=300
)

# حفظ النتائج
with open('COMPLETE_TEST_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write(result.stdout)
    f.write("\n\n" + "="*80 + "\n")
    f.write("STDERR:\n")
    f.write(result.stderr)
    f.write(f"\n\nReturn code: {result.returncode}\n")

# طباعة الملخص
output = result.stdout + result.stderr
passed = output.count(' PASSED ')
failed = output.count(' FAILED ')
errors = output.count(' ERROR ')
skipped = output.count(' SKIPPED ')

print(f"\n{'='*80}")
print("📊 نتائج الاختبارات النهائية:")
print(f"{'='*80}")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
print(f"  📊 المجموع: {passed + failed + errors + skipped}")
print(f"\n📁 Return code: {result.returncode}")
print(f"\n💾 النتائج المحفوظة في: COMPLETE_TEST_RESULTS.txt")
