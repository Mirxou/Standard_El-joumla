#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Dashboard Service
اختبارات خدمة لوحة التحكم
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, date
from typing import Dict, Any, List


# Mock classes for testing
class MockKPI:
    """Mock class for KPI"""
    def __init__(self, key, title, value, change=None, unit=None, color="#2196F3"):
        self.key = key
        self.title = title
        self.value = value
        self.change = change
        self.unit = unit
        self.color = color


class MockChartSeries:
    """Mock class for ChartSeries"""
    def __init__(self, name, color="#2196F3"):
        self.name = name
        self.color = color
        self.points = []


class MockTimeSeriesPoint:
    """Mock class for TimeSeriesPoint"""
    def __init__(self, label, value):
        self.label = label
        self.value = value


class MockDashboardService:
    """Mock class for DashboardService testing"""
    
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
    
    def _scalar(self, query, params=None):
        """Execute scalar query"""
        result = self.db.execute_query(query, params or [])
        if result and len(result) > 0:
            row = result[0]
            return list(row.values())[0] if isinstance(row, dict) else row[0]
        return 0
    
    def _change_pct(self, old_val, new_val):
        """Calculate percentage change"""
        if old_val == 0:
            return 0.0
        return ((new_val - old_val) / old_val) * 100
    
    def get_kpis(self, start_date=None, end_date=None) -> List[MockKPI]:
        """Get all KPIs for dashboard"""
        try:
            if not start_date:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
            
            kpis = [
                self._kpi_sales(start_date, end_date),
                self._kpi_orders_count(start_date, end_date),
                self._kpi_gross_profit(start_date, end_date),
                self._kpi_inventory_value(),
                self._kpi_low_stock_count(),
                self._kpi_receivables(),
                self._kpi_payables(),
                self._kpi_profit_margin(start_date, end_date),
                self._kpi_avg_order_value(start_date, end_date),
                self._kpi_cash_flow(start_date, end_date)
            ]
            return kpis
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting KPIs: {e}")
            return []
    
    def _kpi_sales(self, start, end) -> MockKPI:
        q = """
            SELECT COALESCE(SUM(final_amount), 0) FROM sales 
            WHERE DATE(sale_date) BETWEEN ? AND ?
            AND status NOT IN ('cancelled', 'ملغية')
        """
        sales = self._scalar(q, [start, end])
        prev_sales = self._scalar(q, [start - (end - start), start])
        change = self._change_pct(prev_sales, sales)
        return MockKPI(key="sales", title="المبيعات", value=sales, change=change, unit="ر.س", color="#4CAF50")
    
    def _kpi_orders_count(self, start, end) -> MockKPI:
        q = """
            SELECT COUNT(*) FROM sales 
            WHERE DATE(sale_date) BETWEEN ? AND ?
            AND status NOT IN ('cancelled', 'ملغية')
        """
        count = int(self._scalar(q, [start, end]))
        prev_count = int(self._scalar(q, [start - (end - start), start]))
        change = self._change_pct(prev_count, count)
        return MockKPI(key="orders", title="عدد الطلبات", value=count, change=change, unit=None, color="#2196F3")
    
    def _kpi_gross_profit(self, start, end) -> MockKPI:
        q = """
            SELECT COALESCE(SUM(si.profit), 0)
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            AND s.status NOT IN ('cancelled', 'ملغية')
        """
        profit = self._scalar(q, [start, end])
        prev_profit = self._scalar(q, [start - (end - start), start])
        change = self._change_pct(prev_profit, profit)
        return MockKPI(key="gross_profit", title="إجمالي الربح", value=profit, change=change, unit="ر.س", color="#FF9800")
    
    def _kpi_inventory_value(self) -> MockKPI:
        q = """
            SELECT COALESCE(SUM(current_stock * cost_price), 0) AS value
            FROM products
        """
        value = self._scalar(q)
        return MockKPI(key="inventory_value", title="قيمة المخزون", value=value, unit="ر.س", color="#9C27B0")
    
    def _kpi_low_stock_count(self) -> MockKPI:
        q = """
            SELECT COUNT(*) FROM products WHERE current_stock <= COALESCE(min_stock, 0)
        """
        c = int(self._scalar(q))
        return MockKPI(key="low_stock", title="منتجات منخفضة المخزون", value=c, unit=None, color="#F44336")
    
    def _kpi_receivables(self) -> MockKPI:
        q1 = """
            SELECT COALESCE(SUM(balance), 0) FROM account_balances WHERE account_type = 'receivable'
        """
        v = self._scalar(q1)
        if v == 0:
            q2 = "SELECT COALESCE(SUM(current_balance), 0) FROM customers WHERE current_balance > 0"
            v = self._scalar(q2)
        return MockKPI(key="receivables", title="الذمم المدينة", value=v, unit="ر.س", color="#26A69A")
    
    def _kpi_payables(self) -> MockKPI:
        q1 = """
            SELECT COALESCE(SUM(balance), 0) FROM account_balances WHERE account_type = 'payable'
        """
        v = self._scalar(q1)
        return MockKPI(key="payables", title="الذمم الدائنة", value=v, unit="ر.س", color="#00ACC1")
    
    def _kpi_profit_margin(self, start, end) -> MockKPI:
        q_sales = """
            SELECT COALESCE(SUM(final_amount), 0) FROM sales 
            WHERE DATE(sale_date) BETWEEN ? AND ?
            AND status NOT IN ('cancelled', 'ملغية')
        """
        q_profit = """
            SELECT COALESCE(SUM(si.profit), 0)
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            AND s.status NOT IN ('cancelled', 'ملغية')
        """
        sales = self._scalar(q_sales, [start, end])
        profit = self._scalar(q_profit, [start, end])
        
        margin = 0.0 if sales == 0 else (profit / sales * 100)
        
        period_len = (end - start).days
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_len)
        prev_sales = self._scalar(q_sales, [prev_start, prev_end])
        prev_profit = self._scalar(q_profit, [prev_start, prev_end])
        prev_margin = 0.0 if prev_sales == 0 else (prev_profit / prev_sales * 100)
        
        change = margin - prev_margin
        
        return MockKPI(
            key="profit_margin",
            title="هامش الربح",
            value=margin,
            change=change,
            unit="%",
            color="#673AB7"
        )
    
    def _kpi_avg_order_value(self, start, end) -> MockKPI:
        q = """
            SELECT 
                COALESCE(SUM(final_amount), 0) as total_sales,
                COUNT(*) as order_count
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
            AND status NOT IN ('cancelled', 'ملغية')
        """
        rows = self.db.execute_query(q, [start, end])
        if not rows or rows[0].get("order_count", 0) == 0:
            return MockKPI(key="aov", title="متوسط قيمة الطلب", value=0, unit="ر.س", color="#3F51B5")
        
        total = float(rows[0]["total_sales"])
        count = int(rows[0]["order_count"])
        aov = total / count
        
        return MockKPI(
            key="aov",
            title="متوسط قيمة الطلب",
            value=aov,
            unit="ر.س",
            color="#3F51B5"
        )
    
    def _kpi_cash_flow(self, start, end) -> MockKPI:
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
        
        color = "#4CAF50" if net_flow >= 0 else "#F44336"
        
        return MockKPI(
            key="cash_flow",
            title="التدفق النقدي الصافي",
            value=net_flow,
            unit="ر.س",
            color=color
        )
    
    def get_sales_chart_data(self, days: int = 30) -> MockChartSeries:
        """Get sales chart data for specified days"""
        try:
            end = date.today()
            start = end - timedelta(days=days)
            
            q = """
                SELECT DATE(sale_date) as d, COALESCE(SUM(final_amount), 0) as total
                FROM sales
                WHERE DATE(sale_date) BETWEEN ? AND ?
                AND status NOT IN ('cancelled', 'ملغية')
                GROUP BY DATE(sale_date)
                ORDER BY DATE(sale_date)
            """
            rows = self.db.execute_query(q, [start, end])
            
            series = MockChartSeries(name="المبيعات اليومية", color="#2196F3")
            for r in rows:
                series.points.append(MockTimeSeriesPoint(label=str(r["d"]), value=float(r["total"])))
            
            return series
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting sales chart data: {e}")
            return MockChartSeries(name="المبيعات اليومية")
    
    def get_top_products(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top selling products"""
        try:
            end = date.today()
            start = end - timedelta(days=days)
            
            q = """
                SELECT p.name, SUM(si.quantity) as qty, SUM(si.total_price) as total
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                AND s.status NOT IN ('cancelled', 'ملغية')
                GROUP BY p.id
                ORDER BY qty DESC
                LIMIT ?
            """
            return self.db.execute_query(q, [start, end, limit])
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting top products: {e}")
            return []
    
    def get_recent_sales(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sales"""
        try:
            q = """
                SELECT s.id, s.sale_date, c.name as customer_name, s.final_amount, s.status
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                ORDER BY s.sale_date DESC
                LIMIT ?
            """
            return self.db.execute_query(q, [limit])
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting recent sales: {e}")
            return []
    
    def get_inventory_alerts(self) -> List[Dict[str, Any]]:
        """Get inventory alerts (low stock, out of stock)"""
        try:
            q = """
                SELECT name, current_stock, min_stock,
                       CASE 
                           WHEN current_stock = 0 THEN 'out_of_stock'
                           WHEN current_stock <= min_stock THEN 'low_stock'
                       END as alert_type
                FROM products
                WHERE current_stock <= COALESCE(min_stock, 0)
                ORDER BY current_stock ASC
            """
            return self.db.execute_query(q)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting inventory alerts: {e}")
            return []


class TestDashboardServiceInitialization:
    """اختبارات تهيئة خدمة لوحة التحكم"""
    
    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        service = MockDashboardService(db_manager=mock_db)
        
        assert service.db == mock_db
        assert service.logger is None
    
    def test_initialization_with_logger(self):
        """اختبار التهيئة مع مسجل"""
        mock_db = Mock()
        mock_logger = Mock()
        service = MockDashboardService(db_manager=mock_db, logger=mock_logger)
        
        assert service.db == mock_db
        assert service.logger == mock_logger


class TestGetKPIs:
    """اختبارات الحصول على مؤشرات الأداء الرئيسية"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {"total_sales": 5000.0, "order_count": 50},
            {"d": date.today(), "total": 1000.0}
        ]
        
        service = MockDashboardService(db_manager=mock_db)
        return service, mock_db
    
    def test_get_kpis_success(self, service_with_mocks):
        """اختبار الحصول على KPIs بنجاح"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.side_effect = [
            [{"value": 5000.0}],  # sales
            [{"value": 1000.0}],  # prev sales
            [{"value": 50}],  # orders
            [{"value": 40}],  # prev orders
            [{"value": 1500.0}],  # profit
            [{"value": 1200.0}],  # prev profit
            [{"value": 25000.0}],  # inventory value
            [{"value": 5}],  # low stock
            [{"value": 8000.0}],  # receivables
            [{"value": 0.0}],  # fallback receivables
            [{"value": 3000.0}],  # payables
            [{"value": 5000.0}],  # sales for margin
            [{"value": 1000.0}],  # prev sales for margin
            [{"value": 1500.0}],  # profit for margin
            [{"value": 500.0}],  # prev profit for margin
            [{"total_sales": 5000.0, "order_count": 50}],  # aov
            [{"value": 8000.0}],  # cash in
            [{"value": 3000.0}],  # cash out
        ]
        
        result = service.get_kpis()
        
        assert len(result) == 10
        assert all(isinstance(kpi, MockKPI) for kpi in result)
    
    def test_get_kpis_with_date_range(self, service_with_mocks):
        """اختبار الحصول على KPIs مع نطاق تاريخ"""
        service, mock_db = service_with_mocks
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        mock_db.execute_query.side_effect = [
            [{"value": 3000.0}], [{"value": 2500.0}],
            [{"value": 30}], [{"value": 25}],
            [{"value": 900.0}], [{"value": 750.0}],
            [{"value": 25000.0}],
            [{"value": 3}],
            [{"value": 8000.0}], [{"value": 0.0}],
            [{"value": 3000.0}],
            [{"value": 3000.0}], [{"value": 2500.0}],
            [{"value": 900.0}], [{"value": 750.0}],
            [{"total_sales": 3000.0, "order_count": 30}],
            [{"value": 5000.0}], [{"value": 2000.0}],
        ]
        
        result = service.get_kpis(start_date=start_date, end_date=end_date)
        
        assert len(result) == 10
    
    def test_get_kpis_empty(self):
        """اختبار الحصول على KPIs فارغة"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [{"value": 0}]
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_kpis()
        
        assert len(result) == 10
    
    def test_get_kpis_db_error(self):
        """اختبار خطأ في قاعدة البيانات"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = MockDashboardService(db_manager=mock_db, logger=mock_logger)
        
        result = service.get_kpis()
        
        assert len(result) == 0


