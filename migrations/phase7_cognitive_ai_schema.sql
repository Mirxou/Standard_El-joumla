-- قاعدة بيانات المرحلة 7: الذكاء الاصطناعي المعرفي وتحليلات البيانات المتقدمة
-- Phase 7 Database Schema: Cognitive AI & Advanced Analytics

-- =============================================================================
-- جداول الذكاء الاصطناعي المعرفي
-- =============================================================================

-- جدول قواعد القرار
CREATE TABLE IF NOT EXISTS decision_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    condition TEXT NOT NULL,
    action TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    success_rate REAL DEFAULT 0.0,
    last_triggered DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول سيناريوهات القرار
CREATE TABLE IF NOT EXISTS decision_scenarios (
    scenario_id TEXT PRIMARY KEY,
    decision_type TEXT NOT NULL, -- 'strategic', 'operational', 'tactical'
    title TEXT NOT NULL,
    description TEXT,
    options TEXT, -- JSON array of decision options
    context_data TEXT, -- JSON context information
    risk_assessment TEXT, -- JSON risk analysis
    recommended_option TEXT,
    confidence_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- جدول نتائج القرارات
CREATE TABLE IF NOT EXISTS decision_outcomes (
    outcome_id TEXT PRIMARY KEY,
    scenario_id TEXT,
    chosen_option TEXT,
    actual_outcome TEXT, -- JSON actual results
    predicted_outcome TEXT, -- JSON predicted results
    outcome_accuracy REAL,
    lessons_learned TEXT, -- JSON lessons learned
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES decision_scenarios(scenario_id)
);

-- جدول تحسينات العمليات
CREATE TABLE IF NOT EXISTS process_optimizations (
    process_name TEXT PRIMARY KEY,
    current_performance TEXT, -- JSON current metrics
    identified_bottlenecks TEXT, -- JSON bottlenecks
    suggested_improvements TEXT, -- JSON improvements
    expected_impact TEXT, -- JSON impact analysis
    implementation_priority TEXT, -- JSON priority list
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- جداول التنبؤات الذكية
-- =============================================================================

-- جدول نماذج التنبؤ
CREATE TABLE IF NOT EXISTS forecast_models (
    model_id TEXT PRIMARY KEY,
    model_type TEXT NOT NULL, -- 'linear', 'rf', 'arima', 'neural'
    target_variable TEXT NOT NULL,
    features TEXT, -- JSON array of features
    training_data_period INTEGER, -- days
    accuracy_score REAL,
    last_trained DATETIME,
    model_parameters TEXT, -- JSON parameters
    performance_metrics TEXT, -- JSON metrics
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول نتائج التنبؤ
CREATE TABLE IF NOT EXISTS forecast_results (
    forecast_id TEXT PRIMARY KEY,
    model_id TEXT,
    target_variable TEXT,
    forecast_horizon INTEGER, -- days
    predicted_values TEXT, -- JSON array of predictions
    confidence_intervals TEXT, -- JSON array of intervals
    forecast_dates TEXT, -- JSON array of dates
    accuracy_metrics TEXT, -- JSON accuracy metrics
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    influencing_factors TEXT, -- JSON factors
    FOREIGN KEY (model_id) REFERENCES forecast_models(model_id)
);

-- جدول أنماط الطلب
CREATE TABLE IF NOT EXISTS demand_patterns (
    pattern_id TEXT PRIMARY KEY,
    product_id TEXT,
    pattern_type TEXT NOT NULL, -- 'seasonal', 'trend', 'cyclical', 'irregular'
    seasonality_period INTEGER,
    trend_direction TEXT, -- 'increasing', 'decreasing', 'stable'
    confidence_level REAL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    pattern_data TEXT -- JSON pattern details
);

-- =============================================================================
-- جداول التحليلات المتقدمة للأعمال
-- =============================================================================

-- جدول رؤى الأعمال
CREATE TABLE IF NOT EXISTS business_insights (
    insight_id TEXT PRIMARY KEY,
    insight_type TEXT NOT NULL, -- 'performance', 'trend', 'anomaly', 'opportunity'
    title TEXT NOT NULL,
    description TEXT,
    data_points TEXT, -- JSON data points
    confidence_score REAL,
    impact_level TEXT, -- 'high', 'medium', 'low'
    recommended_actions TEXT, -- JSON actions
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- جدول شرائح العملاء
CREATE TABLE IF NOT EXISTS customer_segments (
    segment_id TEXT PRIMARY KEY,
    segment_name TEXT NOT NULL,
    customer_count INTEGER,
    characteristics TEXT, -- JSON characteristics
    behavior_patterns TEXT, -- JSON behavior patterns
    value_metrics TEXT, -- JSON value metrics
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول مقاييس الأعمال
CREATE TABLE IF NOT EXISTS business_metrics (
    metric_id TEXT PRIMARY KEY,
    metric_name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'financial', 'operational', 'customer', 'product'
    current_value REAL,
    previous_value REAL,
    target_value REAL,
    trend TEXT, -- 'improving', 'declining', 'stable'
    calculation_period TEXT, -- 'daily', 'weekly', 'monthly', 'quarterly'
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول الرؤى التنبؤية
CREATE TABLE IF NOT EXISTS predictive_insights (
    insight_id TEXT PRIMARY KEY,
    prediction_type TEXT NOT NULL,
    target_metric TEXT NOT NULL,
    predicted_value REAL,
    confidence_interval TEXT, -- JSON interval
    time_horizon TEXT, -- 'short_term', 'medium_term', 'long_term'
    influencing_factors TEXT, -- JSON factors
    risk_assessment TEXT, -- JSON risk assessment
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- جداول الذكاء الاصطناعي المعرفي
-- =============================================================================

-- جدول نماذج الذكاء الاصطناعي
CREATE TABLE IF NOT EXISTS ai_models (
    model_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL, -- 'cognitive', 'predictive', 'nlp', 'computer_vision'
    purpose TEXT,
    accuracy_score REAL,
    training_status TEXT, -- 'training', 'trained', 'failed'
    last_trained DATETIME,
    model_path TEXT, -- path to saved model
    parameters TEXT, -- JSON parameters
    performance_metrics TEXT, -- JSON metrics
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    algorithm TEXT,
    feature_importance TEXT, -- JSON
    confusion_matrix TEXT, -- JSON
    cross_validation_scores TEXT, -- JSON
    hyperparameters TEXT, -- JSON
    feature_names TEXT -- JSON
);


-- جدول بيانات التدريب
CREATE TABLE IF NOT EXISTS training_data (
    data_id TEXT PRIMARY KEY,
    model_id TEXT,
    data_type TEXT NOT NULL, -- 'sales', 'customer', 'product', 'operational'
    data_content TEXT, -- JSON data
    labels TEXT, -- JSON labels for supervised learning
    quality_score REAL,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    used_in_training BOOLEAN DEFAULT 0,
    FOREIGN KEY (model_id) REFERENCES ai_models(model_id)
);

-- جدول نتائج الذكاء الاصطناعي
CREATE TABLE IF NOT EXISTS ai_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT,
    input_data TEXT, -- JSON input
    output_data TEXT, -- JSON output
    confidence_score REAL,
    processing_time REAL, -- seconds
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ai_models(model_id)
);

-- =============================================================================
-- جداول التحليلات المتقدمة
-- =============================================================================

-- جدول تحليلات الأداء
CREATE TABLE IF NOT EXISTS performance_analytics (
    analysis_id TEXT PRIMARY KEY,
    analysis_type TEXT NOT NULL, -- 'comprehensive', 'financial', 'operational', 'customer'
    time_period TEXT,
    metrics TEXT, -- JSON metrics
    insights TEXT, -- JSON insights
    recommendations TEXT, -- JSON recommendations
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول تقارير التحليلات
CREATE TABLE IF NOT EXISTS analytics_reports (
    report_id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT, -- JSON report content
    parameters TEXT, -- JSON report parameters
    generated_by TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- جدول لوحات التحكم
CREATE TABLE IF NOT EXISTS dashboards (
    dashboard_id TEXT PRIMARY KEY,
    dashboard_name TEXT NOT NULL,
    dashboard_type TEXT NOT NULL, -- 'executive', 'operational', 'analytical'
    components TEXT, -- JSON dashboard components
    refresh_interval INTEGER, -- minutes
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- فهارس للأداء
-- =============================================================================

-- فهارس للذكاء الاصطناعي المعرفي
CREATE INDEX IF NOT EXISTS idx_decision_scenarios_type ON decision_scenarios(decision_type);
CREATE INDEX IF NOT EXISTS idx_decision_scenarios_created ON decision_scenarios(created_at);
CREATE INDEX IF NOT EXISTS idx_decision_outcomes_scenario ON decision_outcomes(scenario_id);
CREATE INDEX IF NOT EXISTS idx_decision_rules_active ON decision_rules(is_active, priority);

-- فهارس للتنبؤات الذكية
CREATE INDEX IF NOT EXISTS idx_forecast_models_type ON forecast_models(model_type, target_variable);
CREATE INDEX IF NOT EXISTS idx_forecast_results_model ON forecast_results(model_id);
CREATE INDEX IF NOT EXISTS idx_forecast_results_generated ON forecast_results(generated_at);
CREATE INDEX IF NOT EXISTS idx_demand_patterns_type ON demand_patterns(pattern_type);

-- فهارس للتحليلات المتقدمة
CREATE INDEX IF NOT EXISTS idx_business_insights_type ON business_insights(insight_type, impact_level);
CREATE INDEX IF NOT EXISTS idx_business_insights_generated ON business_insights(generated_at);
CREATE INDEX IF NOT EXISTS idx_customer_segments_name ON customer_segments(segment_name);
CREATE INDEX IF NOT EXISTS idx_business_metrics_category ON business_metrics(category, calculation_period);
CREATE INDEX IF NOT EXISTS idx_predictive_insights_type ON predictive_insights(prediction_type);

-- فهارس للذكاء الاصطناعي
CREATE INDEX IF NOT EXISTS idx_ai_models_type ON ai_models(model_type, training_status);
CREATE INDEX IF NOT EXISTS idx_training_data_model ON training_data(model_id, used_in_training);
CREATE INDEX IF NOT EXISTS idx_ai_results_model ON ai_results(model_id, generated_at);

-- فهارس للتحليلات
CREATE INDEX IF NOT EXISTS idx_performance_analytics_type ON performance_analytics(analysis_type, generated_at);
CREATE INDEX IF NOT EXISTS idx_analytics_reports_type ON analytics_reports(report_type, generated_at);
CREATE INDEX IF NOT EXISTS idx_dashboards_type ON dashboards(dashboard_type, is_active);

-- =============================================================================
-- بيانات أولية للاختبار
-- =============================================================================

-- إدراج قواعد قرار أولية
INSERT OR IGNORE INTO decision_rules (rule_id, rule_name, condition, action, priority) VALUES
('RULE_001', 'إعادة طلب مخزون منخفض', 'inventory_low', 'generate_reorder_request', 3),
('RULE_002', 'خصم للعملاء المخلصين', 'loyal_customer_high_value', 'apply_loyalty_discount', 2),
('RULE_003', 'تنبيه انخفاض المبيعات', 'sales_drop_significant', 'alert_management', 4);

-- إدراج نماذج تنبؤ أولية
INSERT OR IGNORE INTO forecast_models (model_id, model_type, target_variable, features, training_data_period, accuracy_score) VALUES
('MODEL_SALES_001', 'linear', 'sales', '["date", "lag_1", "lag_7", "rolling_mean_7"]', 365, 0.75),
('MODEL_INVENTORY_001', 'rf', 'inventory_needs', '["current_stock", "sales_velocity", "seasonal_factor"]', 180, 0.82);

-- إدراج مقاييس أعمال أولية
INSERT OR IGNORE INTO business_metrics (metric_id, metric_name, category, current_value, target_value, trend, calculation_period) VALUES
('METRIC_REVENUE_DAILY', 'الإيرادات اليومية', 'financial', 0, 10000, 'stable', 'daily'),
('METRIC_CUSTOMER_RETENTION', 'معدل الاحتفاظ بالعملاء', 'customer', 0.85, 0.90, 'improving', 'monthly'),
('METRIC_ORDER_FULFILLMENT', 'معدل تنفيذ الطلبات', 'operational', 0.92, 0.95, 'stable', 'weekly');

-- =============================================================================
-- التحديثات المستقبلية
-- =============================================================================

-- ملاحظات للمطورين:
-- 1. يمكن إضافة جداول للبيانات التاريخية المضغوطة
-- 2. إضافة جداول للنماذج المدربة والمحفوظة
-- 3. جداول للتنبيهات والإشعارات التلقائية
-- 4. جداول للتكامل مع APIs خارجية للبيانات
-- 5. جداول للخصوصية وإدارة البيانات الحساسة