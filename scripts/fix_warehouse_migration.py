#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إصلاح Migration - إنشاء المستودع الافتراضي إذا لم يكن موجوداً
Fix Migration Script - Create default warehouse if missing
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager
from src.services.warehouse_service import WarehouseService
from src.models.warehouse import Warehouse


def fix_default_warehouse():
    """إنشاء المستودع الافتراضي إذا لم يكن موجوداً"""
    print("🔧 إصلاح Migration: إنشاء المستودع الافتراضي...")
    
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        warehouse_service = WarehouseService(db_manager)
        
        # التحقق من وجود المستودع الافتراضي
        default_warehouse = warehouse_service.get_default_warehouse()
        
        if default_warehouse:
            print(f"✅ المستودع الافتراضي موجود بالفعل: {default_warehouse.name} (ID: {default_warehouse.id})")
            return True
        
        # البحث عن المستودع بالرمز
        default_warehouse = warehouse_service.get_warehouse_by_code("WH-001")
        
        if default_warehouse:
            print(f"✅ المستودع WH-001 موجود لكن ليس افتراضياً، جعله افتراضياً...")
            default_warehouse.is_default = True
            if warehouse_service.update_warehouse(default_warehouse):
                print("✅ تم جعل المستودع افتراضياً")
                return True
            else:
                print("❌ فشل في جعل المستودع افتراضياً")
                return False
        
        # إنشاء المستودع الافتراضي
        print("⚠️  المستودع الافتراضي غير موجود، جاري إنشاؤه...")
        
        default_warehouse = Warehouse(
            code="WH-001",
            name="المستودع الرئيسي",
            name_en="Main Warehouse",
            is_active=True,
            is_default=True,
            created_by=1
        )
        
        warehouse_id = warehouse_service.create_warehouse(default_warehouse)
        
        if warehouse_id:
            print(f"✅ تم إنشاء المستودع الافتراضي بنجاح (ID: {warehouse_id})")
            
            # نقل المخزون الحالي إلى المستودع الافتراضي
            print("🔄 نقل المخزون الحالي إلى المستودع الافتراضي...")
            
            # التحقق من وجود مخزون منقول بالفعل
            check_query = "SELECT COUNT(*) as count FROM warehouse_inventory WHERE warehouse_id = ?"
            existing_count = db_manager.execute_query(check_query, (warehouse_id,))
            
            if existing_count and existing_count[0].get('count', 0) > 0:
                print(f"ℹ️  يوجد بالفعل {existing_count[0]['count']} سجل مخزون في المستودع الافتراضي")
            else:
                # جدول products لا يحتوي على reorder_point، نستخدم min_stock كبديل
                query = """
                    INSERT OR IGNORE INTO warehouse_inventory (warehouse_id, product_id, quantity, min_stock, max_stock, reorder_point, created_at)
                    SELECT 
                        ? as warehouse_id,
                        id as product_id,
                        COALESCE(current_stock, 0) as quantity,
                        COALESCE(min_stock, 0) as min_stock,
                        COALESCE(max_stock, 0) as max_stock,
                        COALESCE(min_stock, 0) as reorder_point,
                        CURRENT_TIMESTAMP
                    FROM products
                    WHERE COALESCE(current_stock, 0) > 0 OR COALESCE(min_stock, 0) > 0 OR COALESCE(max_stock, 0) > 0
                """
                
                db_manager.execute_query(query, (warehouse_id,))
                print("✅ تم نقل المخزون بنجاح")
            
            db_manager.close()
            return True
        else:
            print("❌ فشل في إنشاء المستودع الافتراضي")
            db_manager.close()
            return False
            
    except Exception as e:
        print(f"❌ خطأ في إصلاح Migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_default_warehouse()
    sys.exit(0 if success else 1)

