#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة عروض الأسعار - Quote Service
تقديم خدمات إدارة عروض الأسعار
"""

import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.quote import Quote, QuoteItem, QuoteStatus
from core.database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class QuoteService:
    """خدمة إدارة عروض الأسعار"""
    
    def __init__(self, db_manager: DatabaseManager):
        """تهيئة خدمة عروض الأسعار"""
        self.db = db_manager
        logger.info("تم تهيئة خدمة عروض الأسعار")
    
    def generate_quote_number(self) -> str:
        """توليد رقم عرض سعر جديد"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT quote_number FROM quotes 
                ORDER BY id DESC LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                last_number = result[0]
                # استخراج الرقم من النمط QT-YYYYMMDD-XXX
                if '-' in last_number:
                    parts = last_number.split('-')
                    if len(parts) == 3:
                        seq = int(parts[2]) + 1
                    else:
                        seq = 1
                else:
                    seq = 1
            else:
                seq = 1
            
            # توليد رقم جديد
            today = date.today().strftime('%Y%m%d')
            quote_number = f"QT-{today}-{seq:03d}"
            
            return quote_number
        except Exception as e:
            logger.error(f"خطأ في توليد رقم عرض السعر: {str(e)}")
            # رقم احتياطي
            return f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def create_quote(self, quote: Quote) -> int:
        """إنشاء عرض سعر جديد"""
        try:
            # توليد رقم إذا لم يكن موجوداً
            if not quote.quote_number:
                quote.quote_number = self.generate_quote_number()
            
            # تعيين تاريخ العرض
            if not quote.quote_date:
                quote.quote_date = date.today()
            
            # تعيين تاريخ الصلاحية (30 يوم افتراضياً)
            if not quote.valid_until:
                quote.valid_until = quote.quote_date + timedelta(days=30)
            
            # حساب المجاميع
            quote.calculate_totals()
            
            # الطوابع الزمنية
            quote.created_at = datetime.now()
            quote.updated_at = datetime.now()
            
            cursor = self.db.connection.cursor()
            
            # إدراج عرض السعر
            cursor.execute("""
                INSERT INTO quotes (
                    quote_number, customer_id, customer_name, customer_phone,
                    customer_email, customer_address, quote_date, valid_until,
                    sent_date, response_date, status, subtotal, discount_amount,
                    discount_percentage, tax_amount, total_amount, payment_terms,
                    delivery_terms, notes, internal_notes, terms_and_conditions,
                    converted_to_sale_id, converted_date, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quote.quote_number, quote.customer_id, quote.customer_name,
                quote.customer_phone, quote.customer_email, quote.customer_address,
                quote.quote_date.isoformat() if quote.quote_date else None,
                quote.valid_until.isoformat() if quote.valid_until else None,
                quote.sent_date.isoformat() if quote.sent_date else None,
                quote.response_date.isoformat() if quote.response_date else None,
                quote.status.name if isinstance(quote.status, QuoteStatus) else quote.status,
                float(quote.subtotal), float(quote.discount_amount),
                float(quote.discount_percentage), float(quote.tax_amount),
                float(quote.total_amount), quote.payment_terms, quote.delivery_terms,
                quote.notes, quote.internal_notes, quote.terms_and_conditions,
                quote.converted_to_sale_id,
                quote.converted_date.isoformat() if quote.converted_date else None,
                quote.created_by,
                quote.created_at.isoformat() if quote.created_at else None,
                quote.updated_at.isoformat() if quote.updated_at else None
            ))
            
            quote_id = cursor.lastrowid
            quote.id = quote_id
            
            # إدراج البنود
            for item in quote.items:
                item.quote_id = quote_id
                item.calculate_totals()
                cursor.execute("""
                    INSERT INTO quote_items (
                        quote_id, product_id, product_name, product_barcode,
                        description, quantity, unit_price, discount_amount,
                        discount_percentage, tax_amount, tax_percentage,
                        total_amount, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quote_id, item.product_id, item.product_name, item.product_barcode,
                    item.description, float(item.quantity), float(item.unit_price),
                    float(item.discount_amount), float(item.discount_percentage),
                    float(item.tax_amount), float(item.tax_percentage),
                    float(item.total_amount), item.notes
                ))
                item.id = cursor.lastrowid
            
            self.db.connection.commit()
            logger.info(f"تم إنشاء عرض السعر: {quote.quote_number}")
            return quote_id
            
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في إنشاء عرض السعر: {str(e)}")
            raise
    
    def get_quote(self, quote_id: int) -> Optional[Quote]:
        """الحصول على عرض سعر بالمعرف"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # تحويل الصف إلى قاموس
            columns = [desc[0] for desc in cursor.description]
            quote_data = dict(zip(columns, row))
            
            # الحصول على البنود
            cursor.execute("SELECT * FROM quote_items WHERE quote_id = ?", (quote_id,))
            items_rows = cursor.fetchall()
            items_columns = [desc[0] for desc in cursor.description]
            
            items = []
            for item_row in items_rows:
                item_data = dict(zip(items_columns, item_row))
                items.append(QuoteItem.from_dict(item_data))
            
            quote_data['items'] = items
            quote = Quote.from_dict(quote_data)
            
            return quote
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على عرض السعر {quote_id}: {str(e)}")
            return None
    
    def get_quote_by_number(self, quote_number: str) -> Optional[Quote]:
        """الحصول على عرض سعر بالرقم"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT id FROM quotes WHERE quote_number = ?", (quote_number,))
            row = cursor.fetchone()
            
            if row:
                return self.get_quote(row[0])
            return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على عرض السعر {quote_number}: {str(e)}")
            return None
    
    def update_quote(self, quote: Quote) -> bool:
        """تحديث عرض سعر"""
        try:
            quote.calculate_totals()
            quote.updated_at = datetime.now()
            
            cursor = self.db.connection.cursor()
            
            # تحديث العرض
            cursor.execute("""
                UPDATE quotes SET
                    customer_id = ?, customer_name = ?, customer_phone = ?,
                    customer_email = ?, customer_address = ?, quote_date = ?,
                    valid_until = ?, sent_date = ?, response_date = ?,
                    status = ?, subtotal = ?, discount_amount = ?,
                    discount_percentage = ?, tax_amount = ?, total_amount = ?,
                    payment_terms = ?, delivery_terms = ?, notes = ?,
                    internal_notes = ?, terms_and_conditions = ?,
                    converted_to_sale_id = ?, converted_date = ?, updated_at = ?
                WHERE id = ?
            """, (
                quote.customer_id, quote.customer_name, quote.customer_phone,
                quote.customer_email, quote.customer_address,
                quote.quote_date.isoformat() if quote.quote_date else None,
                quote.valid_until.isoformat() if quote.valid_until else None,
                quote.sent_date.isoformat() if quote.sent_date else None,
                quote.response_date.isoformat() if quote.response_date else None,
                quote.status.name if isinstance(quote.status, QuoteStatus) else quote.status,
                float(quote.subtotal), float(quote.discount_amount),
                float(quote.discount_percentage), float(quote.tax_amount),
                float(quote.total_amount), quote.payment_terms, quote.delivery_terms,
                quote.notes, quote.internal_notes, quote.terms_and_conditions,
                quote.converted_to_sale_id,
                quote.converted_date.isoformat() if quote.converted_date else None,
                quote.updated_at.isoformat() if quote.updated_at else None,
                quote.id
            ))
            
            # حذف البنود القديمة
            cursor.execute("DELETE FROM quote_items WHERE quote_id = ?", (quote.id,))
            
            # إدراج البنود الجديدة
            for item in quote.items:
                item.quote_id = quote.id
                item.calculate_totals()
                cursor.execute("""
                    INSERT INTO quote_items (
                        quote_id, product_id, product_name, product_barcode,
                        description, quantity, unit_price, discount_amount,
                        discount_percentage, tax_amount, tax_percentage,
                        total_amount, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quote.id, item.product_id, item.product_name, item.product_barcode,
                    item.description, float(item.quantity), float(item.unit_price),
                    float(item.discount_amount), float(item.discount_percentage),
                    float(item.tax_amount), float(item.tax_percentage),
                    float(item.total_amount), item.notes
                ))
            
            self.db.connection.commit()
            logger.info(f"تم تحديث عرض السعر: {quote.quote_number}")
            return True
            
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في تحديث عرض السعر: {str(e)}")
            return False
    
    def delete_quote(self, quote_id: int) -> bool:
        """حذف عرض سعر"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
            self.db.connection.commit()
            logger.info(f"تم حذف عرض السعر {quote_id}")
            return True
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في حذف عرض السعر: {str(e)}")
            return False
    
    def get_all_quotes(self, status: Optional[QuoteStatus] = None,
                       customer_id: Optional[int] = None,
                       from_date: Optional[date] = None,
                       to_date: Optional[date] = None) -> List[Quote]:
        """الحصول على جميع عروض الأسعار مع فلترة اختيارية"""
        try:
            query = "SELECT * FROM quotes WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status.name if isinstance(status, QuoteStatus) else status)
            
            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)
            
            if from_date:
                query += " AND quote_date >= ?"
                params.append(from_date.isoformat())
            
            if to_date:
                query += " AND quote_date <= ?"
                params.append(to_date.isoformat())
            
            query += " ORDER BY quote_date DESC, id DESC"
            
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            quotes = []
            for row in rows:
                columns = [desc[0] for desc in cursor.description]
                quote_data = dict(zip(columns, row))
                
                # الحصول على البنود
                cursor.execute("SELECT * FROM quote_items WHERE quote_id = ?", (quote_data['id'],))
                items_rows = cursor.fetchall()
                items_columns = [desc[0] for desc in cursor.description]
                
                items = []
                for item_row in items_rows:
                    item_data = dict(zip(items_columns, item_row))
                    items.append(QuoteItem.from_dict(item_data))
                
                quote_data['items'] = items
                quotes.append(Quote.from_dict(quote_data))
            
            return quotes
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على عروض الأسعار: {str(e)}")
            return []
    
    def update_quote_status(self, quote_id: int, status: QuoteStatus) -> bool:
        """تحديث حالة عرض السعر"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                UPDATE quotes 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status.name, datetime.now().isoformat(), quote_id))
            
            self.db.connection.commit()
            logger.info(f"تم تحديث حالة عرض السعر {quote_id} إلى {status.value}")
            return True
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في تحديث حالة عرض السعر: {str(e)}")
            return False
    
    def mark_quote_as_sent(self, quote_id: int) -> bool:
        """تعليم عرض السعر كمرسل"""
        quote = self.get_quote(quote_id)
        if quote:
            quote.mark_as_sent()
            return self.update_quote(quote)
        return False
    
    def accept_quote(self, quote_id: int) -> bool:
        """قبول عرض السعر"""
        quote = self.get_quote(quote_id)
        if quote:
            quote.mark_as_accepted()
            return self.update_quote(quote)
        return False
    
    def reject_quote(self, quote_id: int) -> bool:
        """رفض عرض السعر"""
        quote = self.get_quote(quote_id)
        if quote:
            quote.mark_as_rejected()
            return self.update_quote(quote)
        return False
    
    def check_expired_quotes(self) -> List[int]:
        """فحص وتحديث العروض منتهية الصلاحية"""
        try:
            cursor = self.db.connection.cursor()
            today = date.today().isoformat()
            
            # الحصول على العروض منتهية الصلاحية
            cursor.execute("""
                SELECT id FROM quotes 
                WHERE valid_until < ? 
                AND status NOT IN ('CONVERTED', 'ACCEPTED', 'REJECTED', 'CANCELLED', 'EXPIRED')
            """, (today,))
            
            expired_ids = [row[0] for row in cursor.fetchall()]
            
            # تحديث الحالة
            if expired_ids:
                placeholders = ','.join('?' * len(expired_ids))
                cursor.execute(f"""
                    UPDATE quotes 
                    SET status = 'EXPIRED', updated_at = ?
                    WHERE id IN ({placeholders})
                """, [datetime.now().isoformat()] + expired_ids)
                
                self.db.connection.commit()
                logger.info(f"تم تحديث {len(expired_ids)} عرض سعر منتهي الصلاحية")
            
            return expired_ids
            
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في فحص عروض الأسعار منتهية الصلاحية: {str(e)}")
            return []
    
    def get_quote_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات عروض الأسعار"""
        try:
            cursor = self.db.connection.cursor()
            
            stats = {}
            
            # العدد حسب الحالة
            cursor.execute("""
                SELECT status, COUNT(*), SUM(total_amount)
                FROM quotes
                GROUP BY status
            """)
            stats['by_status'] = {row[0]: {'count': row[1], 'total': row[2] or 0} 
                                 for row in cursor.fetchall()}
            
            # إجمالي العروض
            cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM quotes")
            row = cursor.fetchone()
            stats['total_count'] = row[0] or 0
            stats['total_value'] = row[1] or 0
            
            # معدل القبول
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'ACCEPTED' THEN 1 END) * 100.0 / COUNT(*) as acceptance_rate,
                    COUNT(CASE WHEN status = 'CONVERTED' THEN 1 END) * 100.0 / COUNT(*) as conversion_rate
                FROM quotes
                WHERE status IN ('ACCEPTED', 'REJECTED', 'CONVERTED')
            """)
            row = cursor.fetchone()
            stats['acceptance_rate'] = row[0] or 0
            stats['conversion_rate'] = row[1] or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات عروض الأسعار: {str(e)}")
            return {}
