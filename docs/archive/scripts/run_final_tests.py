#!/usr/bin/env python3
"""تشغيل جميع الاختبارات والتحقق من النتائج"""
import subprocess
import sys
import os

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("🚀 جاري تشغيل جميع الاختبارات...")
print("="*80)

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', 
     '--tb=line', '--continue-on-collection-errors'],
    capture_output=True,
    text=True,
    timeout=300
)

# طباعة النتائج
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# حفظ النتائج
with open('FINAL_TEST_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n\nSTDERR:\n")
        f.write(result.stderr)

print("="*80)
print(f"📊 Return code: {result.returncode}")

# عد الاختبارات
passed = result.stdout.count(' PASSED ')
failed = result.stdout.count(' FAILED ')
errors = result.stdout.count(' ERROR ')
skipped = result.stdout.count(' SKIPPED ')

print(f"\n📊 ملخص النتائج:")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
print(f"  📊 المجموع: {passed + failed + errors + skipped}")
