import logging

#!/usr/bin/env python3  # noqa: E265
# -*- coding: utf-8 -*-
"""
خدمة CPQ - Configure Price Quote Service
خدمة التكوين والتسعير والعروض للعملاء B2B
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.models.customer import Customer
from src.services.pricing_service import PricingService


@dataclass
class ProductConfiguration:
    """تكوين المنتج المخصص"""

    product_id: int
    selected_options: Dict[str, Any] = field(default_factory=dict)  # option_name -> selected_value
    custom_text: Dict[str, str] = field(default_factory=dict)  # field_name -> text
    quantity: int = 1
    special_requirements: str = ""


class QuoteItem:
    """عنصر في عرض الأسعار"""

    def __init__(
        self,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
        discount_percentage: Decimal = Decimal("0.00"),
    ):
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.discount_percentage = discount_percentage

    @property
    def line_total(self) -> Decimal:
        """إجمالي السطر قبل الخصم"""
        return self.unit_price * Decimal(str(self.quantity))

    @property
    def discount_amount(self) -> Decimal:
        """مبلغ الخصم"""
        return self.line_total * (self.discount_percentage / Decimal("100"))

    @property
    def net_total(self) -> Decimal:
        """الإجمالي الصافي"""
        return self.line_total - self.discount_amount


class Quote:
    """عرض أسعار شامل"""

    def __init__(
        self,
        customer: Customer,
        items: List[QuoteItem],
        valid_until: date,
        notes: Optional[str] = None,
    ):
        self.customer = customer
        self.items = items
        self.valid_until = valid_until
        self.notes = notes
        self.created_at = datetime.now()
        self.id: Optional[int] = None

    @property
    def subtotal(self) -> Decimal:
        """المجموع الفرعي"""
        return sum(item.line_total for item in self.items)

    @property
    def total_discount(self) -> Decimal:
        """إجمالي الخصومات"""
        return sum(item.discount_amount for item in self.items)

    @property
    def total(self) -> Decimal:
        """الإجمالي النهائي"""
        return sum(item.net_total for item in self.items)

    @property
    def is_expired(self) -> bool:
        """هل انتهت صلاحية العرض؟"""
        return date.today() > self.valid_until


class CPQService:
    """خدمة CPQ للتكوين والتسعير والعروض"""

    def __init__(self, db_manager: DatabaseManager, pricing_service: PricingService, logger=None):
        self.db_manager = db_manager
        self.pricing_service = pricing_service
        self.logger = logger or logging.getLogger(__name__)

    def create_quote(
        self,
        customer_id: int,
        items: List[Dict[str, Any]],
        valid_days: int = 30,
        notes: Optional[str] = None,
    ) -> Optional[Quote]:
        """
        إنشاء عرض أسعار جديد

        Args:
            customer_id: معرف العميل
            items: قائمة العناصر [{'product_id': int, 'quantity': int, 'custom_discount': float}]
            valid_days: عدد أيام صلاحية العرض
            notes: ملاحظات إضافية

        Returns:
            كائن Quote أو None في حالة الخطأ
        """
        try:
            # Get customer
            customer = self._get_customer(customer_id)
            if not customer:
                return None

            # Create quote items
            quote_items = []
            for item_data in items:
                product_id = item_data["product_id"]
                quantity = item_data["quantity"]
                custom_discount = Decimal(str(item_data.get("custom_discount", 0)))

                # Get price for customer
                unit_price = self.pricing_service.get_price_for_customer(product_id, customer, quantity)

                quote_item = QuoteItem(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percentage=custom_discount,
                )

                quote_items.append(quote_item)

            # Calculate valid until date
            valid_until = date.today() + timedelta(days=valid_days)

            # Create quote
            quote = Quote(
                customer=customer,
                items=quote_items,
                valid_until=valid_until,
                notes=notes,
            )

            # Save to database
            quote.id = self._save_quote_to_db(quote)

            return quote

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء عرض الأسعار: {str(e)}")
            return None

    def _get_customer(self, customer_id: int) -> Optional[Customer]:
        """الحصول على العميل من قاعدة البيانات"""
        try:
            customer_data = self.db_manager.fetch_one("SELECT * FROM customers WHERE id = ?", (customer_id,))

            if not customer_data:
                return None

            # Convert to Customer object (simplified)
            return Customer(
                id=customer_data[0],
                name=customer_data[1] or "",
                customer_type=customer_data[16],  # Assuming column position
                pricing_tier=customer_data[19],
                contract_id=customer_data[21],
            )

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على العميل: {str(e)}")
            return None

    def _save_quote_to_db(self, quote: Quote) -> Optional[int]:
        """حفظ عرض الأسعار في قاعدة البيانات"""
        try:
            # Insert quote header
            result = self.db_manager.execute_query(
                """INSERT INTO quotes
                   (customer_id, quote_number, total_amount, status, valid_until, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    quote.customer.id,
                    self._generate_quote_number(),
                    float(quote.total),
                    "draft",
                    quote.valid_until,
                    quote.notes,
                    quote.created_at,
                ),
            )

            quote_id = result.lastrowid if result else None

            if quote_id:
                # Insert quote items
                for item in quote.items:
                    self.db_manager.execute_query(
                        """INSERT INTO quote_items
                           (quote_id, product_id, quantity, unit_price, discount_percentage, line_total)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            quote_id,
                            item.product_id,
                            item.quantity,
                            float(item.unit_price),
                            float(item.discount_percentage),
                            float(item.net_total),
                        ),
                    )

            return quote_id

        except Exception as e:
            self.logger.error(f"خطأ في حفظ عرض الأسعار: {str(e)}")
            return None

    def _generate_quote_number(self) -> str:
        """توليد رقم عرض الأسعار"""
        try:
            # Get current year
            year = datetime.now().year

            # Get next sequence number
            result = self.db_manager.fetch_one(
                "SELECT COUNT(*) FROM quotes WHERE strftime('%Y', created_at) = ?",
                (str(year),),
            )

            sequence = (result[0] if result else 0) + 1

            return f"Q{year}{sequence:04d}"

        except Exception as e:  # noqa: F841
            return f"Q{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def get_quote(self, quote_id: int) -> Optional[Quote]:
        """الحصول على عرض أسعار محدد"""
        try:
            # Get quote header
            quote_data = self.db_manager.fetch_one(
                """SELECT q.*, c.name as customer_name, c.customer_type
                   FROM quotes q
                   JOIN customers c ON q.customer_id = c.id
                   WHERE q.id = ?""",
                (quote_id,),
            )

            if not quote_data:
                return None

            # Get customer (simplified)
            customer = Customer(
                id=quote_data[1],  # customer_id
                name=quote_data[24] or "",  # customer_name
                customer_type=quote_data[25],  # customer_type
            )

            # Get quote items
            items_data = self.db_manager.fetch_all("SELECT * FROM quote_items WHERE quote_id = ?", (quote_id,))

            items = []
            for item_data in items_data:
                item = QuoteItem(
                    product_id=item_data[2],  # product_id
                    quantity=item_data[3],  # quantity
                    unit_price=Decimal(str(item_data[4])),  # unit_price
                    discount_percentage=Decimal(str(item_data[5] or 0)),  # discount_percentage
                )
                items.append(item)

            # Create quote object
            quote = Quote(
                customer=customer,
                items=items,
                valid_until=quote_data[5],  # valid_until
                notes=quote_data[6],  # notes
            )
            quote.id = quote_id
            quote.created_at = quote_data[7]  # created_at

            return quote

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على عرض الأسعار {quote_id}: {str(e)}")
            return None

    def approve_quote(self, quote_id: int, approved_by: str) -> bool:
        """اعتماد عرض الأسعار"""
        try:
            self.db_manager.execute_query(
                """UPDATE quotes
                   SET status = 'approved', approved_by = ?, approved_at = ?
                   WHERE id = ?""",
                (approved_by, datetime.now(), quote_id),
            )
            return True

        except Exception as e:
            self.logger.error(f"خطأ في اعتماد عرض الأسعار {quote_id}: {str(e)}")
            return False

    def reject_quote(self, quote_id: int, rejected_by: str, reason: str) -> bool:
        """رفض عرض الأسعار"""
        try:
            self.db_manager.execute_query(
                """UPDATE quotes
                   SET status = 'rejected', rejected_by = ?, rejected_at = ?, rejection_reason = ?
                   WHERE id = ?""",
                (rejected_by, datetime.now(), reason, quote_id),
            )
            return True

        except Exception as e:
            self.logger.error(f"خطأ في رفض عرض الأسعار {quote_id}: {str(e)}")
            return False

    def convert_quote_to_sale(self, quote_id: int, user_id: int) -> Optional[int]:
        """تحويل عرض الأسعار إلى مبيعة"""
        try:
            quote = self.get_quote(quote_id)
            if not quote or quote.is_expired:
                return None

            # Create sale record
            sale_result = self.db_manager.execute_query(
                """INSERT INTO sales
                   (customer_id, total_amount, status, created_by, created_at, quote_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    quote.customer.id,
                    float(quote.total),
                    "confirmed",
                    user_id,
                    datetime.now(),
                    quote_id,
                ),
            )

            sale_id = sale_result.lastrowid if sale_result else None

            if sale_id:
                # Create sale items
                for item in quote.items:
                    self.db_manager.execute_query(
                        """INSERT INTO sale_items
                           (sale_id, product_id, quantity, unit_price, discount_percentage, line_total)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            sale_id,
                            item.product_id,
                            item.quantity,
                            float(item.unit_price),
                            float(item.discount_percentage),
                            float(item.net_total),
                        ),
                    )

                # Update quote status
                self.db_manager.execute_query(
                    "UPDATE quotes SET status = 'converted', converted_at = ? WHERE id = ?",
                    (datetime.now(), quote_id),
                )

            return sale_id

        except Exception as e:
            self.logger.error(f"خطأ في تحويل عرض الأسعار إلى مبيعة: {str(e)}")
            return None

    def get_quotes_by_customer(self, customer_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """الحصول على عروض الأسعار لعميل محدد"""
        try:
            query = """
                SELECT q.id, q.quote_number, q.total_amount, q.status, q.valid_until,
                       q.created_at, COUNT(qi.id) as item_count
                FROM quotes q
                LEFT JOIN quote_items qi ON q.id = qi.quote_id
                WHERE q.customer_id = ?
            """

            params = [customer_id]

            if status:
                query += " AND q.status = ?"
                params.append(status)

            query += " GROUP BY q.id ORDER BY q.created_at DESC"

            quotes = self.db_manager.fetch_all(query, tuple(params))

            return [
                {
                    "id": q[0],
                    "quote_number": q[1],
                    "total_amount": float(q[2]),
                    "status": q[3],
                    "valid_until": q[4],
                    "created_at": q[5],
                    "item_count": q[6],
                }
                for q in quotes
            ]

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على عروض الأسعار للعميل {customer_id}: {str(e)}")
            return []

    def get_quote_summary(self, quote_id: int) -> Dict[str, Any]:
        """الحصول على ملخص عرض الأسعار"""
        try:
            quote = self.get_quote(quote_id)
            if not quote:
                return {}

            return {
                "id": quote.id,
                "customer": {
                    "id": quote.customer.id,
                    "name": quote.customer.name,
                    "type": quote.customer.customer_type,
                },
                "items": [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price),
                        "discount_percentage": float(item.discount_percentage),
                        "net_total": float(item.net_total),
                    }
                    for item in quote.items
                ],
                "subtotal": float(quote.subtotal),
                "total_discount": float(quote.total_discount),
                "total": float(quote.total),
                "valid_until": quote.valid_until.isoformat(),
                "is_expired": quote.is_expired,
                "created_at": quote.created_at.isoformat(),
            }

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على ملخص عرض الأسعار {quote_id}: {str(e)}")
            return {}
