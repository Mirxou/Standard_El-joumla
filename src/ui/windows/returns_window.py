#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة المرتجعات
Returns Management Window
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit, QMessageBox,
    QHeaderView, QFormLayout, QDateEdit, QGroupBox, QDialogButtonBox,
    QScrollArea, QSplitter, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon, QColor, QFont
from decimal import Decimal
from datetime import datetime, date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.return_service import ReturnService
from models.return_invoice import (
    ReturnInvoice, ReturnItem, ReturnType, 
    ReturnReason, ReturnStatus, RefundMethod
)


class ReturnsWindow(QMainWindow):
    """نافذة إدارة المرتجعات"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.return_service = ReturnService(db_manager)
        self.parent_window = parent
        self.current_return = None
        
        self.setWindowTitle("إدارة المرتجعات")
        self.setGeometry(100, 100, 1400, 800)
        
        self._create_widgets()
        self._setup_connections()
        self._load_returns()
    
    def _create_widgets(self):
        """إنشاء عناصر الواجهة"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # شريط الأدوات
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        # المحتوى الرئيسي
        splitter = QSplitter(Qt.Horizontal)
        
        # القائمة اليسرى
        list_widget = self._create_returns_list()
        splitter.addWidget(list_widget)
        
        # التفاصيل اليمنى
        details_widget = self._create_return_details()
        splitter.addWidget(details_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # شريط الحالة
        status_bar = self._create_status_bar()
        layout.addLayout(status_bar)
    
    def _create_toolbar(self):
        """إنشاء شريط الأدوات"""
        toolbar = QHBoxLayout()
        
        # زر مرتجع جديد
        self.new_return_btn = QPushButton("➕ مرتجع جديد")
        self.new_return_btn.setStyleSheet("background-color: #FF5722; color: white; padding: 8px 16px; font-weight: bold;")
        self.new_return_btn.clicked.connect(self._new_return)
        toolbar.addWidget(self.new_return_btn)
        
        toolbar.addSpacing(10)
        
        # زر موافقة
        self.approve_btn = QPushButton("✅ موافقة")
        self.approve_btn.setEnabled(False)
        self.approve_btn.clicked.connect(self._approve_return)
        toolbar.addWidget(self.approve_btn)
        
        # زر رفض
        self.reject_btn = QPushButton("❌ رفض")
        self.reject_btn.setEnabled(False)
        self.reject_btn.clicked.connect(self._reject_return)
        toolbar.addWidget(self.reject_btn)
        
        # زر إتمام
        self.complete_btn = QPushButton("✔️ إتمام")
        self.complete_btn.setEnabled(False)
        self.complete_btn.clicked.connect(self._complete_return)
        toolbar.addWidget(self.complete_btn)
        
        # زر إلغاء
        self.cancel_btn = QPushButton("🚫 إلغاء")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_return)
        toolbar.addWidget(self.cancel_btn)
        
        toolbar.addSpacing(20)
        
        # زر إشعار دائن
        self.credit_note_btn = QPushButton("📄 إشعار دائن")
        self.credit_note_btn.setEnabled(False)
        self.credit_note_btn.clicked.connect(self._generate_credit_note)
        toolbar.addWidget(self.credit_note_btn)
        
        toolbar.addStretch()
        
        # فلتر النوع
        toolbar.addWidget(QLabel("النوع:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("الكل", None)
        for rtype in ReturnType:
            self.type_filter.addItem(rtype.value, rtype)
        self.type_filter.currentIndexChanged.connect(self._filter_returns)
        toolbar.addWidget(self.type_filter)
        
        # فلتر الحالة
        toolbar.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("الكل", None)
        for status in ReturnStatus:
            self.status_filter.addItem(status.value, status)
        self.status_filter.currentIndexChanged.connect(self._filter_returns)
        toolbar.addWidget(self.status_filter)
        
        # زر تحديث
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self._load_returns)
        toolbar.addWidget(refresh_btn)
        
        return toolbar
    
    def _create_returns_list(self):
        """إنشاء قائمة المرتجعات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("<b>المرتجعات</b>"))
        
        self.returns_table = QTableWidget()
        self.returns_table.setColumnCount(7)
        self.returns_table.setHorizontalHeaderLabels([
            "الرقم", "النوع", "العميل/المورد", "التاريخ", "المبلغ", "طريقة الاسترداد", "الحالة"
        ])
        self.returns_table.horizontalHeader().setStretchLastSection(True)
        self.returns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.returns_table.setSelectionMode(QTableWidget.SingleSelection)
        self.returns_table.setAlternatingRowColors(True)
        self.returns_table.itemSelectionChanged.connect(self._on_return_selected)
        
        layout.addWidget(self.returns_table)
        
        return widget
    
    def _create_return_details(self):
        """إنشاء منطقة تفاصيل المرتجع"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # معلومات المرتجع الأساسية
        info_group = QGroupBox("معلومات المرتجع")
        info_layout = QFormLayout()
        
        self.return_number_label = QLabel("-")
        self.return_type_label = QLabel("-")
        self.return_status_label = QLabel("-")
        self.contact_name_label = QLabel("-")
        self.contact_phone_label = QLabel("-")
        self.return_date_label = QLabel("-")
        self.original_invoice_label = QLabel("-")
        self.return_reason_label = QLabel("-")
        
        info_layout.addRow("رقم المرتجع:", self.return_number_label)
        info_layout.addRow("النوع:", self.return_type_label)
        info_layout.addRow("الحالة:", self.return_status_label)
        info_layout.addRow("العميل/المورد:", self.contact_name_label)
        info_layout.addRow("الهاتف:", self.contact_phone_label)
        info_layout.addRow("التاريخ:", self.return_date_label)
        info_layout.addRow("الفاتورة الأصلية:", self.original_invoice_label)
        info_layout.addRow("السبب:", self.return_reason_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # بنود المرتجع
        items_group = QGroupBox("بنود المرتجع")
        items_layout = QVBoxLayout()
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "المنتج", "الكمية المرتجعة", "الكمية الأصلية", "السعر", "السبب", "قابل للتخزين"
        ])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        
        items_layout.addWidget(self.items_table)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)
        
        # معلومات الاسترداد
        refund_group = QGroupBox("معلومات الاسترداد")
        refund_layout = QFormLayout()
        
        self.refund_method_label = QLabel("-")
        self.refund_amount_label = QLabel("0.00")
        self.refund_date_label = QLabel("-")
        self.refund_reference_label = QLabel("-")
        self.credit_note_label = QLabel("-")
        
        refund_layout.addRow("طريقة الاسترداد:", self.refund_method_label)
        refund_layout.addRow("المبلغ المسترد:", self.refund_amount_label)
        refund_layout.addRow("تاريخ الاسترداد:", self.refund_date_label)
        refund_layout.addRow("المرجع:", self.refund_reference_label)
        refund_layout.addRow("إشعار دائن:", self.credit_note_label)
        
        refund_group.setLayout(refund_layout)
        layout.addWidget(refund_group)
        
        # المجاميع
        totals_group = QGroupBox("المجاميع")
        totals_layout = QFormLayout()
        
        self.total_label = QLabel("0.00")
        total_font = QFont()
        total_font.setBold(True)
        total_font.setPointSize(12)
        self.total_label.setFont(total_font)
        
        totals_layout.addRow("إجمالي المرتجع:", self.total_label)
        
        totals_group.setLayout(totals_layout)
        layout.addWidget(totals_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_status_bar(self):
        """إنشاء شريط الحالة"""
        layout = QHBoxLayout()
        
        self.total_returns_label = QLabel("إجمالي المرتجعات: 0")
        self.total_value_label = QLabel("القيمة الإجمالية: 0.00")
        self.total_refunded_label = QLabel("المبلغ المسترد: 0.00")
        
        layout.addWidget(self.total_returns_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.total_value_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.total_refunded_label)
        layout.addStretch()
        
        return layout
    
    def _setup_connections(self):
        """ربط الإشارات"""
        pass
    
    def _load_returns(self):
        """تحميل المرتجعات"""
        try:
            # الحصول على الفلاتر
            return_type = self.type_filter.currentData()
            status = self.status_filter.currentData()
            
            # تحميل المرتجعات
            returns = self.return_service.get_all_returns(
                return_type=return_type,
                status=status
            )
            
            # تحديث الجدول
            self.returns_table.setRowCount(0)
            
            for ret in returns:
                row = self.returns_table.rowCount()
                self.returns_table.insertRow(row)
                
                # الرقم
                self.returns_table.setItem(row, 0, QTableWidgetItem(ret.return_number))
                
                # النوع
                type_item = QTableWidgetItem(ret.return_type.value)
                type_color = "#FFEBEE" if ret.is_sale_return else "#E3F2FD"
                type_item.setBackground(QColor(type_color))
                self.returns_table.setItem(row, 1, type_item)
                
                # العميل/المورد
                contact = ret.contact_name or "-"
                self.returns_table.setItem(row, 2, QTableWidgetItem(contact))
                
                # التاريخ
                date_str = ret.return_date.strftime("%Y-%m-%d") if ret.return_date else "-"
                self.returns_table.setItem(row, 3, QTableWidgetItem(date_str))
                
                # المبلغ
                amount_item = QTableWidgetItem(f"{float(ret.total_amount):,.2f}")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.returns_table.setItem(row, 4, amount_item)
                
                # طريقة الاسترداد
                refund_text = ret.refund_method.value if ret.refund_method else "-"
                self.returns_table.setItem(row, 5, QTableWidgetItem(refund_text))
                
                # الحالة
                status_item = QTableWidgetItem(ret.status.value)
                status_color = self._get_status_color(ret.status)
                status_item.setBackground(QColor(status_color))
                self.returns_table.setItem(row, 6, status_item)
                
                # حفظ المعرف
                self.returns_table.item(row, 0).setData(Qt.UserRole, ret.id)
            
            # تحديث الإحصائيات
            self._update_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل المرتجعات:\n{str(e)}")
    
    def _filter_returns(self):
        """فلترة المرتجعات"""
        self._load_returns()
    
    def _on_return_selected(self):
        """عند اختيار مرتجع"""
        selected_rows = self.returns_table.selectedItems()
        if not selected_rows:
            self._clear_details()
            self._update_buttons(None)
            return
        
        # الحصول على المعرف
        return_id = self.returns_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        
        # تحميل التفاصيل
        ret = self.return_service.get_return(return_id)
        if ret:
            self.current_return = ret
            self._display_return_details(ret)
            self._update_buttons(ret)
    
    def _display_return_details(self, ret: ReturnInvoice):
        """عرض تفاصيل المرتجع"""
        # معلومات أساسية
        self.return_number_label.setText(ret.return_number)
        self.return_type_label.setText(ret.return_type.value)
        
        status_text = f"<b style='color: {self._get_status_text_color(ret.status)}'>{ret.status.value}</b>"
        self.return_status_label.setText(status_text)
        
        self.contact_name_label.setText(ret.contact_name or "-")
        self.contact_phone_label.setText(ret.contact_phone or "-")
        self.return_date_label.setText(ret.return_date.strftime("%Y-%m-%d") if ret.return_date else "-")
        self.original_invoice_label.setText(ret.original_invoice_number or "-")
        self.return_reason_label.setText(ret.return_reason.value if ret.return_reason else "-")
        
        # البنود
        self.items_table.setRowCount(0)
        for item in ret.items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            
            self.items_table.setItem(row, 0, QTableWidgetItem(item.product_name))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(float(item.quantity_returned))))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(float(item.quantity_original))))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{float(item.unit_price):,.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(item.return_reason.value if item.return_reason else "-"))
            
            restockable = "نعم" if item.restockable else "لا"
            restockable_item = QTableWidgetItem(restockable)
            if item.restockable:
                restockable_item.setBackground(QColor("#C8E6C9"))
            else:
                restockable_item.setBackground(QColor("#FFCDD2"))
            self.items_table.setItem(row, 5, restockable_item)
        
        # معلومات الاسترداد
        self.refund_method_label.setText(ret.refund_method.value if ret.refund_method else "-")
        self.refund_amount_label.setText(f"{float(ret.refund_amount):,.2f} ريال")
        self.refund_date_label.setText(ret.refund_date.strftime("%Y-%m-%d") if ret.refund_date else "-")
        self.refund_reference_label.setText(ret.refund_reference or "-")
        self.credit_note_label.setText(ret.credit_note_number or "-")
        
        # المجموع
        self.total_label.setText(f"{float(ret.total_amount):,.2f} ريال")
    
    def _clear_details(self):
        """مسح التفاصيل"""
        self.current_return = None
        self.return_number_label.setText("-")
        self.return_type_label.setText("-")
        self.return_status_label.setText("-")
        self.contact_name_label.setText("-")
        self.contact_phone_label.setText("-")
        self.return_date_label.setText("-")
        self.original_invoice_label.setText("-")
        self.return_reason_label.setText("-")
        self.items_table.setRowCount(0)
        self.refund_method_label.setText("-")
        self.refund_amount_label.setText("0.00")
        self.refund_date_label.setText("-")
        self.refund_reference_label.setText("-")
        self.credit_note_label.setText("-")
        self.total_label.setText("0.00")
    
    def _update_buttons(self, ret: ReturnInvoice):
        """تحديث حالة الأزرار"""
        if not ret:
            self.approve_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.complete_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.credit_note_btn.setEnabled(False)
            return
        
        self.approve_btn.setEnabled(ret.can_approve)
        self.reject_btn.setEnabled(ret.status == ReturnStatus.PENDING)
        self.complete_btn.setEnabled(ret.can_complete)
        self.cancel_btn.setEnabled(ret.status in [ReturnStatus.PENDING, ReturnStatus.APPROVED])
        self.credit_note_btn.setEnabled(ret.status == ReturnStatus.APPROVED and not ret.credit_note_number)
    
    def _update_statistics(self):
        """تحديث الإحصائيات"""
        try:
            stats = self.return_service.get_return_statistics()
            
            self.total_returns_label.setText(f"إجمالي المرتجعات: {stats.get('total_count', 0)}")
            self.total_value_label.setText(f"القيمة الإجمالية: {stats.get('total_value', 0):,.2f} ريال")
            self.total_refunded_label.setText(f"المبلغ المسترد: {stats.get('total_refunded', 0):,.2f} ريال")
            
        except Exception as e:
            print(f"خطأ في تحديث الإحصائيات: {e}")
    
    def _get_status_color(self, status: ReturnStatus) -> str:
        """الحصول على لون الحالة"""
        colors = {
            ReturnStatus.PENDING: "#FFF9C4",
            ReturnStatus.APPROVED: "#C8E6C9",
            ReturnStatus.REJECTED: "#FFCDD2",
            ReturnStatus.COMPLETED: "#B2DFDB",
            ReturnStatus.CANCELLED: "#CFD8DC"
        }
        return colors.get(status, "#FFFFFF")
    
    def _get_status_text_color(self, status: ReturnStatus) -> str:
        """الحصول على لون نص الحالة"""
        colors = {
            ReturnStatus.PENDING: "#F57C00",
            ReturnStatus.APPROVED: "#388E3C",
            ReturnStatus.REJECTED: "#D32F2F",
            ReturnStatus.COMPLETED: "#00796B",
            ReturnStatus.CANCELLED: "#616161"
        }
        return colors.get(status, "#000000")
    
    def _new_return(self):
        """إنشاء مرتجع جديد"""
        dialog = ReturnFormDialog(self.db, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_returns()
            QMessageBox.information(self, "نجاح", "تم إنشاء المرتجع بنجاح")
    
    def _approve_return(self):
        """الموافقة على مرتجع"""
        if not self.current_return:
            return
        
        if self.return_service.approve_return(self.current_return.id, approved_by=1):
            self._load_returns()
            self._on_return_selected()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على المرتجع")
        else:
            QMessageBox.critical(self, "خطأ", "فشل الموافقة على المرتجع")
    
    def _reject_return(self):
        """رفض مرتجع"""
        if not self.current_return:
            return
        
        reply = QMessageBox.question(
            self, "تأكيد الرفض",
            "هل أنت متأكد من رفض المرتجع؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.return_service.reject_return(self.current_return.id):
                self._load_returns()
                self._on_return_selected()
                QMessageBox.information(self, "تم الرفض", "تم رفض المرتجع")
            else:
                QMessageBox.critical(self, "خطأ", "فشل رفض المرتجع")
    
    def _complete_return(self):
        """إتمام مرتجع"""
        if not self.current_return:
            return
        
        reply = QMessageBox.question(
            self, "تأكيد الإتمام",
            "هل أنت متأكد من إتمام المرتجع؟\nسيتم تحديث المخزون للبنود القابلة لإعادة التخزين.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.return_service.complete_return(self.current_return.id):
                self._load_returns()
                self._on_return_selected()
                QMessageBox.information(self, "نجاح", "تم إتمام المرتجع بنجاح")
            else:
                QMessageBox.critical(self, "خطأ", "فشل إتمام المرتجع")
    
    def _cancel_return(self):
        """إلغاء مرتجع"""
        if not self.current_return:
            return
        
        reply = QMessageBox.question(
            self, "تأكيد الإلغاء",
            "هل أنت متأكد من إلغاء المرتجع؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.return_service.cancel_return(self.current_return.id):
                self._load_returns()
                self._on_return_selected()
                QMessageBox.information(self, "تم الإلغاء", "تم إلغاء المرتجع")
            else:
                QMessageBox.critical(self, "خطأ", "فشل إلغاء المرتجع")
    
    def _generate_credit_note(self):
        """إنشاء إشعار دائن"""
        if not self.current_return:
            return
        
        credit_note_number = self.return_service.generate_credit_note(self.current_return.id)
        if credit_note_number:
            self._load_returns()
            self._on_return_selected()
            QMessageBox.information(
                self, "نجاح",
                f"تم إنشاء إشعار دائن بنجاح\nالرقم: {credit_note_number}"
            )
        else:
            QMessageBox.critical(self, "خطأ", "فشل إنشاء إشعار دائن")


class ReturnFormDialog(QDialog):
    """نافذة إضافة مرتجع"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.return_service = ReturnService(db_manager)
        
        self.setWindowTitle("مرتجع جديد")
        self.setMinimumWidth(600)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """إنشاء عناصر النافذة"""
        layout = QVBoxLayout(self)
        
        # نوع المرتجع
        type_group = QGroupBox("نوع المرتجع")
        type_layout = QHBoxLayout()
        
        self.return_type = QComboBox()
        for rtype in ReturnType:
            self.return_type.addItem(rtype.value, rtype)
        
        type_layout.addWidget(QLabel("النوع:"))
        type_layout.addWidget(self.return_type)
        type_layout.addStretch()
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # معلومات الجهة
        contact_group = QGroupBox("معلومات العميل/المورد")
        contact_layout = QFormLayout()
        
        self.contact_name = QLineEdit()
        self.contact_phone = QLineEdit()
        self.original_invoice = QLineEdit()
        
        contact_layout.addRow("الاسم*:", self.contact_name)
        contact_layout.addRow("الهاتف:", self.contact_phone)
        contact_layout.addRow("رقم الفاتورة الأصلية:", self.original_invoice)
        
        contact_group.setLayout(contact_layout)
        layout.addWidget(contact_group)
        
        # معلومات المرتجع
        return_group = QGroupBox("معلومات المرتجع")
        return_layout = QFormLayout()
        
        self.return_date = QDateEdit()
        self.return_date.setDate(QDate.currentDate())
        self.return_date.setCalendarPopup(True)
        
        self.return_reason = QComboBox()
        for reason in ReturnReason:
            self.return_reason.addItem(reason.value, reason)
        
        self.refund_method = QComboBox()
        for method in RefundMethod:
            self.refund_method.addItem(method.value, method)
        
        return_layout.addRow("تاريخ الإرجاع*:", self.return_date)
        return_layout.addRow("سبب الإرجاع*:", self.return_reason)
        return_layout.addRow("طريقة الاسترداد:", self.refund_method)
        
        return_group.setLayout(return_layout)
        layout.addWidget(return_group)
        
        # ملاحظة
        note = QLabel("ملاحظة: لإضافة بنود المرتجع، يرجى حفظ المرتجع أولاً ثم تعديله")
        note.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(note)
        
        # أزرار
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _save(self):
        """حفظ المرتجع"""
        if not self.contact_name.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم العميل/المورد")
            return
        
        try:
            ret = ReturnInvoice(
                return_type=self.return_type.currentData(),
                contact_name=self.contact_name.text().strip(),
                contact_phone=self.contact_phone.text().strip(),
                original_invoice_number=self.original_invoice.text().strip(),
                return_reason=self.return_reason.currentData(),
                refund_method=self.refund_method.currentData()
            )
            
            r_date = self.return_date.date()
            ret.return_date = date(r_date.year(), r_date.month(), r_date.day())
            
            # إضافة بند تجريبي
            ret.add_item(ReturnItem(
                product_id=1,
                product_name="منتج افتراضي",
                quantity_returned=Decimal('1'),
                quantity_original=Decimal('1'),
                unit_price=Decimal('100.00'),
                return_reason=self.return_reason.currentData(),
                restockable=True
            ))
            
            if self.return_service.create_return(ret):
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل إنشاء المرتجع")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ:\n{str(e)}")
