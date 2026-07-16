import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sales Chart Widget - Interactive Dashboard Chart
ويدجت الرسم البياني التفاعلي للمبيعات
"""

try:
    import pyqtgraph as pg

    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

logger = logging.getLogger(__name__)


class SalesChartWidget(QFrame):
    """
    ويدجت الرسم البياني للمبيعات
    يستخدم PyQtGraph للرسم عالي الأداء
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        if not PYQTGRAPH_AVAILABLE:
            # Fallback: عرض رسالة بدلاً من الرسم
            layout = QVBoxLayout(self)
            error_label = QLabel("⚠️ PyQtGraph غير مثبت. يرجى تثبيته: pip install pyqtgraph")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: #e74c3c; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)
            logger.warning("PyQtGraph غير متاح - سيتم عرض رسالة بدلاً من الرسم البياني")
            return

        # تنسيق الإطار الخارجي
        self.setStyleSheet("""
            SalesChartWidget {
                background-color: rgba(30, 41, 59, 0.4);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.1);
                padding: 10px;
            }
        """)

        # إعداد التخطيط
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # عنوان الرسم البياني
        title_label = QLabel("📊 تحليل المبيعات (آخر 7 أيام)")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #f1f5f9;
            padding: 5px;
        """)
        layout.addWidget(title_label)

        # إعداد PyQtGraph - Quantum Theme
        pg.setConfigOption("background", "#020617")  # Deep Void Background
        pg.setConfigOption("foreground", "#cbd5e1")  # Slate Text
        pg.setConfigOptions(antialias=True)  # High Quality

        # إنشاء عنصر الرسم
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("")
        self.plot_widget.setLabel("left", "المبلغ (د.ج)", color="#38bdf8", **{"font-size": "11pt"})
        self.plot_widget.setLabel("bottom", "الأيام السابقة", color="#38bdf8", **{"font-size": "11pt"})
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)  # Faint grid
        self.plot_widget.setMinimumHeight(300)

        # تنسيق المحور Y (الأرقام)
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(color="#94a3b8", width=1))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(color="#94a3b8", width=1))

        layout.addWidget(self.plot_widget)

        # تهيئة بيانات فارغة
        self.update_chart([], [])

    def update_chart(self, days, amounts):
        """
        تحديث الرسم البياني ببيانات جديدة

        Args:
            days: قائمة الأيام
            amounts: قائمة المبالغ المالية
        """
        if not PYQTGRAPH_AVAILABLE:
            return

        self.plot_widget.clear()

        if not days or not amounts or len(days) == 0 or len(amounts) == 0:
            self.plot_widget.addItem(pg.TextItem("لا توجد بيانات للعرض", color="#94a3b8", anchor=(0.5, 0.5)))
            return

        # التأكد من أن الأطوال متساوية
        if len(days) != len(amounts):
            min_len = min(len(days), len(amounts))
            days = days[:min_len]
            amounts = amounts[:min_len]

        # تحويل إلى numpy arrays للسرعة
        try:
            import numpy as np

            days_array = np.array(days)
            amounts_array = np.array(amounts, dtype=float)
        except ImportError:
            days_array = days
            amounts_array = amounts

        # إنشاء الرسم البياني الشريطي (Bar Chart) - Neon Cyan Style
        bar_chart = pg.BarGraphItem(
            x=days_array,
            height=amounts_array,
            width=0.6,
            brush=pg.mkBrush("#00f3ff"),  # Neon Cyan Fill
            pen=pg.mkPen("#00f3ff", width=1),  # Neon Cyan Border
        )

        self.plot_widget.addItem(bar_chart)

        # إضافة خط الاتجاه (Trend Line) - اختياري
        if len(amounts_array) > 1:
            try:
                import numpy as np

                # حساب خط الاتجاه البسيط
                z = np.polyfit(days_array, amounts_array, 1)
                p = np.poly1d(z)
                trend_line = self.plot_widget.plot(  # noqa: F841
                    days_array,
                    p(days_array),
                    pen=pg.mkPen("#10b981", width=2, style=Qt.DashLine),
                    name="خط الاتجاه",
                )
            except Exception as e:
                logger.debug(f"فشل رسم خط الاتجاه: {e}")

        # تحديث نطاق المحاور
        if len(days_array) > 0:
            self.plot_widget.setXRange(min(days_array) - 0.5, max(days_array) + 0.5, padding=0.1)

        if len(amounts_array) > 0:
            max_amount = max(amounts_array)
            self.plot_widget.setYRange(0, max_amount * 1.1 if max_amount > 0 else 100, padding=0.1)

        logger.debug(f"تم تحديث الرسم البياني: {len(days)} أيام، {len(amounts)} مبالغ")

    def clear_chart(self):
        """مسح الرسم البياني"""
        if PYQTGRAPH_AVAILABLE:
            self.plot_widget.clear()
