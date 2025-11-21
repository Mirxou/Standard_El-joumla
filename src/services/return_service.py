#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المرتجعات - Return Service
تقديم خدمات إدارة مرتجعات المبيعات والمشتريات
"""

import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.return_invoice import (
    ReturnInvoice, ReturnItem, ReturnType, 
    ReturnReason, ReturnStatus, RefundMethod
)
from core.database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ReturnService:
    """خدمة إدارة المرتجعات"""
    
    def __init__(self, db_manager: DatabaseManager):
        """تهيئة خدمة المرتجعات"""
        self.db = db_manager
        logger.info("تم تهيئة خدمة المرتجعات")
    
    def generate_return_number(self) -> str:
        """توليد رقم مرتجع جديد"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT return_number FROM return_invoices 
                ORDER BY id DESC LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                last_number = result[0]
                # استخراج الرقم من النمط RET-YYYYMMDD-XXX
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
            return_number = f"RET-{today}-{seq:03d}"
            
            return return_number
        except Exception as e:
            logger.error(f"خطأ في توليد رقم المرتجع: {str(e)}")
            # رقم احتياطي
            return f"RET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def create_return(self, return_invoice: ReturnInvoice) -> int:
        """إنشاء مرتجع جديد"""
        try:
            # توليد رقم إذا لم يكن موجوداً
            if not return_invoice.return_number:
                return_invoice.return_number = self.generate_return_number()
            
            # تعيين تاريخ الإرجاع
            if not return_invoice.return_date:
                return_invoice.return_date = date.today()
            
            # حساب المجاميع
            return_invoice.calculate_totals()
            
            # الطوابع الزمنية
            return_invoice.created_at = datetime.now()
            return_invoice.updated_at = datetime.now()
            
            cursor = self.db.connection.cursor()
            
            # إدراج المرتجع
            cursor.execute("""
                INSERT INTO return_invoices (
                    return_number, return_type, original_sale_id, original_purchase_id,
                    original_invoice_number, customer_id, supplier_id, contact_name,
                    contact_phone, return_date, original_invoice_date, status,
                    return_reason, description, subtotal, discount_amount, tax_amount,
                    total_amount, refund_method, refund_amount, refund_date,
                    refund_reference, credit_note_number, credit_note_amount,
                    exchange_sale_id, notes, internal_notes, created_by, approved_by,
                    created_at, updated_at, approved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                return_invoice.return_number,
                return_invoice.return_type.name if isinstance(return_invoice.return_type, ReturnType) else return_invoice.return_type,
                return_invoice.original_sale_id, return_invoice.original_purchase_id,
                return_invoice.original_invoice_number, return_invoice.customer_id,
                return_invoice.supplier_id, return_invoice.contact_name,
                return_invoice.contact_phone,
                return_invoice.return_date.isoformat() if return_invoice.return_date else None,
                return_invoice.original_invoice_date.isoformat() if return_invoice.original_invoice_date else None,
                return_invoice.status.name if isinstance(return_invoice.status, ReturnStatus) else return_invoice.status,
                return_invoice.return_reason.name if isinstance(return_invoice.return_reason, ReturnReason) else return_invoice.return_reason,
                return_invoice.description, float(return_invoice.subtotal),
                float(return_invoice.discount_amount), float(return_invoice.tax_amount),
                float(return_invoice.total_amount),
                return_invoice.refund_method.name if isinstance(return_invoice.refund_method, RefundMethod) else return_invoice.refund_method,
                float(return_invoice.refund_amount),
                return_invoice.refund_date.isoformat() if return_invoice.refund_date else None,
                return_invoice.refund_reference, return_invoice.credit_note_number,
                float(return_invoice.credit_note_amount), return_invoice.exchange_sale_id,
                return_invoice.notes, return_invoice.internal_notes,
                return_invoice.created_by, return_invoice.approved_by,
                return_invoice.created_at.isoformat() if return_invoice.created_at else None,
                return_invoice.updated_at.isoformat() if return_invoice.updated_at else None,
                return_invoice.approved_at.isoformat() if return_invoice.approved_at else None
            ))
            
            return_id = cursor.lastrowid
            return_invoice.id = return_id
            
            # إدراج البنود
            for item in return_invoice.items:
                item.return_id = return_id
                item.calculate_totals()
                cursor.execute("""
                    INSERT INTO return_items (
                        return_id, original_sale_item_id, original_purchase_item_id,
                        product_id, product_name, product_barcode, quantity_returned,
                        quantity_original, unit_price, discount_amount, tax_amount,
                        total_amount, return_reason, condition, restockable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    return_id, item.original_sale_item_id, item.original_purchase_item_id,
                    item.product_id, item.product_name, item.product_barcode,
                    float(item.quantity_returned), float(item.quantity_original),
                    float(item.unit_price), float(item.discount_amount),
                    float(item.tax_amount), float(item.total_amount),
                    item.return_reason.name if isinstance(item.return_reason, ReturnReason) else item.return_reason,
                    item.condition, 1 if item.restockable else 0, item.notes
                ))
                item.id = cursor.lastrowid
            
            self.db.connection.commit()
            logger.info(f"تم إنشاء المرتجع: {return_invoice.return_number}")
            return return_id
            
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في إنشاء المرتجع: {str(e)}")
            raise
    
    def get_return(self, return_id: int) -> Optional[ReturnInvoice]:
        """الحصول على مرتجع بالمعرف"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT * FROM return_invoices WHERE id = ?", (return_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # تحويل الصف إلى قاموس
            columns = [desc[0] for desc in cursor.description]
            return_data = dict(zip(columns, row))
            
            # الحصول على البنود
            cursor.execute("SELECT * FROM return_items WHERE return_id = ?", (return_id,))
            items_rows = cursor.fetchall()
            items_columns = [desc[0] for desc in cursor.description]
            
            items = []
            for item_row in items_rows:
                item_data = dict(zip(items_columns, item_row))
                # تحويل restockable من int إلى bool
                item_data['restockable'] = bool(item_data.get('restockable', 1))
                items.append(ReturnItem.from_dict(item_data))
            
            return_data['items'] = items
            return_invoice = ReturnInvoice.from_dict(return_data)
            
            return return_invoice
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المرتجع {return_id}: {str(e)}")
            return None
    
    def get_return_by_number(self, return_number: str) -> Optional[ReturnInvoice]:
        """الحصول على مرتجع بالرقم"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT id FROM return_invoices WHERE return_number = ?", (return_number,))
            row = cursor.fetchone()
            
            if row:
                return self.get_return(row[0])
            return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المرتجع {return_number}: {str(e)}")
            return None
    
    def update_return(self, return_invoice: ReturnInvoice) -> bool:
        """تحديث مرتجع"""
        try:
            return_invoice.calculate_totals()
            return_invoice.updated_at = datetime.now()
            
            cursor = self.db.connection.cursor()
            
            # تحديث المرتجع
            cursor.execute("""
                UPDATE return_invoices SET
                    return_type = ?, original_sale_id = ?, original_purchase_id = ?,
                    original_invoice_number = ?, customer_id = ?, supplier_id = ?,
                    contact_name = ?, contact_phone = ?, return_date = ?,
                    original_invoice_date = ?, status = ?, return_reason = ?,
                    description = ?, subtotal = ?, discount_amount = ?, tax_amount = ?,
                    total_amount = ?, refund_method = ?, refund_amount = ?,
                    refund_date = ?, refund_reference = ?, credit_note_number = ?,
                    credit_note_amount = ?, exchange_sale_id = ?, notes = ?,
                    internal_notes = ?, approved_by = ?, updated_at = ?, approved_at = ?
                WHERE id = ?
            """, (
                return_invoice.return_type.name if isinstance(return_invoice.return_type, ReturnType) else return_invoice.return_type,
                return_invoice.original_sale_id, return_invoice.original_purchase_id,
                return_invoice.original_invoice_number, return_invoice.customer_id,
                return_invoice.supplier_id, return_invoice.contact_name,
                return_invoice.contact_phone,
                return_invoice.return_date.isoformat() if return_invoice.return_date else None,
                return_invoice.original_invoice_date.isoformat() if return_invoice.original_invoice_date else None,
                return_invoice.status.name if isinstance(return_invoice.status, ReturnStatus) else return_invoice.status,
                return_invoice.return_reason.name if isinstance(return_invoice.return_reason, ReturnReason) else return_invoice.return_reason,
                return_invoice.description, float(return_invoice.subtotal),
                float(return_invoice.discount_amount), float(return_invoice.tax_amount),
                float(return_invoice.total_amount),
                return_invoice.refund_method.name if isinstance(return_invoice.refund_method, RefundMethod) else return_invoice.refund_method,
                float(return_invoice.refund_amount),
                return_invoice.refund_date.isoformat() if return_invoice.refund_date else None,
                return_invoice.refund_reference, return_invoice.credit_note_number,
                float(return_invoice.credit_note_amount), return_invoice.exchange_sale_id,
                return_invoice.notes, return_invoice.internal_notes,
                return_invoice.approved_by,
                return_invoice.updated_at.isoformat() if return_invoice.updated_at else None,
                return_invoice.approved_at.isoformat() if return_invoice.approved_at else None,
                return_invoice.id
            ))
            
            # حذف البنود القديمة
            cursor.execute("DELETE FROM return_items WHERE return_id = ?", (return_invoice.id,))
            
            # إدراج البنود الجديدة
            for item in return_invoice.items:
                item.return_id = return_invoice.id
                item.calculate_totals()
                cursor.execute("""
                    INSERT INTO return_items (
                        return_id, original_sale_item_id, original_purchase_item_id,
                        product_id, product_name, product_barcode, quantity_returned,
                        quantity_original, unit_price, discount_amount, tax_amount,
                        total_amount, return_reason, condition, restockable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    return_invoice.id, item.original_sale_item_id, item.original_purchase_item_id,
                    item.product_id, item.product_name, item.product_barcode,
                    float(item.quantity_returned), float(item.quantity_original),
                    float(item.unit_price), float(item.discount_amount),
                    float(item.tax_amount), float(item.total_amount),
                    item.return_reason.name if isinstance(item.return_reason, ReturnReason) else item.return_reason,
                    item.condition, 1 if item.restockable else 0, item.notes
                ))
            
            self.db.connection.commit()
            logger.info(f"تم تحديث المرتجع: {return_invoice.return_number}")
            return True
            
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في تحديث المرتجع: {str(e)}")
            return False
    
    def delete_return(self, return_id: int) -> bool:
        """حذف مرتجع"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM return_invoices WHERE id = ?", (return_id,))
            self.db.connection.commit()
            logger.info(f"تم حذف المرتجع {return_id}")
            return True
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في حذف المرتجع: {str(e)}")
            return False
    
    def get_all_returns(self, return_type: Optional[ReturnType] = None,
                       status: Optional[ReturnStatus] = None,
                       customer_id: Optional[int] = None,
                       supplier_id: Optional[int] = None,
                       from_date: Optional[date] = None,
                       to_date: Optional[date] = None) -> List[ReturnInvoice]:
        """الحصول على جميع المرتجعات مع فلترة اختيارية"""
        try:
            query = "SELECT * FROM return_invoices WHERE 1=1"
            params = []
            
            if return_type:
                query += " AND return_type = ?"
                params.append(return_type.name if isinstance(return_type, ReturnType) else return_type)
            
            if status:
                query += " AND status = ?"
                params.append(status.name if isinstance(status, ReturnStatus) else status)
            
            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)
            
            if supplier_id:
                query += " AND supplier_id = ?"
                params.append(supplier_id)
            
            if from_date:
                query += " AND return_date >= ?"
                params.append(from_date.isoformat())
            
            if to_date:
                query += " AND return_date <= ?"
                params.append(to_date.isoformat())
            
            query += " ORDER BY return_date DESC, id DESC"
            
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            returns = []
            for row in rows:
                columns = [desc[0] for desc in cursor.description]
                return_data = dict(zip(columns, row))
                
                # الحصول على البنود
                cursor.execute("SELECT * FROM return_items WHERE return_id = ?", (return_data['id'],))
                items_rows = cursor.fetchall()
                items_columns = [desc[0] for desc in cursor.description]
                
                items = []
                for item_row in items_rows:
                    item_data = dict(zip(items_columns, item_row))
                    item_data['restockable'] = bool(item_data.get('restockable', 1))
                    items.append(ReturnItem.from_dict(item_data))
                
                return_data['items'] = items
                returns.append(ReturnInvoice.from_dict(return_data))
            
            return returns
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المرتجعات: {str(e)}")
            return []
    
    def approve_return(self, return_id: int, approved_by: int) -> bool:
        """الموافقة على مرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.approve(approved_by):
            return self.update_return(return_invoice)
        return False
    
    def reject_return(self, return_id: int) -> bool:
        """رفض مرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.reject():
            return self.update_return(return_invoice)
        return False
    
    def complete_return(self, return_id: int) -> bool:
        """إتمام مرتجع (بعد الاستلام والمعالجة)"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.complete():
            # تحديث المخزون للبنود القابلة لإعادة التخزين
            if return_invoice.is_sale_return:
                for item in return_invoice.restockable_items:
                    self._restock_item(item.product_id, item.quantity_returned)
            
            return self.update_return(return_invoice)
        return False
    
    def cancel_return(self, return_id: int) -> bool:
        """إلغاء مرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.cancel():
            return self.update_return(return_invoice)
        return False
    
    def process_refund(self, return_id: int, method: RefundMethod, 
                      amount: Decimal, reference: Optional[str] = None) -> bool:
        """معالجة استرداد المبلغ"""
        return_invoice = self.get_return(return_id)
        if return_invoice:
            return_invoice.process_refund(method, amount, reference)
            return self.update_return(return_invoice)
        return False
    
    def generate_credit_note(self, return_id: int) -> Optional[str]:
        """إنشاء إشعار دائن للمرتجع"""
        return_invoice = self.get_return(return_id)
        if return_invoice and return_invoice.status == ReturnStatus.APPROVED:
            # توليد رقم إشعار دائن
            credit_note_number = f"CN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return_invoice.generate_credit_note(credit_note_number)
            
            if self.update_return(return_invoice):
                logger.info(f"تم إنشاء إشعار دائن: {credit_note_number}")
                return credit_note_number
        return None
    
    def _restock_item(self, product_id: int, quantity: Decimal) -> bool:
        """إعادة المنتج للمخزون"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity + ?
                WHERE id = ?
            """, (float(quantity), product_id))
            
            self.db.connection.commit()
            logger.info(f"تم إعادة {quantity} من المنتج {product_id} للمخزون")
            return True
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"خطأ في إعادة المنتج للمخزون: {str(e)}")
            return False
    
    def get_returns_by_original_sale(self, sale_id: int) -> List[ReturnInvoice]:
        """الحصول على جميع المرتجعات المرتبطة بفاتورة بيع"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT id FROM return_invoices 
                WHERE original_sale_id = ?
                ORDER BY return_date DESC
            """, (sale_id,))
            
            return_ids = [row[0] for row in cursor.fetchall()]
            return [self.get_return(rid) for rid in return_ids if self.get_return(rid)]
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على مرتجعات البيع: {str(e)}")
            return []
    
    def get_return_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المرتجعات"""
        try:
            cursor = self.db.connection.cursor()
            
            stats = {}
            
            # العدد والقيمة حسب النوع
            cursor.execute("""
                SELECT return_type, COUNT(*), SUM(total_amount)
                FROM return_invoices
                GROUP BY return_type
            """)
            stats['by_type'] = {row[0]: {'count': row[1], 'total': row[2] or 0} 
                               for row in cursor.fetchall()}
            
            # العدد حسب الحالة
            cursor.execute("""
                SELECT status, COUNT(*), SUM(total_amount)
                FROM return_invoices
                GROUP BY status
            """)
            stats['by_status'] = {row[0]: {'count': row[1], 'total': row[2] or 0} 
                                 for row in cursor.fetchall()}
            
            # العدد حسب السبب
            cursor.execute("""
                SELECT return_reason, COUNT(*)
                FROM return_invoices
                WHERE return_reason IS NOT NULL
                GROUP BY return_reason
            """)
            stats['by_reason'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # إجمالي المرتجعات
            cursor.execute("SELECT COUNT(*), SUM(total_amount), SUM(refund_amount) FROM return_invoices")
            row = cursor.fetchone()
            stats['total_count'] = row[0] or 0
            stats['total_value'] = row[1] or 0
            stats['total_refunded'] = row[2] or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المرتجعات: {str(e)}")
            return {}
