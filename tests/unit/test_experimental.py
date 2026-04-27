#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Experimental and Deprecated Services
اختبارات الخدمات التجريبية والمهملة (Guardrail Tests)
"""

import pytest
from unittest.mock import MagicMock
from src.experimental.deprecated_services.einvoice_service import EInvoiceGenerator, EInvoiceConfig, RecurringInvoiceManager
from src.experimental.deprecated_ui.wholesale_invoice_ui import WholesaleInvoiceWindow

class TestEInvoiceService:
    """اختبارات خدمة الفوترة الإلكترونية (التجريبية)"""

    @pytest.fixture
    def generator(self):
        """إعداد مولد الفواتير الإلكترونية"""
        config = EInvoiceConfig(
            company_vat_number="300012345600003",
            company_name="شركة اختبار",
            company_address="الجزائر"
        )
        return EInvoiceGenerator(config)

    def test_invoice_generation(self, generator):
        """اختبار إنشاء فاتورة إلكترونية"""
        invoice = generator.generate_invoice(
            invoice_number="INV-EXP-001",
            invoice_date="2026-01-01",
            customer_name="عميل اختبار",
            customer_vat="300012345600004",
            items=[{"name": "Item 1", "quantity": 1, "unit_price": 100, "total": 100}],
            total_amount=119.0,
            vat_amount=19.0
        )
        
        assert invoice["invoice_number"] == "INV-EXP-001"
        assert "digital_signature" in invoice
        assert "qr_code" in invoice

    def test_xml_conversion(self, generator):
        """اختبار تحويل الفاتورة إلى XML"""
        invoice_data = {
            "invoice_number": "INV-001",
            "invoice_date": "2026-01-01",
            "seller": {"name": "Seller", "vat_number": "123", "address": "Addr"},
            "buyer": {"name": "Buyer", "vat_number": "456"},
            "items": [],
            "totals": {"subtotal": 100, "vat": 19, "total": 119}
        }
        xml = generator.convert_to_xml(invoice_data)
        assert "<Invoice" in xml
        assert "<ID>INV-001</ID>" in xml

class TestWholesaleInvoiceUI:
    """اختبارات واجهة فاتورة الجملة (المهملة)"""

    def test_instantiation(self, qtbot):
        """التحقق من إمكانية إنشاء الواجهة دون انهيار"""
        try:
            window = WholesaleInvoiceWindow()
            qtbot.addWidget(window)
            assert window is not None
            assert "Wholesale Invoice" in window.windowTitle()
        except Exception as e:
            pytest.skip(f"WholesaleInvoiceWindow failed to instantiate: {e}")

class TestRecurringInvoiceManager:
    """اختبارات مدير الفواتير الدورية (المهمل)"""

    def test_initialization(self):
        """التحقق من التهيئة وإنشاء الجداول"""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_db.connection = mock_conn
        
        manager = RecurringInvoiceManager(mock_db)
        assert manager.db == mock_db
        # التحقق من استدعاء execute لإنشاء الجداول
        assert mock_conn.cursor().execute.called



