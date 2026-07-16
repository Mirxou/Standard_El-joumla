import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
شبكة المنتجات الذكية - Smart Product Grid
تطبق Fitts Law وWCAG 2.2 لتحسين تجربة المستخدم
"""

from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.database_manager import DatabaseManager
from ...models.product import ProductManager
from ...services.pricing_service import PricingService
from ...utils.logger import setup_logger


class SmartProductGrid(QWidget):
    """شبكة منتجات ذكية تطبق Fitts Law وWCAG 2.2"""

    # إشارات
    product_selected = Signal(dict)  # {'product_id': int, 'quantity': int}

    # Touch Target Sizes (WCAG 2.2 SC 2.5.8)
    PRIMARY_BUTTON_SIZE = 80  # px - للإجراءات الأساسية (أكبر من 44x44)
    SECONDARY_BUTTON_SIZE = 60  # px - للإجراءات الثانوية
    MINIMUM_TOUCH_TARGET = 44  # px - الحد الأدنى (WCAG 2.2)

    # Spacing (WCAG 2.2)
    BUTTON_SPACING = 12  # px - المسافة بين الأزرار

    # Thumb Zone (Fitts Law)
    THUMB_ZONE_Y = 0.7  # 70% من الأسفل = منطقة الإبهام المثلى
    THUMB_ZONE_X = (0.3, 0.9)  # المنطقة الأفقية المثلى

    def __init__(
        self,
        db_manager: DatabaseManager,
        pricing_service: PricingService,
        customer=None,
        parent=None,
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.pricing_service = pricing_service
        self.customer = customer
        self.logger = setup_logger(__name__)

        # متغيرات الحالة
        self.products = []
        self.grid_items = []
        self.columns = 4  # عدد الأعمدة الافتراضي

        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # منطقة التمرير
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: #f1f1f1;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a1a1a1;
            }
        """)

        # widget الشبكة
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(self.BUTTON_SPACING)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)

    def load_products(self):
        """تحميل المنتجات وعرضها في الشبكة"""
        try:
            product_manager = ProductManager(self.db_manager)
            products = product_manager.get_all_active()

            self.products = products
            self.update_grid()

        except Exception as e:
            self.logger.error(f"خطأ في تحميل المنتجات: {str(e)}")

    def update_grid(self):
        """تحديث عرض الشبكة"""
        # مسح العناصر الحالية
        for item in self.grid_items:
            item.setParent(None)
            item.deleteLater()

        self.grid_items.clear()

        # إنشاء عناصر جديدة
        row = 0
        col = 0

        for product in self.products:
            item = ProductGridItem(product, self.pricing_service, self.customer, self)
            item.product_clicked.connect(self.on_product_clicked)
            self.grid_items.append(item)

            self.grid_layout.addWidget(item, row, col)

            col += 1
            if col >= self.columns:
                col = 0
                row += 1

        # إضافة عنصر فارغ للتوسع
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(spacer, row + 1, 0, 1, self.columns)

    def on_product_clicked(self, product_data: dict):
        """عند النقر على منتج"""
        self.product_selected.emit(product_data)

    def set_customer(self, customer):
        """تحديث العميل وإعادة حساب الأسعار"""
        self.customer = customer
        self.update_grid()

    def set_columns(self, columns: int):
        """تحديث عدد الأعمدة"""
        self.columns = columns
        self.update_grid()

    def filter_products(self, search_text: str):
        """فلترة المنتجات حسب النص"""
        search_text = search_text.lower().strip()

        if not search_text:
            # إظهار جميع المنتجات
            for item in self.grid_items:
                item.show()
            return

        # إخفاء/إظهار حسب البحث
        for item in self.grid_items:
            product_name = item.product.name.lower()
            product_sku = item.product.sku.lower() if item.product.sku else ""

            if search_text in product_name or search_text in product_sku:
                item.show()
            else:
                item.hide()


class ProductGridItem(QFrame):
    """عنصر منتج واحد في الشبكة"""

    product_clicked = Signal(dict)

    def __init__(self, product, pricing_service: PricingService, customer=None, parent=None):
        super().__init__(parent)
        self.product = product
        self.pricing_service = pricing_service
        self.customer = customer

        self.setFixedSize(180, 220)  # حجم ثابت للتناسق
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """إعداد واجهة العنصر"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # صورة المنتج
        self.image_label = QLabel()
        self.image_label.setFixedSize(120, 120)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                background-color: #1e293b;
            }
        """)

        # اسم المنتج
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 12px;
                color: #1f2937;
            }
        """)

        # السعر
        self.price_label = QLabel()
        self.price_label.setAlignment(Qt.AlignCenter)
        self.price_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #059669;
            }
        """)

        # زر الإضافة
        self.add_button = QPushButton("إضافة")
        self.add_button.setFixedSize(self.parent().PRIMARY_BUTTON_SIZE, self.parent().PRIMARY_BUTTON_SIZE // 2)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)

        # وضع الأزرار حسب Fitts Law
        self.position_buttons()

        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.price_label)
        layout.addWidget(self.add_button)

        # ربط الإشارات
        self.add_button.clicked.connect(self.on_add_clicked)

    def position_buttons(self):
        """وضع الأزرار بناءً على Fitts Law"""
        # الزر الرئيسي في منطقة الإبهام
        button_y = int(self.height() * self.parent().THUMB_ZONE_Y) - self.add_button.height()
        self.add_button.move((self.width() - self.add_button.width()) // 2, button_y)  # منتصف أفقياً

    def update_display(self):
        """تحديث عرض البيانات"""
        # اسم المنتج
        self.name_label.setText(self.product.name[:30] + "..." if len(self.product.name) > 30 else self.product.name)

        # السعر
        if self.customer and self.pricing_service:
            price = self.pricing_service.get_price_for_customer(self.product.id, self.customer, 1)
        else:
            price = self.product.retail_price or Decimal("0.00")

        self.price_label.setText(f"{price:.2f} دج")

        # الصورة (placeholder)
        self.set_product_image()

    def set_product_image(self):
        """تحديد صورة المنتج"""
        # إذا كان هناك صورة حقيقية، استخدمها
        # هنا نستخدم placeholder
        pixmap = QPixmap(120, 120)
        pixmap.fill(QColor("#f3f4f6"))

        painter = QPainter(pixmap)
        painter.setPen(QColor("#9ca3af"))
        painter.setFont(QFont("Arial", 48))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "📦")
        painter.end()

        self.image_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_add_clicked(self):
        """عند النقر على زر الإضافة"""
        # فتح حوار لتحديد الكمية
        from PySide6.QtWidgets import QInputDialog

        quantity, ok = QInputDialog.getInt(self, "تحديد الكمية", "أدخل الكمية:", 1, 1, 9999, 1)

        if ok and quantity > 0:
            product_data = {
                "product_id": self.product.id,
                "name": self.product.name,
                "quantity": quantity,
                "unit_price": (
                    float(self.pricing_service.get_price_for_customer(self.product.id, self.customer, quantity))
                    if self.customer and self.pricing_service
                    else float(self.product.retail_price or 0)
                ),
            }
            self.product_clicked.emit(product_data)
