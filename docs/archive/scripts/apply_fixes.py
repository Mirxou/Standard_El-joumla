import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager

# Get database path
db_path = project_root / "data" / "logical_release.db"

db_manager = DatabaseManager(str(db_path))
db_manager.initialize()
cursor = db_manager.connection.cursor()

try:
    # فحص الأعمدة الموجودة
    cursor.execute('PRAGMA table_info(ai_models)')
    existing_columns = [col[1] for col in cursor.fetchall()]

    # الأعمدة التي نريد إضافتها
    columns_to_add = {
        'feature_importance': 'TEXT',
        'confusion_matrix': 'TEXT',
        'cross_validation_scores': 'TEXT',
        'hyperparameters': 'TEXT',
        'feature_names': 'TEXT'
    }

    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE ai_models ADD COLUMN {col_name} {col_type}")
            print(f"✅ تم إضافة العمود: {col_name}")

    # إضافة بيانات التدريب إذا لم تكن موجودة
    cursor.execute("SELECT COUNT(*) FROM training_data")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO training_data (data_id, data_type, data_content, labels, quality_score, source)
            VALUES
            ('TRAIN_001', 'customer_classification', '[10, 150.0, 1500.0, 5]', '1', 0.9, 'sample_data'),
            ('TRAIN_002', 'customer_classification', '[25, 300.0, 7500.0, 15]', '1', 0.95, 'sample_data'),
            ('TRAIN_003', 'customer_classification', '[3, 80.0, 240.0, 120]', '0', 0.8, 'sample_data'),
            ('TRAIN_004', 'customer_classification', '[1, 50.0, 50.0, 200]', '0', 0.7, 'sample_data'),
            ('TRAIN_005', 'customer_classification', '[50, 500.0, 25000.0, 2]', '1', 0.98, 'sample_data')
        """)
        print("✅ تم إدراج بيانات التدريب التجريبية")

    db_manager.connection.commit()
    print("✅ تم تطبيق جميع الإصلاحات")

except Exception as e:
    print(f"❌ خطأ: {e}")
    db_manager.connection.rollback()

finally:
    db_manager.connection.close()