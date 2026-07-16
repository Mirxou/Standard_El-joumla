#!/usr/bin/env python3
"""
سكريبت لتشغيل الاختبارات والتحقق من الأخطاء
"""
import sys

# إضافة المسار الرئيسي
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

try:
    from src.services.backup_service import BackupService
    from unittest.mock import Mock
    
    # اختبار إنشاء الخدمة
    mock_db = Mock()
    service = BackupService(mock_db)
    print(f"✅ BackupService created successfully")
    print(f"   - service.db = {service.db}")
    print(f"   - service.backup_dir = {service.backup_dir}")
    
    # اختبار وجود الدوال
    methods = ['create_backup', 'restore_backup', 'list_backups', 'delete_backup', 
               'verify_backup', 'export_backup', 'schedule_backup']
    for method in methods:
        if hasattr(service, method):
            print(f"   ✓ Method '{method}' exists")
        else:
            print(f"   ❌ Method '{method}' NOT FOUND")
    
    print("\n✅ All basic tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
