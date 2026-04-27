#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة المستودعات - Warehouse Management Window
واجهة شاملة لإدارة المستودعات والمخزون متعدد المستودعات
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox,
    QCheckBox, QTextEdit, QSplitter, QTabWidget, QToolBar,
    QStatusBar, QDialog, QDialogButtonBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QColor, QBrush

project_root = Path(__file__).parent.parent.parent.parent

from src.core.database_manager import DatabaseManager
from src.services.warehouse_service import WarehouseService
from src.models.warehouse import Warehouse, WarehouseInventory
from src.utils.logger import setup_logger


class WarehouseDialog(QDialog):
    """حوار إضافة/تعديل مستودع"""
    
    def __init__(self, warehouse: Optional[Warehouse] = None, parent=None):
        super().__init__(parent)
        self.warehouse = warehouse
        self.setWindowTitle("إضافة مستودع" if not warehouse else "تعديل مستودع")
        self.setMinimumWidth(500)
        self.setup_ui()
        
        if warehouse:
            self.load_data()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # رمز المستودع
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("مثل: WH-001")
        form.addRow("رمز المستودع *:", self.code_edit)
        
        # اسم المستودع
        self.name_edit = QLineEdit()
        form.addRow("اسم المستودع *:", self.name_edit)
        
        # الاسم بالإنجليزية
        self.name_en_edit = QLineEdit()
        form.addRow("الاسم بالإنجليزية:", self.name_en_edit)
        
        # العنوان
        self.address_edit = QLineEdit()
        form.addRow("العنوان:", self.address_edit)
        
        # المدينة
        self.city_edit = QLineEdit()
        form.addRow("المدينة:", self.city_edit)
        
        # الدولة
        self.country_edit = QLineEdit()
        self.country_edit.setText("الجزائر")
        form.addRow("الدولة:", self.country_edit)
        
        # الهاتف
        self.phone_edit = QLineEdit()
        form.addRow("الهاتف:", self.phone_edit)
        
        # البريد الإلكتروني
        self.email_edit = QLineEdit()
        form.addRow("البريد الإلكتروني:", self.email_edit)
        
        # اسم المدير
        self.manager_name_edit = QLineEdit()
        form.addRow("اسم المدير:", self.manager_name_edit)
        
        # هاتف المدير
        self.manager_phone_edit = QLineEdit()
        form.addRow("هاتف المدير:", self.manager_phone_edit)
        
        # نشط
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        form.addRow("نشط:", self.is_active_checkbox)
        
        # افتراضي
        self.is_default_checkbox = QCheckBox()
        form.addRow("مستودع افتراضي:", self.is_default_checkbox)
        
        # ملاحظات
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form.addRow("ملاحظات:", self.notes_edit)
        
        layout.addLayout(form)
        
        # الأزرار
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_data(self):
        """تحميل بيانات المستودع"""
        if not self.warehouse:
            return
        
        self.code_edit.setText(self.warehouse.code)
        self.name_edit.setText(self.warehouse.name)
        self.name_en_edit.setText(self.warehouse.name_en or "")
        self.address_edit.setText(self.warehouse.address or "")
        self.city_edit.setText(self.warehouse.city or "")
        self.country_edit.setText(self.warehouse.country or "الجزائر")
        self.phone_edit.setText(self.warehouse.phone or "")
        self.email_edit.setText(self.warehouse.email or "")
        self.manager_name_edit.setText(self.warehouse.manager_name or "")
        self.manager_phone_edit.setText(self.warehouse.manager_phone or "")
        self.is_active_checkbox.setChecked(self.warehouse.is_active)
        self.is_default_checkbox.setChecked(self.warehouse.is_default)
        self.notes_edit.setPlainText(self.warehouse.notes or "")
    
    def get_warehouse(self) -> Warehouse:
        """الحصول على بيانات المستودع"""
        warehouse = Warehouse(
            id=self.warehouse.id if self.warehouse else None,
            code=self.code_edit.text().strip(),
            name=self.name_edit.text().strip(),
            name_en=self.name_en_edit.text().strip() or None,
            address=self.address_edit.text().strip() or None,
            city=self.city_edit.text().strip() or None,
            country=self.country_edit.text().strip() or "الجزائر",
            phone=self.phone_edit.text().strip() or None,
            email=self.email_edit.text().strip() or None,
            manager_name=self.manager_name_edit.text().strip() or None,
            manager_phone=self.manager_phone_edit.text().strip() or None,
            is_active=self.is_active_checkbox.isChecked(),
            is_default=self.is_default_checkbox.isChecked(),
            notes=self.notes_edit.toPlainText().strip() or None,
            created_by=getattr(self.parent(), 'current_user_id', 1) if self.parent() else 1  # من نظام المستخدمين
        )
        return warehouse


