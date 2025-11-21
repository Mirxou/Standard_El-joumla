-- ============================================
-- Migration 008: Physical Counts & Stock Adjustments
-- تهجير 008: الجرد الدوري والتسويات
-- Date: November 17, 2025
-- ============================================

-- ============================================
-- 1. جدول الجرد الدوري (Physical Counts)
-- ============================================
CREATE TABLE IF NOT EXISTS physical_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    count_number TEXT NOT NULL UNIQUE,  -- رقم الجرد
    count_date DATE NOT NULL,  -- تاريخ الجرد
    scheduled_date DATE,  -- التاريخ المخطط
    
    -- التفاصيل
    description TEXT,
    location TEXT,  -- الموقع/المستودع
    counted_by INTEGER,  -- المستخدم الذي قام بالجرد
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, in_progress, completed, approved, cancelled
    approved_by INTEGER,
    approved_at DATETIME,
    completed_at DATETIME,
    
    -- الإحصائيات
    total_items INTEGER DEFAULT 0,  -- عدد الأصناف
    counted_items INTEGER DEFAULT 0,  -- الأصناف المجردة
    items_with_variance INTEGER DEFAULT 0,  -- أصناف بها فروقات
    total_variance_value DECIMAL(15,2) DEFAULT 0.00,  -- قيمة الفروقات
    
    -- ملاحظات
    notes TEXT,
    
    -- التواريخ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    
    FOREIGN KEY (counted_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    
    CHECK (status IN ('draft', 'in_progress', 'completed', 'approved', 'cancelled'))
);

-- فهارس جدول الجرد
CREATE INDEX IF NOT EXISTS idx_counts_date ON physical_counts(count_date);
CREATE INDEX IF NOT EXISTS idx_counts_status ON physical_counts(status);
CREATE INDEX IF NOT EXISTS idx_counts_location ON physical_counts(location);
CREATE INDEX IF NOT EXISTS idx_counts_counted_by ON physical_counts(counted_by);

-- ============================================
-- 2. جدول عناصر الجرد (Count Items)
-- ============================================
CREATE TABLE IF NOT EXISTS count_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    count_id INTEGER NOT NULL,  -- معرف الجرد
    product_id INTEGER NOT NULL,
    
    -- معلومات المنتج
    product_code TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_barcode TEXT,
    
    -- الكميات
    system_quantity DECIMAL(15,3) NOT NULL DEFAULT 0.000,  -- الكمية في النظام
    counted_quantity DECIMAL(15,3),  -- الكمية المجردة
    variance_quantity DECIMAL(15,3) DEFAULT 0.000,  -- الفرق
    
    -- القيم
    unit_cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    system_value DECIMAL(15,2) DEFAULT 0.00,  -- القيمة في النظام
    counted_value DECIMAL(15,2) DEFAULT 0.00,  -- القيمة المجردة
    variance_value DECIMAL(15,2) DEFAULT 0.00,  -- قيمة الفرق
    
    -- التفاصيل
    location TEXT,  -- الموقع
    batch_number TEXT,  -- رقم الدفعة
    notes TEXT,
    
    -- الحالة
    is_counted INTEGER DEFAULT 0,  -- 0 = لم يتم العد، 1 = تم العد
    requires_recount INTEGER DEFAULT 0,  -- يحتاج إعادة عد
    
    -- التواريخ
    counted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (count_id) REFERENCES physical_counts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- فهارس جدول عناصر الجرد
CREATE INDEX IF NOT EXISTS idx_count_items_count ON count_items(count_id);
CREATE INDEX IF NOT EXISTS idx_count_items_product ON count_items(product_id);
CREATE INDEX IF NOT EXISTS idx_count_items_variance ON count_items(variance_quantity);
CREATE INDEX IF NOT EXISTS idx_count_items_counted ON count_items(is_counted);

-- ============================================
-- 3. جدول تسويات المخزون (Stock Adjustments)
-- ============================================
CREATE TABLE IF NOT EXISTS stock_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adjustment_number TEXT NOT NULL UNIQUE,  -- رقم التسوية
    adjustment_date DATE NOT NULL,
    
    -- النوع والسبب
    adjustment_type TEXT NOT NULL,  -- count_adjustment, damage, expiry, theft, loss, found, correction, transfer, other
    reason TEXT,
    
    -- المنتج
    product_id INTEGER NOT NULL,
    product_code TEXT NOT NULL,
    product_name TEXT NOT NULL,
    
    -- الكميات
    quantity_before DECIMAL(15,3) NOT NULL DEFAULT 0.000,  -- الكمية قبل
    adjustment_quantity DECIMAL(15,3) NOT NULL DEFAULT 0.000,  -- كمية التسوية (+/-)
    quantity_after DECIMAL(15,3) DEFAULT 0.000,  -- الكمية بعد
    
    -- القيم
    unit_cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    adjustment_value DECIMAL(15,2) DEFAULT 0.00,  -- قيمة التسوية
    
    -- التفاصيل
    location TEXT,
    batch_number TEXT,
    count_id INTEGER,  -- مرتبط بجرد (إذا كانت تسوية جرد)
    
    -- الحالة والموافقة
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, approved, rejected, applied
    created_by INTEGER,
    approved_by INTEGER,
    approved_at DATETIME,
    rejection_reason TEXT,
    
    -- ملاحظات
    notes TEXT,
    
    -- التواريخ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    applied_at DATETIME,
    
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (count_id) REFERENCES physical_counts(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    
    CHECK (adjustment_type IN ('count_adjustment', 'damage', 'expiry', 'theft', 'loss', 'found', 'correction', 'transfer', 'other')),
    CHECK (status IN ('pending', 'approved', 'rejected', 'applied'))
);

