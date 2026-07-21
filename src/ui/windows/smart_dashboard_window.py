#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نافذة لوحة المعلومات الذكية (Smart Insights Dashboard)
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.services.ai_service import AIService
from src.ui.styles.design_tokens import C as Colors
from src.utils.i18n_api import I18n

# Add project root to path


class SmartDashboardWindow(QMainWindow):
    """
    نافذة لوحة المعلومات الذكية (Smart Insights Dashboard)
    Solid Unified Version (Standard El-Joumla)
    """

    window_key = "smart_dashboard"
    window_singleton = True
    window_title = "Smart Dashboard"

    def __init__(self, ai_service: AIService, parent=None):
        super().__init__(parent)
        self.ai_service = ai_service

        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        self.setWindowTitle(self.i18n.get_message("smart_dashboard"))
        self.setMinimumSize(1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet(f"QMainWindow {{ background-color: {Colors.BG_VOID}; }}")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout

        # Action Buttons
        self.refresh_button = QPushButton(self.i18n.get_message("refresh_data"))
        self.refresh_button.clicked.connect(self.refresh_all_data)
        self.main_layout.addWidget(self.refresh_button)

        # Main Grid Layout
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)

        # --- Assistant Group ---
        self.assistant_group = QGroupBox(self.i18n.get_message("smart_assistant"))
        self.assistant_layout = QVBoxLayout()
        self.assistant_query_input = QLineEdit()
        self.assistant_query_input.setPlaceholderText(self.i18n.get_message("ask_question"))
        self.assistant_query_input.returnPressed.connect(self.query_assistant)
        self.assistant_response_display = QTextEdit()
        self.assistant_response_display.setReadOnly(True)
        self.assistant_layout.addWidget(self.assistant_query_input)
        self.assistant_layout.addWidget(self.assistant_response_display)
        self.assistant_group.setLayout(self.assistant_layout)
        self.grid_layout.addWidget(self.assistant_group, 0, 0, 1, 2)  # Span 2 columns

        # --- Low Stock Group ---
        self.low_stock_group = QGroupBox(self.i18n.get_message("low_stock_products"))
        self.low_stock_layout = QVBoxLayout()
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(3)
        self.low_stock_table.setHorizontalHeaderLabels(
            [
                self.i18n.get_message("product"),
                self.i18n.get_message("current_quantity"),
                self.i18n.get_message("reorder_level"),
            ]
        )
        self.low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.low_stock_table.horizontalHeader().setMinimumSectionSize(120)
        self.low_stock_table.horizontalHeader().setDefaultSectionSize(150)
        self.low_stock_table.horizontalHeader().setStretchLastSection(True)
        self.low_stock_layout.addWidget(self.low_stock_table)
        self.low_stock_group.setLayout(self.low_stock_layout)
        self.grid_layout.addWidget(self.low_stock_group, 1, 0)

        # --- Top Selling Group ---
        self.top_selling_group = QGroupBox(self.i18n.get_message("top_selling_products"))
        self.top_selling_layout = QVBoxLayout()
        self.top_selling_table = QTableWidget()
        self.top_selling_table.setColumnCount(2)
        self.top_selling_table.setHorizontalHeaderLabels(
            [self.i18n.get_message("product"), self.i18n.get_message("quantity_sold")]
        )
        self.top_selling_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.top_selling_table.horizontalHeader().setMinimumSectionSize(120)
        self.top_selling_table.horizontalHeader().setDefaultSectionSize(150)
        self.top_selling_table.horizontalHeader().setStretchLastSection(True)
        self.top_selling_layout.addWidget(self.top_selling_table)
        self.top_selling_group.setLayout(self.top_selling_layout)
        self.grid_layout.addWidget(self.top_selling_group, 1, 1)

        central_widget.setLayout(self.main_layout)
        self.refresh_all_data()

    def refresh_all_data(self):
        """Loads and displays all data from the AI service."""
        try:
            self.load_low_stock_products()
            self.load_top_selling_products()
            self.assistant_response_display.setPlaceholderText(self.i18n.get_message("data_updated_ask_question"))
        except Exception as e:
            QMessageBox.critical(
                self,
                self.i18n.get_message("error"),
                self.i18n.get_message("refresh_data_failed", error=str(e)),
            )

    def query_assistant(self):
        """Handles a query to the smart assistant."""
        query_text = self.assistant_query_input.text()
        if not query_text:
            return

        self.assistant_response_display.setPlaceholderText(self.i18n.get_message("processing_query"))
        response = self.ai_service.smart_assistant_query(query_text)

        message = response.get("message", self.i18n.get_message("no_response"))
        data = response.get("data")

        question_label = self.i18n.get_message("question")
        answer_label = self.i18n.get_message("answer")
        display_text = f"<b>{question_label}:</b> {query_text}<br>"
        display_text += f"<b>{answer_label}:</b> {message}<br><br>"

        if data and isinstance(data, list):
            for item in data:
                display_text += "<ul>"
                for key, value in item.items():
                    display_text += f"<li><b>{key}:</b> {value}</li>"
                display_text += "</ul>"

        self.assistant_response_display.setHtml(display_text)
        self.assistant_query_input.clear()

    def load_low_stock_products(self):
        """Loads and displays low stock products."""
        response = self.ai_service.smart_assistant_query("مخزون منخفض")
        products = response.get("data", [])
        self.low_stock_table.setRowCount(len(products))
        for row, item in enumerate(products):
            self.low_stock_table.setItem(row, 0, QTableWidgetItem(str(item.get("name", "N/A"))))
            self.low_stock_table.setItem(row, 1, QTableWidgetItem(str(item.get("quantity", "N/A"))))
            self.low_stock_table.setItem(row, 2, QTableWidgetItem(str(item.get("reorder_level", "N/A"))))

    def load_top_selling_products(self):
        """Loads and displays top selling products."""
        response = self.ai_service.smart_assistant_query("أفضل مبيعات")
        products = response.get("data", [])
        self.top_selling_table.setRowCount(len(products))
        for row, item in enumerate(products):
            self.top_selling_table.setItem(row, 0, QTableWidgetItem(str(item.get("name", "N/A"))))
            self.top_selling_table.setItem(row, 1, QTableWidgetItem(str(item.get("total_sold", "N/A"))))

    def add_widget(self, *args, **kwargs):
        """إضافة ويدجت (Public API) — placeholder for future drag-and-drop support"""
        # Not yet implemented; dashboards use a fixed layout
        pass

    def remove_widget(self, *args, **kwargs):
        """إزالة ويدجت (Public API) — placeholder for future drag-and-drop support"""
        pass

    def arrange_widgets(self, *args, **kwargs):
        """ترتيب الويدجت (Public API) — placeholder for future layout management"""
        pass

    def save_dashboard_layout(self, *args, **kwargs):
        """حفظ تخطيط اللوحة (Public API) — placeholder for future persistence"""
        pass

    def load_smart_widgets(self):
        """تحميل الأدوات الذكية (Public API)"""
        try:
            return self.refresh_all_data()
        except Exception:
            pass


if __name__ == "__main__":
    # This is for testing the window independently
    from PySide6.QtWidgets import QApplication

    from src.core.database_manager import DatabaseManager
    from src.utils.logger import setup_logger

    app = QApplication(sys.argv)

    # Mock services for testing
    db_path = Path(__file__).resolve().parents[3] / "data" / "standard_eljoumla.db"
    db_manager = DatabaseManager(db_path)
    logger = setup_logger("test_dashboard")
    ai_service = AIService(db_manager, logger)

    window = SmartDashboardWindow(ai_service)
    window.show()

    sys.exit(app.exec())
