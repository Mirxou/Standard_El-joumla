-- ============================================================================
-- Migration 005: Create Purchase Orders System Tables
-- نظام أوامر الشراء والاستلام وتقييم الموردين
-- ============================================================================

-- ============================================================================
-- 1. جدول أوامر الشراء (Purchase Orders)
-- ============================================================================
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT NOT NULL UNIQUE,
    
    -- معلومات المورد
    supplier_id INTEGER NOT NULL,
    supplier_name TEXT,
    supplier_contact TEXT,
    
    -- التواريخ
    order_date DATE NOT NULL,
    required_date DATE,
    delivery_date DATE,
    expected_delivery_date DATE,
    
    -- الحالة والأولوية
    status TEXT NOT NULL DEFAULT 'DRAFT',  -- DRAFT, PENDING_APPROVAL, APPROVED, etc.
    priority TEXT NOT NULL DEFAULT 'NORMAL',  -- LOW, NORMAL, HIGH, URGENT
    
    -- شروط التسليم والدفع
    delivery_terms TEXT,  -- EXW, FOB, CIF, DAP, DDP
    payment_terms TEXT,   -- CASH, NET_7, NET_30, etc.
    currency TEXT DEFAULT 'DZD',
    
    -- المبالغ المالية
    subtotal DECIMAL(15, 2) DEFAULT 0.00,
    discount_amount DECIMAL(15, 2) DEFAULT 0.00,
    tax_amount DECIMAL(15, 2) DEFAULT 0.00,
    shipping_cost DECIMAL(15, 2) DEFAULT 0.00,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    
    -- الملاحظات
    notes TEXT,
    terms_conditions TEXT,
    shipping_address TEXT,
    billing_address TEXT,
    
    -- الموافقات
    approved_by INTEGER,
    approval_date DATE,
    approval_notes TEXT,
    
    -- حالة الإرسال
    sent_date DATE,
    confirmed_date DATE,
    confirmed_by_supplier BOOLEAN DEFAULT FALSE,
    
    -- التتبع
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- المدفوعات
    total_paid DECIMAL(15, 2) DEFAULT 0.00,
    remaining_amount DECIMAL(15, 2) DEFAULT 0.00,
    
    -- العلاقات
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- الفهارس لجدول أوامر الشراء
CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(po_number);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_order_date ON purchase_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_po_required_date ON purchase_orders(required_date);
CREATE INDEX IF NOT EXISTS idx_po_priority ON purchase_orders(priority);

