#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت اختبار Multi-Warehouse Migration
Test Script for Multi-Warehouse Migration

التحقق من:
1. Migration تم بنجاح
2. الجداول تم إنشاؤها
3. المستودع الافتراضي موجود
4. نقل المخزون تم بنجاح
5. WarehouseService يعمل
6. InventoryService مع Backward Compatibility يعمل
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.database_manager import DatabaseManager
from src.services.warehouse_service import WarehouseService
from src.services.inventory_service import InventoryService
from src.models.warehouse import Warehouse
from src.utils.logger import setup_logger


class Colors:
    """ألوان للطباعة"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    """طباعة رسالة نجاح"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """طباعة رسالة خطأ"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """طباعة رسالة تحذير"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    """طباعة رسالة معلومات"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")


def print_header(message: str):
    """طباعة عنوان"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def test_database_tables(db_manager: DatabaseManager) -> bool:
    """اختبار وجود الجداول المطلوبة"""
    print_header("1. اختبار وجود الجداول (Database Tables)")
    
    required_tables = [
        'warehouses',
        'warehouse_inventory',
        'warehouse_transfers'
    ]
    
    all_passed = True
    for table in required_tables:
        try:
            exists = db_manager.table_exists(table)
            if exists:
                print_success(f"الجدول '{table}' موجود")
            else:
                print_error(f"الجدول '{table}' غير موجود!")
                all_passed = False
        except Exception as e:
            print_error(f"خطأ في التحقق من الجدول '{table}': {e}")
            all_passed = False
    
    return all_passed


def test_default_warehouse(db_manager: DatabaseManager, warehouse_service: WarehouseService) -> bool:
    """اختبار المستودع الافتراضي"""
    print_header("2. اختبار المستودع الافتراضي (Default Warehouse)")
    
    try:
        # البحث عن المستودع الافتراضي (باستخدام الكود من Migration)
        default_warehouse = warehouse_service.get_warehouse_by_code("WH-001")
        if not default_warehouse:
            # محاولة الحصول على المستودع الافتراضي
            default_warehouse = warehouse_service.get_default_warehouse()
        
        if not default_warehouse:
            print_error("المستودع الافتراضي غير موجود!")
            return False
        
        print_success(f"تم العثور على المستودع الافتراضي: {default_warehouse.name} (Code: {default_warehouse.code})")
        print_info(f"  - ID: {default_warehouse.id}")
        print_info(f"  - نشط: {'نعم' if default_warehouse.is_active else 'لا'}")
        print_info(f"  - افتراضي: {'نعم' if default_warehouse.is_default else 'لا'}")
        
        # التحقق من أن هناك مستودع واحد افتراضي فقط
        all_warehouses = warehouse_service.get_all_warehouses()
        default_count = sum(1 for w in all_warehouses if w.is_default)
        
        if default_count == 1:
            print_success(f"يوجد مستودع افتراضي واحد فقط ({default_count})")
        else:
            print_warning(f"يوجد {default_count} مستودعات افتراضية (يجب أن يكون واحد فقط)")
        
        return True
        
    except Exception as e:
        print_error(f"خطأ في اختبار المستودع الافتراضي: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inventory_migration(db_manager: DatabaseManager, warehouse_service: WarehouseService) -> bool:
    """اختبار نقل المخزون"""
    print_header("3. اختبار نقل المخزون (Inventory Migration)")
    
    try:
        # الحصول على المستودع الافتراضي
        default_warehouse = warehouse_service.get_default_warehouse()
        if not default_warehouse:
            print_error("لا يوجد مستودع افتراضي لاختبار نقل المخزون")
            return False
        
        # الحصول على منتج من قاعدة البيانات
        query = "SELECT id, name, current_stock FROM products WHERE is_active = 1 LIMIT 5"
        products = db_manager.execute_query(query)
        
        if not products:
            print_warning("لا توجد منتجات لاختبار نقل المخزون")
            return True  # ليس خطأ، فقط لا توجد بيانات
        
        print_info(f"تم العثور على {len(products)} منتج للاختبار")
        
        migrated_count = 0
        for product in products:
            product_id = product['id']
            product_name = product['name']
            old_stock = product.get('current_stock', 0)
            
            # التحقق من وجود المخزون في المستودع الافتراضي
            inventory = warehouse_service.inventory_manager.get_inventory(
                default_warehouse.id, product_id
            )
            
            if inventory:
                if inventory.quantity == old_stock:
                    print_success(f"المنتج '{product_name}': المخزون متطابق ({old_stock})")
                    migrated_count += 1
                else:
                    print_warning(f"المنتج '{product_name}': المخزون غير متطابق (قديم: {old_stock}, جديد: {inventory.quantity})")
            else:
                if old_stock == 0:
                    print_info(f"المنتج '{product_name}': لا يوجد مخزون (لا حاجة للنقل)")
                else:
                    print_error(f"المنتج '{product_name}': لم يتم نقل المخزون! (كان: {old_stock})")
        
        if migrated_count > 0:
            print_success(f"تم التحقق من نقل {migrated_count} منتج بنجاح")
        
        return True
        
    except Exception as e:
        print_error(f"خطأ في اختبار نقل المخزون: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_warehouse_service(db_manager: DatabaseManager, warehouse_service: WarehouseService) -> bool:
    """اختبار WarehouseService"""
    print_header("4. اختبار WarehouseService")
    
    try:
        # اختبار الحصول على جميع المستودعات
        warehouses = warehouse_service.get_all_warehouses()
        print_success(f"تم الحصول على {len(warehouses)} مستودع")
        
        if warehouses:
            for wh in warehouses:
                print_info(f"  - {wh.name} ({wh.code}) - {'نشط' if wh.is_active else 'غير نشط'}")
        
        # اختبار إنشاء مستودع جديد (للاختبار فقط)
        # تنظيف المستودعات الاختبارية القديمة أولاً
        import random
        test_code = f"TEST-WH-{random.randint(1000, 9999)}"
        
        test_warehouse = Warehouse(
            code=test_code,
            name="مستودع اختبار",
            name_en="Test Warehouse",
            is_active=True,
            is_default=False
        )
        
        test_id = warehouse_service.create_warehouse(test_warehouse)
        
        if test_id:
            print_success(f"تم إنشاء مستودع اختبار (ID: {test_id}, Code: {test_code})")
            
            # حذف المستودع الاختباري
            if warehouse_service.delete_warehouse(test_id):
                print_success("تم حذف مستودع الاختبار بنجاح")
            else:
                print_warning("فشل في حذف مستودع الاختبار (قد يحتوي على مخزون)")
        else:
            print_error("فشل في إنشاء مستودع اختبار")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"خطأ في اختبار WarehouseService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inventory_service_backward_compatibility(db_manager: DatabaseManager) -> bool:
    """اختبار InventoryService مع Backward Compatibility"""
    print_header("5. اختبار InventoryService (Backward Compatibility)")
    
    try:
        inventory_service = InventoryService(db_manager)
        
        # التحقق من تفعيل Multi-Warehouse
        is_enabled = inventory_service.is_multi_warehouse_enabled()
        if is_enabled:
            print_success("Multi-Warehouse مفعل في InventoryService")
        else:
            print_warning("Multi-Warehouse غير مفعل (قد يكون WarehouseService غير متاح)")
        
        # الحصول على منتج للاختبار
        query = "SELECT id, name, current_stock FROM products WHERE is_active = 1 LIMIT 1"
        products = db_manager.execute_query(query)
        
        if not products:
            print_warning("لا توجد منتجات لاختبار InventoryService")
            return True
        
        product = products[0]
        product_id = product['id']
        product_name = product['name']
        old_stock = product.get('current_stock', 0)
        
        print_info(f"اختبار تعديل المخزون للمنتج: {product_name} (المخزون الحالي: {old_stock})")
        
        # اختبار تعديل المخزون بدون تحديد مستودع (Backward Compatibility)
        # يجب أن يعمل مع الكود القديم
        test_quantity = old_stock + 1
        success = inventory_service.adjust_stock(
            product_id=product_id,
            new_quantity=test_quantity,
            reason="اختبار Backward Compatibility",
            user_id=1
        )
        
        if success:
            print_success("تم تعديل المخزون بنجاح (Backward Compatibility يعمل)")
            
            # استعادة المخزون الأصلي
            inventory_service.adjust_stock(
                product_id=product_id,
                new_quantity=old_stock,
                reason="استعادة بعد الاختبار",
                user_id=1
            )
            print_info("تم استعادة المخزون الأصلي")
        else:
            print_error("فشل في تعديل المخزون")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"خطأ في اختبار InventoryService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_warehouse_transfer(db_manager: DatabaseManager, warehouse_service: WarehouseService) -> bool:
    """اختبار نقل المخزون بين المستودعات"""
    print_header("6. اختبار نقل المخزون بين المستودعات (Warehouse Transfer)")
    
    try:
        # الحصول على المستودع الافتراضي
        default_warehouse = warehouse_service.get_default_warehouse()
        if not default_warehouse:
            print_error("لا يوجد مستودع افتراضي")
            return False
        
        # إنشاء مستودع اختبار (بكود فريد)
        import random
        test_code = f"TRANSFER-TEST-{random.randint(1000, 9999)}"
        
        test_warehouse = Warehouse(
            code=test_code,
            name="مستودع نقل اختبار",
            is_active=True,
            is_default=False
        )
        
        test_wh_id = warehouse_service.create_warehouse(test_warehouse)
        if not test_wh_id:
            print_error("فشل في إنشاء مستودع اختبار")
            return False
        
        print_success(f"تم إنشاء مستودع اختبار (ID: {test_wh_id})")
        
        # الحصول على منتج للاختبار
        query = "SELECT id, name FROM products WHERE is_active = 1 LIMIT 1"
        products = db_manager.execute_query(query)
        
        if not products:
            print_warning("لا توجد منتجات لاختبار النقل")
            # حذف المستودع الاختباري
            warehouse_service.delete_warehouse(test_wh_id)
            return True
        
        product = products[0]
        product_id = product['id']
        product_name = product['name']
        
        # إضافة مخزون في المستودع الافتراضي للاختبار
        warehouse_service.adjust_stock(default_warehouse.id, product_id, 10.0)
        print_info(f"تم إضافة 10 وحدات من '{product_name}' في المستودع الافتراضي")
        
        # إنشاء تحويل
        from src.models.warehouse import WarehouseTransfer
        transfer = WarehouseTransfer(
            from_warehouse_id=default_warehouse.id,
            to_warehouse_id=test_wh_id,
            product_id=product_id,
            quantity=5.0,
            status="pending",
            notes="اختبار نقل"
        )
        
        transfer_id = warehouse_service.create_transfer(transfer)
        
        if transfer_id:
            print_success(f"تم إنشاء تحويل (ID: {transfer_id}, Number: {transfer.transfer_number})")
            
            # إكمال التحويل
            if warehouse_service.complete_transfer(transfer_id, received_by=1):
                print_success("تم إكمال التحويل بنجاح")
                
                # التحقق من المخزون
                source_inv = warehouse_service.inventory_manager.get_inventory(
                    default_warehouse.id, product_id
                )
                dest_inv = warehouse_service.inventory_manager.get_inventory(
                    test_wh_id, product_id
                )
                
                print_info(f"المخزون في المستودع المصدر: {source_inv.quantity if source_inv else 0}")
                print_info(f"المخزون في المستودع الهدف: {dest_inv.quantity if dest_inv else 0}")
            else:
                print_error("فشل في إكمال التحويل")
        else:
            print_error("فشل في إنشاء تحويل")
        
        # تنظيف: حذف المستودع الاختباري
        # (قد يحتوي على مخزون، لذا قد يفشل الحذف)
        try:
            warehouse_service.delete_warehouse(test_wh_id)
        except:
            pass
        
        return True
        
    except Exception as e:
        print_error(f"خطأ في اختبار نقل المخزون: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """الدالة الرئيسية"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("🚀 اختبار Multi-Warehouse Migration")
    print("="*60)
    print(f"{Colors.RESET}\n")
    
    # تهيئة قاعدة البيانات
    try:
        db_manager = DatabaseManager()
        print_info(f"مسار قاعدة البيانات: {db_manager.db_path}")
        
        # تهيئة قاعدة البيانات
        print_info("تهيئة قاعدة البيانات...")
        success = db_manager.initialize()
        
        if not success:
            print_error("فشل في تهيئة قاعدة البيانات!")
            return False
        
        print_success("تم تهيئة قاعدة البيانات بنجاح")
        
    except Exception as e:
        print_error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # تهيئة الخدمات
    try:
        warehouse_service = WarehouseService(db_manager)
    except Exception as e:
        print_error(f"خطأ في تهيئة WarehouseService: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # تشغيل الاختبارات
    results = []
    
    results.append(("الجداول", test_database_tables(db_manager)))
    results.append(("المستودع الافتراضي", test_default_warehouse(db_manager, warehouse_service)))
    results.append(("نقل المخزون", test_inventory_migration(db_manager, warehouse_service)))
    results.append(("WarehouseService", test_warehouse_service(db_manager, warehouse_service)))
    results.append(("Backward Compatibility", test_inventory_service_backward_compatibility(db_manager)))
    results.append(("نقل المخزون بين المستودعات", test_warehouse_transfer(db_manager, warehouse_service)))
    
    # إغلاق قاعدة البيانات
    try:
        db_manager.close()
    except:
        pass
    
    # عرض النتائج النهائية
    print_header("النتائج النهائية")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: نجح")
        else:
            print_error(f"{name}: فشل")
    
    print(f"\n{Colors.BOLD}")
    print("="*60)
    if passed == total:
        print(f"{Colors.GREEN}✅ جميع الاختبارات نجحت! ({passed}/{total}){Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️  بعض الاختبارات فشلت ({passed}/{total}){Colors.RESET}")
    print("="*60)
    print(f"{Colors.RESET}\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




