-- ============================================================================
-- Migration 012: Create Cycle Count System
-- نظام الجرد الدوري
-- ============================================================================

-- ============================================================================
-- 1. جدول خطط الجرد (Cycle Count Plans)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cycle_count_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_number TEXT NOT NULL UNIQUE,
    plan_name TEXT NOT NULL,
    
    -- معلومات الخطة
    description TEXT,
    frequency TEXT DEFAULT 'MONTHLY', -- DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY
    priority TEXT DEFAULT 'NORMAL', -- LOW, NORMAL, HIGH, URGENT
    
    -- النطاق
    scope TEXT DEFAULT 'FULL', -- FULL, PARTIAL, ABC_BASED, RANDOM
    category_filter TEXT, -- فئات محددة
    location_filter TEXT, -- مواقع محددة
    abc_class_filter TEXT, -- A, B, C
    
    -- الجدولة
    start_date DATE NOT NULL,
    end_date DATE,
    next_count_date DATE,
    last_count_date DATE,
    
    -- الإحصائيات
    total_counts_planned INTEGER DEFAULT 0,
    total_counts_completed INTEGER DEFAULT 0,
    total_items_counted INTEGER DEFAULT 0,
    total_discrepancies INTEGER DEFAULT 0,
    
    -- الحالة
    status TEXT DEFAULT 'DRAFT', -- DRAFT, ACTIVE, PAUSED, COMPLETED, CANCELLED
    is_active BOOLEAN DEFAULT 1,
    
    -- التتبع
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- الملاحظات
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_ccp_plan_number ON cycle_count_plans(plan_number);
CREATE INDEX IF NOT EXISTS idx_ccp_status ON cycle_count_plans(status);
CREATE INDEX IF NOT EXISTS idx_ccp_active ON cycle_count_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_ccp_next_date ON cycle_count_plans(next_count_date);

