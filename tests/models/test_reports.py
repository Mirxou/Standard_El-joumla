import pytest
from datetime import date, timedelta
from src.models.reports import ReportManager
from unittest.mock import MagicMock

class TestReportManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def report_manager(self, mock_db):
        return ReportManager(mock_db)

    def test_get_financial_summary_defaults(self, report_manager, mock_db):
        # Setup mock return
        mock_db.execute_query.return_value.fetchone.side_effect = [
            {'total_sales': 1000, 'collected_cash': 800}, # sales_result
            {'total_cogs': 600}, # cogs_result
        ]

        summary = report_manager.get_financial_summary()

        assert summary['total_sales'] == 1000
        assert summary['total_cost'] == 600
        assert summary['net_profit'] == 400
        assert summary['profit_margin'] == 40.0
        assert summary['collected_cash'] == 800

    def test_get_financial_summary_empty(self, report_manager, mock_db):
         # Setup mock return for no data
        mock_db.execute_query.return_value.fetchone.side_effect = [
            {'total_sales': None, 'collected_cash': None},
            {'total_cogs': None},
        ]

        summary = report_manager.get_financial_summary()

        assert summary['total_sales'] == 0
        assert summary['net_profit'] == 0

    def test_get_inventory_analytics(self, report_manager, mock_db):
        mock_db.execute_query.return_value.fetchone.side_effect = [
            {
                'total_cost_value': 5000,
                'total_sales_value': 8000,
                'total_products': 50,
                'total_items': 200
            }, # value_result
            {'count': 5} # low_stock_result
        ]

        analytics = report_manager.get_inventory_analytics()
        
        assert analytics['total_cost_value'] == 5000
        assert analytics['potential_profit'] == 3000
        assert analytics['low_stock_count'] == 5
