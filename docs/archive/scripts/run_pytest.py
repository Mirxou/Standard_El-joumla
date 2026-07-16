#!/usr/bin/env python3
"""تشغيل pytest والحصول على النتائج"""
import subprocess
import sys
import os

os.chdir('c:/Users/aboun/Desktop/Logical Version trae')
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

print("=" * 80)
print("🧪 تشغيل pytest على جميع ملفات الاختبارات")
print("=" * 80)
print()

# تشغيل pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=line'],
    capture_output=True,
    text=True,
    timeout=180
)

# حفظ النتائج
with open('TEST_RESULTS.txt', 'w', encoding='utf-8') as f:
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

# عرض النتائج
lines = result.stdout.split('\n')
print("أول 50 سطر من النتائج:")
print("-" * 80)
for line in lines[:50]:
    print(line)

# عد الأخطاء
failed = result.stdout.count('FAILED')
errors = result.stdout.count('ERROR')
passed = result.stdout.count('PASSED')

print()
print("=" * 80)
print(f"📊 ملخص: {passed} ناجح, {failed} فاشل, {errors} خطأ")
print("=" * 80)

if result.returncode == 0:
    print("🎉 جميع الاختبارات ناجحة!")
else:
    print(f"❌ Return code: {result.returncode}")
    print("\nأخطاء مهمة:")
    for line in lines:
        if 'FAILED' in line or 'ERROR' in line:
            print(f"  {line}")

print("\n📁 النتائج الكاملة محفوظة في: TEST_RESULTS.txt")
