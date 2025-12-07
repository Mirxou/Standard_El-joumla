# Database Migrations

## نظرة عامة
هذا المجلد يحتوي على ملفات migrations لتحديث هيكل قاعدة البيانات بشكل تدريجي وآمن.

## قائمة Migrations

### الأساسية (001-010)
- **001**: `001_create_enhanced_tables.sql` - إنشاء الجداول الأساسية المحسّنة
- **002**: `002_add_missing_columns.sql` - إضافة الأعمدة المفقودة
- **003**: `003_create_accounting_system.sql` - نظام المحاسبة
- **004**: `004_create_quotes_returns.sql` - نظام العروض والمرتجعات
- **005**: `005_create_purchase_orders.sql` - نظام أوامر الشراء
- **006**: `006_create_payment_plans.sql` - نظام خطط الدفع
- **007**: `007_inventory_optimization.sql` - تحسينات المخزون
- **008**: `008_create_inventory_counts.sql` - نظام جرد المخزون
- **009**: `009_create_reports_system.sql` - نظام التقارير
- **010**: `010_create_search_system.sql` - نظام البحث

### الأمان والصلاحيات (011-012)
- **011**: `011_create_permissions_audit.sql` - نظام الصلاحيات والتدقيق
- **012**: `012_create_cycle_count.sql` - نظام الجرد الدوري

### الأداء والتحسينات (013-015)
- **013**: `013_performance_indexes.sql` - فهارس تحسين الأداء
- **014**: `014_alter_variants_add_current_stock.sql` - محاذاة أعمدة المخزون
- **015**: `015_add_products_missing_columns.sql` - إضافة أعمدة مفقودة للمنتجات

### الأنظمة المتقدمة (016-018)
- **016**: `016_create_rbac_audit.sql` - نظام RBAC والتدقيق المتقدم
- **017**: `017_create_system_management.sql` - إدارة النظام والصيانة
- **018**: `018_products_variants_bundles.sql` - المتغيرات والحزم

## التطبيق التلقائي

يتم تطبيق migrations تلقائياً عند تهيئة `DatabaseManager` عبر:
- `_run_migrations()` - تطبيق جميع ملفات migrations
- `check_and_migrate_db()` - التحقق من التحديثات وتطبيقها

## التطبيق اليدوي

يمكن تطبيق migrations يدوياً باستخدام:

```bash
python scripts/apply_migrations.py
```

خيارات:
- `--db`: مسار قاعدة البيانات (افتراضي: `data/inventory.db`)
- `--migrations`: مسار مجلد migrations (افتراضي: `migrations`)
- `--force`: إعادة تطبيق جميع migrations حتى لو طُبّقت مسبقاً

## التحقق من الصحة

للتحقق من صحة ملفات migrations:

```bash
python scripts/validate_migrations.py
```

هذا السكريبت يتحقق من:
- عدم وجود أرقام مكررة
- عدم وجود أرقام مفقودة
- صحة أسماء الملفات
- وجود `PRAGMA foreign_keys = ON` عند الحاجة
- معالجة أخطاء SQL المحتملة

## ملاحظات مهمة

1. **ترتيب التطبيق**: يتم تطبيق migrations حسب الترتيب الرقمي (001, 002, ...)
2. **PRAGMA foreign_keys**: جميع الملفات تحتوي على `PRAGMA foreign_keys = ON` في البداية
3. **معالجة الأخطاء**: يتم تجاهل الأخطاء المتعلقة بالأعمدة أو الفهارس الموجودة مسبقاً
4. **النسخ الاحتياطي**: يتم إنشاء نسخة احتياطية تلقائياً قبل التطبيق

## إضافة Migration جديد

1. أنشئ ملف جديد بالصيغة: `XXX_description.sql` (XXX هو الرقم التالي)
2. أضف `PRAGMA foreign_keys = ON;` في البداية
3. استخدم `CREATE TABLE IF NOT EXISTS` و `CREATE INDEX IF NOT EXISTS`
4. استخدم `ALTER TABLE ADD COLUMN` بحذر (SQLite لا يدعم IF NOT EXISTS)
5. اختبر Migration على قاعدة بيانات تجريبية أولاً

## مثال

```sql
-- Migration 019: Example Migration
PRAGMA foreign_keys = ON;

-- إنشاء جدول جديد
CREATE TABLE IF NOT EXISTS example_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- إضافة فهرس
CREATE INDEX IF NOT EXISTS idx_example_name ON example_table(name);
```

