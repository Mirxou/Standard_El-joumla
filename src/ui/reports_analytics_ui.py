import logging
import numpy as np

"""
واجهة المستخدم للتقارير والتحليلات - Phase 8
Reports & Analytics UI for Unified Commerce 2030 ERP
"""

from datetime import datetime

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.database_manager import DatabaseManager
from src.services.advanced_analytics_service import AdvancedAnalyticsService
from src.services.advanced_reporting_service import AdvancedReportingService
from src.services.business_intelligence_service import BusinessIntelligenceService
from src.utils.logger import setup_logger


class ReportsAnalyticsUI(QWidget):
    """
    واجهة المستخدم للتقارير والتحليلات
    توفر واجهة شاملة لعرض التقارير والتحليلات التفاعلية
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager
        self.logger = setup_logger(__name__)

        # تهيئة الخدمات
        self.reporting_service = AdvancedReportingService(db_manager)
        self.bi_service = BusinessIntelligenceService(db_manager)
        self.analytics_service = AdvancedAnalyticsService(db_manager)

        # إعداد الواجهة
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("التقارير والتحليلات المتقدمة")
        self.setMinimumSize(1400, 900)

        # تخطيط رئيسي
        main_layout = QHBoxLayout(self)

        # لوحة التنقل الجانبية
        self.setup_navigation_panel()
        main_layout.addWidget(self.navigation_panel, 1)

        # منطقة المحتوى الرئيسية
        self.setup_main_content()
        main_layout.addWidget(self.main_content, 4)

    def setup_navigation_panel(self):
        """إعداد لوحة التنقل الجانبية"""
        self.navigation_panel = QWidget()
        self.navigation_panel.setMaximumWidth(300)
        nav_layout = QVBoxLayout(self.navigation_panel)

        # عنوان اللوحة
        title_label = QLabel("التقارير والتحليلات")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        nav_layout.addWidget(title_label)

        # شجرة التنقل
        self.navigation_tree = QTreeWidget()
        self.navigation_tree.setHeaderHidden(True)
        self.navigation_tree.setMaximumHeight(600)

        # إضافة عناصر الشجرة
        self.setup_navigation_tree()
        nav_layout.addWidget(self.navigation_tree)

        # أزرار الإجراءات
        self.setup_action_buttons(nav_layout)

        nav_layout.addStretch()

    def setup_navigation_tree(self):
        """إعداد شجرة التنقل"""
        # التقارير المخصصة
        custom_reports = QTreeWidgetItem(self.navigation_tree)
        custom_reports.setText(0, "📊 التقارير المخصصة")
        custom_reports.setData(0, Qt.UserRole, "custom_reports")

        # تقارير المبيعات
        sales_reports = QTreeWidgetItem(custom_reports)
        sales_reports.setText(0, "مبيعات")
        sales_reports.setData(0, Qt.UserRole, "sales_reports")

        # تقارير المخزون
        inventory_reports = QTreeWidgetItem(custom_reports)
        inventory_reports.setText(0, "مخزون")
        inventory_reports.setData(0, Qt.UserRole, "inventory_reports")

        # تقارير العملاء
        customer_reports = QTreeWidgetItem(custom_reports)
        customer_reports.setText(0, "عملاء")
        customer_reports.setData(0, Qt.UserRole, "customer_reports")

        # اللوحات التفاعلية
        dashboards = QTreeWidgetItem(self.navigation_tree)
        dashboards.setText(0, "📈 اللوحات التفاعلية")
        dashboards.setData(0, Qt.UserRole, "dashboards")

        # لوحة المبيعات
        sales_dashboard = QTreeWidgetItem(dashboards)
        sales_dashboard.setText(0, "لوحة المبيعات")
        sales_dashboard.setData(0, Qt.UserRole, "sales_dashboard")

        # لوحة المخزون
        inventory_dashboard = QTreeWidgetItem(dashboards)
        inventory_dashboard.setText(0, "لوحة المخزون")
        inventory_dashboard.setData(0, Qt.UserRole, "inventory_dashboard")

        # لوحة الأداء المالي
        financial_dashboard = QTreeWidgetItem(dashboards)
        financial_dashboard.setText(0, "الأداء المالي")
        financial_dashboard.setData(0, Qt.UserRole, "financial_dashboard")

        # الذكاء التجاري
        business_intelligence = QTreeWidgetItem(self.navigation_tree)
        business_intelligence.setText(0, "🧠 الذكاء التجاري")
        business_intelligence.setData(0, Qt.UserRole, "business_intelligence")

        # الرؤى التجارية
        business_insights = QTreeWidgetItem(business_intelligence)
        business_insights.setText(0, "الرؤى التجارية")
        business_insights.setData(0, Qt.UserRole, "business_insights")

        # الرؤى التنبؤية
        predictive_insights = QTreeWidgetItem(business_intelligence)
        predictive_insights.setText(0, "الرؤى التنبؤية")
        predictive_insights.setData(0, Qt.UserRole, "predictive_insights")

        # تقسيم العملاء
        customer_segmentation = QTreeWidgetItem(business_intelligence)
        customer_segmentation.setText(0, "تقسيم العملاء")
        customer_segmentation.setData(0, Qt.UserRole, "customer_segmentation")

        # التحليلات المتقدمة
        advanced_analytics = QTreeWidgetItem(self.navigation_tree)
        advanced_analytics.setText(0, "🔬 التحليلات المتقدمة")
        advanced_analytics.setData(0, Qt.UserRole, "advanced_analytics")

        # النماذج التنبؤية
        predictive_models = QTreeWidgetItem(advanced_analytics)
        predictive_models.setText(0, "النماذج التنبؤية")
        predictive_models.setData(0, Qt.UserRole, "predictive_models")

        # الاختبارات الإحصائية
        statistical_tests = QTreeWidgetItem(advanced_analytics)
        statistical_tests.setText(0, "الاختبارات الإحصائية")
        statistical_tests.setData(0, Qt.UserRole, "statistical_tests")

        # تحليل السلاسل الزمنية
        time_series = QTreeWidgetItem(advanced_analytics)
        time_series.setText(0, "تحليل السلاسل الزمنية")
        time_series.setData(0, Qt.UserRole, "time_series")

        # توسيع العناصر الرئيسية
        self.navigation_tree.expandAll()

    def setup_action_buttons(self, layout):
        """إعداد أزرار الإجراءات"""
        # زر إنشاء تقرير جديد
        self.new_report_btn = QPushButton("📄 تقرير جديد")
        self.new_report_btn.setMinimumHeight(35)
        layout.addWidget(self.new_report_btn)

        # زر تصدير البيانات
        self.export_btn = QPushButton("📤 تصدير")
        self.export_btn.setMinimumHeight(35)
        layout.addWidget(self.export_btn)

        # زر التحديث
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setMinimumHeight(35)
        layout.addWidget(self.refresh_btn)

    def setup_main_content(self):
        """إعداد منطقة المحتوى الرئيسية"""
        self.main_content = QWidget()
        content_layout = QVBoxLayout(self.main_content)

        # شريط الأدوات العلوي
        self.setup_toolbar()
        content_layout.addWidget(self.toolbar_widget)

        # منطقة المحتوى الرئيسية مع التبويبات
        self.setup_content_tabs()
        content_layout.addWidget(self.content_tabs)

    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        self.toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(self.toolbar_widget)

        # اختيار الفترة الزمنية
        period_label = QLabel("الفترة:")
        toolbar_layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems(
            [
                "اليوم",
                "الأسبوع الحالي",
                "الشهر الحالي",
                "الربع الحالي",
                "السنة الحالية",
                "الأسبوع الماضي",
                "الشهر الماضي",
                "الربع الماضي",
                "السنة الماضية",
                "فترة مخصصة",
            ]
        )
        toolbar_layout.addWidget(self.period_combo)

        # تاريخ البداية
        start_label = QLabel("من:")
        toolbar_layout.addWidget(start_label)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        toolbar_layout.addWidget(self.start_date)

        # تاريخ النهاية
        end_label = QLabel("إلى:")
        toolbar_layout.addWidget(end_label)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        toolbar_layout.addWidget(self.end_date)

        # زر تطبيق الفلتر
        self.apply_filter_btn = QPushButton("تطبيق")
        self.apply_filter_btn.setMaximumWidth(80)
        toolbar_layout.addWidget(self.apply_filter_btn)

        toolbar_layout.addStretch()

        # مربع البحث
        search_label = QLabel("بحث:")
        toolbar_layout.addWidget(search_label)

        self.search_input = QTextEdit()
        self.search_input.setMaximumHeight(30)
        self.search_input.setMaximumWidth(200)
        self.search_input.setPlaceholderText("ابحث في التقارير...")
        toolbar_layout.addWidget(self.search_input)

    def setup_content_tabs(self):
        """إعداد تبويبات المحتوى"""
        self.content_tabs = QTabWidget()

        # تبويب التقارير
        self.setup_reports_tab()

        # تبويب اللوحات
        self.setup_dashboards_tab()

        # تبويب الذكاء التجاري
        self.setup_business_intelligence_tab()

        # تبويب التحليلات المتقدمة
        self.setup_advanced_analytics_tab()

    def setup_reports_tab(self):
        """إعداد تبويب التقارير"""
        reports_widget = QWidget()
        reports_layout = QVBoxLayout(reports_widget)

        # أدوات التقارير
        reports_toolbar = QHBoxLayout()

        # نوع التقرير
        report_type_label = QLabel("نوع التقرير:")
        reports_toolbar.addWidget(report_type_label)

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            [
                "تقرير المبيعات",
                "تقرير المخزون",
                "تقرير العملاء",
                "التقرير المالي",
                "تقرير الأداء",
                "تقرير مخصص",
            ]
        )
        reports_toolbar.addWidget(self.report_type_combo)

        # زر إنشاء التقرير
        self.generate_report_btn = QPushButton("إنشاء التقرير")
        self.generate_report_btn.setMaximumWidth(120)
        reports_toolbar.addWidget(self.generate_report_btn)

        reports_toolbar.addStretch()
        reports_layout.addLayout(reports_toolbar)

        # جدول التقارير
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(5)
        self.reports_table.setHorizontalHeaderLabels(["اسم التقرير", "النوع", "تاريخ الإنشاء", "الحالة", "الإجراءات"])
        self.reports_table.horizontalHeader().setStretchLastSection(True)
        reports_layout.addWidget(self.reports_table)

        self.content_tabs.addTab(reports_widget, "📊 التقارير")

    def setup_dashboards_tab(self):
        """إعداد تبويب اللوحات"""
        dashboards_widget = QWidget()
        dashboards_layout = QVBoxLayout(dashboards_widget)

        # اختيار اللوحة
        dashboard_selector = QHBoxLayout()

        dashboard_label = QLabel("اللوحة:")
        dashboard_selector.addWidget(dashboard_label)

        self.dashboard_combo = QComboBox()
        self.dashboard_combo.addItems(["لوحة المبيعات", "لوحة المخزون", "لوحة العملاء", "اللوحة المالية"])
        dashboard_selector.addWidget(self.dashboard_combo)

        # زر تحديث اللوحة
        self.refresh_dashboard_btn = QPushButton("تحديث اللوحة")
        dashboard_selector.addWidget(self.refresh_dashboard_btn)

        dashboard_selector.addStretch()
        dashboards_layout.addLayout(dashboard_selector)

        # منطقة الرسوم البيانية
        self.dashboard_charts_area = QWidget()
        self.dashboard_charts_layout = QVBoxLayout(self.dashboard_charts_area)

        # إنشاء رسوم بيانية أولية
        self.create_sample_charts()

        dashboards_layout.addWidget(self.dashboard_charts_area)

        self.content_tabs.addTab(dashboards_widget, "📈 اللوحات")

    def setup_business_intelligence_tab(self):
        """إعداد تبويب الذكاء التجاري"""
        bi_widget = QWidget()
        bi_layout = QVBoxLayout(bi_widget)

        # أدوات الذكاء التجاري
        bi_toolbar = QHBoxLayout()

        # نوع التحليل
        analysis_type_label = QLabel("نوع التحليل:")
        bi_toolbar.addWidget(analysis_type_label)

        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems(
            [
                "الرؤى التجارية",
                "الرؤى التنبؤية",
                "تقسيم العملاء",
                "كشف الشذوذ",
                "تحليل الاتجاهات",
            ]
        )
        bi_toolbar.addWidget(self.analysis_type_combo)

        # زر تشغيل التحليل
        self.run_analysis_btn = QPushButton("تشغيل التحليل")
        self.run_analysis_btn.setMaximumWidth(120)
        bi_toolbar.addWidget(self.run_analysis_btn)

        bi_toolbar.addStretch()
        bi_layout.addLayout(bi_toolbar)

        # منطقة عرض النتائج
        self.bi_results_area = QTextEdit()
        self.bi_results_area.setPlaceholderText("ستظهر هنا نتائج التحليلات الذكية...")
        bi_layout.addWidget(self.bi_results_area)

        # جدول الرؤى
        self.insights_table = QTableWidget()
        self.insights_table.setColumnCount(4)
        self.insights_table.setHorizontalHeaderLabels(["نوع الرؤية", "الوصف", "مستوى التأثير", "تاريخ التوليد"])
        self.insights_table.horizontalHeader().setStretchLastSection(True)
        bi_layout.addWidget(self.insights_table)

        self.content_tabs.addTab(bi_widget, "🧠 الذكاء التجاري")

    def setup_advanced_analytics_tab(self):
        """إعداد تبويب التحليلات المتقدمة"""
        analytics_widget = QWidget()
        analytics_layout = QVBoxLayout(analytics_widget)

        # أدوات التحليلات المتقدمة
        analytics_toolbar = QHBoxLayout()

        # نوع التحليل المتقدم
        advanced_type_label = QLabel("نوع التحليل:")
        analytics_toolbar.addWidget(advanced_type_label)

        self.advanced_type_combo = QComboBox()
        self.advanced_type_combo.addItems(
            [
                "النماذج التنبؤية",
                "الاختبارات الإحصائية",
                "تحليل السلاسل الزمنية",
                "تحسين المخزون",
                "كشف الشذوذ المتقدم",
            ]
        )
        analytics_toolbar.addWidget(self.advanced_type_combo)

        # زر تشغيل التحليل المتقدم
        self.run_advanced_btn = QPushButton("تشغيل التحليل المتقدم")
        self.run_advanced_btn.setMaximumWidth(150)
        analytics_toolbar.addWidget(self.run_advanced_btn)

        analytics_toolbar.addStretch()
        analytics_layout.addLayout(analytics_toolbar)

        # منطقة عرض النتائج المتقدمة
        self.advanced_results_area = QTextEdit()
        self.advanced_results_area.setPlaceholderText("ستظهر هنا نتائج التحليلات المتقدمة...")
        analytics_layout.addWidget(self.advanced_results_area)

        # جدول النتائج المتقدمة
        self.advanced_table = QTableWidget()
        self.advanced_table.setColumnCount(5)
        self.advanced_table.setHorizontalHeaderLabels(
            [
                "نوع التحليل",
                "المتغير المستهدف",
                "دقة النموذج",
                "تاريخ التشغيل",
                "الحالة",
            ]
        )
        self.advanced_table.horizontalHeader().setStretchLastSection(True)
        analytics_layout.addWidget(self.advanced_table)

        self.content_tabs.addTab(analytics_widget, "🔬 التحليلات المتقدمة")

    def setup_connections(self):
        """إعداد الاتصالات"""
        # شجرة التنقل
        self.navigation_tree.itemClicked.connect(self.on_navigation_item_clicked)

        # أزرار الإجراءات
        self.new_report_btn.clicked.connect(self.create_new_report)
        self.export_btn.clicked.connect(self.export_data)
        self.refresh_btn.clicked.connect(self.refresh_all)

        # شريط الأدوات
        self.apply_filter_btn.clicked.connect(self.apply_date_filter)

        # تبويب التقارير
        self.generate_report_btn.clicked.connect(self.generate_selected_report)

        # تبويب اللوحات
        self.refresh_dashboard_btn.clicked.connect(self.refresh_selected_dashboard)

        # تبويب الذكاء التجاري
        self.run_analysis_btn.clicked.connect(self.run_business_intelligence_analysis)

        # تبويب التحليلات المتقدمة
        self.run_advanced_btn.clicked.connect(self.run_advanced_analytics)

    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            # تحميل قائمة التقارير المحفوظة
            self.load_saved_reports()

            # تحميل الرؤى الأخيرة
            self.load_recent_insights()

            # تحديث اللوحات
            self.refresh_selected_dashboard()

        except Exception as e:
            self.logger.error(f"فشل في تحميل البيانات الأولية: {e}")

    def on_navigation_item_clicked(self, item, column):
        """معالجة نقر عنصر في شجرة التنقل"""
        item_type = item.data(0, Qt.UserRole)

        if item_type == "sales_reports":
            self.content_tabs.setCurrentIndex(0)  # تبويب التقارير
            self.report_type_combo.setCurrentText("تقرير المبيعات")
        elif item_type == "inventory_reports":
            self.content_tabs.setCurrentIndex(0)
            self.report_type_combo.setCurrentText("تقرير المخزون")
        elif item_type == "customer_reports":
            self.content_tabs.setCurrentIndex(0)
            self.report_type_combo.setCurrentText("تقرير العملاء")
        elif item_type == "sales_dashboard":
            self.content_tabs.setCurrentIndex(1)  # تبويب اللوحات
            self.dashboard_combo.setCurrentText("لوحة المبيعات")
            self.refresh_selected_dashboard()
        elif item_type == "inventory_dashboard":
            self.content_tabs.setCurrentIndex(1)
            self.dashboard_combo.setCurrentText("لوحة المخزون")
            self.refresh_selected_dashboard()
        elif item_type == "business_insights":
            self.content_tabs.setCurrentIndex(2)  # تبويب الذكاء التجاري
            self.analysis_type_combo.setCurrentText("الرؤى التجارية")
        elif item_type == "predictive_insights":
            self.content_tabs.setCurrentIndex(2)
            self.analysis_type_combo.setCurrentText("الرؤى التنبؤية")
        elif item_type == "predictive_models":
            self.content_tabs.setCurrentIndex(3)  # تبويب التحليلات المتقدمة
            self.advanced_type_combo.setCurrentText("النماذج التنبؤية")

    def create_new_report(self):
        """إنشاء تقرير جديد"""
        # فتح نافذة إنشاء تقرير جديد
        self.logger.info("فتح نافذة إنشاء تقرير جديد")

    def export_data(self):
        """تصدير البيانات"""
        # تصدير البيانات الحالية
        self.logger.info("تصدير البيانات")

    def refresh_all(self):
        """تحديث جميع البيانات"""
        try:
            self.load_saved_reports()
            self.load_recent_insights()
            self.refresh_selected_dashboard()
            self.logger.info("تم تحديث جميع البيانات")
        except Exception as e:
            self.logger.error(f"فشل في تحديث البيانات: {e}")

    def apply_date_filter(self):
        """تطبيق فلتر التاريخ"""
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()

        # تحديث البيانات حسب الفترة المحددة
        self.logger.info(f"تطبيق فلتر التاريخ: {start_date} - {end_date}")

    def generate_selected_report(self):
        """إنشاء التقرير المحدد"""
        report_type = self.report_type_combo.currentText()

        try:
            if report_type == "تقرير المبيعات":
                report = self.reporting_service.generate_sales_report()
            elif report_type == "تقرير المخزون":
                report = self.reporting_service.generate_inventory_report()
            elif report_type == "تقرير العملاء":
                report = self.reporting_service.generate_customer_report()
            else:
                report = None

            if report:
                self.display_report_results(report)
                self.logger.info(f"تم إنشاء {report_type}")
            else:
                self.logger.warning(f"فشل في إنشاء {report_type}")

        except Exception as e:
            self.logger.error(f"فشل في إنشاء التقرير: {e}")

    def refresh_selected_dashboard(self):
        """تحديث اللوحة المحددة"""
        dashboard_type = self.dashboard_combo.currentText()

        try:
            # مسح الرسوم البيانية الحالية
            self.clear_charts_area()

            if dashboard_type == "لوحة المبيعات":
                self.create_sales_dashboard()
            elif dashboard_type == "لوحة المخزون":
                self.create_inventory_dashboard()
            elif dashboard_type == "لوحة العملاء":
                self.create_customer_dashboard()
            elif dashboard_type == "اللوحة المالية":
                self.create_financial_dashboard()

            self.logger.info(f"تم تحديث {dashboard_type}")

        except Exception as e:
            self.logger.error(f"فشل في تحديث اللوحة: {e}")

    def run_business_intelligence_analysis(self):
        """تشغيل تحليل الذكاء التجاري"""
        analysis_type = self.analysis_type_combo.currentText()

        try:
            if analysis_type == "الرؤى التجارية":
                insights = self.bi_service.generate_business_insights()
                self.display_business_insights(insights)
            elif analysis_type == "الرؤى التنبؤية":
                predictions = self.bi_service.generate_predictive_insights()
                self.display_predictive_insights(predictions)
            elif analysis_type == "تقسيم العملاء":
                segments = self.bi_service.segment_customers()
                self.display_customer_segments(segments)

            self.logger.info(f"تم تشغيل تحليل {analysis_type}")

        except Exception as e:
            self.logger.error(f"فشل في تشغيل تحليل الذكاء التجاري: {e}")

    def run_advanced_analytics(self):
        """تشغيل التحليلات المتقدمة"""
        analysis_type = self.advanced_type_combo.currentText()

        try:
            if analysis_type == "تحليل السلاسل الزمنية":
                result = self.analytics_service.perform_time_series_analysis("sales")
                self.display_time_series_results(result)
            elif analysis_type == "تحسين المخزون":
                result = self.analytics_service.optimize_inventory_levels()
                self.display_inventory_optimization(result)

            self.logger.info(f"تم تشغيل التحليل المتقدم: {analysis_type}")

        except Exception as e:
            self.logger.error(f"فشل في تشغيل التحليلات المتقدمة: {e}")

    # طرق عرض النتائج
    def display_report_results(self, report):
        """عرض نتائج التقرير"""
        # إضافة التقرير إلى جدول التقارير
        row_count = self.reports_table.rowCount()
        self.reports_table.insertRow(row_count)

        self.reports_table.setItem(row_count, 0, QTableWidgetItem(report.get("title", "تقرير")))
        self.reports_table.setItem(row_count, 1, QTableWidgetItem(report.get("type", "غير محدد")))
        self.reports_table.setItem(row_count, 2, QTableWidgetItem(str(datetime.now())))
        self.reports_table.setItem(row_count, 3, QTableWidgetItem("مكتمل"))
        self.reports_table.setItem(row_count, 4, QTableWidgetItem("عرض | تصدير"))

    def display_business_insights(self, insights):
        """عرض الرؤى التجارية"""
        self.bi_results_area.clear()

        if not insights:
            self.bi_results_area.setText("لم يتم العثور على رؤى تجارية")
            return

        text = "الرؤى التجارية المولدة:\n\n"
        for insight in insights:
            text += f"🔍 {insight.title}\n"
            text += f"   {insight.description}\n"
            text += f"   مستوى التأثير: {insight.impact_level}\n"
            text += f"   الإجراءات المقترحة: {', '.join(insight.recommended_actions)}\n\n"

        self.bi_results_area.setText(text)

        # تحديث جدول الرؤى
        self.insights_table.setRowCount(0)
        for insight in insights:
            row_count = self.insights_table.rowCount()
            self.insights_table.insertRow(row_count)

            self.insights_table.setItem(row_count, 0, QTableWidgetItem(insight.insight_type))
            self.insights_table.setItem(row_count, 1, QTableWidgetItem(insight.description))
            self.insights_table.setItem(row_count, 2, QTableWidgetItem(insight.impact_level))
            self.insights_table.setItem(row_count, 3, QTableWidgetItem(str(insight.generated_at)))

    def display_predictive_insights(self, predictions):
        """عرض الرؤى التنبؤية"""
        self.bi_results_area.clear()

        if not predictions:
            self.bi_results_area.setText("لم يتم العثور على رؤى تنبؤية")
            return

        text = "الرؤى التنبؤية:\n\n"
        for pred in predictions:
            text += f"🔮 {pred.prediction_type}\n"
            text += f"   القيمة المتوقعة: {pred.predicted_value:.2f}\n"
            text += f"   الأفق الزمني: {pred.time_horizon}\n"
            text += f"   العوامل المؤثرة: {', '.join(pred.influencing_factors)}\n\n"

        self.bi_results_area.setText(text)

    def display_customer_segments(self, segments):
        """عرض شرائح العملاء"""
        self.bi_results_area.clear()

        if not segments:
            self.bi_results_area.setText("لم يتم العثور على شرائح عملاء")
            return

        text = "شرائح العملاء:\n\n"
        for segment in segments:
            text += f"👥 {segment.segment_name}\n"
            text += f"   عدد العملاء: {segment.customer_count}\n"
            text += f"   قيمة العميل المتوسطة: {segment.value_metrics.get('avg_customer_value', 0):.2f}\n\n"

        self.bi_results_area.setText(text)

    def display_time_series_results(self, result):
        """عرض نتائج تحليل السلاسل الزمنية"""
        if result:
            text = f"تحليل السلاسل الزمنية للمتغير: {result.target_variable}\n\n"
            text += f"دقة النموذج: {result.accuracy_metrics.get('accuracy', 0):.2f}%\n"
            text += f"عدد التنبؤات: {len(result.predictions)}\n\n"

            for pred in result.predictions[:5]:  # عرض أول 5 تنبؤات
                text += f"التاريخ: {pred['date']}, القيمة المتوقعة: {pred['predicted_value']:.2f}\n"

            self.advanced_results_area.setText(text)
        else:
            self.advanced_results_area.setText("فشل في إجراء تحليل السلاسل الزمنية")

    def display_inventory_optimization(self, result):
        """عرض نتائج تحسين المخزون"""
        if result:
            text = "توصيات تحسين المخزون:\n\n"
            text += f"إجمالي المنتجات المحللة: {result.accuracy_metrics.get('total_products', 0)}\n"
            text += f"المنتجات عالية المخاطر: {result.accuracy_metrics.get('high_risk_items', 0)}\n\n"

            for rec in result.predictions[:10]:  # عرض أول 10 توصيات
                text += f"المنتج: {rec['product_name']}\n"
                text += f"   المخزون الحالي: {rec['current_stock']}\n"
                text += f"   المخزون المثالي: {rec['optimal_stock']:.0f}\n"
                text += f"   نقطة إعادة الطلب: {rec['reorder_point']:.0f}\n\n"

            self.advanced_results_area.setText(text)
        else:
            self.advanced_results_area.setText("فشل في تحسين مستويات المخزون")

    # طرق إنشاء الرسوم البيانية
    def create_sample_charts(self):
        """إنشاء رسوم بيانية تجريبية"""
        # رسم بياني للمبيعات
        sales_chart = self.create_sales_chart()
        self.dashboard_charts_layout.addWidget(sales_chart)

        # رسم بياني للمخزون
        inventory_chart = self.create_inventory_chart()
        self.dashboard_charts_layout.addWidget(inventory_chart)

    def create_sales_chart(self):
        """إنشاء رسم بياني للمبيعات"""
        chart = QChart()
        chart.setTitle("المبيعات الشهرية")

        series = QLineSeries()
        series.setName("المبيعات")

        # بيانات تجريبية
        for i in range(12):
            series.append(i, (i + 1) * 1000 + np.random.randint(-500, 500))

        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setRange(0, 11)
        axis_x.setLabelFormat("%d")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 15000)
        axis_y.setLabelFormat("%.0f")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(300)
        return chart_view

    def create_inventory_chart(self):
        """إنشاء رسم بياني للمخزون"""
        chart = QChart()
        chart.setTitle("توزيع المخزون")

        series = QPieSeries()
        series.append("منخفض", 30)
        series.append("متوسط", 45)
        series.append("عالي", 25)

        chart.addSeries(series)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(300)
        return chart_view

    def create_sales_dashboard(self):
        """إنشاء لوحة المبيعات"""
        # مسح المنطقة
        self.clear_charts_area()

        # إضافة رسوم بيانية المبيعات
        sales_trend_chart = self.create_sales_trend_chart()
        self.dashboard_charts_layout.addWidget(sales_trend_chart)

        sales_by_category_chart = self.create_sales_by_category_chart()
        self.dashboard_charts_layout.addWidget(sales_by_category_chart)

    def create_inventory_dashboard(self):
        """إنشاء لوحة المخزون"""
        self.clear_charts_area()

        inventory_levels_chart = self.create_inventory_levels_chart()
        self.dashboard_charts_layout.addWidget(inventory_levels_chart)

        stock_turnover_chart = self.create_stock_turnover_chart()
        self.dashboard_charts_layout.addWidget(stock_turnover_chart)

    def create_customer_dashboard(self):
        """إنشاء لوحة العملاء"""
        self.clear_charts_area()

        customer_growth_chart = self.create_customer_growth_chart()
        self.dashboard_charts_layout.addWidget(customer_growth_chart)

    def create_financial_dashboard(self):
        """إنشاء اللوحة المالية"""
        self.clear_charts_area()

        revenue_chart = self.create_revenue_chart()
        self.dashboard_charts_layout.addWidget(revenue_chart)

        profit_chart = self.create_profit_chart()
        self.dashboard_charts_layout.addWidget(profit_chart)

    def clear_charts_area(self):
        """مسح منطقة الرسوم البيانية"""
        while self.dashboard_charts_layout.count():
            item = self.dashboard_charts_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    # طرق إنشاء الرسوم البيانية المحددة
    def create_sales_trend_chart(self):
        """إنشاء رسم بياني اتجاه المبيعات"""
        chart = QChart()
        chart.setTitle("اتجاه المبيعات")

        series = QLineSeries()
        series.setName("المبيعات اليومية")

        # بيانات تجريبية
        for i in range(30):
            series.append(i, 5000 + np.random.randint(-1000, 1000))

        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setRange(0, 29)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(3000, 7000)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(250)
        return chart_view

    def create_sales_by_category_chart(self):
        """إنشاء رسم بياني المبيعات حسب الفئة"""
        chart = QChart()
        chart.setTitle("المبيعات حسب الفئة")

        series = QBarSeries()
        bar_set = QBarSet("المبيعات")
        bar_set.append([45000, 32000, 28000, 15000])

        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(["إلكترونيات", "ملابس", "أغذية", "أخرى"])
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 50000)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(250)
        return chart_view

    def create_inventory_levels_chart(self):
        """إنشاء رسم بياني مستويات المخزون"""
        chart = QChart()
        chart.setTitle("مستويات المخزون")

        series = QBarSeries()
        bar_set = QBarSet("المخزون")
        bar_set.append([150, 200, 80, 300, 120])

        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(["منتج A", "منتج B", "منتج C", "منتج D", "منتج E"])
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 350)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(250)
        return chart_view

    def create_stock_turnover_chart(self):
        """إنشاء رسم بياني دوران المخزون"""
        chart = QChart()
        chart.setTitle("دوران المخزون")

        series = QLineSeries()
        series.setName("معدل الدوران")

        for i in range(12):
            series.append(i, 4 + np.random.random() * 4)

        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setRange(0, 11)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 10)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(250)
        return chart_view

    def create_customer_growth_chart(self):
        """إنشاء رسم بياني نمو العملاء"""
        chart = QChart()
        chart.setTitle("نمو قاعدة العملاء")

        series = QLineSeries()
        series.setName("عدد العملاء")

        customer_count = 1000
        for i in range(12):
            customer_count += np.random.randint(-50, 100)
            series.append(i, customer_count)

        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setRange(0, 11)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(900, 1500)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(250)
        return chart_view

    def create_revenue_chart(self):
        """إنشاء رسم بياني الإيرادات"""
        chart = QChart()
        chart.setTitle("الإيرادات الشهرية")

        series = QBarSeries()
        bar_set = QBarSet("الإيرادات")
        bar_set.append([50000, 55000, 48000, 60000, 52000, 58000])

        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو"])
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 65000)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(250)
        return chart_view

    def create_profit_chart(self):
        """إنشاء رسم بياني الأرباح"""
        chart = QChart()
        chart.setTitle("الأرباح الشهرية")

        series = QLineSeries()
        series.setName("الأرباح")

        for i in range(6):
            series.append(i, 5000 + np.random.randint(-2000, 3000))

        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setRange(0, 5)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 10000)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setMinimumHeight(250)
        return chart_view

    # طرق تحميل البيانات
    def load_saved_reports(self):
        """تحميل التقارير المحفوظة"""
        # محاكاة تحميل التقارير
        self.reports_table.setRowCount(0)

        sample_reports = [
            ("تقرير المبيعات الشهري", "مبيعات", "2024-01-15", "مكتمل"),
            ("تقرير المخزون", "مخزون", "2024-01-14", "مكتمل"),
            ("تقرير العملاء", "عملاء", "2024-01-13", "قيد المراجعة"),
        ]

        for report in sample_reports:
            row_count = self.reports_table.rowCount()
            self.reports_table.insertRow(row_count)

            for col, value in enumerate(report):
                self.reports_table.setItem(row_count, col, QTableWidgetItem(value))

            # إضافة أزرار الإجراءات
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)

            view_btn = QPushButton("عرض")
            view_btn.setMaximumWidth(50)
            export_btn = QPushButton("تصدير")
            export_btn.setMaximumWidth(50)

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(export_btn)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            self.reports_table.setCellWidget(row_count, 4, actions_widget)

    def load_recent_insights(self):
        """تحميل الرؤى الأخيرة"""
        # محاكاة تحميل الرؤى
        self.insights_table.setRowCount(0)

        sample_insights = [
            ("اتجاه", "ارتفاع في المبيعات بنسبة 15%", "عالي", "2024-01-15"),
            ("شذوذ", "انخفاض غير متوقع في المخزون", "متوسط", "2024-01-14"),
            ("فرصة", "إمكانية زيادة المبيعات في فئة معينة", "عالي", "2024-01-13"),
        ]

        for insight in sample_insights:
            row_count = self.insights_table.rowCount()
            self.insights_table.insertRow(row_count)

            for col, value in enumerate(insight):
                self.insights_table.setItem(row_count, col, QTableWidgetItem(value))
