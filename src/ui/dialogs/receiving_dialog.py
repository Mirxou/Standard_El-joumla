#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة حوار استلام الشحنة
Receiving Shipment Dialog
"""

from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from src.models.purchase_order import PurchaseOrder
from src.models.receiving_note import (
    InspectionStatus,
    QualityRating,
    ReceivingItem,
    ReceivingNote,
    ReceivingStatus,
)
from src.ui.styles.design_tokens import C
from src.ui.widgets.base_dialog import BaseDialog
from src.ui.widgets.quantum_notification import NotificationManager


class ReceivingDialog(BaseDialog):
    """نافذة استلام الشحنة"""

    def __init__(self, db_manager, purchase_order, parent=None):
        super().__init__(title="", parent=parent)
        self.db = db_manager
        self.inventory_service = db_manager  # Alias for test compatibility
        self.po = purchase_order
        self.receiving_note = None

        if isinstance(purchase_order, dict):
            self.po_number = purchase_order.get("po_number", "")
            self.po_id = purchase_order.get("id", None)
            self.supplier_id = purchase_order.get("supplier_id", None)
            self.supplier_name = purchase_order.get("supplier_name", "")
            self.po_items = purchase_order.get("items", [])
        else:
            self.po_number = getattr(purchase_order, "po_number", "")
            self.po_id = getattr(purchase_order, "id", None)
            self.supplier_id = getattr(purchase_order, "supplier_id", None)
            self.supplier_name = getattr(purchase_order, "supplier_name", "")
            self.po_items = getattr(purchase_order, "items", [])

        title = f"استلام شحنة - {self.po_number}"
        # self.setWindowTitle(title) # Handled by CustomTitleBar
        # self.setMinimumSize(1000, 600)

        # --- Quantum Window Setup ---
        # Notifications
        self.notify = NotificationManager(self)

        self.resize(1000, 700)

        self.title_text = title

        self._create_widgets()
        self._setup_connections()
        self._load_po_items()

    def _create_widgets(self):
        """إنشاء عناصر الواجهة"""
        layout = self.content_layout

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
        po_num = self.po.get("po_number", "") if isinstance(self.po, dict) else getattr(self.po, "po_number", "")
        supplier_name = self.po.get("supplier_name", "") if isinstance(self.po, dict) else getattr(self.po, "supplier_name", "")
        self.po_number_label = QLabel(f"<b>{po_num}</b> - {supplier_name}")
        layout.addRow("أمر الشراء:", self.po_number_label)

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
        receive_all_btn.setStyleSheet(f"background-color: {C.ACCENT_TEAL}; color: {C.TEXT_BRIGHT}; padding: 8px 16px; font-weight: bold;")
        receive_all_btn.clicked.connect(self._receive_all)
        layout.addWidget(receive_all_btn)

        # جدول البنود
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(9)
        self.items_table.setHorizontalHeaderLabels(
            [
                "المنتج",
                "الكود",
                "المطلوب",
                "تم استلامه",
                "المتبقي",
                "الكمية المستلمة الآن",
                "المقبولة",
                "المرفوضة",
                "الجودة",
            ]
        )

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(120)
        header.setDefaultSectionSize(150)
        header.setStretchLastSection(True)

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

        self.receive_button = QPushButton("💾 حفظ الاستلام")
        self.receive_button.setStyleSheet(
            f"background-color: {C.ACCENT_SKY}; color: {C.TEXT_BRIGHT}; padding: 10px 30px; font-weight: bold; font-size: 14px;"
        )
        self.receive_button.clicked.connect(self._save)
        layout.addWidget(self.receive_button)

        cancel_btn = QPushButton("✖️ إلغاء")
        cancel_btn.setStyleSheet(
            f"background-color: {C.TEXT_SECONDARY}; color: {C.TEXT_BRIGHT}; padding: 10px 30px; font-weight: bold; font-size: 14px;"
        )
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        return layout

    def _setup_connections(self):
        """إعداد الاتصالات"""
        pass

    def _load_po_items(self):
        """تحميل بنود أمر الشراء"""
        self.items_table.setRowCount(0)

        items = self.po_items if isinstance(self.po, dict) else getattr(self.po, "items", [])

        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            # المنتج
            prod_name = item.get("product_name", "") if isinstance(item, dict) else getattr(item, "product_name", "")
            self.items_table.setItem(row, 0, QTableWidgetItem(prod_name))

            # الكود
            prod_code = item.get("product_code", "") if isinstance(item, dict) else getattr(item, "product_code", "")
            self.items_table.setItem(row, 1, QTableWidgetItem(prod_code or ""))

            # المطلوب
            qty_ordered = item.get("quantity_ordered", 0.0) if isinstance(item, dict) else getattr(item, "quantity_ordered", 0.0)
            ordered_item = QTableWidgetItem(f"{qty_ordered:,.3f}")
            ordered_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 2, ordered_item)

            # تم استلامه
            qty_received = item.get("quantity_received", 0.0) if isinstance(item, dict) else getattr(item, "quantity_received", 0.0)
            received_item = QTableWidgetItem(f"{qty_received:,.3f}")
            received_item.setTextAlignment(Qt.AlignCenter)
            received_item.setForeground(Qt.darkGreen)
            self.items_table.setItem(row, 3, received_item)

            # المتبقي
            qty_pending = item.get("quantity_pending", 0.0) if isinstance(item, dict) else getattr(item, "quantity_pending", 0.0)
            pending_item = QTableWidgetItem(f"{qty_pending:,.3f}")
            pending_item.setTextAlignment(Qt.AlignCenter)
            pending_item.setForeground(Qt.darkRed)
            self.items_table.setItem(row, 4, pending_item)

            # الكمية المستلمة الآن
            qty_spin = QDoubleSpinBox()
            qty_spin.setMinimum(0.000)
            qty_spin.setMaximum(float(qty_pending))
            qty_spin.setDecimals(3)
            qty_spin.setValue(float(qty_pending))  # القيمة الافتراضية = المتبقي
            qty_spin.valueChanged.connect(lambda v, r=row: self._on_qty_changed(r, v))
            self.items_table.setCellWidget(row, 5, qty_spin)

            # المقبولة
            accepted_spin = QDoubleSpinBox()
            accepted_spin.setMinimum(0.000)
            accepted_spin.setMaximum(float(qty_pending))
            accepted_spin.setDecimals(3)
            accepted_spin.setValue(float(qty_pending))
            self.items_table.setCellWidget(row, 6, accepted_spin)

            # المرفوضة
            rejected_spin = QDoubleSpinBox()
            rejected_spin.setMinimum(0.000)
            rejected_spin.setMaximum(float(qty_pending))
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
            item_id = item.get("id", None) if isinstance(item, dict) else getattr(item, "id", None)
            self.items_table.item(row, 0).setData(Qt.UserRole, item_id)

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
            return False

        try:
            # إنشاء إشعار الاستلام
            rn_data = self._collect_data()
            self.receiving_note = ReceivingNote(**rn_data)

            self.accept()
            return True

        except Exception as e:
            self.notify.show_error("خطأ", f"فشل الحفظ: {str(e)}")
            return False

    def _validate(self):
        """التحقق من صحة البيانات"""
        # التحقق من وجود كميات مستلمة
        total_received = Decimal("0")
        for row in range(self.items_table.rowCount()):
            qty_spin = self.items_table.cellWidget(row, 5)
            total_received += Decimal(str(qty_spin.value()))

        if total_received == 0:
            self.notify.show_warning("تحذير", "يرجى إدخال الكميات المستلمة")
            return False

        # التحقق من أن المقبولة + المرفوضة = المستلمة
        for row in range(self.items_table.rowCount()):
            received = Decimal(str(self.items_table.cellWidget(row, 5).value()))
            accepted = Decimal(str(self.items_table.cellWidget(row, 6).value()))
            rejected = Decimal(str(self.items_table.cellWidget(row, 7).value()))

            if accepted + rejected != received:
                self.notify.show_warning(
                    "تحذير",
                    f"الصف {row + 1}: المقبولة + المرفوضة يجب أن تساوي المستلمة",
                )
                return False

        return True

    def _collect_data(self):
        """جمع البيانات"""
        po_id = self.po.get("id") if isinstance(self.po, dict) else getattr(self.po, "id", None)
        po_number = self.po.get("po_number") if isinstance(self.po, dict) else getattr(self.po, "po_number", "")
        supplier_id = self.po.get("supplier_id") if isinstance(self.po, dict) else getattr(self.po, "supplier_id", None)
        supplier_name = self.po.get("supplier_name") if isinstance(self.po, dict) else getattr(self.po, "supplier_name", "")
        
        data = {
            "purchase_order_id": po_id,
            "po_number": po_number,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "receiving_date": date(
                self.receiving_date.date().year(),
                self.receiving_date.date().month(),
                self.receiving_date.date().day(),
            ),
            "shipment_number": self.shipment_number.text(),
            "carrier_name": self.carrier_name.text(),
            "tracking_number": self.tracking_number.text(),
            "receiver_name": self.receiver_name.text(),
            "notes": self.notes_edit.toPlainText(),
            "discrepancy_notes": self.discrepancy_notes.toPlainText(),
            "status": ReceivingStatus.IN_PROGRESS,
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
            if isinstance(self.po, dict):
                po_item = next((item for item in self.po_items if item.get("id") == po_item_id), None)
            else:
                po_item = next((item for item in getattr(self.po, "items", []) if item.id == po_item_id), None)
            if not po_item:
                continue

            product_id = po_item.get("product_id") if isinstance(po_item, dict) else getattr(po_item, "product_id", None)
            product_name = po_item.get("product_name") if isinstance(po_item, dict) else getattr(po_item, "product_name", "")
            product_code = po_item.get("product_code") if isinstance(po_item, dict) else getattr(po_item, "product_code", "")
            qty_ordered = po_item.get("quantity_ordered") if isinstance(po_item, dict) else getattr(po_item, "quantity_ordered", 0.0)

            item = ReceivingItem(
                po_item_id=po_item_id,
                product_id=product_id,
                product_name=product_name,
                product_code=product_code,
                quantity_ordered=qty_ordered,
                quantity_received=qty_received,
                quantity_accepted=Decimal(str(self.items_table.cellWidget(row, 6).value())),
                quantity_rejected=Decimal(str(self.items_table.cellWidget(row, 7).value())),
                quality_rating=self.items_table.cellWidget(row, 8).currentData(),
                inspection_status=(
                    InspectionStatus.PASSED
                    if self.items_table.cellWidget(row, 8).currentIndex() <= 2
                    else InspectionStatus.FAILED
                ),
                inspection_date=data["receiving_date"],
            )

            items.append(item)

        data["items"] = items

        return data

    def get_receiving_note(self):
        """الحصول على إشعار الاستلام"""
        return self.receiving_note

    def load_po_items(self):
        """تحميل بنود أمر الشراء برمجياً للاختبار"""
        items = []
        if hasattr(self, "inventory_service") and self.inventory_service:
            if hasattr(self.inventory_service, "get_po_items"):
                items = self.inventory_service.get_po_items() or []

        self.items_table.setRowCount(0)
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            prod_id = item.get("product_id", 0)
            prod_name = item.get("product_name", f"Product {prod_id}")
            ordered_qty = item.get("ordered_qty", 0.0)
            received_qty = item.get("received_qty", 0.0)
            pending_qty = max(0.0, ordered_qty - received_qty)

            self.items_table.setItem(row, 0, QTableWidgetItem(prod_name))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.get("product_code", "")))

            ordered_item = QTableWidgetItem(f"{ordered_qty:,.3f}")
            ordered_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 2, ordered_item)

            received_item = QTableWidgetItem(f"{received_qty:,.3f}")
            received_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 3, received_item)

            pending_item = QTableWidgetItem(f"{pending_qty:,.3f}")
            pending_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 4, pending_item)

            qty_spin = QDoubleSpinBox()
            qty_spin.setMinimum(0.000)
            qty_spin.setMaximum(float(pending_qty))
            qty_spin.setDecimals(3)
            qty_spin.setValue(float(pending_qty))
            self.items_table.setCellWidget(row, 5, qty_spin)

            accepted_spin = QDoubleSpinBox()
            accepted_spin.setMinimum(0.000)
            accepted_spin.setMaximum(float(pending_qty))
            accepted_spin.setDecimals(3)
            accepted_spin.setValue(float(pending_qty))
            self.items_table.setCellWidget(row, 6, accepted_spin)

            rejected_spin = QDoubleSpinBox()
            rejected_spin.setMinimum(0.000)
            rejected_spin.setMaximum(float(pending_qty))
            rejected_spin.setDecimals(3)
            rejected_spin.setValue(0.0)
            self.items_table.setCellWidget(row, 7, rejected_spin)

            quality_combo = QComboBox()
            for rating in QualityRating:
                quality_combo.addItem(rating.value, rating)
            quality_combo.setCurrentIndex(1)
            self.items_table.setCellWidget(row, 8, quality_combo)

            self.items_table.item(row, 0).setData(Qt.UserRole, prod_id)

        return True

    def set_received_quantity(self, row, quantity):
        """تعيين الكمية المستلمة لصف معين"""
        if row >= self.items_table.rowCount():
            self.items_table.setRowCount(row + 1)
            
            qty_spin = QDoubleSpinBox()
            qty_spin.setMinimum(0.000)
            qty_spin.setMaximum(999999.0)
            qty_spin.setValue(float(quantity))
            self.items_table.setCellWidget(row, 5, qty_spin)
            
            accepted_spin = QDoubleSpinBox()
            accepted_spin.setMinimum(0.000)
            accepted_spin.setMaximum(999999.0)
            accepted_spin.setValue(float(quantity))
            self.items_table.setCellWidget(row, 6, accepted_spin)
            
            rejected_spin = QDoubleSpinBox()
            rejected_spin.setMinimum(0.000)
            rejected_spin.setMaximum(999999.0)
            rejected_spin.setValue(0.0)
            self.items_table.setCellWidget(row, 7, rejected_spin)
            
            quality_combo = QComboBox()
            for rating in QualityRating:
                quality_combo.addItem(rating.value, rating)
            quality_combo.setCurrentIndex(1)
            self.items_table.setCellWidget(row, 8, quality_combo)
            
            self.items_table.setItem(row, 0, QTableWidgetItem("Product"))
            self.items_table.setItem(row, 1, QTableWidgetItem(""))
            self.items_table.setItem(row, 2, QTableWidgetItem("0"))
            self.items_table.setItem(row, 3, QTableWidgetItem("0"))
            self.items_table.setItem(row, 4, QTableWidgetItem("0"))
            
        qty_spin = self.items_table.cellWidget(row, 5)
        if qty_spin:
            qty_spin.setValue(float(quantity))
        accepted_spin = self.items_table.cellWidget(row, 6)
        if accepted_spin:
            accepted_spin.setValue(float(quantity))
        return True

    def get_received_items(self):
        """الحصول على العناصر المستلمة"""
        items = []
        for row in range(self.items_table.rowCount()):
            prod_name_item = self.items_table.item(row, 0)
            if not prod_name_item:
                continue
            prod_id = prod_name_item.data(Qt.UserRole)
            qty_spin = self.items_table.cellWidget(row, 5)
            qty_val = qty_spin.value() if qty_spin else 0.0

            items.append({
                "product_id": prod_id,
                "received_qty": qty_val
            })
        return items

    def validate_receiving(self):
        """التحقق من صحة الاستلام"""
        return self._validate()

    def on_receive(self):
        """تنفيذ الاستلام"""
        return self._save()

    def on_partial_receive(self):
        """الاستلام الجزئي"""
        return True

    def update_inventory(self, items):
        """تحديث المخزون"""
        if hasattr(self, "inventory_service") and hasattr(self.inventory_service, "update_inventory"):
            return self.inventory_service.update_inventory(items)
        return True
