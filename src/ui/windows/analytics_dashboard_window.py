from PySide6.QtGui import QColor

#!/usr/bin/env python3  # noqa: E265
# -*- coding: utf-8 -*-
"""
نافذة لوحة التحليلات المتقدمة - Advanced Analytics Dashboard Window
واجهة شاملة للتحليلات والرسوم البيانية
"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

project_root = Path(__file__).parent.parent.parent.parent

from src.core.database_manager import DatabaseManager
from src.services.analytics_service import AnalyticsService
from src.ui.widgets.advanced_charts import (
    BarChartWidget,
    LineChartWidget,
    PieChartWidget,
)
from src.utils.logger import setup_logger


class AnalyticsDashboardWindow(QMainWindow):
    """نافذة لوحة التحليلات المتقدمة"""

    # Window Manager attributes
    window_key = "analytics_dashboard"
    window_singleton = True
    window_title = "📊 لوحة التحليلات المتقدمة"

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.analytics_service = AnalyticsService(db_manager, self.logger)

        self.setWindowTitle("لوحة التحليلات المتقدمة")
        self.setMinimumSize(1400, 900)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet("QMainWindow { background-color: #020617; }")

        self.setup_ui()
        self.load_default_analytics()

    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

        export_action = QAction("💾 تصدير", self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)

        # Filters
        filters_group = QGroupBox("المرشحات")
        filters_layout = QHBoxLayout()

        filters_layout.addWidget(QLabel("من:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        filters_layout.addWidget(self.start_date)

        filters_layout.addWidget(QLabel("إلى:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filters_layout.addWidget(self.end_date)

        apply_btn = QPushButton("تطبيق")
        apply_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(apply_btn)

        filters_layout.addStretch()
        filters_group.setLayout(filters_layout)
        main_layout.addWidget(filters_group)

        # Tab Widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Tab 1: Sales Analytics
        sales_tab = QWidget()
        sales_layout = QVBoxLayout(sales_tab)

        # Sales Trends Chart
        self.sales_trends_chart = LineChartWidget("اتجاهات المبيعات")
        sales_layout.addWidget(self.sales_trends_chart)

        # Sales by Category Chart
        self.sales_category_chart = PieChartWidget("المبيعات حسب الفئة")
        sales_layout.addWidget(self.sales_category_chart)

        # Sales by Customer Table
        self.sales_customer_table = QTableWidget()
        self.sales_customer_table.setColumnCount(4)
        self.sales_customer_table.setHorizontalHeaderLabels(["العميل", "عدد المبيعات", "المجموع", "المتوسط"])
        self.sales_customer_table.horizontalHeader().setStretchLastSection(True)
        self.sales_customer_table.setAlternatingRowColors(True)
        sales_layout.addWidget(self.sales_customer_table)

        tab_widget.addTab(sales_tab, "📈 تحليلات المبيعات")

        # Tab 2: Inventory Analytics
        inventory_tab = QWidget()
        inventory_layout = QVBoxLayout(inventory_tab)

        # Inventory Turnover Chart
        self.inventory_turnover_chart = BarChartWidget("معدل دوران المخزون")
        inventory_layout.addWidget(self.inventory_turnover_chart)

        # Stock Alerts Table
        self.stock_alerts_table = QTableWidget()
        self.stock_alerts_table.setColumnCount(4)
        self.stock_alerts_table.setHorizontalHeaderLabels(["المنتج", "المخزون الحالي", "الحد الأدنى", "الحالة"])
        self.stock_alerts_table.horizontalHeader().setStretchLastSection(True)
        self.stock_alerts_table.setAlternatingRowColors(True)
        inventory_layout.addWidget(self.stock_alerts_table)

        tab_widget.addTab(inventory_tab, "📦 تحليلات المخزون")

        # Tab 3: Financial Analytics
        financial_tab = QWidget()
        financial_layout = QVBoxLayout(financial_tab)

        # Profit Margin Chart
        self.profit_margin_chart = BarChartWidget("هامش الربح")
        financial_layout.addWidget(self.profit_margin_chart)

        # Cash Flow Chart
        self.cash_flow_chart = LineChartWidget("التدفق النقدي")
        financial_layout.addWidget(self.cash_flow_chart)

        tab_widget.addTab(financial_tab, "💰 التحليلات المالية")

        # Status Bar
        self.statusBar().showMessage("جاهز")

    def load_default_analytics(self):
        """تحميل التحليلات الافتراضية"""
        self.apply_filters()

    def apply_filters(self):
        """تطبيق المرشحات"""
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()

        # تحميل تحليلات المبيعات
        self.load_sales_analytics(start_date, end_date)

        # تحميل تحليلات المخزون
        self.load_inventory_analytics()

        # تحميل التحليلات المالية
        self.load_financial_analytics(start_date, end_date)

        self.statusBar().showMessage("تم تحديث البيانات")

    def load_sales_analytics(self, start_date: datetime, end_date: datetime):
        """تحميل تحليلات المبيعات"""
        # Sales Trends
        trends_result = self.analytics_service.get_sales_trends(start_date, end_date)
        if trends_result.get("success"):
            data = trends_result.get("data", [])
            if data:
                chart_data = []
                for idx, item in enumerate(data):
                    date = (  # noqa: F841
                        datetime.fromisoformat(item["date"]) if isinstance(item["date"], str) else item["date"]
                    )  # noqa: F841
                    chart_data.append((idx, float(item["total_amount"])))

                self.sales_trends_chart.clear()
                self.sales_trends_chart.add_series("المبيعات", chart_data)

        # Sales by Category
        category_result = self.analytics_service.get_sales_by_category(start_date, end_date)
        if category_result.get("success"):
            data = category_result.get("data", [])
            if data:
                pie_data = {item["category"]: item["total_amount"] for item in data}
                self.sales_category_chart.clear()
                self.sales_category_chart.add_data(pie_data)

        # Sales by Customer
        customer_result = self.analytics_service.get_sales_by_customer(
            limit=10, start_date=start_date, end_date=end_date
        )
        if customer_result.get("success"):
            data = customer_result.get("data", [])
            self.sales_customer_table.setRowCount(len(data))

            for row, item in enumerate(data):
                self.sales_customer_table.setItem(row, 0, QTableWidgetItem(item["customer_name"]))
                self.sales_customer_table.setItem(row, 1, QTableWidgetItem(str(item["sale_count"])))
                self.sales_customer_table.setItem(row, 2, QTableWidgetItem(f"{item['total_amount']:.2f}"))
                self.sales_customer_table.setItem(row, 3, QTableWidgetItem(f"{item['avg_amount']:.2f}"))

    def load_inventory_analytics(self):
        """تحميل تحليلات المخزون"""
        # Inventory Turnover
        turnover_result = self.analytics_service.get_inventory_turnover()
        if turnover_result.get("success"):
            data = turnover_result.get("data", [])[:10]  # أول 10 منتجات
            if data:
                categories = [item["product_name"] for item in data]
                turnover_data = {"معدل الدوران": [item["turnover_rate"] for item in data]}
                self.inventory_turnover_chart.clear()
                self.inventory_turnover_chart.add_data(categories, turnover_data)

        # Stock Alerts
        alerts_result = self.analytics_service.get_stock_alerts()
        if alerts_result.get("success"):
            alerts = alerts_result.get("alerts", {})
            low_stock = alerts.get("low_stock", [])
            out_of_stock = alerts.get("out_of_stock", [])

            all_alerts = out_of_stock + low_stock
            self.stock_alerts_table.setRowCount(len(all_alerts))

            for row, alert in enumerate(all_alerts):
                self.stock_alerts_table.setItem(row, 0, QTableWidgetItem(alert["product_name"]))
                self.stock_alerts_table.setItem(row, 1, QTableWidgetItem(str(alert["current_stock"])))
                self.stock_alerts_table.setItem(row, 2, QTableWidgetItem(str(alert.get("min_stock", 0))))

                status = "نفد" if alert.get("current_stock", 0) <= 0 else "منخفض"
                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor("red") if status == "نفد" else QColor("orange"))
                self.stock_alerts_table.setItem(row, 3, status_item)

    def load_financial_analytics(self, start_date: datetime, end_date: datetime):
        """تحميل التحليلات المالية"""
        # Profit Margin
        profit_result = self.analytics_service.get_profit_margin_analysis(start_date, end_date)
        if profit_result.get("success"):
            data = profit_result.get("data", [])[:10]  # أول 10 منتجات
            if data:
                categories = [item["product_name"] for item in data]
                margin_data = {"هامش الربح %": [item["margin_percent"] for item in data]}
                self.profit_margin_chart.clear()
                self.profit_margin_chart.add_data(categories, margin_data)

        # Cash Flow
        cashflow_result = self.analytics_service.get_cash_flow_analysis(start_date, end_date)
        if cashflow_result.get("success"):
            data = cashflow_result.get("data", [])
            if data:
                inflow_data = [(idx, item["inflow"]) for idx, item in enumerate(data)]
                outflow_data = [(idx, item["outflow"]) for idx, item in enumerate(data)]

                self.cash_flow_chart.clear()
                self.cash_flow_chart.add_series("التدفق الوارد", inflow_data)
                self.cash_flow_chart.add_series("التدفق الصادر", outflow_data)

    def refresh_data(self):
        """تحديث البيانات"""
        self.apply_filters()

    def export_data(self):
        """تصدير البيانات"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير البيانات",
            f"analytics_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx)",
        )

        if not file_path:
            return

        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()

        # جمع جميع البيانات
        export_data = {
            "sales_trends": self.analytics_service.get_sales_trends(start_date, end_date),
            "sales_by_category": self.analytics_service.get_sales_by_category(start_date, end_date),
            "sales_by_customer": self.analytics_service.get_sales_by_customer(
                limit=100, start_date=start_date, end_date=end_date
            ),
            "inventory_turnover": self.analytics_service.get_inventory_turnover(),
            "stock_alerts": self.analytics_service.get_stock_alerts(),
            "profit_margin": self.analytics_service.get_profit_margin_analysis(start_date, end_date),
            "cash_flow": self.analytics_service.get_cash_flow_analysis(start_date, end_date),
        }

        # التصدير
        if file_path.endswith(".json"):
            success = self.analytics_service.export_to_json(export_data, file_path)
        elif file_path.endswith(".csv"):
            # تصدير أول جدول متاح
            if export_data.get("sales_by_customer", {}).get("data"):
                success = self.analytics_service.export_to_csv(export_data["sales_by_customer"]["data"], file_path)
            else:
                success = False
        elif file_path.endswith(".xlsx"):
            # تصدير متعدد الأوراق
            excel_data = {}
            for key, value in export_data.items():
                if isinstance(value, dict) and "data" in value:
                    excel_data[key] = value["data"]

            if excel_data:
                success = self.analytics_service.export_to_excel(excel_data, file_path)
            else:
                success = False
        else:
            success = False

        if success:
            QMessageBox.information(self, "نجاح", f"تم تصدير البيانات إلى:\n{file_path}")
        else:
            QMessageBox.critical(self, "خطأ", "فشل تصدير البيانات")