-- فهارس جدول التسويات
CREATE INDEX IF NOT EXISTS idx_adjustments_date ON stock_adjustments(adjustment_date);
CREATE INDEX IF NOT EXISTS idx_adjustments_type ON stock_adjustments(adjustment_type);
CREATE INDEX IF NOT EXISTS idx_adjustments_status ON stock_adjustments(status);
CREATE INDEX IF NOT EXISTS idx_adjustments_product ON stock_adjustments(product_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_count ON stock_adjustments(count_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_created_by ON stock_adjustments(created_by);

-- ============================================
-- 4. Views للتقارير
-- ============================================

-- عرض ملخص الجرود
CREATE VIEW IF NOT EXISTS v_count_summary AS
SELECT 
    pc.id,
    pc.count_number,
    pc.count_date,
    pc.location,
    pc.status,
    pc.total_items,
    pc.counted_items,
    pc.items_with_variance,
    pc.total_variance_value,
    u1.username as counted_by_name,
    u2.username as approved_by_name,
    CAST(pc.counted_items AS REAL) / NULLIF(pc.total_items, 0) * 100 as completion_percentage
FROM physical_counts pc
LEFT JOIN users u1 ON pc.counted_by = u1.id
LEFT JOIN users u2 ON pc.approved_by = u2.id;

-- عرض ملخص التسويات
CREATE VIEW IF NOT EXISTS v_adjustment_summary AS
SELECT 
    sa.id,
    sa.adjustment_number,
    sa.adjustment_date,
    sa.adjustment_type,
    sa.product_code,
    sa.product_name,
    sa.adjustment_quantity,
    sa.adjustment_value,
    sa.status,
    u1.username as created_by_name,
    u2.username as approved_by_name,
    CASE 
        WHEN sa.adjustment_quantity > 0 THEN 'زيادة'
        WHEN sa.adjustment_quantity < 0 THEN 'نقص'
        ELSE 'لا تغيير'
    END as direction
FROM stock_adjustments sa
LEFT JOIN users u1 ON sa.created_by = u1.id
LEFT JOIN users u2 ON sa.approved_by = u2.id;

-- عرض عناصر الجرد مع الفروقات
CREATE VIEW IF NOT EXISTS v_count_variances AS
SELECT 
    ci.id,
    ci.count_id,
    pc.count_number,
    ci.product_code,
    ci.product_name,
    ci.system_quantity,
    ci.counted_quantity,
    ci.variance_quantity,
    ci.variance_value,
    ci.location,
    CASE 
        WHEN ci.variance_quantity > 0 THEN 'فائض'
        WHEN ci.variance_quantity < 0 THEN 'نقص'
        ELSE 'مطابق'
    END as variance_type,
    ABS(ci.variance_quantity) as abs_variance
FROM count_items ci
JOIN physical_counts pc ON ci.count_id = pc.id
WHERE ci.is_counted = 1 AND ci.variance_quantity != 0;

-- ============================================
-- 5. Triggers للتحديث التلقائي
-- ============================================

-- تحديث إحصائيات الجرد عند إضافة/تحديث عنصر
CREATE TRIGGER IF NOT EXISTS trg_update_count_stats_after_item_insert
AFTER INSERT ON count_items
FOR EACH ROW
BEGIN
    UPDATE physical_counts SET
        total_items = (SELECT COUNT(*) FROM count_items WHERE count_id = NEW.count_id),
        counted_items = (SELECT COUNT(*) FROM count_items WHERE count_id = NEW.count_id AND is_counted = 1),
        items_with_variance = (SELECT COUNT(*) FROM count_items WHERE count_id = NEW.count_id AND variance_quantity != 0),
        total_variance_value = (SELECT COALESCE(SUM(variance_value), 0) FROM count_items WHERE count_id = NEW.count_id),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.count_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_update_count_stats_after_item_update
AFTER UPDATE ON count_items
FOR EACH ROW
BEGIN
    UPDATE physical_counts SET
        counted_items = (SELECT COUNT(*) FROM count_items WHERE count_id = NEW.count_id AND is_counted = 1),
        items_with_variance = (SELECT COUNT(*) FROM count_items WHERE count_id = NEW.count_id AND variance_quantity != 0),
        total_variance_value = (SELECT COALESCE(SUM(variance_value), 0) FROM count_items WHERE count_id = NEW.count_id),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.count_id;
END;

-- تحديث updated_at عند التعديل
CREATE TRIGGER IF NOT EXISTS trg_counts_updated_at
AFTER UPDATE ON physical_counts
FOR EACH ROW
BEGIN
    UPDATE physical_counts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_adjustments_updated_at
AFTER UPDATE ON stock_adjustments
FOR EACH ROW
BEGIN
    UPDATE stock_adjustments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- 6. بيانات افتراضية (Optional)
-- ============================================

-- يمكن إضافة بيانات افتراضية هنا إذا لزم الأمر

-- ============================================
-- نهاية التهجير
-- ============================================
