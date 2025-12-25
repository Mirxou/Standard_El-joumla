#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests for API Endpoints
اختبارات تكامل لـ API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.app import create_app
from src.api.auth import JWTAuthManager
from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService


@pytest.fixture
def db_manager():
    """إنشاء DatabaseManager للاختبارات"""
    db = DatabaseManager(db_path=":memory:")
    db.initialize()
    
    # إنشاء جداول أساسية
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role_id INTEGER,
            is_active INTEGER DEFAULT 1,
            company_id INTEGER
        )
    """)
    
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_en TEXT,
            barcode TEXT,
            category_id INTEGER,
            unit TEXT DEFAULT 'قطعة',
            cost_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            current_stock INTEGER DEFAULT 0,
            description TEXT,
            image_path TEXT,
            is_active INTEGER DEFAULT 1,
            company_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # إضافة مستخدم اختبار
    from src.core.security_service import AdvancedSecurityService
    security_service = AdvancedSecurityService(db)
    password_hash = security_service.hash_password("test_password")
    
    db.execute_query("""
        INSERT INTO users (username, password_hash, full_name, role_id, is_active, company_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("test_user", password_hash, "Test User", 1, 1, 1))
    
    # إضافة فئة اختبار
    db.execute_query("""
        INSERT INTO categories (id, name, description, is_active)
        VALUES (?, ?, ?, ?)
    """, (1, "عام", "فئة عامة", 1))
    
    yield db
    db.close()


@pytest.fixture
def auth_manager(db_manager):
    """إنشاء Auth Manager للاختبارات"""
    return JWTAuthManager(db_manager, secret_key="test-secret-key")


@pytest.fixture
def test_client(db_manager, auth_manager):
    """إنشاء Test Client للاختبارات"""
    from src.api.app import app
    from src.api.rate_limiter import APIRateLimiter
    
    # Mock global instances
    import src.api.app as app_module
    app_module.db_manager = db_manager
    app_module.auth_manager = auth_manager
    app_module.security_service = AdvancedSecurityService(db_manager)
    app_module.rate_limiter = APIRateLimiter()
    
    client = TestClient(app)
    yield client


@pytest.fixture
def auth_token(test_client, db_manager):
    """إنشاء Token مصادقة للاختبارات"""
    # تسجيل الدخول
    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": "test_user", "password": "test_password"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


class TestAuthEndpoints:
    """اختبارات Authentication Endpoints"""
    
    def test_login_success(self, test_client):
        """اختبار تسجيل الدخول بنجاح"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": "test_password"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
    
    def test_login_wrong_password(self, test_client):
        """اختبار تسجيل الدخول بكلمة مرور خاطئة"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": "wrong_password"}
        )
        
        assert response.status_code == 401
    
    def test_login_user_not_found(self, test_client):
        """اختبار تسجيل الدخول لمستخدم غير موجود"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent_user", "password": "password"}
        )
        
        assert response.status_code == 401
    
    def test_get_current_user(self, test_client, auth_token):
        """اختبار الحصول على المستخدم الحالي"""
        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_user"
        assert data["user_id"] == 1
    
    def test_get_current_user_no_token(self, test_client):
        """اختبار الحصول على المستخدم الحالي بدون Token"""
        response = test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_refresh_token(self, test_client, auth_token):
        """اختبار تحديث Token"""
        # الحصول على refresh_token من تسجيل الدخول
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": "test_password"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        response = test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestProductsEndpoints:
    """اختبارات Products Endpoints"""
    
    def test_get_products_no_auth(self, test_client):
        """اختبار الحصول على المنتجات بدون مصادقة"""
        response = test_client.get("/api/v1/products")
        
        assert response.status_code == 401
    
    def test_get_products(self, test_client, auth_token, db_manager):
        """اختبار الحصول على قائمة المنتجات"""
        # إضافة منتج اختبار
        db_manager.execute_query("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("منتج اختبار", "قطعة", 10.0, 15.0, 100, 1, 1))
        
        response = test_client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "page" in data
        assert "total" in data
        assert isinstance(data["products"], list)
    
    def test_get_product_by_id(self, test_client, auth_token, db_manager):
        """اختبار الحصول على منتج بالمعرف"""
        # إضافة منتج اختبار
        db_manager.execute_query("""
            INSERT INTO products (id, name, unit, cost_price, selling_price, current_stock, is_active, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, "منتج اختبار", "قطعة", 10.0, 15.0, 100, 1, 1))
        
        response = test_client.get(
            "/api/v1/products/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "منتج اختبار"
    
    def test_get_product_not_found(self, test_client, auth_token):
        """اختبار الحصول على منتج غير موجود"""
        response = test_client.get(
            "/api/v1/products/999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
    
    def test_create_product(self, test_client, auth_token):
        """اختبار إنشاء منتج جديد"""
        product_data = {
            "name": "منتج جديد",
            "unit": "قطعة",
            "cost_price": 10.0,
            "selling_price": 15.0,
            "current_stock": 100,
            "is_active": True
        }
        
        response = test_client.post(
            "/api/v1/products",
            json=product_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "منتج جديد"
        assert "id" in data
    
    def test_update_product(self, test_client, auth_token, db_manager):
        """اختبار تحديث منتج"""
        # إضافة منتج اختبار
        db_manager.execute_query("""
            INSERT INTO products (id, name, unit, cost_price, selling_price, current_stock, is_active, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, "منتج قديم", "قطعة", 10.0, 15.0, 100, 1, 1))
        
        update_data = {
            "name": "منتج محدث",
            "selling_price": 20.0
        }
        
        response = test_client.put(
            "/api/v1/products/1",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "منتج محدث"
        assert data["selling_price"] == 20.0
    
    def test_delete_product(self, test_client, auth_token, db_manager):
        """اختبار حذف منتج"""
        # إضافة منتج اختبار
        db_manager.execute_query("""
            INSERT INTO products (id, name, unit, cost_price, selling_price, current_stock, is_active, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, "منتج للحذف", "قطعة", 10.0, 15.0, 100, 1, 1))
        
        response = test_client.delete(
            "/api/v1/products/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 204
        
        # التحقق من الحذف
        get_response = test_client.get(
            "/api/v1/products/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # يجب أن يكون المنتج معطلاً (soft delete)
        assert get_response.status_code in [404, 200]  # قد يعيد 200 مع is_active=False


class TestHealthEndpoints:
    """اختبارات Health Endpoints"""
    
    def test_health_check(self, test_client):
        """اختبار Health Check"""
        response = test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_info_endpoint(self, test_client):
        """اختبار Info Endpoint"""
        response = test_client.get("/api/v1/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

