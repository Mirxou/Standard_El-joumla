-- ========================================
-- الهجرة: إنشاء جداول نظام المحاسبة
-- Migration: Create Accounting System Tables
-- ========================================

-- ========================================
-- 1. جدول دليل الحسابات (Chart of Accounts)
-- ========================================
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- المعلومات الأساسية
    account_code TEXT UNIQUE NOT NULL,      -- رمز الحساب (مثل 1001)
    account_name TEXT NOT NULL,              -- اسم الحساب (مثل "النقد بالصندوق")
    account_type TEXT NOT NULL,              -- نوع الحساب: Asset, Liability, Equity, Revenue, Expense
    sub_type TEXT,                           -- النوع الفرعي (مثل Current Asset)
    description TEXT,                        -- وصف الحساب
    
    -- الخصائص المحاسبية
    normal_side TEXT DEFAULT 'DEBIT',        -- الجانب الطبيعي: DEBIT أو CREDIT
    is_header BOOLEAN DEFAULT 0,             -- هل هو حساب رئيسي فقط (بدون حركات)
    parent_account_id INTEGER,               -- الحساب الأب إن وجد
    
    -- الحالة
    is_active BOOLEAN DEFAULT 1,             -- هل الحساب نشط
    is_locked BOOLEAN DEFAULT 0,             -- هل الحساب مقفل (لا يمكن تعديله)
    
    -- البيانات المالية
    opening_balance DECIMAL(15,2) DEFAULT 0.00,  -- الرصيد الافتتاحي
    current_balance DECIMAL(15,2) DEFAULT 0.00,  -- الرصيد الحالي
    
    -- الطوابع الزمنية
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_account_id) REFERENCES chart_of_accounts(id)
);

-- إنشاء فهرس لتسريع الاستعلامات
CREATE INDEX IF NOT EXISTS idx_coa_code ON chart_of_accounts(account_code);
CREATE INDEX IF NOT EXISTS idx_coa_type ON chart_of_accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_coa_active ON chart_of_accounts(is_active);

-- ========================================
-- 2. جدول اليوميات العامة (General Journal)
-- ========================================
CREATE TABLE IF NOT EXISTS general_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- المعلومات الأساسية
    entry_number TEXT UNIQUE NOT NULL,       -- رقم القيد (مثل JE-SAL-0001-202511)
    entry_date TIMESTAMP NOT NULL,           -- تاريخ القيد
    
    -- المرجعية والتصنيف
    reference_type TEXT,                     -- نوع المرجع: Sales, Purchase, Payment, Manual
    reference_id INTEGER,                    -- معرّف المرجع (بيع أو شراء)
    
    -- الوصف والملاحظات
    description TEXT,                        -- وصف القيد
    notes TEXT,                              -- ملاحظات إضافية
    
    -- الحالة
    is_posted BOOLEAN DEFAULT 0,             -- هل تم ترحيل القيد؟
    posted_date TIMESTAMP,                   -- تاريخ الترحيل
    posted_by TEXT,                          -- من قام بالترحيل
    
    -- المعلومات الإدارية
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- إنشاء فهرس لتسريع الاستعلامات
CREATE INDEX IF NOT EXISTS idx_journal_date ON general_journal(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_posted ON general_journal(is_posted);
CREATE INDEX IF NOT EXISTS idx_journal_type ON general_journal(reference_type);

-- ========================================
-- 3. جدول أسطر اليوميات (Journal Lines)
-- ========================================
CREATE TABLE IF NOT EXISTS journal_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- المراجع
    journal_id INTEGER NOT NULL,             -- معرّف القيد الأب
    account_id INTEGER NOT NULL,             -- معرّف الحساب
    account_code TEXT,                       -- رمز الحساب (للمرجع السريع)
    account_name TEXT,                       -- اسم الحساب (للمرجع السريع)
    
    -- المبالغ
    debit_amount DECIMAL(15,2) DEFAULT 0.00,   -- المبلغ المدين
    credit_amount DECIMAL(15,2) DEFAULT 0.00,  -- المبلغ الدائن
    
    -- الوصف
    description TEXT,                        -- وصف السطر
    
    -- الطوابع الزمنية
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (journal_id) REFERENCES general_journal(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id)
);

-- إنشاء فهرس لتسريع الاستعلامات
CREATE INDEX IF NOT EXISTS idx_lines_journal ON journal_lines(journal_id);
CREATE INDEX IF NOT EXISTS idx_lines_account ON journal_lines(account_id);

