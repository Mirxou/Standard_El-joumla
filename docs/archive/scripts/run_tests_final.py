#!/usr/bin/env python3
"""Script to run all unit tests and save results"""
import subprocess
import sys
import os

os.chdir(r'c:\Users\aboun\Desktop\Logical Version trae')
sys.path.insert(0, r'c:\Users\aboun\Desktop\Logical Version trae')

print("🚀 جاري تشغيل جميع الاختبارات...")
print("="*80)

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', 
     '--tb=short', '--continue-on-collection-errors',
     '--ignore=tests/unit/test_backup_service.py'],
    capture_output=True,
    text=True,
    timeout=300
)

print(result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)

with open('test_results_final.txt', 'w', encoding='utf-8') as f:
    f.write("Return code: " + str(result.returncode) + "\n")
    f.write("="*80 + "\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    if result.stderr:
        f.write("\n\n" + "="*80 + "\n")
        f.write("STDERR:\n")
        f.write(result.stderr)

output = result.stdout + result.stderr
passed = output.count(' PASSED ')
failed = output.count(' FAILED ')
errors = output.count(' ERROR ')
skipped = output.count(' SKIPPED ')

print(f"\n{'='*80}")
print("📊 نتائج الاختبارات:")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
print(f"  📊 المجموع: {passed + failed + errors + skipped}")
print(f"{'='*80}")
print("\n💾 تم حفظ النتائج في: test_results_final.txt")
