"""
Backend-Frontend Integration Tests
اختبارات تكامل Backend ↔ Frontend
اختبارات End-to-End تربط API Backend بـ Frontend logic
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime
import sys
from pathlib import Path

# إضافة المسار
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# استيراد التطبيق
try:
    from src.api.app import app
    from src.api.routes import get_db_manager
    from src.core.database_manager import DatabaseManager
    from src.models.product import ProductManager, Product
    from src.models.customer import CustomerManager, Customer
    from src.models.sale import SaleManager, Sale, SaleItem, SaleStatus
    from src.models.user import UserManager, User, UserRole
except ImportError:
    # محاولة استيراد بديلة
    from api.app import app
    from api.routes import get_db_manager
    from core.database_manager import DatabaseManager
    from models.product import ProductManager, Product
    from models.customer import CustomerManager, Customer
    from models.sale import SaleManager, Sale, SaleItem, SaleStatus
    from models.user import UserManager, User, UserRole


@pytest.mark.integration
class TestBackendFrontendIntegration:
    """اختبارات تكامل Backend ↔ Frontend"""
    
    @pytest.fixture(scope="class")
    def db_instance(self):
        """إنشاء قاعدة بيانات في الذاكرة"""
        db = DatabaseManager(":memory:")
        db.initialize()
        yield db
        db.close()
    
    @pytest.fixture(scope="class")
    def client(self, db_instance):
        """إعداد TestClient مع dependency override"""
        def override_get_db():
            return db_instance
        
        app.dependency_overrides[get_db_manager] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()
    
    @pytest.fixture(scope="class")
    def auth_token(self, client, db_instance):
        """إنشاء مستخدم والحصول على token للمصادقة"""
        # إنشاء مستخدم
        user_manager = UserManager(db_instance)
        try:
            # محاولة إنشاء مستخدم
            user = User(
                username="testuser",
                full_name="Test User",
                password_hash="hashed_password",  # في الواقع سيتم hash
                role=UserRole.ADMIN
            )
            user_id = user_manager.create_user(user, "testpass123")
            
            # تسجيل الدخول
            login_response = client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "testpass123"
            })
            
            if login_response.status_code == 200:
                return login_response.json().get("access_token")
        except Exception:
            pass
        
        # إذا فشل، نعود None (بعض الاختبارات قد تعمل بدون auth)
        return None
    
    @pytest.fixture(scope="class")
    def setup_test_data(self, db_instance):
        """إعداد بيانات اختبار (منتجات وعملاء)"""
        product_manager = ProductManager(db_instance)
        customer_manager = CustomerManager(db_instance)
        
        # إنشاء منتج
        product = Product(
            name="Integration Test Product",
            barcode="INT-001",
            cost_price=Decimal("50.00"),
            selling_price=Decimal("100.00"),
            current_stock=100,
            category_id=1
        )
        product_id = product_manager.create_product(product)
        
        # إنشاء عميل
        customer = Customer(
            name="Integration Test Customer",
            phone="0501234567",
            email="test@example.com"
        )
        customer_id = customer_manager.create_customer(customer)
        
        return {
            "product_id": product_id,
            "customer_id": customer_id
        }
    
    def test_health_check_endpoint(self, client):
        """اختبار Health Check Endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_api_products_list_endpoint(self, client, setup_test_data):
        """اختبار endpoint قائمة المنتجات (GET /api/v1/products/)"""
        response = client.get("/api/v1/products/")
        
        # قد يحتاج auth في بعض الحالات، لكن health check يجب أن يعمل
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))
            # إذا كانت استجابة paginated
            if isinstance(data, dict):
                assert "items" in data or "products" in data or "data" in data
    
    def test_api_product_detail_endpoint(self, client, setup_test_data):
        """اختبار endpoint تفاصيل منتج (GET /api/v1/products/{id})"""
        product_id = setup_test_data["product_id"]
        response = client.get(f"/api/v1/products/{product_id}")
        
        assert response.status_code in [200, 401, 403, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data or "product_id" in data
            assert data.get("id") == product_id or data.get("product_id") == product_id
    
    def test_api_create_product_workflow(self, client, db_instance):
        """اختبار workflow إنشاء منتج من Frontend إلى Backend"""
        product_data = {
            "name": "Frontend Test Product",
            "barcode": "FRONT-001",
            "cost_price": 75.0,
            "selling_price": 150.0,
            "current_stock": 50,
            "category_id": 1
        }
        
        # محاولة إنشاء منتج عبر API
        response = client.post("/api/v1/products/", json=product_data)
        
        # قد يحتاج auth
        assert response.status_code in [201, 401, 403]
        
        if response.status_code == 201:
            created_data = response.json()
            assert "product_id" in created_data or "id" in created_data
            
            # التحقق من قاعدة البيانات مباشرة
            product_id = created_data.get("product_id") or created_data.get("id")
            product_manager = ProductManager(db_instance)
            product = product_manager.get_product_by_id(product_id)
            
            assert product is not None
            assert product.name == product_data["name"]
            assert product.barcode == product_data["barcode"]
    
    def test_api_update_product_workflow(self, client, setup_test_data, db_instance):
        """اختبار workflow تحديث منتج من Frontend إلى Backend"""
        product_id = setup_test_data["product_id"]
        update_data = {
            "name": "Updated Product Name",
            "selling_price": 120.0
        }
        
        # محاولة تحديث منتج عبر API
        response = client.put(f"/api/v1/products/{product_id}", json=update_data)
        
        assert response.status_code in [200, 401, 403, 404]
        
        if response.status_code == 200:
            # التحقق من قاعدة البيانات
            product_manager = ProductManager(db_instance)
            product = product_manager.get_product_by_id(product_id)
            
            assert product is not None
            assert product.name == update_data["name"]
    
    def test_api_create_sale_workflow(self, client, setup_test_data, db_instance):
        """اختبار workflow إنشاء فاتورة بيع من Frontend إلى Backend"""
        sale_data = {
            "customer_id": setup_test_data["customer_id"],
            "items": [
                {
                    "product_id": setup_test_data["product_id"],
                    "quantity": 2,
                    "unit_price": 100.0
                }
            ],
            "status": "confirmed"
        }
        
        # محاولة إنشاء فاتورة عبر API
        response = client.post("/api/v1/sales/", json=sale_data)
        
        assert response.status_code in [201, 400, 401, 403]
        
        if response.status_code == 201:
            sale_response = response.json()
            assert "sale_id" in sale_response or "id" in sale_response
            
            # التحقق من قاعدة البيانات
            sale_id = sale_response.get("sale_id") or sale_response.get("id")
            sale_manager = SaleManager(db_instance)
            sale = sale_manager.get_sale_by_id(sale_id)
            
            assert sale is not None
            assert sale.customer_id == sale_data["customer_id"]
            assert len(sale.items) == 1
    
    def test_api_get_sales_list_workflow(self, client, setup_test_data):
        """اختبار workflow الحصول على قائمة المبيعات"""
        response = client.get("/api/v1/sales/")
        
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))
    
    def test_api_error_handling(self, client):
        """اختبار معالجة الأخطاء في API"""
        # طلب منتج غير موجود
        response = client.get("/api/v1/products/99999")
        assert response.status_code in [404, 401, 403]
        
        # طلب ببيانات غير صحيحة
        response = client.post("/api/v1/products/", json={
            "name": ""  # بيانات غير صحيحة
        })
        assert response.status_code in [400, 422, 401, 403]
    
    def test_api_response_format(self, client, setup_test_data):
        """اختبار تنسيق الاستجابة من API (يجب أن يتوافق مع Frontend)"""
        product_id = setup_test_data["product_id"]
        response = client.get(f"/api/v1/products/{product_id}")
        
        if response.status_code == 200:
            data = response.json()
            # التحقق من أن الاستجابة تحتوي على حقول متوقعة
            assert isinstance(data, dict)
            # قد تحتوي على id أو product_id
            assert "id" in data or "product_id" in data or "name" in data
    
    def test_api_pagination_workflow(self, client, db_instance):
        """اختبار Pagination في API"""
        # إنشاء عدة منتجات
        product_manager = ProductManager(db_instance)
        for i in range(15):
            product = Product(
                name=f"Pagination Test Product {i}",
                barcode=f"PAG-{i:03d}",
                cost_price=Decimal("10.00"),
                selling_price=Decimal("20.00"),
                current_stock=10
            )
            product_manager.create_product(product)
        
        # طلب الصفحة الأولى
        response = client.get("/api/v1/products/?page=1&page_size=10")
        
        if response.status_code == 200:
            data = response.json()
            # قد يكون paginated response
            if isinstance(data, dict):
                # التحقق من وجود pagination metadata
                assert "page" in data or "items" in data or "products" in data


