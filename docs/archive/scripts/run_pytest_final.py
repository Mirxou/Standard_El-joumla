#!/usr/bin/env python3
"""
تشغيل pytest والحصول على النتائج الكاملة
"""
import subprocess
import sys
import os

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("=" * 80)
print("🧪 تشغيل pytest على tests/unit/")
print("=" * 80)

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=line'],
    capture_output=True,
    text=True,
    timeout=180,
    encoding='utf-8'
)

# حفظ النتائج الكاملة
with open('PYTEST_RESULTS.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("PYTEST RESULTS\n")
    f.write("=" * 80 + "\n\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("STDERR:\n")
    f.write(result.stderr)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write(f"Return code: {result.returncode}\n")

# عرض ملخص
print("\n📊 ملخص النتائج:")
print("=" * 80)

# عد الأخطاء
failed_count = result.stdout.count('FAILED')
error_count = result.stdout.count('ERROR')
passed_count = result.stdout.count('PASSED')
warning_count = result.stderr.count('warning') + result.stdout.count('warning')

print(f"✅ PASSED: ~{passed_count}")
print(f"❌ FAILED: {failed_count}")
print(f"💥 ERRORS: {error_count}")
print(f"⚠️ WARNINGS: {warning_count}")

# عرض الأخطاء المهمة
if result.returncode != 0:
    print("\n❌ الاختبارات فشلت!")
    print("\nأول 20 خطأ:")
    lines = result.stdout.split('\n')
    error_lines = [l for l in lines if 'FAILED' in l or 'ERROR' in l][:20]
    for line in error_lines:
        print(f"   {line}")
else:
    print("\n🎉 جميع الاختبارات ناجحة!")

print("\n📁 النتائج الكاملة محفوظة في: PYTEST_RESULTS.txt")
print("=" * 80)

sys.exit(result.returncode)
