import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج التقارير - Reports Model
يحتوي على منطق تجميع البيانات للتقارير المالية والمخزون
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional


class ReportManager:
    """مدير التقارير والإحصائيات"""

    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    def get_financial_summary(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        الحصول على ملخص مالي (المبيعات، التكلفة، الأرباح)
        """
        try:
            # افتراضي: آخر 30 يوم
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            # 1. إجمالي المبيعات (المدفوعة والجزئية والمؤكدة)
            sales_query = """
            SELECT SUM(total_amount) as total_sales, SUM(paid_amount) as collected_cash
            FROM sales
            WHERE date(sale_date) BETWEEN date(?) AND date(?)
            AND status IN ('CONFIRMED', 'PAID', 'PARTIALLY_PAID', 'مؤكدة', 'مدفوعة', 'مدفوعة جزئياً')
            """
            sales_result = self.db_manager.fetch_one(sales_query, (start_date, end_date))
            if sales_result:
                if isinstance(sales_result, dict):
                    total_sales = float(sales_result.get("total_sales") or 0)
                    collected_cash = float(sales_result.get("collected_cash") or 0)
                elif sales_result:
                    total_sales = float(sales_result[0] or 0)
                    collected_cash = float(sales_result[1] or 0)
            else:
                total_sales = 0.0
                collected_cash = 0.0

            # 2. تكلفة البضاعة المباعة (COGS)
            # نحتاج لحساب تكلفة العناصر في الفواتير المؤكدة
            cogs_query = """
            SELECT SUM(si.quantity * p.cost_price) as total_cogs
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE date(s.sale_date) BETWEEN date(?) AND date(?)
            AND s.status IN ('CONFIRMED', 'PAID', 'PARTIALLY_PAID', 'مؤكدة', 'مدفوعة', 'مدفوعة جزئياً')
            """
            cogs_result = self.db_manager.fetch_one(cogs_query, (start_date, end_date))
            if cogs_result:
                if isinstance(cogs_result, dict):
                    total_cost = float(cogs_result.get("total_cogs") or 0)
                elif cogs_result:
                    total_cost = float(cogs_result[0] or 0)
            else:
                total_cost = 0.0

            # 3. صافي الربح
            net_profit = total_sales - total_cost

            # 4. هامش الربح
            profit_margin = 0
            if total_sales > 0:
                profit_margin = round((net_profit / total_sales) * 100, 2)

            return {
                "total_sales": total_sales,
                "total_cost": total_cost,
                "net_profit": net_profit,
                "profit_margin": profit_margin,
                "collected_cash": collected_cash,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting financial summary: {e}")
            return {}

    def get_sales_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        الحصول على اتجاهات المبيعات اليومية
        """
        try:
            start_date = date.today() - timedelta(days=days)

            query = """
            SELECT date(sale_date) as day,
                   SUM(total_amount) as daily_sales,
                   COUNT(id) as orders_count
            FROM sales
            WHERE date(sale_date) >= date(?)
            AND status IN ('CONFIRMED', 'PAID', 'PARTIALLY_PAID', 'مؤكدة', 'مدفوعة', 'مدفوعة جزئياً')
            GROUP BY date(sale_date)
            ORDER BY day ASC
            """

            results = self.db_manager.fetch_all(query, (start_date,))
            return [dict(row) if isinstance(row, dict) else row for row in results]
        except Exception as e:
            self.logger.error(f"Error getting sales trends: {e}")
            return []

    def get_top_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        أكثر المنتجات مبيعاً وربحية
        """
        try:
            query = """
            SELECT p.name,
                   SUM(si.quantity) as units_sold,
                   SUM(si.quantity * si.unit_price) as revenue,
                   (SUM(si.quantity * si.unit_price) - SUM(si.quantity * p.cost_price)) as profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE s.status IN ('CONFIRMED', 'PAID', 'PARTIALLY_PAID', 'مؤكدة', 'مدفوعة', 'مدفوعة جزئياً')
            GROUP BY p.id
            ORDER BY profit DESC
            LIMIT ?
            """
            results = self.db_manager.fetch_all(query, (limit,))
            return [dict(row) if isinstance(row, dict) else row for row in results]
        except Exception as e:
            self.logger.error(f"Error getting top products: {e}")
            return []

    def get_inventory_analytics(self) -> Dict[str, Any]:
        """
        تحليلات المخزون
        """
        try:
            # 1. إجمالي قيمة المخزون (سعر التكلفة وسعر البيع)
            value_query = """
            SELECT
                SUM(current_stock * cost_price) as total_cost_value,
                SUM(current_stock * selling_price) as total_sales_value,
                COUNT(*) as total_products,
                SUM(current_stock) as total_items
            FROM products
            WHERE is_active = 1
            """
            value_result = self.db_manager.fetch_one(value_query)

            # 2. المنتجات منخفضة المخزون
            low_stock_query = """
            SELECT COUNT(*) as count
            FROM products
            WHERE current_stock <= min_stock AND is_active = 1
            """
            low_stock_result = self.db_manager.fetch_one(low_stock_query)

            def _safe_float(result, key, idx=0, default=0.0):
                """Get float from dict or tuple result safely"""
                if result is None:
                    return default
                if isinstance(result, dict):
                    val = result.get(key)
                    return float(val) if val is not None else default
                elif isinstance(result, (tuple, list)) and len(result) > idx:
                    val = result[idx]
                    return float(val) if val is not None else default
                return default

            return {
                "total_cost_value": _safe_float(value_result, "total_cost_value"),
                "total_sales_value": _safe_float(value_result, "total_sales_value", 1),
                "potential_profit": (
                    _safe_float(value_result, "total_sales_value", 0)
                    - _safe_float(value_result, "total_cost_value", 0)
                ),
                "total_products": int(_safe_float(value_result, "total_products", 2)),
                "total_items": int(_safe_float(value_result, "total_items", 3)),
                "low_stock_count": int(_safe_float(low_stock_result, "count", 0)),
            }
        except Exception as e:
            self.logger.error(f"Error getting inventory analytics: {e}")
            return {}
