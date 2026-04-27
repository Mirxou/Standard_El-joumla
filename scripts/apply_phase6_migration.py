#!/usr/bin/env python3
"""
Phase 6: Multi-Warehouse Management & Logistics Integration
Database Migration Script
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_migration():
    """Apply Phase 6 multi-warehouse logistics migration"""
    try:
        logger.info("🚀 بدء تطبيق migration المرحلة 6: إدارة المخازن واللوجستيات")

        # Initialize managers
        config_manager = ConfigManager()
        db_path = config_manager.get('database.path', 'data/erp_system.db')
        db_manager = DatabaseManager(db_path=db_path)
        db_manager.initialize()

        # Read migration file
        migration_path = project_root / 'migrations' / '030_multi_warehouse_logistics.sql'
        if not migration_path.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_path}")

        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        logger.info("📄 قراءة ملف الـ migration")

        # Execute migration
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

            for i, statement in enumerate(statements, 1):
                if statement:
                    logger.info(f"⚡ تنفيذ البيان {i}/{len(statements)}")
                    cursor.execute(statement)

            conn.commit()
            logger.info("✅ تم تطبيق الـ migration بنجاح")

        # Verify tables were created
        verify_tables(db_manager)

        logger.info("🎉 تم إكمال migration المرحلة 6 بنجاح!")

    except Exception as e:
        logger.error(f"❌ فشل في تطبيق الـ migration: {e}")
        raise

def verify_tables(db_manager):
    """Verify that all required tables were created"""
    required_tables = [
        'warehouses',
        'warehouse_transfers',
        'carriers',
        'shipments',
        'routes',
        'shipment_events'
    ]

    logger.info("🔍 التحقق من إنشاء الجداول...")

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()

        for table in required_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                logger.info(f"✅ تم إنشاء الجدول: {table}")
            else:
                logger.warning(f"⚠️ لم يتم العثور على الجدول: {table}")

        # Check sample data
        for table in ['warehouses', 'carriers', 'routes']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"📊 عدد السجلات في {table}: {count}")

if __name__ == "__main__":
    apply_migration()