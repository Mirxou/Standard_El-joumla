# دليل استخدام الوحدات الجديدة (v5.3.0+)

هذا الدليل يوضح كيفية تفعيل واستخدام الوحدات الجديدة التي أغلقت الفجوات الحرجة:

---

## 1. خدمة الفوترة الدورية (Recurring Invoice Service)

**تفعيل الخدمة:**
- يتم تهيئة الخدمة تلقائياً عند بدء التطبيق.

**مثال برمجي:**
```python
svc = app.recurring_invoice_service
# إنشاء اشتراك دوري شهري
svc.create_subscription(customer_id=1, amount=100.0, frequency='monthly', description='اشتراك شهري')
# توليد الفواتير المستحقة تلقائياً
svc.generate_due_invoices()
```

---

## 2. أتمتة التسويق (Marketing Automation Service)

**تفعيل الخدمة:**
- تهيئة تلقائية.

**مثال برمجي:**
```python
svc = app.marketing_automation_service
steps = [
    {"subject": "مرحبا!", "content": "أهلاً بك", "delay_days": 0},
    {"subject": "عرض خاص", "content": "خصم 20%", "delay_days": 3},
]
svc.schedule_drip_sequence("حملة ترحيب", customer_id=1, steps=steps)
svc.send_due_campaigns()
```

---

## 3. المصادقة متعددة العوامل (MFA/OTP)

**تفعيل الخدمة:**
- تهيئة تلقائية. يجب تفعيلها للمستخدم من الإعدادات.

**مثال برمجي:**
```python
svc = app.mfa_service
# تعيين سر جديد للمستخدم
svc.set_otp_secret(user_id=1, secret='BASE32SECRET')
# توليد رمز لمرة واحدة
otp = svc.generate_otp('BASE32SECRET')
# تحقق من الرمز
svc.verify_otp(user_id=1, otp=otp)
```

---

## 4. التشفير (Encryption Service)

**تفعيل الخدمة:**
- تهيئة تلقائية بمفتاح من الإعدادات.

**مثال برمجي:**
```python
svc = app.encryption_service
enc = svc.encrypt('بيانات سرية')
plain = svc.decrypt(enc)
```

---

## 5. الدعم الفني وقاعدة المعرفة (Support Service)

**تفعيل الخدمة:**
- تهيئة تلقائية.

**مثال برمجي:**
```python
svc = app.support_service
# فتح تذكرة دعم
svc.create_ticket(user_id=1, subject='مشكلة في الدخول', description='لا أستطيع تسجيل الدخول')
# إضافة سؤال لقاعدة المعرفة
svc.add_knowledge('كيف أستعيد كلمة المرور؟', 'استخدم زر نسيت كلمة المرور')
# بحث في قاعدة المعرفة
svc.search_knowledge('كلمة المرور')
```

---

> جميع الخدمات متاحة من كائن التطبيق الرئيسي `app` بعد التهيئة.
