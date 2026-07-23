import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التسعير المتقدمة - Advanced Pricing Service
تدعم التسعير المتدرج والديناميكي والعقدي للـ Unified Commerce
"""

from decimal import Decimal
from typing import Optional

from src.core.database_manager import DatabaseManager
from src.models.customer import Customer
from src.utils.logger import setup_logger


class PricingService:
    """نظام تسعير متقدم يدعم Tiered + Dynamic + Contract Pricing"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)

        # Pricing Tiers Configuration
        self.PRICING_TIERS = {
            1: {
                "name": "Basic",
                "discount": Decimal("0.00"),
                "min_volume": Decimal("0.00"),
            },
            2: {
                "name": "Silver",
                "discount": Decimal("0.05"),
                "min_volume": Decimal("10000.00"),
            },
            3: {
                "name": "Gold",
                "discount": Decimal("0.10"),
                "min_volume": Decimal("50000.00"),
            },
            4: {
                "name": "Platinum",
                "discount": Decimal("0.15"),
                "min_volume": Decimal("100000.00"),
            },
            5: {
                "name": "Diamond",
                "discount": Decimal("0.20"),
                "min_volume": Decimal("500000.00"),
            },
        }

    def get_price_for_customer(self, product_id: int, customer: Customer, quantity: float = 1) -> Decimal:
        """
        احسب السعر مع تطبيق جميع القواعد للعميل المحدد

        Args:
            product_id: معرف المنتج
            customer: كائن العميل
            quantity: الكمية المطلوبة

        Returns:
            السعر النهائي بعد تطبيق جميع الخصومات
        """
        try:
            quantity = Decimal(str(quantity))

            # 1. Check Contract Pricing (highest priority)
            if customer.contract_id:
                contract_price = self.get_contract_price(product_id, customer.contract_id)
                if contract_price:
                    return contract_price

            # 2. Check Customer-Specific Price List
            if customer.price_list_id:
                list_price = self.get_price_list_price(product_id, customer.price_list_id)
                if list_price:
                    return list_price

            # 3. Apply Tiered Pricing based on quantity and customer tier
            base_price = self.get_base_price(product_id, customer.customer_type)
            tiered_price = self.apply_volume_tiers(base_price, quantity, customer.pricing_tier)

            # 4. Apply Dynamic Pricing adjustments
            dynamic_price = self.apply_dynamic_pricing(tiered_price, product_id, customer, quantity)

            return dynamic_price

        except Exception as e:
            self.logger.error(f"خطأ في حساب السعر للعميل {customer.id}: {str(e)}")
            # Fallback to base price
            return self.get_base_price(product_id, customer.customer_type)

    def get_base_price(self, product_id: int, customer_type: Optional[str] = None) -> Decimal:
        """الحصول على السعر الأساسي للمنتج"""
        try:
            product = self.db_manager.fetch_one(
                "SELECT retail_price, wholesale_price FROM products WHERE id = ?",
                (product_id,),
            )

            if not product:
                return Decimal("0.00")

            retail_price, wholesale_price = product

            # Choose price based on customer type
            if customer_type in ["wholesale", "vip"] and wholesale_price:
                return Decimal(str(wholesale_price))
            else:
                return Decimal(str(retail_price or 0))

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على السعر الأساسي للمنتج {product_id}: {str(e)}")
            return Decimal("0.00")

    def apply_volume_tiers(self, base_price: Decimal, quantity: Decimal, pricing_tier: Optional[int]) -> Decimal:
        """تطبيق التسعير المتدرج حسب الكمية والمستوى"""
        try:
            # Apply tier discount
            tier_discount = Decimal("0.00")
            if pricing_tier and pricing_tier in self.PRICING_TIERS:
                tier_discount = self.PRICING_TIERS[pricing_tier]["discount"]

            # Apply volume-based discount
            volume_discount = self.calculate_volume_discount(quantity)

            # Combine discounts (tier discount is applied first)
            total_discount = tier_discount + volume_discount - (tier_discount * volume_discount)

            return base_price * (Decimal("1.00") - total_discount)

        except Exception as e:
            self.logger.error(f"خطأ في تطبيق التسعير المتدرج: {str(e)}")
            return base_price

    def calculate_volume_discount(self, quantity: Decimal) -> Decimal:
        """حساب خصم الكمية"""
        try:
            if quantity >= 1000:
                return Decimal("0.10")  # 10% discount
            elif quantity >= 500:
                return Decimal("0.07")  # 7% discount
            elif quantity >= 100:
                return Decimal("0.05")  # 5% discount
            elif quantity >= 50:
                return Decimal("0.03")  # 3% discount
            else:
                return Decimal("0.00")

        except Exception as e:  # noqa: F841
            return Decimal("0.00")

    def get_contract_price(self, product_id: int, contract_id: int) -> Optional[Decimal]:
        """الحصول على السعر التعاقدي"""
        try:
            contract_item = self.db_manager.fetch_one(
                """SELECT agreed_price FROM contract_items
                   WHERE contract_id = ? AND product_id = ?""",
                (contract_id, product_id),
            )

            if contract_item and contract_item[0]:
                return Decimal(str(contract_item[0]))

            return None

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على السعر التعاقدي: {str(e)}")
            return None

    def get_price_list_price(self, product_id: int, price_list_id: int) -> Optional[Decimal]:
        """الحصول على السعر من قائمة الأسعار المخصصة"""
        try:
            price_item = self.db_manager.fetch_one(
                """SELECT custom_price, discount_percentage FROM price_list_items
                   WHERE price_list_id = ? AND product_id = ?""",
                (price_list_id, product_id),
            )

            if not price_item:
                return None

            custom_price, discount_percentage = price_item

            if custom_price:
                return Decimal(str(custom_price))
            elif discount_percentage:
                base_price = self.get_base_price(product_id)
                discount = Decimal(str(discount_percentage)) / Decimal("100")
                return base_price * (Decimal("1.00") - discount)

            return None

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سعر قائمة الأسعار: {str(e)}")
            return None

    def apply_dynamic_pricing(
        self,
        current_price: Decimal,
        product_id: int,
        customer: Customer,
        quantity: Decimal,
    ) -> Decimal:
        """تطبيق التسعير الديناميكي (سيتم تطويره لاحقاً)"""
        # Placeholder for dynamic pricing logic
        # This will include inventory levels, demand signals, competitor pricing, etc.
        return current_price

    def get_customer_pricing_tier(self, customer: Customer) -> int:
        """تحديد مستوى التسعير المناسب للعميل"""
        try:
            # Auto-tier based on purchase history
            if customer.total_purchases >= 500000:
                return 5  # Diamond
            elif customer.total_purchases >= 100000:
                return 4  # Platinum
            elif customer.total_purchases >= 50000:
                return 3  # Gold
            elif customer.total_purchases >= 10000:
                return 2  # Silver
            else:
                return 1  # Basic

        except Exception as e:
            self.logger.error(f"خطأ في تحديد مستوى التسعير: {str(e)}")
            return 1

    def update_customer_pricing_tier(self, customer_id: int) -> bool:
        """تحديث مستوى التسعير للعميل تلقائياً"""
        try:
            customer = self.db_manager.fetch_one("SELECT total_purchases FROM customers WHERE id = ?", (customer_id,))

            if not customer:
                return False

            total_purchases = Decimal(str(customer["total_purchases"]))
            new_tier = self.calculate_pricing_tier(total_purchases)

            self.db_manager.execute_query(
                "UPDATE customers SET pricing_tier = ? WHERE id = ?",
                (new_tier, customer_id),
            )

            return True

        except Exception as e:
            self.logger.error(f"خطأ في تحديث مستوى التسعير للعميل {customer_id}: {str(e)}")
            return False

    def calculate_pricing_tier(self, total_purchases: Decimal) -> int:
        """حساب مستوى التسعير بناءً على إجمالي المشتريات"""
        if total_purchases >= 500000:
            return 5
        elif total_purchases >= 100000:
            return 4
        elif total_purchases >= 50000:
            return 3
        elif total_purchases >= 10000:
            return 2
        else:
            return 1

    def create_price_list(self, name: str, description: Optional[str] = None) -> Optional[int]:
        """إنشاء قائمة أسعار جديدة"""
        try:
            result = self.db_manager.execute_query(
                """INSERT INTO price_lists (name, description) VALUES (?, ?)""",
                (name, description),
            )
            return result.lastrowid if result else None

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء قائمة الأسعار: {str(e)}")
            return None

    def add_price_list_item(
        self,
        price_list_id: int,
        product_id: int,
        custom_price: Optional[Decimal] = None,
        discount_percentage: Optional[Decimal] = None,
    ) -> bool:
        """إضافة عنصر إلى قائمة الأسعار"""
        try:
            self.db_manager.execute_query(
                """INSERT INTO price_list_items
                   (price_list_id, product_id, custom_price, discount_percentage)
                   VALUES (?, ?, ?, ?)""",
                (
                    price_list_id,
                    product_id,
                    float(custom_price) if custom_price else None,
                    float(discount_percentage) if discount_percentage else None,
                ),
            )
            return True

        except Exception as e:
            self.logger.error(f"خطأ في إضافة عنصر لقائمة الأسعار: {str(e)}")
            return False
