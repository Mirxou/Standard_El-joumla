#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص استخدامات sqlite3 المباشرة - Check Direct SQLite3 Usage
"""

from pathlib import Path

def main():
    print("🔍 البحث عن استخدامات sqlite3 المباشرة...")

    project_root = Path(__file__).parent
    sqlite_files = []

    # البحث في ملفات Python
    for py_file in project_root.rglob("*.py"):
        if "test" in str(py_file).lower() or "migration" in str(py_file).lower():
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'sqlite3.connect' in content:
                sqlite_files.append(str(py_file))
        except Exception as e:
            print(f"خطأ في قراءة {py_file}: {e}")

    print(f"📋 تم العثور على {len(sqlite_files)} ملف يستخدم sqlite3.connect:")
    for file in sqlite_files:
        print(f"  - {file}")

    print("\n✅ تم فحص الملفات بنجاح")
    print("💡 يُنصح بإعادة كتابة هذه الملفات لاستخدام DatabaseManager أو Repository pattern")

if __name__ == "__main__":
    main()