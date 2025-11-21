#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الفوترة والدفع - Billing & Payments Service
توليد الفواتير، تسجيل المدفوعات، وإدارة الفواتير الدورية (Subscriptions)
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class BillingService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def generate_invoice(self, sale_id: int, due_days: int = 0) -> Optional[int]:
        try:
            # استرداد بيانات الطلب
            sale = self.db.fetch_one('SELECT id, customer_id, total_amount FROM sales WHERE id = ?', (sale_id,))
            if not sale:
                if self.logger:
                    self.logger.warning(f'لم يتم العثور على الطلب {sale_id} عند توليد الفاتورة')
                else:
                    print(f'WARN: sale {sale_id} not found when generating invoice')
                return None
            total = sale[2]
            now = datetime.now()
            due = None
            if due_days and isinstance(due_days, int) and due_days > 0:
                due = now + timedelta(days=due_days)
            q = 'INSERT INTO invoices (sale_id, customer_id, amount, status, issued_at, due_at) VALUES (?, ?, ?, ?, ?, ?)'
            res = self.db.execute_query(q, (sale_id, sale[1], float(total), 'unpaid', now, due))
            try:
                invoice_id = self.db.get_last_insert_id()
            except Exception:
                invoice_id = None

            if invoice_id:
                if self.logger:
                    self.logger.info(f'تم إنشاء فاتورة ID={invoice_id} للطلب {sale_id}')
                else:
                    print(f'INFO: created invoice ID={invoice_id} for sale {sale_id}')
                return invoice_id
            else:
                if self.logger:
                    self.logger.warning(f'فشل إنشاء الفاتورة للطلب {sale_id}')
                else:
                    print(f'WARN: failed to create invoice for sale {sale_id}')
                return None
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في توليد الفاتورة: {e}')
        return None

    def record_payment(self, invoice_id: int, amount: Decimal, method: str = 'cash', reference: str = None) -> bool:
        try:
            now = datetime.now()
            # Try invoice-oriented payments table first
            try:
                q = 'INSERT INTO payments (invoice_id, amount, method, reference, paid_at) VALUES (?, ?, ?, ?, ?)'
                self.db.execute_query(q, (invoice_id, float(amount), method, reference, now))
            except Exception as e:
                # Fallback to core payments schema (payment_type, entity_id, amount, payment_method, reference_number, payment_date, status, notes, user_id, created_at, updated_at)
                msg = str(e)
                # Check for various "column missing" error messages
                if 'no column' in msg or 'no such column' in msg:
                    # Use core payment schema - simpler insertion
                    q2 = '''INSERT INTO payments (payment_type, entity_id, amount, payment_method, reference_number, payment_date, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                    params2 = (
                        'customer_payment',
                        invoice_id,
                        float(amount),
                        method,
                        reference,
                        now,
                        'completed',
                        now,
                        now
                    )
                    self.db.execute_query(q2, params2)
                else:
                    raise
            # تحديث حالة الفاتورة - تبسيط: اعتبار هذه الدفعة كافية إذا غطت مبلغ الفاتورة
            try:
                invoice_amount = self.db.fetch_one('SELECT amount FROM invoices WHERE id = ?', (invoice_id,))[0] or 0
                if float(amount) >= float(invoice_amount):
                    self.db.execute_query('UPDATE invoices SET status = ?, paid_at = ? WHERE id = ?', ('paid', now, invoice_id))
                if self.logger:
                    self.logger.info(f'تم تسجيل دفعة على الفاتورة {invoice_id} المبلغ: {amount}')
            except Exception as e:
                if self.logger:
                    self.logger.error(f'خطأ عند تحديث حالة الفاتورة بعد الدفع: {e}')
                else:
                    print('WARN: failed to update invoice status after payment:', e)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في تسجيل الدفعة: {e}')
            else:
                import traceback
                print('ERROR recording payment:', e)
                print(traceback.format_exc())
            return False

    def create_recurring_invoice(self, subscription_id: int) -> Optional[int]:
        # تبسيط: إنشاء فاتورة بناءً على إعدادات الاشتراك
        try:
            sub = self.db.fetch_one('SELECT id, customer_id, amount, frequency_days FROM subscriptions WHERE id = ?', (subscription_id,))
            if not sub:
                return None
            # توليد فاتورة
            return self.generate_invoice_for_subscription(sub)
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء فاتورة دورية: {e}')
            return None

    def generate_invoice_for_subscription(self, sub_row) -> Optional[int]:
        try:
            # sub_row: (id, customer_id, amount, frequency_days)
            now = datetime.now()
            q = 'INSERT INTO invoices (sale_id, customer_id, amount, status, issued_at) VALUES (?, ?, ?, ?, ?)'
            res = self.db.execute_query(q, (None, sub_row[1], float(sub_row[2]), 'unpaid', now))
            if res and hasattr(res,'lastrowid'):
                return res.lastrowid
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في توليد فاتورة للاشتراك: {e}')
        return None
