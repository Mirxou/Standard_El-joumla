"""
اختبارات Purchase Orders API (v1.8.0)
"""
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

# تحقق من توفر الخادم
def is_server_available():
    """التحقق من أن خادم API يعمل"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=1)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False

# تخطي الاختبارات إذا الخادم غير متاح
requires_server = pytest.mark.skipif(
    not is_server_available(),
    reason="API server not running on port 8000"
)


def _login():
    r = requests.post(f"{BASE_URL}/auth/login", json={"username":"admin","password":"admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@requires_server
def test_create_purchase_order(token):
    payload = {
        "supplier_id": 1,
        "supplier_name": "مورد تجريبي",
        "required_date": (datetime.now() + timedelta(days=7)).date().isoformat(),
        "currency": "DZD",
        "notes": "طلب شراء تجريبي",
        "items": [
            {"product_id": 1, "product_name": "منتج 1", "quantity_ordered": 10, "unit_price": 50.0},
            {"product_id": 2, "product_name": "منتج 2", "quantity_ordered": 5, "unit_price": 80.0, "discount_percent": 5}
        ]
    }
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE_URL}/purchase/orders", json=payload, headers=h)
    print("📦 إنشاء أمر شراء:", r.status_code, r.text)
    assert r.status_code == 201, r.text
    po_id = r.json()["id"]
    return po_id


@requires_server
def test_list_purchase_orders(token):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/purchase/orders?page=1&page_size=10", headers=h)
    print("📋 قائمة أوامر الشراء:", r.status_code)
    assert r.status_code == 200
    data = r.json()
    return data.get("items", [])


@requires_server
def test_get_purchase_order_detail(token, po_id):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/purchase/orders/{po_id}", headers=h)
    print("🔍 تفاصيل أمر الشراء:", r.status_code)
    assert r.status_code == 200
    return r.json()


@requires_server
def test_update_po_status(token, po_id):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE_URL}/purchase/orders/update-status", json={"po_id": po_id, "new_status": "PENDING_APPROVAL"}, headers=h)
    print("🔄 تحديث حالة أمر الشراء:", r.status_code, r.text)
    assert r.status_code == 200, r.text


@requires_server
def test_receive_po(token, po_id, detail):
    if not detail.get("items"):
        return
    first_item = detail["items"][0]
    h = {"Authorization": f"Bearer {token}"}
    payload = {
        "po_id": po_id,
        "items": [
            {
                "po_item_id": first_item["id"],
                "product_id": first_item["product_id"],
                "product_name": first_item["product_name"],
                "quantity_received": 3,
                "quantity_accepted": 3,
                "quantity_rejected": 0,
                "warehouse_location": "MAIN"
            }
        ],
        "notes": "استلام جزئي"
    }
    r = requests.post(f"{BASE_URL}/purchase/orders/receive", json=payload, headers=h)
    print("✅ استلام أمر شراء:", r.status_code, r.text)
    assert r.status_code == 200, r.text


def run_all():
    token = _login()
    po_id = test_create_purchase_order(token)
    test_list_purchase_orders(token)
    detail = test_get_purchase_order_detail(token, po_id)
    test_update_po_status(token, po_id)
    test_receive_po(token, po_id, detail)
    print("✅ انتهت اختبارات أوامر الشراء بنجاح")

if __name__ == "__main__":
    run_all()
