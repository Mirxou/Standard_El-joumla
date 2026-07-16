-- =====================================================
-- Migration 020: Multi-Currency Support
-- إضافة دعم متعدد العملات
-- =====================================================

PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. جدول العملات (Currencies)
-- =====================================================
CREATE TABLE IF NOT EXISTS currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,              -- رمز العملة (USD, EUR, DZD, etc.)
    name TEXT NOT NULL,                     -- اسم العملة (الدولار الأمريكي، اليورو، الدينار الجزائري)
    symbol TEXT NOT NULL,                   -- رمز العملة ($, €, د.ج)
    is_base INTEGER DEFAULT 0,              -- هل هي العملة الأساسية؟ (0 = لا، 1 = نعم)
    is_active INTEGER DEFAULT 1,            -- هل العملة نشطة؟ (0 = غير نشطة، 1 = نشطة)
    decimal_places INTEGER DEFAULT 2,       -- عدد الأرقام العشرية (2 للدولار، 0 للدينار)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. جدول أسعار الصرف (Exchange Rates)
-- =====================================================
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency_id INTEGER NOT NULL,      -- العملة المصدر
    to_currency_id INTEGER NOT NULL,        -- العملة الهدف
    rate REAL NOT NULL,                     -- سعر الصرف (مثال: 1 USD = 134.5 DZD)
    effective_date DATE NOT NULL,           -- تاريخ بدء السعر
    expiry_date DATE,                        -- تاريخ انتهاء السعر (NULL = لا ينتهي)
    source TEXT,                            -- مصدر السعر (manual, api, etc.)
    is_active INTEGER DEFAULT 1,            -- هل السعر نشط؟
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_currency_id) REFERENCES currencies(id) ON DELETE CASCADE,
    FOREIGN KEY (to_currency_id) REFERENCES currencies(id) ON DELETE CASCADE,
    UNIQUE(from_currency_id, to_currency_id, effective_date)
);

-- =====================================================
-- 3. إضافة أعمدة العملة إلى جدول المبيعات (Sales)
-- =====================================================
-- التحقق من وجود الأعمدة قبل الإضافة (SQLite لا يدعم IF NOT EXISTS في ALTER TABLE)
-- سنستخدم طريقة آمنة: محاولة الإضافة وتجاهل الخطأ إذا كانت موجودة

-- currency_id: العملة المستخدمة في الفاتورة
-- base_amount: المبلغ بالعملة الأساسية
-- converted_amount: المبلغ بالعملة المحددة
-- exchange_rate: سعر الصرف المستخدم

-- ملاحظة: سنستخدم طريقة آمنة - محاولة الإضافة فقط إذا لم تكن موجودة
-- (سيتم التحقق برمجياً في Python)

-- =====================================================
-- 4. إضافة أعمدة العملة إلى جدول المشتريات (Purchases)
-- =====================================================

-- =====================================================
-- 5. إضافة أعمدة العملة إلى جدول المدفوعات (Payments)
-- =====================================================

-- =====================================================
-- 6. إضافة أعمدة العملة إلى جدول الفواتير (Invoices) إن وجد
-- =====================================================

-- =====================================================
-- 7. فهارس لتحسين الأداء
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_currencies_code ON currencies(code);
CREATE INDEX IF NOT EXISTS idx_currencies_is_base ON currencies(is_base);
CREATE INDEX IF NOT EXISTS idx_currencies_is_active ON currencies(is_active);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_from_currency ON exchange_rates(from_currency_id);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_to_currency ON exchange_rates(to_currency_id);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_effective_date ON exchange_rates(effective_date);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_active ON exchange_rates(is_active);

-- =====================================================
-- 8. إدراج العملات الأساسية
-- =====================================================
-- الدينار الجزائري (العملة الأساسية)
INSERT OR IGNORE INTO currencies (code, name, symbol, is_base, is_active, decimal_places) 
VALUES ('DZD', 'الدينار الجزائري', 'د.ج', 1, 1, 0);

-- الدولار الأمريكي
INSERT OR IGNORE INTO currencies (code, name, symbol, is_base, is_active, decimal_places) 
VALUES ('USD', 'الدولار الأمريكي', '$', 0, 1, 2);

-- اليورو
INSERT OR IGNORE INTO currencies (code, name, symbol, is_base, is_active, decimal_places) 
VALUES ('EUR', 'اليورو', '€', 0, 1, 2);

-- الجنيه الإسترليني
INSERT OR IGNORE INTO currencies (code, name, symbol, is_base, is_active, decimal_places) 
VALUES ('GBP', 'الجنيه الإسترليني', '£', 0, 1, 2);

-- الريال السعودي
INSERT OR IGNORE INTO currencies (code, name, symbol, is_base, is_active, decimal_places) 
VALUES ('SAR', 'الريال السعودي', 'ر.س', 0, 1, 2);

-- الدرهم الإماراتي
INSERT OR IGNORE INTO currencies (code, name, symbol, is_base, is_active, decimal_places) 
VALUES ('AED', 'الدرهم الإماراتي', 'د.إ', 0, 1, 2);

-- =====================================================
-- 9. إدراج أسعار صرف افتراضية (مثال)
-- =====================================================
-- ملاحظة: هذه أسعار صرف تقريبية - يجب تحديثها من API حقيقي
-- 1 USD = 134.5 DZD (مثال)
-- 1 EUR = 145.2 DZD (مثال)

-- نحتاج أولاً للحصول على IDs للعملات
-- سنستخدم subquery للحصول على IDs

-- USD to DZD
INSERT OR IGNORE INTO exchange_rates (from_currency_id, to_currency_id, rate, effective_date, source, is_active)
SELECT 
    (SELECT id FROM currencies WHERE code = 'USD'),
    (SELECT id FROM currencies WHERE code = 'DZD'),
    134.5,
    date('now'),
    'manual',
    1
WHERE EXISTS (SELECT 1 FROM currencies WHERE code = 'USD')
  AND EXISTS (SELECT 1 FROM currencies WHERE code = 'DZD');

-- EUR to DZD
INSERT OR IGNORE INTO exchange_rates (from_currency_id, to_currency_id, rate, effective_date, source, is_active)
SELECT 
    (SELECT id FROM currencies WHERE code = 'EUR'),
    (SELECT id FROM currencies WHERE code = 'DZD'),
    145.2,
    date('now'),
    'manual',
    1
WHERE EXISTS (SELECT 1 FROM currencies WHERE code = 'EUR')
  AND EXISTS (SELECT 1 FROM currencies WHERE code = 'DZD');

-- GBP to DZD
INSERT OR IGNORE INTO exchange_rates (from_currency_id, to_currency_id, rate, effective_date, source, is_active)
SELECT 
    (SELECT id FROM currencies WHERE code = 'GBP'),
    (SELECT id FROM currencies WHERE code = 'DZD'),
    170.0,
    date('now'),
    'manual',
    1
WHERE EXISTS (SELECT 1 FROM currencies WHERE code = 'GBP')
  AND EXISTS (SELECT 1 FROM currencies WHERE code = 'DZD');

-- =====================================================
-- ملاحظات مهمة:
-- =====================================================
-- 1. الأعمدة currency_id و exchange_rate و base_amount و converted_amount
--    سيتم إضافتها برمجياً في Python لتجنب أخطاء SQLite
-- 2. يجب التأكد من وجود عملة أساسية واحدة فقط (is_base = 1)
-- 3. أسعار الصرف يجب تحديثها من API حقيقي (Fixer.io, ExchangeRate-API, etc.)
-- 4. جميع المبالغ المالية يجب تخزينها بالعملة الأساسية أيضاً
-- =====================================================

