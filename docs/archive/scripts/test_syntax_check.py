#!/usr/bin/env python3
"""
فحص syntax لجميع ملفات الاختبارات
"""
import ast
import os
import sys

project_root = 'c:/Users/aboun/Desktop/Logical Version trae'
os.chdir(project_root)
sys.path.insert(0, project_root)

# الملفات التي تم الإبلاغ عنها بها أخطاء
problematic_files = [
    'tests/unit/test_database_logger_extended.py',
    'tests/unit/test_database_logger_fixes.py',
    'tests/unit/test_focus_style_manager.py',
    'tests/unit/test_login_dialog.py',
    'tests/unit/test_abc_analysis_window.py',
    'tests/unit/test_backup_service.py',
]

print("=" * 80)
print("🔍 فحص الملفات المشكوك فيها:")
print("=" * 80)

errors = []
for file_path in problematic_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print(f"✅ {file_path} - لا يوجد أخطاء syntax")
    except SyntaxError as e:
        errors.append((file_path, str(e)))
        print(f"❌ {file_path}: {e}")
    except Exception as e:
        errors.append((file_path, str(e)))
        print(f"⚠️ {file_path}: {e}")

print("=" * 80)
print(f"📊 النتيجة: {len(errors)} أخطاء")
print("=" * 80)

if errors:
    print("\n❌ الملفات التي تحتوي على أخطاء:")
    for file_path, error in errors:
        print(f"   {file_path}")
        print(f"      {error}")
    sys.exit(1)
else:
    print("\n🎉 0 أخطاء - جميع الملفات صحيحة!")
    sys.exit(0)
