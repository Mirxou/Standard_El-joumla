-- Migration 009: Advanced Reports System
-- نظام التقارير المتقدمة

-- =====================================================
-- جدول قوالب التقارير (Report Templates)
-- =====================================================
CREATE TABLE IF NOT EXISTS report_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    report_type TEXT NOT NULL,
    description TEXT,
    
    -- الفلاتر الافتراضية (JSON)
    default_filters TEXT,
    default_format TEXT DEFAULT 'pdf',
    
    -- إعدادات العرض
    include_charts BOOLEAN DEFAULT 1,
    chart_types TEXT,  -- JSON array
    columns TEXT,  -- JSON array
    group_by TEXT,
    sort_by TEXT,
    
    -- الحالة
    is_default BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    
    -- التوقيتات
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_report_type CHECK (
        report_type IN (
            'sales_summary', 'sales_detailed', 'sales_by_product', 
            'sales_by_customer', 'sales_by_category', 'sales_by_employee',
            'inventory_movement', 'inventory_valuation', 'inventory_aging',
            'inventory_turnover', 'inventory_reorder', 'inventory_count',
            'financial_income', 'financial_balance', 'financial_cashflow',
            'financial_trial_balance', 'financial_ledger', 'financial_profit_loss',
            'customer_analysis', 'supplier_analysis', 'payment_analysis', 'debt_analysis'
        )
    ),
    CONSTRAINT check_format CHECK (
        default_format IN ('pdf', 'excel', 'csv', 'html', 'json')
    )
);

-- فهارس لقوالب التقارير
CREATE INDEX IF NOT EXISTS idx_report_templates_type 
    ON report_templates(report_type);
CREATE INDEX IF NOT EXISTS idx_report_templates_active 
    ON report_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_report_templates_default 
    ON report_templates(is_default);

-- =====================================================
-- جدول التقارير المحفوظة (Saved Reports)
-- =====================================================
CREATE TABLE IF NOT EXISTS saved_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER,
    
    -- معلومات التقرير
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    
    -- الفلاتر المستخدمة (JSON)
    filters TEXT,
    
    -- معلومات التوليد
    generated_by TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    format TEXT DEFAULT 'pdf',
    
    -- مسار الملف (إذا تم التصدير)
    file_path TEXT,
    file_size INTEGER,
    
    -- الإحصائيات
    total_lines INTEGER DEFAULT 0,
    execution_time REAL,  -- بالثواني
    
    -- الملاحظات
    notes TEXT,
    
    -- التوقيتات
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE SET NULL
);

-- فهارس للتقارير المحفوظة
CREATE INDEX IF NOT EXISTS idx_saved_reports_type 
    ON saved_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_saved_reports_template 
    ON saved_reports(template_id);
CREATE INDEX IF NOT EXISTS idx_saved_reports_generated_at 
    ON saved_reports(generated_at);
CREATE INDEX IF NOT EXISTS idx_saved_reports_generated_by 
    ON saved_reports(generated_by);

-- =====================================================
-- جدول جدولة التقارير (Report Schedules)
-- =====================================================
CREATE TABLE IF NOT EXISTS report_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    
    -- معلومات الجدولة
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    
    -- التكرار
    frequency TEXT NOT NULL,  -- daily, weekly, monthly, yearly
    schedule_time TIME,
    schedule_day_of_week INTEGER,  -- 0-6 (Sunday-Saturday)
    schedule_day_of_month INTEGER,  -- 1-31
    
    -- المستلمون (JSON array of emails)
    recipients TEXT,
    
    -- صيغة التقرير
    export_format TEXT DEFAULT 'pdf',
    
    -- آخر تنفيذ
    last_run_at TIMESTAMP,
    last_run_status TEXT,  -- success, failed
    next_run_at TIMESTAMP,
    
    -- العداد
    run_count INTEGER DEFAULT 0,
    
    -- التوقيتات
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (template_id) REFERENCES report_templates(id) ON DELETE CASCADE,
    CONSTRAINT check_frequency CHECK (
        frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
    ),
    CONSTRAINT check_export_format CHECK (
        export_format IN ('pdf', 'excel', 'csv', 'html')
    )
);

-- فهارس لجدولة التقارير
CREATE INDEX IF NOT EXISTS idx_report_schedules_template 
    ON report_schedules(template_id);
CREATE INDEX IF NOT EXISTS idx_report_schedules_active 
    ON report_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run 
    ON report_schedules(next_run_at);

-- =====================================================
-- Views للتقارير
-- =====================================================

-- عرض ملخص التقارير المحفوظة
CREATE VIEW IF NOT EXISTS v_saved_reports_summary AS
SELECT 
    sr.id,
    sr.title,
    sr.report_type,
    sr.generated_by,
    sr.generated_at,
    sr.format,
    sr.total_lines,
    sr.execution_time,
    rt.name as template_name,
    CASE 
        WHEN sr.file_path IS NOT NULL THEN 'exported'
        ELSE 'not_exported'
    END as export_status
FROM saved_reports sr
LEFT JOIN report_templates rt ON sr.template_id = rt.id
ORDER BY sr.generated_at DESC;

-- عرض إحصائيات التقارير
CREATE VIEW IF NOT EXISTS v_reports_statistics AS
SELECT 
    report_type,
    COUNT(*) as total_reports,
    AVG(execution_time) as avg_execution_time,
    SUM(total_lines) as total_lines_generated,
    MAX(generated_at) as last_generated_at
FROM saved_reports
GROUP BY report_type;

-- عرض الجدولة النشطة
CREATE VIEW IF NOT EXISTS v_active_schedules AS
SELECT 
    rs.id,
    rs.name,
    rt.name as template_name,
    rt.report_type,
    rs.frequency,
    rs.schedule_time,
    rs.next_run_at,
    rs.last_run_at,
    rs.last_run_status,
    rs.run_count
FROM report_schedules rs
JOIN report_templates rt ON rs.template_id = rt.id
WHERE rs.is_active = 1
ORDER BY rs.next_run_at;

-- =====================================================
-- Triggers
-- =====================================================

-- تحديث تاريخ التعديل لقوالب التقارير
CREATE TRIGGER IF NOT EXISTS update_report_template_timestamp
AFTER UPDATE ON report_templates
BEGIN
    UPDATE report_templates 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- تحديث تاريخ التعديل لجدولة التقارير
CREATE TRIGGER IF NOT EXISTS update_report_schedule_timestamp
AFTER UPDATE ON report_schedules
BEGIN
    UPDATE report_schedules 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- تحديث عداد التشغيل والتاريخ التالي
CREATE TRIGGER IF NOT EXISTS increment_schedule_run_count
AFTER UPDATE OF last_run_at ON report_schedules
WHEN NEW.last_run_at != OLD.last_run_at
BEGIN
    UPDATE report_schedules 
    SET run_count = run_count + 1
    WHERE id = NEW.id;
END;

-- =====================================================
-- بيانات افتراضية
-- =====================================================

-- قوالب افتراضية للتقارير
INSERT OR IGNORE INTO report_templates (name, report_type, description, is_default) VALUES
('تقرير المبيعات اليومي', 'sales_summary', 'ملخص المبيعات اليومي الافتراضي', 1),
('تقرير حركة المخزون الشهري', 'inventory_movement', 'حركة المخزون الشهرية', 1),
('قائمة الدخل الشهرية', 'financial_income', 'قائمة الدخل للفترة الشهرية', 1),
('ميزان المراجعة', 'financial_trial_balance', 'ميزان المراجعة الدوري', 1);

-- =====================================================
-- النهاية
-- =====================================================
