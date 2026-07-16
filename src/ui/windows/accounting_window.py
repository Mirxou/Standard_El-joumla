#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة المحاسبة
Accounting Management Window

توفر واجهة شاملة لإدارة الحسابات والقيود المحاسبية والقوائم المالية
"""

import csv as csv_module
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...models.account import Account
from ...models.journal_entry import JournalEntry, JournalLine
from ...services.accounting_service import AccountingService


class AccountingWindow(QMainWindow):
    """نافذة إدارة المحاسبة"""

    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "accounting"
    window_singleton = True
    window_title = "إدارة المحاسبة"

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.accounting = AccountingService(db_manager)
        self.parent_window = parent

        self.setWindowTitle("إدارة المحاسبة")
        # استخدام أيقونة التطبيق الرئيسية بدلاً من accounting.png
        icon_path = Path(__file__).parent.parent.parent.parent / "assets" / "icons" / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            # Fallback: استخدام أيقونة Qt القياسية
            from PySide6.QtWidgets import QStyle

            app = QApplication.instance()
            if app:
                style = app.style()
                if style:
                    self.setWindowIcon(style.standardIcon(QStyle.SP_FileDialogInfoView))
        self.setGeometry(100, 100, 1200, 700)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet("QMainWindow { background-color: #020617; }")

        self._create_widgets()
        self._setup_connections()
        self._load_data()

    def load_transactions(self) -> List[Any]:
        """تحميل المعاملات"""
        return []

    def add_transaction(self, data: Dict[str, Any] = None) -> bool:
        """إضافة معاملة"""
        return True

    def edit_transaction(self, transaction_id: int, data: Dict[str, Any] = None) -> bool:
        """تعديل معاملة"""
        return True

    def delete_transaction(self, transaction_id: int) -> bool:
        """حذف معاملة"""
        return True

    def get_balance(self) -> float:
        """الحصول على الرصيد الإجمالي"""
        return 0.0

    def generate_report(self, report_type: str) -> bool:
        """توليد تقرير محاسبي"""
        return True

    def _create_widgets(self):
        """إنشاء عناصر الواجهة"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout(main_widget)

        # إنشاء التبويبات
        self.tabs = QTabWidget()

        # تبويب دليل الحسابات
        self.chart_tab = self._create_chart_of_accounts_tab()
        self.tabs.addTab(self.chart_tab, "دليل الحسابات")

        # تبويب اليومية العامة
        self.journal_tab = self._create_journal_tab()
        self.tabs.addTab(self.journal_tab, "اليومية العامة")

        # تبويب ميزان المراجعة
        self.trial_tab = self._create_trial_balance_tab()
        self.tabs.addTab(self.trial_tab, "ميزان المراجعة")

        # تبويب القوائم المالية
        self.financial_tab = self._create_financial_statements_tab()
        self.tabs.addTab(self.financial_tab, "القوائم المالية")

        layout.addWidget(self.tabs)

        # أزرار التحكم السفلية
        buttons_layout = QHBoxLayout()

        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self._refresh_all)
        buttons_layout.addWidget(refresh_btn)

        buttons_layout.addStretch()

        export_btn = QPushButton("تصدير")
        export_btn.clicked.connect(self._export_data)
        buttons_layout.addWidget(export_btn)

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def _create_chart_of_accounts_tab(self):
        """إنشاء تبويب دليل الحسابات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # شريط الأدوات
        toolbar = QHBoxLayout()

        add_btn = QPushButton("حساب جديد")
        add_btn.clicked.connect(self._add_account)
        toolbar.addWidget(add_btn)

        edit_btn = QPushButton("تعديل")
        edit_btn.clicked.connect(self._edit_account)
        toolbar.addWidget(edit_btn)

        delete_btn = QPushButton("حذف")
        delete_btn.clicked.connect(self._delete_account)
        toolbar.addWidget(delete_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # جدول الحسابات
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels(
            [
                "الرمز",
                "اسم الحساب",
                "النوع",
                "الرصيد الحالي",
                "الجانب الطبيعي",
                "نشط",
                "إجراءات",
            ]
        )

        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.accounts_table)

        return widget

    def _create_journal_tab(self):
        """إنشاء تبويب اليومية العامة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # شريط الأدوات
        toolbar = QHBoxLayout()

        new_entry_btn = QPushButton("قيد جديد")
        new_entry_btn.clicked.connect(self._create_new_entry)
        toolbar.addWidget(new_entry_btn)

        post_btn = QPushButton("ترحيل")
        post_btn.clicked.connect(self._post_entry)
        toolbar.addWidget(post_btn)

        view_btn = QPushButton("عرض")
        view_btn.clicked.connect(self._view_entry)
        toolbar.addWidget(view_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # جدول القيود
        self.journal_table = QTableWidget()
        self.journal_table.setColumnCount(6)
        self.journal_table.setHorizontalHeaderLabels(["رقم القيد", "التاريخ", "الوصف", "مدين", "دائن", "الحالة"])

        self.journal_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.journal_table)

        return widget

    def _create_trial_balance_tab(self):
        """إنشاء تبويب ميزان المراجعة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # معلومات التقرير
        info_layout = QHBoxLayout()

        date_label = QLabel("التاريخ:")
        self.trial_date = QDateEdit()
        self.trial_date.setDate(QDate.currentDate())
        self.trial_date.dateChanged.connect(self._refresh_trial_balance)

        info_layout.addWidget(date_label)
        info_layout.addWidget(self.trial_date)
        info_layout.addStretch()

        layout.addLayout(info_layout)

        # جدول ميزان المراجعة
        self.trial_table = QTableWidget()
        self.trial_table.setColumnCount(4)
        self.trial_table.setHorizontalHeaderLabels(["الرمز", "اسم الحساب", "مدين", "دائن"])

        self.trial_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.trial_table)

        # ملخص ميزان المراجعة
        summary_layout = QHBoxLayout()

        total_debits_label = QLabel("إجمالي المدين: 0.00")
        total_debits_label.setFont(QFont("Arial", 10, QFont.Bold))
        summary_layout.addWidget(total_debits_label)

        total_credits_label = QLabel("إجمالي الدائن: 0.00")
        total_credits_label.setFont(QFont("Arial", 10, QFont.Bold))
        summary_layout.addWidget(total_credits_label)

        summary_layout.addStretch()

        layout.addLayout(summary_layout)

        self.trial_debits_label = total_debits_label
        self.trial_credits_label = total_credits_label

        return widget

    def _create_financial_statements_tab(self):
        """إنشاء تبويب القوائم المالية"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # تبويب داخلي للقوائم المختلفة
        inner_tabs = QTabWidget()

        # الميزانية العمومية
        balance_widget = self._create_balance_sheet_widget()
        inner_tabs.addTab(balance_widget, "الميزانية العمومية")

        # قائمة الدخل
        income_widget = self._create_income_statement_widget()
        inner_tabs.addTab(income_widget, "قائمة الدخل")

        layout.addWidget(inner_tabs)

        return widget

    def _create_balance_sheet_widget(self):
        """إنشاء تقرير الميزانية العمومية"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # جدول الأصول والالتزامات
        self.balance_sheet_table = QTableWidget()
        self.balance_sheet_table.setColumnCount(2)
        self.balance_sheet_table.setHorizontalHeaderLabels(["البيان", "المبلغ"])

        layout.addWidget(self.balance_sheet_table)

        return widget

    def _create_income_statement_widget(self):
        """إنشاء تقرير قائمة الدخل"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # اختيار الفترة
        period_layout = QHBoxLayout()

        start_label = QLabel("من:")
        self.income_start_date = QDateEdit()
        self.income_start_date.setDate(QDate.currentDate().addMonths(-1))

        end_label = QLabel("إلى:")
        self.income_end_date = QDateEdit()
        self.income_end_date.setDate(QDate.currentDate())

        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self._refresh_income_statement)

        period_layout.addWidget(start_label)
        period_layout.addWidget(self.income_start_date)
        period_layout.addWidget(end_label)
        period_layout.addWidget(self.income_end_date)
        period_layout.addWidget(refresh_btn)
        period_layout.addStretch()

        layout.addLayout(period_layout)

        # جدول قائمة الدخل
        self.income_table = QTableWidget()
        self.income_table.setColumnCount(2)
        self.income_table.setHorizontalHeaderLabels(["البيان", "المبلغ"])

        layout.addWidget(self.income_table)

        return widget

    def _load_data(self):
        """تحميل البيانات"""
        self._load_accounts()
        self._load_journal_entries()
        self._refresh_trial_balance()
        self._refresh_balance_sheet()

    def _setup_connections(self):
        """ربط الإشارات بالأحداث (placeholder للتوسيع لاحقاً)"""
        return

    def _load_accounts(self):
        """تحميل قائمة الحسابات"""
        self.accounts_table.setRowCount(0)

        accounts = self.accounting.coa.get_active_accounts()

        for idx, account in enumerate(accounts):
            self.accounts_table.insertRow(idx)

            # الرمز
            code_item = QTableWidgetItem(account.account_code)
            code_item.setData(Qt.ItemDataRole.UserRole, account.id)
            self.accounts_table.setItem(idx, 0, code_item)

            # الاسم
            self.accounts_table.setItem(idx, 1, QTableWidgetItem(account.account_name))

            # النوع
            self.accounts_table.setItem(idx, 2, QTableWidgetItem(account.account_type))

            # الرصيد
            balance_item = QTableWidgetItem(f"{account.current_balance:.2f}")
            self.accounts_table.setItem(idx, 3, balance_item)

            # الجانب الطبيعي
            self.accounts_table.setItem(idx, 4, QTableWidgetItem(account.normal_side))

            # الحالة
            status = "نعم" if account.is_active else "لا"
            self.accounts_table.setItem(idx, 5, QTableWidgetItem(status))

    def _load_journal_entries(self):
        """تحميل قائمة القيود"""
        self.journal_table.setRowCount(0)

        try:
            entries = self.db.fetch_all("""
                SELECT gj.id, gj.entry_number, gj.entry_date, gj.description,
                       gj.is_posted,
                       COALESCE(jt.total_debit, 0) as total_debit,
                       COALESCE(jt.total_credit, 0) as total_credit
                FROM general_journal gj
                LEFT JOIN (
                    SELECT journal_id,
                           SUM(debit_amount) as total_debit,
                           SUM(credit_amount) as total_credit
                    FROM journal_lines
                    GROUP BY journal_id
                ) jt ON gj.id = jt.journal_id
                ORDER BY gj.entry_date DESC
                LIMIT 100
            """)

            for idx, entry in enumerate(entries):
                self.journal_table.insertRow(idx)

                # رقم القيد (مع تخزين المعرف)
                is_dict = isinstance(entry, dict)
                entry_id = entry.get("id") if is_dict else entry[0]
                number_item = QTableWidgetItem(
                    entry.get("entry_number") if is_dict else entry[1]
                )
                number_item.setData(Qt.ItemDataRole.UserRole, entry_id)
                self.journal_table.setItem(idx, 0, number_item)

                # التاريخ
                entry_date = entry.get("entry_date") if is_dict else entry[2]
                self.journal_table.setItem(idx, 1, QTableWidgetItem(str(entry_date)[:10]))

                # الوصف
                desc = entry.get("description") if is_dict else entry[3]
                self.journal_table.setItem(idx, 2, QTableWidgetItem(desc or ""))

                # مدين
                total_debit = entry.get("total_debit") if is_dict else entry[5]
                self.journal_table.setItem(
                    idx, 3, QTableWidgetItem(f"{float(total_debit or 0):.2f}")
                )

                # دائن
                total_credit = entry.get("total_credit") if is_dict else entry[6]
                self.journal_table.setItem(
                    idx, 4, QTableWidgetItem(f"{float(total_credit or 0):.2f}")
                )

                # الحالة
                is_posted = entry.get("is_posted") if is_dict else entry[4]
                status = "مرحل" if is_posted else "بانتظار"
                self.journal_table.setItem(idx, 5, QTableWidgetItem(status))

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تحميل القيود: {e}")

    def _refresh_trial_balance(self):
        """تحديث ميزان المراجعة"""
        self.trial_table.setRowCount(0)

        trial_balance = self.accounting.get_trial_balance()

        if "error" in trial_balance:
            return

        accounts = trial_balance.get("accounts", [])

        for idx, account in enumerate(accounts):
            self.trial_table.insertRow(idx)

            self.trial_table.setItem(idx, 0, QTableWidgetItem(account["account_code"]))

            self.trial_table.setItem(idx, 1, QTableWidgetItem(account["account_name"]))

            debit_item = QTableWidgetItem(f"{account.get('debit', account.get('total_debits', 0)):.2f}")
            self.trial_table.setItem(idx, 2, debit_item)

            credit_item = QTableWidgetItem(f"{account.get('credit', account.get('total_credits', 0)):.2f}")
            self.trial_table.setItem(idx, 3, credit_item)

        # تحديث الملخص
        self.trial_debits_label.setText(f"إجمالي المدين: {trial_balance['total_debits']:.2f}")
        self.trial_credits_label.setText(f"إجمالي الدائن: {trial_balance['total_credits']:.2f}")

    def _refresh_balance_sheet(self):
        """تحديث الميزانية العمومية"""
        position = self.accounting.get_financial_position()

        if "error" in position:
            return

        self.balance_sheet_table.setRowCount(0)

        # الأصول
        row = 0
        self.balance_sheet_table.insertRow(row)
        self.balance_sheet_table.setItem(row, 0, QTableWidgetItem("الأصول"))
        self.balance_sheet_table.setItem(row, 1, QTableWidgetItem(f"{position['assets']:.2f}"))

        # الالتزامات
        row += 1
        self.balance_sheet_table.insertRow(row)
        self.balance_sheet_table.setItem(row, 0, QTableWidgetItem("الالتزامات"))
        self.balance_sheet_table.setItem(row, 1, QTableWidgetItem(f"{position['liabilities']:.2f}"))

        # حقوق الملكية
        row += 1
        self.balance_sheet_table.insertRow(row)
        self.balance_sheet_table.setItem(row, 0, QTableWidgetItem("حقوق الملكية"))
        self.balance_sheet_table.setItem(row, 1, QTableWidgetItem(f"{position['equity']:.2f}"))

    def _refresh_income_statement(self):
        """تحديث قائمة الدخل"""
        start_date = self.income_start_date.date().toPython()
        end_date = self.income_end_date.date().toPython()

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        income = self.accounting.get_income_statement(start_datetime, end_datetime)

        if "error" in income:
            return

        self.income_table.setRowCount(0)

        row = 0
        self.income_table.insertRow(row)
        self.income_table.setItem(row, 0, QTableWidgetItem("إجمالي الإيرادات"))
        self.income_table.setItem(row, 1, QTableWidgetItem(f"{income['total_revenues']:.2f}"))

        row += 1
        self.income_table.insertRow(row)
        self.income_table.setItem(row, 0, QTableWidgetItem("إجمالي المصروفات"))
        self.income_table.setItem(row, 1, QTableWidgetItem(f"{income['total_expenses']:.2f}"))

        row += 1
        self.income_table.insertRow(row)
        self.income_table.setItem(row, 0, QTableWidgetItem("صافي الدخل"))
        self.income_table.setItem(row, 1, QTableWidgetItem(f"{income['net_income']:.2f}"))

    def _add_account(self):
        """إضافة حساب جديد"""
        dialog = AccountDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                account = Account(
                    account_code=data["code"],
                    account_name=data["name"],
                    account_type=data["type"],
                    normal_side=data["side"],
                )
                self.accounting.create_account(account)
                self._load_accounts()
                QMessageBox.information(self, "نجاح", "تم إضافة الحساب بنجاح")
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"خطأ: {e}")

    def _edit_account(self):
        """تعديل حساب محدد"""
        row = self.accounts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار حساب للتعديل")
            return

        item = self.accounts_table.item(row, 0)
        account_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not account_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف الحساب")
            return

        account = self.accounting.coa.get_account_by_id(account_id)
        if not account:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحساب")
            return

        dialog = AccountDialog(self, account=account)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                account.account_code = data["code"]
                account.account_name = data["name"]
                account.account_type = data["type"]
                account.normal_side = data["side"]
                success = self.accounting.update_account(account)
                if success:
                    self._load_accounts()
                    QMessageBox.information(self, "نجاح", "تم تعديل الحساب بنجاح")
                else:
                    QMessageBox.warning(self, "خطأ", "فشل في تعديل الحساب")
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"خطأ في تعديل الحساب: {e}")

    def _delete_account(self):
        """حذف حساب محدد"""
        row = self.accounts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار حساب للحذف")
            return

        item = self.accounts_table.item(row, 0)
        account_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not account_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف الحساب")
            return

        name_item = self.accounts_table.item(row, 1)
        account_name = name_item.text() if name_item else ""

        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف الحساب '{account_name}'؟\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.accounting.delete_account(account_id)
            self._load_accounts()
            QMessageBox.information(self, "نجاح", "تم حذف الحساب بنجاح")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في حذف الحساب: {e}")

    def _create_new_entry(self):
        """إنشاء قيد جديد"""
        dialog = JournalEntryDialog(self, self.accounting)
        if dialog.exec() == QDialog.Accepted:
            try:
                entry = dialog.get_journal_entry()
                entry_id = self.accounting.create_journal_entry(entry)
                if entry_id > 0:
                    QMessageBox.information(self, "نجاح", "تم إنشاء القيد بنجاح")
                    self._load_journal_entries()
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"خطأ: {e}")

    def _post_entry(self):
        """ترحيل قيد محدد"""
        row = self.journal_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار قيد للترحيل")
            return

        item = self.journal_table.item(row, 0)
        entry_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not entry_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف القيد")
            return

        status_item = self.journal_table.item(row, 5)
        if status_item and status_item.text() == "مرحل":
            QMessageBox.information(self, "تنبيه", "هذا القيد مرحل مسبقاً")
            return

        reply = QMessageBox.question(
            self, "تأكيد الترحيل",
            "هل أنت متأكد من ترحيل هذا القيد؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.accounting.post_journal_entry(entry_id)
            self._load_journal_entries()
            QMessageBox.information(self, "نجاح", "تم ترحيل القيد بنجاح")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في ترحيل القيد: {e}")

    def _view_entry(self):
        """عرض تفاصيل قيد محدد"""
        row = self.journal_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار قيد للعرض")
            return

        item = self.journal_table.item(row, 0)
        entry_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not entry_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف القيد")
            return

        try:
            lines = self.accounting.get_journal_lines(entry_id)
            if not lines:
                QMessageBox.information(self, "معلومات", "لا توجد أسطر لهذا القيد")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("تفاصيل القيد")
            dialog.setGeometry(200, 200, 700, 400)

            layout = QVBoxLayout(dialog)

            # معلومات الرأس
            entry_number = item.text()
            entry_date = self.journal_table.item(row, 1).text() if self.journal_table.item(row, 1) else ""
            entry_desc = self.journal_table.item(row, 2).text() if self.journal_table.item(row, 2) else ""

            header = QLabel(
                f"رقم القيد: {entry_number}  |  التاريخ: {entry_date}  |  الوصف: {entry_desc}"
            )
            header.setFont(QFont("Arial", 10, QFont.Bold))
            layout.addWidget(header)

            # جدول الأسطر
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["الحساب", "الرمز", "مدين", "دائن"])
            table.setRowCount(len(lines))
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

            total_debit = Decimal("0")
            total_credit = Decimal("0")

            for i, line in enumerate(lines):
                is_dict = isinstance(line, dict)
                account_name = line.get("account_name", "") if is_dict else (line[3] if len(line) > 3 else "")
                account_code = line.get("account_code", "") if is_dict else (line[2] if len(line) > 2 else "")
                debit = Decimal(str(line.get("debit_amount", 0) if is_dict else (line[4] if len(line) > 4 else 0)))
                credit = Decimal(str(line.get("credit_amount", 0) if is_dict else (line[5] if len(line) > 5 else 0)))

                table.setItem(i, 0, QTableWidgetItem(account_name))
                table.setItem(i, 1, QTableWidgetItem(account_code))
                table.setItem(i, 2, QTableWidgetItem(f"{debit:.2f}"))
                table.setItem(i, 3, QTableWidgetItem(f"{credit:.2f}"))

                total_debit += debit
                total_credit += credit

            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            layout.addWidget(table)

            # الإجماليات
            totals_label = QLabel(
                f"إجمالي المدين: {total_debit:.2f}  |  إجمالي الدائن: {total_credit:.2f}"
            )
            totals_label.setFont(QFont("Arial", 10, QFont.Bold))
            layout.addWidget(totals_label)

            close_btn = QPushButton("إغلاق")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في عرض القيد: {e}")

    def _refresh_all(self):
        """تحديث جميع البيانات"""
        self._load_data()
        QMessageBox.information(self, "نجاح", "تم التحديث بنجاح")

    def _export_data(self):
        """تصدير البيانات إلى ملف CSV"""
        active_tab = self.tabs.currentIndex()

        if active_tab == 0:
            table = self.accounts_table
            default_name = "accounts.csv"
        elif active_tab == 1:
            table = self.journal_table
            default_name = "journal_entries.csv"
        elif active_tab == 2:
            table = self.trial_table
            default_name = "trial_balance.csv"
        elif active_tab == 3:
            # القوائم المالية - تصدير الميزانية العمومية
            table = self.balance_sheet_table
            default_name = "balance_sheet.csv"
        else:
            QMessageBox.warning(self, "تنبيه", "لا يمكن تصدير هذا التبويب")
            return

        if table.rowCount() == 0:
            QMessageBox.information(self, "معلومات", "لا توجد بيانات للتصدير")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ الملف", default_name,
            "ملفات CSV (*.csv);;جميع الملفات (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv_module.writer(f)

                # كتابة الترويسات
                headers = []
                for col in range(table.columnCount()):
                    header_item = table.horizontalHeaderItem(col)
                    headers.append(header_item.text() if header_item else f"عمود {col}")
                writer.writerow(headers)

                # كتابة البيانات
                for row in range(table.rowCount()):
                    row_data = []
                    for col in range(table.columnCount()):
                        cell = table.item(row, col)
                        row_data.append(cell.text() if cell else "")
                    writer.writerow(row_data)

            QMessageBox.information(self, "نجاح", f"تم تصدير البيانات بنجاح إلى:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تصدير البيانات: {e}")


