#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة أوامر الشراء
Purchase Orders Management Window
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit, QMessageBox,
    QHeaderView, QFormLayout, QDateEdit, QGroupBox, QDialogButtonBox,
    QScrollArea, QSplitter, QListWidget, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon, QColor, QFont
from decimal import Decimal
from datetime import datetime, date, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.purchase_order_service import PurchaseOrderService
from models.purchase_order import (
    PurchaseOrder, PurchaseOrderItem, POStatus, 
    POPriority, DeliveryTerms, PaymentTerms
)
from ui.dialogs.purchase_order_dialog import PurchaseOrderDialog
from ui.dialogs.receiving_dialog import ReceivingDialog


class PurchaseOrdersWindow(QMainWindow):
    """نافذة إدارة أوامر الشراء"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.po_service = PurchaseOrderService(db_manager)
        self.parent_window = parent
        self.current_po = None
        
        self.setWindowTitle("إدارة أوامر الشراء - Purchase Orders")
        self.setGeometry(50, 50, 1600, 900)
        
        self._create_widgets()
        self._setup_connections()
        self._load_purchase_orders()
    
    def _create_widgets(self):
        """إنشاء عناصر الواجهة"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # شريط الأدوات العلوي
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        # المحتوى الرئيسي
        splitter = QSplitter(Qt.Horizontal)
        
        # القائمة اليسرى
        list_widget = self._create_po_list()
        splitter.addWidget(list_widget)
        
        # التفاصيل اليمنى
        details_widget = self._create_po_details()
        splitter.addWidget(details_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # شريط الحالة السفلي
        status_bar = self._create_status_bar()
        layout.addLayout(status_bar)
    
    def _create_toolbar(self):
        """إنشاء شريط الأدوات"""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # زر أمر شراء جديد
        self.new_po_btn = QPushButton("➕ أمر شراء جديد")
        self.new_po_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.new_po_btn.clicked.connect(self._new_purchase_order)
        toolbar.addWidget(self.new_po_btn)
        
        toolbar.addSpacing(20)
        
        # زر تحرير
        self.edit_btn = QPushButton("✏️ تحرير")
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet(self._get_button_style("#FF9800"))
        self.edit_btn.clicked.connect(self._edit_purchase_order)
        toolbar.addWidget(self.edit_btn)
        
        # زر حذف/إلغاء
        self.delete_btn = QPushButton("🗑️ إلغاء")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(self._get_button_style("#F44336"))
        self.delete_btn.clicked.connect(self._cancel_purchase_order)
        toolbar.addWidget(self.delete_btn)
        
        toolbar.addSpacing(20)
        
        # أزرار سير العمل
        workflow_group = QGroupBox("سير العمل")
        workflow_layout = QHBoxLayout(workflow_group)
        
        self.submit_btn = QPushButton("📤 تقديم للموافقة")
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self._submit_for_approval)
        workflow_layout.addWidget(self.submit_btn)
        
        self.approve_btn = QPushButton("✅ موافقة")
        self.approve_btn.setEnabled(False)
        self.approve_btn.clicked.connect(self._approve_po)
        workflow_layout.addWidget(self.approve_btn)
        
        self.send_btn = QPushButton("📧 إرسال للمورد")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self._send_to_supplier)
        workflow_layout.addWidget(self.send_btn)
        
        self.receive_btn = QPushButton("📦 استلام")
        self.receive_btn.setEnabled(False)
        self.receive_btn.clicked.connect(self._receive_shipment)
        workflow_layout.addWidget(self.receive_btn)
        
        toolbar.addWidget(workflow_group)
        
        toolbar.addStretch()
        
        # الفلاتر
        filters_group = QGroupBox("الفلاتر")
        filters_layout = QHBoxLayout(filters_group)
        
        filters_layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("الكل", None)
        for status in POStatus:
            self.status_filter.addItem(status.value, status)
        self.status_filter.currentIndexChanged.connect(self._filter_pos)
        filters_layout.addWidget(self.status_filter)
        
        filters_layout.addWidget(QLabel("الأولوية:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItem("الكل", None)
        for priority in POPriority:
            self.priority_filter.addItem(priority.value, priority)
        self.priority_filter.currentIndexChanged.connect(self._filter_pos)
        filters_layout.addWidget(self.priority_filter)
        
        toolbar.addWidget(filters_group)
        
        # زر تحديث
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setStyleSheet(self._get_button_style("#607D8B"))
        refresh_btn.clicked.connect(self._load_purchase_orders)
        toolbar.addWidget(refresh_btn)
        
        return toolbar
    
    def _create_po_list(self):
        """إنشاء قائمة أوامر الشراء"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # عنوان
        header = QLabel("<b style='font-size: 16px;'>📋 أوامر الشراء</b>")
        layout.addWidget(header)
        
        # الجدول
        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(8)
        self.pos_table.setHorizontalHeaderLabels([
            "رقم الأمر", "المورد", "التاريخ", "المطلوب في",
            "الحالة", "الأولوية", "الإجمالي", "الاستلام %"
        ])
        
        header = self.pos_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        self.pos_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pos_table.setSelectionMode(QTableWidget.SingleSelection)
        self.pos_table.setAlternatingRowColors(True)
        self.pos_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E0E0E0;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: #BBDEFB;
                color: black;
            }
        """)
        
        layout.addWidget(self.pos_table)
        
        return widget
    
    def _create_po_details(self):
        """إنشاء تبويبات التفاصيل"""
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        
        # تبويب: معلومات عامة
        info_tab = self._create_info_tab()
        tabs.addTab(info_tab, "📄 المعلومات العامة")
        
        # تبويب: البنود
        items_tab = self._create_items_tab()
        tabs.addTab(items_tab, "📦 البنود")
        
        # تبويب: الموافقات
        approval_tab = self._create_approval_tab()
        tabs.addTab(approval_tab, "✅ الموافقات")
        
        # تبويب: الاستلام
        receiving_tab = self._create_receiving_tab()
        tabs.addTab(receiving_tab, "📥 الاستلام")
        
        return tabs
    
    def _create_info_tab(self):
        """تبويب المعلومات العامة"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # معلومات أساسية
        basic_group = QGroupBox("معلومات أساسية")
        basic_layout = QFormLayout(basic_group)
        
        self.po_number_label = QLabel()
        basic_layout.addRow("<b>رقم الأمر:</b>", self.po_number_label)
        
        self.po_status_label = QLabel()
        basic_layout.addRow("<b>الحالة:</b>", self.po_status_label)
        
        self.po_priority_label = QLabel()
        basic_layout.addRow("<b>الأولوية:</b>", self.po_priority_label)
        
        self.po_order_date_label = QLabel()
        basic_layout.addRow("<b>تاريخ الأمر:</b>", self.po_order_date_label)
        
        self.po_required_date_label = QLabel()
        basic_layout.addRow("<b>التاريخ المطلوب:</b>", self.po_required_date_label)
        
        layout.addWidget(basic_group)
        
        # معلومات المورد
        supplier_group = QGroupBox("معلومات المورد")
        supplier_layout = QFormLayout(supplier_group)
        
        self.supplier_name_label = QLabel()
        supplier_layout.addRow("<b>اسم المورد:</b>", self.supplier_name_label)
        
        self.supplier_contact_label = QLabel()
        supplier_layout.addRow("<b>جهة الاتصال:</b>", self.supplier_contact_label)
        
        layout.addWidget(supplier_group)
        
        # الشروط
        terms_group = QGroupBox("الشروط")
        terms_layout = QFormLayout(terms_group)
        
        self.delivery_terms_label = QLabel()
        terms_layout.addRow("<b>شروط التسليم:</b>", self.delivery_terms_label)
        
        self.payment_terms_label = QLabel()
        terms_layout.addRow("<b>شروط الدفع:</b>", self.payment_terms_label)
        
        layout.addWidget(terms_group)
        
        # المبالغ
        amounts_group = QGroupBox("المبالغ")
        amounts_layout = QFormLayout(amounts_group)
        
        self.subtotal_label = QLabel()
        amounts_layout.addRow("<b>المجموع الفرعي:</b>", self.subtotal_label)
        
        self.discount_label = QLabel()
        amounts_layout.addRow("<b>الخصم:</b>", self.discount_label)
        
        self.tax_label = QLabel()
        amounts_layout.addRow("<b>الضريبة:</b>", self.tax_label)
        
        self.shipping_label = QLabel()
        amounts_layout.addRow("<b>الشحن:</b>", self.shipping_label)
        
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        amounts_layout.addRow("<b>الإجمالي:</b>", self.total_label)
        
        layout.addWidget(amounts_group)
        
        # الملاحظات
        notes_group = QGroupBox("الملاحظات")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_text)
        
        layout.addWidget(notes_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _create_items_tab(self):
        """تبويب البنود"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # جدول البنود
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(9)
        self.items_table.setHorizontalHeaderLabels([
            "المنتج", "الكود", "الكمية المطلوبة", "المستلمة",
            "المتبقية", "السعر", "الخصم%", "الضريبة%", "الصافي"
        ])
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.items_table.setAlternatingRowColors(True)
        layout.addWidget(self.items_table)
        
        # ملخص البنود
        summary = QLabel()
        summary.setStyleSheet("background-color: #E3F2FD; padding: 10px; font-weight: bold;")
        self.items_summary_label = summary
        layout.addWidget(summary)
        
        return widget
    
    def _create_approval_tab(self):
        """تبويب الموافقات"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # معلومات الموافقة
        approval_group = QGroupBox("معلومات الموافقة")
        approval_layout = QFormLayout(approval_group)
        
        self.approved_by_label = QLabel("-")
        approval_layout.addRow("<b>تمت الموافقة بواسطة:</b>", self.approved_by_label)
        
        self.approval_date_label = QLabel("-")
        approval_layout.addRow("<b>تاريخ الموافقة:</b>", self.approval_date_label)
        
        self.approval_notes_text = QTextEdit()
        self.approval_notes_text.setReadOnly(True)
        self.approval_notes_text.setMaximumHeight(80)
        approval_layout.addRow("<b>ملاحظات الموافقة:</b>", self.approval_notes_text)
        
        layout.addWidget(approval_group)
        
        # معلومات الإرسال
        sending_group = QGroupBox("معلومات الإرسال")
        sending_layout = QFormLayout(sending_group)
        
        self.sent_date_label = QLabel("-")
        sending_layout.addRow("<b>تاريخ الإرسال:</b>", self.sent_date_label)
        
        self.confirmed_date_label = QLabel("-")
        sending_layout.addRow("<b>تاريخ التأكيد:</b>", self.confirmed_date_label)
        
        self.confirmed_by_supplier_label = QLabel("-")
        sending_layout.addRow("<b>تم التأكيد من المورد:</b>", self.confirmed_by_supplier_label)
        
        layout.addWidget(sending_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_receiving_tab(self):
        """تبويب الاستلام"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # ملخص الاستلام
        summary_group = QGroupBox("ملخص الاستلام")
        summary_layout = QFormLayout(summary_group)
        
        self.total_ordered_label = QLabel("0")
        summary_layout.addRow("<b>إجمالي المطلوب:</b>", self.total_ordered_label)
        
        self.total_received_label = QLabel("0")
        summary_layout.addRow("<b>إجمالي المستلم:</b>", self.total_received_label)
        
        self.receipt_percentage_label = QLabel("0%")
        self.receipt_percentage_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        summary_layout.addRow("<b>نسبة الاستلام:</b>", self.receipt_percentage_label)
        
        layout.addWidget(summary_group)
        
        # قائمة إشعارات الاستلام
        receiving_notes_group = QGroupBox("إشعارات الاستلام")
        rn_layout = QVBoxLayout(receiving_notes_group)
        
        self.receiving_notes_table = QTableWidget()
        self.receiving_notes_table.setColumnCount(5)
        self.receiving_notes_table.setHorizontalHeaderLabels([
            "رقم الإشعار", "التاريخ", "الحالة", "المستلم", "الملاحظات"
        ])
        
        header = self.receiving_notes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        rn_layout.addWidget(self.receiving_notes_table)
        
        layout.addWidget(receiving_notes_group)
        
        return widget
    
    def _create_status_bar(self):
        """إنشاء شريط الحالة"""
        statusbar = QHBoxLayout()
        
        self.total_pos_label = QLabel("إجمالي الأوامر: 0")
        statusbar.addWidget(self.total_pos_label)
        
        statusbar.addSpacing(20)
        
        self.total_value_label = QLabel("القيمة الإجمالية: 0 ريال")
        statusbar.addWidget(self.total_value_label)
        
        statusbar.addStretch()
        
        self.status_message = QLabel("جاهز")
        statusbar.addWidget(self.status_message)
        
        return statusbar
    
    def _setup_connections(self):
        """إعداد الاتصالات"""
        self.pos_table.itemSelectionChanged.connect(self._on_po_selected)
    
    def _load_purchase_orders(self):
        """تحميل أوامر الشراء"""
        try:
            pos = self.po_service.get_all_purchase_orders(limit=500)
            
            self.pos_table.setRowCount(0)
            total_value = Decimal('0.00')
            
            for po in pos:
                row = self.pos_table.rowCount()
                self.pos_table.insertRow(row)
                
                # رقم الأمر
                self.pos_table.setItem(row, 0, QTableWidgetItem(po.po_number))
                
                # المورد
                self.pos_table.setItem(row, 1, QTableWidgetItem(po.supplier_name or ""))
                
                # تاريخ الأمر
                date_str = po.order_date.strftime("%Y-%m-%d") if po.order_date else ""
                self.pos_table.setItem(row, 2, QTableWidgetItem(date_str))
                
                # التاريخ المطلوب
                req_date_str = po.required_date.strftime("%Y-%m-%d") if po.required_date else ""
                req_item = QTableWidgetItem(req_date_str)
                if po.is_overdue:
                    req_item.setBackground(QColor("#FFEBEE"))
                    req_item.setForeground(QColor("#D32F2F"))
                self.pos_table.setItem(row, 3, req_item)
                
                # الحالة
                status_item = QTableWidgetItem(po.status.value if hasattr(po.status, 'value') else str(po.status))
                status_item.setBackground(QColor(self._get_status_color(po.status)))
                self.pos_table.setItem(row, 4, status_item)
                
                # الأولوية
                priority_item = QTableWidgetItem(po.priority.value if hasattr(po.priority, 'value') else str(po.priority))
                priority_item.setBackground(QColor(self._get_priority_color(po.priority)))
                self.pos_table.setItem(row, 5, priority_item)
                
                # الإجمالي
                total_item = QTableWidgetItem(f"{po.total_amount:,.2f}")
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.pos_table.setItem(row, 6, total_item)
                
                # نسبة الاستلام
                receipt_pct = po.receipt_percentage
                receipt_item = QTableWidgetItem(f"{receipt_pct:.1f}%")
                receipt_item.setTextAlignment(Qt.AlignCenter)
                if receipt_pct >= 100:
                    receipt_item.setBackground(QColor("#C8E6C9"))
                elif receipt_pct > 0:
                    receipt_item.setBackground(QColor("#FFF9C4"))
                self.pos_table.setItem(row, 7, receipt_item)
                
                # حفظ المعرف
                self.pos_table.item(row, 0).setData(Qt.UserRole, po.id)
                
                total_value += po.total_amount
            
            # تحديث الإحصائيات
            self.total_pos_label.setText(f"إجمالي الأوامر: {len(pos)}")
            self.total_value_label.setText(f"القيمة الإجمالية: {total_value:,.2f} ريال")
            
            self.status_message.setText(f"تم تحميل {len(pos)} أمر شراء")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل أوامر الشراء: {str(e)}")
    
    def _filter_pos(self):
        """تصفية أوامر الشراء"""
        status = self.status_filter.currentData()
        priority = self.priority_filter.currentData()
        
        try:
            pos = self.po_service.get_all_purchase_orders(
                status=status,
                priority=priority,
                limit=500
            )
            
            self._update_table_with_pos(pos)
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل التصفية: {str(e)}")
    
    def _update_table_with_pos(self, pos):
        """تحديث الجدول بأوامر الشراء"""
        # (نفس محتوى _load_purchase_orders)
        pass
    
    def _on_po_selected(self):
        """عند اختيار أمر شراء"""
        selected = self.pos_table.selectedItems()
        if not selected:
            self._clear_details()
            self._update_buttons_state()
            return
        
        row = selected[0].row()
        po_id = self.pos_table.item(row, 0).data(Qt.UserRole)
        
        try:
            self.current_po = self.po_service.get_purchase_order(po_id)
            if self.current_po:
                self._display_po_details(self.current_po)
                self._update_buttons_state()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل تحميل التفاصيل: {str(e)}")
    
    def _display_po_details(self, po: PurchaseOrder):
        """عرض تفاصيل أمر الشراء"""
        # المعلومات الأساسية
        self.po_number_label.setText(po.po_number)
        self.po_status_label.setText(po.status.value if hasattr(po.status, 'value') else str(po.status))
        self.po_priority_label.setText(po.priority.value if hasattr(po.priority, 'value') else str(po.priority))
        self.po_order_date_label.setText(po.order_date.strftime("%Y-%m-%d") if po.order_date else "-")
        self.po_required_date_label.setText(po.required_date.strftime("%Y-%m-%d") if po.required_date else "-")
        
        # معلومات المورد
        self.supplier_name_label.setText(po.supplier_name or "-")
        self.supplier_contact_label.setText(po.supplier_contact or "-")
        
        # الشروط
        self.delivery_terms_label.setText(po.delivery_terms.value if hasattr(po.delivery_terms, 'value') else str(po.delivery_terms))
        self.payment_terms_label.setText(po.payment_terms.value if hasattr(po.payment_terms, 'value') else str(po.payment_terms))
        
        # المبالغ
        self.subtotal_label.setText(f"{po.subtotal:,.2f} {po.currency}")
        self.discount_label.setText(f"{po.discount_amount:,.2f} {po.currency}")
        self.tax_label.setText(f"{po.tax_amount:,.2f} {po.currency}")
        self.shipping_label.setText(f"{po.shipping_cost:,.2f} {po.currency}")
        self.total_label.setText(f"{po.total_amount:,.2f} {po.currency}")
        
        # الملاحظات
        self.notes_text.setPlainText(po.notes or "")
        
        # البنود
        self._display_po_items(po.items)
        
        # الموافقات
        self._display_approval_info(po)
        
        # الاستلام
        self._display_receiving_info(po)
    
    def _display_po_items(self, items):
        """عرض بنود أمر الشراء"""
        self.items_table.setRowCount(0)
        
        total_qty_ordered = Decimal('0')
        total_qty_received = Decimal('0')
        
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            
            self.items_table.setItem(row, 0, QTableWidgetItem(item.product_name))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.product_code or ""))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{item.quantity_ordered:,.3f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item.quantity_received:,.3f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{item.quantity_pending:,.3f}"))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{item.unit_price:,.2f}"))
            self.items_table.setItem(row, 6, QTableWidgetItem(f"{item.discount_percent:.2f}%"))
            self.items_table.setItem(row, 7, QTableWidgetItem(f"{item.tax_percent:.2f}%"))
            self.items_table.setItem(row, 8, QTableWidgetItem(f"{item.net_amount:,.2f}"))
            
            total_qty_ordered += item.quantity_ordered
            total_qty_received += item.quantity_received
        
        # الملخص
        summary_text = f"إجمالي البنود: {len(items)} | "
        summary_text += f"الكمية المطلوبة: {total_qty_ordered:,.3f} | "
        summary_text += f"المستلمة: {total_qty_received:,.3f}"
        self.items_summary_label.setText(summary_text)
    
    def _display_approval_info(self, po: PurchaseOrder):
        """عرض معلومات الموافقة"""
        if po.approved_by:
            self.approved_by_label.setText(f"مستخدم #{po.approved_by}")
        else:
            self.approved_by_label.setText("-")
        
        if po.approval_date:
            self.approval_date_label.setText(po.approval_date.strftime("%Y-%m-%d"))
        else:
            self.approval_date_label.setText("-")
        
        self.approval_notes_text.setPlainText(po.approval_notes or "")
        
        if po.sent_date:
            self.sent_date_label.setText(po.sent_date.strftime("%Y-%m-%d"))
        else:
            self.sent_date_label.setText("-")
        
        if po.confirmed_date:
            self.confirmed_date_label.setText(po.confirmed_date.strftime("%Y-%m-%d"))
        else:
            self.confirmed_date_label.setText("-")
        
        self.confirmed_by_supplier_label.setText("نعم" if po.confirmed_by_supplier else "لا")
    
    def _display_receiving_info(self, po: PurchaseOrder):
        """عرض معلومات الاستلام"""
        self.total_ordered_label.setText(f"{po.total_quantity_ordered:,.3f}")
        self.total_received_label.setText(f"{po.total_quantity_received:,.3f}")
        self.receipt_percentage_label.setText(f"{po.receipt_percentage:.1f}%")
        
        # TODO: تحميل إشعارات الاستلام
        self.receiving_notes_table.setRowCount(0)
    
    def _clear_details(self):
        """مسح التفاصيل"""
        self.current_po = None
        # مسح جميع Labels و TextEdits
    
    def _update_buttons_state(self):
        """تحديث حالة الأزرار"""
        has_selection = self.current_po is not None
        
        self.edit_btn.setEnabled(has_selection and self.current_po.can_be_edited if has_selection else False)
        self.delete_btn.setEnabled(has_selection and self.current_po.is_draft if has_selection else False)
        
        if has_selection:
            self.submit_btn.setEnabled(self.current_po.is_draft)
            self.approve_btn.setEnabled(self.current_po.status == POStatus.PENDING_APPROVAL)
            self.send_btn.setEnabled(self.current_po.is_approved)
            self.receive_btn.setEnabled(self.current_po.can_receive if hasattr(self.current_po, 'can_receive') else False)
        else:
            self.submit_btn.setEnabled(False)
            self.approve_btn.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.receive_btn.setEnabled(False)
    
    def _new_purchase_order(self):
        """أمر شراء جديد"""
        dialog = PurchaseOrderDialog(self.db, parent=self)
        if dialog.exec() == QDialog.Accepted:
            po = dialog.get_purchase_order()
            if po:
                try:
                    po_id = self.po_service.create_purchase_order(po)
                    QMessageBox.information(self, "نجح", f"تم إنشاء أمر الشراء: {po.po_number}")
                    self._load_purchase_orders()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل إنشاء أمر الشراء: {str(e)}")
    
    def _edit_purchase_order(self):
        """تحرير أمر شراء"""
        if not self.current_po:
            return
        
        dialog = PurchaseOrderDialog(self.db, po=self.current_po, parent=self)
        if dialog.exec() == QDialog.Accepted:
            po = dialog.get_purchase_order()
            if po:
                try:
                    self.po_service.update_purchase_order(po)
                    QMessageBox.information(self, "نجح", "تم تحديث أمر الشراء")
                    self._load_purchase_orders()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل التحديث: {str(e)}")
    
    def _cancel_purchase_order(self):
        """إلغاء أمر شراء"""
        if not self.current_po:
            return
        
        reply = QMessageBox.question(
            self, "تأكيد الإلغاء",
            f"هل أنت متأكد من إلغاء أمر الشراء {self.current_po.po_number}؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.current_po.cancel()
                self.po_service.update_purchase_order(self.current_po)
                QMessageBox.information(self, "نجح", "تم إلغاء أمر الشراء")
                self._load_purchase_orders()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل الإلغاء: {str(e)}")
    
    def _submit_for_approval(self):
        """تقديم للموافقة"""
        if not self.current_po:
            return
        
        try:
            if self.po_service.submit_for_approval(self.current_po.id, submitted_by=1):  # TODO: الحصول على ID المستخدم الحالي
                QMessageBox.information(self, "نجح", "تم تقديم الأمر للموافقة")
                self._load_purchase_orders()
            else:
                QMessageBox.warning(self, "فشل", "لا يمكن تقديم هذا الأمر للموافقة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التقديم: {str(e)}")
    
    def _approve_po(self):
        """الموافقة على أمر شراء"""
        if not self.current_po:
            return
        
        try:
            if self.po_service.approve_purchase_order(self.current_po.id, approved_by=1):  # TODO: ID المستخدم
                QMessageBox.information(self, "نجح", "تمت الموافقة على أمر الشراء")
                self._load_purchase_orders()
            else:
                QMessageBox.warning(self, "فشل", "لا يمكن الموافقة على هذا الأمر")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشلت الموافقة: {str(e)}")
    
    def _send_to_supplier(self):
        """إرسال إلى المورد"""
        if not self.current_po:
            return
        
        try:
            if self.po_service.send_to_supplier(self.current_po.id):
                QMessageBox.information(self, "نجح", "تم إرسال أمر الشراء إلى المورد")
                self._load_purchase_orders()
            else:
                QMessageBox.warning(self, "فشل", "لا يمكن إرسال هذا الأمر")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الإرسال: {str(e)}")
    
    def _receive_shipment(self):
        """استلام شحنة"""
        if not self.current_po:
            return
        
        dialog = ReceivingDialog(self.db, self.current_po, parent=self)
        if dialog.exec() == QDialog.Accepted:
            receiving_note = dialog.get_receiving_note()
            if receiving_note:
                try:
                    self.po_service.receive_shipment(self.current_po.id, receiving_note)
                    QMessageBox.information(self, "نجح", f"تم استلام الشحنة: {receiving_note.receiving_number}")
                    self._load_purchase_orders()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل الاستلام: {str(e)}")
    
    def _get_button_style(self, color):
        """أسلوب الزر"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #757575;
            }}
        """
    
    def _get_status_color(self, status):
        """لون الحالة"""
        colors = {
            POStatus.DRAFT: "#E0E0E0",
            POStatus.PENDING_APPROVAL: "#FFF9C4",
            POStatus.APPROVED: "#C8E6C9",
            POStatus.SENT: "#BBDEFB",
            POStatus.CONFIRMED: "#B2DFDB",
            POStatus.PARTIALLY_RECEIVED: "#FFE0B2",
            POStatus.FULLY_RECEIVED: "#A5D6A7",
            POStatus.CLOSED: "#CFD8DC",
            POStatus.CANCELLED: "#FFCDD2"
        }
        return colors.get(status, "#FFFFFF")
    
    def _get_priority_color(self, priority):
        """لون الأولوية"""
        colors = {
            POPriority.LOW: "#E8F5E9",
            POPriority.NORMAL: "#FFF9C4",
            POPriority.HIGH: "#FFE0B2",
            POPriority.URGENT: "#FFCDD2"
        }
        return colors.get(priority, "#FFFFFF")
