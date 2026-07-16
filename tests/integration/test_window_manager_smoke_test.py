#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window Manager Smoke Test - اختبار سريع للنوافذ
Quick smoke test for all registered windows
"""

import sys
import time

from PySide6.QtWidgets import QApplication

from src.core.window_manager import WindowManager


def smoke_test():
    """
    اختبار سريع لجميع النوافذ المسجلة
    يفتح ويغلق كل نافذة بسرعة للتحقق من عدم وجود أخطاء حرجة
    """
    app = QApplication(sys.argv)
    wm = WindowManager(organization="LogicalVersion", appname="ERP", parent=None)

    # تسجيل نافذة اختبار بسيطة للتحقق من أن النظام يعمل
    from PySide6.QtWidgets import QMainWindow

    class TestWindow(QMainWindow):
        window_key = "test_smoke"
        window_singleton = True
        window_title = "Test Window"

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Test Window")
            self.resize(400, 300)

    # تسجيل نافذة الاختبار
    wm.register_window(
        window_key="test_smoke",
        window_class=TestWindow,
        title="Test Window",
        singleton=True,
    )

    # ملاحظة: النوافذ يجب أن تكون مسجلة مسبقاً في main_window.py
    # هذا الاختبار يتحقق فقط من أن النوافذ المسجلة يمكن فتحها وإغلاقها

    keys = list(wm._configs.keys())

    if not keys:
        # print("⚠️  لا توجد نوافذ مسجلة!")
        pass
        # print("   تأكد من أن main_window.py يقوم بتسجيل النوافذ")
        return []

    # print(f"✅ تم العثور على {len(keys)} نافذة مسجلة")
    # print(f"📋 النوافذ: {', '.join(keys)}")
    # print()

    failures = []

    for k in keys:
        # print(f"🔍 فتح {k}...", end=" ")
        try:
            inst = wm.open_window(k)
            if not inst:
                # print("❌ فشل")
                failures.append(k)
                continue

            time.sleep(0.2)  # انتظار قصير لمحاكاة فتح فعلي

            if not wm.is_open(k):
                # print("⚠️  غير مفتوحة")
                failures.append(k)
            else:
                # print("✅ نجح")
                pass

            # print(f"   🔒 إغلاق {k}...", end=" ")
            closed = wm.close_window(k)
            if not closed:
                # print("❌ فشل")
                failures.append(k)
            else:
                # print("✅ نجح")
                pass

            time.sleep(0.1)

        except Exception as e:  # noqa: F841
            # print(f"❌ خطأ: {e}")
            failures.append(k)

    # print()
    wm.close_all()

    if failures:
        # print(f"❌ فشل في {len(failures)} نافذة: {', '.join(failures)}")
        pass
    else:
        # print("✅ جميع النوافذ تعمل بشكل صحيح!")
        pass

    app.quit()
    return failures


if __name__ == "__main__":
    # print("=" * 60)
    pass
    # print("Window Manager Smoke Test")
    # print("=" * 60)
    # print()

    fails = smoke_test()

    # print()
    # print("=" * 60)

    if fails:
        # print(f"❌ SMOKE TEST FAILED: {len(fails)} نافذة فشلت")
        sys.exit(2)
    else:
        # print("✅ SMOKE TEST PASSED: جميع النوافذ تعمل!")
        sys.exit(0)