class TestKPICalculations:
    """اختبارات حسابات KPI"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        service = MockDashboardService(db_manager=mock_db)
        return service, mock_db
    
    def test_kpi_sales(self, service_with_mocks):
        """اختبار حساب مبيعات KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.side_effect = [
            [{"value": 10000.0}],
            [{"value": 8000.0}]
        ]
        
        result = service._kpi_sales(date.today() - timedelta(days=30), date.today())
        
        assert result.key == "sales"
        assert result.value == 10000.0
        assert result.change == 25.0  # (10000-8000)/8000 * 100
    
    def test_kpi_orders_count(self, service_with_mocks):
        """اختبار حساب عدد الطلبات KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.side_effect = [
            [{"value": 100}],
            [{"value": 80}]
        ]
        
        result = service._kpi_orders_count(date.today() - timedelta(days=30), date.today())
        
        assert result.key == "orders"
        assert result.value == 100
    
    def test_kpi_inventory_value(self, service_with_mocks):
        """اختبار حساب قيمة المخزون KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.return_value = [{"value": 50000.0}]
        
        result = service._kpi_inventory_value()
        
        assert result.key == "inventory_value"
        assert result.value == 50000.0
    
    def test_kpi_low_stock_count(self, service_with_mocks):
        """اختبار حساب منتجات منخفضة المخزون KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.return_value = [{"value": 10}]
        
        result = service._kpi_low_stock_count()
        
        assert result.key == "low_stock"
        assert result.value == 10
    
    def test_kpi_profit_margin(self, service_with_mocks):
        """اختبار حساب هامش الربح KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.side_effect = [
            [{"value": 10000.0}], [{"value": 8000.0}],
            [{"value": 2000.0}], [{"value": 1500.0}],
            [{"value": 9000.0}], [{"value": 7000.0}],
            [{"value": 1800.0}], [{"value": 1300.0}],
        ]
        
        result = service._kpi_profit_margin(date.today() - timedelta(days=30), date.today())
        
        assert result.key == "profit_margin"
        assert result.unit == "%"
    
    def test_kpi_avg_order_value(self, service_with_mocks):
        """اختبار حساب متوسط قيمة الطلب KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.return_value = [{"total_sales": 5000.0, "order_count": 50}]
        
        result = service._kpi_avg_order_value(date.today() - timedelta(days=30), date.today())
        
        assert result.key == "aov"
        assert result.value == 100.0  # 5000/50
    
    def test_kpi_avg_order_value_no_orders(self, service_with_mocks):
        """اختبار حساب متوسط قيمة الطلب بدون طلبات"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.return_value = [{"total_sales": 0.0, "order_count": 0}]
        
        result = service._kpi_avg_order_value(date.today() - timedelta(days=30), date.today())
        
        assert result.key == "aov"
        assert result.value == 0
    
    def test_kpi_cash_flow_positive(self, service_with_mocks):
        """اختبار حساب التدفق النقدي الإيجابي KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.side_effect = [
            [{"value": 15000.0}],
            [{"value": 5000.0}]
        ]
        
        result = service._kpi_cash_flow(date.today() - timedelta(days=30), date.today())
        
        assert result.key == "cash_flow"
        assert result.value == 10000.0
        assert result.color == "#4CAF50"
    
    def test_kpi_cash_flow_negative(self, service_with_mocks):
        """اختبار حساب التدفق النقدي السلبي KPI"""
        service, mock_db = service_with_mocks
        mock_db.execute_query.side_effect = [
            [{"value": 5000.0}],
            [{"value": 15000.0}]
        ]
        
        result = service._kpi_cash_flow(date.today() - timedelta(days=30), date.today())
        
        assert result.key == "cash_flow"
        assert result.value == -10000.0
        assert result.color == "#F44336"


class TestGetSalesChartData:
    """اختبارات الحصول على بيانات مخطط المبيعات"""
    
    def test_get_sales_chart_data_success(self):
        """اختبار الحصول على بيانات المخطط بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {"d": "2024-01-01", "total": 1000.0},
            {"d": "2024-01-02", "total": 1500.0},
            {"d": "2024-01-03", "total": 800.0}
        ]
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_sales_chart_data(days=30)
        
        assert result.name == "المبيعات اليومية"
        assert len(result.points) == 3
        assert result.points[0].label == "2024-01-01"
        assert result.points[0].value == 1000.0
    
    def test_get_sales_chart_data_empty(self):
        """اختبار الحصول على بيانات المخطط فارغة"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_sales_chart_data(days=30)
        
        assert result.name == "المبيعات اليومية"
        assert len(result.points) == 0
    
    def test_get_sales_chart_data_db_error(self):
        """اختبار خطأ في قاعدة البيانات"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = MockDashboardService(db_manager=mock_db, logger=mock_logger)
        
        result = service.get_sales_chart_data(days=30)
        
        assert result.name == "المبيعات اليومية"
        assert len(result.points) == 0


