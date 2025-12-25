#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run All Tests Script
تشغيل جميع الاختبارات
"""

import sys
import subprocess
from pathlib import Path

def run_test(script_name, description):
    """تشغيل اختبار"""
    print(f"\n{'=' * 50}")
    print(f"{description}")
    print("=" * 50)
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            timeout=300
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠️ {description} انتهت مهلة الانتظار")
        return False
    except Exception as e:
        print(f"❌ خطأ في {description}: {e}")
        return False


def main():
    """الدالة الرئيسية"""
    print("🧪 تشغيل جميع الاختبارات...")
    print("=" * 50)
    
    tests = [
        ("test_services.py", "1️⃣ اختبار الخدمات (Services Tests)"),
        ("test_docker.py", "2️⃣ اختبار Docker Setup"),
        ("test_api.py", "3️⃣ اختبار REST API"),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for script, description in tests:
        if run_test(script, description):
            total_passed += 1
        else:
            total_failed += 1
    
    # Final Summary
    print("\n" + "=" * 50)
    print("📊 الملخص النهائي:")
    print("=" * 50)
    print(f"   ✅ نجحت: {total_passed}")
    print(f"   ❌ فشلت: {total_failed}")
    print("=" * 50)
    
    if total_failed == 0:
        print("\n🎉 جميع الاختبارات نجحت! النظام جاهز!")
        return 0
    else:
        print("\n⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

