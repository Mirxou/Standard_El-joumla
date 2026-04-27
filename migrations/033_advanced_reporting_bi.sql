-- Migration 033: Advanced Reporting & Business Intelligence Tables
-- Phase 8 Database Schema Extensions

PRAGMA foreign_keys = ON;

-- ============================================
-- 1. Report Templates Table
-- ============================================
CREATE TABLE IF NOT EXISTS report_templates (
    template_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- 'sales', 'inventory', 'financial', 'operational'
    template_config TEXT NOT NULL, -- JSON configuration
    query_template TEXT, -- SQL template with placeholders
    ui_config TEXT, -- JSON UI configuration for builder
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    is_public BOOLEAN DEFAULT 0
);

-- ============================================
-- 2. Generated Reports Table
-- ============================================
CREATE TABLE IF NOT EXISTS generated_reports (
    report_id TEXT PRIMARY KEY,
    template_id TEXT,
    report_name TEXT NOT NULL,
    parameters TEXT, -- JSON parameters used
    generated_data TEXT, -- JSON report data
    execution_time REAL, -- seconds
    row_count INTEGER,
    generated_by TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    file_path TEXT, -- path to exported file if any
    FOREIGN KEY (template_id) REFERENCES report_templates(template_id)
);

-- ============================================
-- 3. Dashboard Configurations Table
-- ============================================
CREATE TABLE IF NOT EXISTS dashboard_configs (
    dashboard_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- 'executive', 'operational', 'analytical'
    layout_config TEXT NOT NULL, -- JSON layout configuration
    widgets_config TEXT NOT NULL, -- JSON widgets configuration
    data_sources TEXT, -- JSON data source mappings
    refresh_interval INTEGER DEFAULT 300, -- seconds
    is_public BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. Dashboard Widgets Table
-- ============================================
CREATE TABLE IF NOT EXISTS dashboard_widgets (
    widget_id TEXT PRIMARY KEY,
    dashboard_id TEXT NOT NULL,
    widget_type TEXT NOT NULL, -- 'chart', 'kpi', 'table', 'metric'
    title TEXT NOT NULL,
    position_x INTEGER,
    position_y INTEGER,
    width INTEGER,
    height INTEGER,
    config TEXT NOT NULL, -- JSON widget configuration
    data_query TEXT, -- SQL query or data source
    refresh_rate INTEGER DEFAULT 60, -- seconds
    is_visible BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dashboard_id) REFERENCES dashboard_configs(dashboard_id) ON DELETE CASCADE
);

-- ============================================
-- 5. KPI Definitions Table
-- ============================================
CREATE TABLE IF NOT EXISTS kpi_definitions (
    kpi_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- 'financial', 'operational', 'customer', 'product'
    calculation_formula TEXT NOT NULL, -- SQL expression or formula
    target_value REAL,
    target_operator TEXT DEFAULT '>', -- '>', '<', '>=', '<=', '='
    unit TEXT,
    frequency TEXT DEFAULT 'daily', -- 'real_time', 'hourly', 'daily', 'weekly', 'monthly'
    data_source TEXT, -- table or view name
    is_active BOOLEAN DEFAULT 1,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. KPI Values Table (Time Series)
-- ============================================
CREATE TABLE IF NOT EXISTS kpi_values (
    value_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id TEXT NOT NULL,
    value REAL NOT NULL,
    target_value REAL,
    calculation_date DATETIME NOT NULL,
    period_start DATETIME,
    period_end DATETIME,
    metadata TEXT, -- JSON additional data
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kpi_id) REFERENCES kpi_definitions(kpi_id) ON DELETE CASCADE
);

-- ============================================
-- 7. Report Schedules Table
-- ============================================
CREATE TABLE IF NOT EXISTS report_schedules (
    schedule_id TEXT PRIMARY KEY,
    report_template_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    schedule_config TEXT NOT NULL, -- JSON cron expression and parameters
    parameters TEXT, -- JSON default parameters
    recipients TEXT, -- JSON email recipients
    output_format TEXT DEFAULT 'pdf', -- 'pdf', 'excel', 'csv'
    is_active BOOLEAN DEFAULT 1,
    last_run DATETIME,
    next_run DATETIME,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_template_id) REFERENCES report_templates(template_id)
);

