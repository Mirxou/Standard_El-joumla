#!/usr/bin/env python3
"""
Phase 6: Multi-Warehouse Management & Logistics Integration
Database Integration Test
"""

import logging
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
import sys  # noqa: F811
from pathlib import Path

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
import sys  # noqa: F811
from pathlib import Path

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_database_integration():
    """Test database integration for Phase 6 services"""
    try:
        logger.info("🚀 بدء اختبار تكامل قاعدة البيانات للمرحلة 6")

        # Initialize managers
        config_manager = ConfigManager()
        db_path = config_manager.get("database.path", "data/erp_system.db")
        db_manager = DatabaseManager(db_path=db_path)
        db_manager.initialize()

        # Test basic database operations without complex service dependencies
        logger.info("🧪 اختبار العمليات الأساسية لقاعدة البيانات...")

        # Test warehouse table exists and can be queried
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check if tables exist
            tables = [
                "warehouses",
                "warehouse_transfers",
                "carriers",
                "shipments",
                "routes",
                "shipment_events",
            ]
            for table in tables:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                if cursor.fetchone():
                    logger.info(f"✅ الجدول {table} موجود")
                else:
                    logger.warning(f"⚠️ الجدول {table} غير موجود")

            # Test inserting sample data
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO carriers
                    (carrier_id, name, type, reliability_score, average_cost_per_kg, average_delivery_days, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    ("TEST_CAR001", "Test Carrier", "ground", 0.9, 10.0, 2, 1),
                )

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO warehouses
                    (code, name, address, city, country, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        "TEST_WH001",
                        "Test Warehouse",
                        "Test Address",
                        "Test City",
                        "Saudi Arabia",
                        1,
                    ),
                )

                conn.commit()
                logger.info("✅ تم إدراج البيانات التجريبية بنجاح")

            except Exception as e:
                logger.error(f"❌ فشل إدراج البيانات التجريبية: {e}")

            # Test querying data
            cursor.execute("SELECT COUNT(*) FROM carriers WHERE carrier_id LIKE 'TEST_%'")
            carrier_count = cursor.fetchone()[0]
            logger.info(f"📊 عدد شركات الشحن التجريبية: {carrier_count}")

            cursor.execute("SELECT COUNT(*) FROM warehouses WHERE code LIKE 'TEST_%'")
            warehouse_count = cursor.fetchone()[0]
            logger.info(f"📊 عدد المخازن التجريبية: {warehouse_count}")

        logger.info("🎉 تم إكمال اختبار التكامل الأساسي بنجاح!")

        return True

    except Exception as e:
        logger.error(f"❌ فشل اختبار التكامل: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_database_integration()
    sys.exit(0 if success else 1)
