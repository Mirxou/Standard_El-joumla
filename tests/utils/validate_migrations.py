#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للتحقق من صحة ملفات migrations
Script to validate migration files
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple


def validate_migration_files(migrations_dir: Path) -> Dict[str, any]:
    """التحقق من صحة ملفات migrations"""
    
    issues = {
        "duplicate_numbers": [],
        "missing_numbers": [],
        "invalid_names": [],
        "sql_errors": [],
        "foreign_key_issues": []
    }
    
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        return {"error": "لا توجد ملفات migrations"}
    
    # استخراج الأرقام من أسماء الملفات
    migration_numbers = {}
    number_pattern = re.compile(r'^(\d{3})_')
    
    for migration_file in migration_files:
        match = number_pattern.match(migration_file.name)
        if match:
            number = int(match.group(1))
            if number in migration_numbers:
                issues["duplicate_numbers"].append({
                    "number": number,
                    "files": [migration_numbers[number], migration_file.name]
                })
            else:
                migration_numbers[number] = migration_file.name
        else:
            issues["invalid_names"].append(migration_file.name)
    
    # التحقق من الأرقام المفقودة
    if migration_numbers:
        min_num = min(migration_numbers.keys())
        max_num = max(migration_numbers.keys())
        expected_numbers = set(range(min_num, max_num + 1))
        actual_numbers = set(migration_numbers.keys())
        missing = expected_numbers - actual_numbers
        if missing:
            issues["missing_numbers"] = sorted(missing)
    
    # التحقق من صحة SQL
    for migration_file in migration_files:
        try:
            content = migration_file.read_text(encoding='utf-8')
            
            # التحقق من وجود PRAGMA foreign_keys
            if "ALTER TABLE" in content or "CREATE TABLE" in content:
                if "PRAGMA foreign_keys" not in content and "PRAGMA foreign_keys = ON" not in content:
                    issues["sql_errors"].append({
                        "file": migration_file.name,
                        "issue": "قد تحتاج إلى PRAGMA foreign_keys = ON"
                    })
            
            # التحقق من وجود أخطاء SQL واضحة
            if "ALTER TABLE" in content and "IF NOT EXISTS" not in content:
                # SQLite لا يدعم IF NOT EXISTS في ALTER TABLE
                if "ADD COLUMN" in content:
                    issues["sql_errors"].append({
                        "file": migration_file.name,
                        "issue": "ALTER TABLE ADD COLUMN قد يفشل إذا كان العمود موجوداً (SQLite لا يدعم IF NOT EXISTS)"
                    })
        
        except Exception as e:
            issues["sql_errors"].append({
                "file": migration_file.name,
                "issue": f"خطأ في قراءة الملف: {e}"
            })
    
    return {
        "total_files": len(migration_files),
        "issues": issues,
        "migration_numbers": migration_numbers
    }


def generate_migration_report(migrations_dir: Path) -> str:
    """إنشاء تقرير عن ملفات migrations"""
    
    result = validate_migration_files(migrations_dir)
    
    if "error" in result:
        return f"❌ {result['error']}"
    
    report = []
    report.append("=" * 60)
    report.append("📊 تقرير التحقق من Migrations")
    report.append("=" * 60)
    report.append(f"\n📁 إجمالي الملفات: {result['total_files']}")
    report.append("")
    
    # عرض الأرقام المكررة
    if result["issues"]["duplicate_numbers"]:
        report.append("⚠️  أرقام مكررة:")
        for dup in result["issues"]["duplicate_numbers"]:
            report.append(f"   رقم {dup['number']:03d}:")
            for file in dup["files"]:
                report.append(f"      - {file}")
        report.append("")
    else:
        report.append("✅ لا توجد أرقام مكررة")
        report.append("")
    
    # عرض الأرقام المفقودة
    if result["issues"]["missing_numbers"]:
        report.append("⚠️  أرقام مفقودة:")
        for num in result["issues"]["missing_numbers"]:
            report.append(f"   - {num:03d}")
        report.append("")
    else:
        report.append("✅ لا توجد أرقام مفقودة")
        report.append("")
    
    # عرض أسماء غير صالحة
    if result["issues"]["invalid_names"]:
        report.append("⚠️  أسماء ملفات غير صالحة:")
        for name in result["issues"]["invalid_names"]:
            report.append(f"   - {name}")
        report.append("")
    else:
        report.append("✅ جميع أسماء الملفات صالحة")
        report.append("")
    
    # عرض مشاكل SQL
    if result["issues"]["sql_errors"]:
        report.append("⚠️  مشاكل محتملة في SQL:")
        for error in result["issues"]["sql_errors"]:
            report.append(f"   {error['file']}: {error['issue']}")
        report.append("")
    else:
        report.append("✅ لا توجد مشاكل واضحة في SQL")
        report.append("")
    
    # عرض قائمة الملفات مرتبة
    report.append("📋 قائمة الملفات (مرتبة):")
    for num in sorted(result["migration_numbers"].keys()):
        report.append(f"   {num:03d}: {result['migration_numbers'][num]}")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


def suggest_renaming(migrations_dir: Path) -> List[Tuple[str, str]]:
    """اقتراح إعادة تسمية الملفات لحل التكرار"""
    
    result = validate_migration_files(migrations_dir)
    
    if "error" in result or not result["issues"]["duplicate_numbers"]:
        return []
    
    suggestions = []
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    # العثور على أعلى رقم مستخدم
    max_num = max(result["migration_numbers"].keys()) if result["migration_numbers"] else 0
    
    for dup in result["issues"]["duplicate_numbers"]:
        files = dup["files"]
        # الاحتفاظ بالملف الأول كما هو، وإعادة تسمية الباقي
        for i, file_name in enumerate(files[1:], 1):
            old_path = migrations_dir / file_name
            # استخراج الجزء بعد الرقم
            parts = file_name.split("_", 1)
            if len(parts) > 1:
                new_num = max_num + i
                new_name = f"{new_num:03d}_{parts[1]}"
                new_path = migrations_dir / new_name
                suggestions.append((str(old_path), str(new_path)))
                max_num = new_num
    
    return suggestions


if __name__ == "__main__":
    import sys
    
    project_root = Path(__file__).parent.parent
    migrations_dir = project_root / "migrations"
    
    if not migrations_dir.exists():
        print(f"❌ مجلد migrations غير موجود: {migrations_dir}")
        sys.exit(1)
    
    # إنشاء التقرير
    report = generate_migration_report(migrations_dir)
    print(report)
    
    # اقتراح إعادة التسمية
    suggestions = suggest_renaming(migrations_dir)
    if suggestions:
        print("\n" + "=" * 60)
        print("💡 اقتراحات إعادة التسمية:")
        print("=" * 60)
        for old_path, new_path in suggestions:
            print(f"   {Path(old_path).name} → {Path(new_path).name}")
        print("\n⚠️  ملاحظة: يجب إعادة ترقيم الملفات يدوياً لتجنب المشاكل")




