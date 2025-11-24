#!/usr/bin/env python3
"""
خدمة أتمتة التسويق (Marketing Automation Service)
تدعم جدولة الحملات وتتابع الرسائل (Drip Campaigns)
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class MarketingAutomationService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self._init_table()

    def _init_table(self):
        q = '''
        CREATE TABLE IF NOT EXISTS automated_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            sequence_step INTEGER NOT NULL,
            subject TEXT,
            content TEXT,
            scheduled_date DATE NOT NULL,
            sent BOOLEAN DEFAULT 0,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.db.execute_query(q)

    def schedule_drip_sequence(self, campaign_name: str, customer_id: int, steps: List[Dict[str, Any]], start_date: Optional[str]=None):
        """
        steps: List of dicts: [{"subject":..., "content":..., "delay_days":...}, ...]
        """
        base_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.now()
        for idx, step in enumerate(steps):
            scheduled = base_date + timedelta(days=sum(s['delay_days'] for s in steps[:idx+1]))
            q = '''INSERT INTO automated_campaigns (campaign_name, customer_id, sequence_step, subject, content, scheduled_date) VALUES (?, ?, ?, ?, ?, ?)'''
            self.db.execute_query(q, (campaign_name, customer_id, idx+1, step['subject'], step['content'], scheduled.strftime('%Y-%m-%d')))

    def send_due_campaigns(self):
        """إرسال الرسائل المجدولة المستحقة اليوم"""
        today = datetime.now().strftime('%Y-%m-%d')
        q = '''SELECT * FROM automated_campaigns WHERE sent=0 AND scheduled_date <= ?'''
        rows = self.db.fetch_all(q, (today,))
        for row in rows:
            # هنا مكان التكامل مع خدمة البريد الإلكتروني الفعلية
            # send_email(row['customer_id'], row['subject'], row['content'])
            uq = '''UPDATE automated_campaigns SET sent=1, sent_at=CURRENT_TIMESTAMP WHERE id=?'''
            self.db.execute_query(uq, (row['id'],))
            if self.logger:
                self.logger.info(f'تم إرسال رسالة حملة {row["campaign_name"]} للعميل {row["customer_id"]} (الخطوة {row["sequence_step"]})')
