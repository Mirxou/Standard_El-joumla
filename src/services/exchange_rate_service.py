import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة أسعار الصرف - Exchange Rate Service
إدارة أسعار الصرف وتحويل العملات
محسنة لاستخدام DatabaseManager المطور مع معالجة مرنة للبيانات

Production-Ready:
- Safe Decimal handling (no division by zero)
- convert_amount() high-level API
- Thread-safe rate updates
"""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import List, Optional

from src.core.database_manager import DatabaseManager
from src.models.currency import Currency, CurrencyManager, ExchangeRate
from src.utils.logger import setup_logger


class ExchangeRateService:
    """خدمة أسعار الصرف"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.currency_manager = CurrencyManager(db_manager)

    def _safe_decimal(self, value, default: str = "0") -> Decimal:
        """تحويل آمن لـ Decimal مع حماية من القيم غير الصالحة."""
        if value is None or str(value).strip() == "":
            return Decimal(default)
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            self.logger.warning(f"Invalid decimal value: {value!r}, using default {default}")
            return Decimal(default)

    def get_exchange_rate(
        self,
        from_currency_id: int,
        to_currency_id: int,
        target_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """الحصول على سعر الصرف بين عملتين بنمط Mapping مرن."""
        try:
            if from_currency_id == to_currency_id:
                return Decimal("1.0")
            if target_date is None:
                target_date = date.today()

            query = """
                SELECT rate FROM exchange_rates
                WHERE from_currency_id = ? AND to_currency_id = ?
                  AND effective_date <= ? AND (expiry_date IS NULL OR expiry_date >= ?)
                  AND is_active = 1
                ORDER BY effective_date DESC LIMIT 1
            """
            target_iso = target_date.isoformat()

            # البحث المباشر
            row = self.db_manager.fetch_one(query, (from_currency_id, to_currency_id, target_iso, target_iso))
            if row:
                is_dict = isinstance(row, dict)
                rate = self._safe_decimal(row.get("rate") if is_dict else row[0])
                if rate > 0:
                    return rate

            # محاولة العكس
            row = self.db_manager.fetch_one(query, (to_currency_id, from_currency_id, target_iso, target_iso))
            if row:
                is_dict = isinstance(row, dict)
                rate = self._safe_decimal(row.get("rate") if is_dict else row[0])
                if rate > 0:
                    return (Decimal("1.0") / rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

            return None
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سعر الصرف: {e}")
            return None

    def convert_amount(
        self,
        amount: Decimal,
        from_currency_id: int,
        to_currency_id: int,
        target_date: Optional[date] = None,
        decimal_places: int = 2,
    ) -> Optional[Decimal]:
        """تحويل مبلغ من عملة لأخرى.

        Args:
            amount: المبلغ المراد تحويله
            from_currency_id: معرف العملة المصدر
            to_currency_id: معرف العملة الهدف
            target_date: تاريخ سعر الصرف (اختياري، افتراضي اليوم)
            decimal_places: عدد الأرقام العشرية في النتيجة

        Returns:
            المبلغ المحول أو None إذا لم يتوفر سعر صرف
        """
        try:
            if from_currency_id == to_currency_id:
                return amount

            rate = self.get_exchange_rate(from_currency_id, to_currency_id, target_date)
            if rate is None:
                self.logger.warning(f"No exchange rate found: {from_currency_id} → {to_currency_id}")
                return None

            quantize_str = "0." + "0" * decimal_places
            converted = (self._safe_decimal(amount) * rate).quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
            return converted
        except Exception as e:
            self.logger.error(f"خطأ في تحويل المبلغ: {e}")
            return None

    def add_exchange_rate(
        self,
        from_currency_id: int,
        to_currency_id: int,
        rate: Decimal,
        effective_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        source: str = "manual",
    ) -> Optional[int]:
        """إضافة سعر صرف جديد باستخدام execute_insert."""
        try:
            if effective_date is None:
                effective_date = date.today()

            # التحقق من أن السعر موجب
            decimal_rate = self._safe_decimal(rate)
            if decimal_rate <= 0:
                self.logger.error(f"Invalid exchange rate: {rate}")
                return None

            query = """
                INSERT INTO exchange_rates
                (from_currency_id, to_currency_id, rate, effective_date, expiry_date,
                 source, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            params = (
                from_currency_id,
                to_currency_id,
                float(decimal_rate),
                effective_date.isoformat(),
                expiry_date.isoformat() if expiry_date else None,
                source,
            )
            return self.db_manager.execute_insert(query, params)
        except Exception as e:
            self.logger.error(f"خطأ في إضافة سعر الصرف: {e}")
            return None

    def update_exchange_rate(self, rate_id: int, new_rate: Decimal, source: str = "manual") -> bool:
        """تحديث سعر صرف موجود."""
        try:
            decimal_rate = self._safe_decimal(new_rate)
            if decimal_rate <= 0:
                self.logger.error(f"Invalid exchange rate for update: {new_rate}")
                return False

            query = """
                UPDATE exchange_rates
                SET rate = ?, source = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            result = self.db_manager.execute_non_query(query, (float(decimal_rate), source, rate_id))
            return result > 0
        except Exception as e:
            self.logger.error(f"خطأ في تحديث سعر الصرف: {e}")
            return False

    def deactivate_rate(self, rate_id: int) -> bool:
        """إلغاء تفعيل سعر صرف."""
        try:
            query = """
                UPDATE exchange_rates
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            return self.db_manager.execute_non_query(query, (rate_id,)) > 0
        except Exception as e:
            self.logger.error(f"خطأ في إلغاء تفعيل سعر الصرف: {e}")
            return False

    def get_exchange_rates(
        self,
        from_currency_id: Optional[int] = None,
        to_currency_id: Optional[int] = None,
        include_inactive: bool = False,
    ) -> List[ExchangeRate]:
        """قائمة أسعار الصرف بنمط Mapping مرن."""
        try:
            query = "SELECT * FROM exchange_rates WHERE 1=1"
            params = []
            if from_currency_id:
                query += " AND from_currency_id = ?"
                params.append(from_currency_id)
            if to_currency_id:
                query += " AND to_currency_id = ?"
                params.append(to_currency_id)
            if not include_inactive:
                query += " AND is_active = 1"
            query += " ORDER BY effective_date DESC, created_at DESC"

            rows = self.db_manager.fetch_all(query, params)
            rates = []
            for row in rows:
                is_dict = isinstance(row, dict)

                def gv(k, i, d=None):
                    if is_dict:
                        return row.get(k, d)
                    return row[i] if len(row) > i else d

                rates.append(
                    ExchangeRate(
                        id=gv("id", 0),
                        from_currency_id=gv("from_currency_id", 1),
                        to_currency_id=gv("to_currency_id", 2),
                        rate=self._safe_decimal(gv("rate", 3), "1.0"),
                        effective_date=(
                            date.fromisoformat(gv("effective_date", 4)) if gv("effective_date", 4) else None
                        ),
                        expiry_date=(date.fromisoformat(gv("expiry_date", 5)) if gv("expiry_date", 5) else None),
                        source=gv("source", 6),
                        is_active=bool(gv("is_active", 7)),
                        created_at=(datetime.fromisoformat(gv("created_at", 8)) if gv("created_at", 8) else None),
                    )
                )
            return rates
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على أسعار الصرف: {e}")
            return []

    def get_base_currency(self) -> Optional[Currency]:
        """الحصول على العملة الأساسية."""
        return self.currency_manager.get_base_currency()

    def get_all_currencies(self, include_inactive: bool = False) -> List[Currency]:
        """الحصول على جميع العملات."""
        return self.currency_manager.get_all_currencies(include_inactive)
