# 🎯 خطة عمل تحسين التغطية - التنفيذ الفوري

**التاريخ**: 10 ديسمبر 2025  
**الحالة الحالية**: 28.87% (630 اختبار)  
**الهدف الأول**: 60% (1,100+ اختبار)  
**المدة المتوقعة**: أسبوعان

---

## 📊 خلاصة الوضع الحالي

| المقياس | القيمة |
|---------|--------|
| التغطية الحالية | 28.87% |
| عدد الاختبارات | 630 |
| الأسطر المغطاة | 24,455 / 34,383 |
| الأسطر المطلوبة للوصول إلى 60% | ~5,200 إضافي |
| الاختبارات المطلوبة (تقريباً) | 200-300 اختبار |

---

## 🚀 خطة التنفيذ السريعة

### المرحلة 1: Utils و Core (الأسبوع الأول)
**الهدف**: 28.87% → 35-38%

#### 1.1 تعزيز اختبارات Utils
- **validators.py**: إضافة 25 اختبار جديد
- **decorators.py**: إضافة 20 اختبار جديد
- **helpers.py**: إضافة 20 اختبار جديد

#### 1.2 اختبارات Core الأساسية
- **database_manager.py**: إضافة 35 اختبار
- **config_manager.py**: إضافة 20 اختبار
- **exception_handler.py**: إضافة 15 اختبار

**الإجمالي المرحلة 1**: 100-120 اختبار جديد

---

### المرحلة 2: Models و Services (الأسبوع الثاني)
**الهدف**: 35-38% → 55-60%

#### 2.1 اختبارات Models
- **product.py**: 40 اختبار
- **sale.py**: 40 اختبار
- **customer.py**: 35 اختبار
- **purchase.py**: 35 اختبار
- **inventory.py**: 30 اختبار

#### 2.2 اختبارات الخدمات
- **inventory_service.py**: 40 اختبار
- **sales_service.py**: 40 اختبار
- **payment_service.py**: 35 اختبار
- **user_service.py**: 35 اختبار

#### 2.3 اختبارات التكامل
- **complete_workflows.py**: 45 اختبار
- **multi_company.py**: 30 اختبار
- **multi_warehouse.py**: 30 اختبار

**الإجمالي المرحلة 2**: 225-280 اختبار جديد

---

## 📋 القائمة الفورية للتنفيذ

### ملفات Tests المطلوبة (20 ملف):

**الأسبوع الأول** (8 ملفات):
1. `tests/utils/test_validators_extended.py`
2. `tests/utils/test_decorators_extended.py`
3. `tests/utils/test_helpers_extended.py`
4. `tests/core/test_database_manager_extended.py`
5. `tests/core/test_config_manager_extended.py`
6. `tests/core/test_exception_handler_extended.py`
7. `tests/core/test_window_manager_extended.py`
8. `tests/security/test_password_manager_extended.py`

**الأسبوع الثاني** (12 ملف):
9. `tests/models/test_product_extended.py`
10. `tests/models/test_sale_extended.py`
11. `tests/models/test_customer_extended.py`
12. `tests/models/test_purchase_extended.py`
13. `tests/models/test_inventory_extended.py`
14. `tests/services/test_inventory_service_extended.py`
15. `tests/services/test_sales_service_extended.py`
16. `tests/services/test_payment_service_extended.py`
17. `tests/services/test_user_service_extended.py`
18. `tests/integration/test_complete_workflows.py`
19. `tests/integration/test_multi_company.py`
20. `tests/integration/test_multi_warehouse.py`

---

## 📈 توقعات التقدم

### نهاية الأسبوع الأول:
```
✅ التغطية: 28.87% → 35-38%
✅ الاختبارات: 630 → 730-750
✅ الملفات الجديدة: 8
```

### نهاية الأسبوع الثاني:
```
✅ التغطية: 35-38% → 55-60%
✅ الاختبارات: 750 → 950-1000
✅ الملفات الجديدة: 20
```

---

## 🛠️ أدوات المراقبة

### تشغيل الاختبارات مع التغطية:
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### عرض تقدم التغطية:
```bash
pytest --cov=src --cov-report=term-missing | grep "TOTAL"
```

---

## 🎯 الأهداف اليومية

| التاريخ | الهدف | النتيجة المتوقعة |
|--------|------|-----------------|
| 10 ديسمبر | 3-4 ملفات اختبار | 28.87% → 30% |
| 11 ديسمبر | 4-5 ملفات اختبار | 30% → 32% |
| 12-13 ديسمبر | 5-6 ملفات اختبار | 32% → 35-38% |
| 14 ديسمبر | نهاية الأسبوع 1 | 35-38% مؤكدة |
| 17-24 ديسمبر | 12 ملف اختبار | 35% → 55-60% |

---

## ✅ الخطوات التالية الفورية

1. **إنشاء مجلدات الاختبارات المفقودة**:
   ```
   tests/utils/
   tests/core/
   tests/models/
   tests/services/
   tests/integration/
   ```

2. **إنشاء أول ملف اختبار**:
   `tests/utils/test_validators_extended.py`

3. **تشغيل الاختبارات الأولى**:
   ```bash
   pytest tests/utils/test_validators_extended.py -v --cov=src.utils.validators
   ```

4. **مراقبة التقدم**:
   ```bash
   pytest --cov=src --cov-report=term-missing | tail -5
   ```

---

**الحالة**: جاهز للتنفيذ الفوري  
**التاريخ**: 10 ديسمبر 2025  
**المسؤول**: GitHub Copilot
