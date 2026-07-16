"""
Unit Tests for API Modules
اختبارات وحدة لوحدات API
"""

from src.api.api_client import APIClient, HybridDataService
from src.api.integration_models import (
    AccountingWebhookPayload,
    PaymentWebhookPayload,
    SMSNotificationPayload,
)


class TestAPIClient:
    """اختبارات APIClient"""

    def test_api_client_init(self):
        """اختبار تهيئة APIClient"""
        client = APIClient(base_url="https://api.example.com")
        assert client.base_url == "https://api.example.com"
        assert client.timeout == 5

    def test_api_client_is_online(self):
        """اختبار التحقق من حالة الاتصال"""
        client = APIClient(base_url="https://httpbin.org")
        # قد يكون متصلاً أو غير متصل حسب الاتصال بالإنترنت
        is_online = client.is_online()
        assert isinstance(is_online, bool)

    def test_hybrid_data_service_init(self, db_manager):
        """اختبار تهيئة HybridDataService"""
        api_client = APIClient(base_url="https://api.example.com")
        service = HybridDataService(db_manager, api_client)
        assert service.db is not None
        assert service.api is not None


class TestIntegrationModels:
    """اختبارات IntegrationModels"""

    def test_accounting_webhook_payload(self):
        """اختبار AccountingWebhookPayload"""
        payload = AccountingWebhookPayload(invoice_id=1, amount=1000.0, customer="Test Customer", date="2024-01-01")
        assert payload.invoice_id == 1
        assert payload.amount == 1000.0
        assert payload.customer == "Test Customer"

    def test_payment_webhook_payload(self):
        """اختبار PaymentWebhookPayload"""
        payload = PaymentWebhookPayload(order_id=1, status="paid", amount=500.0, payment_method="cash")
        assert payload.order_id == 1
        assert payload.status == "paid"
        assert payload.amount == 500.0

    def test_sms_notification_payload(self):
        """اختبار SMSNotificationPayload"""
        payload = SMSNotificationPayload(to="+1234567890", message="Test message")
        assert payload.to == "+1234567890"
        assert payload.message == "Test message"
