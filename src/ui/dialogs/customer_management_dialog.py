#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
نافذة إدارة العملاء
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from src.ui.styles.design_tokens import C
from src.ui.widgets.base_dialog import BaseDialog
from src.ui.widgets.quantum_notification import NotificationManager


class CustomerManagementDialog(BaseDialog):
    """نافذة إدارة العملاء"""

    def __init__(self, db_manager, logger=None, parent=None):
        super().__init__(title="", parent=parent)
        self.db_manager = db_manager
        self.logger = logger
        self.customers = []

        # self.setWindowTitle("إدارة العملاء") # Handled by CustomTitleBar
        # self.setGeometry(100, 100, 800, 500)

        # --- Quantum Window Setup ---
        # Notifications
        self.notify = NotificationManager(self)

        self.resize(800, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.init_ui()
        self.load_customers()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = self.content_layout

        # Re-assign layout to content_layout for the rest of the elements
        layout = self.content_layout

        # شريط البحث والإضافة
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن عميل...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)

        add_btn = QPushButton("+ عميل جديد")
        add_btn.setMinimumHeight(32)
        add_btn.clicked.connect(self.add_customer)
        search_layout.addWidget(add_btn)

        layout.addLayout(search_layout)

        # جدول العملاء
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الاسم", "الهاتف", "البريد الإلكتروني", "الرصيد", "الإجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {C.BORDER_DEFAULT};
                gridline-color: {C.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {C.TEXT_PRIMARY};
                color: {C.TEXT_BRIGHT};
                padding: 5px;
                border: none;
            }}
        """)
        layout.addWidget(self.table)

        # أزرار الإغلاق
        close_layout = QHBoxLayout()
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.close)
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def load_customers(self):
        """تحميل قائمة العملاء"""
        try:
            query = "SELECT id, name, phone, email, current_balance, is_active FROM customers ORDER BY name"
            results = self.db_manager.fetch_all(query)

            self.customers = []
            for row in results:
                cust_id = row["id"]
                name = row["name"]
                phone = row["phone"]
                email = row["email"]
                balance = row["current_balance"]
                is_active = row["is_active"]
                self.customers.append(
                    {
                        "id": cust_id,
                        "name": name,
                        "phone": phone or "",
                        "email": email or "",
                        "balance": balance or 0,
                        "is_active": is_active,
                    }
                )

            self.display_customers(self.customers)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل العملاء: {str(e)}")
            self.notify.show_error("خطأ", f"فشل في تحميل العملاء: {str(e)}")

    def display_customers(self, customers):
        """عرض العملاء في الجدول"""
        self.table.setRowCount(0)

        for cust in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # الاسم
            name_item = QTableWidgetItem(cust["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, cust["id"])
            self.table.setItem(row, 0, name_item)

            # الهاتف
            phone_item = QTableWidgetItem(cust["phone"])
            self.table.setItem(row, 1, phone_item)

            # البريد الإلكتروني
            email_item = QTableWidgetItem(cust["email"])
            self.table.setItem(row, 2, email_item)

            # الرصيد
            balance_item = QTableWidgetItem(f"{float(cust['balance']):,.2f}")
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, balance_item)

            # أزرار الإجراءات
            actions_layout = QHBoxLayout()

            edit_btn = QPushButton("تعديل")
            edit_btn.setMaximumWidth(60)
            edit_btn.clicked.connect(lambda checked, cust_id=cust["id"]: self.edit_customer(cust_id))

            delete_btn = QPushButton("حذف")
            delete_btn.setMaximumWidth(60)
            delete_btn.setStyleSheet(f"background-color: {C.ACCENT_CORAL}; color: {C.TEXT_BRIGHT};")
            delete_btn.clicked.connect(lambda checked, cust_id=cust["id"]: self.delete_customer(cust_id))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            actions_widget = self.create_widget_from_layout(actions_layout)
            self.table.setCellWidget(row, 4, actions_widget)

    def create_widget_from_layout(self, layout):
        """إنشاء widget من layout"""
        from PySide6.QtWidgets import QWidget

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def on_search(self, text):
        """البحث في العملاء"""
        filtered = [c for c in self.customers if text.lower() in c["name"].lower() or text in c["phone"]]
        self.display_customers(filtered)

    def add_customer(self):
        """إضافة عميل جديد"""
        from src.ui.dialogs.customer_form_dialog import CustomerFormDialog

        dialog = CustomerFormDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_customers()

    def edit_customer(self, customer_id):
        """تعديل عميل"""
        from src.ui.dialogs.customer_form_dialog import CustomerFormDialog

        dialog = CustomerFormDialog(self.db_manager, customer_id=customer_id, parent=self)
        if dialog.exec():
            self.load_customers()

    def delete_customer(self, customer_id):
        """حذف عميل (soft-delete مع التحقق من السجلات المرتبطة)"""
        try:
            # التحقق من وجود عمليات بيع مرتبطة
            sales_count = self.db_manager.fetch_one(
                "SELECT COUNT(*) FROM sales WHERE customer_id = ?", (customer_id,)
            )[0] or 0

            if sales_count > 0:
                reply = QMessageBox.warning(
                    self,
                    "تحذير",
                    f"هذا العميل لديه {sales_count} عملية بيع مرتبطة. سيتم تعطيل العميل بدلاً من حذفه.",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                )
                if reply != QMessageBox.StandardButton.Ok:
                    return

            # Soft-delete: تعطيل العميل بدلاً من حذفه
            self.db_manager.execute_query(
                "UPDATE customers SET is_active = 0 WHERE id = ?", (customer_id,)
            )
            self.load_customers()
            self.notify.show_success("نجاح", "تم تعطيل العميل بنجاح")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف العميل: {str(e)}")
            self.notify.show_error("خطأ", f"فشل في حذف العميل: {str(e)}")
