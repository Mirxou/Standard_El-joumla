#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة حوار استلام الشحنة
Receiving Shipment Dialog
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QDoubleSpinBox,
    QMessageBox, QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt, QDate
from decimal import Decimal
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.receiving_note import (
    ReceivingNote, ReceivingItem, ReceivingStatus,
    InspectionStatus, QualityRating
)
from models.purchase_order import PurchaseOrder


class ReceivingDialog(QDialog):
    """نافذة استلام الشحنة"""
    
    def __init__(self, db_manager, purchase_order: PurchaseOrder, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.po = purchase_order
        self.receiving_note = None
        
        self.setWindowTitle(f"استلام شحنة - {purchase_order.po_number}")
        self.setMinimumSize(1000, 600)
        
        self._create_widgets()
        self._setup_connections()
        self._load_po_items()
    
    def _create_widgets(self):
        """إنشاء عناصر الواجهة"""
        layout = QVBoxLayout(self)
        
        # معلومات الشحنة
        shipment_group = self._create_shipment_info_group()
        layout.addWidget(shipment_group)
        
        # البنود للاستلام
        items_group = self._create_items_group()
        layout.addWidget(items_group)
        
        # الملاحظات
        notes_group = self._create_notes_group()
        layout.addWidget(notes_group)
        
        # الأزرار
        buttons = self._create_buttons()
        layout.addLayout(buttons)
    
    def _create_shipment_info_group(self):
        """مجموعة معلومات الشحنة"""
        group = QGroupBox("معلومات الشحنة")
        layout = QFormLayout(group)
        
        # أمر الشراء
        po_label = QLabel(f"<b>{self.po.po_number}</b> - {self.po.supplier_name}")
        layout.addRow("أمر الشراء:", po_label)
        
        # تاريخ الاستلام
        self.receiving_date = QDateEdit()
        self.receiving_date.setDate(QDate.currentDate())
        self.receiving_date.setCalendarPopup(True)
        layout.addRow("تاريخ الاستلام:", self.receiving_date)
        
        # معلومات الشحن
        shipping_layout = QHBoxLayout()
        
        self.shipment_number = QLineEdit()
        self.shipment_number.setPlaceholderText("رقم الشحنة")
        shipping_layout.addWidget(QLabel("رقم الشحنة:"))
        shipping_layout.addWidget(self.shipment_number)
        
        shipping_layout.addSpacing(20)
        
        self.carrier_name = QLineEdit()
        self.carrier_name.setPlaceholderText("شركة الشحن")
        shipping_layout.addWidget(QLabel("شركة الشحن:"))
        shipping_layout.addWidget(self.carrier_name)
        
        layout.addRow("", shipping_layout)
        
        # رقم التتبع
        self.tracking_number = QLineEdit()
        self.tracking_number.setPlaceholderText("رقم التتبع")
        layout.addRow("رقم التتبع:", self.tracking_number)
        
        # المستلم
        self.receiver_name = QLineEdit()
        self.receiver_name.setPlaceholderText("اسم الموظف المستلم")
        layout.addRow("المستلم:", self.receiver_name)
        
        return group
    
    def _create_items_group(self):
        """مجموعة البنود"""
        group = QGroupBox("البنود المطلوب استلامها")
        layout = QVBoxLayout(group)
        
        # زر استلام الكل
        receive_all_btn = QPushButton("✅ استلام الكل")
        receive_all_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px; font-weight: bold;")
        receive_all_btn.clicked.connect(self._receive_all)
        layout.addWidget(receive_all_btn)
        
        # جدول البنود
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(9)
        self.items_table.setHorizontalHeaderLabels([
            "المنتج", "الكود", "المطلوب", "تم استلامه",
            "المتبقي", "الكمية المستلمة الآن", "المقبولة", "المرفوضة", "الجودة"
        ])
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.items_table)
        
        return group
    
    def _create_notes_group(self):
        """مجموعة الملاحظات"""
        group = QGroupBox("الملاحظات")
        layout = QFormLayout(group)
        
        # ملاحظات عامة
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        layout.addRow("ملاحظات:", self.notes_edit)
        
        # ملاحظات الاختلافات
        self.discrepancy_notes = QTextEdit()
        self.discrepancy_notes.setMaximumHeight(60)
        layout.addRow("اختلافات:", self.discrepancy_notes)
        
        return group
    
    def _create_buttons(self):
        """أزرار الحوار"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ الاستلام")
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
    
    def _load_po_items(self):
        """تحميل بنود أمر الشراء"""
        self.items_table.setRowCount(0)
        
        for item in self.po.items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            
            # المنتج
            self.items_table.setItem(row, 0, QTableWidgetItem(item.product_name))
            
            # الكود
            self.items_table.setItem(row, 1, QTableWidgetItem(item.product_code or ""))
            
            # المطلوب
            ordered_item = QTableWidgetItem(f"{item.quantity_ordered:,.3f}")
            ordered_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 2, ordered_item)
            
            # تم استلامه
            received_item = QTableWidgetItem(f"{item.quantity_received:,.3f}")
            received_item.setTextAlignment(Qt.AlignCenter)
            received_item.setForeground(Qt.darkGreen)
            self.items_table.setItem(row, 3, received_item)
            
            # المتبقي
            pending_item = QTableWidgetItem(f"{item.quantity_pending:,.3f}")
            pending_item.setTextAlignment(Qt.AlignCenter)
            pending_item.setForeground(Qt.darkRed)
            self.items_table.setItem(row, 4, pending_item)
            
            # الكمية المستلمة الآن
            qty_spin = QDoubleSpinBox()
            qty_spin.setMinimum(0.000)
            qty_spin.setMaximum(float(item.quantity_pending))
            qty_spin.setDecimals(3)
            qty_spin.setValue(float(item.quantity_pending))  # القيمة الافتراضية = المتبقي
            qty_spin.valueChanged.connect(lambda v, r=row: self._on_qty_changed(r, v))
            self.items_table.setCellWidget(row, 5, qty_spin)
            
            # المقبولة
            accepted_spin = QDoubleSpinBox()
            accepted_spin.setMinimum(0.000)
            accepted_spin.setMaximum(float(item.quantity_pending))
            accepted_spin.setDecimals(3)
            accepted_spin.setValue(float(item.quantity_pending))
            self.items_table.setCellWidget(row, 6, accepted_spin)
            
            # المرفوضة
            rejected_spin = QDoubleSpinBox()
            rejected_spin.setMinimum(0.000)
            rejected_spin.setMaximum(float(item.quantity_pending))
            rejected_spin.setDecimals(3)
            rejected_spin.setValue(0.000)
            self.items_table.setCellWidget(row, 7, rejected_spin)
            
            # تقييم الجودة
            quality_combo = QComboBox()
            for rating in QualityRating:
                quality_combo.addItem(rating.value, rating)
            quality_combo.setCurrentIndex(1)  # GOOD
            self.items_table.setCellWidget(row, 8, quality_combo)
            
            # حفظ معرف البند
            self.items_table.item(row, 0).setData(Qt.UserRole, item.id)
    
    def _receive_all(self):
        """استلام جميع الكميات المتبقية"""
        for row in range(self.items_table.rowCount()):
            qty_spin = self.items_table.cellWidget(row, 5)
            accepted_spin = self.items_table.cellWidget(row, 6)
            
            # تعيين الكمية المستلمة = المتبقي
            max_qty = qty_spin.maximum()
            qty_spin.setValue(max_qty)
            accepted_spin.setValue(max_qty)
    
    def _on_qty_changed(self, row, value):
        """عند تغيير الكمية المستلمة"""
        # تحديث الكمية المقبولة تلقائياً
        accepted_spin = self.items_table.cellWidget(row, 6)
        rejected_spin = self.items_table.cellWidget(row, 7)
        
        # إذا لم يكن هناك رفض، اجعل المقبولة = المستلمة
        if rejected_spin.value() == 0:
            accepted_spin.setMaximum(value)
            accepted_spin.setValue(value)
    
    def _save(self):
        """حفظ إشعار الاستلام"""
        if not self._validate():
            return
        
        try:
            # إنشاء إشعار الاستلام
            rn_data = self._collect_data()
            self.receiving_note = ReceivingNote(**rn_data)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {str(e)}")
    
    def _validate(self):
        """التحقق من صحة البيانات"""
        # التحقق من وجود كميات مستلمة
        total_received = Decimal('0')
        for row in range(self.items_table.rowCount()):
            qty_spin = self.items_table.cellWidget(row, 5)
            total_received += Decimal(str(qty_spin.value()))
        
        if total_received == 0:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الكميات المستلمة")
            return False
        
        # التحقق من أن المقبولة + المرفوضة = المستلمة
        for row in range(self.items_table.rowCount()):
            received = Decimal(str(self.items_table.cellWidget(row, 5).value()))
            accepted = Decimal(str(self.items_table.cellWidget(row, 6).value()))
            rejected = Decimal(str(self.items_table.cellWidget(row, 7).value()))
            
            if accepted + rejected != received:
                QMessageBox.warning(
                    self, "تحذير",
                    f"الصف {row + 1}: المقبولة + المرفوضة يجب أن تساوي المستلمة"
                )
                return False
        
        return True
    
    def _collect_data(self):
        """جمع البيانات"""
        data = {
            'purchase_order_id': self.po.id,
            'po_number': self.po.po_number,
            'supplier_id': self.po.supplier_id,
            'supplier_name': self.po.supplier_name,
            'receiving_date': date(
                self.receiving_date.date().year(),
                self.receiving_date.date().month(),
                self.receiving_date.date().day()
            ),
            'shipment_number': self.shipment_number.text(),
            'carrier_name': self.carrier_name.text(),
            'tracking_number': self.tracking_number.text(),
            'receiver_name': self.receiver_name.text(),
            'notes': self.notes_edit.toPlainText(),
            'discrepancy_notes': self.discrepancy_notes.toPlainText(),
            'status': ReceivingStatus.IN_PROGRESS,
        }
        
        # البنود
        items = []
        for row in range(self.items_table.rowCount()):
            po_item_id = self.items_table.item(row, 0).data(Qt.UserRole)
            
            qty_received = Decimal(str(self.items_table.cellWidget(row, 5).value()))
            
            # تخطى البنود التي لم يتم استلامها
            if qty_received == 0:
                continue
            
            # الحصول على بيانات البند من أمر الشراء
            po_item = next((item for item in self.po.items if item.id == po_item_id), None)
            if not po_item:
                continue
            
            item = ReceivingItem(
                po_item_id=po_item_id,
                product_id=po_item.product_id,
                product_name=po_item.product_name,
                product_code=po_item.product_code,
                quantity_ordered=po_item.quantity_ordered,
                quantity_received=qty_received,
                quantity_accepted=Decimal(str(self.items_table.cellWidget(row, 6).value())),
                quantity_rejected=Decimal(str(self.items_table.cellWidget(row, 7).value())),
                quality_rating=self.items_table.cellWidget(row, 8).currentData(),
                inspection_status=InspectionStatus.PASSED if self.items_table.cellWidget(row, 8).currentIndex() <= 2 else InspectionStatus.FAILED,
                inspection_date=data['receiving_date']
            )
            
            items.append(item)
        
        data['items'] = items
        
        return data
    
    def get_receiving_note(self):
        """الحصول على إشعار الاستلام"""
        return self.receiving_note
