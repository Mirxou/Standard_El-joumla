#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run All Tests Orchestrator
مشغل الاختبارات الشامل
"""

import sys
from pathlib import Path

import pytest


def main():
    """الدالة الرئيسية لتشغيل الاختبارات"""
    # print("\n" + "=" * 60)
    # print("🚀 Standard El-Joumla ERP - Test Suite Orchestrator")
    # print("=" * 60)

    # تحديد مسار المشروع ومسار الاختبارات
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent

    # التأكد من وجود مسار src في sys.path
    src_path = str(project_root / "src")  # noqa: F841
    # print(f"📂 Project Root: {project_root}")
    # print(f"🧪 Tests Directory: {tests_dir}")
    # print("-" * 60)

    # تشغيل pytest
    args = [
        "-v",
        str(tests_dir),
    ]

    # التحقق من وجود معاملات إضافية
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    # print(f"🎬 Running: pytest {' '.join(args)}")

    returncode = pytest.main(args)

    # print("\n" + "=" * 60)
    if returncode == 0:
        # print("✅ SUCCESS: All tests passed!")
        pass
    else:
        # print(f"❌ FAILURE: Tests failed with exit code {returncode}")
        pass
    # print("=" * 60 + "\n")

    return returncode


if __name__ == "__main__":
    sys.exit(main())
