from decimal import Decimal

# ضبط المسار لاستيراد التطبيق الرئيسي
from pathlib import Path  # noqa: F811

import pytest
from fastapi.testclient import TestClient

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
# 🔥 FIX: استيراد كائن FastAPI من المكان الصحيح (api.app) وليس من main.py
from src.api.app import app
from src.api.routes import (  # noqa: F401
    get_db_manager,
)  # الدالة التي تحقن قاعدة البيانات في الـ Routes
from src.core.database_manager import DatabaseManager
from src.models.customer import Customer, CustomerManager
from src.models.product import Product, ProductManager


class TestApiSalesFlow:
    """
    اختبار تكامل لطبقة API (End-to-End HTTP Test).
    يحاكي طلبات حقيقية من عميل (مثل تطبيق جوال).
    """

    @pytest.fixture(scope="module")
    def db_instance(self):
        """إنشاء قاعدة بيانات في الذاكرة للاختبار"""
        db = DatabaseManager(":memory:")
        db.initialize()
        yield db
        db.close()

    @pytest.fixture(scope="module")
    def client(self, db_instance):
        """إعداد TestClient مع monkeypatching"""
        from src.api import app as api_app
        from src.api.routes import get_db_manager  # noqa: F811

        old_db = api_app.db_manager
        old_auth_db = api_app.auth_manager.db_manager
        old_secret = api_app.auth_manager.secret_key

        api_app.db_manager = db_instance
        api_app.auth_manager.db_manager = db_instance
        api_app.auth_manager.secret_key = "test-secret-key-12345"

        def override_get_db():
            return db_instance

        app.dependency_overrides[get_db_manager] = override_get_db

        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()
        api_app.db_manager = old_db
        api_app.auth_manager.db_manager = old_auth_db
        api_app.auth_manager.secret_key = old_secret

    @pytest.fixture(scope="module")
    def auth_token(self, client, db_instance):
        """الحصول على Token للمصادقة"""
        from src.api.app import auth_manager
        from src.models.user import User, UserManager, UserRole

        user_manager = UserManager(db_instance)
        username, password = "sales_user", "pass123"
        user = user_manager.get_user_by_username(username)
        if not user:
            user = User(username=username, full_name="Sales User", role=UserRole.ADMIN.value)
            user_manager.create_user(user, password)

        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json().get("access_token")

        user = user_manager.get_user_by_username(username)
        return auth_manager.create_access_token(user_id=user.id, username=user.username)

    @pytest.fixture(scope="module")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}

    @pytest.fixture(scope="module")
    def setup_data(self, db_instance):
        """تجهيز بيانات أولية (منتج وعميل) ليكون الطلب صحيحاً"""
        pm = ProductManager(db_instance)
        cm = CustomerManager(db_instance)

        # 1. إنشاء منتج
        prod_id = pm.create_product(
            Product(
                name="API Test Product",
                barcode="API-123",
                cost_price=Decimal("50"),
                selling_price=Decimal("100"),
                current_stock=100,
                category_id=1,
            )
        )

        # 2. إنشاء عميل
        cust_id = cm.create_customer(Customer(name="API Client User", phone="999888777"))

        return {"product_id": prod_id, "customer_id": cust_id}

    def test_create_sale_endpoint_success(self, client, setup_data, auth_headers):
        """
        السيناريو السعيد: إرسال JSON صحيح لإنشاء فاتورة واستلام 201 Created.
        """
        payload = {
            "customer_id": setup_data["customer_id"],
            "items": [
                {
                    "product_id": setup_data["product_id"],
                    "quantity": 2,
                    "unit_price": 100.0,
                }
            ],
            "status": "confirmed",
        }

        # إرسال طلب POST مع headers المصادقة
        response = client.post("/api/v1/sales/", json=payload, headers=auth_headers)

        # التحقق من الاستجابة
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        assert "id" in data or "sale_id" in data
        # data["success"] might not be present in the new response model, checking status_code is enough
        # but if we want to be sure:
        if "success" in data:
            assert data["success"] is True

    def test_create_sale_endpoint_invalid_data(self, client, auth_headers):
        """
        سيناريو الفشل: إرسال بيانات ناقصة والتحقق من أن الـ API يرفضها.
        """
        payload = {"customer_id": 9999, "items": []}

        response = client.post("/api/v1/sales/", json=payload, headers=auth_headers)
        assert response.status_code == 422