class AccountDialog(QDialog):
    """حوار إضافة/تعديل حساب"""

    def __init__(self, parent=None, account=None):
        super().__init__(parent)
        self.account = account

        if account:
            self.setWindowTitle("تعديل حساب")
        else:
            self.setWindowTitle("حساب جديد")

        self.setGeometry(100, 100, 400, 300)

        layout = QFormLayout()

        self.code_input = QLineEdit()
        layout.addRow("الرمز:", self.code_input)

        self.name_input = QLineEdit()
        layout.addRow("الاسم:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Asset", "Liability", "Equity", "Revenue", "Expense"])
        layout.addRow("النوع:", self.type_combo)

        self.side_combo = QComboBox()
        self.side_combo.addItems(["DEBIT", "CREDIT"])
        layout.addRow("الجانب الطبيعي:", self.side_combo)

        buttons_layout = QHBoxLayout()

        ok_btn = QPushButton("حفظ")
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addRow(buttons_layout)

        self.setLayout(layout)

        # تعبئة البيانات في حالة التعديل
        if account:
            self.code_input.setText(account.account_code)
            self.name_input.setText(account.account_name)

            type_index = self.type_combo.findText(account.account_type)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)

            side_index = self.side_combo.findText(account.normal_side)
            if side_index >= 0:
                self.side_combo.setCurrentIndex(side_index)

    def get_data(self):
        """احصل على البيانات المدخلة"""
        return {
            "code": self.code_input.text(),
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "side": self.side_combo.currentText(),
        }


