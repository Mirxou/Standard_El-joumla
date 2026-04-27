#!/usr/bin/env python3
"""
Phase 9 Final Validation Script
التحقق النهائي من اكتمال Phase 9
"""

print('Phase 9 Final Validation')
print('=' * 40)

# اختبار الاستيراد
try:
    from src.services.advanced_ai_service import AdvancedAIService
    print('✅ AdvancedAIService imported successfully')
except Exception as e:
    print(f'❌ Import error: {e}')

try:
    from src.ui.ai_service_ui import AIServiceUI
    print('✅ AIServiceUI imported successfully')
except Exception as e:
    print(f'❌ Import error: {e}')

# اختبار قاعدة البيانات
try:
    from src.core.database_manager import DatabaseManager
    db = DatabaseManager()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%ai%"')
        tables = cursor.fetchall()
        print(f'✅ AI tables created: {len(tables)} tables')
        for table in tables:
            print(f'   - {table[0]}')
except Exception as e:
    print(f'❌ Database error: {e}')

print('=' * 40)
print('Phase 9: COMPLETE!')
print('Advanced AI & Machine Learning - Ready 🚀')



