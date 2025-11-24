# دليل التكاملات الخارجية (External Integrations Guide)

هذا الدليل يوضح كيف يمكن ربط نظام الإصدار المنطقي مع أنظمة خارجية (محاسبة، دفع إلكتروني، SMS، إلخ) عبر REST API أو Webhooks أو أدوات مثل Zapier/Make.

---

## 1. تكامل المحاسبة (Accounting Integration)
- **الهدف:** إرسال قيود أو فواتير إلى نظام محاسبي خارجي (مثل QuickBooks، Xero).
- **الآلية:**
  - تصدير الفواتير بصيغة JSON/CSV.
  - Webhook عند إنشاء فاتورة جديدة:
    ```json
    POST /webhooks/accounting
    {
      "invoice_id": 123,
      "amount": 1000.0,
      "customer": "شركة س",
      "date": "2025-11-23"
    }
    ```
  - أو استخدام Zapier لربط REST API مع النظام الخارجي.

## 2. الدفع الإلكتروني (Payment Integration)
- **الهدف:** استقبال إشعارات الدفع من بوابات مثل Stripe، PayPal، STC Pay.
- **الآلية:**
  - تفعيل Webhook لاستقبال إشعار الدفع:
    ```json
    POST /webhooks/payment
    {
      "order_id": 456,
      "status": "paid",
      "amount": 500.0,
      "payment_method": "Stripe"
    }
    ```
  - تحديث حالة الطلب تلقائياً.

## 3. الرسائل القصيرة (SMS Integration)
- **الهدف:** إرسال رسائل OTP أو إشعارات عبر SMS (Twilio، Unifonic، إلخ).
- **الآلية:**
  - REST API لإرسال رسالة:
    ```http
    POST /notifications/sms
    {
      "to": "+9665xxxxxxx",
      "message": "رمز التحقق: 123456"
    }
    ```
  - أو ربط Zapier/Make مع خدمة SMS.

## 4. تكاملات أخرى (Other Integrations)
- **الدردشة:** ربط مع Slack/Teams عبر Webhook.
- **التقارير:** تصدير تلقائي إلى Google Sheets/Excel عبر Zapier.
- **التنبيهات:** إرسال إشعارات Push عبر Firebase/OneSignal.

---

## 5. استخدام Zapier/Make
- يمكن ربط أي حدث (فاتورة، طلب، تذكرة دعم) مع أكثر من 5000 تطبيق عبر Zapier/Make بدون كود.
- أمثلة:
  - عند إنشاء فاتورة → أضف صف في Google Sheet.
  - عند دفع طلب → أرسل رسالة WhatsApp تلقائياً.

---

> جميع نقاط التكامل قابلة للتخصيص حسب متطلبات العميل. لمزيد من التفاصيل راجع وثائق REST API (`API_REFERENCE.md`).
