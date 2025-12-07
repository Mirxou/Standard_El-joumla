-- Migration 015: Add missing columns to products table for compatibility
-- إضافة الأعمدة المفقودة في جدول products للتوافق مع الكود
-- 
-- هذا الملف يضيف الأعمدة التالية إذا لم تكن موجودة:
-- - max_stock: الحد الأقصى للمخزون
-- - supplier_id: معرف المورد (قد يكون موجوداً في بعض قواعد البيانات)
-- - selling_price: سعر البيع (قد يكون موجوداً في بعض قواعد البيانات)
--
-- ملاحظة: SQLite لا يدعم ALTER TABLE ADD COLUMN IF NOT EXISTS
-- يجب تنفيذ هذا الملف مع معالجة الأخطاء في الكود (try-except)
-- أو التحقق من وجود الأعمدة قبل إضافتها

PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. إضافة max_stock (الحد الأقصى للمخزون)
-- ============================================================================
-- هذا العمود مطلوب في report_exporter.py لتقرير حالة المخزون
-- إذا كان موجوداً بالفعل، سيتم تجاهل الخطأ في الكود
ALTER TABLE products ADD COLUMN max_stock INTEGER DEFAULT 0;

-- ============================================================================
-- 2. إضافة supplier_id (معرف المورد)
-- ============================================================================
-- هذا العمود موجود في migrations/001_create_enhanced_tables.sql
-- لكن قد لا يكون موجوداً في قواعد البيانات القديمة
-- إذا كان موجوداً بالفعل، سيتم تجاهل الخطأ في الكود
ALTER TABLE products ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id);

-- ============================================================================
-- 3. إضافة selling_price (سعر البيع)
-- ============================================================================
-- هذا العمود موجود في database_manager.py
-- لكن قد لا يكون موجوداً في قواعد البيانات القديمة
-- إذا كان موجوداً بالفعل، سيتم تجاهل الخطأ في الكود
ALTER TABLE products ADD COLUMN selling_price DECIMAL(10,2) DEFAULT 0;

-- ============================================================================
-- 4. إنشاء الفهارس
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_products_max_stock ON products(max_stock);
CREATE INDEX IF NOT EXISTS idx_products_selling_price ON products(selling_price);

-- ============================================================================
-- 5. تحديث القيم الافتراضية
-- ============================================================================
-- تهيئة max_stock بقيمة 0 إذا كانت NULL
UPDATE products SET max_stock = COALESCE(max_stock, 0) WHERE max_stock IS NULL;

-- تهيئة selling_price بقيمة 0 إذا كانت NULL
UPDATE products SET selling_price = COALESCE(selling_price, 0) WHERE selling_price IS NULL;

-- ============================================================================
-- ملاحظات مهمة:
-- ============================================================================
-- 1. هذا الملف يجب تنفيذه مع معالجة الأخطاء في الكود
-- 2. إذا كانت الأعمدة موجودة بالفعل، سيتم إرجاع خطأ SQLite
-- 3. يُنصح بالتحقق من وجود الأعمدة قبل إضافتها باستخدام PRAGMA table_info
-- 4. يمكن استخدام الكود التالي في Python:
--    try:
--        cursor.execute("ALTER TABLE products ADD COLUMN max_stock INTEGER DEFAULT 0")
--    except sqlite3.OperationalError as e:
--        if "duplicate column" not in str(e).lower():
--            raise

