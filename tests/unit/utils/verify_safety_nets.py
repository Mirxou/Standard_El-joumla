#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت التحقق من Safety Nets
التحقق من وجود finally blocks في جميع الدوال الحرجة
"""

import re
import sys
from pathlib import Path


def check_finally_blocks(file_path: Path) -> dict:
    """التحقق من وجود finally blocks في الدوال الحرجة"""
    results = {
        "file": str(file_path),
        "critical_functions": [],
        "missing_finally": [],
        "has_finally": [],
    }

    # الدوال الحرجة التي يجب أن تحتوي على finally
    critical_functions = [
        ("_build_page", "بناء الصفحات"),
        ("refresh_sales_data", "تحديث بيانات المبيعات"),
        ("refresh_purchases_data", "تحديث بيانات المشتريات"),
        ("refresh_payments_data", "تحديث بيانات المدفوعات"),
        ("_on_inventory_data_loaded", "معالجة بيانات المخزون"),
        ("_on_sales_data_loaded", "معالجة بيانات المبيعات"),
    ]

    try:
        content = file_path.read_text(encoding="utf-8")

        for func_name, description in critical_functions:
            # البحث عن تعريف الدالة
            func_pattern = rf"def\s+{func_name}\s*\([^)]*\):"
            func_match = re.search(func_pattern, content)

            if not func_match:
                results["critical_functions"].append(
                    {
                        "name": func_name,
                        "description": description,
                        "status": "not_found",
                        "message": f"❌ الدالة {func_name} غير موجودة",
                    }
                )
                continue

            # البحث عن finally block بعد تعريف الدالة
            func_start = func_match.end()
            func_end = find_function_end(content, func_start)
            func_body = content[func_start:func_end]

            # التحقق من وجود finally
            finally_pattern = r"finally\s*:"
            has_finally = bool(re.search(finally_pattern, func_body))

            # التحقق من وجود session_monitor_timer.start في finally
            has_timer_restart = False
            if has_finally:
                finally_match = re.search(finally_pattern, func_body)
                if finally_match:
                    finally_start = finally_match.end()
                    finally_block = func_body[finally_start:]
                    # البحث عن session_monitor_timer.start في finally block
                    timer_pattern = r"session_monitor_timer\.start\("
                    has_timer_restart = bool(re.search(timer_pattern, finally_block))

            if has_finally and has_timer_restart:
                results["has_finally"].append(
                    {
                        "name": func_name,
                        "description": description,
                        "status": "✅",
                        "message": f"✅ {func_name}: لديها finally مع إعادة تشغيل المؤقت",
                    }
                )
            elif has_finally:
                results["has_finally"].append(
                    {
                        "name": func_name,
                        "description": description,
                        "status": "⚠️",
                        "message": f"⚠️ {func_name}: لديها finally لكن بدون إعادة تشغيل المؤقت",
                    }
                )
            else:
                results["missing_finally"].append(
                    {
                        "name": func_name,
                        "description": description,
                        "status": "❌",
                        "message": f"❌ {func_name}: لا تحتوي على finally block",
                    }
                )

    except Exception as e:
        results["error"] = str(e)

    return results


def find_function_end(content: str, start_pos: int) -> int:
    """العثور على نهاية الدالة (بناءً على المسافات البادئة)"""
    lines = content[start_pos:].split("\n")
    if not lines:
        return start_pos

    # الحصول على مستوى المسافة البادئة للدالة
    first_line = lines[0] if lines else ""
    base_indent = len(first_line) - len(first_line.lstrip())

    # البحث عن السطر الأول الذي له نفس المستوى أو أقل (نهاية الدالة)
    for i, line in enumerate(lines[1:], 1):
        if line.strip():  # تخطي الأسطر الفارغة
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                return start_pos + sum(len(l) + 1 for l in lines[:i])  # noqa: E741

    return len(content)


def main():
    """الدالة الرئيسية"""
    # print("=" * 70)
    # print("🛡️  التحقق من Safety Nets (شبكة الأمان)")
    # print("=" * 70)
    # print()

    # البحث عن ملف main_window.py
    project_root = Path(__file__).parent.parent
    main_window_path = project_root / "src" / "ui" / "windows" / "main_window.py"

    if not main_window_path.exists():
        # print(f"❌ لم يتم العثور على الملف: {main_window_path}")
        sys.exit(1)

    # print(f"📁 فحص الملف: {main_window_path}")
    # print()

    # التحقق من finally blocks
    results = check_finally_blocks(main_window_path)

    # عرض النتائج
    # print("📊 النتائج:")
    # print("-" * 70)

    if results.get("error"):
        # print(f"❌ خطأ: {results['error']}")
        sys.exit(1)

    # الدوال التي لديها finally
    if results["has_finally"]:
        # print("\n✅ الدوال المحمية (لديها finally block):")
        for func in results["has_finally"]:
            # print(f"   {func['message']}")
            pass

    # الدوال المفقودة finally
    if results["missing_finally"]:
        # print("\n❌ الدوال غير المحمية (مفقودة finally block):")
        for func in results["missing_finally"]:
            # print(f"   {func['message']}")
            pass

    # الدوال غير الموجودة
    if results["critical_functions"]:
        # print("\n⚠️  الدوال غير الموجودة:")
        for func in results["critical_functions"]:
            # print(f"   {func['message']}")
            pass

    # print()
    # print("-" * 70)

    # الملخص
    total = len(results["has_finally"]) + len(results["missing_finally"]) + len(results["critical_functions"])
    protected = len([f for f in results["has_finally"] if f["status"] == "✅"])

    # print("\n📈 الملخص:")
    # print(f"   ✅ محمية بالكامل: {protected}/{total}")
    # print(f"   ⚠️  محمية جزئياً: {len([f for f in results['has_finally'] if f['status'] == '⚠️'])}")
    # print(f"   ❌ غير محمية: {len(results['missing_finally'])}")

    if protected == total and len(results["missing_finally"]) == 0:
        # print("\n🎉 جميع الدوال الحرجة محمية بالكامل!")
        pass
        # print("✅ النظام جاهز للاختبار")
        return 0
    else:
        # print("\n⚠️  يوجد دوال غير محمية - يرجى المراجعة")
        return 1


if __name__ == "__main__":
    sys.exit(main())
