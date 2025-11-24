#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Assistant Service (v5.3.0)
مساعد ذكي للإجابة على الأسئلة الشائعة حول النظام
"""
from typing import Optional, Dict, Any
from datetime import datetime
import re

class SmartAssistant:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def answer(self, query: str) -> str:
        q = query.strip().lower()
        # الأسئلة المدعومة
        if re.search(r'(مبيعات اليوم|today.*sales|كم مبيعات اليوم)', q):
            return self._get_today_sales()
        if re.search(r'(منخفض[ة] المخزون|low stock|products.*low)', q):
            return self._get_low_stock_products()
        if re.search(r'(أكثر المنتجات مبيعاً|top.*products|best sellers)', q):
            return self._get_top_selling_products()
        if re.search(r'(رصيد|balance|حساب)', q):
            return self._get_balance_summary()
        return "عذراً، لم أفهم سؤالك. جرب سؤالاً مثل: كم مبيعات اليوم؟ أو ما هي المنتجات منخفضة المخزون؟"

    def _get_today_sales(self) -> str:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            row = self.db.fetch_one('SELECT COALESCE(SUM(total_amount),0) FROM sales WHERE DATE(created_at)=?', (today,))
            total = float(row[0] or 0)
            return f"إجمالي مبيعات اليوم: {total:.2f}"
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في جلب مبيعات اليوم: {e}')
            return "تعذر جلب مبيعات اليوم."

    def _get_low_stock_products(self) -> str:
        try:
            rows = self.db.fetch_all('SELECT name, current_stock, min_stock FROM products WHERE current_stock <= min_stock ORDER BY current_stock ASC LIMIT 5')
            if not rows:
                return "لا توجد منتجات منخفضة المخزون حالياً."
            msg = "المنتجات منخفضة المخزون:\n"
            for r in rows:
                msg += f"- {r[0]} (المخزون: {r[1]}, الحد الأدنى: {r[2]})\n"
            return msg.strip()
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في جلب المنتجات منخفضة المخزون: {e}')
            return "تعذر جلب المنتجات منخفضة المخزون."

    def _get_top_selling_products(self) -> str:
        try:
            rows = self.db.fetch_all('''SELECT p.name, SUM(si.quantity) as qty FROM sale_items si JOIN products p ON si.product_id=p.id GROUP BY si.product_id ORDER BY qty DESC LIMIT 5''')
            if not rows:
                return "لا توجد بيانات مبيعات كافية."
            msg = "أكثر المنتجات مبيعاً:\n"
            for r in rows:
                msg += f"- {r[0]} (الكمية: {r[1]})\n"
            return msg.strip()
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في جلب المنتجات الأكثر مبيعاً: {e}')
            return "تعذر جلب المنتجات الأكثر مبيعاً."

    def _get_balance_summary(self) -> str:
        try:
            row = self.db.fetch_one('SELECT COALESCE(SUM(current_balance),0) FROM customers')
            total = float(row[0] or 0)
            return f"إجمالي أرصدة العملاء: {total:.2f}"
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في جلب الأرصدة: {e}')
            return "تعذر جلب الأرصدة."
