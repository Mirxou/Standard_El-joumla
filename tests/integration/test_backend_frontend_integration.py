"""
Backend-Frontend Integration Tests
اختبارات تكامل Backend ↔ Frontend
اختبارات End-to-End تربط API Backend بـ Frontend logic
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

# FORCE Environment Variable for tests
os.environ["JWT_SECRET_KEY"] = "test-secret-key-12345"

from src.api.app import app
from src.api.routes import get_auth_manager, get_db_manager
from src.core.database_manager import DatabaseManager
from src.models.customer import Customer, CustomerManager
from src.models.product import Product, ProductManager
from src.models.user import User, UserManager, UserRole


@pytest.mark.integration
class TestIntegrationBase:
    """قاعدة اختبارات التكامل - تحتوي على fixtures مشتركة"""

    @pytest.fixture(scope="class")
    def db_instance(self):
        """إنشاء قاعدة بيانات في الذاكرة"""
        db = DatabaseManager(":memory:")
        db.initialize()
        yield db
        db.close()

    @pytest.fixture(scope="class")
    def client(self, db_instance):
        """إعداد TestClient مع monkeypatching للـ global managers"""
        from src.api import app as api_app

        # حفظ القيم الأصلية
        old_db = api_app.db_manager
        old_auth_db = api_app.auth_manager.db_manager
        old_secret = api_app.auth_manager.secret_key

        # تحديث القيم لخدمة التست
        test_secret = "test-secret-key-12345"
        api_app.db_manager = db_instance
        api_app.auth_manager.db_manager = db_instance
        api_app.auth_manager.secret_key = test_secret

        def override_get_db():
            return db_instance

        def override_get_auth():
            return api_app.auth_manager

        app.dependency_overrides[get_db_manager] = override_get_db
        app.dependency_overrides[get_auth_manager] = override_get_auth

        with TestClient(app) as c:
            yield c

        # استعادة القيم الأصلية
        app.dependency_overrides.clear()
        api_app.db_manager = old_db
        api_app.auth_manager.db_manager = old_auth_db
        api_app.auth_manager.secret_key = old_secret

    @pytest.fixture(scope="class")
    def auth_token(self, client, db_instance):
        """إنشاء مستخدم والحصول على token للمصادقة"""
        from src.api.app import auth_manager

        user_manager = UserManager(db_instance)

        username = "integration_user"
        password = "testpass123"

        user = user_manager.get_user_by_username(username)
        if not user:
            user_manager.create_user(User(username=username, role=UserRole.ADMIN.value), password)
            user = user_manager.get_user_by_username(username)

        # محاولة الحصول على Token عبر الـ API أولاً للتأكد من أن الـ Login Endpoint يعمل
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json().get("access_token")

        # Fallback: إنشاء Token مباشرة باستخدام auth_manager
        return auth_manager.create_access_token(user_id=user.id, username=user.username)

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """رأس المصادقة"""
        if auth_token:
            return {"Authorization": f"Bearer {auth_token}"}
        return {}


class TestBackendFrontendIntegration(TestIntegrationBase):
    """اختبارات تكامل Backend ↔ Frontend"""

    @pytest.fixture(scope="class")
    def setup_test_data(self, db_instance):
        product_manager = ProductManager(db_instance)
        customer_manager = CustomerManager(db_instance)

        product_id = product_manager.create_product(
            Product(
                name="Integration Test Product",
                barcode="INT-001",
                cost_price=Decimal("50.00"),
                selling_price=Decimal("100.00"),
                current_stock=100,
                category_id=1,
            )
        )

        customer_id = customer_manager.create_customer(
            Customer(
                name="Integration Test Customer",
                phone="0501234567",
                email="test@example.com",
            )
        )

        return {"product_id": product_id, "customer_id": customer_id}

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_products_list(self, client, setup_test_data, auth_headers):
        response = client.get("/api/v1/products/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))

    def test_api_product_detail(self, client, setup_test_data, auth_headers):
        product_id = setup_test_data["product_id"]
        response = client.get(f"/api/v1/products/{product_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == product_id

    def test_api_create_product_workflow(self, client, db_instance, auth_headers):
        product_data = {
            "name": "Frontend Test Product",
            "barcode": "FRONT-001",
            "cost_price": 75.0,
            "selling_price": 150.0,
            "current_stock": 50,
            "category_id": 1,
        }
        response = client.post("/api/v1/products/", json=product_data, headers=auth_headers)
        assert response.status_code == 201

        # التحقق من قاعدة البيانات
        pm = ProductManager(db_instance)
        pid = response.json().get("product_id") or response.json().get("id")
        product = pm.get_product_by_id(pid)
        assert product is not None
        assert product.name == product_data["name"]


class TestAPIEndToEndWorkflows(TestIntegrationBase):
    """اختبارات End-to-End للـ Workflows الكاملة"""

    def test_sale_to_inventory_workflow(self, client, db_instance, auth_headers):
        pm = ProductManager(db_instance)
        cm = CustomerManager(db_instance)

        pid = pm.create_product(
            Product(
                name="Workflow P",
                barcode="W-1",
                cost_price=Decimal("10"),
                selling_price=Decimal("20"),
                current_stock=100,
            )
        )
        cid = cm.create_customer(Customer(name="Workflow C", phone="123"))

        sale_data = {
            "customer_id": cid,
            "items": [{"product_id": pid, "quantity": 10, "unit_price": 20.0}],
            "status": "confirmed",
        }

        response = client.post("/api/v1/sales/", json=sale_data, headers=auth_headers)
        assert response.status_code == 201

        # التحقق من تحديث المخزون
        product = pm.get_product_by_id(pid)
        assert product.current_stock == 90

    def test_product_search_workflow(self, client, db_instance, auth_headers):
        pm = ProductManager(db_instance)
        pm.create_product(
            Product(
                name="Search Me",
                barcode="S-1",
                cost_price=Decimal("10"),
                selling_price=Decimal("20"),
                current_stock=10,
            )
        )

        response = client.get("/api/v1/products/?search=Search", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # التحقق من وجود نتائج (سواء كانت قائمة أو كائن يحتوي على قائمة)
        if isinstance(data, list):
            assert len(data) > 0
        else:
            assert len(data.get("products", [])) > 0 or len(data.get("items", [])) > 0 or data.get("total", 0) > 0
