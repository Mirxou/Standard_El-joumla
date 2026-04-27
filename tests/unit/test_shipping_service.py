#!/usr/bin/env python3
"""
اختبارات Shipping Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from src.services.shipping_service import ShippingService

class TestShippingService:
    """اختبارات خدمة الشحن"""
    
    @pytest.fixture
    def shipping_service(self):
        """إنشاء خدمة شحن"""
        mock_db = MagicMock()
        return ShippingService(db_manager=mock_db)
    
    def test_initialization(self, shipping_service):
        """اختبار التهيئة"""
        assert shipping_service is not None
        assert shipping_service.db_manager is not None
    
    def test_create_shipment_no_integration(self, shipping_service):
        """اختبار إنشاء شحنة بتكامل غير موجود"""
        shipping_service.db_manager.fetch_one.return_value = None
        
        success, shipment_id, response = shipping_service.create_shipment(
            integration_id=1,
            sale_id=100,
            origin_address="Origin",
            destination_address="Dest",
            weight=Decimal("5.0")
        )
        assert success is False
        assert response.get("error") == "التكامل غير موجود"
    
    def test_track_shipment_no_integration(self, shipping_service):
        """اختبار تتبع شحنة بتكامل غير موجود"""
        shipping_service.db_manager.fetch_one.return_value = None
        
        success, response = shipping_service.track_shipment("TRACK123", 1)
        assert success is False
        assert response.get("error") == "التكامل غير موجود"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
