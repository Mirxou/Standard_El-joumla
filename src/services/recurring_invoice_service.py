#!/usr/bin/env python3
"""
خدمة الفوترة الدورية (Recurring Invoice Service)
تدعم إنشاء فواتير متكررة تلقائياً للعملاء حسب جدول زمني محدد (شهري/سنوي)
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class RecurringInvoiceService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self._init_table()

    def _init_table(self):
        q = '''
        CREATE TABLE IF NOT EXISTS recurring_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            frequency TEXT NOT NULL, -- 'monthly', 'yearly', 'weekly'
            amount REAL NOT NULL,
            description TEXT,
            last_invoice_date DATE,
            next_invoice_date DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.db.execute_query(q)

    def create_subscription(self, customer_id: int, amount: float, frequency: str, start_date: Optional[str]=None, end_date: Optional[str]=None, description: Optional[str]=None) -> int:
        start = start_date or datetime.now().strftime('%Y-%m-%d')
        q = '''
        INSERT INTO recurring_invoices (customer_id, start_date, end_date, frequency, amount, description, next_invoice_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        next_date = start
        params = (customer_id, start, end_date, frequency, amount, description, next_date)
        res = self.db.execute_query(q, params)
        return res.lastrowid if hasattr(res, 'lastrowid') else None

    def get_active_subscriptions(self) -> List[Dict[str, Any]]:
        q = '''SELECT * FROM recurring_invoices WHERE is_active = 1 AND (end_date IS NULL OR end_date >= DATE('now'))'''
        rows = self.db.fetch_all(q)
        return [dict(row) for row in rows]

    def generate_due_invoices(self):
        """إنشاء الفواتير المستحقة اليوم تلقائياً"""
        subs = self.get_active_subscriptions()
        today = datetime.now().date()
        for sub in subs:
            next_date = datetime.strptime(sub['next_invoice_date'], '%Y-%m-%d').date()
            if next_date <= today:
                # إنشاء الفاتورة (جدول invoices)
                q = '''INSERT INTO invoices (customer_id, amount, invoice_date, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)'''
                self.db.execute_query(q, (sub['customer_id'], sub['amount'], today, sub['description'], 'pending'))
                # تحديث الاشتراك
                new_next = self._calc_next_date(next_date, sub['frequency'])
                uq = '''UPDATE recurring_invoices SET last_invoice_date=?, next_invoice_date=?, updated_at=CURRENT_TIMESTAMP WHERE id=?'''
                self.db.execute_query(uq, (today, new_next, sub['id']))
                if self.logger:
                    self.logger.info(f'تم إنشاء فاتورة دورية للعميل {sub["customer_id"]} بمبلغ {sub["amount"]} ليوم {today}')

    def _calc_next_date(self, last: datetime, freq: str) -> str:
        if freq == 'monthly':
            next_date = last + timedelta(days=30)
        elif freq == 'yearly':
            next_date = last + timedelta(days=365)
        elif freq == 'weekly':
            next_date = last + timedelta(days=7)
        else:
            next_date = last + timedelta(days=30)
        return next_date.strftime('%Y-%m-%d')
