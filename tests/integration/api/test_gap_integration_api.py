#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GAP Integration API Tests — اختبارات تكامل الـ API للخدمات الجديدة (Task 3-a)

يغطي ربط الخدمات المبنية حديثاً بطبقة FastAPI:
    - مرتجعات المشتريات (PurchaseReturnService): دورة كاملة + أخطاء قواعد العمل (422)
    - طابعة الإيصالات ESC/POS (طباعة إيصال بعد البيع + معاينة نصية، dry_run بدون عتاد)
    - درج النقدية (فتح + حالة)
    - تقارير X/Z للورديات (من تسوية SalesService الموجودة)
    - الباركود (ربط + قراءة ممسوحة + تعارض 422 + ملصق مع معاينة)
    - LAN discovery + Sync flush (تدهور رشيق)
    - المصادقة: الـ API يفرض Bearer Token عبر AuthMiddleware (401 بدون توكن)

نمط التهيئة منسوخ من tests/integration/test_backend_frontend_integration.py:
    استبدال api_app.db_manager + auth_manager بقاعدة مؤقتة وOverride لـ get_db_manager
    ثم تسجيل الدخول الحقيقي عبر /api/v1/auth/login.
"""

import os

# ⚠️ يجب ضبط JWT_SECRET_KEY قبل أي استيراد لـ src.api.app (≥ 32 حرفاً)
os.environ["JWT_SECRET_KEY"] = "test-secret-key-gap-integration-0123456789abcdef"

from decimal import Decimal

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.routes import get_current_user, get_db_manager  # noqa: F401
from src.core.database_manager import DatabaseManager
from src.models.product import Product, ProductManager
from src.models.user import User, UserManager, UserRole

API = "/api/v1"


class TestGapIntegrationAPI:
    """اختبارات تكامل الـ API للخدمات الجديدة — Task 3-a"""

    # ──────────────────── البنية التحتية (نفس نمط الأشقاء) ────────────────────

    @pytest.fixture(scope="class")
    def db_instance(self, tmp_path_factory):
        """قاعدة بيانات SQLite مؤقتة على القرص (آمنة عبر خيوط TestClient)

        نعطّل ConnectionPool صراحةً: مع الملفات يُنشئ initialize() مسبباً اتصالات
        متعددة، وSaleManager.create_sale يكتب عبر db_manager.connection المشترك
        بينما transaction() يأخذ اتصال pool آخر (BEGIN IMMEDIATE) → 'database
        is locked'. تعطيل الـ pool يجعل مسار الاتصال الواحد (نفس مسار :memory:
        المستخدم في اختبارات الأشقاء).
        """
        db_path = str(tmp_path_factory.mktemp("gap_api") / "gap_test.db")
        db = DatabaseManager(db_path=db_path)
        db._pool_options = {"enabled": False}
        db.initialize()
        yield db
        db.close()

    @pytest.fixture(scope="class")
    def client(self, db_instance):
        """TestClient مع استبدال db_manager وتشغيل الـ lifespan (هجرات + فئات افتراضية)

        نستبدل أيضاً db داخل security_service/permission_manager للـ auth_manager
        لأنها تُبنى على المدير الأصلي وقت الاستيراد — بدون ذلك تفشل المصادقة
        على قاعدة مؤقتة ('NoneType' object has no attribute 'cursor').
        """
        from src.api import app as api_app

        old_db = api_app.db_manager
        old_auth_db = api_app.auth_manager.db_manager
        old_secret = api_app.auth_manager.secret_key
        old_security_db = api_app.auth_manager.security_service.db
        old_permission_db = api_app.auth_manager.permission_manager.db

        api_app.db_manager = db_instance
        api_app.auth_manager.db_manager = db_instance
        api_app.auth_manager.secret_key = "test-secret-key-gap-integration-0123456789abcdef"
        api_app.auth_manager.security_service.db = db_instance
        api_app.auth_manager.permission_manager.db = db_instance

        def override_get_db():
            return db_instance

        # بعض ملفات الاختبار الأخرى تضع override عاماً لـ get_current_user على
        # مستوى الموديول (test_sync_api.py) يُتسرب لبقية الملفات في نفس جلسة
        # pytest — نزيله ليعمل مسار المصادقة الحقيقي (AuthMiddleware → state)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_db_manager] = override_get_db

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()
        api_app.db_manager = old_db
        api_app.auth_manager.db_manager = old_auth_db
        api_app.auth_manager.secret_key = old_secret
        api_app.auth_manager.security_service.db = old_security_db
        api_app.auth_manager.permission_manager.db = old_permission_db

    @pytest.fixture(scope="class")
    def auth_headers(self, client, db_instance):
        """تسجيل دخول حقيقي عبر /auth/login (نفس أسلوب الأشقاء)"""
        user_manager = UserManager(db_instance)
        username, password = "gap_api_admin", "gap-pass-123"  # TEST ONLY

        user = user_manager.get_user_by_username(username)
        if not user:
            user_manager.create_user(
                User(username=username, full_name="Gap API Admin", role=UserRole.ADMIN.value),
                password,
            )
            user = user_manager.get_user_by_username(username)
        assert user is not None, "فشل إنشاء مستخدم الاختبار"

        response = client.post(f"{API}/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200, response.text
        token = response.json().get("access_token")
        assert token, "لم يُرجع الـ login أي access_token"
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture(scope="class")
    def seeded(self, client, db_instance):
        """بيانات أولية: منتج + مورد + فاتورة شراء + دفعة مخزون (للمرتجعات والباركود)

        - فاتورة الشراء تُزرع عبر SQL مباشر (نفس أنماط تهيئة اختبارات الخدمة) —
          اختبارنا يستهدف طبقة مرتجعات المشتريات لا endpoint إنشاء المشتريات.
        - الدفعة مطلوبة: الموافقة تعين الدفعات FEFO-عكسي من batches.
        """
        pm = ProductManager(db_instance)
        product_id = pm.create_product(
            Product(
                name="Gap API Product",
                barcode="GAP-SEED-BARCODE",
                cost_price=Decimal("50"),
                selling_price=Decimal("100"),
                current_stock=100,
                category_id=1,
            )
        )
        assert product_id, "فشل إنشاء منتج الاختبار"

        # المورد عبر SQL مباشر بالأعمدة الأساسية فقط — مخطط suppliers الموسّع
        # (name_en/city/...) يعتمد على هجرات بيئة الإنتاج غير موجودة في قاعدة مؤقتة
        supplier_id = db_instance.execute_insert(
            "INSERT INTO suppliers (name, contact_person, phone, is_active) VALUES (?, ?, ?, 1)",
            ("Gap API Supplier", "Gap Contact", "0100000000"),
        )
        assert supplier_id, "فشل إنشاء مورد الاختبار"

        # فاتورة شراء (اشترى 10 وحدات) — الكمية القابلة للإرجاع تعتمد purchase_items
        purchase_id = db_instance.execute_insert(
            """
            INSERT INTO purchases (invoice_number, supplier_id, total_amount, final_amount, status, is_active)
            VALUES (?, ?, ?, ?, 'received', 1)
            """,
            (f"GAP-PO-{supplier_id}", supplier_id, "500", "500"),
        )
        assert purchase_id, "فشل إنشاء فاتورة الشراء"
        db_instance.execute_insert(
            """
            INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, total_cost)
            VALUES (?, ?, ?, ?, ?)
            """,
            (purchase_id, product_id, 10, "50", "500"),
        )

        # دفعة مخزون كافية للمرتجع (3) وللبيع النقدي (2) معاً
        batch_id = db_instance.execute_insert(
            """
            INSERT INTO batches (product_id, batch_number, quantity, cost_price, supplier_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (product_id, "BATCH-GAP-1", 100, "50", supplier_id),
        )
        assert batch_id, "فشل إنشاء الدفعة"

        # منتج ثانٍ بباركود محجوز مسبقاً (لاختبار تعارض الباركود 422 بشكل حتمي)
        second_id = pm.create_product(
            Product(
                name="Gap Second Product",
                barcode="GAP-SECOND-BARCODE",
                cost_price=Decimal("10"),
                selling_price=Decimal("20"),
            )
        )
        assert second_id, "فشل إنشاء المنتج الثاني"

        return {
            "product_id": product_id,
            "supplier_id": supplier_id,
            "purchase_id": purchase_id,
            "batch_id": batch_id,
            "second_product_id": second_id,
        }

    # ──────────────────── 1) مرتجعات المشتريات — دورة كاملة ────────────────────

    def test_purchase_return_full_cycle(self, client, auth_headers, seeded):
        """إنشاء → موافقة → إتمام → ظهور في القائمة المكتملة → الكمية القابلة تنخفض"""
        pid, sid = seeded["product_id"], seeded["supplier_id"]

        # الكمية القابلة قبل المرتجع = 10 (المشترى)
        r = client.get(
            f"{API}/purchase-returns/returnable",
            params={"supplier_id": sid, "product_id": pid},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert float(r.json()["returnable_quantity"]) == 10.0

        # إنشاء مسودة مرتجع بكمية 3
        r = client.post(
            f"{API}/purchase-returns",
            json={
                "supplier_id": sid,
                "purchase_id": seeded["purchase_id"],
                "reason": "تالف من التسليم",
                "items": [{"product_id": pid, "quantity": 3}],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        return_id = body["id"]
        assert body["status"] == "draft"

        # الموافقة (تعين الدفعات FEFO-عكسي)
        r = client.post(
            f"{API}/purchase-returns/{return_id}/approve",
            json={},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "approved"

        # الإتمام (إشعار دائن) — ذري: خصم دفعات + مخزون + قيد + تسوية
        r = client.post(
            f"{API}/purchase-returns/{return_id}/complete",
            json={"refund_method": "credit_note"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "completed"

        # يظهر في القائمة المفلترة بالمكتملة
        r = client.get(
            f"{API}/purchase-returns",
            params={"status": "completed", "supplier_id": sid},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        listed = r.json()
        assert listed["count"] >= 1
        assert any(item["id"] == return_id for item in listed["returns"])

        # تفاصيل المرتجع مع بنوده
        r = client.get(f"{API}/purchase-returns/{return_id}", headers=auth_headers)
        assert r.status_code == 200, r.text
        detail = r.json()
        assert detail["status"] == "completed"
        assert detail["items"], "المرتجع بلا بنود!"
        assert sum(float(i["quantity"]) for i in detail["items"]) == 3.0

        # الكمية القابلة بعد المرتجع = 10 − 3 = 7
        r = client.get(
            f"{API}/purchase-returns/returnable",
            params={"supplier_id": sid, "product_id": pid},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert float(r.json()["returnable_quantity"]) == 7.0

    def test_purchase_return_exceeds_returnable_422(self, client, auth_headers, seeded):
        """تجاوز الكمية القابلة → 422 مع تفاصيل خطأ النطاق (نمط CreditLimitError)"""
        pid, sid = seeded["product_id"], seeded["supplier_id"]
        r = client.post(
            f"{API}/purchase-returns",
            json={
                "supplier_id": sid,
                "items": [{"product_id": pid, "quantity": 9999}],
            },
            headers=auth_headers,
        )
        assert r.status_code == 422, r.text
        detail = r.json()["detail"]
        assert detail["error"] == "purchase_return_error"
        assert detail["message"]  # رسالة عربية موجودة

    def test_purchase_return_unknown_404(self, client, auth_headers):
        """المرتجع غير موجود → 404 (نفس نمط GET /products/{id})"""
        r = client.get(f"{API}/purchase-returns/999999", headers=auth_headers)
        assert r.status_code == 404, r.text

    def test_purchase_return_invalid_refund_method_422(self, client, auth_headers, seeded):
        """طريقة استرداد غير معروفة → 422 invalid_refund_method"""
        r = client.post(
            f"{API}/purchase-returns",
            json={
                "supplier_id": seeded["supplier_id"],
                "items": [{"product_id": seeded["product_id"], "quantity": 1}],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        client.post(f"{API}/purchase-returns/{rid}/approve", json={}, headers=auth_headers)

        r = client.post(
            f"{API}/purchase-returns/{rid}/complete",
            json={"refund_method": "bitcoin"},
            headers=auth_headers,
        )
        assert r.status_code == 422, r.text
        assert r.json()["detail"]["error"] == "invalid_refund_method"

    # ──────────────────── 2) طباعة الإيصال بعد البيع (الجوهرة) ────────────────────

    def test_create_sale_with_print_receipt_and_preview(self, client, auth_headers, seeded):
        """POST /sales?print_receipt=true → 201 + receipt_preview يحوي رقم الفاتورة وTOTAL"""
        payload = {
            "payment_method": "نقدي",
            "paid_amount": 200.0,
            "items": [
                {
                    "product_id": seeded["product_id"],
                    "quantity": 2,
                    "unit_price": 100.0,
                }
            ],
        }
        r = client.post(f"{API}/sales?print_receipt=true", json=payload, headers=auth_headers)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["id"], "فاتورة بلا معرف"
        preview = body.get("receipt_preview")
        assert preview, "receipt_preview مفقود رغم print_receipt=true"
        assert body["invoice_number"] in preview, "المعاينة بلا رقم الفاتورة"
        assert "TOTAL" in preview, "المعاينة بلا سطر TOTAL"

        # طباعة صريحة للفاتورة نفسها عبر /sales/{id}/receipt
        r = client.post(f"{API}/sales/{body['id']}/receipt", headers=auth_headers)
        assert r.status_code == 200, r.text
        receipt = r.json()
        assert receipt["printed"] is True
        assert receipt["dry_run"] is True, "بدون hardware_config يجب أن يكون dry_run"
        assert body["invoice_number"] in receipt["preview"]
        assert "TOTAL" in receipt["preview"]

    def test_create_sale_without_print_receipt(self, client, auth_headers, seeded):
        """الافتراضي: لا طباعة → receipt_preview None ولا تأثير على البيع"""
        payload = {
            "payment_method": "نقدي",
            "paid_amount": 100.0,
            "items": [{"product_id": seeded["product_id"], "quantity": 1, "unit_price": 100.0}],
        }
        r = client.post(f"{API}/sales", json=payload, headers=auth_headers)
        assert r.status_code == 201, r.text
        assert r.json().get("receipt_preview") is None

    def test_sale_receipt_unknown_sale_404(self, client, auth_headers):
        """إيصال فاتورة غير موجودة → 404"""
        r = client.post(f"{API}/sales/999999/receipt", headers=auth_headers)
        assert r.status_code == 404, r.text

    # ──────────────────── 3) درج النقدية ────────────────────

    def test_cash_drawer_open_and_status(self, client, auth_headers):
        """فتح الدرج (dry_run بدون عتاد) → opened True + status unknown، والحالة تقرأ نفسها"""
        r = client.post(
            f"{API}/pos/cash-drawer/open",
            json={"reason": "جرد نقدية"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["opened"] is True
        assert body["status"] == "unknown"  # لا يوجد عتاد قراءة في sandbox
        assert body["dry_run"] is True

        r = client.get(f"{API}/pos/cash-drawer/status", headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "unknown"

    # ──────────────────── 4) تقارير X/Z للورديات ────────────────────

    def test_pos_x_and_z_reports(self, client, auth_headers):
        """بدء وردية → تقرير X ثم Z مع معاينة نصية صحيحة"""
        r = client.post(f"{API}/pos/sessions", json={"opening_cash": 100.0}, headers=auth_headers)
        assert r.status_code == 200, r.text
        session_id = r.json()["session_id"]

        r = client.post(f"{API}/pos/reports/x", json={"session_id": session_id}, headers=auth_headers)
        assert r.status_code == 200, r.text
        x_report = r.json()
        assert x_report["printed"] is True
        assert x_report["session_id"] == session_id
        assert "X REPORT" in x_report["preview"]

        r = client.post(f"{API}/pos/reports/z", json={"session_id": session_id}, headers=auth_headers)
        assert r.status_code == 200, r.text
        z_report = r.json()
        assert z_report["printed"] is True
        assert "Z REPORT" in z_report["preview"]

    def test_pos_report_unknown_session_404(self, client, auth_headers):
        """تقرير لوردية غير موجودة → 404"""
        r = client.post(f"{API}/pos/reports/x", json={"session_id": 999999}, headers=auth_headers)
        assert r.status_code == 404, r.text

    # ──────────────────── 5) الباركود ────────────────────

    def test_barcode_assign_scan_lookup_flow(self, client, auth_headers, seeded):
        """ربط باركود تلقائي → قراءة الممسوح تعيد المنتج → غير معروف 404"""
        pid = seeded["product_id"]

        r = client.post(f"{API}/products/{pid}/assign-barcode", json={}, headers=auth_headers)
        assert r.status_code == 200, r.text
        assigned = r.json()["barcode"]
        assert assigned.startswith("200"), "الباركود التلقائي من نطاق المتجر الداخلي"

        r = client.get(f"{API}/products/scan/{assigned}", headers=auth_headers)
        assert r.status_code == 200, r.text
        product = r.json()
        assert product["found"] is True
        assert product["id"] == pid
        assert float(product["selling_price"]) == 100.0

        # باركود غير معروف → 404 (العقد الموثق في endpoint scan)
        r = client.get(f"{API}/products/scan/UNKNOWN-NO-PRODUCT-999", headers=auth_headers)
        assert r.status_code == 404, r.text

    def test_barcode_collision_422(self, client, auth_headers, seeded):
        """ربط باركود صريح مستخدم لمنتج آخر → 422 barcode_collision (لا استبدال صامت)"""
        # المنتج الثاني محجوز له باركود من البداية — محاولة سلبها للمنتج الأول
        r = client.post(
            f"{API}/products/{seeded['product_id']}/assign-barcode",
            json={"barcode": "GAP-SECOND-BARCODE"},
            headers=auth_headers,
        )
        assert r.status_code == 422, r.text
        assert r.json()["detail"]["error"] == "barcode_collision"

        # باركود صريح لمنتج غير موجود → 422 (مسار ValueError في الخدمة)
        r = client.post(
            f"{API}/products/999999/assign-barcode",
            json={"barcode": "ANY-VALUE"},
            headers=auth_headers,
        )
        assert r.status_code == 422, r.text

    def test_barcode_label_with_preview(self, client, auth_headers, seeded):
        """طباعة ملصق باركود → dry-run بدون طابعة يعيد printed True + نص المعاينة"""
        pid = seeded["product_id"]
        r = client.post(
            f"{API}/products/{pid}/barcode-label",
            params={"label_format": "30x20mm"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["printed"] is True  # dry-run آمن بدون طابعة ملصقات
        assert body["preview"], "معاينة الملصق مفقودة"
        assert "30x20mm" in body["preview"]
        assert "GAP" in body["preview"] or str(pid) in body["preview"]

    # ──────────────────── 6) LAN + Sync ────────────────────

    def test_lan_discover_returns_list(self, client, auth_headers):
        """اكتشاف LAN → 200 وقائمة (غالباً فارغة — zeroconf غائب في sandbox)"""
        r = client.get(f"{API}/lan/discover", params={"timeout_ms": 300}, headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body["devices"], list)
        assert body["count"] == len(body["devices"])

    def test_sync_flush_returns_result_dict(self, client, auth_headers):
        """تفريغ المزامنة → 200 وقاموس النتيجة كما هو (success/reason/flushed)"""
        r = client.post(f"{API}/sync/flush", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "success" in body
        assert body["reason"] == "api"
        assert "flushed" in body

    # ──────────────────── 7) المصادقة ────────────────────

    def test_protected_endpoints_reject_without_token(self, client):
        """بدون Bearer Token → AuthMiddleware يرفض (401) — سلوك الأشقاء نفسه

        ملاحظة سلوكية: HTTPException داخل AuthMiddleware تتصاعد خارج التطبيق
        (لا يعالجها ExceptionMiddleware الداخلي) — لذا الاختبار يتوقع رفعها
        بنفس الطريقة التي يتصرف بها التطبيق فعلياً.
        """
        targets = [
            ("GET", f"{API}/purchase-returns"),
            ("POST", f"{API}/pos/cash-drawer/open"),
            ("POST", f"{API}/sync/flush"),
        ]
        for method, path in targets:
            with pytest.raises(HTTPException) as exc_info:
                client.request(method, path, json={})
            assert exc_info.value.status_code == 401
