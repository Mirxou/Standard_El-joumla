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

        # KPIs - Enhanced with new metrics
        data.kpis = [
            self._kpi_total_sales(start, end),
            self._kpi_today_sales(end),
            self._kpi_month_sales(end),
            self._kpi_gross_profit(start, end),
            self._kpi_profit_margin(start, end),            # NEW
            self._kpi_avg_order_value(start, end),          # NEW
            self._kpi_inventory_value(),
            self._kpi_inventory_turnover(start, end),       # NEW
            self._kpi_low_stock_count(),
            self._kpi_receivables(),
            self._kpi_payables(),
            self._kpi_cash_flow(start, end),                # NEW
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

    def _kpi_profit_margin(self, start: date, end: date) -> KPI:
        """هامش الربح (Profit Margin %) = (الربح / المبيعات) × 100"""
        q_sales = """
            SELECT COALESCE(SUM(final_amount), 0) FROM sales WHERE DATE(sale_date) BETWEEN ? AND ?
        """
        q_profit = """
            SELECT COALESCE(SUM(si.profit), 0)
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
        """
        sales = self._scalar(q_sales, [start, end])
        profit = self._scalar(q_profit, [start, end])
        
        margin = 0.0 if sales == 0 else (profit / sales * 100)
        
        # Previous period margin
        period_len = (end - start).days
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_len)
        prev_sales = self._scalar(q_sales, [prev_start, prev_end])
        prev_profit = self._scalar(q_profit, [prev_start, prev_end])
        prev_margin = 0.0 if prev_sales == 0 else (prev_profit / prev_sales * 100)
        
        change = margin - prev_margin
        
        return KPI(
            key="profit_margin",
            title="هامش الربح",
            value=margin,
            change=change,
            unit="%",
            color="#673AB7"
        )

    def _kpi_avg_order_value(self, start: date, end: date) -> KPI:
        """متوسط قيمة الطلب (AOV - Average Order Value)"""
        q = """
            SELECT 
                COALESCE(SUM(final_amount), 0) as total_sales,
                COUNT(*) as order_count
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
        """
        rows = self.db.execute_query(q, [start, end])
        if not rows or rows[0]["order_count"] == 0:
            return KPI(key="aov", title="متوسط قيمة الطلب", value=0, unit="ر.س", color="#3F51B5")
        
        total = float(rows[0]["total_sales"])
        count = int(rows[0]["order_count"])
        aov = total / count
        
        # Previous period AOV
        period_len = (end - start).days
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_len)
        prev_rows = self.db.execute_query(q, [prev_start, prev_end])
        prev_aov = 0.0
        if prev_rows and prev_rows[0]["order_count"] > 0:
            prev_aov = float(prev_rows[0]["total_sales"]) / int(prev_rows[0]["order_count"])
        
        change = self._change_pct(prev_aov, aov)
        
        return KPI(
            key="aov",
            title="متوسط قيمة الطلب",
            value=aov,
            change=change,
            unit="ر.س",
            color="#3F51B5"
        )

    def _kpi_inventory_turnover(self, start: date, end: date) -> KPI:
        """معدل دوران المخزون (Inventory Turnover) = تكلفة البضاعة المباعة / متوسط المخزون"""
        # Cost of Goods Sold (COGS) during period
        q_cogs = """
            SELECT COALESCE(SUM(si.quantity * si.unit_price - si.profit), 0) as cogs
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
        """
        cogs = self._scalar(q_cogs, [start, end])
        
        # Average inventory value
        q_inv = """
            SELECT COALESCE(SUM(current_stock * cost_price), 0) as value FROM products
        """
        avg_inventory = self._scalar(q_inv)
        
        turnover = 0.0 if avg_inventory == 0 else (cogs / avg_inventory)
        
        return KPI(
            key="inventory_turnover",
            title="معدل دوران المخزون",
            value=turnover,
            unit="مرة",
            color="#8E24AA"
        )

    def _kpi_cash_flow(self, start: date, end: date) -> KPI:
        """التدفق النقدي = (المقبوضات - المدفوعات)"""
        q_in = """
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE DATE(payment_date) BETWEEN ? AND ? AND payment_type = 'received'
        """
        q_out = """
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE DATE(payment_date) BETWEEN ? AND ? AND payment_type = 'paid'
        """
        cash_in = self._scalar(q_in, [start, end])
        cash_out = self._scalar(q_out, [start, end])
        net_flow = cash_in - cash_out
        
        # Previous period
        period_len = (end - start).days
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_len)
        prev_in = self._scalar(q_in, [prev_start, prev_end])
        prev_out = self._scalar(q_out, [prev_start, prev_end])
        prev_flow = prev_in - prev_out
        
        change = self._change_pct(prev_flow, net_flow)
        
        color = "#4CAF50" if net_flow >= 0 else "#F44336"
        
        return KPI(
            key="cash_flow",
            title="التدفق النقدي الصافي",
            value=net_flow,
            change=change,
            unit="ر.س",
            color=color
        )

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
        """تنفيذ استعلام وإرجاع قيمة واحدة كـ float"""
        try:
            rows = self.db.execute_query(query, params or [])
            if not rows:
                return 0.0
            value = list(rows[0].values())[0]
            if value is None:
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _change_pct(self, prev: float, curr: float) -> float:
        """حساب نسبة التغيير بين قيمتين"""
        # Handle None values
        if prev is None:
            prev = 0.0
        if curr is None:
            curr = 0.0
        
        # Convert to float if needed
        prev = float(prev) if not isinstance(prev, float) else prev
        curr = float(curr) if not isinstance(curr, float) else curr
        
        if prev == 0:
            return 0.0 if curr == 0 else 100.0
        
        try:
            return ((curr - prev) * 100 / prev)
        except (ValueError, ZeroDivisionError, TypeError):
            return 0.0

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

    # ============================ New Advanced Analytics ============================
    def get_revenue_vs_expenses(self, start: date, end: date) -> Dict[str, List[Dict[str, Any]]]:
        """مقارنة الإيرادات والمصروفات يومياً"""
        q_revenue = """
            SELECT DATE(sale_date) as day, COALESCE(SUM(final_amount), 0) as amount
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
            GROUP BY DATE(sale_date)
            ORDER BY DATE(sale_date)
        """
        q_expenses = """
            SELECT DATE(purchase_date) as day, COALESCE(SUM(total_amount), 0) as amount
            FROM purchases
            WHERE DATE(purchase_date) BETWEEN ? AND ?
            GROUP BY DATE(purchase_date)
            ORDER BY DATE(purchase_date)
        """
        return {
            "revenue": self.db.execute_query(q_revenue, [start, end]),
            "expenses": self.db.execute_query(q_expenses, [start, end])
        }

    def get_inventory_status_distribution(self) -> List[Dict[str, Any]]:
        """توزيع حالة المخزون: منخفض / عادي / عالي"""
        q = """
            SELECT 
                CASE 
                    WHEN current_stock = 0 THEN 'نفذ من المخزون'
                    WHEN current_stock <= COALESCE(min_stock, 0) THEN 'منخفض'
                    WHEN current_stock >= COALESCE(max_stock, current_stock * 2) THEN 'مرتفع'
                    ELSE 'عادي'
                END as status,
                COUNT(*) as count,
                SUM(current_stock * cost_price) as value
            FROM products
            GROUP BY status
        """
        return self.db.execute_query(q)

    def get_profit_trend(self, start: date, end: date) -> List[Dict[str, Any]]:
        """اتجاه الربحية اليومي"""
        q = """
            SELECT 
                DATE(s.sale_date) as day,
                COALESCE(SUM(si.profit), 0) as profit,
                COALESCE(SUM(si.total_price), 0) as sales,
                CASE 
                    WHEN SUM(si.total_price) > 0 
                    THEN (SUM(si.profit) * 100.0 / SUM(si.total_price))
                    ELSE 0
                END as margin
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY DATE(s.sale_date)
            ORDER BY DATE(s.sale_date)
        """
        return self.db.execute_query(q, [start, end])

    def get_customer_insights(self, start: date, end: date) -> Dict[str, Any]:
        """رؤى العملاء: جديد vs متكرر، متوسط القيمة"""
        q_total = """
            SELECT COUNT(DISTINCT customer_id) as total_customers
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
        """
        q_repeat = """
            SELECT COUNT(*) as repeat_customers
            FROM (
                SELECT customer_id
                FROM sales
                WHERE DATE(sale_date) BETWEEN ? AND ?
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            )
        """
        q_avg_value = """
            SELECT 
                AVG(customer_total) as avg_customer_value
            FROM (
                SELECT customer_id, SUM(final_amount) as customer_total
                FROM sales
                WHERE DATE(sale_date) BETWEEN ? AND ?
                GROUP BY customer_id
            )
        """
        
        total_rows = self.db.execute_query(q_total, [start, end])
        repeat_rows = self.db.execute_query(q_repeat, [start, end])
        avg_rows = self.db.execute_query(q_avg_value, [start, end])
        
        total = int(total_rows[0]["total_customers"]) if total_rows else 0
        repeat = int(repeat_rows[0]["repeat_customers"]) if repeat_rows else 0
        new = total - repeat
        avg_val = float(avg_rows[0]["avg_customer_value"] or 0) if avg_rows else 0.0
        
        return {
            "total_customers": total,
            "new_customers": new,
            "repeat_customers": repeat,
            "repeat_rate": (repeat / total * 100) if total > 0 else 0.0,
            "avg_customer_value": avg_val
        }