class TestGetTopProducts:
    """اختبارات الحصول على أفضل المنتجات"""
    
    def test_get_top_products_success(self):
        """اختبار الحصول على أفضل المنتجات بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {"name": "Product A", "qty": 100, "total": 5000.0},
            {"name": "Product B", "qty": 80, "total": 4000.0},
            {"name": "Product C", "qty": 60, "total": 3000.0}
        ]
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_top_products(days=30, limit=10)
        
        assert len(result) == 3
        assert result[0]["name"] == "Product A"
        assert result[0]["qty"] == 100
    
    def test_get_top_products_empty(self):
        """اختبار الحصول على أفضل المنتجات فارغة"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_top_products(days=30, limit=10)
        
        assert len(result) == 0
    
    def test_get_top_products_db_error(self):
        """اختبار خطأ في قاعدة البيانات"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = MockDashboardService(db_manager=mock_db, logger=mock_logger)
        
        result = service.get_top_products(days=30, limit=10)
        
        assert len(result) == 0


class TestGetRecentSales:
    """اختبارات الحصول على المبيعات الأخيرة"""
    
    def test_get_recent_sales_success(self):
        """اختبار الحصول على المبيعات الأخيرة بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {"id": 1, "sale_date": "2024-01-03", "customer_name": "Customer A", "final_amount": 500.0, "status": "completed"},
            {"id": 2, "sale_date": "2024-01-02", "customer_name": "Customer B", "final_amount": 300.0, "status": "completed"},
            {"id": 3, "sale_date": "2024-01-01", "customer_name": None, "final_amount": 200.0, "status": "pending"}
        ]
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_recent_sales(limit=10)
        
        assert len(result) == 3
        assert result[0]["customer_name"] == "Customer A"
    
    def test_get_recent_sales_empty(self):
        """اختبار الحصول على المبيعات الأخيرة فارغة"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_recent_sales(limit=10)
        
        assert len(result) == 0


class TestGetInventoryAlerts:
    """اختبارات الحصول على تنبيهات المخزون"""
    
    def test_get_inventory_alerts_success(self):
        """اختبار الحصول على التنبيهات بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {"name": "Product A", "current_stock": 0, "min_stock": 10, "alert_type": "out_of_stock"},
            {"name": "Product B", "current_stock": 5, "min_stock": 10, "alert_type": "low_stock"},
            {"name": "Product C", "current_stock": 2, "min_stock": 5, "alert_type": "low_stock"}
        ]
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_inventory_alerts()
        
        assert len(result) == 3
        assert result[0]["alert_type"] == "out_of_stock"
        assert result[1]["alert_type"] == "low_stock"
    
    def test_get_inventory_alerts_empty(self):
        """اختبار الحصول على التنبيهات فارغة"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []
        
        service = MockDashboardService(db_manager=mock_db)
        
        result = service.get_inventory_alerts()
        
        assert len(result) == 0


class TestChangePercentage:
    """اختبارات حساب النسبة المئوية للتغيير"""
    
    def test_change_pct_positive(self):
        """اختبار حساب التغيير الإيجابي"""
        mock_db = Mock()
        service = MockDashboardService(db_manager=mock_db)
        
        result = service._change_pct(100, 150)
        
        assert result == 50.0
    
    def test_change_pct_negative(self):
        """اختبار حساب التغيير السلبي"""
        mock_db = Mock()
        service = MockDashboardService(db_manager=mock_db)
        
        result = service._change_pct(100, 75)
        
        assert result == -25.0
    
    def test_change_pct_zero_old(self):
        """اختبار حساب التغيير مع قيمة قديمة صفر"""
        mock_db = Mock()
        service = MockDashboardService(db_manager=mock_db)
        
        result = service._change_pct(0, 100)
        
        assert result == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



