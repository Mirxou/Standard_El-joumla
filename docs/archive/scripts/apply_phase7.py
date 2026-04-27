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
    with open('migrations/phase7_cognitive_ai_schema.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # تنفيذ السكريبت
    cursor.executescript(sql_script)
    db_manager.connection.commit()

    print("✅ تم تطبيق هجرة المرحلة 7 بنجاح")

    # فحص الجداول المُنشأة
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ai_%'")
    ai_tables = cursor.fetchall()
    print(f"جداول الذكاء الاصطناعي: {[row[0] for row in ai_tables]}")

except Exception as e:
    print(f"❌ خطأ في تطبيق الهجرة: {e}")
    db_manager.connection.rollback()

finally:
    db_manager.connection.close()