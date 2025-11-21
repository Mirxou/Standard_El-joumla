# 🚀 دليل البدء السريع - v3.5.0
# Quick Start Guide - Version 3.5.0

---

## 📦 التثبيت السريع / Quick Installation

```powershell
# 1. تنشيط البيئة الافتراضية
.\.venv\Scripts\Activate.ps1

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. تشغيل النظام
uvicorn src.api.app:app --reload --port 8000

# 4. فتح الوثائق
Start-Process "http://localhost:8000/docs"
```

---

## 🔐 المصادقة الأساسية / Basic Authentication

### تسجيل الدخول

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**الاستجابة:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

---

## 🛡️ تفعيل MFA / Enable MFA

### الطريقة 1: SMS OTP

```bash
curl -X POST "http://localhost:8000/auth/mfa/enable" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "methods": ["SMS"],
    "phone_number": "+966501234567"
  }'
```

### الطريقة 2: TOTP (Authenticator App)

```bash
curl -X POST "http://localhost:8000/auth/mfa/enable" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "methods": ["TOTP"]
  }'
```

**الاستجابة:**
```json
{
  "message": "تم تفعيل MFA بنجاح",
  "totp_qr_url": "otpauth://totp/AccountingSystem:admin?secret=JBSWY3DPEHPK3PXP&issuer=AccountingSystem",
  "backup_codes": [
    "12345678",
    "87654321",
    ...
  ]
}
```

### التحقق من MFA

```bash
# إرسال OTP
curl -X POST "http://localhost:8000/auth/mfa/send-otp?method=SMS" \
  -H "Authorization: Bearer YOUR_TOKEN"

# التحقق من الكود
curl -X POST "http://localhost:8000/auth/mfa/verify" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "SMS",
    "code": "123456"
  }'
```

---

## 🤖 استخدام Chatbot

```bash
curl -X POST "http://localhost:8000/ai/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "message": "كم عدد المنتجات في المخزون؟"
  }'
```

**الاستجابة:**
```json
{
  "response": "لديك 150 منتج في المخزون حالياً",
  "intent": "inventory_inquiry",
  "confidence": 0.95,
  "language": "ar"
}
```

---

## 📊 التحليلات التنبؤية / Predictive Analytics

### توقع المبيعات

```bash
curl -X GET "http://localhost:8000/ai/forecast/sales?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**الاستجابة:**
```json
{
  "period_days": 7,
  "historical_avg": 15000.0,
  "trend": "increasing",
  "predicted_sales": 16500.0,
  "confidence": "medium",
  "forecast": [
    {"date": "2024-12-21", "amount": 2200},
    {"date": "2024-12-22", "amount": 2350},
    ...
  ]
}
```

### رؤى العميل

```bash
curl -X GET "http://localhost:8000/ai/insights/customer/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**الاستجابة:**
```json
{
  "customer_id": 1,
  "segment": "VIP",
  "lifetime_value": 50000.0,
  "avg_order_value": 1500.0,
  "purchase_frequency": 2.5,
  "last_purchase_days": 5,
  "churn_risk": "low",
  "recommended_actions": [
    "إرسال عرض خاص",
    "دعوة لبرنامج الولاء"
  ]
}
```

---

## 🎁 نظام الولاء / Loyalty Program

### كسب النقاط

```bash
curl -X POST "http://localhost:8000/loyalty/earn" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "invoice_id": 100,
    "amount": 500.0
  }'
```

### استرداد النقاط

```bash
curl -X POST "http://localhost:8000/loyalty/redeem" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "points": 100
  }'
```

### التحقق من الرصيد

```bash
curl -X GET "http://localhost:8000/loyalty/balance/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**الاستجابة:**
```json
{
  "customer_id": 1,
  "points": 5000,
  "tier": "gold",
  "tier_benefits": {
    "cashback_rate": 0.03,
    "special_discounts": true,
    "priority_support": true
  },
  "next_tier": "platinum",
  "points_to_next_tier": 5000
}
```

---

## 📄 الفواتير الإلكترونية / E-Invoicing

### إنشاء فاتورة إلكترونية

```bash
curl -X POST "http://localhost:8000/einvoice/generate/100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**الاستجابة:**
```json
{
  "invoice_id": 100,
  "einvoice_id": "E-INV-2024-001",
  "signature": "a1b2c3d4e5f6...",
  "qr_data": "AQIDBAUGBwgJ...",
  "status": "signed",
  "message": "تم إنشاء الفاتورة الإلكترونية بنجاح"
}
```

