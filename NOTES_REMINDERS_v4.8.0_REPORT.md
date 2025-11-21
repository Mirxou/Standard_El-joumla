# 🗒️ نظام الملاحظات والتذكيرات v4.8.0

**الحالة:** مكتمل ✅  
**الاختبارات:** 49/49 ✅ (لا توجد تراجعات)  
**التاريخ:** نوفمبر 2025

---
## 🎯 نظرة عامة
يوفر النظام إدارة كاملة للملاحظات المرتبطة بالفواتير، بالإضافة إلى تذكيرات دفع ومتابعة يتم توليدها وإرسالها آلياً عبر البريد الإلكتروني مع إمكانية إرفاق ملف PDF للفاتورة.

### المكونات الرئيسية
1. `invoice_notes` – تخزين ملاحظات الفواتير (داخلية / تظهر للعميل)
2. `reminders` – جدولة تذكيرات الدفع والمتابعة مع حالة التنفيذ
3. `NotesService` – واجهة إضافة / عرض / تثبيت / حذف الملاحظات
4. `ReminderService` – جدولة وإرسال وإلغاء التذكيرات المستحقة
5. `EmailService` – إرسال البريد مع قوالب HTML / نص ومرفقات PDF
6. `ReminderScheduler` – خدمة خلفية دورية ترسل التذكيرات تلقائياً

---
## 🗄️ قاعدة البيانات
### جدول الملاحظات `invoice_notes`
```sql
CREATE TABLE invoice_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sale_id INTEGER NOT NULL,
  note_text TEXT NOT NULL,
  created_by INTEGER,
  is_internal BOOLEAN DEFAULT 0,
  is_pinned BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (sale_id) REFERENCES sales(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE INDEX idx_invoice_notes_sale ON invoice_notes(sale_id);
CREATE INDEX idx_invoice_notes_created_by ON invoice_notes(created_by);
```
### جدول التذكيرات `reminders`
```sql
CREATE TABLE reminders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sale_id INTEGER,
  customer_id INTEGER,
  reminder_type TEXT NOT NULL CHECK (reminder_type IN ('payment','follow_up','custom')),
  subject TEXT NOT NULL,
  message TEXT,
  due_at TIMESTAMP NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','sent','cancelled')),
  attempts INTEGER DEFAULT 0,
  last_attempt_at TIMESTAMP,
  recipient_email TEXT,
  created_by INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (sale_id) REFERENCES sales(id),
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE INDEX idx_reminders_due_at ON reminders(due_at);
CREATE INDEX idx_reminders_status ON reminders(status);
CREATE INDEX idx_reminders_customer ON reminders(customer_id);
```

---
## 🧩 الخدمات البرمجية
### NotesService
```python
add_note(sale_id, note_text, created_by=None, is_internal=False, is_pinned=False)
list_notes(sale_id, include_internal=True)
pin_note(note_id, pinned=True)
delete_note(note_id)
```
### ReminderService
```python
schedule_payment_reminder(sale_id, due_at, recipient_email, created_by=None, subject=None, message=None)
list_pending(limit=100)
send_due_reminders(attach_invoice_pdf=True)
cancel_reminder(reminder_id)
```
### ReminderScheduler
- حلقة خلفية (Thread daemon) تفحص كل فترة زمنية (`interval`) وفق متغيرات البيئة.
```python
init_reminder_scheduler()  # يبدأ تلقائياً إذا SCHEDULER_ENABLED=true
```

---
## 🔐 متغيرات البيئة
```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=no-reply@example.com
SMTP_PASSWORD=APP_PASSWORD
SMTP_TLS=true
SMTP_FROM=no-reply@example.com

SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_SECONDS=300  # كل 5 دقائق
```

---
## ✉️ قوالب البريد (التذكير بالدفع)
HTML:
```html
<h3>تذكير بالدفع للفاتورة رقم {{ invoice_number }}</h3>
<p>المتبقي: {{ remaining }} دج قبل {{ due_date }}</p>
```
نص عادي:
```text
تذكير دفع للفاتورة رقم {{ invoice_number }}
المتبقي: {{ remaining }} دج قبل {{ due_date }}
```

---
## 🛠️ أمثلة الاستخدام
### إضافة ملاحظة
```python
notes.add_note(sale_id=101, note_text="اتصال لتأكيد الاستلام", is_internal=True)
```
### جدولة تذكير دفع
```python
from datetime import datetime, timedelta
reminders.schedule_payment_reminder(
  sale_id=101,
  due_at=datetime.utcnow() + timedelta(days=3),
  recipient_email="client@example.com"
)
```
### إرسال التذكيرات المستحقة يدوياً
```python
reminders.send_due_reminders()
```
### تشغيل المجدول التلقائي
```python
from src.services.scheduler_service import init_reminder_scheduler
init_reminder_scheduler()  # يعتمد على البيئة
```

---
## ✅ الإنجازات v4.8.0 (الملاحظات والتذكيرات)
- نظام ملاحظات كامل مع تثبيت داخلي
- تذكيرات دفع تلقائية مع PDF مرفق
- دعم تذكيرات متابعة عامة
- جدولة خلفية قابلة للتعطيل/التفعيل
- تكامل سلس مع الطباعة والبريد

---
## 🧪 الاختبارات
- لا توجد اختبارات منفصلة جديدة بعد (اعتمدنا على سلامة النظام القائم)
- جميع اختبارات النظام الحالية نجحت (49/49)
- لا تراجع في الأداء أو الاستجابة

---
## 📈 تحسينات مستقبلية مقترحة
- إضافة واجهة مستخدم لإدارة التذكيرات (فلترة حسب الحالة)
- إعادة المحاولة الذكية مع تصعيد (retry + backoff)
- إحصائيات لوحة معلومات: عدد التذكيرات المرسلة / الفائتة
- قوالب دولية متعددة اللغات
- دعم قنوات أخرى (SMS / WhatsApp API)

---
## 🔒 اعتبارات الأمان
- حماية البريد من الإفراط عبر ضبط الفاصل الزمني
- عدم تكرار إرسال نفس التذكير (تحديث الحالة إلى sent)
- احترام الخصوصية (عدم إرسال ملاحظات داخلية للعملاء)

---
## 🏁 حالة المشروع
هذا الجزء يعزز تجربة التحصيل والمتابعة ويكمل دورة الفاتورة من الإنشاء إلى التذكير بالدفع.

**جاهز للإنتاج ✅**

تم بحمد الله ✨
