#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حوار تعديل المخزون
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QDoubleSpinBox, QLineEdit, QLabel, QPushButton,
    QMessageBox, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QWidget
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from ...utils.i18n_api import I18n

from src.ui.widgets.custom_title_bar import CustomTitleBar
from src.ui.widgets.quantum_notification import NotificationManager


class AdjustStockDialog(QDialog):
    """واجهة بسيطة لتعديل كمية مخزون منتج"""
    
    stock_adjusted = Signal()
    
    def __init__(self, inventory_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.product_manager = inventory_service.product_manager
        self.products = self.product_manager.get_all_products(active_only=True)
        
        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))
        
        # self.setWindowTitle(self.i18n.get_message("adjust_stock_title"))
        # self.setMinimumWidth(400)
        
        # --- Quantum Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Notifications
        self.notify = NotificationManager(self)
        
        self.resize(450, 400) # Slightly larger
        
        self._build_ui()
        self._populate_products()
    
    def _build_ui(self):
        # تخطيط جذري شفاف
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)
        
        # الإطار الرئيسي
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #f5f5f5;
                border: 1px solid #3498db;
                border-radius: 10px;
            }
        """)
        self.main_frame.setObjectName("MainFrame")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor("#3498db"))
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)
        
        root_layout.addWidget(self.main_frame)
        
        # تخطيط النافذة الداخلية
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(0)
        
        # 1. Custom Title Bar
        self.title_bar = CustomTitleBar(self, title=self.i18n.get_message("adjust_stock_title"), is_dialog=True)
        layout.addWidget(self.title_bar)
        
        # Container for content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(content_widget)
        
        # Re-assign layout to content_layout for the existing widget helpers
        layout = content_layout
        
        form = QFormLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        form.addRow(self.i18n.get_message("table_product") + ":", self.product_combo)
        
        self.current_stock_label = QLabel("-")
        form.addRow(self.i18n.get_message("current_stock") + ":", self.current_stock_label)
        
        self.new_quantity_spin = QDoubleSpinBox()
        self.new_quantity_spin.setRange(0, 10_000_000)
        self.new_quantity_spin.setDecimals(3)
        form.addRow(self.i18n.get_message("new_quantity") + ":", self.new_quantity_spin)
        
        self.reason_input = QLineEdit()
        form.addRow(self.i18n.get_message("reason_optional") + ":", self.reason_input)
        
        layout.addLayout(form)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        save_btn = QPushButton(self.i18n.get_message("save"))
        save_btn.clicked.connect(self._handle_save)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(self.i18n.get_message("cancel"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _populate_products(self):
        self.product_combo.clear()
        for product in self.products:
            display = self.i18n.get_message("product_display", name=product.name, id=product.id)
            self.product_combo.addItem(display, product)
        if self.products:
            self._on_product_changed(0)
    
    def _on_product_changed(self, index: int):
        product = self.product_combo.itemData(index)
        if not product:
            self.current_stock_label.setText("-")
            self.new_quantity_spin.setValue(0)
            return
        self.current_stock_label.setText(str(product.current_stock))
        self.new_quantity_spin.setValue(float(product.current_stock))
    
    def _handle_save(self):
        product = self.product_combo.currentData()
        if not product:
            self.notify.show_warning(self.i18n.get_message("warning"), self.i18n.get_message("select_product"))
            return
        
        new_quantity = self.new_quantity_spin.value()
        reason = self.reason_input.text().strip()
        
        try:
            success = self.inventory_service.adjust_stock(
                product_id=product.id,
                new_quantity=new_quantity,
                reason=reason or self.i18n.get_message("adjust_via_ui")
            )
            if success:
                # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                try:
                    from ...core.signals import signals
                    signals.inventory_updated.emit()
                    signals.stock_adjusted.emit(product.id)
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.debug(f"✅ تم إطلاق إشارات: inventory_updated, stock_adjusted")
                except Exception as e:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
                
                self.notify.show_success(self.i18n.get_message("success"), self.i18n.get_message("stock_adjusted_success"))
                self.stock_adjusted.emit()
                self.accept()
            else:
                self.notify.show_warning(self.i18n.get_message("warning"), self.i18n.get_message("stock_adjust_failed"))
        except Exception as e:
            self.notify.show_error(self.i18n.get_message("error"), f"{self.i18n.get_message('stock_adjust_error')}:\n{str(e)}")