-- ============================================
-- 8. Business Insights Table
-- ============================================
CREATE TABLE IF NOT EXISTS business_insights (
    insight_id TEXT PRIMARY KEY,
    insight_type TEXT NOT NULL, -- 'trend', 'anomaly', 'opportunity', 'warning'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    data_source TEXT, -- what data triggered this insight
    insight_data TEXT NOT NULL, -- JSON insight details
    confidence_score REAL, -- 0-1 confidence level
    impact_level TEXT, -- 'low', 'medium', 'high', 'critical'
    recommended_actions TEXT, -- JSON list of actions
    is_read BOOLEAN DEFAULT 0,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_report_templates_category ON report_templates(category, is_active);
CREATE INDEX IF NOT EXISTS idx_generated_reports_template ON generated_reports(template_id, generated_at);
CREATE INDEX IF NOT EXISTS idx_dashboard_configs_category ON dashboard_configs(category, is_active);
CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_dashboard ON dashboard_widgets(dashboard_id, is_visible);
CREATE INDEX IF NOT EXISTS idx_kpi_definitions_category ON kpi_definitions(category, is_active);
CREATE INDEX IF NOT EXISTS idx_kpi_values_kpi_date ON kpi_values(kpi_id, calculation_date);
CREATE INDEX IF NOT EXISTS idx_report_schedules_template ON report_schedules(report_template_id, is_active);
CREATE INDEX IF NOT EXISTS idx_business_insights_type ON business_insights(insight_type, impact_level, generated_at);

-- ============================================
-- Sample Data for Testing
-- ============================================

-- Sample Report Templates
INSERT OR IGNORE INTO report_templates (template_id, name, description, category, template_config, query_template) VALUES
('TEMPLATE_SALES_SUMMARY', 'تقرير ملخص المبيعات', 'تقرير شامل للمبيعات الشهرية', 'sales',
 '{"fields": ["date", "total_sales", "order_count"], "group_by": ["month"], "filters": []}',
 'SELECT strftime(''%Y-%m'', created_at) as month, SUM(total_amount) as total_sales, COUNT(*) as order_count FROM sales WHERE created_at >= ? GROUP BY month ORDER BY month'),

('TEMPLATE_INVENTORY_STATUS', 'تقرير حالة المخزون', 'تقرير مفصل لحالة المخزون', 'inventory',
 '{"fields": ["product_name", "current_stock", "min_stock", "max_stock"], "filters": []}',
 'SELECT p.name as product_name, SUM(wi.quantity) as current_stock, SUM(wi.min_stock) as min_stock, SUM(wi.max_stock) as max_stock FROM warehouse_inventory wi JOIN products p ON wi.product_id = p.id GROUP BY p.id, p.name'),

('TEMPLATE_FINANCIAL_PERFORMANCE', 'تقرير الأداء المالي', 'تقرير الأداء المالي الشهري', 'financial',
 '{"fields": ["month", "revenue", "costs", "profit", "margin"], "filters": []}',
 'SELECT month, revenue, costs, (revenue - costs) as profit, ROUND((revenue - costs) / revenue * 100, 2) as margin FROM financial_summary ORDER BY month');

-- Sample KPI Definitions
INSERT OR IGNORE INTO kpi_definitions (kpi_id, name, description, category, calculation_formula, target_value, unit, frequency) VALUES
('KPI_TOTAL_SALES', 'إجمالي المبيعات', 'إجمالي قيمة المبيعات', 'financial', 'SELECT SUM(total_amount) FROM sales WHERE DATE(created_at) = DATE(?)', 50000, 'SAR', 'daily'),
('KPI_ORDER_COUNT', 'عدد الطلبات', 'عدد الطلبات المكتملة', 'operational', 'SELECT COUNT(*) FROM sales WHERE status = ''completed'' AND DATE(created_at) = DATE(?)', 50, 'orders', 'daily'),
('KPI_INVENTORY_TURNOVER', 'معدل دوران المخزون', 'معدل دوران المخزون', 'operational', 'SELECT AVG(turnover_rate) FROM inventory_turnover WHERE month = strftime(''%Y-%m'', ?)', 4.0, 'ratio', 'monthly'),
('KPI_CUSTOMER_RETENTION', 'معدل الاحتفاظ بالعملاء', 'نسبة العملاء المحتفظ بهم', 'customer', 'SELECT AVG(retention_rate) FROM customer_retention WHERE period_end >= ? AND period_end <= ?', 85.0, '%', 'monthly');

-- Sample Dashboard Configuration
INSERT OR IGNORE INTO dashboard_configs (dashboard_id, name, description, category, layout_config, widgets_config) VALUES
('DASHBOARD_EXECUTIVE', 'لوحة المدير التنفيذي', 'لوحة تحكم شاملة للمدير التنفيذي', 'executive',
 '{"grid_columns": 12, "grid_rows": 8}',
 '[{"widget_id": "sales_chart", "type": "chart", "position": {"x": 0, "y": 0, "width": 8, "height": 4}}, {"widget_id": "kpi_panel", "type": "kpi", "position": {"x": 8, "y": 0, "width": 4, "height": 4}}]');

-- Sample Business Insights (using existing table structure)
INSERT OR IGNORE INTO business_insights (insight_id, insight_type, title, description, confidence_score, impact_level, recommended_actions) VALUES
('INSIGHT_SALES_TREND_PHASE8', 'trend', 'اتجاه إيجابي في المبيعات', 'المبيعات زادت بنسبة 15% خلال الشهر الماضي', 0.85, 'medium', '["زيادة المخزون", "تعزيز الحملات التسويقية"]'),
('INSIGHT_INVENTORY_LOW_PHASE8', 'warning', 'مخزون منخفض لمنتجات رئيسية', '5 منتجات وصلت لحد إعادة الطلب', 0.95, 'high', '["إعادة طلب فورية", "مراجعة سياسات المخزون"]');
