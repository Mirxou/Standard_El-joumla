import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
واجهة المبيعات المدمجة - Blended Sales UI
واجهة تتكيف تلقائياً بين وضع B2B و B2C حسب نوع العميل
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.database_manager import DatabaseManager
from src.models.customer import Customer
from src.models.sale import PaymentMethod, Sale, SaleItem, SaleStatus
from src.services.cpq_service import CPQService
from src.services.dynamic_pricing_engine import DynamicPricingEngine
from src.services.pricing_service import PricingService
from src.services.sales_service import SalesService
from src.ui.components.ai_components import AIButton, AIPromptInput
from src.utils.logger import setup_logger
from src.utils.math_utils import to_decimal


class PriceUpdateWorker(QObject):
    """عامل تحديث الأسعار في الخلفية"""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, pricing_service, dynamic_pricing, product_id, customer, quantity):
        super().__init__()
        self.pricing_service = pricing_service
        self.dynamic_pricing = dynamic_pricing
        self.product_id = product_id
        self.customer = customer
        self.quantity = quantity

    def run(self):
        try:
            # Get base price
            base_price = self.pricing_service.get_price_for_customer(self.product_id, self.customer, self.quantity)

            # Get dynamic adjustments
            final_price = self.dynamic_pricing.adjust_price(
                base_price, self.product_id, self.customer, Decimal(str(self.quantity))
            )

            # Get pricing insights
            insights = self.dynamic_pricing.get_pricing_insights(
                self.product_id, self.customer, Decimal(str(self.quantity))
            )

            result = {
                "base_price": base_price,
                "final_price": final_price,
                "insights": insights,
            }

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class SaleCreationWorker(QObject):
    """عامل إنشاء المبيعات وعروض الأسعار في الخلفية"""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, mode, customer, cart_items, cpq_service, sales_service):
        super().__init__()
        self.mode = mode  # 'quote' or 'sale'
        self.customer = customer
        self.cart_items = cart_items
        self.cpq_service = cpq_service
        self.sales_service = sales_service

    def run(self):
        try:
            if self.mode == "quote":
                items_data = []
                for item in self.cart_items:
                    items_data.append(
                        {
                            "product_id": item["product_id"],
                            "quantity": item["quantity"],
                            "custom_discount": 0,
                        }
                    )
                quote = self.cpq_service.create_quote(
                    self.customer.id,
                    items_data,
                    valid_days=30,
                    notes="تم إنشاؤه من واجهة المبيعات المدمجة",
                )
                if quote:
                    self.finished.emit({"type": "quote", "id": quote.id, "total": float(quote.total)})
                else:
                    self.error.emit("فشل في إنشاء عرض الأسعار")
            else:
                # إنشاء مبيعة حقيقية
                sale = Sale(
                    invoice_number=self.sales_service._generate_invoice_number(),
                    customer_id=self.customer.id,
                    sale_date=date.today(),
                    status=SaleStatus.CONFIRMED,
                    payment_method=PaymentMethod.CASH,
                    items=[],
                )
                subtotal = sum(item.get("final_price", 0) * item["quantity"] for item in self.cart_items)
                sale.total_amount = to_decimal(subtotal)
                sale.final_amount = sale.total_amount
                sale.paid_amount = sale.final_amount
                sale.remaining_amount = Decimal("0")

                for item in self.cart_items:
                    sale_item = SaleItem(
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                        unit_price=to_decimal(item.get("final_price", 0)),
                        discount=Decimal("0"),
                    )
                    sale_item.calculate_totals()
                    sale.items.append(sale_item)

                # Use sales_service.create_sale to trigger inventory and accounting
                sale_id = self.sales_service.create_sale(sale)
                if sale_id:
                    self.finished.emit({"type": "sale", "id": sale_id, "total": float(subtotal)})
                else:
                    self.error.emit("فشل في إنشاء المبيعة في قاعدة البيانات أو الكمية غير متوفرة")

        except Exception as e:
            self.error.emit(str(e))


