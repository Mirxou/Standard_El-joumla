#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Webhook Service
اختبارات وحدة لـ Webhook Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.services.webhook_service import WebhookService, Webhook, WebhookLog
from src.core.database_manager import DatabaseManager


class TestWebhook:
    """اختبارات Webhook Data Class"""
    
    def test_webhook_to_dict(self):
        """اختبار تحويل Webhook إلى Dictionary"""
        webhook = Webhook(
            id=1,
            name="Test Webhook",
            url="https://example.com/webhook",
            event_type="sale_created",
            http_method="POST",
            is_active=True,
            retry_count=3,
            timeout_seconds=30,
            company_id=1,
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        data = webhook.to_dict()
        
        assert data["id"] == 1
        assert data["name"] == "Test Webhook"
        assert data["url"] == "https://example.com/webhook"
        assert data["event_type"] == "sale_created"
        assert data["is_active"] == True
        assert data["retry_count"] == 3
    
    def test_webhook_from_dict(self):
        """اختبار إنشاء Webhook من Dictionary"""
        data = {
            "id": 1,
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "event_type": "sale_created",
            "http_method": "POST",
            "is_active": True,
            "retry_count": 3,
            "timeout_seconds": 30,
            "created_at": "2024-01-01T12:00:00"
        }
        
        webhook = Webhook.from_dict(data)
        
        assert webhook.id == 1
        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/webhook"
        assert webhook.event_type == "sale_created"
        assert webhook.is_active == True


class TestWebhookService:
    """اختبارات Webhook Service"""
    
    @pytest.fixture
    def db_manager(self):
        """إنشاء DatabaseManager للاختبارات"""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        
        # إنشاء جداول Webhooks
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                event_type TEXT NOT NULL,
                http_method TEXT DEFAULT 'POST',
                headers TEXT,
                payload_template TEXT,
                is_active INTEGER DEFAULT 1,
                retry_count INTEGER DEFAULT 3,
                timeout_seconds INTEGER DEFAULT 30,
                secret_key TEXT,
                company_id INTEGER,
                created_by INTEGER,
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
                response_body TEXT,
                error_message TEXT,
                attempt_number INTEGER DEFAULT 1,
                is_success INTEGER DEFAULT 0,
                execution_time_ms INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
            )
        """)
        
        # Drop existing companies table and create it with code column
        db.execute_query("DROP TABLE IF EXISTS companies")
        
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL
            )
        """)
        
        # إضافة شركة تجريبية
        db.execute_query("INSERT INTO companies (id, code, name) VALUES (1, 'TEST', 'Test Company')")
        
        return db
    
    @pytest.fixture
    def webhook_service(self, db_manager):
        """إنشاء WebhookService للاختبارات"""
        return WebhookService(db_manager, logger=Mock())
    
    def test_create_webhook(self, webhook_service):
        """اختبار إنشاء Webhook"""
        webhook_id = webhook_service.create_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            event_type="sale_created",
            company_id=1
        )
        
        assert webhook_id is not None
        assert webhook_id > 0
        
        # التحقق من إنشاء Webhook
        webhook = webhook_service.get_webhook(webhook_id, company_id=1)
        assert webhook is not None
        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/webhook"
        assert webhook.event_type == "sale_created"
    
    def test_get_webhook(self, webhook_service):
        """اختبار الحصول على Webhook"""
        # إنشاء Webhook
        webhook_id = webhook_service.create_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            event_type="sale_created",
            company_id=1
        )
        
        # الحصول على Webhook
        webhook = webhook_service.get_webhook(webhook_id, company_id=1)
        
        assert webhook is not None
        assert webhook.id == webhook_id
        assert webhook.name == "Test Webhook"
    
    def test_get_all_webhooks(self, webhook_service):
        """اختبار الحصول على جميع Webhooks"""
        # إنشاء عدة Webhooks
        webhook_service.create_webhook(
            name="Webhook 1",
            url="https://example.com/webhook1",
            event_type="sale_created",
            company_id=1
        )
        
        webhook_service.create_webhook(
            name="Webhook 2",
            url="https://example.com/webhook2",
            event_type="payment_received",
            company_id=1
        )
        
        # الحصول على جميع Webhooks
        webhooks = webhook_service.get_all_webhooks(company_id=1)
        
        assert len(webhooks) == 2
    
    def test_get_all_webhooks_filter_by_event_type(self, webhook_service):
        """اختبار فلترة Webhooks حسب نوع الحدث"""
        # إنشاء Webhooks
        webhook_service.create_webhook(
            name="Sale Webhook",
            url="https://example.com/sale",
            event_type="sale_created",
            company_id=1
        )
        
        webhook_service.create_webhook(
            name="Payment Webhook",
            url="https://example.com/payment",
            event_type="payment_received",
            company_id=1
        )
        
        # الحصول على Webhooks لنوع حدث محدد
        sale_webhooks = webhook_service.get_all_webhooks(
            event_type="sale_created",
            company_id=1
        )
        
        assert len(sale_webhooks) == 1
        assert sale_webhooks[0].event_type == "sale_created"
    
    def test_update_webhook(self, webhook_service):
        """اختبار تحديث Webhook"""
        # إنشاء Webhook
        webhook_id = webhook_service.create_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            event_type="sale_created",
            company_id=1
        )
        
        # تحديث Webhook
        success = webhook_service.update_webhook(
            webhook_id=webhook_id,
            name="Updated Webhook",
            url="https://example.com/updated",
            company_id=1
        )
        
        assert success == True
        
        # التحقق من التحديث
        webhook = webhook_service.get_webhook(webhook_id, company_id=1)
        assert webhook.name == "Updated Webhook"
        assert webhook.url == "https://example.com/updated"
    
    def test_delete_webhook(self, webhook_service):
        """اختبار حذف Webhook"""
        # إنشاء Webhook
        webhook_id = webhook_service.create_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            event_type="sale_created",
            company_id=1
        )
        
        # حذف Webhook
        success = webhook_service.delete_webhook(webhook_id, company_id=1)
        
        assert success == True
        
        # التحقق من الحذف
        webhook = webhook_service.get_webhook(webhook_id, company_id=1)
        assert webhook is None
    
    def test_build_payload_with_template(self, webhook_service):
        """اختبار بناء Payload مع Template"""
        webhook = Webhook(
            id=1,
            name="Test",
            url="https://example.com/webhook",
            event_type="sale_created",
            payload_template='{"event": "{event_type}", "webhook_id": {webhook_id}}'
        )
        
        event_payload = {"sale_id": 123, "amount": 100.0}
        
        final_payload = webhook_service._build_payload(webhook, event_payload)
        
        assert "event" in final_payload
        assert final_payload["sale_id"] == 123
        assert final_payload["amount"] == 100.0
    
    def test_build_payload_without_template(self, webhook_service):
        """اختبار بناء Payload بدون Template"""
        webhook = Webhook(
            id=1,
            name="Test",
            url="https://example.com/webhook",
            event_type="sale_created",
            payload_template=None
        )
        
        event_payload = {"sale_id": 123, "amount": 100.0}
        
        final_payload = webhook_service._build_payload(webhook, event_payload)
        
        assert final_payload == event_payload
    
    def test_trigger_webhook(self, webhook_service):
        """اختبار إطلاق Webhook"""
        # Mock Dispatcher
        mock_dispatcher = Mock()
        webhook_service.dispatcher = mock_dispatcher
        
        # إنشاء Webhook نشط
        webhook_id = webhook_service.create_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            event_type="sale_created",
            is_active=True,
            company_id=1
        )
        
        # إطلاق Webhook
        payload = {"sale_id": 123, "amount": 100.0}
        webhook_service.trigger_webhook(
            event_type="sale_created",
            payload=payload,
            entity_id=123,
            company_id=1
        )
        
        # التحقق من استدعاء Dispatcher
        assert mock_dispatcher.deliver_webhook.called
    
    def test_get_webhook_logs(self, webhook_service):
        """اختبار الحصول على سجلات Webhooks"""
        # إنشاء Webhook
        webhook_id = webhook_service.create_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            event_type="sale_created",
            company_id=1
        )
        
        # إضافة سجل تجريبي مباشرة
        webhook_service.db_manager.execute_query("""
            INSERT INTO webhook_logs (
                webhook_id, event_type, entity_id, payload,
                response_status, is_success, attempt_number, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            webhook_id,
            "sale_created",
            123,
            '{"sale_id": 123}',
            200,
            1,
            1,
            datetime.now().isoformat()
        ))
        
        # الحصول على السجلات
        logs = webhook_service.get_webhook_logs(webhook_id=webhook_id, company_id=1)
        
        assert len(logs) == 1
        assert logs[0].webhook_id == webhook_id
        assert logs[0].event_type == "sale_created"
        assert logs[0].is_success == True