-- ============================================================================
-- 2. جدول جلسات الجرد (Cycle Count Sessions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cycle_count_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_number TEXT NOT NULL UNIQUE,
    plan_id INTEGER,
    
    -- معلومات الجلسة
    session_name TEXT NOT NULL,
    count_date DATE NOT NULL,
    scheduled_date DATE,
    
    -- النطاق
    location TEXT,
    warehouse_id INTEGER,
    category TEXT,
    abc_class TEXT, -- A, B, C
    
    -- الفريق
    counter_name TEXT NOT NULL, -- من يقوم بالجرد
    supervisor_name TEXT, -- المشرف
    
    -- التوقيت
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    
    -- الإحصائيات
    total_items INTEGER DEFAULT 0,
    items_counted INTEGER DEFAULT 0,
    items_matched INTEGER DEFAULT 0,
    items_with_variance INTEGER DEFAULT 0,
    
    -- الدقة
    accuracy_percentage DECIMAL(5, 2) DEFAULT 0.00,
    total_variance_value DECIMAL(15, 2) DEFAULT 0.00,
    
    -- الحالة
    status TEXT DEFAULT 'PLANNED', -- PLANNED, IN_PROGRESS, COMPLETED, CANCELLED, APPROVED
    
    -- التتبع
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    approved_by TEXT,
    approved_at TIMESTAMP,
    
    -- الملاحظات
    notes TEXT,
    
    FOREIGN KEY (plan_id) REFERENCES cycle_count_plans(id) ON DELETE SET NULL,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

CREATE INDEX IF NOT EXISTS idx_ccs_session_number ON cycle_count_sessions(session_number);
CREATE INDEX IF NOT EXISTS idx_ccs_plan ON cycle_count_sessions(plan_id);
CREATE INDEX IF NOT EXISTS idx_ccs_status ON cycle_count_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ccs_count_date ON cycle_count_sessions(count_date);
CREATE INDEX IF NOT EXISTS idx_ccs_counter ON cycle_count_sessions(counter_name);

-- ============================================================================
-- 3. جدول بنود الجرد (Cycle Count Items)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cycle_count_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    
    -- معلومات المنتج
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    product_sku TEXT,
    
    -- الموقع
    location TEXT,
    bin_location TEXT,
    
    -- الكميات
    system_quantity INTEGER DEFAULT 0, -- الكمية في النظام
    counted_quantity INTEGER DEFAULT 0, -- الكمية المجرودة
    variance INTEGER DEFAULT 0, -- الفرق
    variance_percentage DECIMAL(5, 2) DEFAULT 0.00,
    
    -- القيمة
    unit_cost DECIMAL(15, 2) DEFAULT 0.00,
    variance_value DECIMAL(15, 2) DEFAULT 0.00, -- قيمة الفرق
    
    -- التصنيف
    abc_class TEXT, -- A, B, C
    category TEXT,
    
    -- الحالة
    status TEXT DEFAULT 'PENDING', -- PENDING, COUNTED, VERIFIED, ADJUSTED, CANCELLED
    match_status TEXT DEFAULT 'UNKNOWN', -- MATCH, VARIANCE, MISSING, EXTRA
    
    -- التحقق
    is_verified BOOLEAN DEFAULT 0,
    verified_by TEXT,
    verified_at TIMESTAMP,
    
    -- التعديل
    is_adjusted BOOLEAN DEFAULT 0,
    adjusted_at TIMESTAMP,
    adjustment_reference TEXT,
    
    -- السبب
    variance_reason TEXT, -- سبب الاختلاف
    
    -- التتبع
    counted_at TIMESTAMP,
    counted_by TEXT,
    
    -- الملاحظات
    notes TEXT,
    
    FOREIGN KEY (session_id) REFERENCES cycle_count_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_cci_session ON cycle_count_items(session_id);
CREATE INDEX IF NOT EXISTS idx_cci_product ON cycle_count_items(product_id);
CREATE INDEX IF NOT EXISTS idx_cci_status ON cycle_count_items(status);
CREATE INDEX IF NOT EXISTS idx_cci_match_status ON cycle_count_items(match_status);
CREATE INDEX IF NOT EXISTS idx_cci_abc_class ON cycle_count_items(abc_class);

-- ============================================================================
-- 4. جدول أسباب الاختلاف (Variance Reasons)
-- ============================================================================
CREATE TABLE IF NOT EXISTS variance_reasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    category TEXT, -- THEFT, DAMAGE, COUNTING_ERROR, SYSTEM_ERROR, SHRINKAGE, etc.
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- إدراج أسباب افتراضية
INSERT OR IGNORE INTO variance_reasons (code, name_ar, name_en, category) VALUES
('COUNT_ERROR', 'خطأ في العد', 'Counting Error', 'COUNTING_ERROR'),
('THEFT', 'سرقة', 'Theft', 'THEFT'),
('DAMAGE', 'تلف', 'Damage', 'DAMAGE'),
('SHRINKAGE', 'انكماش', 'Shrinkage', 'SHRINKAGE'),
('SYSTEM_ERROR', 'خطأ في النظام', 'System Error', 'SYSTEM_ERROR'),
('RECEIVING_ERROR', 'خطأ في الاستلام', 'Receiving Error', 'RECEIVING_ERROR'),
('SHIPPING_ERROR', 'خطأ في الشحن', 'Shipping Error', 'SHIPPING_ERROR'),
('EXPIRED', 'منتهي الصلاحية', 'Expired', 'DAMAGE'),
('OBSOLETE', 'متقادم', 'Obsolete', 'DAMAGE'),
('LOCATION_ERROR', 'خطأ في الموقع', 'Location Error', 'COUNTING_ERROR');

-- ============================================================================
-- 5. Views للتحليلات
-- ============================================================================

-- عرض ملخص الجرد
CREATE VIEW IF NOT EXISTS v_cycle_count_summary AS
SELECT 
    ccs.id,
    ccs.session_number,
    ccs.session_name,
    ccs.count_date,
    ccs.counter_name,
    ccs.status,
    ccs.total_items,
    ccs.items_counted,
    ccs.items_with_variance,
    ccs.accuracy_percentage,
    ccs.total_variance_value,
    COUNT(DISTINCT cci.id) as detail_items_count,
    SUM(CASE WHEN cci.match_status = 'MATCH' THEN 1 ELSE 0 END) as matched_items,
    SUM(CASE WHEN cci.match_status = 'VARIANCE' THEN 1 ELSE 0 END) as variance_items,
    SUM(CASE WHEN cci.variance > 0 THEN 1 ELSE 0 END) as overage_items,
    SUM(CASE WHEN cci.variance < 0 THEN 1 ELSE 0 END) as shortage_items,
    SUM(ABS(cci.variance_value)) as total_abs_variance_value
FROM cycle_count_sessions ccs
LEFT JOIN cycle_count_items cci ON ccs.id = cci.session_id
GROUP BY ccs.id;

-- عرض تحليل ABC
CREATE VIEW IF NOT EXISTS v_cycle_count_abc_analysis AS
SELECT 
    ccs.session_number,
    cci.abc_class,
    COUNT(*) as item_count,
    SUM(CASE WHEN cci.match_status = 'MATCH' THEN 1 ELSE 0 END) as matched,
    SUM(CASE WHEN cci.match_status = 'VARIANCE' THEN 1 ELSE 0 END) as variances,
    ROUND(AVG(cci.variance_percentage), 2) as avg_variance_pct,
    SUM(ABS(cci.variance_value)) as total_variance_value,
    ROUND(100.0 * SUM(CASE WHEN cci.match_status = 'MATCH' THEN 1 ELSE 0 END) / COUNT(*), 2) as accuracy_pct
FROM cycle_count_sessions ccs
JOIN cycle_count_items cci ON ccs.id = cci.session_id
WHERE ccs.status IN ('COMPLETED', 'APPROVED')
GROUP BY ccs.session_number, cci.abc_class;

-- ============================================================================
-- 6. Triggers
-- ============================================================================

-- تحديث timestamp عند التعديل
CREATE TRIGGER IF NOT EXISTS update_ccp_timestamp
AFTER UPDATE ON cycle_count_plans
BEGIN
    UPDATE cycle_count_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_ccs_timestamp
AFTER UPDATE ON cycle_count_sessions
BEGIN
    UPDATE cycle_count_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- حساب التباين تلقائياً
CREATE TRIGGER IF NOT EXISTS calculate_variance
AFTER UPDATE OF counted_quantity ON cycle_count_items
BEGIN
    UPDATE cycle_count_items 
    SET 
        variance = NEW.counted_quantity - NEW.system_quantity,
        variance_percentage = CASE 
            WHEN NEW.system_quantity > 0 THEN 
                ROUND(100.0 * (NEW.counted_quantity - NEW.system_quantity) / NEW.system_quantity, 2)
            ELSE 0 
        END,
        variance_value = (NEW.counted_quantity - NEW.system_quantity) * NEW.unit_cost,
        match_status = CASE 
            WHEN NEW.counted_quantity = NEW.system_quantity THEN 'MATCH'
            ELSE 'VARIANCE'
        END
    WHERE id = NEW.id;
END;

-- تحديث إحصائيات الجلسة
CREATE TRIGGER IF NOT EXISTS update_session_stats
AFTER UPDATE ON cycle_count_items
BEGIN
    UPDATE cycle_count_sessions
    SET 
        items_counted = (
            SELECT COUNT(*) FROM cycle_count_items 
            WHERE session_id = NEW.session_id AND status = 'COUNTED'
        ),
        items_matched = (
            SELECT COUNT(*) FROM cycle_count_items 
            WHERE session_id = NEW.session_id AND match_status = 'MATCH'
        ),
        items_with_variance = (
            SELECT COUNT(*) FROM cycle_count_items 
            WHERE session_id = NEW.session_id AND match_status = 'VARIANCE'
        ),
        total_variance_value = (
            SELECT COALESCE(SUM(ABS(variance_value)), 0) FROM cycle_count_items 
            WHERE session_id = NEW.session_id
        ),
        accuracy_percentage = (
            SELECT ROUND(100.0 * COUNT(CASE WHEN match_status = 'MATCH' THEN 1 END) / 
                   NULLIF(COUNT(*), 0), 2)
            FROM cycle_count_items 
            WHERE session_id = NEW.session_id AND status = 'COUNTED'
        )
    WHERE id = NEW.session_id;
END;

-- ============================================================================
-- 7. Sample Data (للاختبار)
-- ============================================================================

-- خطة جرد شهرية
INSERT OR IGNORE INTO cycle_count_plans (
    plan_number, plan_name, description, frequency, scope, 
    start_date, status, created_by
) VALUES (
    'CCP-2025-001',
    'جرد شهري - جميع المنتجات',
    'جرد دوري شهري لجميع المنتجات في المخزن الرئيسي',
    'MONTHLY',
    'FULL',
    '2025-01-01',
    'ACTIVE',
    'admin'
);

-- خطة جرد المنتجات من فئة A
INSERT OR IGNORE INTO cycle_count_plans (
    plan_number, plan_name, description, frequency, scope, abc_class_filter,
    start_date, status, created_by
) VALUES (
    'CCP-2025-002',
    'جرد أسبوعي - فئة A',
    'جرد أسبوعي للمنتجات عالية القيمة (فئة A)',
    'WEEKLY',
    'ABC_BASED',
    'A',
    '2025-01-01',
    'ACTIVE',
    'admin'
);
