-- =====================================================
-- Migration 021: Multi-Company Support
-- إضافة دعم متعدد الشركات
-- =====================================================

PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. جدول الشركات (Companies)
-- =====================================================
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,                  -- رمز الشركة (مثل: COMP-001)
    name TEXT NOT NULL,                          -- اسم الشركة
    name_en TEXT,                                -- الاسم بالإنجليزية
    legal_name TEXT,                             -- الاسم القانوني
    tax_id TEXT,                                 -- الرقم الضريبي
    registration_number TEXT,                    -- رقم التسجيل التجاري
    
    -- معلومات الاتصال
    address TEXT,                                 -- العنوان
    city TEXT,                                   -- المدينة
    state TEXT,                                  -- الولاية/المحافظة
    country TEXT DEFAULT 'الجزائر',              -- الدولة
    postal_code TEXT,                            -- الرمز البريدي
    phone TEXT,                                  -- الهاتف
    phone2 TEXT,                                 -- هاتف إضافي
    email TEXT,                                  -- البريد الإلكتروني
    website TEXT,                                -- الموقع الإلكتروني
    
    -- معلومات مالية
    base_currency_id INTEGER,                    -- العملة الأساسية
    fiscal_year_start DATE,                      -- بداية السنة المالية
    fiscal_year_end DATE,                        -- نهاية السنة المالية
    tax_rate DECIMAL(5,2) DEFAULT 19.00,         -- معدل الضريبة الافتراضي
    
    -- إعدادات
    is_active INTEGER DEFAULT 1,                -- نشط/غير نشط
    is_default INTEGER DEFAULT 0,                -- الشركة الافتراضية
    timezone TEXT DEFAULT 'Africa/Algiers',     -- المنطقة الزمنية
    locale TEXT DEFAULT 'ar_DZ',                -- اللغة/المنطقة
    date_format TEXT DEFAULT 'YYYY-MM-DD',      -- تنسيق التاريخ
    time_format TEXT DEFAULT 'HH:mm:ss',        -- تنسيق الوقت
    
    -- معلومات إضافية
    logo_path TEXT,                              -- مسار الشعار
    notes TEXT,                                  -- ملاحظات
    metadata TEXT,                                -- بيانات إضافية (JSON)
    
    -- الطوابع الزمنية
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,                          -- المستخدم الذي أنشأ الشركة
    updated_by INTEGER,                          -- المستخدم الذي حدث الشركة
    
    FOREIGN KEY (base_currency_id) REFERENCES currencies(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================
-- 2. جدول ربط المستخدمين بالشركات (User Companies)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    is_default INTEGER DEFAULT 0,               -- الشركة الافتراضية للمستخدم
    is_active INTEGER DEFAULT 1,                -- نشط/غير نشط
    role TEXT,                                   -- دور المستخدم في هذه الشركة
    permissions TEXT,                            -- الصلاحيات الخاصة (JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(user_id, company_id)
);

-- =====================================================
-- 3. فهارس لتحسين الأداء
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_companies_code ON companies(code);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_is_active ON companies(is_active);
CREATE INDEX IF NOT EXISTS idx_companies_is_default ON companies(is_default);
CREATE INDEX IF NOT EXISTS idx_companies_tax_id ON companies(tax_id);

CREATE INDEX IF NOT EXISTS idx_user_companies_user ON user_companies(user_id);
CREATE INDEX IF NOT EXISTS idx_user_companies_company ON user_companies(company_id);
CREATE INDEX IF NOT EXISTS idx_user_companies_default ON user_companies(user_id, is_default);

-- =====================================================
-- 4. إدراج شركة افتراضية
-- =====================================================
-- ملاحظة: سيتم إضافة company_id إلى الجداول برمجياً في Python
-- لتجنب أخطاء SQLite مع ALTER TABLE

INSERT OR IGNORE INTO companies (
    code, name, name_en, legal_name,
    address, city, country,
    is_active, is_default,
    created_at, updated_at
) VALUES (
    'COMP-001',
    'الشركة الافتراضية',
    'Default Company',
    'الشركة الافتراضية',
    '',
    'الجزائر',
    'الجزائر',
    1,
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- =====================================================
-- ملاحظات مهمة:
-- =====================================================
-- 1. سيتم إضافة company_id إلى جميع الجداول برمجياً في Python
--    لتجنب أخطاء SQLite مع ALTER TABLE
-- 2. الجداول التي تحتاج company_id:
--    - products, product_variants, bundle_products
--    - customers, suppliers
--    - sales, sale_items, purchases, purchase_items
--    - payments, payment_schedules
--    - warehouses, warehouse_inventory, warehouse_transfers
--    - invoices, quotes, return_invoices
--    - purchase_orders, receiving_notes
--    - physical_counts, cycle_counts
--    - chart_of_accounts, journal_entries, journal_lines
--    - marketing_campaigns, customer_segments
--    - وغيرها من الجداول الرئيسية
-- 3. بعض الجداول قد تكون مشتركة بين الشركات:
--    - currencies (يمكن أن تكون مشتركة أو خاصة)
--    - exchange_rates (يمكن أن تكون مشتركة أو خاصة)
--    - users (مشترك، لكن مرتبط بشركات عبر user_companies)
--    - roles, permissions (قد تكون مشتركة أو خاصة)
-- 4. يجب التأكد من وجود شركة افتراضية واحدة فقط (is_default = 1)
-- 5. يجب ربط جميع المستخدمين بشركة افتراضية عند إضافة company_id
-- =====================================================

