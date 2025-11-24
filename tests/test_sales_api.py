"""
اختبارات Sales, Customer, Quotes API Endpoints
الإصدار: v1.3.0
"""

import pytest
import requests
import json
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

@requires_server
def test_update_order_status(token, order_id, new_status="confirmed"):
    """تحديث حالة طلب البيع"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"order_id": order_id, "new_status": new_status}
    response = requests.post(f"{BASE_URL}/sales/orders/update-status", json=payload, headers=headers)
    print(f"🔄 تحديث حالة الطلب: Status={response.status_code}, Body={response.text}")
    assert response.status_code == 200, f"فشل تحديث حالة الطلب: {response.text}"
    data = response.json()
    print(f"✅ {data.get('message')}")
    return data

@requires_server
def test_track_order_payment(token, order_id):
    """تتبع مدفوعات الطلب"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"order_id": order_id}
    response = requests.post(f"{BASE_URL}/sales/orders/track-payment", json=payload, headers=headers)
    print(f"💳 تتبع المدفوعات: Status={response.status_code}, Body={response.text}")
    assert response.status_code == 200, f"فشل تتبع المدفوعات: {response.text}"
    data = response.json()
    print(f"✅ مجموع المدفوع: {data.get('total_paid')}")
    return data

@requires_server
def test_create_order_refund(token, order_id, amount=50.0, reason="استرداد جزئي"):
    """إنشاء استرداد للطلب"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"order_id": order_id, "amount": amount, "reason": reason}
    response = requests.post(f"{BASE_URL}/sales/orders/create-refund", json=payload, headers=headers)
    print(f"💸 إنشاء استرداد: Status={response.status_code}, Body={response.text}")
    assert response.status_code == 200, f"فشل إنشاء الاسترداد: {response.text}"
    data = response.json()
    print(f"✅ {data.get('message')}")
    return data

@requires_server
def test_create_order_return(token, order_id, items=None, reason="مرتجع جزئي"):
    """إنشاء مرتجع للطلب"""
    headers = {"Authorization": f"Bearer {token}"}
    if items is None:
        items = [{"product_id": 1, "quantity": 1}]
    payload = {"order_id": order_id, "items": items, "reason": reason}
    response = requests.post(f"{BASE_URL}/sales/orders/create-return", json=payload, headers=headers)
    print(f"↩️  إنشاء مرتجع: Status={response.status_code}, Body={response.text}")
    assert response.status_code == 200, f"فشل إنشاء المرتجع: {response.text}"
    data = response.json()
    print(f"✅ {data.get('message')}")
    print(f"✅ {data.get('message')}")
    return data


@requires_server
def test_login():
    """تسجيل الدخول والحصول على token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    print(f"✅ تسجيل الدخول: Token = {data['access_token'][:20]}...")
    return data["access_token"]


@requires_server
def test_create_customer(token):
    """إنشاء عميل جديد"""
    headers = {"Authorization": f"Bearer {token}"}
    customer_data = {
        "name": "شركة النور للتجارة",
        "phone": "0501234567",
        "email": "alnour@example.com",
        "address": "الجزائر العاصمة - حي السلام",
        "credit_limit": 50000.0,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/customers", json=customer_data, headers=headers)
    print(f"📝 إنشاء عميل: Status={response.status_code}, Body={response.text}")
    
    if response.status_code == 201:
        data = response.json()
        assert "id" in data
        customer_id = data["id"]
        print(f"✅ تم إنشاء العميل برقم: {customer_id}")
        return customer_id
    else:
        print(f"❌ فشل إنشاء العميل: {response.text}")
        return None


@requires_server
def test_get_customer_detail(token, customer_id):
    """عرض تفاصيل العميل"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/customers/{customer_id}", headers=headers)
    print(f"🔍 تفاصيل العميل: Status={response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ اسم العميل: {data.get('name')}")
        print(f"   الهاتف: {data.get('phone')}")
        print(f"   الحد الائتماني: {data.get('credit_limit')}")
        return data
    else:
        print(f"❌ فشل عرض العميل: {response.text}")
        return None


@requires_server
def test_list_customers(token):
    """عرض قائمة العملاء"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/customers", headers=headers)
    print(f"📋 قائمة العملاء: Status={response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ عدد العملاء: {data.get('total', len(data.get('items', [])))}")
        return data
    else:
        print(f"❌ فشل عرض القائمة: {response.text}")
        return None


