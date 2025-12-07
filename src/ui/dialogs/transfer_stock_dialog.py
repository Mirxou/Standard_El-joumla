#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حوار نقل المخزون بين المنتجات
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QDoubleSpinBox, QLineEdit, QPushButton, QMessageBox,
    QHBoxLayout
)
from PySide6.QtCore import Signal
from pathlib import Path
from ...utils.i18n_api import I18n


class TransferStockDialog(QDialog):
    """واجهة مبسطة لنقل الكميات بين منتجين"""
    
    transfer_completed = Signal()
    
    def __init__(self, inventory_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.product_manager = inventory_service.product_manager
        self.products = self.product_manager.get_all_products(active_only=True)
        
        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))
        
        self.setWindowTitle(self.i18n.get_message("transfer_stock_title"))
        self.setMinimumWidth(420)
        self._build_ui()
        self._populate_products()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.from_combo = QComboBox()
        form.addRow(self.i18n.get_message("from_product") + ":", self.from_combo)
        
        self.to_combo = QComboBox()
        form.addRow(self.i18n.get_message("to_product") + ":", self.to_combo)
        
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.001, 10_000_000)
        self.quantity_spin.setDecimals(3)
        form.addRow(self.i18n.get_message("table_quantity") + ":", self.quantity_spin)
        
        self.reason_input = QLineEdit()
        form.addRow(self.i18n.get_message("reason_optional") + ":", self.reason_input)
        
        layout.addLayout(form)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        save_btn = QPushButton(self.i18n.get_message("execute_transfer"))
        save_btn.clicked.connect(self._handle_transfer)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(self.i18n.get_message("cancel"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _populate_products(self):
        self.from_combo.clear()
        self.to_combo.clear()
        for product in self.products:
            display = self.i18n.get_message("product_display_with_stock", name=product.name, id=product.id, stock=product.current_stock)
            self.from_combo.addItem(display, product)
            self.to_combo.addItem(display, product)
        if self.products:
            self.from_combo.setCurrentIndex(0)
            if len(self.products) > 1:
                self.to_combo.setCurrentIndex(1)
    
    def _handle_transfer(self):
        from_product = self.from_combo.currentData()
        to_product = self.to_combo.currentData()
        quantity = self.quantity_spin.value()
        reason = self.reason_input.text().strip()
        
        if not from_product or not to_product:
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("select_products"))
            return
        if from_product.id == to_product.id:
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("cannot_transfer_same_product"))
            return
        if quantity <= 0:
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("enter_valid_quantity"))
            return
        
        try:
            success = self.inventory_service.transfer_stock(
                from_product_id=from_product.id,
                to_product_id=to_product.id,
                quantity=quantity,
                reason=reason or self.i18n.get_message("transfer_via_ui")
            )
            if success:
                # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                try:
                    from ...core.signals import signals
                    signals.inventory_updated.emit()
                    signals.stock_transferred.emit()
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.debug(f"✅ تم إطلاق إشارات: inventory_updated, stock_transferred")
                except Exception as e:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
                
                QMessageBox.information(self, self.i18n.get_message("success"), self.i18n.get_message("stock_transferred_success"))
                self.transfer_completed.emit()
                self.accept()
            else:
                QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("transfer_failed"))
        except Exception as e:
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('transfer_error')}:\n{str(e)}")

