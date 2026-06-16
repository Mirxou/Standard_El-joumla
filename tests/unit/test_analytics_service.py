#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Analytics Service"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from src.services.analytics_service import AnalyticsService


class TestAnalyticsServiceInitialization:
    def test_initialization_with_db_manager(self):
        mock_db = Mock()
        service = AnalyticsService(db_manager=mock_db)
        assert service.db_manager == mock_db
        assert service.tenant_isolation is None

    def test_initialization_with_tenant_isolation(self):
        mock_db = Mock()
        mock_tenant = Mock()
        mock_tenant.get_current_company_id.return_value = 1
        service = AnalyticsService(db_manager=mock_db, tenant_isolation=mock_tenant)
        assert service.db_manager == mock_db
        assert service.tenant_isolation == mock_tenant


class TestGetSalesTrends:
    @pytest.fixture
    def service_with_mock_db(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {"date": "2024-01-01", "total_amount": 100.0, "transaction_count": 5},
            {"date": "2024-01-02", "total_amount": 150.0, "transaction_count": 8},
        ]
        return AnalyticsService(db_manager=mock_db)

    def test_get_sales_trends_success(self, service_with_mock_db):
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result = service_with_mock_db.get_sales_trends(start_date, end_date)
        assert result.get("success") is True
        assert "data" in result
        assert "trends" in result

    def test_get_sales_trends_with_tenant(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {"date": "2024-01-01", "total_amount": 100.0, "transaction_count": 5},
        ]
        mock_tenant = Mock()
        mock_tenant.get_current_company_id.return_value = 1
        service = AnalyticsService(db_manager=mock_db, tenant_isolation=mock_tenant)
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result = service.get_sales_trends(start_date, end_date)
        assert result.get("success") is True
        mock_db.fetch_all.assert_called_once()

    def test_get_sales_trends_exception(self):
        mock_db = Mock()
        mock_db.fetch_all.side_effect = Exception("Database error")
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_trends(datetime.now() - timedelta(days=30), datetime.now())
        assert "error" in result

    def test_get_sales_trends_empty_data(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_trends()
        assert result.get("data") == []


class TestGetSalesByCategory:
    @pytest.fixture
    def service_with_mock_db(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {
                "category_name": "Electronics",
                "sale_count": 10,
                "total_quantity": 50,
                "total_amount": 5000.0,
            },
            {
                "category_name": "Clothing",
                "sale_count": 15,
                "total_quantity": 30,
                "total_amount": 3000.0,
            },
        ]
        return AnalyticsService(db_manager=mock_db)

    def test_get_sales_by_category_success(self, service_with_mock_db):
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result = service_with_mock_db.get_sales_by_category(start_date, end_date)
        assert result.get("success") is True
        assert "data" in result

    def test_get_sales_by_category_with_null_category(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {
                "category_name": None,
                "sale_count": 5,
                "total_quantity": 10,
                "total_amount": 1000.0,
            },
        ]
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_by_category()
        assert result["data"][0]["category"] == "بدون فئة"

    def test_get_sales_by_category_exception(self):
        mock_db = Mock()
        mock_db.fetch_all.side_effect = Exception("Database error")
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_by_category()
        assert "error" in result


class TestGetSalesByCustomer:
    @pytest.fixture
    def service_with_mock_db(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "customer_name": "John Doe",
                "sale_count": 5,
                "total_amount": 5000.0,
                "avg_amount": 1000.0,
            },
        ]
        return AnalyticsService(db_manager=mock_db)

    def test_get_sales_by_customer_success(self, service_with_mock_db):
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result = service_with_mock_db.get_sales_by_customer(limit=10, start_date=start_date, end_date=end_date)
        assert result.get("success") is True
        assert "data" in result

    def test_get_sales_by_customer_with_tenant(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "customer_name": "John Doe",
                "sale_count": 5,
                "total_amount": 5000.0,
                "avg_amount": 1000.0,
            },
        ]
        mock_tenant = Mock()
        mock_tenant.get_current_company_id.return_value = 1
        service = AnalyticsService(db_manager=mock_db, tenant_isolation=mock_tenant)
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result = service.get_sales_by_customer(limit=10, start_date=start_date, end_date=end_date)
        assert result.get("success") is True
        mock_db.fetch_all.assert_called_once()

    def test_get_sales_by_customer_exception(self):
        mock_db = Mock()
        mock_db.fetch_all.side_effect = Exception("Database error")
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_by_customer()
        assert "error" in result


class TestDefaultDates:
    def test_default_dates_for_sales_trends(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_trends()
        assert result.get("success") is True

    def test_default_dates_for_sales_by_category(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_by_category()
        assert result.get("success") is True

    def test_default_dates_for_sales_by_customer(self):
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        service = AnalyticsService(db_manager=mock_db)
        result = service.get_sales_by_customer()
        assert result.get("success") is True