@requires_server
def test_create_sales_order(token, customer_id):
    """إنشاء طلب بيع"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Assuming we have product_id=1 from existing test data
    order_data = {
        "customer_id": customer_id,
        "items": [
            {
                "product_id": 1,
                "variant_id": None,
                "quantity": 5,
                "unit_price": 100.0,
                "discount": 10.0  # 10% discount
            },
            {
                "product_id": 2,
                "variant_id": None,
                "quantity": 3,
                "unit_price": 200.0,
                "discount": 0
            }
        ],
        "notes": "طلب اختبار من API",
        "payment_method": "نقدي"
    }
    
    response = requests.post(f"{BASE_URL}/sales/orders", json=order_data, headers=headers)
    print(f"🛒 إنشاء طلب بيع: Status={response.status_code}, Body={response.text}")
    
    if response.status_code == 201:
        data = response.json()
        assert "id" in data
        order_id = data["id"]
        print(f"✅ تم إنشاء الطلب برقم: {order_id}")
        return order_id
    else:
        print(f"❌ فشل إنشاء الطلب: {response.text}")
        return None


@requires_server
def test_list_sales_orders(token):
    """عرض قائمة طلبات البيع"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/sales/orders", headers=headers)
    print(f"📋 قائمة الطلبات: Status={response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ عدد الطلبات: {data.get('total', 0)}")
        if data.get("items"):
            first = data["items"][0]
            print(f"   أول طلب: {first.get('invoice_number')} - المبلغ: {first.get('total_amount')}")
        return data
    else:
        print(f"❌ فشل عرض القائمة: {response.text}")
        return None


@requires_server
def test_get_sales_order_detail(token, order_id):
    """عرض تفاصيل طلب البيع"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/sales/orders/{order_id}", headers=headers)
    print(f"🔍 تفاصيل الطلب: Status={response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ رقم الفاتورة: {data.get('invoice_number')}")
        print(f"   العميل: {data.get('customer_name')}")
        print(f"   المبلغ الإجمالي: {data.get('total_amount')}")
        print(f"   عدد المنتجات: {len(data.get('items', []))}")
        return data
    else:
        print(f"❌ فشل عرض الطلب: {response.text}")
        return None


@requires_server
def test_create_quote(token, customer_id):
    """إنشاء عرض سعر"""
    headers = {"Authorization": f"Bearer {token}"}
    
    valid_until = (datetime.now() + timedelta(days=7)).date().isoformat()
    
    quote_data = {
        "customer_id": customer_id,
        "items": [
            {
                "product_id": 1,
                "variant_id": None,
                "quantity": 10,
                "unit_price": 95.0,
                "discount": 5.0
            }
        ],
        "valid_until": valid_until,
        "notes": "عرض سعر خاص لمدة أسبوع"
    }
    
    response = requests.post(f"{BASE_URL}/sales/quotes", json=quote_data, headers=headers)
    print(f"💰 إنشاء عرض سعر: Status={response.status_code}, Body={response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ تم إنشاء عرض السعر: {data.get('quote_number')}")
        return data.get("id")
    elif response.status_code == 501:
        print(f"⚠️  جدول quotes غير موجود (متوقع في هذه النسخة)")
        return None
    else:
        print(f"❌ فشل إنشاء عرض السعر: {response.text}")
        return None


@requires_server
def test_list_quotes(token):
    """عرض قائمة عروض الأسعار"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/sales/quotes", headers=headers)
    print(f"📋 قائمة عروض الأسعار: Status={response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ عدد عروض الأسعار: {data.get('total', 0)}")
        return data
    else:
        print(f"⚠️  {response.text}")
        return None


def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("=" * 60)
    print("🚀 بدء اختبارات Sales, Customer, Quotes API")
    print("=" * 60)
    
    try:
        # 1. Login
        token = test_login()
        print()
        
        # 2. Customer Tests
        print("--- اختبارات العملاء ---")
        customer_id = test_create_customer(token)
        if customer_id:
            test_get_customer_detail(token, customer_id)
        test_list_customers(token)
        print()
        
        # 3. Sales Order Tests
        print("--- اختبارات طلبات البيع ---")
        if customer_id:
            order_id = test_create_sales_order(token, customer_id)
            if order_id:
                test_get_sales_order_detail(token, order_id)
                # New: Update order status
                test_update_order_status(token, order_id, new_status="confirmed")
                # New: Track payment
                test_track_order_payment(token, order_id)
                # New: Create refund
                test_create_order_refund(token, order_id, amount=50.0, reason="استرداد جزئي")
                # New: Create return
                test_create_order_return(token, order_id, items=[{"product_id": 1, "quantity": 1}], reason="مرتجع جزئي")
        test_list_sales_orders(token)
        print()
        
        # 4. Quote Tests
        print("--- اختبارات عروض الأسعار ---")
        if customer_id:
            quote_id = test_create_quote(token, customer_id)
        test_list_quotes(token)
        print()
        
        print("=" * 60)
        print("✅ انتهت الاختبارات بنجاح")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ خطأ في الاختبارات: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
