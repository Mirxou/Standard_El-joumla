# 🔌 دليل التكاملات - Integration Guide

## نظرة عامة

يدعم نظام الإصدار المنطقي عدة أنواع من التكاملات:
- Email Integration
- API Integration
- Payment Gateway Integration
- Third-party Services

## Email Integration

### الإعداد

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.load_config()

# تعيين إعدادات البريد
config.set('email.enabled', True)
config.set('email.smtp_server', 'smtp.gmail.com')
config.set('email.smtp_port', 587)
config.set('email.smtp_username', 'your_email@gmail.com')
config.set('email.smtp_password', 'your_password')
config.set('email.smtp_use_tls', True)
config.set('email.from_email', 'your_email@gmail.com')
config.set('email.from_name', 'Your Company')
config.save_config()
```

### استخدام متغيرات البيئة

```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_password
```

### إرسال بريد إلكتروني

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.core.config_manager import ConfigManager

def send_email(to_email, subject, body, html_body=None):
    config = ConfigManager()
    config.load_config()
    email_settings = config.get_email_settings()
    
    if not email_settings['enabled']:
        return False
    
    # إنشاء الرسالة
    msg = MIMEMultipart('alternative')
    msg['From'] = f"{email_settings['from_name']} <{email_settings['from_email']}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # إضافة النص
    msg.attach(MIMEText(body, 'plain'))
    if html_body:
        msg.attach(MIMEText(html_body, 'html'))
    
    # إرسال الرسالة
    try:
        server = smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port'])
        server.starttls()
        server.login(email_settings['smtp_username'], email_settings['smtp_password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"خطأ في إرسال البريد: {e}")
        return False

# استخدام
send_email(
    to_email="customer@example.com",
    subject="فاتورة جديدة",
    body="تم إنشاء فاتورة جديدة",
    html_body="<h1>فاتورة جديدة</h1><p>تم إنشاء فاتورة جديدة</p>"
)
```

## API Integration

### الإعداد

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.load_config()

# تعيين إعدادات API
config.set('api.enabled', True)
config.set('api.base_url', 'https://api.example.com')
config.set('api.api_key', 'your_api_key')
config.set('api.timeout', 30)
config.set('api.retry_attempts', 3)
config.set('api.verify_ssl', True)
config.save_config()
```

### استخدام متغيرات البيئة

```bash
export API_BASE_URL=https://api.example.com
export API_KEY=your_api_key
```

### API Client

```python
import requests
from src.core.config_manager import ConfigManager
from src.security.rate_limiter import api_rate_limiter

class APIClient:
    def __init__(self):
        config = ConfigManager()
        config.load_config()
        self.api_settings = config.get_api_settings()
        self.base_url = self.api_settings['base_url']
        self.api_key = self.api_settings['api_key']
        self.timeout = self.api_settings['timeout']
        self.retry_attempts = self.api_settings['retry_attempts']
    
    def _make_request(self, method, endpoint, data=None, params=None):
        # التحقق من Rate Limit
        is_allowed, remaining = api_rate_limiter.is_allowed(self.api_key)
        if not is_allowed:
            raise Exception("Rate limit exceeded")
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.api_settings['verify_ssl']
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def get(self, endpoint, params=None):
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint, data=None):
        return self._make_request('POST', endpoint, data=data)
    
    def put(self, endpoint, data=None):
        return self._make_request('PUT', endpoint, data=data)
    
    def delete(self, endpoint):
        return self._make_request('DELETE', endpoint)

# استخدام
api_client = APIClient()
result = api_client.get('products', params={'page': 1, 'limit': 10})
```

## Payment Gateway Integration

### مثال: تكامل مع بوابة دفع

```python
import requests
import hashlib
import hmac

