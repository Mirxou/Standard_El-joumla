#!/usr/bin/env python3
"""تشغيل جميع الاختبارات والتحقق من النتائج"""
import subprocess
import sys
import os

# إعداد المسار
os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("=" * 80)
print("🧪 تشغيل جميع اختبارات pytest")
print("=" * 80)
print()

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=short', '--continue-on-collection-errors'],
    capture_output=True,
    text=True,
    timeout=300
)

# حفظ النتائج الكاملة
with open('FINAL_TEST_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("FINAL PYTEST RESULTS\n")
    f.write("=" * 80 + "\n\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("STDERR:\n")
    f.write(result.stderr)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write(f"Return code: {result.returncode}\n")

# عرض الملخص
print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)

if result.stderr:
    print("\n⚠️ STDERR:")
    print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)

print("\n" + "=" * 80)
print(f"📊 Return code: {result.returncode}")
print("=" * 80)

# عد النتائج
passed = result.stdout.count(' PASSED ')
failed = result.stdout.count(' FAILED ')
errors = result.stdout.count(' ERROR ')
skipped = result.stdout.count(' SKIPPED ')

print(f"\n📈 النتائج:")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
print(f"  📊 المجموع: {passed + failed + errors + skipped}")

if result.returncode == 0 and failed == 0 and errors == 0:
    print("\n🎉 جميع الاختبارات نجحت!")
else:
    print(f"\n⚠️ هناك {failed} فشل و {errors} خطأ")
    
print("\n💾 النتائج المحفوظة في: FINAL_TEST_RESULTS.txt")
