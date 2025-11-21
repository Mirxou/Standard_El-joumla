-- ============================================================================
-- Migration 007: Inventory Optimization System
-- نظام تحسين المخزون - تحليل ABC، الأرصدة الآمنة، تتبع الدفعات
-- ============================================================================

-- ============================================================================
-- 1. جدول إعدادات الأرصدة الآمنة (Safety Stock Configurations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS safety_stock_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL UNIQUE,
    
    -- نقاط المخزون
    reorder_point DECIMAL(15, 2) DEFAULT 0.00,       -- نقطة إعادة الطلب
    safety_stock DECIMAL(15, 2) DEFAULT 0.00,        -- المخزون الآمن
    maximum_stock DECIMAL(15, 2) DEFAULT 0.00,       -- الحد الأقصى
    minimum_stock DECIMAL(15, 2) DEFAULT 0.00,       -- الحد الأدنى
    
    -- بيانات الطلب
    average_daily_demand DECIMAL(15, 2) DEFAULT 0.00,  -- الطلب اليومي المتوسط
    lead_time_days INTEGER DEFAULT 7,                   -- مدة التوريد بالأيام
    service_level DECIMAL(5, 2) DEFAULT 95.00,         -- مستوى الخدمة %
    
    -- كمية الطلب الاقتصادية
    economic_order_quantity DECIMAL(15, 2) DEFAULT 0.00,  -- EOQ
    
    -- التكاليف
    holding_cost_percentage DECIMAL(5, 2) DEFAULT 20.00,  -- تكلفة الحفظ %
    order_cost DECIMAL(10, 2) DEFAULT 50.00,              -- تكلفة الطلب
    
    -- التتبع
    last_reorder_date DATE,
    last_stockout_date DATE,
    stockout_count INTEGER DEFAULT 0,
    
    -- التفعيل
    is_active BOOLEAN DEFAULT 1,
    auto_reorder_enabled BOOLEAN DEFAULT 0,
    
    -- التواريخ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_ssc_product ON safety_stock_configs(product_id);
CREATE INDEX IF NOT EXISTS idx_ssc_active ON safety_stock_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_ssc_auto_reorder ON safety_stock_configs(auto_reorder_enabled);

-- ============================================================================
-- 2. جدول الدفعات (Product Batches)
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    
    -- معلومات الدفعة
    batch_number TEXT NOT NULL,
    serial_numbers TEXT,  -- قائمة الأرقام المتسلسلة مفصولة بفواصل
    
    -- الكميات
    initial_quantity DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    current_quantity DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    reserved_quantity DECIMAL(15, 2) DEFAULT 0.00,
    available_quantity DECIMAL(15, 2) DEFAULT 0.00,
    
    -- التواريخ
    manufacturing_date DATE,
    expiry_date DATE,
    received_date DATE NOT NULL,
    
    -- الموقع
    warehouse_location TEXT,
    rack_number TEXT,
    bin_number TEXT,
    
    -- المورد
    supplier_id INTEGER,
    supplier_name TEXT,
    purchase_order_number TEXT,
    
    -- السعر
    unit_cost DECIMAL(15, 2) DEFAULT 0.00,
    total_cost DECIMAL(15, 2) DEFAULT 0.00,
    
    -- الحالة
    status TEXT DEFAULT 'ACTIVE',  -- ACTIVE, EXPIRED, EXPIRING_SOON, DAMAGED, RECALLED
    
    -- الملاحظات
    notes TEXT,
    quality_check_passed BOOLEAN DEFAULT 1,
    
    -- التواريخ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_pb_product ON product_batches(product_id);
CREATE INDEX IF NOT EXISTS idx_pb_batch_number ON product_batches(batch_number);
CREATE INDEX IF NOT EXISTS idx_pb_expiry_date ON product_batches(expiry_date);
CREATE INDEX IF NOT EXISTS idx_pb_status ON product_batches(status);
CREATE INDEX IF NOT EXISTS idx_pb_supplier ON product_batches(supplier_id);

-- ============================================================================
-- 3. جدول حركات الدفعات (Batch Movements)
-- ============================================================================
CREATE TABLE IF NOT EXISTS batch_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    
    -- نوع الحركة
    movement_type TEXT NOT NULL,  -- RECEIVE, SALE, ADJUSTMENT, TRANSFER, DAMAGE, EXPIRE
    
    -- الكمية
    quantity DECIMAL(15, 2) NOT NULL,
    quantity_before DECIMAL(15, 2),
    quantity_after DECIMAL(15, 2),
    
    -- المرجع
    reference_type TEXT,  -- SALE, PURCHASE, ADJUSTMENT
    reference_id INTEGER,
    reference_number TEXT,
    
    -- التفاصيل
    notes TEXT,
    performed_by INTEGER,
    
    -- التاريخ
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (batch_id) REFERENCES product_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (performed_by) REFERENCES users(id)
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_bm_batch ON batch_movements(batch_id);
CREATE INDEX IF NOT EXISTS idx_bm_product ON batch_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_bm_type ON batch_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_bm_date ON batch_movements(movement_date);

-- ============================================================================
-- 4. جدول تحليل ABC (ABC Analysis Results)
-- ============================================================================
CREATE TABLE IF NOT EXISTS abc_analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    
    -- بيانات المبيعات
    annual_sales_quantity DECIMAL(15, 2) DEFAULT 0.00,
    annual_sales_value DECIMAL(15, 2) DEFAULT 0.00,
    average_unit_price DECIMAL(15, 2) DEFAULT 0.00,
    
    -- بيانات المخزون
    stock_quantity DECIMAL(15, 2) DEFAULT 0.00,
    stock_value DECIMAL(15, 2) DEFAULT 0.00,
    
    -- تحليل ABC
    abc_category TEXT,  -- A, B, C
    percentage_of_total_value DECIMAL(5, 2),
    cumulative_percentage DECIMAL(5, 2),
    rank_position INTEGER,
    
    -- المبيعات
    sales_frequency INTEGER DEFAULT 0,
    last_sale_date DATE,
    
    -- التوصيات
    recommendations TEXT,  -- JSON
    priority_level INTEGER DEFAULT 1,
    
    -- فترة التحليل
    analysis_period_months INTEGER DEFAULT 12,
    analysis_date DATE NOT NULL,
    
    -- التواريخ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_abc_product ON abc_analysis_results(product_id);
CREATE INDEX IF NOT EXISTS idx_abc_category ON abc_analysis_results(abc_category);
CREATE INDEX IF NOT EXISTS idx_abc_date ON abc_analysis_results(analysis_date);
CREATE INDEX IF NOT EXISTS idx_abc_rank ON abc_analysis_results(rank_position);

-- ============================================================================
-- 5. Views للتقارير
-- ============================================================================

-- عرض ملخص الأرصدة الآمنة مع الحالة
CREATE VIEW IF NOT EXISTS v_safety_stock_status AS
SELECT 
    p.id as product_id,
    p.code as product_code,
    p.name as product_name,
    p.stock_quantity as current_stock,
    ssc.reorder_point,
    ssc.safety_stock,
    ssc.maximum_stock,
    ssc.minimum_stock,
    ssc.average_daily_demand,
    ssc.lead_time_days,
    
    -- حساب الحالة
    CASE 
        WHEN p.stock_quantity <= 0 THEN 'STOCKOUT'
        WHEN p.stock_quantity <= ssc.minimum_stock THEN 'CRITICAL'
        WHEN p.stock_quantity <= ssc.reorder_point THEN 'REORDER'
        WHEN p.stock_quantity <= ssc.reorder_point * 1.2 THEN 'APPROACHING'
        ELSE 'NORMAL'
    END as reorder_status,
    
    -- حساب كمية الطلب المقترحة
    CASE 
        WHEN p.stock_quantity < ssc.reorder_point THEN ssc.maximum_stock - p.stock_quantity
        ELSE 0
    END as suggested_order_quantity,
    
    -- أيام حتى نفاذ المخزون
    CASE 
        WHEN ssc.average_daily_demand > 0 THEN CAST(p.stock_quantity / ssc.average_daily_demand AS INTEGER)
        ELSE NULL
    END as days_until_stockout,
    
    ssc.auto_reorder_enabled,
    ssc.last_reorder_date,
    ssc.stockout_count
    
FROM safety_stock_configs ssc
JOIN products p ON ssc.product_id = p.id
WHERE ssc.is_active = 1;

-- عرض الدفعات القريبة من انتهاء الصلاحية
CREATE VIEW IF NOT EXISTS v_expiring_batches AS
SELECT 
    pb.id,
    pb.product_id,
    p.code as product_code,
    p.name as product_name,
    pb.batch_number,
    pb.current_quantity,
    pb.available_quantity,
    pb.manufacturing_date,
    pb.expiry_date,
    pb.warehouse_location,
    pb.supplier_name,
    pb.status,
    
    -- أيام حتى انتهاء الصلاحية
    julianday(pb.expiry_date) - julianday('now') as days_to_expiry,
    
    -- أيام في المخزون
    julianday('now') - julianday(pb.received_date) as days_in_stock,
    
    -- قيمة الدفعة
    pb.current_quantity * pb.unit_cost as batch_value
    
FROM product_batches pb
JOIN products p ON pb.product_id = p.id
WHERE pb.expiry_date IS NOT NULL
AND pb.current_quantity > 0
AND pb.status IN ('ACTIVE', 'EXPIRING_SOON')
ORDER BY pb.expiry_date ASC;

-- عرض ملخص تحليل ABC الحالي
CREATE VIEW IF NOT EXISTS v_current_abc_analysis AS
SELECT 
    p.id as product_id,
    p.code as product_code,
    p.name as product_name,
    p.category,
    abc.abc_category,
    abc.annual_sales_value,
    abc.stock_value,
    abc.percentage_of_total_value,
    abc.rank_position,
    abc.sales_frequency,
    abc.last_sale_date,
    abc.priority_level,
    abc.analysis_date
FROM abc_analysis_results abc
JOIN products p ON abc.product_id = p.id
WHERE abc.analysis_date = (
    SELECT MAX(analysis_date) FROM abc_analysis_results
)
ORDER BY abc.rank_position;

-- عرض المنتجات التي تحتاج إعادة طلب
CREATE VIEW IF NOT EXISTS v_reorder_recommendations AS
SELECT 
    p.id as product_id,
    p.code as product_code,
    p.name as product_name,
    p.stock_quantity as current_stock,
    ssc.reorder_point,
    ssc.safety_stock,
    ssc.maximum_stock - p.stock_quantity as suggested_quantity,
    ssc.economic_order_quantity as eoq,
    
    -- الأولوية
    CASE 
        WHEN p.stock_quantity <= 0 THEN 5
        WHEN p.stock_quantity <= ssc.minimum_stock THEN 4
        WHEN p.stock_quantity <= ssc.reorder_point THEN 3
        ELSE 2
    END as priority,
    
    -- الإلحاح
    CASE 
        WHEN p.stock_quantity <= 0 THEN 'URGENT'
        WHEN p.stock_quantity <= ssc.minimum_stock THEN 'HIGH'
        WHEN p.stock_quantity <= ssc.reorder_point THEN 'MEDIUM'
        ELSE 'LOW'
    END as urgency,
    
    -- أيام حتى نفاذ المخزون
    CASE 
        WHEN ssc.average_daily_demand > 0 THEN CAST(p.stock_quantity / ssc.average_daily_demand AS INTEGER)
        ELSE NULL
    END as days_until_stockout,
    
    ssc.lead_time_days,
    ssc.auto_reorder_enabled
    
FROM safety_stock_configs ssc
JOIN products p ON ssc.product_id = p.id
WHERE ssc.is_active = 1
AND p.stock_quantity <= ssc.reorder_point
ORDER BY priority DESC, current_stock ASC;

-- عرض إحصائيات الدفعات حسب المنتج
CREATE VIEW IF NOT EXISTS v_batch_statistics AS
SELECT 
    p.id as product_id,
    p.code as product_code,
    p.name as product_name,
    COUNT(pb.id) as total_batches,
    SUM(CASE WHEN pb.status = 'ACTIVE' THEN 1 ELSE 0 END) as active_batches,
    SUM(CASE WHEN pb.status = 'EXPIRING_SOON' THEN 1 ELSE 0 END) as expiring_batches,
    SUM(CASE WHEN pb.status = 'EXPIRED' THEN 1 ELSE 0 END) as expired_batches,
    SUM(pb.current_quantity) as total_quantity,
    SUM(pb.current_quantity * pb.unit_cost) as total_value,
    MIN(pb.expiry_date) as earliest_expiry,
    MAX(pb.received_date) as latest_received
FROM products p
LEFT JOIN product_batches pb ON p.id = pb.product_id
GROUP BY p.id;

-- ============================================================================
-- 6. Triggers للتحديث التلقائي
-- ============================================================================

-- تحديث updated_at للأرصدة الآمنة
CREATE TRIGGER IF NOT EXISTS update_ssc_timestamp 
AFTER UPDATE ON safety_stock_configs
FOR EACH ROW
BEGIN
    UPDATE safety_stock_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- تحديث updated_at للدفعات
CREATE TRIGGER IF NOT EXISTS update_batch_timestamp 
AFTER UPDATE ON product_batches
FOR EACH ROW
BEGIN
    UPDATE product_batches SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- تسجيل حركة الدفعة عند التحديث
CREATE TRIGGER IF NOT EXISTS log_batch_movement 
AFTER UPDATE OF current_quantity ON product_batches
FOR EACH ROW
WHEN OLD.current_quantity != NEW.current_quantity
BEGIN
    INSERT INTO batch_movements (
        batch_id, product_id, movement_type, quantity,
        quantity_before, quantity_after, notes, movement_date
    ) VALUES (
        NEW.id, NEW.product_id,
        CASE WHEN NEW.current_quantity > OLD.current_quantity THEN 'RECEIVE' ELSE 'SALE' END,
        ABS(NEW.current_quantity - OLD.current_quantity),
        OLD.current_quantity,
        NEW.current_quantity,
        'Auto-logged movement',
        CURRENT_TIMESTAMP
    );
END;

-- ============================================================================
-- النهاية
-- ============================================================================