class BlendedSalesUI(QWidget):
    """واجهة المبيعات المدمجة المتكيفة"""

    # Signals
    sale_completed = Signal(dict)  # {'sale_id': int, 'total': float, 'customer': Customer}
    quote_created = Signal(dict)  # {'quote_id': int, 'total': float, 'customer': Customer}

    def __init__(self, db_manager: DatabaseManager, user_id: int):
        super().__init__()
        self.db = db_manager
        self.user_id = user_id
        self.logger = setup_logger(__name__)

        # Initialize services
        self.pricing_service = PricingService(self.db)
        self.cpq_service = CPQService(self.db, self.pricing_service)
        self.dynamic_pricing = DynamicPricingEngine(self.db)
        self.sales_service = SalesService(self.db, self.logger)

        # UI state
        self.current_customer: Optional[Customer] = None
        self.cart_items = []
        self.is_b2b_mode = False
        self.quote_mode = False

        # UI adaptation
        self.ui_adaptation_service = None  # Will be set by parent

        self.init_ui()
        self.setup_connections()
        self.apply_adaptive_styling()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle("نظام المبيعات المدمج - Unified Sales System")
        self.setMinimumSize(1200, 800)

        layout = QHBoxLayout(self)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Customer & Product selection
        self.left_panel = self.create_left_panel()
        splitter.addWidget(self.left_panel)

        # Right panel - Cart & Checkout
        self.right_panel = self.create_right_panel()
        splitter.addWidget(self.right_panel)

        # Set splitter proportions
        splitter.setSizes([400, 800])

        layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("جاهز")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)

    def create_left_panel(self) -> QWidget:
        """إنشاء اللوحة اليسرى - اختيار العميل والمنتج"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Customer selection section
        customer_group = QGroupBox("اختيار العميل")
        customer_layout = QVBoxLayout(customer_group)

        # Customer search
        search_layout = QHBoxLayout()
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("ابحث عن العميل...")
        search_layout.addWidget(self.customer_search)

        self.customer_combo = QComboBox()
        self.customer_combo.addItem("اختر عميل", 0)
        search_layout.addWidget(self.customer_combo)

        customer_layout.addLayout(search_layout)

        # Customer info display
        self.customer_info = QLabel("لم يتم اختيار عميل")
        self.customer_info.setStyleSheet("""
            QLabel {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 10px;
                min-height: 60px;
            }
        """)
        customer_layout.addWidget(self.customer_info)

        layout.addWidget(customer_group)

        # Product selection section
        product_group = QGroupBox("اختيار المنتج")
        product_layout = QVBoxLayout(product_group)

        # Product search and category filter
        filter_layout = QHBoxLayout()

        self.category_combo = QComboBox()
        self.category_combo.addItem("جميع الفئات", "")
        # Will be populated with actual categories
        filter_layout.addWidget(QLabel("الفئة:"))
        filter_layout.addWidget(self.category_combo)

        product_layout.addLayout(filter_layout)

        # Product search
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("ابحث عن المنتج...")
        product_layout.addWidget(self.product_search)

        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["المنتج", "السعر", "المخزون", "الإجراء"])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        product_layout.addWidget(self.products_table)

        layout.addWidget(product_group)

        # AI Prompt Input for natural language product search
        self.ai_prompt = AIPromptInput("اكتب طلبك باللغة الطبيعية...")
        self.ai_prompt.setMaximumHeight(100)
        layout.addWidget(self.ai_prompt)

        return panel

    def create_right_panel(self) -> QWidget:
        """إنشاء اللوحة اليمنى - السلة والدفع"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Mode indicator
        self.mode_indicator = QLabel("وضع B2C")
        self.mode_indicator.setStyleSheet("""
            QLabel {
                background-color: #007bff;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                text-align: center;
            }
        """)
        self.mode_indicator.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.mode_indicator)

        # Cart section
        cart_group = QGroupBox("سلة المشتريات")
        cart_layout = QVBoxLayout(cart_group)

        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["المنتج", "الكمية", "السعر", "الإجمالي", "إزالة"])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        cart_layout.addWidget(self.cart_table)

        # Cart totals
        totals_layout = QVBoxLayout()

        self.subtotal_label = QLabel("المجموع الفرعي: €0.00")
        self.discount_label = QLabel("الخصم: €0.00")
        self.tax_label = QLabel("الضريبة: €0.00")
        self.total_label = QLabel("الإجمالي: €0.00")

        for label in [
            self.subtotal_label,
            self.discount_label,
            self.tax_label,
            self.total_label,
        ]:
            label.setStyleSheet("font-weight: bold; font-size: 14px;")
            totals_layout.addWidget(label)

        cart_layout.addLayout(totals_layout)

        # Quote mode toggle
        self.quote_mode_check = QCheckBox("إنشاء عرض أسعار بدلاً من مبيعة فورية")
        cart_layout.addWidget(self.quote_mode_check)

        layout.addWidget(cart_group)

        # Action buttons
        buttons_layout = QHBoxLayout()

        self.clear_cart_btn = QPushButton("إفراغ السلة")
        self.clear_cart_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")

        self.checkout_btn = AIButton("إتمام الشراء")
        self.checkout_btn.setEnabled(False)

        buttons_layout.addWidget(self.clear_cart_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.checkout_btn)

        layout.addLayout(buttons_layout)

        # Progress indicator for price calculations
        self.price_progress = QProgressBar()
        self.price_progress.setVisible(False)
        layout.addWidget(self.price_progress)

        return panel

    def setup_connections(self):
        """إعداد الاتصالات"""
        # Customer selection
        self.customer_combo.currentIndexChanged.connect(self.on_customer_selected)
        self.customer_search.textChanged.connect(self.on_customer_search)

        # Product selection
        self.product_search.textChanged.connect(self.on_product_search)
        self.category_combo.currentIndexChanged.connect(self.on_category_filter)

        # AI prompt
        self.ai_prompt.prompt_submitted.connect(self.on_ai_prompt_submitted)

        # Cart actions
        self.clear_cart_btn.clicked.connect(self.clear_cart)
        self.checkout_btn.clicked.connect(self.checkout)

        # Quote mode
        self.quote_mode_check.toggled.connect(self.on_quote_mode_toggled)

        # Table interactions
        self.products_table.cellClicked.connect(self.on_product_table_clicked)
        self.cart_table.cellClicked.connect(self.on_cart_table_clicked)

    def apply_adaptive_styling(self):
        """تطبيق التصميم المتكيف"""
        # Apply base styling

        # Adaptive colors based on mode
        self.update_mode_styling()

    def update_mode_styling(self):
        """تحديث ألوان الواجهة حسب الوضع"""
        if self.is_b2b_mode:
            # B2B colors - professional blue
            mode_color = "#007bff"
            mode_text = "وضع B2B"
        else:
            # B2C colors - consumer green
            mode_color = "#28a745"  # noqa: F841
            mode_text = "وضع B2C"

        self.mode_indicator.setText(mode_text)
        self.mode_indicator.setStyleSheet("""
            QLabel {{
                background-color: {mode_color};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                text-align: center;
            }}
        """)

        # Update checkout button color
        self.checkout_btn.setStyleSheet("""
            QPushButton {{
                background-color: {mode_color};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.adjust_color_brightness(mode_color, -20)};
            }}
            QPushButton:pressed {{
                background-color: {self.adjust_color_brightness(mode_color, -40)};
            }}
        """)

    def adjust_color_brightness(self, hex_color: str, brightness_offset: int) -> str:
        """تعديل سطوع اللون"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        # Adjust brightness
        new_rgb = []
        for component in rgb:
            new_component = max(0, min(255, component + brightness_offset))
            new_rgb.append(new_component)

        # Convert back to hex
        return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"

    def set_customer(self, customer: Customer):
        """تعيين العميل الحالي"""
        self.current_customer = customer

        # Update UI mode based on customer type
        self.is_b2b_mode = customer.customer_type == "b2b"
        self.update_mode_styling()

        # Update customer info display
        customer_info = """
        <b>{customer.name}</b><br>
        النوع: {customer.customer_type.title()}<br>
        التصنيف: {customer.pricing_tier or 'قياسي'}
        """

        if hasattr(customer, "total_purchases") and customer.total_purchases:
            customer_info += f"<br>إجمالي المشتريات: €{customer.total_purchases:,.2f}"

        self.customer_info.setText(customer_info)

        # Load customer-specific products and pricing
        self.load_products()
        self.update_cart_totals()

        # Adapt UI based on customer
        self.adapt_ui_for_customer()

    def adapt_ui_for_customer(self):
        """تكييف الواجهة حسب العميل"""
        if not self.current_customer:
            return

        # B2B specific features
        if self.is_b2b_mode:
            self.quote_mode_check.setVisible(True)
            self.quote_mode_check.setChecked(True)  # Default to quote mode for B2B
            self.checkout_btn.setText("إنشاء عرض أسعار")

            # Show bulk pricing options
            self.show_bulk_pricing_options()

        else:
            # B2C features
            self.quote_mode_check.setVisible(False)
            self.checkout_btn.setText("إتمام الشراء")

            # Hide bulk options
            self.hide_bulk_pricing_options()

    def show_bulk_pricing_options(self):
        """إظهار خيارات التسعير بالجملة"""
        # This would add bulk discount indicators, minimum order quantities, etc.

    def hide_bulk_pricing_options(self):
        """إخفاء خيارات التسعير بالجملة"""

    def load_products(self):
        """تحميل المنتجات مع الأسعار المخصصة"""
        try:
            # Get products (simplified - would use proper product service)
            products = self.db.fetch_all("SELECT id, name, retail_price, current_stock FROM products LIMIT 100")

            self.products_table.setRowCount(len(products))

            for row, product in enumerate(products):
                product_id, name, base_price, stock = product

                # Calculate customer-specific price
                if self.current_customer:
                    price = self.pricing_service.get_price_for_customer(product_id, self.current_customer, 1)
                else:
                    price = Decimal(str(base_price or 0))

                # Product name
                name_item = QTableWidgetItem(name)
                self.products_table.setItem(row, 0, name_item)

                # Price
                price_item = QTableWidgetItem(f"€{price:.2f}")
                self.products_table.setItem(row, 1, price_item)

                # Stock
                stock_item = QTableWidgetItem(str(stock or 0))
                self.products_table.setItem(row, 2, stock_item)

                # Add to cart button
                add_btn = QPushButton("إضافة")
                add_btn.clicked.connect(lambda checked, pid=product_id: self.add_to_cart(pid))
                self.products_table.setCellWidget(row, 3, add_btn)

        except Exception as e:
            self.logger.error(f"Error loading products: {e}", exc_info=True)

    def add_to_cart(self, product_id: int, quantity: int = 1):
        """إضافة منتج للسلة"""
        if not self.current_customer:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار عميل أولاً")
            return

        # Check if product already in cart
        existing_item = None
        for item in self.cart_items:
            if item["product_id"] == product_id:
                existing_item = item
                break

        if existing_item:
            existing_item["quantity"] += quantity
        else:
            # Add new item
            self.cart_items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "base_price": Decimal("0"),  # Will be calculated
                    "final_price": Decimal("0"),  # Will be calculated
                }
            )

        # Update cart display
        self.update_cart_display()

        # Calculate prices asynchronously
        self.calculate_cart_prices()

    def update_cart_display(self):
        """تحديث عرض السلة"""
        self.cart_table.setRowCount(len(self.cart_items))

        for row, item in enumerate(self.cart_items):
            product_id = item["product_id"]
            quantity = item["quantity"]

            # Get product name
            product_name = self.get_product_name(product_id)

            # Product name
            name_item = QTableWidgetItem(product_name)
            self.cart_table.setItem(row, 0, name_item)

            # Quantity
            quantity_spin = QSpinBox()
            quantity_spin.setValue(quantity)
            quantity_spin.setMinimum(1)
            quantity_spin.valueChanged.connect(lambda value, pid=product_id: self.update_item_quantity(pid, value))
            self.cart_table.setCellWidget(row, 1, quantity_spin)

            # Price (will be updated by price calculation)
            price_item = QTableWidgetItem(f"€{item.get('final_price', 0):.2f}")
            self.cart_table.setItem(row, 2, price_item)

            # Total
            total = item.get("final_price", 0) * quantity
            total_item = QTableWidgetItem(f"€{total:.2f}")
            self.cart_table.setItem(row, 3, total_item)

            # Remove button
            remove_btn = QPushButton("إزالة")
            remove_btn.setStyleSheet("QPushButton { color: #dc3545; }")
            remove_btn.clicked.connect(lambda checked, pid=product_id: self.remove_from_cart(pid))
            self.cart_table.setCellWidget(row, 4, remove_btn)

    def calculate_cart_prices(self):
        """حساب أسعار السلة"""
        if not self.current_customer:
            return

        self.price_progress.setVisible(True)
        self.price_progress.setRange(0, len(self.cart_items))
        self.price_progress.setValue(0)

        # Calculate prices for each item
        for i, item in enumerate(self.cart_items):
            # Start price calculation thread
            self.calculate_item_price(item, i)

    def calculate_item_price(self, item: dict, index: int):
        """حساب سعر عنصر واحد"""
        worker = PriceUpdateWorker(
            self.pricing_service,
            self.dynamic_pricing,
            item["product_id"],
            self.current_customer,
            item["quantity"],
        )

        worker.finished.connect(lambda result: self.on_price_calculated(result, item, index))
        worker.error.connect(lambda error: self.on_price_error(error, item))

        # Start calculation in thread
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def on_price_calculated(self, result: dict, item: dict, index: int):
        """معالجة نتيجة حساب السعر"""
        item["base_price"] = result["base_price"]
        item["final_price"] = result["final_price"]
        item["insights"] = result["insights"]

        # Update progress
        self.price_progress.setValue(self.price_progress.value() + 1)

        if self.price_progress.value() >= len(self.cart_items):
            self.price_progress.setVisible(False)
            self.update_cart_display()
            self.update_cart_totals()

    def on_price_error(self, error: str, item: dict):
        """معالجة خطأ في حساب السعر"""
        self.logger.error(f"Price calculation error: {error}", exc_info=True)
        self.price_progress.setValue(self.price_progress.value() + 1)

    def update_cart_totals(self):
        """تحديث إجماليات السلة"""
        subtotal = sum(item.get("final_price", 0) * item["quantity"] for item in self.cart_items)

        # Calculate discounts (simplified)
        discount = Decimal("0")
        if self.is_b2b_mode:
            # B2B discounts
            discount = subtotal * Decimal("0.05")  # 5% B2B discount

        # Tax calculation (simplified)
        tax_rate = Decimal("0.19")  # 19% VAT
        taxable_amount = subtotal - discount
        tax = taxable_amount * tax_rate

        total = taxable_amount + tax

        # Update labels
        self.subtotal_label.setText(f"المجموع الفرعي: €{subtotal:.2f}")
        self.discount_label.setText(f"الخصم: €{discount:.2f}")
        self.tax_label.setText(f"الضريبة: €{tax:.2f}")
        self.total_label.setText(f"الإجمالي: €{total:.2f}")

        # Enable/disable checkout
        self.checkout_btn.setEnabled(len(self.cart_items) > 0)

    def checkout(self):
        """إتمام الشراء أو إنشاء عرض أسعار بشكل غير متزامن"""
        if not self.current_customer or not self.cart_items:
            return

        try:
            self.checkout_btn.setEnabled(False)
            self.price_progress.setVisible(True)
            self.price_progress.setRange(0, 0)  # Loading state

            mode = "quote" if (self.quote_mode and self.is_b2b_mode) else "sale"

            self.checkout_thread = QThread()
            self.checkout_worker = SaleCreationWorker(
                mode=mode,
                customer=self.current_customer,
                cart_items=self.cart_items,
                cpq_service=self.cpq_service,
                sales_service=self.sales_service,
            )
            self.checkout_worker.moveToThread(self.checkout_thread)

            self.checkout_thread.started.connect(self.checkout_worker.run)
            self.checkout_worker.finished.connect(self._on_checkout_finished)
            self.checkout_worker.error.connect(self._on_checkout_error)

            self.checkout_worker.finished.connect(self.checkout_thread.quit)
            self.checkout_worker.error.connect(self.checkout_thread.quit)
            self.checkout_worker.finished.connect(self.checkout_worker.deleteLater)
            self.checkout_worker.error.connect(self.checkout_worker.deleteLater)
            self.checkout_thread.finished.connect(self.checkout_thread.deleteLater)

            self.checkout_thread.start()

        except Exception as e:
            self.checkout_btn.setEnabled(True)
            self.price_progress.setVisible(False)
            QMessageBox.critical(self, "خطأ", f"فشل في بدء العملية: {str(e)}")

    def _on_checkout_finished(self, result: dict):
        self.checkout_btn.setEnabled(True)
        self.price_progress.setVisible(False)
        self.price_progress.setRange(0, 100)

        if result["type"] == "quote":
            self.quote_created.emit(
                {
                    "quote_id": result["id"],
                    "total": result["total"],
                    "customer": self.current_customer,
                }
            )
            QMessageBox.information(self, "نجح", f"تم إنشاء عرض الأسعار رقم {result['id']}")
        else:
            self.sale_completed.emit(
                {
                    "sale_id": result["id"],
                    "total": result["total"],
                    "customer": self.current_customer,
                }
            )
            QMessageBox.information(self, "نجح", f"تم إتمام المبيعة رقم {result['id']}")

        self.clear_cart()

    def _on_checkout_error(self, error: str):
        self.checkout_btn.setEnabled(True)
        self.price_progress.setVisible(False)
        self.price_progress.setRange(0, 100)
        QMessageBox.critical(self, "خطأ", f"فشل في إتمام العملية:\n{error}")

    def clear_cart(self):
        """إفراغ السلة"""
        self.cart_items.clear()
        self.update_cart_display()
        self.update_cart_totals()

    def remove_from_cart(self, product_id: int):
        """إزالة منتج من السلة"""
        self.cart_items = [item for item in self.cart_items if item["product_id"] != product_id]
        self.update_cart_display()
        self.update_cart_totals()

    def update_item_quantity(self, product_id: int, new_quantity: int):
        """تحديث كمية المنتج"""
        for item in self.cart_items:
            if item["product_id"] == product_id:
                item["quantity"] = new_quantity
                break

        self.calculate_cart_prices()

    def get_product_name(self, product_id: int) -> str:
        """الحصول على اسم المنتج"""
        try:
            product = self.db.fetch_one("SELECT name FROM products WHERE id = ?", (product_id,))
            return (
                product["name"]
                if isinstance(product, dict) and "name" in product
                else (product[0] if product else f"منتج {product_id}")
            )
        except Exception:
            return f"منتج {product_id}"

    # Event handlers
    def on_customer_selected(self, index: int):
        if index > 0:
            customer_id = self.customer_combo.itemData(index)
            # Load customer (would use customer service)
            customer = Customer(id=customer_id, name=self.customer_combo.currentText())
            self.set_customer(customer)

    def on_customer_search(self, text: str):
        # Implement customer search
        pass

    def on_product_search(self, text: str):
        # Implement product search
        pass

    def on_category_filter(self, index: int):
        # Implement category filtering
        pass

    def on_ai_prompt_submitted(self, prompt: str):
        # Process natural language product requests
        self.logger.debug(f"AI Prompt: {prompt}")
        # Would integrate with AI service to interpret and add products

    def on_quote_mode_toggled(self, checked: bool):
        self.quote_mode = checked
        if checked:
            self.checkout_btn.setText("إنشاء عرض أسعار")
        else:
            self.checkout_btn.setText("إتمام الشراء")

    def on_product_table_clicked(self, row: int, column: int):
        # Handle product table clicks
        pass

    def on_cart_table_clicked(self, row: int, column: int):
        # Handle cart table clicks
        pass
