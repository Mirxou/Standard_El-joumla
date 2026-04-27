#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Services Test Script
اختبار شامل لجميع الخدمات
"""

import sys
import pytest
from pathlib import Path

project_root = Path(__file__).parent.parent
import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
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
    
    assert tests_failed == 0, f"Failed {tests_failed} imports"



def test_database_initialization():
    """اختبار تهيئة قاعدة البيانات"""
    print("\n2️⃣ اختبار تهيئة قاعدة البيانات...")
    
    try:
        from src.core.database_manager import DatabaseManager
        
        db = DatabaseManager(':memory:')
    except Exception as e:
        pytest.fail(f"Database initialization error: {e}")



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
    
    assert tests_failed == 0, f"Failed {tests_failed} service initializations"



if __name__ == "__main__":
    sys.exit(0)




