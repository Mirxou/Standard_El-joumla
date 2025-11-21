#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة حوار إنشاء/تحرير أمر الشراء
Purchase Order Create/Edit Dialog
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QDoubleSpinBox,
    QMessageBox, QHeaderView, QSpinBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from decimal import Decimal
from datetime import datetime, date, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.purchase_order import (
    PurchaseOrder, PurchaseOrderItem, POStatus,
    POPriority, DeliveryTerms, PaymentTerms
)


class PurchaseOrderDialog(QDialog):
    """نافذة إنشاء/تحرير أمر شراء"""
    
    def __init__(self, db_manager, po=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.po = po
        self.is_edit_mode = po is not None
        self.items = []
        
        self.setWindowTitle("تحرير أمر الشراء" if self.is_edit_mode else "أمر شراء جديد")
        self.setMinimumSize(1200, 700)
        
        self._load_data()
        self._create_widgets()
        self._setup_connections()
        
        if self.is_edit_mode:
            self._load_po_data()
    
    def _load_data(self):
        """تحميل البيانات المطلوبة"""
        # تحميل الموردين
        try:
            query = "SELECT id, name FROM suppliers ORDER BY name"
            self.suppliers = self.db.execute_query(query)
        except:
            self.suppliers = []
        
        # تحميل المنتجات
        try:
            query = "SELECT id, name, code, unit_price FROM products ORDER BY name"
            self.products = self.db.execute_query(query)
        except:
            self.products = []
    
    def _create_widgets(self):
        """إنشاء عناصر الواجهة"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # معلومات أساسية
        basic_group = self._create_basic_info_group()
        layout.addWidget(basic_group)
        
        # البنود
        items_group = self._create_items_group()
        layout.addWidget(items_group)
        
        # الملاحظات والشروط
        notes_group = self._create_notes_group()
        layout.addWidget(notes_group)
        
        # الملخص المالي
        summary_group = self._create_summary_group()
        layout.addWidget(summary_group)
        
        # الأزرار
        buttons = self._create_buttons()
        layout.addLayout(buttons)
    
    def _create_basic_info_group(self):
        """مجموعة المعلومات الأساسية"""
        group = QGroupBox("المعلومات الأساسية")
        layout = QFormLayout(group)
        
        # المورد
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("-- اختر المورد --", None)
        for supplier_id, name in self.suppliers:
            self.supplier_combo.addItem(name, supplier_id)
        self.supplier_combo.currentIndexChanged.connect(self._on_supplier_changed)
        layout.addRow("<b>المورد:</b>", self.supplier_combo)
        
        # جهة الاتصال
        self.contact_edit = QLineEdit()
        layout.addRow("جهة الاتصال:", self.contact_edit)
        
        # التواريخ
        date_layout = QHBoxLayout()
        
        self.order_date = QDateEdit()
        self.order_date.setDate(QDate.currentDate())
        self.order_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("تاريخ الأمر:"))
        date_layout.addWidget(self.order_date)
        
        date_layout.addSpacing(20)
        
        self.required_date = QDateEdit()
        self.required_date.setDate(QDate.currentDate().addDays(30))
        self.required_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("التاريخ المطلوب:"))
        date_layout.addWidget(self.required_date)
        
        layout.addRow("", date_layout)
        
        # الأولوية والعملة
        priority_layout = QHBoxLayout()
        
        self.priority_combo = QComboBox()
        for priority in POPriority:
            self.priority_combo.addItem(priority.value, priority)
        self.priority_combo.setCurrentIndex(1)  # NORMAL
        priority_layout.addWidget(QLabel("الأولوية:"))
        priority_layout.addWidget(self.priority_combo)
        
        priority_layout.addSpacing(20)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["SAR", "USD", "EUR", "AED"])
        priority_layout.addWidget(QLabel("العملة:"))
        priority_layout.addWidget(self.currency_combo)
        
        layout.addRow("", priority_layout)
        
        # شروط التسليم والدفع
        terms_layout = QHBoxLayout()
        
        self.delivery_terms_combo = QComboBox()
        for term in DeliveryTerms:
            self.delivery_terms_combo.addItem(term.value, term)
        terms_layout.addWidget(QLabel("شروط التسليم:"))
        terms_layout.addWidget(self.delivery_terms_combo)
        
        terms_layout.addSpacing(20)
        
        self.payment_terms_combo = QComboBox()
        for term in PaymentTerms:
            self.payment_terms_combo.addItem(term.value, term)
        terms_layout.addWidget(QLabel("شروط الدفع:"))
        terms_layout.addWidget(self.payment_terms_combo)
        
        layout.addRow("", terms_layout)
        
        return group
    
    def _create_items_group(self):
        """مجموعة البنود"""
        group = QGroupBox("البنود")
        layout = QVBoxLayout(group)
        
        # أزرار إدارة البنود
        buttons_layout = QHBoxLayout()
        
        add_item_btn = QPushButton("➕ إضافة منتج")
        add_item_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px; font-weight: bold;")
        add_item_btn.clicked.connect(self._add_item)
        buttons_layout.addWidget(add_item_btn)
        
        remove_item_btn = QPushButton("➖ حذف البند")
        remove_item_btn.setStyleSheet("background-color: #F44336; color: white; padding: 8px 16px; font-weight: bold;")
        remove_item_btn.clicked.connect(self._remove_item)
        buttons_layout.addWidget(remove_item_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # جدول البنود
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(9)
        self.items_table.setHorizontalHeaderLabels([
            "المنتج", "الكود", "الكمية", "السعر",
            "الخصم%", "الضريبة%", "المجموع الفرعي", "الصافي", ""
        ])
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.items_table.setMinimumHeight(250)
        layout.addWidget(self.items_table)
        
        return group
    
    def _create_notes_group(self):
        """مجموعة الملاحظات"""
        group = QGroupBox("الملاحظات والشروط")
        layout = QHBoxLayout(group)
        
        # الملاحظات
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel("ملاحظات:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        layout.addLayout(notes_layout)
        
        # الشروط والأحكام
        terms_layout = QVBoxLayout()
        terms_layout.addWidget(QLabel("الشروط والأحكام:"))
        self.terms_edit = QTextEdit()
        self.terms_edit.setMaximumHeight(80)
        terms_layout.addWidget(self.terms_edit)
        layout.addLayout(terms_layout)
        
        return group
    
    def _create_summary_group(self):
        """مجموعة الملخص المالي"""
        group = QGroupBox("الملخص المالي")
        layout = QFormLayout(group)
        
        # المجموع الفرعي
        self.subtotal_label = QLabel("0.00")
        self.subtotal_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addRow("المجموع الفرعي:", self.subtotal_label)
        
        # الخصم
        discount_layout = QHBoxLayout()
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setMaximum(999999.99)
        self.discount_spin.setPrefix("- ")
        self.discount_spin.setSuffix(" ريال")
        self.discount_spin.valueChanged.connect(self._calculate_totals)
        discount_layout.addWidget(self.discount_spin)
        layout.addRow("الخصم:", discount_layout)
        
        # الضريبة
        tax_layout = QHBoxLayout()
        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setMaximum(999999.99)
        self.tax_spin.setPrefix("+ ")
        self.tax_spin.setSuffix(" ريال")
        self.tax_spin.valueChanged.connect(self._calculate_totals)
        tax_layout.addWidget(self.tax_spin)
        layout.addRow("الضريبة:", tax_layout)
        
        # الشحن
        shipping_layout = QHBoxLayout()
        self.shipping_spin = QDoubleSpinBox()
        self.shipping_spin.setMaximum(999999.99)
        self.shipping_spin.setPrefix("+ ")
        self.shipping_spin.setSuffix(" ريال")
        self.shipping_spin.valueChanged.connect(self._calculate_totals)
        shipping_layout.addWidget(self.shipping_spin)
        layout.addRow("الشحن:", shipping_layout)
        
        # الإجمالي
        self.total_label = QLabel("0.00")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976D2;")
        layout.addRow("<b>الإجمالي:</b>", self.total_label)
        
        return group
    
    def _create_buttons(self):
        """أزرار الحوار"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px 30px; font-weight: bold; font-size: 14px;")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖️ إلغاء")
        cancel_btn.setStyleSheet("background-color: #757575; color: white; padding: 10px 30px; font-weight: bold; font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        return layout
    
    def _setup_connections(self):
        """إعداد الاتصالات"""
        pass
    
    def _on_supplier_changed(self, index):
        """عند تغيير المورد"""
        supplier_id = self.supplier_combo.currentData()
        if supplier_id:
            # تحميل معلومات المورد
            try:
                query = "SELECT contact_person FROM suppliers WHERE id = ?"
                result = self.db.execute_query(query, (supplier_id,))
                if result:
                    self.contact_edit.setText(result[0][0] or "")
            except:
                pass
    
    def _add_item(self):
        """إضافة بند جديد"""
        from .product_selection_dialog import ProductSelectionDialog
        
        # فتح نافذة اختيار المنتج (أو استخدام combo box بسيط)
        product_combo = QComboBox()
        product_combo.addItem("-- اختر المنتج --", None)
        for product in self.products:
            product_combo.addItem(f"{product[1]} ({product[2]})", product)
        
        # إضافة صف جديد
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # المنتج
        self.items_table.setCellWidget(row, 0, product_combo)
        
        # الكود
        self.items_table.setItem(row, 1, QTableWidgetItem(""))
        
        # الكمية
        qty_spin = QDoubleSpinBox()
        qty_spin.setMinimum(0.001)
        qty_spin.setMaximum(999999.999)
        qty_spin.setDecimals(3)
        qty_spin.setValue(1.000)
        qty_spin.valueChanged.connect(lambda: self._update_item_row(row))
        self.items_table.setCellWidget(row, 2, qty_spin)
        
        # السعر
        price_spin = QDoubleSpinBox()
        price_spin.setMinimum(0.00)
        price_spin.setMaximum(999999.99)
        price_spin.setDecimals(2)
        price_spin.valueChanged.connect(lambda: self._update_item_row(row))
        self.items_table.setCellWidget(row, 3, price_spin)
        
        # الخصم%
        discount_spin = QDoubleSpinBox()
        discount_spin.setMinimum(0.00)
        discount_spin.setMaximum(100.00)
        discount_spin.setDecimals(2)
        discount_spin.setSuffix("%")
        discount_spin.valueChanged.connect(lambda: self._update_item_row(row))
        self.items_table.setCellWidget(row, 4, discount_spin)
        
        # الضريبة%
        tax_spin = QDoubleSpinBox()
        tax_spin.setMinimum(0.00)
        tax_spin.setMaximum(100.00)
        tax_spin.setDecimals(2)
        tax_spin.setValue(15.00)  # القيمة الافتراضية
        tax_spin.setSuffix("%")
        tax_spin.valueChanged.connect(lambda: self._update_item_row(row))
        self.items_table.setCellWidget(row, 5, tax_spin)
        
        # المجموع الفرعي
        self.items_table.setItem(row, 6, QTableWidgetItem("0.00"))
        
        # الصافي
        self.items_table.setItem(row, 7, QTableWidgetItem("0.00"))
        
        # ربط تغيير المنتج
        product_combo.currentIndexChanged.connect(lambda: self._on_product_changed(row))
    
    def _on_product_changed(self, row):
        """عند تغيير المنتج في صف"""
        product_combo = self.items_table.cellWidget(row, 0)
        product_data = product_combo.currentData()
        
        if product_data:
            # تحديث الكود والسعر
            self.items_table.item(row, 1).setText(product_data[2] or "")
            price_spin = self.items_table.cellWidget(row, 3)
            price_spin.setValue(float(product_data[3]) if product_data[3] else 0.00)
            
            self._update_item_row(row)
    
    def _update_item_row(self, row):
        """تحديث حسابات الصف"""
        try:
            qty_spin = self.items_table.cellWidget(row, 2)
            price_spin = self.items_table.cellWidget(row, 3)
            discount_spin = self.items_table.cellWidget(row, 4)
            tax_spin = self.items_table.cellWidget(row, 5)
            
            qty = Decimal(str(qty_spin.value()))
            price = Decimal(str(price_spin.value()))
            discount_pct = Decimal(str(discount_spin.value()))
            tax_pct = Decimal(str(tax_spin.value()))
            
            # المجموع الفرعي
            subtotal = qty * price
            
            # الخصم
            discount_amount = subtotal * (discount_pct / 100)
            
            # بعد الخصم
            after_discount = subtotal - discount_amount
            
            # الضريبة
            tax_amount = after_discount * (tax_pct / 100)
            
            # الصافي
            net_amount = after_discount + tax_amount
            
            # تحديث الجدول
            self.items_table.item(row, 6).setText(f"{subtotal:,.2f}")
            self.items_table.item(row, 7).setText(f"{net_amount:,.2f}")
            
            # إعادة حساب الإجمالي
            self._calculate_totals()
            
        except:
            pass
    
    def _remove_item(self):
        """حذف البند المحدد"""
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)
            self._calculate_totals()
    
    def _calculate_totals(self):
        """حساب الإجماليات"""
        subtotal = Decimal('0.00')
        
        for row in range(self.items_table.rowCount()):
            try:
                net_text = self.items_table.item(row, 7).text().replace(',', '')
                subtotal += Decimal(net_text)
            except:
                pass
        
        discount = Decimal(str(self.discount_spin.value()))
        tax = Decimal(str(self.tax_spin.value()))
        shipping = Decimal(str(self.shipping_spin.value()))
        
        total = subtotal - discount + tax + shipping
        
        self.subtotal_label.setText(f"{subtotal:,.2f}")
        self.total_label.setText(f"{total:,.2f}")
    
    def _load_po_data(self):
        """تحميل بيانات أمر الشراء للتحرير"""
        if not self.po:
            return
        
        # المورد
        for i in range(self.supplier_combo.count()):
            if self.supplier_combo.itemData(i) == self.po.supplier_id:
                self.supplier_combo.setCurrentIndex(i)
                break
        
        self.contact_edit.setText(self.po.supplier_contact or "")
        
        # التواريخ
        if self.po.order_date:
            self.order_date.setDate(QDate(self.po.order_date.year, self.po.order_date.month, self.po.order_date.day))
        if self.po.required_date:
            self.required_date.setDate(QDate(self.po.required_date.year, self.po.required_date.month, self.po.required_date.day))
        
        # الأولوية
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i) == self.po.priority:
                self.priority_combo.setCurrentIndex(i)
                break
        
        # العملة
        self.currency_combo.setCurrentText(self.po.currency)
        
        # الشروط
        for i in range(self.delivery_terms_combo.count()):
            if self.delivery_terms_combo.itemData(i) == self.po.delivery_terms:
                self.delivery_terms_combo.setCurrentIndex(i)
                break
        
        for i in range(self.payment_terms_combo.count()):
            if self.payment_terms_combo.itemData(i) == self.po.payment_terms:
                self.payment_terms_combo.setCurrentIndex(i)
                break
        
        # البنود
        for item in self.po.items:
            self._add_item()
            row = self.items_table.rowCount() - 1
            
            # تحديد المنتج
            product_combo = self.items_table.cellWidget(row, 0)
            for i in range(product_combo.count()):
                data = product_combo.itemData(i)
                if data and data[0] == item.product_id:
                    product_combo.setCurrentIndex(i)
                    break
            
            # الكمية والسعر
            self.items_table.cellWidget(row, 2).setValue(float(item.quantity_ordered))
            self.items_table.cellWidget(row, 3).setValue(float(item.unit_price))
            self.items_table.cellWidget(row, 4).setValue(float(item.discount_percent))
            self.items_table.cellWidget(row, 5).setValue(float(item.tax_percent))
        
        # المبالغ
        self.discount_spin.setValue(float(self.po.discount_amount))
        self.tax_spin.setValue(float(self.po.tax_amount))
        self.shipping_spin.setValue(float(self.po.shipping_cost))
        
        # الملاحظات
        self.notes_edit.setPlainText(self.po.notes or "")
        self.terms_edit.setPlainText(self.po.terms_conditions or "")
    
    def _save(self):
        """حفظ أمر الشراء"""
        # التحقق من الصحة
        if not self._validate():
            return
        
        try:
            # إنشاء كائن أمر الشراء
            po_data = self._collect_data()
            
            if self.is_edit_mode:
                # تحديث
                for key, value in po_data.items():
                    setattr(self.po, key, value)
            else:
                # إنشاء جديد
                self.po = PurchaseOrder(**po_data)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {str(e)}")
    
    def _validate(self):
        """التحقق من صحة البيانات"""
        if not self.supplier_combo.currentData():
            QMessageBox.warning(self, "تحذير", "يرجى اختيار المورد")
            return False
        
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "يرجى إضافة منتج واحد على الأقل")
            return False
        
        # التحقق من صحة البنود
        for row in range(self.items_table.rowCount()):
            product_combo = self.items_table.cellWidget(row, 0)
            if not product_combo.currentData():
                QMessageBox.warning(self, "تحذير", f"يرجى اختيار منتج للبند رقم {row + 1}")
                return False
        
        return True
    
    def _collect_data(self):
        """جمع البيانات من النموذج"""
        # البيانات الأساسية
        supplier_id = self.supplier_combo.currentData()
        supplier_name = self.supplier_combo.currentText()
        
        data = {
            'supplier_id': supplier_id,
            'supplier_name': supplier_name,
            'supplier_contact': self.contact_edit.text(),
            'order_date': date(self.order_date.date().year(), self.order_date.date().month(), self.order_date.date().day()),
            'required_date': date(self.required_date.date().year(), self.required_date.date().month(), self.required_date.date().day()),
            'priority': self.priority_combo.currentData(),
            'currency': self.currency_combo.currentText(),
            'delivery_terms': self.delivery_terms_combo.currentData(),
            'payment_terms': self.payment_terms_combo.currentData(),
            'notes': self.notes_edit.toPlainText(),
            'terms_conditions': self.terms_edit.toPlainText(),
            'discount_amount': Decimal(str(self.discount_spin.value())),
            'tax_amount': Decimal(str(self.tax_spin.value())),
            'shipping_cost': Decimal(str(self.shipping_spin.value())),
        }
        
        # البنود
        items = []
        for row in range(self.items_table.rowCount()):
            product_combo = self.items_table.cellWidget(row, 0)
            product_data = product_combo.currentData()
            
            if product_data:
                item = PurchaseOrderItem(
                    product_id=product_data[0],
                    product_name=product_data[1],
                    product_code=product_data[2],
                    quantity_ordered=Decimal(str(self.items_table.cellWidget(row, 2).value())),
                    unit_price=Decimal(str(self.items_table.cellWidget(row, 3).value())),
                    discount_percent=Decimal(str(self.items_table.cellWidget(row, 4).value())),
                    tax_percent=Decimal(str(self.items_table.cellWidget(row, 5).value()))
                )
                item.calculate_totals()
                items.append(item)
        
        data['items'] = items
        
        return data
    
    def get_purchase_order(self):
        """الحصول على أمر الشراء"""
        return self.po
