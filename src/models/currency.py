import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج العملات - Currency Model
يحتوي على جميع العمليات المتعلقة بالعملات وأسعار الصرف
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager


@dataclass
class Currency:
    """نموذج بيانات العملة"""

    id: Optional[int] = None
    code: str = ""  # رمز العملة (USD, EUR, DZD)
    name: str = ""  # اسم العملة
    symbol: str = ""  # رمز العملة ($, €, د.ج)
    is_base: bool = False  # هل هي العملة الأساسية؟
    is_active: bool = True  # هل العملة نشطة؟
    decimal_places: int = 2  # عدد الأرقام العشرية
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "is_base": 1 if self.is_base else 0,
            "is_active": 1 if self.is_active else 0,
            "decimal_places": self.decimal_places,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Currency":
        """إنشاء من قاموس"""
        return cls(
            id=data.get("id"),
            code=data.get("code", ""),
            name=data.get("name", ""),
            symbol=data.get("symbol", ""),
            is_base=bool(data.get("is_base", 0)),
            is_active=bool(data.get("is_active", 1)),
            decimal_places=data.get("decimal_places", 2),
            created_at=(datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None),
            updated_at=(datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None),
        )


@dataclass
class ExchangeRate:
    """نموذج بيانات سعر الصرف"""

    id: Optional[int] = None
    from_currency_id: int = 0  # العملة المصدر
    to_currency_id: int = 0  # العملة الهدف
    rate: Decimal = Decimal("1.0")  # سعر الصرف
    effective_date: Optional[date] = None  # تاريخ بدء السعر
    expiry_date: Optional[date] = None  # تاريخ انتهاء السعر
    source: str = "manual"  # مصدر السعر
    is_active: bool = True  # هل السعر نشط؟
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "from_currency_id": self.from_currency_id,
            "to_currency_id": self.to_currency_id,
            "rate": float(self.rate),
            "effective_date": (self.effective_date.isoformat() if self.effective_date else None),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "source": self.source,
            "is_active": 1 if self.is_active else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExchangeRate":
        """إنشاء من قاموس"""
        return cls(
            id=data.get("id"),
            from_currency_id=data.get("from_currency_id", 0),
            to_currency_id=data.get("to_currency_id", 0),
            rate=Decimal(str(data.get("rate", 1.0))),
            effective_date=(date.fromisoformat(data["effective_date"]) if data.get("effective_date") else None),
            expiry_date=(date.fromisoformat(data["expiry_date"]) if data.get("expiry_date") else None),
            source=data.get("source", "manual"),
            is_active=bool(data.get("is_active", 1)),
            created_at=(datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None),
            updated_at=(datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None),
        )


class CurrencyManager:
    """مدير العملات"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger

    def get_base_currency(self) -> Optional[Currency]:
        """الحصول على العملة الأساسية"""
        try:
            query = """
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
                WHERE is_base = 1 AND is_active = 1
                LIMIT 1
            """
            row = self.db_manager.fetch_one(query)
            if row:
                return self._row_to_currency(row)
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العملة الأساسية: {e}")
            return None

    def get_currency(self, currency_id: int) -> Optional[Currency]:
        """الحصول على عملة حسب المعرف"""
        try:
            query = """
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
                WHERE id = ?
            """
            row = self.db_manager.fetch_one(query, (currency_id,))
            if row:
                return self._row_to_currency(row)
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العملة: {e}")
            return None

    def get_currency_by_code(self, code: str) -> Optional[Currency]:
        """الحصول على عملة حسب الرمز"""
        try:
            query = """
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
                WHERE UPPER(code) = UPPER(?)
            """
            row = self.db_manager.fetch_one(query, (code,))
            if row:
                return self._row_to_currency(row)
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العملة: {e}")
            return None

    def get_all_currencies(self, include_inactive: bool = False) -> List[Currency]:
        """الحصول على جميع العملات"""
        try:
            query = """
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
            """
            if not include_inactive:
                query += " WHERE is_active = 1"
            query += " ORDER BY is_base DESC, code ASC"

            results = self.db_manager.fetch_all(query)
            return [self._row_to_currency(row) for row in results]
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العملات: {e}")
            return []

    def add_currency(self, currency: Currency) -> Optional[int]:
        """إضافة عملة جديدة"""
        try:
            # إذا كانت العملة الأساسية، إلغاء الأساسية من العملات الأخرى
            if currency.is_base:
                self.db_manager.execute_non_query("UPDATE currencies SET is_base = 0 WHERE is_base = 1")

            query = """
                INSERT INTO currencies (code, name, symbol, is_base, is_active, decimal_places)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                currency.code.upper(),
                currency.name,
                currency.symbol,
                1 if currency.is_base else 0,
                1 if currency.is_active else 0,
                currency.decimal_places,
            )
            return self.db_manager.execute_insert(query, params)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة العملة: {e}")
            return None

    def update_currency(self, currency: Currency) -> bool:
        """تحديث عملة"""
        try:
            # إذا كانت العملة الأساسية، إلغاء الأساسية من العملات الأخرى
            if currency.is_base:
                self.db_manager.execute_non_query(
                    "UPDATE currencies SET is_base = 0 WHERE is_base = 1 AND id != ?",
                    (currency.id,),
                )

            query = """
                UPDATE currencies
                SET code = ?, name = ?, symbol = ?, is_base = ?, is_active = ?,
                    decimal_places = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            params = (
                currency.code.upper(),
                currency.name,
                currency.symbol,
                1 if currency.is_base else 0,
                1 if currency.is_active else 0,
                currency.decimal_places,
                currency.id,
            )
            result = self.db_manager.execute_non_query(query, params)
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث العملة: {e}")
            return False

    def delete_currency(self, currency_id: int) -> bool:
        """حذف عملة"""
        try:
            # لا يمكن حذف العملة الأساسية
            currency = self.get_currency(currency_id)
            if currency and currency.is_base:
                return False

            result = self.db_manager.execute_non_query("DELETE FROM currencies WHERE id = ?", (currency_id,))
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف العملة: {e}")
            return False

    def _row_to_currency(self, row) -> Optional[Currency]:
        """تحويل صف قاعدة البيانات إلى كائن عملة"""
        if not row:
            return None
        try:
            is_dict = isinstance(row, dict)

            def get_val(key, idx, default=None):
                if is_dict:
                    return row.get(key, default)
                return row[idx] if len(row) > idx else default

            return Currency(
                id=get_val("id", 0),
                code=get_val("code", 1),
                name=get_val("name", 2),
                symbol=get_val("symbol", 3),
                is_base=bool(get_val("is_base", 4)),
                is_active=bool(get_val("is_active", 5)),
                decimal_places=get_val("decimal_places", 6, 2),
                created_at=self._parse_datetime(get_val("created_at", 7)),
                updated_at=self._parse_datetime(get_val("updated_at", 8)),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error mapping currency: {e}")
            return None

    def _parse_datetime(self, val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            return None
