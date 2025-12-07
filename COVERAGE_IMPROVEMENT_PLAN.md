# 📊 خطة تحسين تغطية الكود - Coverage Improvement Plan

## 📈 الوضع الحالي

- **التغطية الحالية**: 28.87%
- **الهدف المطلوب**: 60%
- **الفجوة**: 31.13%
- **إجمالي الأسطر**: 34,383 سطر
- **الأسطر المغطاة**: 24,455 سطر
- **الأسطر المطلوبة للوصول إلى 60%**: ~5,200 سطر إضافي

---

## 🎯 استراتيجية التحسين

### المرحلة 1: الوحدات الأساسية (Priority: 🔴 High)
**الهدف**: الوصول إلى 50%+ تغطية

#### 1.1 Core Modules
- [ ] `src/core/database_manager.py` - اختبارات CRUD والاتصالات
- [ ] `src/core/config_manager.py` - اختبارات الإعدادات
- [ ] `src/core/error_dialog.py` - اختبارات معالجة الأخطاء
- [ ] `src/core/exception_handler.py` - اختبارات معالجة الاستثناءات

**الاختبارات المطلوبة**: ~15-20 اختبار
**التغطية المتوقعة**: 50-60%

#### 1.2 Models (النماذج)
- [ ] `src/models/product.py` - ProductManager CRUD
- [ ] `src/models/sale.py` - SaleManager CRUD
- [ ] `src/models/customer.py` - CustomerManager CRUD
- [ ] `src/models/purchase.py` - PurchaseManager CRUD
- [ ] `src/models/payment.py` - PaymentManager CRUD

**الاختبارات المطلوبة**: ~25-30 اختبار
**التغطية المتوقعة**: 50-60%

#### 1.3 Services (الخدمات)
- [ ] `src/services/inventory_service.py` - عمليات المخزون
- [ ] `src/services/sales_service.py` - عمليات المبيعات
- [ ] `src/services/payment_service.py` - عمليات المدفوعات
- [ ] `src/services/user_service.py` - إدارة المستخدمين

**الاختبارات المطلوبة**: ~20-25 اختبار
**التغطية المتوقعة**: 50-60%

**إجمالي المرحلة 1**: ~60-75 اختبار → +15-20% تغطية

---

### المرحلة 2: الوحدات المتوسطة (Priority: 🟡 Medium)
**الهدف**: الوصول إلى 60%+ تغطية

#### 2.1 Security (الأمان)
- [ ] `src/security/mfa_service.py` - اختبارات MFA
- [ ] `src/security/rate_limiter.py` - اختبارات Rate Limiting

**الاختبارات المطلوبة**: ~10-15 اختبار
**التغطية المتوقعة**: 60-70%

#### 2.2 API (واجهة البرمجة)
- [ ] `src/api/api_client.py` - اختبارات API Client
- [ ] `src/api/integration_models.py` - اختبارات النماذج

**الاختبارات المطلوبة**: ~10-15 اختبار
**التغطية المتوقعة**: 50-60%

#### 2.3 Utils (الأدوات المساعدة)
- [x] `src/utils/i18n_api.py` - ✅ 87% (ممتاز)
- [x] `src/utils/logger.py` - ✅ 70% (جيد)
- [x] `src/utils/math_utils.py` - ✅ 70% (جيد)

**الاختبارات المطلوبة**: ~5-10 اختبار إضافية
**التغطية المتوقعة**: 75-80%

**إجمالي المرحلة 2**: ~25-40 اختبار → +10-15% تغطية

---

### المرحلة 3: واجهات المستخدم (Priority: 🟢 Low)
**الهدف**: الوصول إلى 40%+ تغطية

#### 3.1 Windows (النوافذ)
- [ ] `src/ui/windows/main_window.py` - 18.68% → 40%
- [ ] `src/ui/windows/reports_window.py` - 56.15% → 60%
- [ ] `src/ui/windows/smart_dashboard_window.py` - 14.74% → 40%

**الاختبارات المطلوبة**: ~15-20 اختبار
**التغطية المتوقعة**: 40-50%

#### 3.2 Dialogs (الحوارات)
- [ ] `src/ui/dialogs/sales_dialog.py` - 42.89% → 50%
- [ ] `src/ui/dialogs/product_dialog.py` - اختبارات CRUD
- [ ] `src/ui/dialogs/login_dialog.py` - اختبارات تسجيل الدخول

**الاختبارات المطلوبة**: ~10-15 اختبار
**التغطية المتوقعة**: 40-50%

