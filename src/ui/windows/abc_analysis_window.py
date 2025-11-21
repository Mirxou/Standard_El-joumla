"""
ABC Analysis Window - نافذة تحليل ABC
تحليل وتصنيف المنتجات حسب القيمة
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QComboBox, QSpinBox, QProgressBar, QMessageBox, QGridLayout,
    QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from typing import List, Dict
from decimal import Decimal

from ...core.database_manager import DatabaseManager
from ...services.inventory_optimization_service import InventoryOptimizationService
from ...models.inventory_optimization import ABCAnalysisResult, ABCCategory


class ABCAnalysisWorker(QThread):
    """عامل تحليل ABC في خلفية"""
    analysis_completed = Signal(list, dict)
    progress_updated = Signal(int, str)
    
    def __init__(self, service: InventoryOptimizationService, period_months: int):
        super().__init__()
        self.service = service
        self.period_months = period_months
    
    def run(self):
        """تشغيل التحليل"""
        try:
            self.progress_updated.emit(25, "جاري جمع بيانات المبيعات...")
            results = self.service.perform_abc_analysis(self.period_months)
            
            self.progress_updated.emit(75, "جاري حساب الملخص...")
            summary = self.service.get_abc_summary(results)
            
            self.progress_updated.emit(100, "اكتمل التحليل")
            self.analysis_completed.emit(results, summary)
            
        except Exception as e:
            self.progress_updated.emit(0, f"خطأ: {str(e)}")


class ABCAnalysisWindow(QWidget):
    """نافذة تحليل ABC"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.service = InventoryOptimizationService(db_manager)
        self.current_results: List[ABCAnalysisResult] = []
        self.current_summary: Dict = {}
        
        self.setWindowTitle("تحليل ABC للمنتجات")
        self.setMinimumSize(1200, 700)
        
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("تحليل ABC للمنتجات")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # أدوات التحكم
        controls_group = self.create_controls_section()
        layout.addWidget(controls_group)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("جاهز")
        layout.addWidget(self.status_label)
        
        # علامات التبويب
        self.tabs = QTabWidget()
        
        # تبويب النتائج
        results_tab = self.create_results_tab()
        self.tabs.addTab(results_tab, "📊 النتائج التفصيلية")
        
        # تبويب الملخص
        summary_tab = self.create_summary_tab()
        self.tabs.addTab(summary_tab, "📈 الملخص والرسوم البيانية")
        
        # تبويب التوصيات
        recommendations_tab = self.create_recommendations_tab()
        self.tabs.addTab(recommendations_tab, "💡 التوصيات")
        
        layout.addWidget(self.tabs)
    
    def create_controls_section(self) -> QGroupBox:
        """قسم أدوات التحكم"""
        group = QGroupBox("إعدادات التحليل")
        layout = QHBoxLayout()
        
        # فترة التحليل
        layout.addWidget(QLabel("فترة التحليل:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("آخر 3 أشهر", 3)
        self.period_combo.addItem("آخر 6 أشهر", 6)
        self.period_combo.addItem("آخر سنة", 12)
        self.period_combo.addItem("آخر سنتين", 24)
        self.period_combo.setCurrentIndex(2)  # 12 شهر افتراضي
        layout.addWidget(self.period_combo)
        
        layout.addStretch()
        
        # زر تشغيل التحليل
        self.analyze_btn = QPushButton("🔍 تشغيل التحليل")
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.analyze_btn.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        layout.addWidget(self.analyze_btn)
        
        # زر التصدير
        self.export_btn = QPushButton("📥 تصدير النتائج")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
    
    def create_results_tab(self) -> QWidget:
        """تبويب النتائج التفصيلية"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # فلاتر
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("تصفية حسب الفئة:"))
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("الكل", None)
        self.category_filter.addItem("فئة A فقط", "A")
        self.category_filter.addItem("فئة B فقط", "B")
        self.category_filter.addItem("فئة C فقط", "C")
        self.category_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # جدول النتائج
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(12)
        self.results_table.setHorizontalHeaderLabels([
            "الترتيب", "كود المنتج", "اسم المنتج",
            "المبيعات السنوية (كمية)", "المبيعات السنوية (قيمة)",
            "السعر المتوسط", "المخزون الحالي", "قيمة المخزون",
            "الفئة", "نسبة من الإجمالي", "النسبة التراكمية", "الأولوية"
        ])
        
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.results_table)
        
        return widget
    
    def create_summary_tab(self) -> QWidget:
        """تبويب الملخص والرسوم البيانية"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # ملخص إحصائي
        stats_group = QGroupBox("الملخص الإحصائي")
        stats_layout = QGridLayout()
        
        self.stats_labels = {}
        stats = [
            ("total_products", "إجمالي المنتجات"),
            ("category_a_count", "عدد منتجات فئة A"),
            ("category_b_count", "عدد منتجات فئة B"),
            ("category_c_count", "عدد منتجات فئة C"),
            ("category_a_value", "قيمة فئة A"),
            ("category_b_value", "قيمة فئة B"),
            ("category_c_value", "قيمة فئة C"),
            ("total_value", "إجمالي القيمة")
        ]
        
        for i, (key, label) in enumerate(stats):
            row = i // 2
            col = (i % 2) * 2
            
            stats_layout.addWidget(QLabel(f"{label}:"), row, col)
            value_label = QLabel("0")
            value_label.setFont(QFont("Arial", 11, QFont.Bold))
            self.stats_labels[key] = value_label
            stats_layout.addWidget(value_label, row, col + 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # الرسوم البيانية
        charts_layout = QHBoxLayout()
        
        # رسم دائري للتوزيع
        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QChartView.Antialiasing)
        charts_layout.addWidget(self.pie_chart_view)
        
        # رسم أعمدة للقيمة
        self.bar_chart_view = QChartView()
        self.bar_chart_view.setRenderHint(QChartView.Antialiasing)
        charts_layout.addWidget(self.bar_chart_view)
        
        layout.addLayout(charts_layout)
        
        return widget
    
    def create_recommendations_tab(self) -> QWidget:
        """تبويب التوصيات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # جدول التوصيات
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(5)
        self.recommendations_table.setHorizontalHeaderLabels([
            "المنتج", "الفئة", "الأولوية", "التوصيات", "الإجراءات المقترحة"
        ])
        
        self.recommendations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.recommendations_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.recommendations_table)
        
        return widget
    
    def run_analysis(self):
        """تشغيل تحليل ABC"""
        period_months = self.period_combo.currentData()
        
        # تعطيل الزر وإظهار شريط التقدم
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # تشغيل العامل في الخلفية
        self.worker = ABCAnalysisWorker(self.service, period_months)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.analysis_completed.connect(self.display_results)
        self.worker.start()
    
    def update_progress(self, value: int, message: str):
        """تحديث شريط التقدم"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def display_results(self, results: List[ABCAnalysisResult], summary: Dict):
        """عرض النتائج"""
        self.current_results = results
        self.current_summary = summary
        
        # إخفاء شريط التقدم وتفعيل الأزرار
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # ملء الجداول
        self.populate_results_table(results)
        self.update_summary_tab(summary)
        self.populate_recommendations(results)
        
        # رسم البيانات
        self.draw_charts(summary)
        
        self.status_label.setText(f"تم تحليل {len(results)} منتج بنجاح")
    
    def populate_results_table(self, results: List[ABCAnalysisResult]):
        """ملء جدول النتائج"""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # الترتيب
            self.results_table.setItem(row, 0, QTableWidgetItem(str(result.rank)))
            
            # معلومات المنتج
            self.results_table.setItem(row, 1, QTableWidgetItem(result.product_code))
            self.results_table.setItem(row, 2, QTableWidgetItem(result.product_name))
            
            # المبيعات
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{result.annual_sales_quantity:,.0f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{result.annual_sales_value:,.2f}"))
            self.results_table.setItem(row, 5, QTableWidgetItem(f"{result.average_unit_price:,.2f}"))
            
            # المخزون
            self.results_table.setItem(row, 6, QTableWidgetItem(f"{result.current_stock:,.0f}"))
            self.results_table.setItem(row, 7, QTableWidgetItem(f"{result.stock_value:,.2f}"))
            
            # الفئة مع اللون
            category_item = QTableWidgetItem(result.category_label)
            category_color = self.get_category_color(result.abc_category)
            category_item.setBackground(category_color)
            self.results_table.setItem(row, 8, category_item)
            
            # النسب
            self.results_table.setItem(row, 9, QTableWidgetItem(f"{result.percentage_of_total_value:.2f}%"))
            self.results_table.setItem(row, 10, QTableWidgetItem(f"{result.cumulative_percentage:.2f}%"))
            
            # الأولوية
            priority_item = QTableWidgetItem(str(result.priority_level))
            if result.priority_level >= 4:
                priority_item.setBackground(QColor(255, 200, 200))
            self.results_table.setItem(row, 11, priority_item)
    
    def update_summary_tab(self, summary: Dict):
        """تحديث تبويب الملخص"""
        self.stats_labels['total_products'].setText(str(summary.get('total_products', 0)))
        self.stats_labels['category_a_count'].setText(str(summary.get('category_a_count', 0)))
        self.stats_labels['category_b_count'].setText(str(summary.get('category_b_count', 0)))
        self.stats_labels['category_c_count'].setText(str(summary.get('category_c_count', 0)))
        
        total_value = summary.get('total_value', Decimal('0'))
        self.stats_labels['category_a_value'].setText(f"{summary.get('category_a_value', 0):,.2f} ريال")
        self.stats_labels['category_b_value'].setText(f"{summary.get('category_b_value', 0):,.2f} ريال")
        self.stats_labels['category_c_value'].setText(f"{summary.get('category_c_value', 0):,.2f} ريال")
        self.stats_labels['total_value'].setText(f"{total_value:,.2f} ريال")
    
    def populate_recommendations(self, results: List[ABCAnalysisResult]):
        """ملء جدول التوصيات"""
        # تصفية المنتجات التي تحتاج انتباه
        important_products = [r for r in results if r.needs_attention or r.priority_level >= 4]
        
        self.recommendations_table.setRowCount(len(important_products))
        
        for row, result in enumerate(important_products):
            self.recommendations_table.setItem(row, 0, QTableWidgetItem(result.product_name))
            self.recommendations_table.setItem(row, 1, QTableWidgetItem(result.category_label))
            self.recommendations_table.setItem(row, 2, QTableWidgetItem(str(result.priority_level)))
            
            # التوصيات
            recommendations_text = "\n".join(result.recommendations)
            self.recommendations_table.setItem(row, 3, QTableWidgetItem(recommendations_text))
            
            # الإجراءات
            actions = self.get_suggested_actions(result)
            self.recommendations_table.setItem(row, 4, QTableWidgetItem(actions))
    
    def draw_charts(self, summary: Dict):
        """رسم البيانات"""
        # رسم دائري للعدد
        pie_series = QPieSeries()
        pie_series.append(f"فئة A ({summary.get('category_a_count', 0)})", 
                         summary.get('category_a_count', 0))
        pie_series.append(f"فئة B ({summary.get('category_b_count', 0)})", 
                         summary.get('category_b_count', 0))
        pie_series.append(f"فئة C ({summary.get('category_c_count', 0)})", 
                         summary.get('category_c_count', 0))
        
        # ألوان الشرائح
        pie_series.slices()[0].setColor(QColor(255, 100, 100))  # A - أحمر
        pie_series.slices()[1].setColor(QColor(255, 200, 100))  # B - برتقالي
        pie_series.slices()[2].setColor(QColor(150, 200, 255))  # C - أزرق
        
        for slice in pie_series.slices():
            slice.setLabelVisible(True)
        
        pie_chart = QChart()
        pie_chart.addSeries(pie_series)
        pie_chart.setTitle("توزيع المنتجات حسب الفئة")
        pie_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        self.pie_chart_view.setChart(pie_chart)
        
        # رسم أعمدة للقيمة
        bar_set = QBarSet("القيمة (ريال)")
        bar_set.append(float(summary.get('category_a_value', 0)))
        bar_set.append(float(summary.get('category_b_value', 0)))
        bar_set.append(float(summary.get('category_c_value', 0)))
        
        bar_series = QBarSeries()
        bar_series.append(bar_set)
        
        bar_chart = QChart()
        bar_chart.addSeries(bar_series)
        bar_chart.setTitle("القيمة الإجمالية حسب الفئة")
        bar_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        categories = ["فئة A", "فئة B", "فئة C"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        bar_chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        bar_chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        self.bar_chart_view.setChart(bar_chart)
    
    def apply_filters(self):
        """تطبيق الفلاتر"""
        category = self.category_filter.currentData()
        
        for row in range(self.results_table.rowCount()):
            if category is None:
                self.results_table.setRowHidden(row, False)
            else:
                # الحصول على فئة المنتج من العمود 8
                item = self.results_table.item(row, 8)
                if item:
                    show = category in item.text()
                    self.results_table.setRowHidden(row, not show)
    
    def export_results(self):
        """تصدير النتائج"""
        QMessageBox.information(self, "تصدير", "سيتم إضافة وظيفة التصدير قريباً")
    
    def get_category_color(self, category: str) -> QColor:
        """الحصول على لون الفئة"""
        colors = {
            ABCCategory.A.value: QColor(255, 200, 200),  # أحمر فاتح
            ABCCategory.B.value: QColor(255, 240, 200),  # برتقالي فاتح
            ABCCategory.C.value: QColor(200, 230, 255)   # أزرق فاتح
        }
        return colors.get(category, QColor(255, 255, 255))
    
    def get_suggested_actions(self, result: ABCAnalysisResult) -> str:
        """الحصول على الإجراءات المقترحة"""
        actions = []
        
        if result.abc_category == ABCCategory.A.value:
            actions.append("✓ ضمان التوفر الدائم")
            actions.append("✓ مراجعة الأسعار شهرياً")
            if result.days_since_last_sale and result.days_since_last_sale > 30:
                actions.append("⚠️ مراجعة استراتيجية التسويق")
        elif result.abc_category == ABCCategory.B.value:
            actions.append("✓ مراجعة ربع سنوية")
            actions.append("✓ تحسين مستوى المخزون")
        else:
            if result.stock_value > 5000:
                actions.append("💡 تقليل المخزون")
                actions.append("💡 عروض خاصة للتصريف")
        
        return "\n".join(actions)
