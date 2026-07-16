"""
اختبارات نماذج Dashboard
Tests for Dashboard models
"""

import unittest
from datetime import date, datetime

from src.models.dashboard import KPI, ChartSeries, DashboardData, TimeSeriesPoint


class TestKPI(unittest.TestCase):
    """اختبارات KPI dataclass"""

    def test_kpi_creation_basic(self):
        """إنشاء KPI أساسي"""
        kpi = KPI(key="sales", title="المبيعات", value=10000)
        self.assertEqual(kpi.key, "sales")
        self.assertEqual(kpi.title, "المبيعات")
        self.assertEqual(kpi.value, 10000)
        self.assertEqual(kpi.change, 0.0)
        self.assertEqual(kpi.color, "#2196F3")

    def test_kpi_with_all_fields(self):
        """إنشاء KPI بجميع الحقول"""
        kpi = KPI(
            key="revenue",
            title="الإيرادات",
            value=50000.50,
            change=15.5,
            change_label="+15.5%",
            unit="د.ج",
            color="#4CAF50",
        )
        self.assertEqual(kpi.key, "revenue")
        self.assertEqual(kpi.value, 50000.50)
        self.assertEqual(kpi.change, 15.5)
        self.assertEqual(kpi.change_label, "+15.5%")
        self.assertEqual(kpi.unit, "د.ج")
        self.assertEqual(kpi.color, "#4CAF50")

    def test_kpi_int_value(self):
        """KPI مع قيمة int"""
        kpi = KPI(key="count", title="العدد", value=100)
        self.assertIsInstance(kpi.value, int)
        self.assertEqual(kpi.value, 100)


class TestTimeSeriesPoint(unittest.TestCase):
    """اختبارات TimeSeriesPoint"""

    def test_time_series_point_basic(self):
        """إنشاء نقطة زمنية أساسية"""
        point = TimeSeriesPoint(label="يناير", value=1500.0)
        self.assertEqual(point.label, "يناير")
        self.assertEqual(point.value, 1500.0)
        self.assertIsNone(point.ts)

    def test_time_series_point_with_timestamp(self):
        """نقطة زمنية مع timestamp"""
        now = datetime.now()
        point = TimeSeriesPoint(label="اليوم", value=2500.5, ts=now)
        self.assertEqual(point.label, "اليوم")
        self.assertEqual(point.value, 2500.5)
        self.assertEqual(point.ts, now)


class TestChartSeries(unittest.TestCase):
    """اختبارات ChartSeries"""

    def test_chart_series_empty(self):
        """إنشاء سلسلة فارغة"""
        series = ChartSeries(name="المبيعات")
        self.assertEqual(series.name, "المبيعات")
        self.assertEqual(series.points, [])
        self.assertIsNone(series.color)

    def test_chart_series_with_points(self):
        """سلسلة مع نقاط"""
        points = [
            TimeSeriesPoint("ينا", 100),
            TimeSeriesPoint("فبر", 150),
            TimeSeriesPoint("مار", 200),
        ]
        series = ChartSeries(name="الإيرادات", points=points, color="#FF5722")
        self.assertEqual(series.name, "الإيرادات")
        self.assertEqual(len(series.points), 3)
        self.assertEqual(series.points[0].value, 100)
        self.assertEqual(series.color, "#FF5722")


class TestDashboardData(unittest.TestCase):
    """اختبارات DashboardData"""

    def test_dashboard_data_basic(self):
        """إنشاء بيانات dashboard أساسية"""
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)
        dash = DashboardData(period_start=start, period_end=end)

        self.assertEqual(dash.period_start, start)
        self.assertEqual(dash.period_end, end)
        self.assertEqual(dash.kpis, [])
        self.assertEqual(dash.sales_series, [])
        self.assertEqual(dash.top_products, [])
        self.assertEqual(dash.inventory_value, 0.0)
        self.assertEqual(dash.low_stock_count, 0)
        self.assertEqual(dash.receivables_balance, 0.0)
        self.assertEqual(dash.payables_balance, 0.0)
        self.assertEqual(dash.active_customers, 0)
        self.assertEqual(dash.active_suppliers, 0)
        self.assertIsNone(dash.notes)
        self.assertEqual(dash.distribution, [])

    def test_dashboard_data_with_kpis(self):
        """dashboard مع KPIs"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        kpis = [KPI("sales", "المبيعات", 100000), KPI("profit", "الربح", 25000)]
        dash = DashboardData(
            period_start=start,
            period_end=end,
            kpis=kpis,
            inventory_value=500000.0,
            low_stock_count=5,
            active_customers=150,
        )

        self.assertEqual(len(dash.kpis), 2)
        self.assertEqual(dash.kpis[0].key, "sales")
        self.assertEqual(dash.inventory_value, 500000.0)
        self.assertEqual(dash.low_stock_count, 5)
        self.assertEqual(dash.active_customers, 150)

    def test_dashboard_data_with_series(self):
        """dashboard مع سلاسل بيانات"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        series = [ChartSeries("المبيعات", [TimeSeriesPoint("Week1", 5000)])]
        dash = DashboardData(period_start=start, period_end=end, sales_series=series)

        self.assertEqual(len(dash.sales_series), 1)
        self.assertEqual(dash.sales_series[0].name, "المبيعات")

    def test_dashboard_data_with_distribution(self):
        """dashboard مع بيانات التوزيع"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        dist = [
            {"label": "إلكترونيات", "value": 45000},
            {"label": "ملابس", "value": 30000},
            {"label": "أغذية", "value": 25000},
        ]
        dash = DashboardData(period_start=start, period_end=end, distribution=dist)

        self.assertEqual(len(dash.distribution), 3)
        self.assertEqual(dash.distribution[0]["label"], "إلكترونيات")
        self.assertEqual(dash.distribution[1]["value"], 30000)

    def test_dashboard_data_with_top_products(self):
        """dashboard مع أفضل المنتجات"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        products = [
            {"name": "منتج 1", "quantity": 100, "revenue": 50000},
            {"name": "منتج 2", "quantity": 80, "revenue": 40000},
        ]
        dash = DashboardData(period_start=start, period_end=end, top_products=products)

        self.assertEqual(len(dash.top_products), 2)
        self.assertEqual(dash.top_products[0]["name"], "منتج 1")

    def test_dashboard_data_with_notes(self):
        """dashboard مع ملاحظات"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)
        dash = DashboardData(
            period_start=start,
            period_end=end,
            notes="ملاحظات مهمة حول الأداء",
            receivables_balance=100000.0,
            payables_balance=50000.0,
        )

        self.assertEqual(dash.notes, "ملاحظات مهمة حول الأداء")
        self.assertEqual(dash.receivables_balance, 100000.0)
        self.assertEqual(dash.payables_balance, 50000.0)


if __name__ == "__main__":
    unittest.main()
