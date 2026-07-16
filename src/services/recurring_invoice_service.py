#!/usr/bin/env python3
"""
خدمة الفوترة الدورية (Recurring Invoice Service)
تدعم إنشاء فواتير متكررة تلقائياً للعملاء حسب جدول زمني محدد (شهري/سنوي)
"""

import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional


class RecurringInvoiceService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self._init_table()

    def _init_table(self):
        q = """
        CREATE TABLE IF NOT EXISTS recurring_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            frequency TEXT NOT NULL, -- 'monthly', 'quarterly', 'yearly', 'weekly'
            amount REAL NOT NULL,
            description TEXT,
            last_invoice_date DATE,
            next_invoice_date DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute_query(q)

    def create_subscription(
        self,
        customer_id: int,
        amount: float,
        frequency: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
    ) -> int:
        start = start_date or datetime.now().strftime("%Y-%m-%d")
        q = """
        INSERT INTO recurring_invoices (customer_id, start_date, end_date, frequency, amount, description, next_invoice_date)  # noqa: E501
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        next_date = start
        params = (
            customer_id,
            start,
            end_date,
            frequency,
            amount,
            description,
            next_date,
        )
        res = self.db.execute_query(q, params)
        return res.lastrowid if hasattr(res, "lastrowid") else None

    def get_active_subscriptions(self) -> List[Dict[str, Any]]:
        q = """SELECT * FROM recurring_invoices WHERE is_active = 1 AND (end_date IS NULL OR end_date >= DATE('now'))"""
        rows = self.db.fetch_all(q)
        return [dict(row) for row in rows]

    def _generate_invoice_number(self) -> str:
        """توليد رقم فاتورة فريد للفاتورة الدورية.

        Format: INV-YYYYMMDD-XXXX (sequential per day)
        Fallback: INV-UUID (collision-proof)
        """
        try:
            today_str = datetime.now().strftime("%Y%m%d")
            prefix = f"INV-{today_str}-"
            row = self.db.fetch_one(
                "SELECT invoice_number FROM sales WHERE invoice_number LIKE ? ORDER BY id DESC LIMIT 1",
                (f"{prefix}%",),
            )
            if row:
                last_num = row.get("invoice_number") if isinstance(row, dict) else row[0]
                try:
                    seq = int(last_num.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            return f"{prefix}{seq:04d}"
        except Exception:
            return f"INV-{uuid.uuid4().hex[:12].upper()}"

    def generate_due_invoices(self):
        """إنشاء الفواتير المستحقة اليوم تلقائياً"""
        subs = self.get_active_subscriptions()
        today = datetime.now().date()
        for sub in subs:
            next_date = datetime.strptime(sub["next_invoice_date"], "%Y-%m-%d").date()
            if next_date <= today:
                # إنشاء الفاتورة في جدول sales (الجدول الرئيسي للمبيعات)
                invoice_number = self._generate_invoice_number()
                q = """INSERT INTO sales (
                    invoice_number, customer_id, total_amount, discount_amount,
                    final_amount, payment_method, status, paid_amount,
                    remaining_amount, sale_date, notes, created_at, updated_at
                ) VALUES (?, ?, ?, 0, ?, 'نقدي', 'pending', 0, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""  # noqa: E501
                self.db.execute_query(
                    q,
                    (
                        invoice_number,
                        sub["customer_id"],
                        sub["amount"],
                        sub["amount"],
                        sub["amount"],
                        today,
                        sub["description"],
                    ),
                )
                # تحديث الاشتراك
                new_next = self._calc_next_date(next_date, sub["frequency"])
                uq = """UPDATE recurring_invoices SET last_invoice_date=?, next_invoice_date=?, updated_at=CURRENT_TIMESTAMP WHERE id=?"""  # noqa: E501
                self.db.execute_query(uq, (today, new_next, sub["id"]))
                if self.logger:
                    self.logger.info(
                        f'تم إنشاء فاتورة دورية {invoice_number} للعميل {sub["customer_id"]} بمبلغ {sub["amount"]} ليوم {today}'
                    )

    def _calc_next_date(self, last, freq: str) -> str:
        """حساب التاريخ التالي باستخدام relativedelta للحساب التقويمي الصحيح.

        - monthly: إضافة شهر واحد (يتعامل مع الأشهر المختلفة الأطوال)
        - yearly: إضافة سنة واحدة (يتعامل مع السنوات الكبيسة)
        - quarterly: إضافة 3 أشهر
        - weekly: إضافة 7 أيام
        """
        if freq == "monthly":
            next_date = last + relativedelta(months=+1)
        elif freq == "yearly":
            next_date = last + relativedelta(years=+1)
        elif freq == "quarterly":
            next_date = last + relativedelta(months=+3)
        elif freq == "weekly":
            next_date = last + timedelta(days=7)
        else:
            next_date = last + relativedelta(months=+1)
        return next_date.strftime("%Y-%m-%d")
