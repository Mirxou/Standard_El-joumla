-- Migration: Add Multi-Warehouse Support
-- Date: 2025-12-07
-- Description: إضافة دعم متعدد المستودعات (Multi-Warehouse)
-- Phase: 1.1 - Vertical Slice 1 (Database + Model)

PRAGMA foreign_keys = ON;

-- ============================================
-- 1. جدول المستودعات (Warehouses)
-- ============================================
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,              -- رمز المستودع (مثل: WH-001)
    name TEXT NOT NULL,                      -- اسم المستودع
    name_en TEXT,                            -- الاسم بالإنجليزية
    address TEXT,                            -- العنوان
    city TEXT,                               -- المدينة
    country TEXT DEFAULT 'الجزائر',          -- الدولة
    phone TEXT,                              -- الهاتف
    email TEXT,                              -- البريد الإلكتروني
    manager_name TEXT,                       -- اسم المدير
    manager_phone TEXT,                      -- هاتف المدير
    is_active INTEGER DEFAULT 1,            -- نشط/غير نشط
    is_default INTEGER DEFAULT 0,          -- المستودع الافتراضي
    notes TEXT,                              -- ملاحظات
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,                      -- المستخدم الذي أنشأ المستودع
    updated_by INTEGER                       -- المستخدم الذي حدث المستودع
);

-- ============================================
-- 2. جدول مخزون المستودعات (Warehouse Inventory)
-- ============================================
CREATE TABLE IF NOT EXISTS warehouse_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL,          -- معرف المستودع
    product_id INTEGER NOT NULL,             -- معرف المنتج
    quantity REAL DEFAULT 0.0,              -- الكمية المتوفرة
    reserved_quantity REAL DEFAULT 0.0,      -- الكمية المحجوزة
    available_quantity REAL GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,  -- الكمية المتاحة
    min_stock REAL DEFAULT 0.0,             -- الحد الأدنى للمخزون
    max_stock REAL DEFAULT 0.0,             -- الحد الأقصى للمخزون
    reorder_point REAL DEFAULT 0.0,        -- نقطة إعادة الطلب
    last_movement_date DATETIME,            -- تاريخ آخر حركة
    last_count_date DATETIME,               -- تاريخ آخر جرد
    notes TEXT,                              -- ملاحظات
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(warehouse_id, product_id)        -- منع التكرار
);

-- ============================================
-- 3. جدول حركات المخزون بين المستودعات (Warehouse Transfers)
-- ============================================
CREATE TABLE IF NOT EXISTS warehouse_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_number TEXT UNIQUE NOT NULL,   -- رقم التحويل
    from_warehouse_id INTEGER NOT NULL,     -- المستودع المصدر
    to_warehouse_id INTEGER NOT NULL,       -- المستودع الهدف
    product_id INTEGER NOT NULL,            -- المنتج
    quantity REAL NOT NULL,                 -- الكمية
    status TEXT DEFAULT 'pending',          -- الحالة: pending, in_transit, completed, cancelled
    transfer_date DATETIME DEFAULT CURRENT_TIMESTAMP,  -- تاريخ التحويل
    received_date DATETIME,                 -- تاريخ الاستلام
    notes TEXT,                             -- ملاحظات
    created_by INTEGER,                     -- المستخدم الذي أنشأ التحويل
    received_by INTEGER,                    -- المستخدم الذي استلم التحويل
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- ============================================
-- 4. تحديث جدول stock_movements لدعم المستودعات
-- ============================================
-- إضافة عمود warehouse_id إذا لم يكن موجوداً
-- (سنستخدم ALTER TABLE فقط إذا كان الجدول موجوداً)
-- ملاحظة: SQLite لا يدعم ALTER TABLE ADD COLUMN IF NOT EXISTS مباشرة
-- سنستخدم طريقة آمنة:

-- التحقق من وجود الجدول أولاً
-- إذا كان موجوداً، نضيف العمود
-- إذا لم يكن موجوداً، سيتم إنشاؤه في migration آخر

-- ============================================
-- 5. تحديث جدول products لإضافة warehouse_id الافتراضي
-- ============================================
-- ملاحظة: سنستخدم warehouse_id في warehouse_inventory بدلاً من products
-- هذا يسمح بوجود منتج في عدة مستودعات

