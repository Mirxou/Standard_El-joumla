#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة المحاسبة
Accounting Management Window

توفر واجهة شاملة لإدارة الحسابات والقيود المحاسبية والقوائم المالية
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QLabel,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit,
    QMessageBox, QHeaderView, QFormLayout, QDateEdit, QGroupBox,
    QScrollArea
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QIcon, QColor, QFont
from decimal import Decimal
from datetime import datetime

from ...services.accounting_service import AccountingService
from ...models.account import Account
from ...models.journal_entry import JournalEntry, JournalLine


class AccountingWindow(QMainWindow):
    """نافذة إدارة المحاسبة"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.accounting = AccountingService(db_manager)
        self.parent_window = parent
        
        self.setWindowTitle("إدارة المحاسبة")
        self.setWindowIcon(QIcon("assets/icons/accounting.png"))
        self.setGeometry(100, 100, 1200, 700)
        
        self._create_widgets()
        self._setup_connections()
        self._load_data()
    
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
        self.accounts_table.setHorizontalHeaderLabels([
            "الرمز", "اسم الحساب", "النوع", "الرصيد الحالي",
            "الجانب الطبيعي", "نشط", "إجراءات"
        ])
        
        self.accounts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        
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
        self.journal_table.setHorizontalHeaderLabels([
            "رقم القيد", "التاريخ", "الوصف", "مدين", "دائن", "الحالة"
        ])
        
        self.journal_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        
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
        self.trial_table.setHorizontalHeaderLabels([
            "الرمز", "اسم الحساب", "مدين", "دائن"
        ])
        
        self.trial_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        
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
        self.balance_sheet_table.setHorizontalHeaderLabels([
            "البيان", "المبلغ"
        ])
        
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
        self.income_table.setHorizontalHeaderLabels([
            "البيان", "المبلغ"
        ])
        
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
            self.accounts_table.setItem(
                idx, 0, QTableWidgetItem(account.account_code)
            )
            
            # الاسم
            self.accounts_table.setItem(
                idx, 1, QTableWidgetItem(account.account_name)
            )
            
            # النوع
            self.accounts_table.setItem(
                idx, 2, QTableWidgetItem(account.account_type)
            )
            
            # الرصيد
            balance_item = QTableWidgetItem(f"{account.current_balance:.2f}")
            self.accounts_table.setItem(idx, 3, balance_item)
            
            # الجانب الطبيعي
            self.accounts_table.setItem(
                idx, 4, QTableWidgetItem(account.normal_side)
            )
            
            # الحالة
            status = "نعم" if account.is_active else "لا"
            self.accounts_table.setItem(
                idx, 5, QTableWidgetItem(status)
            )
    
    def _load_journal_entries(self):
        """تحميل قائمة القيود"""
        self.journal_table.setRowCount(0)
        
        try:
            entries = self.db.fetch_all("""
                SELECT id, entry_number, entry_date, description,
                       is_posted
                FROM general_journal
                ORDER BY entry_date DESC
                LIMIT 100
            """)
            
            for idx, entry in enumerate(entries):
                self.journal_table.insertRow(idx)
                
                # رقم القيد
                self.journal_table.setItem(
                    idx, 0, QTableWidgetItem(entry[1])
                )
                
                # التاريخ
                self.journal_table.setItem(
                    idx, 1, QTableWidgetItem(str(entry[2])[:10])
                )
                
                # الوصف
                self.journal_table.setItem(
                    idx, 2, QTableWidgetItem(entry[3] or "")
                )
                
                # الحالة
                status = "مرحل" if entry[4] else "بانتظار"
                self.journal_table.setItem(
                    idx, 5, QTableWidgetItem(status)
                )
        
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
            
            self.trial_table.setItem(
                idx, 0, QTableWidgetItem(account["account_code"])
            )
            
            self.trial_table.setItem(
                idx, 1, QTableWidgetItem(account["account_name"])
            )
            
            debit_item = QTableWidgetItem(f"{account['debit']:.2f}")
            self.trial_table.setItem(idx, 2, debit_item)
            
            credit_item = QTableWidgetItem(f"{account['credit']:.2f}")
            self.trial_table.setItem(idx, 3, credit_item)
        
        # تحديث الملخص
        self.trial_debits_label.setText(
            f"إجمالي المدين: {trial_balance['total_debits']:.2f}"
        )
        self.trial_credits_label.setText(
            f"إجمالي الدائن: {trial_balance['total_credits']:.2f}"
        )
    
    def _refresh_balance_sheet(self):
        """تحديث الميزانية العمومية"""
        position = self.accounting.get_financial_position()
        
        if "error" in position:
            return
        
        self.balance_sheet_table.setRowCount(0)
        
        # الأصول
        row = 0
        self.balance_sheet_table.insertRow(row)
        self.balance_sheet_table.setItem(
            row, 0, QTableWidgetItem("الأصول")
        )
        self.balance_sheet_table.setItem(
            row, 1, QTableWidgetItem(f"{position['assets']:.2f}")
        )
        
        # الالتزامات
        row += 1
        self.balance_sheet_table.insertRow(row)
        self.balance_sheet_table.setItem(
            row, 0, QTableWidgetItem("الالتزامات")
        )
        self.balance_sheet_table.setItem(
            row, 1, QTableWidgetItem(f"{position['liabilities']:.2f}")
        )
        
        # حقوق الملكية
        row += 1
        self.balance_sheet_table.insertRow(row)
        self.balance_sheet_table.setItem(
            row, 0, QTableWidgetItem("حقوق الملكية")
        )
        self.balance_sheet_table.setItem(
            row, 1, QTableWidgetItem(f"{position['equity']:.2f}")
        )
    
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
        self.income_table.setItem(
            row, 0, QTableWidgetItem("إجمالي الإيرادات")
        )
        self.income_table.setItem(
            row, 1, QTableWidgetItem(f"{income['total_revenues']:.2f}")
        )
        
        row += 1
        self.income_table.insertRow(row)
        self.income_table.setItem(
            row, 0, QTableWidgetItem("إجمالي المصروفات")
        )
        self.income_table.setItem(
            row, 1, QTableWidgetItem(f"{income['total_expenses']:.2f}")
        )
        
        row += 1
        self.income_table.insertRow(row)
        self.income_table.setItem(
            row, 0, QTableWidgetItem("صافي الدخل")
        )
        self.income_table.setItem(
            row, 1, QTableWidgetItem(f"{income['net_income']:.2f}")
        )
    
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
                    normal_side=data["side"]
                )
                self.accounting.create_account(account)
                self._load_accounts()
                QMessageBox.information(self, "نجاح", "تم إضافة الحساب بنجاح")
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"خطأ: {e}")
    
    def _edit_account(self):
        """تعديل حساب"""
        QMessageBox.information(self, "تعديل", "ميزة التعديل قريبًا")
    
    def _delete_account(self):
        """حذف حساب"""
        QMessageBox.information(self, "حذف", "ميزة الحذف قريبًا")
    
    def _create_new_entry(self):
        """إنشاء قيد جديد"""
        dialog = JournalEntryDialog(self, self.accounting)
        if dialog.exec() == QDialog.Accepted:
            entry = dialog.get_journal_entry()
            try:
                entry_id = self.accounting.create_journal_entry(entry)
                if entry_id > 0:
                    QMessageBox.information(self, "نجاح", "تم إنشاء القيد بنجاح")
                    self._load_journal_entries()
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"خطأ: {e}")
    
    def _post_entry(self):
        """ترحيل قيد"""
        QMessageBox.information(self, "ترحيل", "ميزة الترحيل قريبًا")
    
    def _view_entry(self):
        """عرض قيد"""
        QMessageBox.information(self, "عرض", "ميزة العرض قريبًا")
    
    def _refresh_all(self):
        """تحديث جميع البيانات"""
        self._load_data()
        QMessageBox.information(self, "نجاح", "تم التحديث بنجاح")
    
    def _export_data(self):
        """تصدير البيانات"""
        QMessageBox.information(self, "تصدير", "ميزة التصدير قريبًا")


class AccountDialog(QDialog):
    """حوار إضافة/تعديل حساب"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("حساب جديد")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QFormLayout()
        
        self.code_input = QLineEdit()
        layout.addRow("الرمز:", self.code_input)
        
        self.name_input = QLineEdit()
        layout.addRow("الاسم:", self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Asset", "Liability", "Equity", "Revenue", "Expense"
        ])
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
    
    def get_data(self):
        """احصل على البيانات المدخلة"""
        return {
            "code": self.code_input.text(),
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "side": self.side_combo.currentText()
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
        self.lines_table.setHorizontalHeaderLabels([
            "الحساب", "الوصف", "مدين", "دائن"
        ])
        
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
            entry_date=datetime.combine(
                self.date_input.date().toPython(),
                datetime.min.time()
            ),
            description=self.description_input.text(),
            reference_type="Manual"
        )
        
        # إضافة الأسطر (تطبيق بسيط)
        # سيتم تحسينها لاحقًا
        
        return entry