-- ========================================
-- 4. جدول الدورات المحاسبية (Accounting Periods)
-- ========================================
CREATE TABLE IF NOT EXISTS accounting_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- معلومات الدورة
    period_name TEXT NOT NULL,               -- اسم الدورة (مثل "نوفمبر 2025")
    period_type TEXT NOT NULL,               -- نوع الدورة: Monthly, Quarterly, Annual
    
    -- التواريخ
    start_date DATE NOT NULL,                -- تاريخ بداية الدورة
    end_date DATE NOT NULL,                  -- تاريخ نهاية الدورة
    
    -- الحالة
    is_closed BOOLEAN DEFAULT 0,             -- هل تم إغلاق الدورة؟
    closed_date TIMESTAMP,                   -- تاريخ الإغلاق
    closed_by TEXT,                          -- من قام بالإغلاق
    
    -- الملاحظات
    notes TEXT,
    
    -- الطوابع الزمنية
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- إنشاء فهرس لتسريع الاستعلامات
CREATE INDEX IF NOT EXISTS idx_period_dates ON accounting_periods(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_period_closed ON accounting_periods(is_closed);

-- ========================================
-- 5. جدول الرصيد الافتتاحي (Opening Balance)
-- ========================================
CREATE TABLE IF NOT EXISTS opening_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- المراجع
    account_id INTEGER NOT NULL,             -- معرّف الحساب
    period_id INTEGER,                       -- معرّف الدورة المحاسبية
    
    -- البيانات
    opening_date DATE NOT NULL,              -- تاريخ الفتح
    opening_balance DECIMAL(15,2) NOT NULL,  -- الرصيد الافتتاحي
    description TEXT,                        -- وصف الرصيد
    
    -- الطوابع الزمنية
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id),
    FOREIGN KEY (period_id) REFERENCES accounting_periods(id)
);

-- إنشاء فهرس لتسريع الاستعلامات
CREATE INDEX IF NOT EXISTS idx_opening_account ON opening_balances(account_id);
CREATE INDEX IF NOT EXISTS idx_opening_period ON opening_balances(period_id);

-- ========================================
-- إدراج دليل الحسابات الافتراضي
-- ========================================

-- رؤوس الحسابات الرئيسية
INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type, sub_type, normal_side, is_header, is_active, opening_balance)
VALUES 
    ('1000', 'الأصول الحالية', 'Asset', 'Current Asset', 'DEBIT', 1, 1, 0),
    ('1500', 'الأصول الثابتة', 'Asset', 'Fixed Asset', 'DEBIT', 1, 1, 0),
    ('2000', 'الالتزامات الحالية', 'Liability', 'Current Liability', 'CREDIT', 1, 1, 0),
    ('3000', 'حقوق الملكية', 'Equity', 'Equity', 'CREDIT', 1, 1, 0),
    ('4000', 'الإيرادات', 'Revenue', 'Revenue', 'CREDIT', 1, 1, 0),
    ('5000', 'المصروفات', 'Expense', 'Expense', 'DEBIT', 1, 1, 0);

-- الأصول الحالية
INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type, sub_type, normal_side, is_active, parent_account_id)
VALUES 
    ('1001', 'النقد بالصندوق', 'Asset', 'Current Asset', 'DEBIT', 1, 1),
    ('1002', 'النقد بالبنك', 'Asset', 'Current Asset', 'DEBIT', 1, 1),
    ('1010', 'حسابات العملاء', 'Asset', 'Current Asset', 'DEBIT', 1, 1),
    ('1020', 'المخزون', 'Asset', 'Current Asset', 'DEBIT', 1, 1);

-- الالتزامات الحالية
INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type, sub_type, normal_side, is_active, parent_account_id)
VALUES 
    ('2001', 'حسابات الموردين', 'Liability', 'Current Liability', 'CREDIT', 1, 1),
    ('2010', 'الضرائب المستحقة', 'Liability', 'Current Liability', 'CREDIT', 1, 1);

-- حقوق الملكية
INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type, normal_side, is_active, parent_account_id)
VALUES 
    ('3001', 'رأس المال', 'Equity', 'CREDIT', 1, 1),
    ('3010', 'الأرباح المحتفظ بها', 'Equity', 'CREDIT', 1, 1);

-- الإيرادات
INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type, normal_side, is_active, parent_account_id)
VALUES 
    ('4001', 'إيرادات المبيعات', 'Revenue', 'CREDIT', 1, 1),
    ('4010', 'عمولات', 'Revenue', 'CREDIT', 1, 1);

-- المصروفات
INSERT OR IGNORE INTO chart_of_accounts (account_code, account_name, account_type, normal_side, is_active, parent_account_id)
VALUES 
    ('5001', 'تكلفة البضاعة المباعة', 'Expense', 'DEBIT', 1, 1),
    ('5010', 'رواتب الموظفين', 'Expense', 'DEBIT', 1, 1),
    ('5020', 'مصروفات الإيجار', 'Expense', 'DEBIT', 1, 1),
    ('5030', 'مصروفات النقل', 'Expense', 'DEBIT', 1, 1);

-- ========================================
-- إنشاء أول دورة محاسبية (نوفمبر 2025)
-- ========================================
INSERT OR IGNORE INTO accounting_periods (period_name, period_type, start_date, end_date, is_closed)
VALUES ('نوفمبر 2025', 'Monthly', '2025-11-01', '2025-11-30', 0);
