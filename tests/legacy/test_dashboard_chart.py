#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Interactive Dashboard Chart
سكريبت اختبار للرسم البياني التفاعلي
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
import sys  # noqa: F811
from pathlib import Path

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])


def test_sales_chart_widget():
    """اختبار ويدجت الرسم البياني"""
    # print("=" * 60)
    # print("🧪 اختبار ويدجت الرسم البياني (SalesChartWidget)")
    # print("=" * 60)

    try:
        # 1. اختبار الاستيراد
        # print("\n1️⃣ اختبار الاستيراد...")
        from src.ui.widgets.sales_chart import SalesChartWidget

        # print("   ✅ تم استيراد SalesChartWidget بنجاح")

        # 2. اختبار إنشاء الويدجت
        # print("\n2️⃣ اختبار إنشاء الويدجت...")
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            chart = SalesChartWidget()
            # print("   ✅ تم إنشاء الويدجت بنجاح")

            # 3. اختبار تحديث البيانات
            # print("\n3️⃣ اختبار تحديث البيانات...")
            days = [1, 2, 3, 4, 5, 6, 7]
            amounts = [1000.0, 1500.0, 800.0, 2200.0, 1800.0, 3000.0, 2500.0]

            chart.update_chart(days, amounts)
            # print("   ✅ تم تحديث الرسم البياني بنجاح")

            # 4. اختبار PyQtGraph
            # print("\n4️⃣ اختبار PyQtGraph...")
            try:
                pass
                # print(f"   ✅ PyQtGraph مثبت - الإصدار: {pg.__version__}")
            except ImportError:
                # print("   ⚠️  PyQtGraph غير مثبت - سيتم عرض رسالة بدلاً من الرسم")
                pass
                # print("   💡 قم بتثبيته: pip install pyqtgraph")

            # print("\n" + "=" * 60)
            # print("✅ جميع الاختبارات نجحت!")
            # print("=" * 60)
            return True

        except Exception as e:  # noqa: F841
            # print(f"   ❌ خطأ في إنشاء الويدجت: {e}")
            return False

    except ImportError as e:  # noqa: F841
        # print(f"   ❌ خطأ في الاستيراد: {e}")
        return False
    except Exception as e:  # noqa: F841
        # print(f"   ❌ خطأ غير متوقع: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_chart_data_formatting():
    """اختبار تنسيق بيانات الرسم البياني"""
    # print("\n" + "=" * 60)
    # print("🧪 اختبار تنسيق بيانات الرسم البياني")
    # print("=" * 60)

    try:
        # بيانات تجريبية
        days = [1, 2, 3, 4, 5, 6, 7]  # noqa: F841
        amounts = [1000.0, 1500.0, 800.0, 2200.0, 1800.0, 3000.0, 2500.0]  # noqa: F841

        # print("\n📊 البيانات:")
        # print(f"   الأيام: {days}")
        # print(f"   المبالغ: {amounts}")
        # print(f"   الإجمالي: {sum(amounts):,.2f} دج")
        # print(f"   المتوسط: {sum(amounts)/len(amounts):,.2f} دج")
        # print(f"   الأعلى: {max(amounts):,.2f} دج (اليوم {days[amounts.index(max(amounts))]})")
        # print(f"   الأدنى: {min(amounts):,.2f} دج (اليوم {days[amounts.index(min(amounts))]})")

        # print("\n✅ تنسيق البيانات صحيح")
        return True

    except Exception as e:  # noqa: F841
        # print(f"❌ خطأ في تنسيق البيانات: {e}")
        return False


if __name__ == "__main__":
    import io
    import sys  # noqa: F811

    # إصلاح encoding في Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # print("\nبدء اختبارات الداشبورد التفاعلي\n")

    # اختبار الويدجت
    test1 = test_sales_chart_widget()

    # اختبار تنسيق البيانات
    test2 = test_chart_data_formatting()

    # النتيجة النهائية
    # print("\n" + "=" * 60)
    if test1 and test2:
        # print("✅ جميع الاختبارات نجحت!")
        pass
        # print("=" * 60)
        sys.exit(0)
    else:
        # print("❌ بعض الاختبارات فشلت")
        pass
        # print("=" * 60)
        sys.exit(1)
