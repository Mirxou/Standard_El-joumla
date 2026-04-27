#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for AccountingIntegrationService
اختبارات وحدة لخدمة تكامل المحاسبة
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock
from src.services.accounting_integration_service import AccountingIntegrationService, AccountingSync

class TestAccountingIntegrationService:
    @pytest.fixture
    def db_manager(self):
        mock_db = MagicMock()
        return mock_db

    @pytest.fixture
    def service(self, db_manager):
        with patch('src.services.accounting_integration_service.TenantIsolationManager', return_value=MagicMock()):
            return AccountingIntegrationService(db_manager)

    def test_initialization(self, service):
        """Test if the service initializes correctly"""
        assert service.db_manager is not None
        assert service.logger is not None

    def test_sync_sale_quickbooks_success(self, service, db_manager):
        """Test successful synchronization of a sale to QuickBooks"""
        integration_id = 1
        sale_id = 101
        
        # Mock integration data
        service._get_integration = MagicMock(return_value={
            "id": integration_id,
            "is_active": True,
            "provider": "QUICKBOOKS",
            "api_key": "test_key",
            "api_secret": "test_secret"
        })
        
        # Mock sale data
        service._get_sale_data = MagicMock(return_value={
            "id": sale_id,
            "total_amount": 1000.0,
            "customer_id": 5,
            "customer_name": "Test Customer",
            "invoice_number": "INV-101",
            "sale_date": "2026-04-16"
        })
        
        # Mock _save_sync
        service._save_sync = MagicMock()
        
        success, provider_id, response = service.sync_sale(integration_id, sale_id)
        
        assert success is True
        assert provider_id.startswith("QB_")
        assert response["simulated"] is True
        service._save_sync.assert_called_once()

    def test_sync_sale_xero_success(self, service, db_manager):
        """Test successful synchronization of a sale to Xero"""
        integration_id = 2
        sale_id = 102
        
        # Mock integration data
        service._get_integration = MagicMock(return_value={
            "id": integration_id,
            "is_active": True,
            "provider": "XERO",
            "api_key": "test_key"
        })
        
        # Mock sale data
        service._get_sale_data = MagicMock(return_value={
            "id": sale_id,
            "total_amount": 500.0,
            "customer_id": 6,
            "invoice_number": "INV-102"
        })
        
        # Mock _save_sync
        service._save_sync = MagicMock()
        
        success, provider_id, response = service.sync_sale(integration_id, sale_id)
        
        assert success is True
        assert provider_id.startswith("XERO_")
        service._save_sync.assert_called_once()

    def test_sync_sale_inactive_integration(self, service):
        """Test synchronization attempt with an inactive integration"""
        service._get_integration = MagicMock(return_value={"id": 1, "is_active": False})
        
        success, provider_id, response = service.sync_sale(1, 101)
        
        assert success is False
        assert response["error"] == "التكامل غير نشط"

    def test_sync_purchase_success(self, service):
        """Test successful synchronization of a purchase"""
        integration_id = 1
        purchase_id = 201
        
        service._get_integration = MagicMock(return_value={"id": integration_id, "provider": "QUICKBOOKS"})
        service._get_purchase_data = MagicMock(return_value={"id": purchase_id})
        
        success, provider_id, response = service.sync_purchase(integration_id, purchase_id)
        
        assert success is True
        assert "PURCHASE" in provider_id

    def test_sync_payment_success(self, service):
        """Test successful synchronization of a payment"""
        integration_id = 1
        payment_id = 301
        
        service._get_integration = MagicMock(return_value={"id": integration_id, "provider": "XERO"})
        service._get_payment_data = MagicMock(return_value={"id": payment_id})
        
        success, provider_id, response = service.sync_payment(integration_id, payment_id)
        
        assert success is True
        assert "PAYMENT" in provider_id

if __name__ == "__main__":
    pytest.main([__file__])



