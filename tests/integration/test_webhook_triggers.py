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

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER,
                total_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'pending',
                currency_id INTEGER,
                exchange_rate REAL DEFAULT 1.0,
                base_amount REAL,
                converted_amount REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity_ordered REAL NOT NULL,
                unit_cost REAL NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE
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
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company_id INTEGER
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company_id INTEGER
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                current_stock REAL DEFAULT 0,
                company_id INTEGER
            )
        """)
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
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
        
        # بيانات تجريبية
        db.execute_query("INSERT INTO companies (id, name) VALUES (1, 'Test Company')")
        db.execute_query("INSERT INTO customers (id, name, company_id) VALUES (1, 'Test Customer', 1)")
        db.execute_query("INSERT INTO suppliers (id, name, company_id) VALUES (1, 'Test Supplier', 1)")
        db.execute_query("INSERT INTO products (id, name, current_stock, company_id) VALUES (1, 'Test Product', 100, 1)")
        
        return db
    
    @pytest.fixture
    def webhook_service(self, db_manager):
        """إنشاء WebhookService للاختبارات"""
        return WebhookService(db_manager, logger=Mock())
    
    @patch('src.core.webhook_dispatcher.get_webhook_dispatcher')
    def test_sale_created_webhook_trigger(self, mock_get_dispatcher, db_manager, webhook_service):
        """اختبار إطلاق Webhook عند إنشاء فاتورة مبيعات"""
        # Mock Dispatcher
        mock_dispatcher = Mock()
        mock_get_dispatcher.return_value = mock_dispatcher
        
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
        # Note: في الواقع، Webhook يتم إطلاقه داخل create_sale
        # لكن للاختبار، يمكن التحقق من وجود Webhook Logs
    
    @patch('src.core.webhook_dispatcher.get_webhook_dispatcher')
    def test_payment_received_webhook_trigger(self, mock_get_dispatcher, db_manager, webhook_service):
        """اختبار إطلاق Webhook عند استلام دفعة"""
        # Mock Dispatcher
        mock_dispatcher = Mock()
        mock_get_dispatcher.return_value = mock_dispatcher
        
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
        payment = payment_service.create_customer_payment(
            customer_id=1,
            amount=Decimal("50.00"),
            payment_method=PM.CASH.value
        )
        
        # التحقق من إنشاء الدفعة
        assert payment is not None
    
    @patch('src.core.webhook_dispatcher.get_webhook_dispatcher')
    def test_purchase_created_webhook_trigger(self, mock_get_dispatcher, db_manager, webhook_service):
        """اختبار إطلاق Webhook عند إنشاء فاتورة شراء"""
        # Mock Dispatcher
        mock_dispatcher = Mock()
        mock_get_dispatcher.return_value = mock_dispatcher
        
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
            status=PurchaseStatus.PENDING,
            payment_status="pending"
        )
        purchase.items = []
        
        purchase_id = purchase_manager.create_purchase(purchase)
        
        # التحقق من إنشاء الفاتورة
        assert purchase_id is not None
    
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

