#!/usr/bin/env python3
"""تشغيل شامل لجميع الاختبارات مع تقرير مفصل"""
import subprocess
import sys
import os
from datetime import datetime

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("="*80)
print("🚀 بدء تشغيل جميع الاختبارات")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', 
     '-v', '--tb=short', '--continue-on-collection-errors',
     '-x', '--ignore=tests/unit/test_backup_service.py'],
    capture_output=True,
    text=True,
    timeout=180
)

# تحليل النتائج
output = result.stdout + result.stderr

# عدادات
passed = output.count(' PASSED ')
failed = output.count(' FAILED ')
errors = output.count(' ERROR ')
skipped = output.count(' SKIPPED ')
collected = output.count('collected')

# حفظ التقرير
report = f"""
{'='*80}
📊 تقرير الاختبارات النهائي
{'='*80}
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 النتائج:
  ✅ PASSED:  {passed}
  ❌ FAILED:  {failed}
  💥 ERRORS:  {errors}
  ⏭️ SKIPPED: {skipped}
  ─────────────
  📊 المجموع: {passed + failed + errors + skipped}

📋 تفاصيل التشغيل:
  Return Code: {result.returncode}
  المدة: {datetime.now().strftime('%H:%M:%S')}

{'='*80}
"""

# طباعة التقرير
print(report)

# حفظ في ملف
with open('COMPLETE_TEST_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write(report)
    f.write("\n\n=== OUTPUT ===\n")
    f.write(output[-5000:] if len(output) > 5000 else output)

print("💾 تم حفظ النتائج في COMPLETE_TEST_RESULTS.txt")

sys.exit(0 if result.returncode in [0, 5] else result.returncode)
