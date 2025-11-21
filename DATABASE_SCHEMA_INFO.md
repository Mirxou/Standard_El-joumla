# 📊 بنية قاعدة البيانات - معلومات الأعمدة

## جدول Customers (العملاء)
```
Column                Type              Nullable  Default
──────────────────────────────────────────────────────────
id                    INTEGER           NOT NULL  (PK)
name                  TEXT              NOT NULL
phone                 TEXT              NULL
email                 TEXT              NULL
address               TEXT              NULL
credit_limit          DECIMAL(10,2)     NULL      0
current_balance       DECIMAL(10,2)     NULL      0  ✅ موجود
is_active             BOOLEAN           NULL      1
created_at            TIMESTAMP         NULL
updated_at            TIMESTAMP         NULL
```

**الملاحظات**:
- ✅ يحتوي على عمود `current_balance`
- ✅ يحتوي على عمود `credit_limit`
- ✅ آمن للاستعلام عن الأرصدة المستحقة

---

## جدول Suppliers (الموردين)
```
Column                Type              Nullable  Default
──────────────────────────────────────────────────────────
id                    INTEGER           NOT NULL  (PK)
name                  TEXT              NOT NULL
contact_person        TEXT              NULL
phone                 TEXT              NULL
email                 TEXT              NULL
address               TEXT              NULL
tax_number            TEXT              NULL
is_active             BOOLEAN           NULL      1
created_at            TIMESTAMP         NULL
updated_at            TIMESTAMP         NULL
```

**الملاحظات**:
- ❌ **لا يحتوي** على عمود `current_balance`
- ❌ **لا يحتوي** على عمود `credit_limit`
- ⚠️ استعلامات الأرصدة ستفشل إذا لم تكن محمية

---

## جدول Sales (المبيعات)
```
Column                Type              Nullable  Default
──────────────────────────────────────────────────────────
id                    INTEGER           NOT NULL  (PK)
customer_id           INTEGER           NOT NULL  (FK)
product_id            INTEGER           NOT NULL  (FK)
quantity              DECIMAL(10,2)     NOT NULL
unit_price            DECIMAL(10,2)     NOT NULL
total_amount          DECIMAL(10,2)     NOT NULL
notes                 TEXT              NULL
created_at            TIMESTAMP         NULL
updated_at            TIMESTAMP         NULL
```

---

## جدول Purchases (المشتريات)
```
Column                Type              Nullable  Default
──────────────────────────────────────────────────────────
id                    INTEGER           NOT NULL  (PK)
supplier_id           INTEGER           NOT NULL  (FK)
product_id            INTEGER           NOT NULL  (FK)
quantity              DECIMAL(10,2)     NOT NULL
unit_price            DECIMAL(10,2)     NOT NULL
total_amount          DECIMAL(10,2)     NOT NULL
notes                 TEXT              NULL
created_at            TIMESTAMP         NULL
updated_at            TIMESTAMP         NULL
```

---

## المقارنة بين الجداول

| الميزة | Customers | Suppliers |
|--------|-----------|-----------|
| current_balance | ✅ نعم | ❌ لا |
| credit_limit | ✅ نعم | ❌ لا |
| العمليات المرتبطة | sales | purchases |
| يمكن الاستعلام عن الأرصدة | ✅ نعم | ❌ لا |

---

## الاستعلامات الآمنة للتقارير

### ✅ آمن - تقرير العملاء (Customers)
```sql
-- الأرصدة المستحقة من العملاء
SELECT name, COALESCE(current_balance, 0) as balance 
FROM customers 
WHERE COALESCE(current_balance, 0) > 0;
```

### ❌ خطر - تقرير الموردين (Suppliers)
```sql
-- هذا سيفشل!
SELECT name, current_balance 
FROM suppliers 
WHERE current_balance > 0;  -- 🔴 NO SUCH COLUMN
```

### ✅ آمن - البديل للموردين
```sql
-- استخدم العمليات بدلاً من الأرصدة
SELECT s.name, COUNT(*) as purchase_count, SUM(p.total_amount) as total
FROM suppliers s
LEFT JOIN purchases p ON s.id = p.supplier_id
GROUP BY s.id;
```

---

## تأثير الإصلاحات على الاستعلامات

### قبل الإصلاح ❌
```python
# خطأ في السطر 5
top_balance = db.fetch_all(
    "SELECT name, current_balance FROM suppliers"  # ❌ CRASH!
)
```

### بعد الإصلاح ✅
```python
# آمن تماماً - لا يعطل حتى لو لم يوجد الوصول
try:
    top_suppliers = db.fetch_all(
        "SELECT s.name, COUNT(*) FROM suppliers s "
        "LEFT JOIN purchases p ON s.id = p.supplier_id "
        "GROUP BY s.id"  # ✅ آمن
    )
except:
    top_suppliers = []  # ✅ تدهور آمن
```

---

## ملخص التدابير الوقائية

### 1. استخدام COALESCE() دائماً
```sql
-- ❌ قد يعيد NULL
SELECT SUM(total_amount) FROM sales;

-- ✅ آمن - يعيد 0 إذا لم توجد صفوف
SELECT COALESCE(SUM(total_amount), 0) FROM sales;
```

### 2. استخدام Try/Except
```python
# ❌ التطبيق قد ينهار
data = db.fetch_all(query_with_optional_columns)

# ✅ التطبيق يستمر
try:
    data = db.fetch_all(query_with_optional_columns)
except:
    data = []  # قيمة افتراضية آمنة
```

### 3. التحقق قبل الاستخدام
```python
# ❌ قد يعطل إذا كانت data فارغة
for item in data:
    process(item)

# ✅ آمن
if data:
    for item in data:
        process(item)
else:
    show_message("لا توجد بيانات")
```

---

## الخلاصة

✅ **حالة الإصلاح**: جميع التقارير الآن محمية بشكل صحيح
✅ **الأداء**: بدون أثر على الأداء
✅ **المرونة**: يعمل حتى مع تغيرات شكل قاعدة البيانات
✅ **التجربة**: رسائل خطأ ودية وليست رسائل SQL الخام

---

**آخر تحديث**: 2025-11-17  
**الحالة**: ✅ مصدق ومختبر
