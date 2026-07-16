"""
Migration for Phase 9: Advanced AI & Machine Learning Integration
إضافة جداول قاعدة البيانات للذكاء الاصطناعي المتقدم
"""

import sqlite3
import os
from pathlib import Path

# مسار المشروع دائماً من موقع الملف — لا يعتمد على cwd
_PROJECT_ROOT = Path(__file__).parent.parent

def run_migration():
    """تشغيل migration لـ Phase 9"""
    db_path = str(_PROJECT_ROOT / "data" / "standard_eljoumla.db")

    # إنشاء مجلد data إذا لم يكن موجوداً
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            print("بدء Migration Phase 9...")

            # جدول تجارب التعلم الآلي التلقائي
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    target_column TEXT NOT NULL,
                    features TEXT NOT NULL,  -- JSON array
                    algorithms TEXT,  -- JSON array of algorithms to try
                    status TEXT DEFAULT 'pending',  -- pending, running, completed, failed
                    best_model TEXT,  -- best model class name
                    best_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    max_time INTEGER DEFAULT 30,  -- max time in minutes
                    metadata TEXT  -- JSON additional metadata
                )
            ''')

            # جدول تحليلات الصور
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_analysis (
                    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    analysis_type TEXT DEFAULT 'general',
                    analysis_results TEXT NOT NULL,  -- JSON results
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_used TEXT,  -- AI model used for analysis
                    confidence REAL,
                    processing_time REAL  -- in seconds
                )
            ''')

            # جدول المحادثات مع الذكاء الاصطناعي
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,  -- 'user' or 'ai'
                    message_content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,  -- optional user identifier
                    context TEXT,  -- JSON context information
                    response_metadata TEXT  -- JSON metadata about the response
                )
            ''')

            # جدول الرؤى الذكية
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_insights (
                    insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    impact TEXT DEFAULT 'medium',  -- low, medium, high
                    related_data TEXT,  -- JSON related data
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_used TEXT,  -- AI model that generated the insight
                    category TEXT,  -- sales, inventory, customers, financial, etc.
                    expires_at TIMESTAMP,  -- optional expiration date
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # جدول نماذج الذكاء الاصطناعي المدربة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trained_ai_models (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL,  -- classification, regression, clustering, nlp, vision
                    algorithm TEXT NOT NULL,
                    purpose TEXT,
                    dataset_info TEXT,  -- JSON info about training dataset
                    performance_metrics TEXT,  -- JSON performance metrics
                    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    model_path TEXT,  -- path to saved model file
                    version TEXT DEFAULT '1.0',
                    status TEXT DEFAULT 'active',  -- active, deprecated, archived
                    metadata TEXT  -- JSON additional metadata
                )
            ''')

            # جدول بيانات التدريب
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_datasets (
                    dataset_id TEXT PRIMARY KEY,
                    dataset_name TEXT NOT NULL,
                    data_type TEXT NOT NULL,  -- sales, customer, product, operational, text, image
                    data_source TEXT,  -- file path, database table, API endpoint
                    record_count INTEGER,
                    feature_count INTEGER,
                    quality_score REAL DEFAULT 0.5,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP,
                    metadata TEXT,  -- JSON additional metadata
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # جدول نتائج الذكاء الاصطناعي
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    input_data TEXT,  -- JSON input data
                    output_data TEXT,  -- JSON output data
                    confidence_score REAL,
                    processing_time REAL,  -- in seconds
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    session_id TEXT,
                    feedback_score REAL,  -- user feedback on result quality
                    feedback_comment TEXT,
                    metadata TEXT  -- JSON additional metadata
                )
            ''')

            # جدول سيناريوهات التنبؤ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictive_scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    scenario_name TEXT NOT NULL,
                    scenario_type TEXT NOT NULL,  -- sales_forecast, inventory_demand, customer_behavior
                    model_id TEXT,  -- AI model used
                    parameters TEXT,  -- JSON parameters for the scenario
                    time_horizon TEXT,  -- 1day, 1week, 1month, 1year
                    confidence_interval REAL DEFAULT 0.95,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_run TIMESTAMP,
                    results TEXT,  -- JSON results of last run
                    status TEXT DEFAULT 'active',
                    metadata TEXT  -- JSON additional metadata
                )
            ''')

            # جدول تفسيرات النماذج
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_explanations (
                    explanation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    result_id INTEGER,  -- reference to ai_results
                    explanation_type TEXT NOT NULL,  -- feature_importance, partial_dependence, shap_values
                    explanation_data TEXT NOT NULL,  -- JSON explanation data
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    method_used TEXT,  -- SHAP, LIME, etc.
                    metadata TEXT  -- JSON additional metadata
                )
            ''')

            # جدول مراقبة النماذج
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_monitoring (
                    monitoring_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    threshold_value REAL,
                    status TEXT,  -- normal, warning, critical
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    alert_sent BOOLEAN DEFAULT 0,
                    metadata TEXT  -- JSON additional metadata
                )
            ''')

            # إضافة فهارس للأداء
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_experiments_status ON ml_experiments(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ml_experiments_created ON ml_experiments(created_at)')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_conversations_conversation ON ai_conversations(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_conversations_created ON ai_conversations(created_at)')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_insights_type ON ai_insights(insight_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_insights_generated ON ai_insights(generated_at)')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trained_models_type ON trained_ai_models(model_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trained_models_status ON trained_ai_models(status)')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_results_model ON ai_results(model_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_results_generated ON ai_results(generated_at)')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictive_scenarios_type ON predictive_scenarios(scenario_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictive_scenarios_status ON predictive_scenarios(status)')

            conn.commit()
            print("✅ تم إنشاء جداول Phase 9 بنجاح")

            # التحقق من الجداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ml_%' OR name LIKE 'ai_%' OR name LIKE 'trained_%' OR name LIKE 'training_%' OR name LIKE 'predictive_%' OR name LIKE 'model_%' OR name LIKE 'image_%'")
            tables = cursor.fetchall()
            print(f"الجداول المُنشأة: {[table[0] for table in tables]}")

    except Exception as e:
        print(f"❌ فشل في Migration Phase 9: {e}")
        raise

# ملاحظة: تم حذف _insert_sample_data — البيانات التجريبية لا تنتمي لملفات migration الإنتاجية.
# استخدم scripts/generate_dummy_data.py إذا كنت بحاجة لبيانات اختبار.

if __name__ == "__main__":
    run_migration()