### تصدير XML

```bash
curl -X GET "http://localhost:8000/einvoice/100/xml" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📢 التسويق / Marketing

### إنشاء شريحة عملاء

```bash
curl -X POST "http://localhost:8000/marketing/segments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "عملاء VIP",
    "description": "العملاء الأكثر قيمة",
    "criteria": {
      "tier": "platinum",
      "min_purchases": 10
    }
  }'
```

### إنشاء حملة

```bash
curl -X POST "http://localhost:8000/marketing/campaigns" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "عرض نهاية العام",
    "campaign_type": "EMAIL",
    "segment_id": 1,
    "subject": "خصم 30% على جميع المنتجات",
    "content": "عزيزي العميل، نقدم لك خصم استثنائي...",
    "budget": 10000.0
  }'
```

### إرسال الحملة

```bash
curl -X POST "http://localhost:8000/marketing/campaigns/1/send" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### تحليلات الحملة

```bash
curl -X GET "http://localhost:8000/marketing/campaigns/1/analytics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**الاستجابة:**
```json
{
  "campaign_id": 1,
  "sent": 500,
  "opened": 400,
  "clicked": 250,
  "converted": 75,
  "revenue": 112500.0,
  "cost": 10000.0,
  "roi": 1025.0,
  "cost_per_conversion": 133.33
}
```

---

## 🏪 بوابة الموردين / Vendor Portal

### لوحة تحكم المورد

```bash
curl -X GET "http://localhost:8000/vendor/dashboard/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**الاستجابة:**
```json
{
  "vendor_id": 1,
  "total_orders": 45,
  "pending_orders": 3,
  "total_value": 150000.0,
  "avg_delivery_time": 3.5,
  "rating": 4.7,
  "new_messages": 2
}
```

### طلبات الشراء

```bash
curl -X GET "http://localhost:8000/vendor/orders/1?status=pending" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 التقارير / Reports

### تقرير المبيعات

```bash
curl -X GET "http://localhost:8000/reports/sales?start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### تقرير المخزون

```bash
curl -X GET "http://localhost:8000/reports/inventory" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### تقرير العملاء

```bash
curl -X GET "http://localhost:8000/reports/customers?segment=VIP" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 الاختبار / Testing

```powershell
# اختبار شامل
pytest -v

# اختبار ميزات AI
pytest test_ai_features.py -v

# اختبار MFA
pytest test_ai_features.py -k "mfa" -v

# اختبار التسويق
pytest test_ai_features.py -k "marketing" -v
```

---

## 📚 روابط مفيدة / Useful Links

- **API Documentation**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🆘 المساعدة / Help

### أخطاء شائعة

#### خطأ: "Rate limit exceeded"
```json
{
  "detail": "تم تجاوز حد المعدل. يرجى المحاولة لاحقاً."
}
```
**الحل:** انتظر 5 دقائق ثم حاول مرة أخرى.

#### خطأ: "Invalid OTP"
```json
{
  "verified": false,
  "message": "كود غير صحيح"
}
```
**الحل:** تحقق من الكود أو اطلب كود جديد.

#### خطأ: "Token expired"
```json
{
  "detail": "انتهت صلاحية الرمز"
}
```
**الحل:** سجل الدخول مرة أخرى للحصول على رمز جديد.

---

## 🎯 نصائح سريعة / Quick Tips

1. **احفظ Backup Codes** عند تفعيل MFA
2. **استخدم TOTP** للأمان الأفضل
3. **راقب تحليلات الحملات** لتحسين ROI
4. **استفد من Chatbot** للاستفسارات السريعة
5. **تابع نقاط الولاء** لزيادة ولاء العملاء

---

**النظام الآن جاهز للاستخدام! 🚀**

Version: 3.5.0  
Status: ✅ Production Ready
