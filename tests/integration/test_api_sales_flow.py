import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
import sys
from pathlib import Path

# ضبط المسار لاستيراد التطبيق الرئيسي
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# 🔥 FIX: استيراد كائن FastAPI من المكان الصحيح (api.app) وليس من main.py
from api.app import app
from core.database_manager import DatabaseManager
from api.routes import get_db_manager # الدالة التي تحقن قاعدة البيانات في الـ Routes
from models.product import ProductManager, Product
from models.customer import CustomerManager, Customer

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
        """
        إعداد TestClient مع استبدال قاعدة البيانات الحقيقية بقاعدة بيانات الذاكرة.
        هذا يسمى Dependency Override في FastAPI.
        """
        def override_get_db():
            return db_instance

        app.dependency_overrides[get_db_manager] = override_get_db
        with TestClient(app) as c:
            yield c
        # تنظيف الـ override بعد الانتهاء
        app.dependency_overrides.clear()

    @pytest.fixture(scope="module")
    def setup_data(self, db_instance):
        """تجهيز بيانات أولية (منتج وعميل) ليكون الطلب صحيحاً"""
        pm = ProductManager(db_instance)
        cm = CustomerManager(db_instance)

        # 1. إنشاء منتج
        prod_id = pm.create_product(Product(
            name="API Test Product",
            barcode="API-123",
            cost_price=Decimal("50"),
            selling_price=Decimal("100"),
            current_stock=100, # 🔥 FIX: إضافة المخزون هنا مباشرة
            category_id=1
        ))

        # 2. إنشاء عميل
        cust_id = cm.create_customer(Customer(name="API Client User", phone="999888777"))

        return {"product_id": prod_id, "customer_id": cust_id}

    def test_create_sale_endpoint_success(self, client, setup_data):
        """
        السيناريو السعيد: إرسال JSON صحيح لإنشاء فاتورة واستلام 201 Created.
        """
        payload = {
            "customer_id": setup_data["customer_id"],
            "items": [
                {
                    "product_id": setup_data["product_id"],
                    "quantity": 2,
                    "unit_price": 100.0 # السعر الذي سيتم البيع به
                }
            ],
            "status": "confirmed"
        }

        # إرسال طلب POST
        # 🔥 FIX: التأكد من أن الـ URL صحيح (نفترض أنه /api/v1/sales/)
        response = client.post("/api/v1/sales/", json=payload)

        # التحقق من الاستجابة
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "sale_id" in data
        assert data["success"] is True
        assert data["total_amount"] == 200.0

    def test_create_sale_endpoint_invalid_data(self, client):
        """
        سيناريو الفشل: إرسال بيانات ناقصة والتحقق من أن الـ API يرفضها (422 Unprocessable Entity).
        """
        payload = {
            "customer_id": 9999, # عميل غير موجود
            "items": [] # قائمة فارغة (غير مسموح بها)
        }

        response = client.post("/api/v1/sales/", json=payload)
        
        # FastAPI يعيد 422 تلقائياً عند فشل التحقق من صحة البيانات (Pydantic Validation)
        assert response.status_code == 422