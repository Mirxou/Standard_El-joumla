#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests for Webhook Triggers
اختبارات تكامل لـ Webhook Triggers
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.database_manager import DatabaseManager
from src.models.sale import Sale, SaleItem, SaleManager, SaleStatus, PaymentMethod
from src.models.purchase import Purchase, PurchaseItem, PurchaseManager, PurchaseStatus
from src.services.payment_service import PaymentService, PaymentType, PaymentMethod as PM
from src.services.webhook_service import WebhookService


class TestWebhookTriggers:
    """اختبارات Webhook Triggers"""
    
    @pytest.fixture
    def db_manager(self):
        """إنشاء DatabaseManager للاختبارات"""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        
        # إنشاء جداول أساسية
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                total_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                final_amount REAL DEFAULT 0,
                payment_method TEXT,
                sale_date DATE,
                user_id INTEGER,
                notes TEXT,
                status TEXT DEFAULT 'draft',
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0,
                currency_id INTEGER,
                exchange_rate REAL DEFAULT 1.0,
                base_amount REAL,
                converted_amount REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_percent REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE
            )
        """)
        
        db.execute_query("DROP TABLE IF EXISTS purchases")
        db.execute_query("""
            CREATE TABLE purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                supplier_invoice_number TEXT,
                supplier_id INTEGER,
                purchase_date DATE,
                expected_delivery_date DATE,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'pending',
                payment_terms TEXT,
                subtotal_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                shipping_cost REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0,
                currency_id INTEGER,
                exchange_rate REAL DEFAULT 1.0,
                base_amount REAL,
                converted_amount REAL,
                notes TEXT,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute_query("DROP TABLE IF EXISTS purchase_items")
        db.execute_query("""
            CREATE TABLE purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity_ordered REAL NOT NULL,
                quantity_received REAL DEFAULT 0,
                unit_cost REAL NOT NULL,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_percent REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                expiry_date DATE,
                batch_number TEXT,
                notes TEXT,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_number TEXT UNIQUE NOT NULL,
                payment_type TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'معلق',
                amount REAL NOT NULL DEFAULT 0.00,
                payment_date DATE NOT NULL,
                customer_id INTEGER,
                supplier_id INTEGER,
                user_id INTEGER,
                sale_id INTEGER,
                purchase_id INTEGER,
                currency_id INTEGER,
                exchange_rate REAL DEFAULT 1.0,
                base_amount REAL,
                converted_amount REAL,
                company_id INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        
        db.execute_query("DROP TABLE IF EXISTS customers")
        db.execute_query("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company_id INTEGER
            )
        """)
        
        db.execute_query("DROP TABLE IF EXISTS suppliers")
        db.execute_query("""
            CREATE TABLE suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company_id INTEGER
            )
        """)
        
        db.execute_query("DROP TABLE IF EXISTS products")
        db.execute_query("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                current_stock REAL DEFAULT 0,
                company_id INTEGER
            )
        """)
        
        db.execute_query("DROP TABLE IF EXISTS companies")
        db.execute_query("""
            CREATE TABLE companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                event_type TEXT NOT NULL,
                http_method TEXT DEFAULT 'POST',
                is_active INTEGER DEFAULT 1,
                retry_count INTEGER DEFAULT 3,
                timeout_seconds INTEGER DEFAULT 30,
                company_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                webhook_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                entity_id INTEGER,
                payload TEXT NOT NULL,
                response_status INTEGER,
                is_success INTEGER DEFAULT 0,
                attempt_number INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
            )
        """)
        
        # بيانات تجريبية (استخدم INSERT OR IGNORE لتفادي الأخطاء عند إعادة تشغيل الاختبارات)
        db.execute_query("INSERT OR IGNORE INTO companies (id, name, code) VALUES (1, 'Test Company', 'TC')")
        db.execute_query("INSERT OR IGNORE INTO customers (id, name, company_id) VALUES (1, 'Test Customer', 1)")
        db.execute_query("INSERT OR IGNORE INTO suppliers (id, name, company_id) VALUES (1, 'Test Supplier', 1)")
        db.execute_query("INSERT OR IGNORE INTO products (id, name, current_stock, company_id) VALUES (1, 'Test Product', 100, 1)")
        
        yield db
        
        # تنظيف
        try:
            db.close()
        except:
            pass
    
    @pytest.fixture
    def webhook_service(self, db_manager):
        """إنشاء WebhookService للاختبارات"""
        return WebhookService(db_manager, logger=Mock())
    
    @patch('src.core.tenant_isolation.TenantIsolationManager.get_current_company_id')
    @patch('src.services.webhook_service.get_webhook_dispatcher')
    def test_sale_created_webhook_trigger(self, mock_get_dispatcher, mock_get_company_id, db_manager, webhook_service):
        """اختبار إطلاق Webhook عند إنشاء فاتورة مبيعات"""
        from src.core.webhook_dispatcher import WebhookDeliveryResult
        
        # Mock Dispatcher
        mock_dispatcher = Mock()
        mock_get_dispatcher.return_value = mock_dispatcher
        
        # Mock deliver_webhook side effect to call the callback
        def deliver_side_effect(*args, **kwargs):
            callback = kwargs.get('callback')
            if callback:
                result = WebhookDeliveryResult(success=True, status_code=200, execution_time_ms=100)
                # Ensure payload is a JSON string as expected by callback
                import json
                payload_json = json.dumps(kwargs.get('payload', {}))
                callback(
                    result=result,
                    webhook_id=kwargs.get('webhook_id'),
                    event_type=kwargs.get('event_type'),
                    entity_id=kwargs.get('entity_id'),
                    payload_json=payload_json
                )
            return True
            
        mock_dispatcher.deliver_webhook.side_effect = deliver_side_effect
        
        # Mock Company ID
        mock_get_company_id.return_value = 1
        
        # إنشاء Webhook نشط
        webhook_service.create_webhook(
            name="Sale Webhook",
            url="https://example.com/sale",
            event_type="sale_created",
            is_active=True,
            company_id=1
        )
        
        # إنشاء فاتورة مبيعات
        sale_manager = SaleManager(db_manager, logger=Mock())
        sale = Sale(
            invoice_number="INV-001",
            customer_id=1,
            total_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            sale_date=date.today(),
            status=SaleStatus.CONFIRMED,
            payment_method=PaymentMethod.CASH,
            created_by=1
        )
        sale.items = []
        
        sale_id = sale_manager.create_sale(sale)
        
        # التحقق من إطلاق Webhook
        assert sale_id is not None
        
        # 1. التحقق من استدعاء الـ Dispatcher
        assert mock_dispatcher.deliver_webhook.called, "لم يتم استدعاء الـ dispatcher لإرسال الـ webhook"
        args, kwargs = mock_dispatcher.deliver_webhook.call_args
        assert kwargs['url'] == "https://example.com/sale"
        assert kwargs['payload']['invoice_number'] == "INV-001"
        
        # 2. التحقق من وجود سجل في webhook_logs
        logs = db_manager.fetch_all("SELECT * FROM webhook_logs WHERE event_type = 'sale_created'")
        assert len(logs) > 0, "لم يتم العثور على سجل في webhook_logs"
    
    @patch('src.core.tenant_isolation.TenantIsolationManager.get_current_company_id')
    @patch('src.services.webhook_service.get_webhook_dispatcher')
    def test_payment_received_webhook_trigger(self, mock_get_dispatcher, mock_get_company_id, db_manager, webhook_service):
        """اختبار إطلاق Webhook عند استلام دفعة"""
        from src.core.webhook_dispatcher import WebhookDeliveryResult
        
        # Mock Dispatcher
        mock_dispatcher = Mock()
        mock_get_dispatcher.return_value = mock_dispatcher
        
        # Mock deliver_webhook side effect to call the callback
        def deliver_side_effect(*args, **kwargs):
            callback = kwargs.get('callback')
            if callback:
                result = WebhookDeliveryResult(success=True, status_code=200, execution_time_ms=100)
                import json
                payload_json = json.dumps(kwargs.get('payload', {}))
                callback(
                    result=result,
                    webhook_id=kwargs.get('webhook_id'),
                    event_type=kwargs.get('event_type'),
                    entity_id=kwargs.get('entity_id'),
                    payload_json=payload_json
                )
            return True
            
        mock_dispatcher.deliver_webhook.side_effect = deliver_side_effect
        
        # Mock Company ID
        mock_get_company_id.return_value = 1
        
        # إنشاء Webhook نشط
        webhook_service.create_webhook(
            name="Payment Webhook",
            url="https://example.com/payment",
            event_type="payment_received",
            is_active=True,
            company_id=1
        )
        
        # إنشاء دفعة
        payment_service = PaymentService(db_manager, logger=Mock())
        
        payment_id = payment_service.create_customer_payment(
            customer_id=1,
            amount=Decimal("50.00"),
            payment_method=PM.CASH.value
        )
        
        # التحقق من إنشاء الدفعة وإطلاق الـ Webhook
        assert payment_id is not None
        
        # 1. التحقق من الـ Dispatcher
        assert mock_dispatcher.deliver_webhook.called, "لم يتم استدعاء الـ dispatcher للدفعة"
        
        # 2. التحقق من السجلات
        logs = db_manager.fetch_all("SELECT * FROM webhook_logs WHERE event_type = 'payment_received'")
        assert len(logs) > 0, "لم يتم العثور على سجل دفعة في webhook_logs"
    
    @patch('src.core.tenant_isolation.TenantIsolationManager.get_current_company_id')
    @patch('src.services.webhook_service.get_webhook_dispatcher')
    def test_purchase_created_webhook_trigger(self, mock_get_dispatcher, mock_get_company_id, db_manager, webhook_service):
        """اختبار إطلاق Webhook عند إنشاء فاتورة شراء"""
        from src.core.webhook_dispatcher import WebhookDeliveryResult
        
        # Mock Dispatcher
        mock_dispatcher = Mock()
        mock_get_dispatcher.return_value = mock_dispatcher
        
        # Mock deliver_webhook side effect to call the callback
        def deliver_side_effect(*args, **kwargs):
            callback = kwargs.get('callback')
            if callback:
                result = WebhookDeliveryResult(success=True, status_code=200, execution_time_ms=100)
                import json
                payload_json = json.dumps(kwargs.get('payload', {}))
                callback(
                    result=result,
                    webhook_id=kwargs.get('webhook_id'),
                    event_type=kwargs.get('event_type'),
                    entity_id=kwargs.get('entity_id'),
                    payload_json=payload_json
                )
            return True
            
        mock_dispatcher.deliver_webhook.side_effect = deliver_side_effect
        
        # Mock Company ID
        mock_get_company_id.return_value = 1
        
        # إنشاء Webhook نشط
        webhook_service.create_webhook(
            name="Purchase Webhook",
            url="https://example.com/purchase",
            event_type="purchase_created",
            is_active=True,
            company_id=1
        )
        
        # إنشاء فاتورة شراء
        purchase_manager = PurchaseManager(db_manager, logger=Mock())
        purchase = Purchase(
            invoice_number="PO-001",
            supplier_id=1,
            purchase_date=date.today(),
            status=PurchaseStatus.PENDING.value,
            payment_status="pending"
        )
        purchase.items = []
        
        purchase_id = purchase_manager.create_purchase(purchase)
        
        # التحقق من إنشاء الفاتورة وإطلاق الـ Webhook
        assert purchase_id is not None
        
        # 1. التحقق من الـ Dispatcher
        assert mock_dispatcher.deliver_webhook.called, "لم يتم استدعاء الـ dispatcher للمشتريات"
        
        # 2. التحقق من السجلات
        logs = db_manager.fetch_all("SELECT * FROM webhook_logs WHERE event_type = 'purchase_created'")
        assert len(logs) > 0, "لم يتم العثور على سجل مشتريات في webhook_logs"
    
    def test_webhook_not_triggered_when_inactive(self, db_manager, webhook_service):
        """اختبار عدم إطلاق Webhook غير نشط"""
        # إنشاء Webhook غير نشط
        webhook_service.create_webhook(
            name="Inactive Webhook",
            url="https://example.com/inactive",
            event_type="sale_created",
            is_active=False,
            company_id=1
        )
        
        # التحقق من عدم وجود Webhooks نشطة
        active_webhooks = webhook_service.get_all_webhooks(
            event_type="sale_created",
            is_active=True,
            company_id=1
        )
        
        assert len(active_webhooks) == 0
    
    def test_multiple_webhooks_for_same_event(self, db_manager, webhook_service):
        """اختبار إطلاق عدة Webhooks لنفس الحدث"""
        # إنشاء عدة Webhooks لنفس الحدث
        webhook_service.create_webhook(
            name="Webhook 1",
            url="https://example.com/webhook1",
            event_type="sale_created",
            is_active=True,
            company_id=1
        )
        
        webhook_service.create_webhook(
            name="Webhook 2",
            url="https://example.com/webhook2",
            event_type="sale_created",
            is_active=True,
            company_id=1
        )
        
        # الحصول على جميع Webhooks النشطة
        webhooks = webhook_service.get_all_webhooks(
            event_type="sale_created",
            is_active=True,
            company_id=1
        )
        
        assert len(webhooks) == 2





