#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Services Test Script
اختبار شامل لجميع الخدمات
"""

import sys
from pathlib import Path

# إضافة مسار المشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """اختبار استيراد الوحدات"""
    print("1️⃣ اختبار استيراد الوحدات Python...")
    
    tests_passed = 0
    tests_failed = 0
    
    modules_to_test = [
        ("src.core.database_manager", "DatabaseManager"),
        ("src.services.compliance_service", "ComplianceService"),
        ("src.services.sso_service", "SSOService"),
        ("src.core.security_monitor", "SecurityMonitor"),
        ("src.core.intrusion_detection", "IntrusionDetectionSystem"),
        ("src.services.security_reports_service", "SecurityReportsService"),
        ("src.services.webhook_service", "WebhookService"),
        ("src.services.cloud_sync_service", "CloudSyncService"),
    ]
    
    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"   ✅ {class_name}")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ {class_name}: {e}")
            tests_failed += 1
    
    return tests_passed, tests_failed


def test_database_initialization():
    """اختبار تهيئة قاعدة البيانات"""
    print("\n2️⃣ اختبار تهيئة قاعدة البيانات...")
    
    try:
        from src.core.database_manager import DatabaseManager
        
        db = DatabaseManager(':memory:')
        if db.initialize():
            print("   ✅ Database initialization")
            return 1, 0
        else:
            print("   ❌ Database initialization failed")
            return 0, 1
    except Exception as e:
        print(f"   ❌ Database initialization error: {e}")
        return 0, 1


def test_services_initialization():
    """اختبار تهيئة الخدمات"""
    print("\n3️⃣ اختبار تهيئة الخدمات...")
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        from src.core.database_manager import DatabaseManager
        
        db = DatabaseManager(':memory:')
        db.initialize()
        
        # Test ComplianceService
        try:
            from src.services.compliance_service import ComplianceService
            compliance = ComplianceService(db)
            print("   ✅ ComplianceService initialized")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ ComplianceService: {e}")
            tests_failed += 1
        
        # Test SSOService
        try:
            from src.services.sso_service import SSOService
            sso = SSOService(db)
            print("   ✅ SSOService initialized")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ SSOService: {e}")
            tests_failed += 1
        
        # Test SecurityMonitor
        try:
            from src.core.security_monitor import SecurityMonitor
            from src.utils.logger import setup_logger
            logger = setup_logger(__name__)
            monitor = SecurityMonitor(db, logger)
            print("   ✅ SecurityMonitor initialized")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ SecurityMonitor: {e}")
            tests_failed += 1
        
        # Test IntrusionDetectionSystem
        try:
            from src.core.intrusion_detection import IntrusionDetectionSystem
            from src.utils.logger import setup_logger
            logger = setup_logger(__name__)
            ids = IntrusionDetectionSystem(db, logger)
            print("   ✅ IntrusionDetectionSystem initialized")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ IntrusionDetectionSystem: {e}")
            tests_failed += 1
            
    except Exception as e:
        print(f"   ❌ Services initialization error: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def main():
    """الدالة الرئيسية"""
    print("🧪 اختبار الخدمات...")
    print("=" * 50)
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Imports
    passed, failed = test_imports()
    total_passed += passed
    total_failed += failed
    
    # Test 2: Database
    passed, failed = test_database_initialization()
    total_passed += passed
    total_failed += failed
    
    # Test 3: Services
    passed, failed = test_services_initialization()
    total_passed += passed
    total_failed += failed
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ملخص اختبارات الخدمات:")
    print(f"   ✅ نجحت: {total_passed}")
    print(f"   ❌ فشلت: {total_failed}")
    print("=" * 50)
    
    if total_failed == 0:
        print("\n🎉 جميع اختبارات الخدمات نجحت!")
        return 0
    else:
        print("\n⚠️ بعض الاختبارات فشلت.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