**إجمالي المرحلة 3**: ~25-35 اختبار → +5-10% تغطية

---

## 📊 التغطية الحالية حسب الفئة

### ✅ وحدات بتغطية جيدة (> 70%)
- `src/utils/i18n_api.py` - 87.04% ✅
- `src/utils/logger.py` - 70.41% ✅
- `src/utils/math_utils.py` - 70.00% ✅

### ⚠️ وحدات بتغطية متوسطة (40-70%)
- `src/ui/windows/reports_window.py` - 56.15%
- `src/ui/dialogs/sales_dialog.py` - 42.89%
- `src/ui/widgets/sales_chart.py` - 49.37%
- `src/ui/theme_manager.py` - 38.64%

### ❌ وحدات بتغطية منخفضة (< 40%)
- `src/core/` - معظم الوحدات < 30%
- `src/models/` - معظم النماذج < 30%
- `src/services/` - معظم الخدمات < 30%
- `src/ui/windows/main_window.py` - 18.68%
- `src/ui/dialogs/` - معظم الحوارات < 20%

---

## 🎯 الأهداف الزمنية

### الهدف القصير المدى (شهر واحد)
- **الهدف**: 40% تغطية
- **الاختبارات المطلوبة**: ~60-75 اختبار
- **التركيز**: Core, Models, Services الأساسية

### الهدف المتوسط المدى (3 أشهر)
- **الهدف**: 60% تغطية
- **الاختبارات المطلوبة**: ~100-150 اختبار
- **التركيز**: جميع الوحدات الأساسية + Security + API

### الهدف الطويل المدى (6 أشهر)
- **الهدف**: 80%+ تغطية
- **الاختبارات المطلوبة**: ~200-250 اختبار
- **التركيز**: تغطية شاملة لجميع الوحدات

---

## 📝 قائمة المهام

### المرحلة 1: Core & Models (أسبوع 1-2)
- [ ] اختبارات `DatabaseManager` (CRUD, Connections, Transactions)
- [ ] اختبارات `ConfigManager` (Settings, Persistence)
- [ ] اختبارات `ProductManager` (CRUD, Validation)
- [ ] اختبارات `SaleManager` (CRUD, Calculations)
- [ ] اختبارات `CustomerManager` (CRUD, Search)

### المرحلة 2: Services (أسبوع 3-4)
- [ ] اختبارات `InventoryService` (Stock Operations)
- [ ] اختبارات `SalesService` (Sales Operations)
- [ ] اختبارات `PaymentService` (Payment Operations)
- [ ] اختبارات `UserService` (Authentication, Authorization)

### المرحلة 3: Security & API (أسبوع 5-6)
- [ ] اختبارات `MFAService` (2FA Operations)
- [ ] اختبارات `RateLimiter` (Rate Limiting)
- [ ] اختبارات `APIClient` (API Operations)

### المرحلة 4: UI (أسبوع 7-8)
- [ ] اختبارات `MainWindow` (Basic Operations)
- [ ] اختبارات `SalesDialog` (Dialog Operations)
- [ ] اختبارات `ProductDialog` (Dialog Operations)

---

## 🔧 الأدوات والموارد

### الأدوات المستخدمة:
- **pytest**: إطار الاختبارات
- **coverage.py**: قياس التغطية
- **pytest-cov**: تكامل pytest مع coverage
- **pytest-qt**: اختبارات Qt UI

### الموارد:
- **الاختبارات الحالية**: 42 ملف اختبار
- **الأسطر المغطاة**: 24,455 سطر
- **الأسطر المطلوبة**: ~5,200 سطر إضافي

---

## 📈 التقدم المتوقع

### بعد المرحلة 1 (شهر واحد):
- **التغطية المتوقعة**: 40-45%
- **الاختبارات المضافة**: ~60-75 اختبار

### بعد المرحلة 2 (شهرين):
- **التغطية المتوقعة**: 50-55%
- **الاختبارات المضافة**: ~85-115 اختبار

### بعد المرحلة 3 (3 أشهر):
- **التغطية المتوقعة**: 60%+
- **الاختبارات المضافة**: ~100-150 اختبار

---

## ✅ الخطوات التالية الفورية

1. **إنشاء اختبارات Core Modules** (أسبوع 1)
2. **إنشاء اختبارات Models** (أسبوع 2)
3. **إنشاء اختبارات Services** (أسبوع 3-4)
4. **مراجعة التغطية أسبوعياً**

---

**آخر تحديث**: 5 ديسمبر 2025
**التغطية الحالية**: 28.87%
**الهدف**: 60%

