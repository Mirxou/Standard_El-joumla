#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
لوحة تحكم المدفوعات - Payment Dashboard
نافذة متقدمة لعرض تحليلات وإحصائيات المدفوعات مع رسوم بيانية تفاعلية
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QComboBox, QDateEdit,
    QGroupBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QTimer, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QLineSeries, QValueAxis, QBarCategoryAxis
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.payment_service import PaymentService


class KPIWidget(QFrame):
    """عنصر واجهة لعرض مؤشر أداء رئيسي"""
    
    def __init__(self, title: str, value: str, change: str = "", color: str = "#3498db"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # العنوان
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #7f8c8d; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # القيمة
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # التغيير
        if change:
            change_label = QLabel(change)
            change_color = "#27ae60" if change.startswith("+") else "#e74c3c"
            change_label.setStyleSheet(f"font-size: 10px; color: {change_color};")
            change_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(change_label)
        
        self.setMinimumHeight(100)
        self.setMaximumHeight(120)


class ChartWidget(QFrame):
    """عنصر واجهة للرسوم البيانية"""
    
    def __init__(self, title: str):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # العنوان
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # منطقة الرسم البياني
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view)
        
        self.setMinimumHeight(300)


class DataUpdateWorker(QThread):
    """عامل تحديث البيانات في الخلفية"""
    
    data_updated = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, payment_service: PaymentService):
        super().__init__()
        self.payment_service = payment_service
        self.running = True
    
    def run(self):
        """تشغيل عملية تحديث البيانات"""
        try:
            from datetime import date
            
            # جمع جميع البيانات المطلوبة
            data = {}
            
            # تحديد الفترات الزمنية
            end_date = date.today()
            start_date = date(end_date.year, end_date.month, 1)  # أول الشهر
            
            # فترة المقارنة
            prev_end = start_date - timedelta(days=1)
            prev_start = date(prev_end.year, prev_end.month, 1)
            
            # مؤشرات الأداء الرئيسية (مع معالجة الأخطاء)
            try:
                data['kpis'] = self.payment_service.get_payment_performance_kpis(start_date, end_date)
            except Exception as e:
                data['kpis'] = {}
            
            # تحليل الاتجاهات (مع معالجة الأخطاء)
            try:
                data['trends'] = self.payment_service.get_payment_trends_analysis(start_date, end_date, 'monthly')
            except Exception as e:
                data['trends'] = {}
            
            # التوقعات (مع معالجة الأخطاء)
            try:
                data['forecast'] = self.payment_service.get_payment_forecast(12, 3)
            except Exception as e:
                data['forecast'] = {}
            
            # مقارنة الفترات (مع معالجة الأخطاء)
            try:
                data['comparison'] = self.payment_service.get_period_comparison_analysis(
                    prev_start, prev_end, start_date, end_date
                )
            except Exception as e:
                data['comparison'] = {}
            
            # تقرير الأعمار (مع معالجة الأخطاء)
            try:
                data['aging'] = self.payment_service.get_aging_report('receivables')
            except Exception as e:
                data['aging'] = {}
            
            # تدفق نقدي (مع معالجة الأخطاء)
            try:
                data['cash_flow'] = self.payment_service.get_cash_flow_report(start_date, end_date)
            except Exception as e:
                data['cash_flow'] = {}
            
            self.data_updated.emit(data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """إيقاف العامل"""
        self.running = False
        self.quit()
        self.wait()


class PaymentDashboard(QMainWindow):
    """لوحة تحكم المدفوعات الرئيسية"""
    
    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "payment_dashboard"
    window_singleton = True
    window_title = "لوحة تحكم المدفوعات"
    
    def __init__(self, db_manager, parent=None, payment_service: PaymentService = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.payment_service = payment_service or PaymentService(db_manager)
        
        # إعداد النافذة
        self.setWindowTitle("لوحة تحكم المدفوعات - Payment Dashboard")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # متغيرات البيانات
        self.dashboard_data = {}
        
        # إعداد الواجهة
        self.setup_ui()
        self.setup_styles()
        
        # إعداد عامل تحديث البيانات
        self.data_worker = DataUpdateWorker(self.payment_service)
        self.data_worker.data_updated.connect(self.update_dashboard_data)
        self.data_worker.error_occurred.connect(self.handle_error)
        
        # تحديث البيانات كل 5 دقائق
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(300000)  # 5 دقائق
        
        # تحديث أولي
        self.refresh_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # شريط التحكم العلوي
        self.create_control_bar(main_layout)
        
        # منطقة المحتوى الرئيسية
        content_splitter = QSplitter(Qt.Vertical)
        
        # الجزء العلوي - مؤشرات الأداء الرئيسية
        kpi_widget = self.create_kpi_section()
        content_splitter.addWidget(kpi_widget)
        
        # الجزء الأوسط - الرسوم البيانية
        charts_widget = self.create_charts_section()
        content_splitter.addWidget(charts_widget)
        
        # الجزء السفلي - الجداول التفصيلية
        tables_widget = self.create_tables_section()
        content_splitter.addWidget(tables_widget)
        
        # تعيين النسب
        content_splitter.setSizes([200, 400, 300])
        
        main_layout.addWidget(content_splitter)
    
    def create_control_bar(self, parent_layout):
        """إنشاء شريط التحكم العلوي"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setMaximumHeight(80)
        
        layout = QHBoxLayout(control_frame)
        
        # عنوان اللوحة
        title_label = QLabel("📊 لوحة تحكم المدفوعات")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # فلاتر التاريخ
        date_label = QLabel("الفترة:")
        layout.addWidget(date_label)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "آخر 7 أيام", "آخر 30 يوم", "آخر 3 أشهر", 
            "آخر 6 أشهر", "آخر سنة", "مخصص"
        ])
        self.period_combo.setCurrentIndex(1)  # آخر 30 يوم
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        layout.addWidget(self.period_combo)
        
        # تواريخ مخصصة
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setEnabled(False)
        layout.addWidget(self.start_date)
        
        layout.addWidget(QLabel("إلى"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setEnabled(False)
        layout.addWidget(self.end_date)
        
        # أزرار التحكم
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 تصدير")
        export_btn.clicked.connect(self.export_dashboard)
        layout.addWidget(export_btn)
        
        parent_layout.addWidget(control_frame)
    
    def create_kpi_section(self) -> QWidget:
        """إنشاء قسم مؤشرات الأداء الرئيسية"""
        kpi_widget = QWidget()
        kpi_layout = QGridLayout(kpi_widget)
        kpi_layout.setSpacing(10)
        
        # إنشاء مؤشرات الأداء
        self.kpi_widgets = {}
        
        kpi_configs = [
            ("إجمالي المدفوعات", "0 ر.س", "", "#3498db"),
            ("عدد المعاملات", "0", "", "#27ae60"),
            ("متوسط قيمة المعاملة", "0 ر.س", "", "#f39c12"),
            ("معدل التحصيل", "0%", "", "#9b59b6"),
            ("المبالغ المستحقة", "0 ر.س", "", "#e74c3c"),
            ("التدفق النقدي", "0 ر.س", "", "#1abc9c")
        ]
        
        for i, (title, value, change, color) in enumerate(kpi_configs):
            kpi = KPIWidget(title, value, change, color)
            self.kpi_widgets[title] = kpi
            row, col = divmod(i, 3)
            kpi_layout.addWidget(kpi, row, col)
        
        return kpi_widget
    
    def create_charts_section(self) -> QWidget:
        """إنشاء قسم الرسوم البيانية"""
        charts_widget = QTabWidget()
        
        # تبويب الاتجاهات
        trends_tab = QWidget()
        trends_layout = QHBoxLayout(trends_tab)
        
        self.trends_chart = ChartWidget("اتجاهات المدفوعات الشهرية")
        trends_layout.addWidget(self.trends_chart)
        
        self.payment_types_chart = ChartWidget("توزيع أنواع المدفوعات")
        trends_layout.addWidget(self.payment_types_chart)
        
        charts_widget.addTab(trends_tab, "📈 الاتجاهات")
        
        # تبويب التوقعات
        forecast_tab = QWidget()
        forecast_layout = QHBoxLayout(forecast_tab)
        
        self.forecast_chart = ChartWidget("توقعات المدفوعات")
        forecast_layout.addWidget(self.forecast_chart)
        
        self.cash_flow_chart = ChartWidget("التدفق النقدي")
        forecast_layout.addWidget(self.cash_flow_chart)
        
        charts_widget.addTab(forecast_tab, "🔮 التوقعات")
        
        # تبويب المقارنات
        comparison_tab = QWidget()
        comparison_layout = QHBoxLayout(comparison_tab)
        
        self.comparison_chart = ChartWidget("مقارنة الفترات")
        comparison_layout.addWidget(self.comparison_chart)
        
        self.aging_chart = ChartWidget("أعمار الذمم")
        comparison_layout.addWidget(self.aging_chart)
        
        charts_widget.addTab(comparison_tab, "⚖️ المقارنات")
        
        return charts_widget
    
    def create_tables_section(self) -> QWidget:
        """إنشاء قسم الجداول التفصيلية"""
        tables_widget = QTabWidget()
        
        # جدول أحدث المعاملات
        self.recent_transactions_table = QTableWidget()
        self.setup_transactions_table()
        tables_widget.addTab(self.recent_transactions_table, "💳 أحدث المعاملات")
        
        # جدول العملاء الأكثر نشاطاً
        self.top_customers_table = QTableWidget()
        self.setup_customers_table()
        tables_widget.addTab(self.top_customers_table, "👥 العملاء الأكثر نشاطاً")
        
        # جدول تحليل طرق الدفع
        self.payment_methods_table = QTableWidget()
        self.setup_payment_methods_table()
        tables_widget.addTab(self.payment_methods_table, "💰 طرق الدفع")
        
        return tables_widget
    
    def setup_transactions_table(self):
        """إعداد جدول المعاملات"""
        headers = ["التاريخ", "النوع", "المبلغ", "العميل", "طريقة الدفع", "الحالة"]
        self.recent_transactions_table.setColumnCount(len(headers))
        self.recent_transactions_table.setHorizontalHeaderLabels(headers)
        
        # تعيين عرض الأعمدة
        header = self.recent_transactions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
    
    def setup_customers_table(self):
        """إعداد جدول العملاء"""
        headers = ["العميل", "عدد المعاملات", "إجمالي المبلغ", "متوسط المعاملة", "آخر معاملة"]
        self.top_customers_table.setColumnCount(len(headers))
        self.top_customers_table.setHorizontalHeaderLabels(headers)
        
        header = self.top_customers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
    
    def setup_payment_methods_table(self):
        """إعداد جدول طرق الدفع"""
        headers = ["طريقة الدفع", "عدد المعاملات", "النسبة", "إجمالي المبلغ", "متوسط المبلغ"]
        self.payment_methods_table.setColumnCount(len(headers))
        self.payment_methods_table.setHorizontalHeaderLabels(headers)
        
        header = self.payment_methods_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
    
    def setup_styles(self):
        """إعداد الأنماط"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)
    
    def on_period_changed(self, period_text: str):
        """معالجة تغيير الفترة"""
        if period_text == "مخصص":
            self.start_date.setEnabled(True)
            self.end_date.setEnabled(True)
        else:
            self.start_date.setEnabled(False)
            self.end_date.setEnabled(False)
            
            # تحديث التواريخ حسب الفترة المختارة
            end_date = QDate.currentDate()
            if period_text == "آخر 7 أيام":
                start_date = end_date.addDays(-7)
            elif period_text == "آخر 30 يوم":
                start_date = end_date.addDays(-30)
            elif period_text == "آخر 3 أشهر":
                start_date = end_date.addMonths(-3)
            elif period_text == "آخر 6 أشهر":
                start_date = end_date.addMonths(-6)
            elif period_text == "آخر سنة":
                start_date = end_date.addYears(-1)
            else:
                start_date = end_date.addDays(-30)
            
            self.start_date.setDate(start_date)
            self.end_date.setDate(end_date)
        
        # تحديث البيانات
        self.refresh_data()
    
    def refresh_data(self):
        """تحديث بيانات اللوحة"""
        if not self.data_worker.isRunning():
            self.data_worker.start()
    
    def update_dashboard_data(self, data: Dict[str, Any]):
        """تحديث بيانات اللوحة"""
        self.dashboard_data = data
        
        # تحديث مؤشرات الأداء
        self.update_kpis(data.get('kpis', {}))
        
        # تحديث الرسوم البيانية
        self.update_charts(data)
        
        # تحديث الجداول
        self.update_tables(data)
    
    def update_kpis(self, kpis: Dict[str, Any]):
        """تحديث مؤشرات الأداء الرئيسية"""
        try:
            # تحديث القيم في مؤشرات الأداء
            if "إجمالي المدفوعات" in self.kpi_widgets and 'total_amount' in kpis:
                total_amount = f"{kpis['total_amount']:,.0f} ر.س"
                # تحديث النص في المؤشر
                
            if "عدد المعاملات" in self.kpi_widgets and 'total_transactions' in kpis:
                total_transactions = f"{kpis['total_transactions']:,}"
                
            # يمكن إضافة المزيد من التحديثات هنا
            
        except Exception as e:
            print(f"خطأ في تحديث مؤشرات الأداء: {e}")
    
    def update_charts(self, data: Dict[str, Any]):
        """تحديث الرسوم البيانية"""
        try:
            # تحديث رسم الاتجاهات
            if 'trends' in data:
                self.update_trends_chart(data['trends'])
            
            # تحديث رسم التوقعات
            if 'forecast' in data:
                self.update_forecast_chart(data['forecast'])
            
            # تحديث رسم المقارنات
            if 'comparison' in data:
                self.update_comparison_chart(data['comparison'])
                
        except Exception as e:
            print(f"خطأ في تحديث الرسوم البيانية: {e}")
    
    def update_trends_chart(self, trends_data: Dict[str, Any]):
        """تحديث رسم الاتجاهات"""
        try:
            chart = QChart()
            chart.setTitle("اتجاهات المدفوعات")
            
            # إنشاء سلسلة خطية
            series = QLineSeries()
            series.setName("المدفوعات")
            
            # إضافة البيانات (مثال)
            if 'periods' in trends_data:
                for i, period in enumerate(trends_data['periods'][:12]):  # آخر 12 فترة
                    series.append(i, period.get('total_amount', 0))
            
            chart.addSeries(series)
            chart.createDefaultAxes()
            
            self.trends_chart.chart_view.setChart(chart)
            
        except Exception as e:
            print(f"خطأ في تحديث رسم الاتجاهات: {e}")
    
    def update_forecast_chart(self, forecast_data: Dict[str, Any]):
        """تحديث رسم التوقعات"""
        try:
            chart = QChart()
            chart.setTitle("توقعات المدفوعات")
            
            # سلسلة البيانات التاريخية
            historical_series = QLineSeries()
            historical_series.setName("البيانات التاريخية")
            
            # سلسلة التوقعات
            forecast_series = QLineSeries()
            forecast_series.setName("التوقعات")
            
            # إضافة البيانات
            if 'forecasts' in forecast_data:
                for i, forecast in enumerate(forecast_data['forecasts']):
                    forecast_series.append(i, forecast.get('predicted_amount', 0))
            
            chart.addSeries(historical_series)
            chart.addSeries(forecast_series)
            chart.createDefaultAxes()
            
            self.forecast_chart.chart_view.setChart(chart)
            
        except Exception as e:
            print(f"خطأ في تحديث رسم التوقعات: {e}")
    
    def update_comparison_chart(self, comparison_data: Dict[str, Any]):
        """تحديث رسم المقارنات"""
        try:
            chart = QChart()
            chart.setTitle("مقارنة الفترات")
            
            # إنشاء مجموعة أعمدة
            series = QBarSeries()
            
            # مجموعة الفترة السابقة
            prev_set = QBarSet("الفترة السابقة")
            prev_set.append(comparison_data.get('previous_period', {}).get('total_amount', 0))
            
            # مجموعة الفترة الحالية
            current_set = QBarSet("الفترة الحالية")
            current_set.append(comparison_data.get('current_period', {}).get('total_amount', 0))
            
            series.append(prev_set)
            series.append(current_set)
            
            chart.addSeries(series)
            chart.createDefaultAxes()
            
            self.comparison_chart.chart_view.setChart(chart)
            
        except Exception as e:
            print(f"خطأ في تحديث رسم المقارنات: {e}")
    
    def update_tables(self, data: Dict[str, Any]):
        """تحديث الجداول"""
        try:
            # تحديث جدول المعاملات الأخيرة
            # يمكن إضافة المنطق هنا لتحديث الجداول
            pass
            
        except Exception as e:
            print(f"خطأ في تحديث الجداول: {e}")
    
    def export_dashboard(self):
        """تصدير بيانات اللوحة"""
        try:
            # يمكن إضافة منطق التصدير هنا
            QMessageBox.information(self, "تصدير", "سيتم إضافة وظيفة التصدير قريباً")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير البيانات: {str(e)}")
    
    def handle_error(self, error_message: str):
        """معالجة الأخطاء"""
        QMessageBox.warning(self, "تحذير", f"خطأ في تحديث البيانات: {error_message}")
    
    def closeEvent(self, event):
        """حدث إغلاق النافذة"""
        # إيقاف العامل
        if hasattr(self, 'data_worker'):
            self.data_worker.stop()
        
        # إيقاف المؤقت
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        event.accept()