class PaymentGateway:
    def __init__(self, merchant_id, secret_key):
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.base_url = "https://payment-gateway.com/api"
    
    def create_payment(self, amount, currency, order_id, callback_url):
        # إنشاء توقيع
        signature_data = f"{self.merchant_id}{amount}{currency}{order_id}"
        signature = hmac.new(
            self.secret_key.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # إرسال الطلب
        response = requests.post(
            f"{self.base_url}/payments",
            json={
                "merchant_id": self.merchant_id,
                "amount": amount,
                "currency": currency,
                "order_id": order_id,
                "callback_url": callback_url,
                "signature": signature
            }
        )
        
        return response.json()
    
    def verify_payment(self, payment_id, amount):
        # التحقق من الدفع
        response = requests.get(
            f"{self.base_url}/payments/{payment_id}/verify",
            params={
                "merchant_id": self.merchant_id,
                "amount": amount
            }
        )
        
        return response.json()

# استخدام
payment_gateway = PaymentGateway(
    merchant_id="your_merchant_id",
    secret_key="your_secret_key"
)

payment = payment_gateway.create_payment(
    amount=1000.0,
    currency="SAR",
    order_id="ORDER-123",
    callback_url="https://yoursite.com/payment/callback"
)
```

## Webhook Integration

### استقبال Webhooks

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    # التحقق من التوقيع
    signature = request.headers.get('X-Signature')
    payload = request.get_data()
    
    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # معالجة Webhook
    data = request.json
    
    if data['event'] == 'payment.completed':
        # تحديث حالة الدفع في قاعدة البيانات
        update_payment_status(data['payment_id'], 'completed')
    
    return jsonify({"status": "ok"}), 200
```

## أمثلة عملية

### مثال 1: إرسال فاتورة بالبريد

```python
from src.services.invoice_print_service import InvoicePrintService
from src.core.config_manager import ConfigManager

def send_invoice_by_email(sale_id, customer_email):
    # توليد HTML الفاتورة
    print_service = InvoicePrintService()
    invoice_data = get_invoice_data(sale_id)
    success, message, html_content = print_service.generate_invoice_html(invoice_data)
    
    if not success:
        return False
    
    # إرسال البريد
    config = ConfigManager()
    config.load_config()
    email_settings = config.get_email_settings()
    
    return send_email(
        to_email=customer_email,
        subject=f"فاتورة #{invoice_data['id']}",
        body="تم إرفاق الفاتورة",
        html_body=html_content
    )
```

### مثال 2: مزامنة المنتجات مع API خارجي

```python
from src.models.product import ProductManager
from src.core.database_manager import DatabaseManager

def sync_products_with_external_api():
    db_manager = DatabaseManager()
    db_manager.initialize()
    product_manager = ProductManager(db_manager)
    api_client = APIClient()
    
    # جلب المنتجات من API
    external_products = api_client.get('products')
    
    # تحديث المنتجات المحلية
    for ext_product in external_products:
        local_product = product_manager.get_product_by_barcode(ext_product['barcode'])
        
        if local_product:
            # تحديث المنتج الموجود
            product_manager.update_product(local_product.id, {
                'name': ext_product['name'],
                'price': ext_product['price'],
                'stock': ext_product['stock']
            })
        else:
            # إضافة منتج جديد
            from src.models.product import Product
            new_product = Product(
                name=ext_product['name'],
                barcode=ext_product['barcode'],
                cost_price=ext_product['cost_price'],
                selling_price=ext_product['price'],
                current_stock=ext_product['stock']
            )
            product_manager.create_product(new_product)
```

### مثال 3: تكامل مع نظام CRM

```python
class CRMIntegration:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://crm.example.com/api"
    
    def create_customer(self, customer_data):
        response = requests.post(
            f"{self.base_url}/customers",
            json=customer_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def update_customer(self, customer_id, customer_data):
        response = requests.put(
            f"{self.base_url}/customers/{customer_id}",
            json=customer_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def sync_sale(self, sale_data):
        response = requests.post(
            f"{self.base_url}/sales",
            json=sale_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()

# استخدام
crm = CRMIntegration(api_key="your_crm_api_key")

# مزامنة عميل جديد
customer = crm.create_customer({
    "name": "أحمد محمد",
    "email": "ahmed@example.com",
    "phone": "0555123456"
})

# مزامنة فاتورة
sale = crm.sync_sale({
    "customer_id": customer['id'],
    "total": 1000.0,
    "items": [...]
})
```

## أفضل الممارسات

1. **استخدم متغيرات البيئة للأسرار:**
   - لا تحفظ API Keys في الكود
   - استخدم متغيرات البيئة

2. **استخدم Rate Limiting:**
   - لحماية API Endpoints
   - لتجنب تجاوز الحدود

3. **معالجة الأخطاء:**
   - استخدم Retry مع Exponential Backoff
   - سجل الأخطاء للتحليل

4. **التحقق من التوقيعات:**
   - للـ Webhooks
   - للـ API Requests

5. **استخدم HTTPS:**
   - دائماً للاتصالات الخارجية
   - تحقق من شهادات SSL

---

**تم إنشاء هذا الدليل بواسطة:** Logical Version Team  
**التاريخ:** 2025-01-15  
**الإصدار:** 5.3.0

