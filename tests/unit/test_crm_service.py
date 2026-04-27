#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for CRM Service
اختبارات خدمة إدارة العملاء (CRM)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.services.crm_service import CRMService, Lead, LeadStatus, Opportunity, OpportunityStage


class TestLeadStatus:
    """اختبارات حالات العملاء المحتملين"""
    
    def test_lead_status_values(self):
        """اختبار قيم حالات العملاء المحتملين"""
        assert LeadStatus.NEW.value == "new"
        assert LeadStatus.CONTACTED.value == "contacted"
        assert LeadStatus.QUALIFIED.value == "qualified"
        assert LeadStatus.PROPOSAL_SENT.value == "proposal_sent"
        assert LeadStatus.NEGOTIATION.value == "negotiation"
        assert LeadStatus.WON.value == "won"
        assert LeadStatus.LOST.value == "lost"


class TestOpportunityStage:
    """اختبارات مراحل الفرص البيعية"""
    
    def test_opportunity_stage_values(self):
        """اختبار قيم مراحل الفرص البيعية"""
        assert OpportunityStage.PROSPECTING.value == "prospecting"
        assert OpportunityStage.QUALIFICATION.value == "qualification"
        assert OpportunityStage.PROPOSAL.value == "proposal"
        assert OpportunityStage.NEGOTIATION.value == "negotiation"
        assert OpportunityStage.CLOSING.value == "closing"
        assert OpportunityStage.WON.value == "won"
        assert OpportunityStage.LOST.value == "lost"


class TestLead:
    """اختبارات فئة Lead"""
    
    def test_lead_creation_default(self):
        """اختبار إنشاء Lead افتراضي"""
        lead = Lead()
        
        assert lead.lead_id is None
        assert lead.name == ""
        assert lead.company is None
        assert lead.status == LeadStatus.NEW
        assert lead.expected_value == 0.0
    
    def test_lead_creation_with_values(self):
        """اختبار إنشاء Lead مع قيم"""
        lead = Lead(
            lead_id=1,
            name="Test Lead",
            company="Test Company",
            phone="1234567890",
            email="test@example.com",
            source="website",
            status=LeadStatus.QUALIFIED,
            assigned_to=1,
            expected_value=5000.0,
            notes="Important lead"
        )
        
        assert lead.lead_id == 1
        assert lead.name == "Test Lead"
        assert lead.company == "Test Company"
        assert lead.status == LeadStatus.QUALIFIED
        assert lead.expected_value == 5000.0


class TestOpportunity:
    """اختبارات فئة Opportunity"""
    
    def test_opportunity_creation_default(self):
        """اختبار إنشاء Opportunity افتراضية"""
        opp = Opportunity()
        
        assert opp.opportunity_id is None
        assert opp.name == ""
        assert opp.customer_id is None
        assert opp.stage == OpportunityStage.PROSPECTING
        assert opp.expected_value == 0.0
        assert opp.probability == 0.0
    
    def test_opportunity_creation_with_values(self):
        """اختبار إنشاء Opportunity مع قيم"""
        expected_date = datetime.now() + timedelta(days=30)
        
        opp = Opportunity(
            opportunity_id=1,
            name="Big Deal",
            customer_id=1,
            lead_id=1,
            stage=OpportunityStage.NEGOTIATION,
            expected_value=10000.0,
            probability=75.0,
            expected_close_date=expected_date,
            assigned_to=1,
            description="Important opportunity"
        )
        
        assert opp.opportunity_id == 1
        assert opp.name == "Big Deal"
        assert opp.stage == OpportunityStage.NEGOTIATION
        assert opp.expected_value == 10000.0
        assert opp.probability == 75.0


class TestCRMServiceInitialization:
    """اختبارات تهيئة CRMService"""
    
    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = MagicMock()
        
        service = CRMService(db_manager=mock_db)
        
        assert service.db == mock_db
    
    def test_initialization_with_logger(self):
        """اختبار التهيئة مع مسجل"""
        mock_db = MagicMock()
        mock_logger = MagicMock()
        
        service = CRMService(db_manager=mock_db, logger=mock_logger)
        
        assert service.logger == mock_logger


