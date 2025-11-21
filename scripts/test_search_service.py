#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت اختبار خدمة البحث المتقدم
يختبر وظائف البحث والفلاتر والاقتراحات
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# إضافة مسار src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager
from src.services.advanced_search_service import AdvancedSearchService
from src.models.search import SearchEntity, FilterOperator, SearchFilter, SearchQuery


def test_search_service():
    """اختبار شامل لخدمة البحث المتقدم"""
    
    print("=" * 80)
    print("🔍 اختبار خدمة البحث المتقدم")
    print("=" * 80)
    
    try:
        # تهيئة قاعدة البيانات
        db_path = project_root / "data" / "inventory.db"
        db_manager = DatabaseManager(str(db_path))
        db_manager.initialize()
        search_service = AdvancedSearchService(db_manager)
        
        print("\n✓ تم تهيئة الخدمات بنجاح")
        
        # اختبار 1: البحث في المنتجات
        print("\n" + "-" * 80)
        print("📦 اختبار 1: البحث في المنتجات")
        print("-" * 80)
        
        query = SearchQuery(
            entity=SearchEntity.PRODUCTS,
            keyword="",
            limit=10,
            offset=0
        )
        
        result = search_service.search(query)
        print(f"عدد المنتجات المسترجعة: {len(result.records)}")
        print(f"إجمالي النتائج: {result.total_count}")
        print(f"وقت التنفيذ: {result.execution_time_ms}ms")
        
        if result.records:
            print("\nأول 3 منتجات:")
            for i, item in enumerate(result.records[:3], 1):
                print(f"{i}. {item.get('name', 'N/A')} - الباركود: {item.get('barcode', 'N/A')}")
        
        # اختبار 2: البحث بكلمة مفتاحية
        print("\n" + "-" * 80)
        print("🔎 اختبار 2: البحث بكلمة مفتاحية في المنتجات")
        print("-" * 80)
        
        query_with_keyword = SearchQuery(
            entity=SearchEntity.PRODUCTS,
            keyword="منتج",
            limit=5,
            offset=0
        )
        
        result = search_service.search(query_with_keyword)
        print(f"عدد المنتجات التي تحتوي على 'منتج': {result.total_count}")
        
        # اختبار 3: البحث مع فلتر
        print("\n" + "-" * 80)
        print("⚖️ اختبار 3: البحث في المنتجات (المخزون < 10)")
        print("-" * 80)
        
        low_stock_filter = SearchFilter(
            field="current_stock",
            operator=FilterOperator.LESS_THAN,
            value="10"
        )
        
        query_with_filter = SearchQuery(
            entity=SearchEntity.PRODUCTS,
            keyword="",
            filters=[low_stock_filter],
            limit=10,
            offset=0
        )
        
        result = search_service.search(query_with_filter)
        print(f"عدد المنتجات ذات المخزون المنخفض: {result.total_count}")
        
        if result.records:
            print("\nمنتجات بمخزون منخفض:")
            for item in result.records[:5]:
                print(f"- {item.get('name', 'N/A')}: {item.get('current_stock', 0)} وحدة")
        
        # اختبار 4: البحث في العملاء
        print("\n" + "-" * 80)
        print("👥 اختبار 4: البحث في العملاء")
        print("-" * 80)
        
        query = SearchQuery(
            entity=SearchEntity.CUSTOMERS,
            keyword="",
            limit=10,
            offset=0
        )
        
        result = search_service.search(query)
        print(f"عدد العملاء: {result.total_count}")
        
        if result.records:
            print("\nأول 3 عملاء:")
            for i, item in enumerate(result.records[:3], 1):
                print(f"{i}. {item.get('name', 'N/A')} - الهاتف: {item.get('phone', 'N/A')}")
        
        # اختبار 5: البحث مع فلتر رصيد العملاء
        print("\n" + "-" * 80)
        print("💰 اختبار 5: عملاء لديهم رصيد (رصيد > 0)")
        print("-" * 80)
        
        balance_filter = SearchFilter(
            field="current_balance",
            operator=FilterOperator.GREATER_THAN,
            value="0"
        )
        
        query_with_balance = SearchQuery(
            entity=SearchEntity.CUSTOMERS,
            keyword="",
            filters=[balance_filter],
            limit=10,
            offset=0
        )
        
        result = search_service.search(query_with_balance)
        print(f"عدد العملاء الذين لديهم رصيد: {result.total_count}")
        
        if result.records:
            print("\nعملاء لديهم رصيد:")
            for item in result.records[:5]:
                print(f"- {item.get('name', 'N/A')}: {item.get('current_balance', 0)} ريال")
        
        # اختبار 6: البحث في المبيعات
        print("\n" + "-" * 80)
        print("🛒 اختبار 6: البحث في المبيعات")
        print("-" * 80)
        
        query = SearchQuery(
            entity=SearchEntity.SALES,
            keyword="",
            limit=5,
            offset=0
        )
        
        result = search_service.search(query)
        print(f"عدد فواتير المبيعات: {result.total_count}")
        
        if result.records:
            print("\nآخر 3 فواتير:")
            for i, item in enumerate(result.records[:3], 1):
                print(f"{i}. فاتورة #{item.get('invoice_number', 'N/A')} - "
                      f"المبلغ: {item.get('final_amount', 0):.2f} ريال - "
                      f"التاريخ: {item.get('sale_date', 'N/A')}")
        
        # اختبار 7: البحث العام (في جميع الكيانات)
        print("\n" + "-" * 80)
        print("🌐 اختبار 7: البحث العام في جميع الكيانات")
        print("-" * 80)
        
        query = SearchQuery(
            entity=SearchEntity.ALL,
            keyword="test",
            limit=5,
            offset=0
        )
        
        result = search_service.search(query)
        print(f"إجمالي النتائج من جميع الكيانات: {result.total_count}")
        
        # اختبار 8: الفلاتر المحفوظة
        print("\n" + "-" * 80)
        print("💾 اختبار 8: الفلاتر المحفوظة")
        print("-" * 80)
        
        saved_filters = search_service.list_saved_filters()
        print(f"عدد الفلاتر المحفوظة: {len(saved_filters)}")
        
        if saved_filters:
            print("\nالفلاتر المتوفرة:")
            for i, sf in enumerate(saved_filters, 1):
                print(f"{i}. {sf.name} ({sf.entity}) - {sf.description or 'بدون وصف'}")
                if sf.is_default:
                    print(f"   [افتراضي]")
        
        # اختبار 9: اختبار فلتر محفوظ
        if saved_filters:
            print("\n" + "-" * 80)
            print("🔄 اختبار 9: تحميل واستخدام فلتر محفوظ")
            print("-" * 80)
            
            first_filter = saved_filters[0]
            print(f"تحميل الفلتر: {first_filter.name}")
            
            loaded_filter = search_service.load_filter(first_filter.id)
            if loaded_filter:
                # تحويل query_data من JSON إلى SearchQuery
                query_dict = json.loads(loaded_filter.query_data)
                query = SearchQuery.from_dict(query_dict)
                
                result = search_service.search(query)
                print(f"عدد النتائج باستخدام الفلتر المحفوظ: {result.total_count}")
        
        # اختبار 10: الحصول على الحقول المتاحة
        print("\n" + "-" * 80)
        print("📋 اختبار 10: الحقول المتاحة للبحث")
        print("-" * 80)
        
        for entity in [SearchEntity.PRODUCTS, SearchEntity.CUSTOMERS, SearchEntity.SALES]:
            fields = search_service.get_available_fields(entity)
            print(f"\n{entity.value}:")
            field_names = [f['name'] for f in fields]
            print(f"  الحقول: {', '.join(field_names)}")
        
        # ملخص النتائج
        print("\n" + "=" * 80)
        print("📊 ملخص الاختبارات")
        print("=" * 80)
        
        summary = {
            "status": "نجاح",
            "timestamp": datetime.now().isoformat(),
            "tests_completed": 10,
            "saved_filters_count": len(saved_filters),
            "entities_tested": [
                SearchEntity.PRODUCTS.value,
                SearchEntity.CUSTOMERS.value,
                SearchEntity.SALES.value,
                SearchEntity.ALL.value
            ]
        }
        
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        
        print("\n✅ جميع الاختبارات اكتملت بنجاح!")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ خطأ في الاختبار: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "فشل", "error": str(e)}


if __name__ == "__main__":
    test_search_service()
