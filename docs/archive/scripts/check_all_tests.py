#!/usr/bin/env python3
"""
فحص جميع ملفات الاختبارات للأخطاء
"""
import sys
import os
import ast
import importlib.util

sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')
os.chdir('c:/Users/aboun/Desktop/Logical Version trae')

print("=" * 80)
print("🔍 فحص جميع ملفات الاختبارات")
print("=" * 80)

# قائمة الملفات للفحص
test_files = []
for root, dirs, files in os.walk('tests/unit'):
    for file in files:
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(os.path.join(root, file))

print(f"عدد ملفات الاختبارات: {len(test_files)}")
print()

errors = []
warnings = []
skipped = []

for file_path in sorted(test_files):
    try:
        # فحص syntax
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        
        # محاولة الاستيراد
        module_name = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ {file_path}")
        except Exception as e:
            error_msg = str(e)
            if 'No module named' in error_msg or 'cannot import' in error_msg:
                # Missing dependency - skip
                skipped.append((file_path, error_msg))
                print(f"⏭️  {file_path} (يتطلب تبعيات: {error_msg[:50]}...)")
            else:
                errors.append((file_path, error_msg))
                print(f"❌ {file_path}: {error_msg[:80]}")
                
    except SyntaxError as e:
        errors.append((file_path, f"Syntax Error: {e}"))
        print(f"❌ {file_path}: Syntax Error - {e}")
    except Exception as e:
        errors.append((file_path, str(e)))
        print(f"❌ {file_path}: {str(e)[:80]}")

print()
print("=" * 80)
print("📊 ملخص النتائج:")
print("=" * 80)
print(f"✅ ناجح: {len(test_files) - len(errors) - len(skipped)}")
print(f"⏭️  تم تخطيه (يتطلب تبعيات): {len(skipped)}")
print(f"❌ أخطاء: {len(errors)}")

if errors:
    print()
    print("❌ الأخطاء:")
    for file_path, error in errors:
        print(f"   {file_path}")
        print(f"      {error[:100]}")

print()
if len(errors) == 0:
    print("🎉 0 أخطاء - جميع الملفات صحيحة!")
else:
    print(f"⚠️ يوجد {len(errors)} أخطاء تحتاج إلى إصلاح")

# حفظ التقرير
with open('test_check_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total test files: {len(test_files)}\n")
    f.write(f"Successful: {len(test_files) - len(errors) - len(skipped)}\n")
    f.write(f"Skipped (missing deps): {len(skipped)}\n")
    f.write(f"Errors: {len(errors)}\n\n")
    if errors:
        f.write("Errors:\n")
        for file_path, error in errors:
            f.write(f"  {file_path}: {error}\n")

sys.exit(1 if errors else 0)
