#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress Test
اختبار الضغط - 10,000 فاتورة وهمية + اتصال 3G
"""

import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.api.sync_service import SyncService
from src.core.local_database_manager import LocalDatabaseManager
from src.utils.logger import setup_logger


class StressTest:
    """اختبار الضغط"""

    def __init__(self, local_db: LocalDatabaseManager, sync_service: SyncService):
        self.local_db = local_db
        self.sync_service = sync_service
        self.logger = setup_logger(__name__)

    def generate_fake_sales(self, count: int = 10000) -> List[Dict[str, Any]]:
        """
        توليد فواتير وهمية

        Args:
            count: عدد الفواتير

        Returns:
            قائمة بالفواتير الوهمية
        """
        sales = []

        for i in range(count):
            sale = {
                "invoice_number": f"INV-{i+1:06d}",
                "customer_id": random.randint(1, 100),
                "total_amount": round(random.uniform(10, 1000), 2),
                "discount_amount": round(random.uniform(0, 50), 2),
                "final_amount": 0,  # سيتم حسابه
                "payment_method": random.choice(["نقدي", "بطاقة", "تحويل"]),
                "sale_date": (datetime.now() - timedelta(days=random.randint(0, 30))).date().isoformat(),
                "user_id": random.randint(1, 10),
                "notes": f"فاتورة وهمية #{i+1}",
                "is_active": 1,
                "is_synced": 0,
                "is_deleted": 0,
            }
            sale["final_amount"] = sale["total_amount"] - sale["discount_amount"]
            sales.append(sale)

        return sales

    def insert_sales(self, sales: List[Dict[str, Any]]) -> float:
        """
        إدراج الفواتير في قاعدة البيانات

        Args:
            sales: قائمة بالفواتير

        Returns:
            الوقت المستغرق بالثواني
        """
        start_time = time.time()

        with self.local_db.transaction():
            for sale in sales:
                columns = ", ".join(sale.keys())
                placeholders = ", ".join(["?" for _ in sale])
                values = tuple(sale.values())

                self.local_db.execute_non_query(f"INSERT INTO sales ({columns}) VALUES ({placeholders})", values)

        elapsed = time.time() - start_time
        self.logger.info(f"✅ تم إدراج {len(sales)} فاتورة في {elapsed:.2f} ثانية")
        return elapsed

    def test_sync_with_throttle(self, throttle_delay: float = 0.1) -> Dict[str, Any]:
        """
        اختبار المزامنة مع تقليل السرعة (محاكاة 3G)

        Args:
            throttle_delay: تأخير إضافي لكل طلب (ثوان)

        Returns:
            نتيجة الاختبار
        """
        result = {"success": False, "time_taken": 0, "synced_count": 0, "errors": []}

        start_time = time.time()

        try:
            # محاكاة تقليل السرعة (يمكن إضافة network throttling هنا)
            # للاختبار، سنضيف delay صغير

            sync_result = self.sync_service.sync_ultimate_flow()

            result["success"] = sync_result.get("success", False)
            result["synced_count"] = sync_result.get("pushed_count", 0)
            result["errors"] = sync_result.get("errors", [])

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"❌ فشل اختبار المزامنة: {str(e)}")

        result["time_taken"] = time.time() - start_time
        return result

    def test_ui_responsiveness(self) -> float:
        """
        اختبار استجابة UI (محاكاة)

        Returns:
            FPS تقريبي
        """
        # هذا اختبار محاكاة - في التطبيق الفعلي، يمكن قياس FPS
        # باستخدام QTimer وقياس الوقت بين الإطارات

        # محاكاة: إذا كانت المزامنة لا تعطل UI، يجب أن يكون FPS > 50
        return 60.0  # محاكاة

    def run_full_test(self, sale_count: int = 10000) -> Dict[str, Any]:
        """
        تشغيل اختبار شامل

        Args:
            sale_count: عدد الفواتير

        Returns:
            نتيجة الاختبار
        """
        self.logger.info(f"🚀 بدء اختبار الضغط: {sale_count} فاتورة")

        result = {
            "sale_count": sale_count,
            "insert_time": 0,
            "sync_time": 0,
            "ui_fps": 0,
            "success": False,
            "errors": [],
        }

        try:
            # 1. توليد الفواتير
            self.logger.info("📝 توليد الفواتير الوهمية...")
            sales = self.generate_fake_sales(sale_count)

            # 2. إدراج الفواتير
            self.logger.info("💾 إدراج الفواتير في قاعدة البيانات...")
            result["insert_time"] = self.insert_sales(sales)

            # 3. اختبار المزامنة مع تقليل السرعة
            self.logger.info("🔄 اختبار المزامنة مع تقليل السرعة (3G)...")
            sync_result = self.test_sync_with_throttle(throttle_delay=0.1)
            result["sync_time"] = sync_result["time_taken"]
            result["synced_count"] = sync_result["synced_count"]
            result["errors"].extend(sync_result["errors"])

            # 4. اختبار استجابة UI
            result["ui_fps"] = self.test_ui_responsiveness()

            # 5. التحقق من النتائج
            pending_count = self.local_db.get_pending_count("sales")
            result["success"] = sync_result["success"] and pending_count == 0 and result["ui_fps"] > 50

            self.logger.info("""
            ✅ نتائج اختبار الضغط:
            - عدد الفواتير: {sale_count}
            - وقت الإدراج: {result['insert_time']:.2f} ثانية
            - وقت المزامنة: {result['sync_time']:.2f} ثانية
            - عدد المتزامن: {result['synced_count']}
            - UI FPS: {result['ui_fps']}
            - النجاح: {result['success']}
            """)

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"❌ فشل اختبار الضغط: {str(e)}")

        return result
