#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Migration Manager
مدير Migrations للقاعدة المحلية
"""

import os
import importlib
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.core.local_database_manager import LocalDatabaseManager
from src.utils.logger import setup_logger


class LocalMigrationManager:
    """مدير Migrations للقاعدة المحلية"""
    
    def __init__(self, db_manager: LocalDatabaseManager):
        self.db = db_manager
        self.logger = setup_logger(__name__)
        self.migrations_dir = Path(__file__).parent / "migrations"
    
    def initialize(self):
        """تهيئة جدول schema_migrations"""
        self.db.execute_non_query("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
    
    def get_applied_migrations(self) -> List[str]:
        """الحصول على قائمة Migrations المطبقة"""
        results = self.db.execute_query(
            "SELECT version FROM schema_migrations ORDER BY version",
            exclude_deleted=False
        )
        return [row['version'] for row in results]
    
    def get_pending_migrations(self) -> List[str]:
        """الحصول على قائمة Migrations المعلقة"""
        applied = set(self.get_applied_migrations())
        all_migrations = self._discover_migrations()
        return [m for m in all_migrations if m not in applied]
    
    def _discover_migrations(self) -> List[str]:
        """اكتشاف جميع Migrations المتاحة"""
        migrations = []
        if not self.migrations_dir.exists():
            return migrations
        
        for file in sorted(self.migrations_dir.glob("*.py")):
            if file.name.startswith("__"):
                continue
            # استخراج رقم الإصدار من اسم الملف (مثل 001_initial_schema.py -> 001)
            version = file.stem.split("_")[0]
            if version.isdigit():
                migrations.append(version)
        
        return sorted(migrations)
    
    def apply_migration(self, version: str) -> bool:
        """
        تطبيق Migration
        
        Args:
            version: رقم إصدار Migration
            
        Returns:
            True إذا نجح التطبيق
        """
        try:
            # تحميل Migration
            migration = self._load_migration(version)
            if not migration:
                self.logger.error(f"❌ Migration غير موجود: {version}")
                return False
            
            # تطبيق Migration
            self.logger.info(f"🔄 تطبيق Migration: {version}")
            migration.upgrade(self.db)
            
            # تسجيل Migration
            self.db.execute_non_query(
                """
                INSERT INTO schema_migrations (version, description)
                VALUES (?, ?)
                """,
                (version, migration.description if hasattr(migration, 'description') else '')
            )
            
            self.logger.info(f"✅ تم تطبيق Migration: {version}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل تطبيق Migration {version}: {str(e)}")
            return False
    
    def _load_migration(self, version: str):
        """تحميل Migration"""
        migration_file = self.migrations_dir / f"{version}_*.py"
        files = list(self.migrations_dir.glob(f"{version}_*.py"))
        
        if not files:
            return None
        
        file_path = files[0]
        module_name = f"src.core.local_migrations.migrations.{file_path.stem}"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            self.logger.error(f"❌ فشل تحميل Migration {version}: {str(e)}")
            return None
    
    def apply_all_pending(self) -> bool:
        """تطبيق جميع Migrations المعلقة"""
        pending = self.get_pending_migrations()
        if not pending:
            self.logger.info("✅ لا توجد Migrations معلقة")
            return True
        
        self.logger.info(f"🔄 تطبيق {len(pending)} Migration معلق...")
        for version in pending:
            if not self.apply_migration(version):
                return False
        
        self.logger.info("✅ تم تطبيق جميع Migrations المعلقة")
        return True
