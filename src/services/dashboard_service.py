"""
خدمة لوحات المعلومات (Dashboard)
تحسب مؤشرات الأداء (KPIs) وتجهز بيانات الرسوم البيانية.
"""
from __future__ import annotations
from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal

from ..core.database_manager import DatabaseManager
from ..models.dashboard import KPI, DashboardData, ChartSeries, TimeSeriesPoint


class DashboardService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    # ============================ Public API ============================
    def load_dashboard(self, start: date, end: date) -> DashboardData:
        data = DashboardData(period_start=start, period_end=end)

        # KPIs
        data.kpis = [
            self._kpi_total_sales(start, end),
            self._kpi_today_sales(end),
            self._kpi_month_sales(end),
            self._kpi_gross_profit(start, end),
            self._kpi_inventory_value(),
            self._kpi_low_stock_count(),
            self._kpi_receivables(),
            self._kpi_payables(),
        ]

        # Time series: sales per day
        data.sales_series = [self._series_sales_per_day(start, end)]

        # Top products
        data.top_products = self._top_products(start, end, 10)

        # Activity
        data.active_customers = self._active_customers(start, end)
        data.active_suppliers = self._active_suppliers(start, end)

        # Default distribution: by payment method
        data.distribution = self.get_distribution_by_payment_method(start, end)

        return data

    # ============================ KPIs ============================
    def _kpi_total_sales(self, start: date, end: date) -> KPI:
        q = """
            SELECT COALESCE(SUM(final_amount), 0) AS total
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
        """
        total = self._scalar(q, [start, end])
        prev_total = self._scalar(q, [start - (end - start), start])
        change = self._change_pct(prev_total, total)
        return KPI(key="total_sales", title="إجمالي المبيعات", value=total, change=change, unit="ر.س", color="#4CAF50")

    def _kpi_today_sales(self, today: date) -> KPI:
        q = """
            SELECT COALESCE(SUM(final_amount), 0) AS total
            FROM sales
            WHERE DATE(sale_date) = ?
        """
        total = self._scalar(q, [today])
        y = today - timedelta(days=1)
        prev = self._scalar(q, [y])
        change = self._change_pct(prev, total)
        return KPI(key="today_sales", title="مبيعات اليوم", value=total, change=change, unit="ر.س", color="#2196F3")

    def _kpi_month_sales(self, today: date) -> KPI:
        start = today.replace(day=1)
        q = """
            SELECT COALESCE(SUM(final_amount), 0) AS total
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
        """
        total = self._scalar(q, [start, today])
        prev_start = (start - timedelta(days=1)).replace(day=1)
        prev_end = start - timedelta(days=1)
        prev = self._scalar(q, [prev_start, prev_end])
        change = self._change_pct(prev, total)
        return KPI(key="month_sales", title="مبيعات هذا الشهر", value=total, change=change, unit="ر.س", color="#1976D2")

    def _kpi_gross_profit(self, start: date, end: date) -> KPI:
        q = """
            SELECT COALESCE(SUM(si.profit), 0) AS profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
        """
        profit = self._scalar(q, [start, end])
        prev_profit = self._scalar(q, [start - (end - start), start])
        change = self._change_pct(prev_profit, profit)
        return KPI(key="gross_profit", title="إجمالي الربح", value=profit, change=change, unit="ر.س", color="#FF9800")

    def _kpi_inventory_value(self) -> KPI:
        q = """
            SELECT COALESCE(SUM(current_stock * cost_price), 0) AS value
            FROM products
        """
        value = self._scalar(q)
        return KPI(key="inventory_value", title="قيمة المخزون", value=value, unit="ر.س", color="#9C27B0")

    def _kpi_low_stock_count(self) -> KPI:
        q = """
            SELECT COUNT(*) FROM products WHERE current_stock <= COALESCE(min_stock, 0)
        """
        c = self._scalar(q)
        return KPI(key="low_stock", title="منتجات منخفضة المخزون", value=int(c), unit=None, color="#F44336")

    def _kpi_receivables(self) -> KPI:
        # Prefer account_balances table if populated; fallback to customers.current_balance
        q1 = """
            SELECT COALESCE(SUM(balance), 0) FROM account_balances WHERE account_type = 'receivable'
        """
        v = self._scalar(q1)
        if v == 0:
            q2 = "SELECT COALESCE(SUM(current_balance), 0) FROM customers WHERE current_balance > 0"
            v = self._scalar(q2)
        return KPI(key="receivables", title="الذمم المدينة", value=v, unit="ر.س", color="#26A69A")

    def _kpi_payables(self) -> KPI:
        q1 = """
            SELECT COALESCE(SUM(balance), 0) FROM account_balances WHERE account_type = 'payable'
        """
        v = self._scalar(q1)
        return KPI(key="payables", title="الذمم الدائنة", value=v, unit="ر.س", color="#00ACC1")

    # ============================ Series & Lists ============================
    def _series_sales_per_day(self, start: date, end: date) -> ChartSeries:
        q = """
            SELECT DATE(sale_date) as d, COALESCE(SUM(final_amount), 0) as total
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
            GROUP BY DATE(sale_date)
            ORDER BY DATE(sale_date)
        """
        rows = self.db.execute_query(q, [start, end])
        series = ChartSeries(name="المبيعات اليومية", color="#2196F3")
        for r in rows:
            series.points.append(TimeSeriesPoint(label=str(r["d"]), value=float(r["total"])) )
        return series

    def _top_products(self, start: date, end: date, limit: int = 10, category_id: int | None = None) -> List[Dict[str, Any]]:
        base = """
            SELECT p.name, SUM(si.quantity) as qty, SUM(si.total_price) as total
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
        """
        params: List[Any] = [start, end]
        if category_id:
            base += " AND p.category_id = ?"
            params.append(category_id)
        base += " GROUP BY p.id ORDER BY total DESC LIMIT ?"
        params.append(limit)
        return self.db.execute_query(base, params)

    def list_categories(self) -> List[Dict[str, Any]]:
        return self.db.execute_query("SELECT id, name FROM categories ORDER BY name")

    # ============================ Helpers ============================
    def _scalar(self, query: str, params: List[Any] | None = None) -> float:
        rows = self.db.execute_query(query, params or [])
        if not rows:
            return 0.0
        value = list(rows[0].values())[0]
        return float(value or 0)

    def _change_pct(self, prev: float, curr: float) -> float:
        if prev == 0:
            return 0.0 if curr == 0 else 100.0
        return float((Decimal(str(curr)) - Decimal(str(prev))) * 100 / Decimal(str(prev)))

    # ============================ Additional Metrics ============================
    def _active_customers(self, start: date, end: date) -> int:
        q = """
            SELECT COUNT(DISTINCT customer_id) AS cnt
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
        """
        return int(self._scalar(q, [start, end]))

    def _active_suppliers(self, start: date, end: date) -> int:
        q = """
            SELECT COUNT(DISTINCT supplier_id) AS cnt
            FROM purchases
            WHERE DATE(purchase_date) BETWEEN ? AND ?
        """
        return int(self._scalar(q, [start, end]))

    # ============================ Distributions ============================
    def get_distribution_by_payment_method(self, start: date, end: date) -> List[Dict[str, Any]]:
        q = """
            SELECT COALESCE(payment_method, 'غير محدد') AS label,
                   COALESCE(SUM(final_amount), 0) AS value
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
            GROUP BY payment_method
            ORDER BY value DESC
        """
        return self.db.execute_query(q, [start, end])

    def get_distribution_by_category(self, start: date, end: date) -> List[Dict[str, Any]]:
        q = """
            SELECT COALESCE(c.name, 'غير مصنف') AS label,
                   COALESCE(SUM(si.total_price), 0) AS value
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            LEFT JOIN products p ON si.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY value DESC
        """
        return self.db.execute_query(q, [start, end])
