#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المشتريات - Purchase Service
توفّر دوال مساعدة للواجهة لإدارة فواتير الشراء
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.models.purchase import (
    PaymentStatus,
    Purchase,
    PurchaseItem,
    PurchaseManager,
    PurchaseStatus,
)
from src.models.supplier import SupplierManager
from src.services.exchange_rate_service import ExchangeRateService
from src.utils.logger import setup_logger


class PurchaseService:
    """خدمة المشتريات"""

    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.purchase_manager = PurchaseManager(db_manager, self.logger)
        self.supplier_manager = SupplierManager(db_manager, self.logger)
        self.exchange_rate_service = ExchangeRateService(db_manager, self.logger)
        self._purchase_cache: Dict[str, Any] = {
            "data": [],
            "summary": {},
            "filters": {},
        }

    def create_purchase(self, purchase: Purchase) -> Optional[int]:
        """إنشاء فاتورة شراء"""
        try:
            # Multi-Currency (في حال كان النموذج يدعمه)
            currency_id = getattr(purchase, "currency_id", None)
            if currency_id:
                try:
                    base_currency = self.exchange_rate_service.currency_manager.get_base_currency()
                    if base_currency:
                        exchange_rate = self.exchange_rate_service.get_exchange_rate(
                            currency_id, base_currency.id, purchase.purchase_date
                        )
                        if exchange_rate:
                            setattr(purchase, "exchange_rate", exchange_rate)
                            setattr(
                                purchase,
                                "base_amount",
                                purchase.total_amount * exchange_rate,
                            )
                            setattr(purchase, "converted_amount", purchase.total_amount)
                        else:
                            setattr(purchase, "base_amount", purchase.total_amount)
                            setattr(purchase, "converted_amount", purchase.total_amount)
                            setattr(purchase, "exchange_rate", Decimal("1.0"))
                    else:
                        setattr(purchase, "base_amount", purchase.total_amount)
                        setattr(purchase, "converted_amount", purchase.total_amount)
                        setattr(purchase, "exchange_rate", Decimal("1.0"))
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error calculating exchange rate: {e}")
                    setattr(purchase, "base_amount", purchase.total_amount)
                    setattr(purchase, "converted_amount", purchase.total_amount)
                    setattr(purchase, "exchange_rate", Decimal("1.0"))
            else:
                setattr(purchase, "base_amount", purchase.total_amount)
                setattr(purchase, "converted_amount", purchase.total_amount)
                setattr(purchase, "exchange_rate", Decimal("1.0"))

            return self.purchase_manager.create_purchase(purchase)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error creating purchase: {e}")
            return None

    def get_purchase_by_id(self, purchase_id: int) -> Optional[Purchase]:
        return self.purchase_manager.get_purchase_by_id(purchase_id)

    def list_purchases(self, **kwargs) -> List[Dict[str, Any]]:
        """إرجاع قائمة مبسطة للاستخدام في الواجهة"""
        try:
            # Normalize filters
            if "status" in kwargs:
                kwargs["status"] = self._normalize_status(kwargs["status"])
            if "payment_status" in kwargs:
                kwargs["payment_status"] = self._normalize_payment_status(kwargs["payment_status"])

            purchases = self.purchase_manager.search_purchases(
                search_term=kwargs.get("search_term", ""),
                supplier_id=kwargs.get("supplier_id"),
                status=kwargs.get("status"),
                start_date=kwargs.get("start_date"),
                end_date=kwargs.get("end_date"),
            )

            results = [p.to_dict() for p in purchases]
            self._purchase_cache["filters"] = kwargs
            self._purchase_cache["data"] = results
            return results
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error listing purchases: {e}")
            return []

    def get_purchases_summary(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        try:
            summary = self.purchase_manager.get_purchases_summary(start_date, end_date)
            self._purchase_cache["summary"] = summary
            return summary
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error getting summary: {e}")
            return {
                "total_purchases": 0,
                "total_amount": 0.0,
                "total_paid": 0.0,
                "total_remaining": 0.0,
            }

    def create_auto_reorder_draft(self, product_id: int, quantity: int = 10) -> Optional[int]:
        """إنشاء مسودة طلب شراء تلقائياً (Agentic Action)"""
        try:
            from src.models.product import ProductManager

            pm = ProductManager(self.db_manager, self.logger)
            product = pm.get_product_by_id(product_id)
            if not product:
                return None

            # Find supplier
            supplier_id = getattr(product, "supplier_id", None)
            if not supplier_id:
                last_q = "SELECT supplier_id FROM purchases p JOIN purchase_items pi ON p.id = pi.purchase_id WHERE pi.product_id = ? ORDER BY p.purchase_date DESC LIMIT 1"  # noqa: E501
                res = self.db_manager.fetch_one(last_q, (product_id,))
                if res:
                    supplier_id = res.get("supplier_id") if isinstance(res, dict) else res[0]

            if not supplier_id:
                s_res = self.db_manager.fetch_one("SELECT id FROM suppliers WHERE is_active = 1 LIMIT 1")
                if s_res:
                    supplier_id = s_res.get("id") if isinstance(s_res, dict) else s_res[0]

            if not supplier_id:
                return None

            purchase = Purchase(
                supplier_id=supplier_id,
                purchase_date=date.today(),
                status=PurchaseStatus.PENDING.value,
                notes="Created by Vision 2030 Agentic AI (Auto-Reorder)",
            )

            item = PurchaseItem(
                product_id=product_id,
                quantity_ordered=Decimal(str(quantity)),
                unit_cost=product.cost_price,
            )
            purchase.items = [item]

            return self.create_purchase(purchase)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Auto-Reorder Failed: {e}")
            return None

    def _normalize_status(self, val: Optional[str]) -> Optional[str]:
        if not val or val == "الكل":
            return None
        if isinstance(val, PurchaseStatus):
            return val.value
        mapping = {
            "معلقة": PurchaseStatus.PENDING.value,
            "مستلمة": PurchaseStatus.RECEIVED.value,
            "جزئية": PurchaseStatus.PARTIAL.value,
            "ملغية": PurchaseStatus.CANCELLED.value,
            "مرتجعة": PurchaseStatus.RETURNED.value,
        }
        return mapping.get(val, val)

    def _normalize_payment_status(self, val: Optional[str]) -> Optional[str]:
        if not val or val == "الكل":
            return None
        if isinstance(val, PaymentStatus):
            return val.value
        mapping = {
            "غير مدفوعة": PaymentStatus.UNPAID.value,
            "مدفوعة جزئياً": PaymentStatus.PARTIAL.value,
            "مدفوعة": PaymentStatus.PAID.value,
            "متأخرة": PaymentStatus.OVERDUE.value,
        }
        return mapping.get(val, val)