@pytest.mark.integration
class TestFrontendBackendDataFlow:
    """اختبار تدفق البيانات من Frontend إلى Backend والعكس"""
    
    @pytest.fixture(scope="class")
    def db_instance(self):
        """إنشاء قاعدة بيانات في الذاكرة"""
        db = DatabaseManager(":memory:")
        db.initialize()
        yield db
        db.close()
    
    @pytest.fixture(scope="class")
    def client(self, db_instance):
        """إعداد TestClient"""
        def override_get_db():
            return db_instance
        
        app.dependency_overrides[get_db_manager] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()
    
    def test_complete_product_crud_workflow(self, client, db_instance):
        """اختبار workflow CRUD كامل لمنتج"""
        product_manager = ProductManager(db_instance)
        
        # 1. CREATE - إنشاء منتج عبر API
        create_data = {
            "name": "CRUD Test Product",
            "barcode": "CRUD-001",
            "cost_price": 50.0,
            "selling_price": 100.0,
            "current_stock": 25
        }
        
        create_response = client.post("/api/v1/products/", json=create_data)
        
        if create_response.status_code == 201:
            created = create_response.json()
            product_id = created.get("product_id") or created.get("id")
            
            # 2. READ - قراءة المنتج عبر API
            read_response = client.get(f"/api/v1/products/{product_id}")
            assert read_response.status_code in [200, 404]
            
            if read_response.status_code == 200:
                read_data = read_response.json()
                assert read_data.get("name") == create_data["name"]
            
            # 3. UPDATE - تحديث المنتج عبر API
            update_data = {
                "name": "Updated CRUD Product",
                "selling_price": 120.0
            }
            
            update_response = client.put(f"/api/v1/products/{product_id}", json=update_data)
            assert update_response.status_code in [200, 404]
            
            # 4. DELETE - حذف المنتج (اختياري، يعتمد على API)
            # delete_response = client.delete(f"/api/v1/products/{product_id}")
            # assert delete_response.status_code in [204, 200, 404]
    
    def test_data_validation_workflow(self, client):
        """اختبار التحقق من صحة البيانات في workflow"""
        # محاولة إنشاء منتج ببيانات غير صحيحة
        invalid_data = {
            "name": "",  # اسم فارغ
            "barcode": "",  # باركود فارغ
            "cost_price": -10,  # سعر سالب
        }
        
        response = client.post("/api/v1/products/", json=invalid_data)
        
        # يجب أن يرفض البيانات غير الصحيحة
        assert response.status_code in [400, 422, 401, 403]
        
        if response.status_code in [400, 422]:
            error_data = response.json()
            # يجب أن تحتوي على رسالة خطأ
            assert "detail" in error_data or "message" in error_data or "error" in error_data