-- ============================================================================
-- 2. جدول بنود أوامر الشراء (Purchase Order Items)
-- ============================================================================
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_order_id INTEGER NOT NULL,
    
    -- معلومات المنتج
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    product_code TEXT,
    
    -- الكميات
    quantity_ordered DECIMAL(15, 3) NOT NULL,
    quantity_received DECIMAL(15, 3) DEFAULT 0.000,
    quantity_pending DECIMAL(15, 3) DEFAULT 0.000,
    
    -- الأسعار
    unit_price DECIMAL(15, 2) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0.00,
    tax_percent DECIMAL(5, 2) DEFAULT 0.00,
    
    -- المبالغ
    subtotal DECIMAL(15, 2) DEFAULT 0.00,
    discount_amount DECIMAL(15, 2) DEFAULT 0.00,
    tax_amount DECIMAL(15, 2) DEFAULT 0.00,
    net_amount DECIMAL(15, 2) DEFAULT 0.00,
    
    -- التواريخ
    required_date DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    
    -- المواصفات
    specifications TEXT,
    quality_requirements TEXT,
    packaging_requirements TEXT,
    
    -- الملاحظات
    notes TEXT,
    
    -- التتبع
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- العلاقات
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- الفهارس لجدول بنود أوامر الشراء
CREATE INDEX IF NOT EXISTS idx_po_items_po ON purchase_order_items(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_po_items_product ON purchase_order_items(product_id);

-- ============================================================================
-- 3. جدول إشعارات الاستلام (Receiving Notes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS receiving_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receiving_number TEXT NOT NULL UNIQUE,
    
    -- أمر الشراء المرتبط
    purchase_order_id INTEGER NOT NULL,
    po_number TEXT,
    
    -- المورد
    supplier_id INTEGER NOT NULL,
    supplier_name TEXT,
    
    -- معلومات الشحنة
    shipment_number TEXT,
    carrier_name TEXT,
    tracking_number TEXT,
    
    -- التواريخ
    receiving_date DATE NOT NULL,
    shipment_date DATE,
    expected_date DATE,
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING, IN_PROGRESS, COMPLETED, etc.
    
    -- موظف الاستلام
    received_by INTEGER,
    receiver_name TEXT,
    
    -- الملاحظات
    notes TEXT,
    discrepancy_notes TEXT,  -- ملاحظات الاختلافات
    
    -- التوقيعات
    receiver_signature TEXT,
    supervisor_signature TEXT,
    
    -- التتبع
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- العلاقات
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (received_by) REFERENCES users(id)
);

-- الفهارس لجدول إشعارات الاستلام
CREATE INDEX IF NOT EXISTS idx_rn_number ON receiving_notes(receiving_number);
CREATE INDEX IF NOT EXISTS idx_rn_po ON receiving_notes(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_rn_supplier ON receiving_notes(supplier_id);
CREATE INDEX IF NOT EXISTS idx_rn_date ON receiving_notes(receiving_date);
CREATE INDEX IF NOT EXISTS idx_rn_status ON receiving_notes(status);

-- ============================================================================
-- 4. جدول بنود الاستلام (Receiving Items)
-- ============================================================================
CREATE TABLE IF NOT EXISTS receiving_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receiving_id INTEGER NOT NULL,
    po_item_id INTEGER NOT NULL,
    
    -- معلومات المنتج
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    product_code TEXT,
    
    -- الكميات
    quantity_ordered DECIMAL(15, 3) NOT NULL,
    quantity_received DECIMAL(15, 3) NOT NULL,
    quantity_accepted DECIMAL(15, 3) DEFAULT 0.000,
    quantity_rejected DECIMAL(15, 3) DEFAULT 0.000,
    quantity_damaged DECIMAL(15, 3) DEFAULT 0.000,
    
    -- الفحص
    inspection_status TEXT DEFAULT 'NOT_REQUIRED',  -- NOT_REQUIRED, PENDING, IN_PROGRESS, PASSED, FAILED
    quality_rating TEXT,  -- EXCELLENT, GOOD, ACCEPTABLE, POOR, REJECTED
    inspection_notes TEXT,
    inspector_name TEXT,
    inspection_date DATE,
    
    -- التخزين
    warehouse_location TEXT,
    batch_number TEXT,
    serial_numbers TEXT,  -- أرقام تسلسلية مفصولة بفاصلة
    expiry_date DATE,
    
    -- المطابقة
    matches_specifications BOOLEAN DEFAULT TRUE,
    variance_reason TEXT,
    
    -- الملاحظات
    notes TEXT,
    
    -- العلاقات
    FOREIGN KEY (receiving_id) REFERENCES receiving_notes(id) ON DELETE CASCADE,
    FOREIGN KEY (po_item_id) REFERENCES purchase_order_items(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- الفهارس لجدول بنود الاستلام
CREATE INDEX IF NOT EXISTS idx_ri_receiving ON receiving_items(receiving_id);
CREATE INDEX IF NOT EXISTS idx_ri_po_item ON receiving_items(po_item_id);
CREATE INDEX IF NOT EXISTS idx_ri_product ON receiving_items(product_id);
CREATE INDEX IF NOT EXISTS idx_ri_inspection ON receiving_items(inspection_status);

-- ============================================================================
-- 5. جدول تقييم الموردين (Supplier Evaluations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS supplier_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    supplier_name TEXT,
    
    -- الفترة التقييمية
    evaluation_period_start DATE,
    evaluation_period_end DATE,
    
    -- معايير التقييم (من 1 إلى 5)
    quality_score DECIMAL(3, 2) DEFAULT 0.00,          -- جودة المنتجات
    delivery_score DECIMAL(3, 2) DEFAULT 0.00,         -- الالتزام بالمواعيد
    pricing_score DECIMAL(3, 2) DEFAULT 0.00,          -- التنافسية السعرية
    communication_score DECIMAL(3, 2) DEFAULT 0.00,    -- التواصل والاستجابة
    reliability_score DECIMAL(3, 2) DEFAULT 0.00,      -- الموثوقية
    
    -- المقاييس الفعلية
    total_orders INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    on_time_deliveries INTEGER DEFAULT 0,
    late_deliveries INTEGER DEFAULT 0,
    rejected_shipments INTEGER DEFAULT 0,
    total_value DECIMAL(15, 2) DEFAULT 0.00,
    
    -- معدلات
    on_time_delivery_rate DECIMAL(5, 2) DEFAULT 0.00,
    quality_acceptance_rate DECIMAL(5, 2) DEFAULT 0.00,
    average_lead_time_days DECIMAL(10, 2) DEFAULT 0.00,
    
    -- التقييم النهائي
    overall_score DECIMAL(3, 2) DEFAULT 0.00,  -- من 5
    grade TEXT,  -- A+, A, B+, B, C, D, F
    
    -- التوصيات
    is_approved BOOLEAN DEFAULT TRUE,
    is_preferred BOOLEAN DEFAULT FALSE,
    notes TEXT,
    recommendations TEXT,
    
    -- التتبع
    evaluated_by INTEGER,
    evaluation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- العلاقات
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (evaluated_by) REFERENCES users(id)
);

-- الفهارس لجدول تقييم الموردين
CREATE INDEX IF NOT EXISTS idx_se_supplier ON supplier_evaluations(supplier_id);
CREATE INDEX IF NOT EXISTS idx_se_date ON supplier_evaluations(evaluation_date);
CREATE INDEX IF NOT EXISTS idx_se_score ON supplier_evaluations(overall_score);
CREATE INDEX IF NOT EXISTS idx_se_grade ON supplier_evaluations(grade);

-- ============================================================================
-- 6. Views للتقارير
-- ============================================================================

-- عرض ملخص أوامر الشراء
CREATE VIEW IF NOT EXISTS v_purchase_orders_summary AS
SELECT 
    po.id,
    po.po_number,
    po.supplier_name,
    po.order_date,
    po.required_date,
    po.status,
    po.priority,
    po.total_amount,
    po.total_paid,
    po.remaining_amount,
    COUNT(poi.id) as total_items,
    SUM(poi.quantity_ordered) as total_quantity_ordered,
    SUM(poi.quantity_received) as total_quantity_received,
    SUM(poi.quantity_pending) as total_quantity_pending,
    CASE 
        WHEN SUM(poi.quantity_ordered) > 0 
        THEN (SUM(poi.quantity_received) / SUM(poi.quantity_ordered)) * 100
        ELSE 0 
    END as receipt_percentage
FROM purchase_orders po
LEFT JOIN purchase_order_items poi ON po.id = poi.purchase_order_id
GROUP BY po.id;

-- عرض ملخص الاستلام
CREATE VIEW IF NOT EXISTS v_receiving_summary AS
SELECT 
    rn.id,
    rn.receiving_number,
    rn.po_number,
    rn.supplier_name,
    rn.receiving_date,
    rn.status,
    rn.receiver_name,
    COUNT(ri.id) as total_items,
    SUM(ri.quantity_received) as total_received,
    SUM(ri.quantity_accepted) as total_accepted,
    SUM(ri.quantity_rejected) as total_rejected,
    CASE 
        WHEN SUM(ri.quantity_received) > 0 
        THEN (SUM(ri.quantity_accepted) / SUM(ri.quantity_received)) * 100
        ELSE 0 
    END as acceptance_rate
FROM receiving_notes rn
LEFT JOIN receiving_items ri ON rn.id = ri.receiving_id
GROUP BY rn.id;

-- عرض أداء الموردين
CREATE VIEW IF NOT EXISTS v_supplier_performance AS
SELECT 
    s.id as supplier_id,
    s.name as supplier_name,
    COUNT(DISTINCT po.id) as total_orders,
    SUM(po.total_amount) as total_value,
    COUNT(DISTINCT CASE WHEN rn.receiving_date <= po.required_date THEN rn.id END) as on_time_deliveries,
    COUNT(DISTINCT rn.id) as total_deliveries,
    CASE 
        WHEN COUNT(DISTINCT rn.id) > 0 
        THEN (COUNT(DISTINCT CASE WHEN rn.receiving_date <= po.required_date THEN rn.id END) * 100.0 / COUNT(DISTINCT rn.id))
        ELSE 0 
    END as on_time_rate,
    AVG(CASE 
        WHEN rn.receiving_date IS NOT NULL AND po.order_date IS NOT NULL 
        THEN julianday(rn.receiving_date) - julianday(po.order_date)
        ELSE NULL 
    END) as avg_lead_time_days,
    se.overall_score as latest_score,
    se.grade as latest_grade
FROM suppliers s
LEFT JOIN purchase_orders po ON s.id = po.supplier_id
LEFT JOIN receiving_notes rn ON po.id = rn.purchase_order_id
LEFT JOIN supplier_evaluations se ON s.id = se.supplier_id AND se.id = (
    SELECT id FROM supplier_evaluations WHERE supplier_id = s.id ORDER BY evaluation_date DESC LIMIT 1
)
GROUP BY s.id;

-- ============================================================================
-- 7. Triggers للتحديث التلقائي
-- ============================================================================

-- تحديث updated_at عند التحديث
CREATE TRIGGER IF NOT EXISTS update_po_timestamp 
AFTER UPDATE ON purchase_orders
FOR EACH ROW
BEGIN
    UPDATE purchase_orders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_rn_timestamp 
AFTER UPDATE ON receiving_notes
FOR EACH ROW
BEGIN
    UPDATE receiving_notes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_se_timestamp 
AFTER UPDATE ON supplier_evaluations
FOR EACH ROW
BEGIN
    UPDATE supplier_evaluations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- النهاية
-- ============================================================================
