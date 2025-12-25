#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة أسعار الصرف - Exchange Rate Service
إدارة أسعار الصرف وتحويل العملات
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.models.currency import Currency, ExchangeRate, CurrencyManager
from src.utils.logger import setup_logger


class ExchangeRateService:
    """خدمة أسعار الصرف"""
    
    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.currency_manager = CurrencyManager(db_manager)
    
    def get_exchange_rate(
        self, 
        from_currency_id: int, 
        to_currency_id: int, 
        target_date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        الحصول على سعر الصرف بين عملتين
        
        Args:
            from_currency_id: معرف العملة المصدر
            to_currency_id: معرف العملة الهدف
            target_date: التاريخ المطلوب (افتراضي: اليوم)
        
        Returns:
            سعر الصرف أو None إذا لم يوجد
        """
        try:
            if from_currency_id == to_currency_id:
                return Decimal('1.0')
            
            if target_date is None:
                target_date = date.today()
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # البحث عن سعر الصرف النشط للتاريخ المحدد
            cursor.execute("""
                SELECT rate
                FROM exchange_rates
                WHERE from_currency_id = ?
                  AND to_currency_id = ?
                  AND effective_date <= ?
                  AND (expiry_date IS NULL OR expiry_date >= ?)
                  AND is_active = 1
                ORDER BY effective_date DESC
                LIMIT 1
            """, (from_currency_id, to_currency_id, target_date, target_date))
            
            row = cursor.fetchone()
            if row:
                return Decimal(str(row[0]))
            
            # محاولة العكس (إذا كان 1 USD = 134.5 DZD، فإن 1 DZD = 1/134.5 USD)
            cursor.execute("""
                SELECT rate
                FROM exchange_rates
                WHERE from_currency_id = ?
                  AND to_currency_id = ?
                  AND effective_date <= ?
                  AND (expiry_date IS NULL OR expiry_date >= ?)
                  AND is_active = 1
                ORDER BY effective_date DESC
                LIMIT 1
            """, (to_currency_id, from_currency_id, target_date, target_date))
            
            row = cursor.fetchone()
            if row:
                # حساب المعكوس
                return Decimal('1.0') / Decimal(str(row[0]))
            
            return None
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سعر الصرف: {e}")
            return None
    
    def convert_amount(
        self,
        amount: Decimal,
        from_currency_id: int,
        to_currency_id: int,
        target_date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        تحويل مبلغ من عملة إلى أخرى
        
        Args:
            amount: المبلغ المراد تحويله
            from_currency_id: معرف العملة المصدر
            to_currency_id: معرف العملة الهدف
            target_date: التاريخ المطلوب (افتراضي: اليوم)
        
        Returns:
            المبلغ المحول أو None إذا فشل التحويل
        """
        try:
            if from_currency_id == to_currency_id:
                return amount
            
            rate = self.get_exchange_rate(from_currency_id, to_currency_id, target_date)
            if rate is None:
                return None
            
            return amount * rate
        except Exception as e:
            self.logger.error(f"خطأ في تحويل المبلغ: {e}")
            return None
    
    def convert_to_base_currency(
        self,
        amount: Decimal,
        currency_id: int,
        target_date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        تحويل مبلغ إلى العملة الأساسية
        
        Args:
            amount: المبلغ المراد تحويله
            currency_id: معرف العملة الحالية
            target_date: التاريخ المطلوب (افتراضي: اليوم)
        
        Returns:
            المبلغ بالعملة الأساسية أو None إذا فشل التحويل
        """
        try:
            base_currency = self.currency_manager.get_base_currency()
            if not base_currency:
                return None
            
            if currency_id == base_currency.id:
                return amount
            
            return self.convert_amount(amount, currency_id, base_currency.id, target_date)
        except Exception as e:
            self.logger.error(f"خطأ في تحويل المبلغ إلى العملة الأساسية: {e}")
            return None
    
    def add_exchange_rate(
        self,
        from_currency_id: int,
        to_currency_id: int,
        rate: Decimal,
        effective_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        source: str = "manual"
    ) -> Optional[int]:
        """
        إضافة سعر صرف جديد
        
        Args:
            from_currency_id: معرف العملة المصدر
            to_currency_id: معرف العملة الهدف
            rate: سعر الصرف
            effective_date: تاريخ بدء السعر (افتراضي: اليوم)
            expiry_date: تاريخ انتهاء السعر (افتراضي: None)
            source: مصدر السعر (manual, api, etc.)
        
        Returns:
            معرف السعر الجديد أو None إذا فشل
        """
        try:
            if effective_date is None:
                effective_date = date.today()
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO exchange_rates 
                (from_currency_id, to_currency_id, rate, effective_date, expiry_date, source, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                from_currency_id,
                to_currency_id,
                float(rate),
                effective_date.isoformat(),
                expiry_date.isoformat() if expiry_date else None,
                source
            ))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"خطأ في إضافة سعر الصرف: {e}")
            conn.rollback()
            return None
    
    def update_exchange_rate(
        self,
        rate_id: int,
        rate: Decimal,
        expiry_date: Optional[date] = None,
        is_active: bool = True
    ) -> bool:
        """
        تحديث سعر صرف موجود
        
        Args:
            rate_id: معرف سعر الصرف
            rate: سعر الصرف الجديد
            expiry_date: تاريخ انتهاء السعر
            is_active: هل السعر نشط؟
        
        Returns:
            True إذا نجح التحديث، False خلاف ذلك
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE exchange_rates
                SET rate = ?, expiry_date = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                float(rate),
                expiry_date.isoformat() if expiry_date else None,
                1 if is_active else 0,
                rate_id
            ))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"خطأ في تحديث سعر الصرف: {e}")
            conn.rollback()
            return False
    
    def delete_exchange_rate(self, rate_id: int) -> bool:
        """
        حذف سعر صرف (تعطيل بدلاً من الحذف الفعلي للحفاظ على التاريخ)
        
        Args:
            rate_id: معرف سعر الصرف
        
        Returns:
            True إذا نجح الحذف، False خلاف ذلك
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # التحقق من وجود السعر
            cursor.execute("SELECT id FROM exchange_rates WHERE id = ?", (rate_id,))
            if not cursor.fetchone():
                self.logger.warning(f"سعر الصرف برقم {rate_id} غير موجود")
                return False
            
            # تعطيل بدلاً من الحذف الفعلي
            cursor.execute("""
                UPDATE exchange_rates
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (rate_id,))
            
            conn.commit()
            self.logger.info(f"تم تعطيل سعر الصرف برقم {rate_id}")
            return True
        except Exception as e:
            self.logger.error(f"خطأ في حذف سعر الصرف: {e}")
            conn.rollback()
            return False
    
    def get_exchange_rates(
        self,
        from_currency_id: Optional[int] = None,
        to_currency_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[ExchangeRate]:
        """
        الحصول على قائمة أسعار الصرف
        
        Args:
            from_currency_id: فلترة حسب العملة المصدر (اختياري)
            to_currency_id: فلترة حسب العملة الهدف (اختياري)
            include_inactive: تضمين الأسعار غير النشطة
        
        Returns:
            قائمة أسعار الصرف
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, from_currency_id, to_currency_id, rate, effective_date,
                       expiry_date, source, is_active, created_at, updated_at
                FROM exchange_rates
                WHERE 1=1
            """
            
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
            
            cursor.execute(query, params)
            
            rates = []
            for row in cursor.fetchall():
                rates.append(ExchangeRate(
                    id=row[0],
                    from_currency_id=row[1],
                    to_currency_id=row[2],
                    rate=Decimal(str(row[3])),
                    effective_date=date.fromisoformat(row[4]) if row[4] else None,
                    expiry_date=date.fromisoformat(row[5]) if row[5] else None,
                    source=row[6],
                    is_active=bool(row[7]),
                    created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    updated_at=datetime.fromisoformat(row[9]) if row[9] else None
                ))
            
            return rates
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على أسعار الصرف: {e}")
            return []
    
    def sync_exchange_rates_from_api(self) -> bool:
        """
        مزامنة أسعار الصرف من API خارجي
        
        Returns:
            True إذا نجحت المزامنة، False خلاف ذلك
        """
        try:
            # TODO: تنفيذ مزامنة من API (Fixer.io, ExchangeRate-API, etc.)
            # سيتم تنفيذها في المرحلة التالية
            self.logger.info("مزامنة أسعار الصرف من API - قيد التطوير")
            return False
        except Exception as e:
            self.logger.error(f"خطأ في مزامنة أسعار الصرف: {e}")
            return False

