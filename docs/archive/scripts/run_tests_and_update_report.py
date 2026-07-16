#!/usr/bin/env python3
"""تشغيل جميع الاختبارات وتحديث تقرير التغطية"""
import subprocess
import sys
import os
import re
from pathlib import Path

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("=" * 80)
print("🧪 تشغيل جميع الاختبارات وتحديث التقرير")
print("=" * 80)
print()

# الحصول على قائمة جميع ملفات الاختبار
test_files = list(Path('tests/unit').glob('test_*.py'))
print(f"📁 عدد ملفات الاختبار: {len(test_files)}")

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=line', '--continue-on-collection-errors', '-x'],
    capture_output=True,
    text=True,
    timeout=300
)

# تحليل النتائج
output = result.stdout + result.stderr

# عد الاختبارات
passed = output.count(' PASSED ')
failed = output.count(' FAILED ')
errors = output.count(' ERROR ')
skipped = output.count(' SKIPPED ')
total_tests = passed + failed + errors + skipped

# عد الملفات
files_passed = len(re.findall(r' tests/unit/test_[\w_]+\.py ', output))

print(f"\n📊 النتائج:")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
print(f"  📊 المجموع: {total_tests}")
print(f"\n📁 الملفات المختبرة: {files_passed}")

# حفظ النتائج
with open('FINAL_TEST_RUN_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("FINAL TEST RESULTS\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"إجمالي الاختبارات: {total_tests}\n")
    f.write(f"✅ ناجح: {passed}\n")
    f.write(f"❌ فاشل: {failed}\n")
    f.write(f"💥 أخطاء: {errors}\n")
    f.write(f"⏭️ تم تخطيه: {skipped}\n\n")
    f.write("=" * 80 + "\n")
    f.write("OUTPUT:\n")
    f.write("=" * 80 + "\n")
    f.write(output[-5000:] if len(output) > 5000 else output)

print("\n💾 تم حفظ النتائج في: FINAL_TEST_RUN_RESULTS.txt")

# إرجاع الملخص
print(f"\n🎯 Return code: {result.returncode}")
sys.exit(0 if (failed == 0 and errors == 0) else 1)
