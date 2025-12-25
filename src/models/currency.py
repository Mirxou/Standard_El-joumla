#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج العملات - Currency Model
يحتوي على جميع العمليات المتعلقة بالعملات وأسعار الصرف
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager


@dataclass
class Currency:
    """نموذج بيانات العملة"""
    id: Optional[int] = None
    code: str = ""                          # رمز العملة (USD, EUR, DZD)
    name: str = ""                          # اسم العملة
    symbol: str = ""                        # رمز العملة ($, €, د.ج)
    is_base: bool = False                   # هل هي العملة الأساسية؟
    is_active: bool = True                  # هل العملة نشطة؟
    decimal_places: int = 2                 # عدد الأرقام العشرية
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'symbol': self.symbol,
            'is_base': 1 if self.is_base else 0,
            'is_active': 1 if self.is_active else 0,
            'decimal_places': self.decimal_places,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Currency':
        """إنشاء من قاموس"""
        return cls(
            id=data.get('id'),
            code=data.get('code', ''),
            name=data.get('name', ''),
            symbol=data.get('symbol', ''),
            is_base=bool(data.get('is_base', 0)),
            is_active=bool(data.get('is_active', 1)),
            decimal_places=data.get('decimal_places', 2),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class ExchangeRate:
    """نموذج بيانات سعر الصرف"""
    id: Optional[int] = None
    from_currency_id: int = 0               # العملة المصدر
    to_currency_id: int = 0                 # العملة الهدف
    rate: Decimal = Decimal('1.0')          # سعر الصرف
    effective_date: Optional[date] = None  # تاريخ بدء السعر
    expiry_date: Optional[date] = None     # تاريخ انتهاء السعر
    source: str = "manual"                  # مصدر السعر
    is_active: bool = True                  # هل السعر نشط؟
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'from_currency_id': self.from_currency_id,
            'to_currency_id': self.to_currency_id,
            'rate': float(self.rate),
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'source': self.source,
            'is_active': 1 if self.is_active else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeRate':
        """إنشاء من قاموس"""
        return cls(
            id=data.get('id'),
            from_currency_id=data.get('from_currency_id', 0),
            to_currency_id=data.get('to_currency_id', 0),
            rate=Decimal(str(data.get('rate', 1.0))),
            effective_date=date.fromisoformat(data['effective_date']) if data.get('effective_date') else None,
            expiry_date=date.fromisoformat(data['expiry_date']) if data.get('expiry_date') else None,
            source=data.get('source', 'manual'),
            is_active=bool(data.get('is_active', 1)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


class CurrencyManager:
    """مدير العملات"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_base_currency(self) -> Optional[Currency]:
        """الحصول على العملة الأساسية"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
                WHERE is_base = 1 AND is_active = 1
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return Currency(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    symbol=row[3],
                    is_base=bool(row[4]),
                    is_active=bool(row[5]),
                    decimal_places=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    updated_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
            return None
        except Exception as e:
            print(f"خطأ في الحصول على العملة الأساسية: {e}")
            return None
    
    def get_currency(self, currency_id: int) -> Optional[Currency]:
        """الحصول على عملة حسب المعرف"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
                WHERE id = ?
            """, (currency_id,))
            
            row = cursor.fetchone()
            if row:
                return Currency(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    symbol=row[3],
                    is_base=bool(row[4]),
                    is_active=bool(row[5]),
                    decimal_places=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    updated_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
            return None
        except Exception as e:
            print(f"خطأ في الحصول على العملة: {e}")
            return None
    
    def get_currency_by_code(self, code: str) -> Optional[Currency]:
        """الحصول على عملة حسب الرمز"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
                WHERE UPPER(code) = UPPER(?)
            """, (code,))
            
            row = cursor.fetchone()
            if row:
                return Currency(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    symbol=row[3],
                    is_base=bool(row[4]),
                    is_active=bool(row[5]),
                    decimal_places=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    updated_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
            return None
        except Exception as e:
            print(f"خطأ في الحصول على العملة: {e}")
            return None
    
    def get_all_currencies(self, include_inactive: bool = False) -> List[Currency]:
        """الحصول على جميع العملات"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, code, name, symbol, is_base, is_active, decimal_places,
                       created_at, updated_at
                FROM currencies
            """
            
            if not include_inactive:
                query += " WHERE is_active = 1"
            
            query += " ORDER BY is_base DESC, code ASC"
            
            cursor.execute(query)
            
            currencies = []
            for row in cursor.fetchall():
                currencies.append(Currency(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    symbol=row[3],
                    is_base=bool(row[4]),
                    is_active=bool(row[5]),
                    decimal_places=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    updated_at=datetime.fromisoformat(row[8]) if row[8] else None
                ))
            
            return currencies
        except Exception as e:
            print(f"خطأ في الحصول على العملات: {e}")
            return []
    
    def add_currency(self, currency: Currency) -> Optional[int]:
        """إضافة عملة جديدة"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # إذا كانت العملة الأساسية، إلغاء الأساسية من العملات الأخرى
            if currency.is_base:
                cursor.execute("UPDATE currencies SET is_base = 0 WHERE is_base = 1")
            
            cursor.execute("""
                INSERT INTO currencies (code, name, symbol, is_base, is_active, decimal_places)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                currency.code.upper(),
                currency.name,
                currency.symbol,
                1 if currency.is_base else 0,
                1 if currency.is_active else 0,
                currency.decimal_places
            ))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"خطأ في إضافة العملة: {e}")
            conn.rollback()
            return None
    
    def update_currency(self, currency: Currency) -> bool:
        """تحديث عملة"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # إذا كانت العملة الأساسية، إلغاء الأساسية من العملات الأخرى
            if currency.is_base:
                cursor.execute("UPDATE currencies SET is_base = 0 WHERE is_base = 1 AND id != ?", (currency.id,))
            
            cursor.execute("""
                UPDATE currencies
                SET code = ?, name = ?, symbol = ?, is_base = ?, is_active = ?, 
                    decimal_places = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                currency.code.upper(),
                currency.name,
                currency.symbol,
                1 if currency.is_base else 0,
                1 if currency.is_active else 0,
                currency.decimal_places,
                currency.id
            ))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"خطأ في تحديث العملة: {e}")
            conn.rollback()
            return False
    
    def delete_currency(self, currency_id: int) -> bool:
        """حذف عملة"""
        try:
            # لا يمكن حذف العملة الأساسية
            currency = self.get_currency(currency_id)
            if currency and currency.is_base:
                return False
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM currencies WHERE id = ?", (currency_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"خطأ في حذف العملة: {e}")
            conn.rollback()
            return False

