#!/usr/bin/env python3
"""
تشغيل شاملة لجميع الاختبارات مع تقرير مفصل
"""
import subprocess
import sys
import os
import re
from pathlib import Path

os.chdir(r'c:\Users\aboun\Desktop\Logical Version trae')
sys.path.insert(0, r'c:\Users\aboun\Desktop\Logical Version trae')

print("="*80)
print("🚀 بدء التشغيل الشامل لجميع الاختبارات")
print("="*80)

# تعطيل PyQt5
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# تشغيل جميع الاختبارات باستثناء test_backup_service.py
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', 
     '-v', '--tb=line', 
     '--continue-on-collection-errors',
     '--ignore=tests/unit/test_backup_service.py'],
    capture_output=True,
    text=True,
    timeout=600
)

output = result.stdout + result.stderr

# عد النتائج
passed = len(re.findall(r'\sPASSED\s', output))
failed = len(re.findall(r'\sFAILED\s', output))
errors = len(re.findall(r'\sERROR\s', output))
skipped = len(re.findall(r'\sSKIPPED\s', output))

# استخراج الأخطاء الفريدة
error_patterns = []
for line in output.split('\n'):
    if 'FAILED' in line or 'ERROR' in line:
        if '::' in line:
            test_name = line.split('::')[1].split()[0] if '::' in line else 'unknown'
            error_patterns.append(test_name)

# حفظ النتائج
with open('ALL_TESTS_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write(f"Return code: {result.returncode}\n")
    f.write("="*80 + "\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n" + "="*80 + "\n")
    f.write("STDERR:\n")
    f.write(result.stderr)
    f.write("\n" + "="*80 + "\n")
    f.write("SUMMARY:\n")
    f.write(f"  PASSED:  {passed}\n")
    f.write(f"  FAILED:  {failed}\n")
    f.write(f"  ERRORS:  {errors}\n")
    f.write(f"  SKIPPED: {skipped}\n")
    f.write(f"  TOTAL:   {passed + failed + errors + skipped}\n")

print(f"\n{'='*80}")
print("📊 نتائج الاختبارات الشاملة:")
print(f"{'='*80}")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
total = passed + failed + errors + skipped
print(f"  📊 المجموع: {total}")
if total > 0:
    print(f"  📈 نسبة النجاح: {(passed/total*100):.1f}%")
print(f"{'='*80}")

# عرض أول 10 أخطاء
if failed > 0 or errors > 0:
    print("\n❌ الأخطاء المكتشفة:")
    error_lines = [l for l in output.split('\n') if 'FAILED' in l or 'ERROR' in l][:10]
    for line in error_lines:
        print(f"  - {line[:80]}")

print(f"\n💾 تم حفظ النتائج في: ALL_TESTS_RESULTS.txt")
print("="*80)