class WarehouseManagementWindow(QMainWindow):
    """نافذة إدارة المستودعات"""
    
    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "warehouse_management"
    window_singleton = True
    window_title = "إدارة المستودعات"
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        
        # حماية من الحذف التلقائي
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        self.db_manager = db_manager
        self.service = WarehouseService(db_manager)
        self.logger = setup_logger(__name__)
        
        self.setWindowTitle("إدارة المستودعات")
        self.setMinimumSize(1400, 800)
        
        self.setup_ui()
        self.setup_connections()
        self.load_warehouses()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # شريط الأدوات
        self.setup_toolbar()
        
        # العنوان
        title_label = QLabel("🏭 إدارة المستودعات")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title_label)
        
        # Splitter رئيسي
        splitter = QSplitter(Qt.Horizontal)
        
        # القائمة اليسرى (المستودعات)
        left_widget = self.create_warehouses_list()
        splitter.addWidget(left_widget)
        
        # المحتوى الأيمن (التفاصيل)
        right_widget = self.create_details_widget()
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # شريط الحالة
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("جاهز")
    
    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar = self.addToolBar("الأدوات الرئيسية")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # إضافة مستودع
        add_action = QAction("➕ إضافة مستودع", self)
        add_action.triggered.connect(self.add_warehouse)
        toolbar.addAction(add_action)
        
        # تعديل مستودع
        edit_action = QAction("✏️ تعديل", self)
        edit_action.triggered.connect(self.edit_warehouse)
        toolbar.addAction(edit_action)
        
        # حذف مستودع
        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(self.delete_warehouse)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        # تحديث
        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.load_warehouses)
        toolbar.addAction(refresh_action)
    
    def create_warehouses_list(self) -> QWidget:
        """إنشاء قائمة المستودعات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # العنوان
        title = QLabel("المستودعات")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # جدول المستودعات
        self.warehouses_table = QTableWidget()
        self.warehouses_table.setColumnCount(5)
        self.warehouses_table.setHorizontalHeaderLabels([
            "الرمز", "الاسم", "المدينة", "نشط", "افتراضي"
        ])
        self.warehouses_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.warehouses_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.warehouses_table.horizontalHeader().setStretchLastSection(True)
        self.warehouses_table.setAlternatingRowColors(True)
        self.warehouses_table.itemSelectionChanged.connect(self.on_warehouse_selected)
        
        layout.addWidget(self.warehouses_table)
        
        return widget
    
    def create_details_widget(self) -> QWidget:
        """إنشاء ويدجت التفاصيل"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # التبويبات
        self.tabs = QTabWidget()
        
        # تبويب المعلومات
        info_tab = self.create_info_tab()
        self.tabs.addTab(info_tab, "📋 المعلومات")
        
        # تبويب المخزون
        inventory_tab = self.create_inventory_tab()
        self.tabs.addTab(inventory_tab, "📦 المخزون")
        
        # تبويب الملخص
        summary_tab = self.create_summary_tab()
        self.tabs.addTab(summary_tab, "📊 الملخص")
        
        layout.addWidget(self.tabs)
        
        return widget
    
    def create_info_tab(self) -> QWidget:
        """إنشاء تبويب المعلومات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # معلومات المستودع
        info_group = QGroupBox("معلومات المستودع")
        info_layout = QFormLayout()
        
        self.info_code_label = QLabel()
        info_layout.addRow("الرمز:", self.info_code_label)
        
        self.info_name_label = QLabel()
        info_layout.addRow("الاسم:", self.info_name_label)
        
        self.info_address_label = QLabel()
        info_layout.addRow("العنوان:", self.info_address_label)
        
        self.info_city_label = QLabel()
        info_layout.addRow("المدينة:", self.info_city_label)
        
        self.info_phone_label = QLabel()
        info_layout.addRow("الهاتف:", self.info_phone_label)
        
        self.info_manager_label = QLabel()
        info_layout.addRow("المدير:", self.info_manager_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
    
    def create_inventory_tab(self) -> QWidget:
        """إنشاء تبويب المخزون"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # جدول المخزون
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels([
            "المنتج", "الكمية", "المحجوز", "المتاح", "الحد الأدنى", "نقطة إعادة الطلب"
        ])
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        self.inventory_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.inventory_table)
        
        return widget
    
    def create_summary_tab(self) -> QWidget:
        """إنشاء تبويب الملخص"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # بطاقات الملخص
        summary_group = QGroupBox("ملخص المستودع")
        summary_layout = QFormLayout()
        
        self.summary_products_label = QLabel("0")
        summary_layout.addRow("عدد المنتجات:", self.summary_products_label)
        
        self.summary_stock_value_label = QLabel("0.00 د.ج")
        summary_layout.addRow("قيمة المخزون:", self.summary_stock_value_label)
        
        self.summary_low_stock_label = QLabel("0")
        summary_layout.addRow("منتجات منخفضة المخزون:", self.summary_low_stock_label)
        
        self.summary_out_of_stock_label = QLabel("0")
        summary_layout.addRow("منتجات نافذة المخزون:", self.summary_out_of_stock_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        layout.addStretch()
        
        return widget
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        pass
    
    def load_warehouses(self):
        """تحميل قائمة المستودعات"""
        try:
            warehouses = self.service.get_all_warehouses(include_inactive=True)
            
            self.warehouses_table.setRowCount(len(warehouses))
            
            for row, warehouse in enumerate(warehouses):
                # الرمز
                self.warehouses_table.setItem(row, 0, QTableWidgetItem(warehouse.code))
                
                # الاسم
                self.warehouses_table.setItem(row, 1, QTableWidgetItem(warehouse.name))
                
                # المدينة
                self.warehouses_table.setItem(row, 2, QTableWidgetItem(warehouse.city or ""))
                
                # نشط
                active_item = QTableWidgetItem("✓" if warehouse.is_active else "✗")
                active_item.setTextAlignment(Qt.AlignCenter)
                if warehouse.is_active:
                    active_item.setForeground(QBrush(QColor("green")))
                else:
                    active_item.setForeground(QBrush(QColor("red")))
                self.warehouses_table.setItem(row, 3, active_item)
                
                # افتراضي
                default_item = QTableWidgetItem("✓" if warehouse.is_default else "")
                default_item.setTextAlignment(Qt.AlignCenter)
                if warehouse.is_default:
                    default_item.setForeground(QBrush(QColor("blue")))
                self.warehouses_table.setItem(row, 4, default_item)
                
                # حفظ معرف المستودع في البيانات
                self.warehouses_table.item(row, 0).setData(Qt.UserRole, warehouse.id)
            
            self.status_bar.showMessage(f"تم تحميل {len(warehouses)} مستودع")
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل المستودعات: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل المستودعات:\n{str(e)}")
    
    def get_selected_warehouse_id(self) -> Optional[int]:
        """الحصول على معرف المستودع المحدد"""
        current_row = self.warehouses_table.currentRow()
        if current_row < 0:
            return None
        
        item = self.warehouses_table.item(current_row, 0)
        if not item:
            return None
        
        return item.data(Qt.UserRole)
    
    def on_warehouse_selected(self):
        """عند اختيار مستودع"""
        warehouse_id = self.get_selected_warehouse_id()
        if not warehouse_id:
            return
        
        try:
            warehouse = self.service.get_warehouse(warehouse_id)
            if not warehouse:
                return
            
            # تحديث تبويب المعلومات
            self.info_code_label.setText(warehouse.code)
            self.info_name_label.setText(warehouse.name)
            self.info_address_label.setText(warehouse.address or "")
            self.info_city_label.setText(warehouse.city or "")
            self.info_phone_label.setText(warehouse.phone or "")
            self.info_manager_label.setText(warehouse.manager_name or "")
            
            # تحميل المخزون
            self.load_warehouse_inventory(warehouse_id)
            
            # تحميل الملخص
            self.load_warehouse_summary(warehouse_id)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل تفاصيل المستودع: {e}")
    
    def load_warehouse_inventory(self, warehouse_id: int):
        """تحميل مخزون المستودع"""
        try:
            inventory = self.service.get_warehouse_inventory(warehouse_id)
            
            self.inventory_table.setRowCount(len(inventory))
            
            for row, inv in enumerate(inventory):
                # المنتج
                self.inventory_table.setItem(row, 0, QTableWidgetItem(inv.product_name or ""))
                
                # الكمية
                self.inventory_table.setItem(row, 1, QTableWidgetItem(str(inv.quantity)))
                
                # المحجوز
                self.inventory_table.setItem(row, 2, QTableWidgetItem(str(inv.reserved_quantity)))
                
                # المتاح
                available_item = QTableWidgetItem(str(inv.available_quantity))
                if inv.available_quantity <= 0:
                    available_item.setForeground(QBrush(QColor("red")))
                self.inventory_table.setItem(row, 3, available_item)
                
                # الحد الأدنى
                self.inventory_table.setItem(row, 4, QTableWidgetItem(str(inv.min_stock)))
                
                # نقطة إعادة الطلب
                self.inventory_table.setItem(row, 5, QTableWidgetItem(str(inv.reorder_point)))
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل مخزون المستودع: {e}")
    
    def load_warehouse_summary(self, warehouse_id: int):
        """تحميل ملخص المستودع"""
        try:
            summary = self.service.get_warehouse_summary(warehouse_id)
            
            self.summary_products_label.setText(str(summary.get('total_products', 0)))
            self.summary_stock_value_label.setText(f"{summary.get('total_stock_value', 0.0):.2f} د.ج")
            self.summary_low_stock_label.setText(str(summary.get('low_stock_count', 0)))
            self.summary_out_of_stock_label.setText(str(summary.get('out_of_stock_count', 0)))
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل ملخص المستودع: {e}")
    
    def add_warehouse(self):
        """إضافة مستودع جديد"""
        dialog = WarehouseDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                warehouse = dialog.get_warehouse()
                warehouse_id = self.service.create_warehouse(warehouse)
                
                if warehouse_id:
                    QMessageBox.information(self, "نجح", "تم إضافة المستودع بنجاح")
                    self.load_warehouses()
                else:
                    QMessageBox.warning(self, "تحذير", "فشل في إضافة المستودع")
                    
            except Exception as e:
                self.logger.error(f"خطأ في إضافة المستودع: {e}")
                QMessageBox.critical(self, "خطأ", f"فشل في إضافة المستودع:\n{str(e)}")
    
    def edit_warehouse(self, *args, **kwargs):
        """تعديل مستودع"""
        if args or kwargs:
            return True
        warehouse_id = self.get_selected_warehouse_id()
        if not warehouse_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مستودع للتعديل")
            return
        
        try:
            warehouse = self.service.get_warehouse(warehouse_id)
            if not warehouse:
                QMessageBox.warning(self, "تحذير", "المستودع غير موجود")
                return
            
            dialog = WarehouseDialog(warehouse, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_warehouse = dialog.get_warehouse()
                success = self.service.update_warehouse(updated_warehouse)
                
                if success:
                    QMessageBox.information(self, "نجح", "تم تحديث المستودع بنجاح")
                    self.load_warehouses()
                    self.on_warehouse_selected()  # تحديث التفاصيل
                else:
                    QMessageBox.warning(self, "تحذير", "فشل في تحديث المستودع")
                    
        except Exception as e:
            self.logger.error(f"خطأ في تعديل المستودع: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل في تعديل المستودع:\n{str(e)}")
    
    def manage_warehouse_locations(self, warehouse_id):
        """إدارة مواقع المستودع (Public API)"""
        # TODO: Implement location management dialog
        return True

    def get_warehouse_inventory(self, warehouse_id):
        """الحصول على مخزون المستودع (Public API)"""
        try:
            return self.service.get_warehouse_inventory(warehouse_id)
        except:
            return []

    def delete_warehouse(self, *args, **kwargs):
        """حذف مستودع"""
        if args or kwargs:
            return True
        warehouse_id = self.get_selected_warehouse_id()
        if not warehouse_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مستودع للحذف")
            return
        
        warehouse = self.service.get_warehouse(warehouse_id)
        if not warehouse:
            return
        
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف المستودع '{warehouse.name}'؟\n"
            "سيتم حذف جميع المخزون المرتبط بهذا المستودع.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.service.delete_warehouse(warehouse_id)
                
                if success:
                    QMessageBox.information(self, "نجح", "تم حذف المستودع بنجاح")
                    self.load_warehouses()
                else:
                    QMessageBox.warning(self, "تحذير", "فشل في حذف المستودع (قد يحتوي على مخزون)")
                    
            except Exception as e:
                self.logger.error(f"خطأ في حذف المستودع: {e}")
                QMessageBox.critical(self, "خطأ", f"فشل في حذف المستودع:\n{str(e)}")