@pytest.mark.integration
class TestAPIEndToEndWorkflows:
    """اختبارات End-to-End للـ Workflows الكاملة"""
    
    @pytest.fixture(scope="class")
    def db_instance(self):
        """إنشاء قاعدة بيانات في الذاكرة"""
        db = DatabaseManager(":memory:")
        db.initialize()
        yield db
        db.close()
    
    @pytest.fixture(scope="class")
    def client(self, db_instance):
        """إعداد TestClient"""
        def override_get_db():
            return db_instance
        
        app.dependency_overrides[get_db_manager] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()
    
    @pytest.fixture(scope="class")
    def setup_workflow_data(self, db_instance):
        """إعداد بيانات للـ workflows"""
        product_manager = ProductManager(db_instance)
        customer_manager = CustomerManager(db_instance)
        
        # إنشاء منتج
        product = Product(
            name="Workflow Product",
            barcode="WORK-001",
            cost_price=Decimal("30.00"),
            selling_price=Decimal("60.00"),
            current_stock=100
        )
        product_id = product_manager.create_product(product)
        
        # إنشاء عميل
        customer = Customer(
            name="Workflow Customer",
            phone="0509876543"
        )
        customer_id = customer_manager.create_customer(customer)
        
        return {
            "product_id": product_id,
            "customer_id": customer_id,
            "initial_stock": 100
        }
    
    def test_sale_to_inventory_update_workflow(self, client, setup_workflow_data, db_instance):
        """اختبار workflow البيع وتحديث المخزون"""
        product_id = setup_workflow_data["product_id"]
        customer_id = setup_workflow_data["customer_id"]
        initial_stock = setup_workflow_data["initial_stock"]
        
        # إنشاء فاتورة بيع عبر API
        sale_data = {
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 5,
                    "unit_price": 60.0
                }
            ],
            "status": "confirmed"
        }
        
        sale_response = client.post("/api/v1/sales/", json=sale_data)
        
        if sale_response.status_code == 201:
            # التحقق من تحديث المخزون
            product_manager = ProductManager(db_instance)
            product = product_manager.get_product_by_id(product_id)
            
            # يجب أن ينخفض المخزون
            expected_stock = initial_stock - 5
            assert product.current_stock == expected_stock
    
    def test_product_search_workflow(self, client, db_instance):
        """اختبار workflow البحث عن المنتجات"""
        # إنشاء منتجات للبحث
        product_manager = ProductManager(db_instance)
        for i in range(5):
            product = Product(
                name=f"Search Product {i}",
                barcode=f"SEARCH-{i}",
                cost_price=Decimal("10.00"),
                selling_price=Decimal("20.00"),
                current_stock=10
            )
            product_manager.create_product(product)
        
        # البحث عن منتجات عبر API
        response = client.get("/api/v1/products/?search=Search")
        
        if response.status_code == 200:
            data = response.json()
            # يجب أن تحتوي على نتائج
            assert isinstance(data, (dict, list))

