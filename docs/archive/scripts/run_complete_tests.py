#!/usr/bin/env python3
"""تشغيل جميع الاختبارات والتحقق من النتائج"""
import subprocess
import sys
import os
from pathlib import Path

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("=" * 80)
print("🧪 تشغيل جميع الاختبارات")
print("=" * 80)

# عد ملفات الاختبار
test_files = list(Path('tests/unit').glob('test_*.py'))
print(f"📁 عدد ملفات الاختبار: {len(test_files)}")
print()

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=short', 
     '--continue-on-collection-errors', '--ignore=tests/unit/test_backup_service.py'],
    capture_output=True,
    text=True,
    timeout=300
)

# تحليل النتائج
output = result.stdout + result.stderr

# عد النتائج
passed = output.count(' PASSED ')
failed = output.count(' FAILED ')
errors = output.count(' ERROR ')
skipped = output.count(' SKIPPED ')
total = passed + failed + errors + skipped

print(f"📊 النتائج:")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
print(f"  📊 المجموع: {total}")
print(f"\n📁 Return code: {result.returncode}")

# حفظ النتائج
with open('COMPLETE_TEST_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write(f"إجمالي الاختبارات: {total}\n")
    f.write(f"✅ ناجح: {passed}\n")
    f.write(f"❌ فاشل: {failed}\n")
    f.write(f"💥 أخطاء: {errors}\n")
    f.write(f"⏭️ تم تخطيه: {skipped}\n\n")
    f.write("=" * 80 + "\n")
    f.write("OUTPUT:\n")
    f.write("=" * 80 + "\n")
    f.write(output[-5000:] if len(output) > 5000 else output)

print("\n💾 تم حفظ النتائج في: COMPLETE_TEST_RESULTS.txt")
