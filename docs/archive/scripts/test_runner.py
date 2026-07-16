#!/usr/bin/env python3
"""
Quick test runner to verify fixes
"""
import subprocess
import sys
import os

os.chdir(r'c:\Users\aboun\Desktop\Logical Version trae')
sys.path.insert(0, r'c:\Users\aboun\Desktop\Logical Version trae')

print("🚀 تشغيل اختبار test_backup_service.py...")
print("="*80)

# Run a quick test
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/unit/test_backup_service.py', '-v', '--tb=short'],
    capture_output=True,
    text=True,
    timeout=120
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Save results
with open('test_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"Return code: {result.returncode}\n")
    f.write("=" * 80 + "\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n" + "=" * 80 + "\n")
    f.write("STDERR:\n")
    f.write(result.stderr)
    f.write("\n" + "=" * 80 + "\n")

# Count results
output = result.stdout + result.stderr
passed = output.count(' PASSED ')
failed = output.count(' FAILED ')
errors = output.count(' ERROR ')
skipped = output.count(' SKIPPED ')

print(f"\n{'='*80}")
print("📊 ملخص الاختبار:")
print(f"  ✅ PASSED:  {passed}")
print(f"  ❌ FAILED:  {failed}")
print(f"  💥 ERRORS:  {errors}")
print(f"  ⏭️ SKIPPED: {skipped}")
print(f"  ─────────────")
print(f"  📊 المجموع: {passed + failed + errors + skipped}")
print(f"{'='*80}")

print(f"Tests completed. Return code: {result.returncode}")
print(f"Output saved to test_results.txt")