class TestCreateCustomer:
    """اختبارات إنشاء العميل"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة CRM مع mocks"""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.lastrowid = 1
        mock_db.execute_query.return_value = mock_result
        
        service = CRMService(db_manager=mock_db)
        return service
    
    def test_create_customer_success(self, service_with_mocks):
        """اختبار إنشاء عميل بنجاح"""
        customer_data = {
            'name': 'Test Customer',
            'phone': '1234567890',
            'email': 'test@example.com',
            'address': 'Test Address',
            'credit_limit': 1000.0,
            'current_balance': 0.0
        }
        
        result = service_with_mocks.create_customer(customer_data)
        
        assert result == 1
        service_with_mocks.db.execute_query.assert_called_once()
    
    def test_create_customer_minimal_data(self, service_with_mocks):
        """اختبار إنشاء عميل ببيانات قليلة"""
        customer_data = {
            'name': 'Minimal Customer'
        }
        
        result = service_with_mocks.create_customer(customer_data)
        
        assert result == 1
    
    def test_create_customer_db_error(self):
        """اختبار فشل إنشاء عميل"""
        mock_db = MagicMock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = MagicMock()
        
        service = CRMService(db_manager=mock_db, logger=mock_logger)
        
        customer_data = {'name': 'Test'}
        result = service.create_customer(customer_data)
        
        assert result is None
        mock_logger.error.assert_called_once()


class TestGetCustomer:
    """اختبارات الحصول على العميل"""
    
    def test_get_customer_success(self):
        """اختبار الحصول على عميل بنجاح"""
        mock_db = MagicMock()
        mock_db.fetch_one.return_value = {
            'id': 1,
            'name': 'Test Customer',
            'phone': '1234567890',
            'email': 'test@example.com'
        }
        
        service = CRMService(db_manager=mock_db)
        
        result = service.get_customer(1)
        
        assert result is not None
        assert result['id'] == 1
        assert result['name'] == 'Test Customer'
    
    def test_get_customer_not_found(self):
        """اختبار الحصول على عميل غير موجود"""
        mock_db = MagicMock()
        mock_db.fetch_one.return_value = None
        
        service = CRMService(db_manager=mock_db)
        
        result = service.get_customer(999)
        
        assert result is None


class TestSearchCustomers:
    """اختبارات البحث عن العملاء"""
    
    def test_search_customers_success(self):
        """اختبار البحث عن العملاء بنجاح"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            {'id': 1, 'name': 'John Doe'},
            {'id': 2, 'name': 'Jane Smith'}
        ]
        
        service = CRMService(db_manager=mock_db)
        
        result = service.search_customers('John')
        
        assert len(result) == 2
    
    def test_search_customers_empty(self):
        """اختبار البحث بدون نتائج"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        
        service = CRMService(db_manager=mock_db)
        
        result = service.search_customers('NonExistent')
        
        assert len(result) == 0


class TestCreateLead:
    """اختبارات إنشاء العميل المحتمل"""
    
    def test_create_lead_success(self):
        """اختبار إنشاء Lead بنجاح"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_db.get_connection().cursor.return_value = mock_cursor
        
        service = CRMService(db_manager=mock_db)
        
        lead = Lead(name='Test Lead', company='Test Company', email='lead@example.com')
        
        result = service.create_lead(lead)
        
        assert result == 1


class TestGetLeads:
    """اختبارات الحصول على العملاء المحتملين"""
    
    def test_list_leads(self):
        """اختبار الحصول على قائمة Leads"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            {'lead_id': 1, 'name': 'Lead 1', 'company': '', 'phone': '', 'email': '', 'source': '', 'status': 'new', 'assigned_to': 1, 'expected_value': 0, 'notes': ''},
            {'lead_id': 2, 'name': 'Lead 2', 'company': '', 'phone': '', 'email': '', 'source': '', 'status': 'contacted', 'assigned_to': 1, 'expected_value': 0, 'notes': ''}
        ]
        
        service = CRMService(db_manager=mock_db)
        
        result = service.list_leads()
        
        assert len(result) == 2


class TestUpdateLeadStatus:
    """اختبارات تحديث حالة العميل المحتمل"""
    
    def test_update_lead_status_success(self):
        """اختبار تحديث حالة Lead بنجاح"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection().cursor.return_value = mock_cursor
        
        service = CRMService(db_manager=mock_db)
        
        result = service.update_lead_status(1, LeadStatus.QUALIFIED)
        
        assert result is True


class TestCreateOpportunity:
    """اختبارات إنشاء الفرصة البيعية"""
    
    def test_create_opportunity_success(self):
        """اختبار إنشاء Opportunity بنجاح"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_db.get_connection().cursor.return_value = mock_cursor
        
        service = CRMService(db_manager=mock_db)
        
        opp = Opportunity(
            name='Big Deal',
            customer_id=1,
            expected_value=10000.0,
            probability=50.0
        )
        
        result = service.create_opportunity(opp)
        
        assert result == 1


class TestGetSalesPipeline:
    """اختبارات الحصول على مسار المبيعات"""
    
    def test_get_sales_pipeline_success(self):
        """اختبار الحصول على مسار المبيعات بنجاح"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            {'count': 5, 'total_value': 50000.0}
        ]
        
        service = CRMService(db_manager=mock_db)
        
        result = service.get_sales_pipeline()
        
        assert len(result) == len(OpportunityStage)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