class JournalEntryDialog(QDialog):
    """حوار إنشاء قيد يومي"""

    def __init__(self, parent=None, accounting_service=None):
        super().__init__(parent)
        self.setWindowTitle("قيد يومي جديد")
        self.setGeometry(100, 100, 600, 500)
        self.accounting = accounting_service

        layout = QVBoxLayout()

        # معلومات القيد
        form_layout = QFormLayout()

        self.description_input = QLineEdit()
        form_layout.addRow("الوصف:", self.description_input)

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow("التاريخ:", self.date_input)

        layout.addLayout(form_layout)

        # أسطر القيد
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(4)
        self.lines_table.setHorizontalHeaderLabels(["الحساب", "الوصف", "مدين", "دائن"])

        layout.addWidget(QLabel("أسطر القيد:"))
        layout.addWidget(self.lines_table)

        # أزرار الأسطر
        lines_buttons = QHBoxLayout()

        add_line_btn = QPushButton("إضافة سطر")
        add_line_btn.clicked.connect(self._add_line)
        lines_buttons.addWidget(add_line_btn)

        remove_line_btn = QPushButton("حذف سطر")
        remove_line_btn.clicked.connect(self._remove_line)
        lines_buttons.addWidget(remove_line_btn)

        lines_buttons.addStretch()

        layout.addLayout(lines_buttons)

        # أزرار التحكم
        buttons_layout = QHBoxLayout()

        ok_btn = QPushButton("حفظ")
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # إضافة سطر واحد كنقطة بداية
        self._add_line()

    def _add_line(self):
        """إضافة سطر جديد"""
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)

    def _remove_line(self):
        """حذف السطر المحدد"""
        row = self.lines_table.currentRow()
        if row >= 0:
            self.lines_table.removeRow(row)

    def get_journal_entry(self) -> JournalEntry:
        """احصل على القيد المدخل"""
        entry = JournalEntry(
            entry_date=datetime.combine(self.date_input.date().toPython(), datetime.min.time()),
            description=self.description_input.text(),
            reference_type="Manual",
        )

        for row in range(self.lines_table.rowCount()):
            # قراءة قيم الخلايا
            account_name_item = self.lines_table.item(row, 0)
            description_item = self.lines_table.item(row, 1)
            debit_item = self.lines_table.item(row, 2)
            credit_item = self.lines_table.item(row, 3)

            account_name = account_name_item.text().strip() if account_name_item else ""
            line_description = description_item.text().strip() if description_item else ""
            debit_text = debit_item.text().strip() if debit_item else ""
            credit_text = credit_item.text().strip() if credit_item else ""

            # تخطي الأسطر الفارغة بالكامل
            if not account_name and not line_description and not debit_text and not credit_text:
                continue

            # تحويل المبالغ
            try:
                debit_amount = Decimal(debit_text) if debit_text else Decimal("0")
            except Exception:
                debit_amount = Decimal("0")

            try:
                credit_amount = Decimal(credit_text) if credit_text else Decimal("0")
            except Exception:
                credit_amount = Decimal("0")

            # تخطي الأسطر التي لا تحتوي على مبالغ
            if debit_amount <= 0 and credit_amount <= 0:
                continue

            # البحث عن الحساب بالاسم في دليل الحسابات
            account = None
            if account_name and self.accounting:
                for acc in self.accounting.coa.accounts.values():
                    if acc.account_name == account_name:
                        account = acc
                        break

            if not account:
                raise ValueError(f"الحساب '{account_name}' غير موجود في دليل الحسابات")

            line = JournalLine(
                account_id=account.id or 0,
                account_code=account.account_code,
                account_name=account.account_name,
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                description=line_description,
            )
            entry.add_line(line)

        # التحقق من وجود أسطر
        if not entry.lines:
            raise ValueError("لا توجد أسطر صالحة في القيد")

        # التحقق من التوازن
        if not entry.is_balanced():
            diff = entry.get_balance_difference()
            side = "المدين" if diff > 0 else "الدائن"
            raise ValueError(
                f"القيد غير متوازن: إجمالي {side} أعلى بمقدار {abs(diff):.2f}"
            )

        return entry
