#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حوار تعديل المخزون
"""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from src.ui.widgets.base_dialog import BaseDialog
from src.ui.widgets.quantum_notification import NotificationManager

from ...utils.i18n_api import I18n


class AdjustStockDialog(BaseDialog):
    """واجهة بسيطة لتعديل كمية مخزون منتج"""

    stock_adjusted = Signal()

    def __init__(self, inventory_service, parent=None):
        super().__init__(title="", parent=parent)
        self.inventory_service = inventory_service
        self.product_manager = inventory_service.product_manager
        self.products = self.product_manager.get_all_products(active_only=True)

        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        # self.setWindowTitle(self.i18n.get_message("adjust_stock_title"))
        # self.setMinimumWidth(400)

        # --- Quantum Window Setup ---
        # Notifications
        self.notify = NotificationManager(self)

        self.resize(450, 400)  # Slightly larger

        self._build_ui()
        self._populate_products()

    def _build_ui(self):
        layout = self.content_layout

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
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                self.i18n.get_message("select_product"),
            )
            return

        new_quantity = self.new_quantity_spin.value()
        reason = self.reason_input.text().strip()

        try:
            success = self.inventory_service.adjust_stock(
                product_id=product.id,
                new_quantity=new_quantity,
                reason=reason or self.i18n.get_message("adjust_via_ui"),
            )
            if success:
                # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                try:
                    from ...core.signals import signals

                    signals.inventory_updated.emit()
                    signals.stock_adjusted.emit(product.id)
                    if hasattr(self, "logger") and self.logger:
                        self.logger.debug("✅ تم إطلاق إشارات: inventory_updated, stock_adjusted")
                except Exception as e:
                    if hasattr(self, "logger") and self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")

                self.notify.show_success(
                    self.i18n.get_message("success"),
                    self.i18n.get_message("stock_adjusted_success"),
                )
                self.stock_adjusted.emit()
                self.accept()
            else:
                self.notify.show_warning(
                    self.i18n.get_message("warning"),
                    self.i18n.get_message("stock_adjust_failed"),
                )
        except Exception as e:
            self.notify.show_error(
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('stock_adjust_error')}:\n{str(e)}",
            )
