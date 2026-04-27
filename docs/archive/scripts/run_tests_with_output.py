#!/usr/bin/env python3
"""
تشغيل الاختبارات وحفظ النتائج في ملف
"""
import subprocess
import sys
import os
import time

os.chdir(r'c:\Users\aboun\Desktop\Logical Version trae')
sys.path.insert(0, r'c:\Users\aboun\Desktop\Logical Version trae')

# تشغيل pytest وحفظ النتائج
print("🚀 جاري تشغيل الاختبارات...")
print("="*80)

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/', 
     '-v', '--tb=line', 
     '--continue-on-collection-errors',
     '--ignore=tests/unit/test_backup_service.py',
     '--ignore=tests/unit/test_api_authenticator.py'],
    capture_output=True,
    text=True,
    timeout=600
)

# حفظ النتائج
output = result.stdout + "\n" + result.stderr

with open('TEST_RESULTS_NEW.txt', 'w', encoding='utf-8') as f:
    f.write(f"Return code: {result.returncode}\n")
    f.write("="*80 + "\n")
    f.write("OUTPUT:\n")
    f.write(output)

# طباعة الملخص
print(output[-3000:])  # Print last 3000 chars

print("\n" + "="*80)
print("✅ تم الانتهاء!")
print("💾 النتائج محفوظة في: TEST_RESULTS_NEW.txt")
