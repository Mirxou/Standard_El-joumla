#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التقارير والتحليلات المحسّنة
توليد تقارير مبيعات، مالية ومخزون قابلة للتصدير
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class ReportsService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def sales_report(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        try:
            q = "SELECT SUM(total_amount), COUNT(*) FROM sales WHERE status = 'confirmed'"
            params = []
            if start_date:
                q += ' AND created_at >= ?'
                params.append(start_date)
            if end_date:
                q += ' AND created_at <= ?'
                params.append(end_date)
            row = self.db.fetch_one(q, tuple(params))
            total = float(row[0] or 0)
            count = int(row[1] or 0)
            return {'total_revenue': total, 'orders_count': count}
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في تقرير المبيعات: {e}')
            return {}

    def inventory_report(self) -> Dict[str, Any]:
        try:
            q = 'SELECT SUM(current_stock * base_price) as value, SUM(current_stock) as qty FROM products WHERE is_active = 1'
            row = self.db.fetch_one(q)
            return {'inventory_value': float(row[0] or 0), 'total_items': int(row[1] or 0)}
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في تقرير المخزون: {e}')
            return {}

    def financial_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        try:
            q_sales = 'SELECT SUM(total_amount) FROM sales WHERE status = "confirmed"'
            params = []
            if start_date:
                q_sales += ' AND created_at >= ?'
                params.append(start_date)
            if end_date:
                q_sales += ' AND created_at <= ?'
                params.append(end_date)
            total_sales = float(self.db.fetch_one(q_sales, tuple(params))[0] or 0)

            q_purchases = 'SELECT SUM(total_amount) FROM purchases WHERE status = "received"'
            total_purchases = float(self.db.fetch_one(q_purchases)[0] or 0)

            q_profit = total_sales - total_purchases
            return {'total_sales': total_sales, 'total_purchases': total_purchases, 'net_profit': total_sales - total_purchases}
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في ملخص مالي: {e}')
            return {}