-- ============================================
-- 6. الفهارس (Indexes) للأداء
-- ============================================
CREATE INDEX IF NOT EXISTS idx_warehouses_code ON warehouses(code);
CREATE INDEX IF NOT EXISTS idx_warehouses_active ON warehouses(is_active);
CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_warehouse ON warehouse_inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_product ON warehouse_inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_warehouse_product ON warehouse_inventory(warehouse_id, product_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_transfers_from ON warehouse_transfers(from_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_transfers_to ON warehouse_transfers(to_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_transfers_status ON warehouse_transfers(status);
CREATE INDEX IF NOT EXISTS idx_warehouse_transfers_date ON warehouse_transfers(transfer_date);

-- ============================================
-- 7. إنشاء مستودع افتراضي
-- ============================================
INSERT OR IGNORE INTO warehouses (code, name, name_en, is_default, is_active, created_at)
VALUES ('WH-001', 'المستودع الرئيسي', 'Main Warehouse', 1, 1, CURRENT_TIMESTAMP);

-- ============================================
-- 8. نقل المخزون الحالي إلى المستودع الافتراضي
-- ============================================
-- نسخ المخزون الحالي من products إلى warehouse_inventory
-- ملاحظة: reorder_point قد لا يكون موجوداً في بعض قواعد البيانات القديمة
-- لذلك نستخدم min_stock كبديل إذا لم يكن reorder_point موجوداً

-- محاولة استخدام reorder_point إذا كان موجوداً، وإلا نستخدم min_stock
-- SQLite لا يدعم IF EXISTS للعمود، لذا نستخدم طريقة آمنة:
-- نستخدم CASE مع subquery للتحقق من وجود العمود

INSERT OR IGNORE INTO warehouse_inventory (warehouse_id, product_id, quantity, min_stock, max_stock, reorder_point, created_at)
SELECT 
    (SELECT id FROM warehouses WHERE is_default = 1 LIMIT 1) as warehouse_id,
    p.id as product_id,
    COALESCE(p.current_stock, 0) as quantity,
    COALESCE(p.min_stock, 0) as min_stock,
    COALESCE(p.max_stock, 0) as max_stock,
    -- استخدام min_stock كـ reorder_point إذا لم يكن reorder_point موجوداً
    COALESCE(p.min_stock, 0) as reorder_point,
    CURRENT_TIMESTAMP
FROM products p
WHERE COALESCE(p.current_stock, 0) > 0 OR COALESCE(p.min_stock, 0) > 0 OR COALESCE(p.max_stock, 0) > 0;

-- ============================================
-- 9. Triggers للتحديث التلقائي
-- ============================================

-- Trigger لتحديث updated_at في warehouses
CREATE TRIGGER IF NOT EXISTS trg_warehouses_updated_at
AFTER UPDATE ON warehouses
BEGIN
    UPDATE warehouses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger لتحديث updated_at في warehouse_inventory
CREATE TRIGGER IF NOT EXISTS trg_warehouse_inventory_updated_at
AFTER UPDATE ON warehouse_inventory
BEGIN
    UPDATE warehouse_inventory SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger لتحديث last_movement_date عند تغيير الكمية
CREATE TRIGGER IF NOT EXISTS trg_warehouse_inventory_movement_date
AFTER UPDATE OF quantity ON warehouse_inventory
BEGIN
    UPDATE warehouse_inventory SET last_movement_date = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- 10. Views للاستعلامات الشائعة
-- ============================================

-- View: إجمالي المخزون لكل منتج في جميع المستودعات
CREATE VIEW IF NOT EXISTS v_product_total_stock AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.barcode,
    SUM(wi.quantity) as total_stock,
    SUM(wi.reserved_quantity) as total_reserved,
    SUM(wi.available_quantity) as total_available,
    COUNT(DISTINCT wi.warehouse_id) as warehouse_count
FROM products p
LEFT JOIN warehouse_inventory wi ON p.id = wi.product_id
GROUP BY p.id, p.name, p.barcode;

-- View: المخزون المنخفض لكل مستودع
CREATE VIEW IF NOT EXISTS v_low_stock_by_warehouse AS
SELECT 
    w.id as warehouse_id,
    w.code as warehouse_code,
    w.name as warehouse_name,
    wi.product_id,
    p.name as product_name,
    wi.quantity,
    wi.min_stock,
    wi.reorder_point,
    CASE 
        WHEN wi.quantity <= 0 THEN 'out_of_stock'
        WHEN wi.quantity <= wi.min_stock THEN 'low_stock'
        WHEN wi.quantity <= wi.reorder_point THEN 'reorder_needed'
        ELSE 'ok'
    END as stock_status
FROM warehouse_inventory wi
JOIN warehouses w ON wi.warehouse_id = w.id
JOIN products p ON wi.product_id = p.id
WHERE wi.quantity <= wi.reorder_point OR wi.quantity <= wi.min_stock
ORDER BY w.name, p.name;

