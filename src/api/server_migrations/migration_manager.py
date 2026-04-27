#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server Migration Manager
مدير Migrations للخادم (Server-side)
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


class ServerMigrationManager:
    """مدير Migrations للخادم"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        تهيئة Server Migration Manager
        
        Args:
            db_manager: مدير قاعدة البيانات (Server-side)
        """
        self.db = db_manager
        self.logger = setup_logger(__name__)
        # استخدام مجلد migrations الموجود في الجذر
        project_root = Path(__file__).parent.parent.parent.parent
        self.migrations_dir = project_root / "migrations"
    
    def initialize(self):
        """تهيئة جدول schema_migrations"""
        try:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_file TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            self.logger.info("✅ تم تهيئة جدول schema_migrations")
        except Exception as e:
            self.logger.error(f"❌ فشل تهيئة جدول schema_migrations: {str(e)}")
    
    def get_applied_migrations(self) -> List[str]:
        """الحصول على قائمة Migrations المطبقة"""
        try:
            results = self.db.fetch_all(
                "SELECT migration_file FROM schema_migrations ORDER BY migration_file"
            )
            return [row['migration_file'] for row in results]
        except Exception as e:
            self.logger.error(f"❌ فشل جلب Migrations المطبقة: {str(e)}")
            return []
    
    def get_pending_migrations(self) -> List[str]:
        """الحصول على قائمة Migrations المعلقة"""
        applied = set(self.get_applied_migrations())
        all_migrations = self._discover_migrations()
        return [m for m in all_migrations if m not in applied]
    
    def _discover_migrations(self) -> List[str]:
        """اكتشاف جميع Migrations المتاحة"""
        migrations = []
        if not self.migrations_dir.exists():
            self.logger.warning(f"⚠️ مجلد migrations غير موجود: {self.migrations_dir}")
            return migrations
        
        # البحث عن ملفات .sql
        for file in sorted(self.migrations_dir.glob("*.sql")):
            migrations.append(file.name)
        
        return migrations
    
    def apply_migration(self, migration_file: str) -> bool:
        """
        تطبيق Migration
        
        Args:
            migration_file: اسم ملف Migration
        
        Returns:
            True إذا نجح التطبيق
        """
        try:
            migration_path = self.migrations_dir / migration_file
            if not migration_path.exists():
                self.logger.error(f"❌ ملف Migration غير موجود: {migration_file}")
                return False
            
            # قراءة محتوى Migration
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # تطبيق Migration (يجب أن يكون في transaction)
            self.logger.info(f"🔄 تطبيق Migration: {migration_file}")
            
            # تقسيم SQL إلى عبارات منفصلة
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        self.db.execute_non_query(statement)
                    except Exception as e:
                        # تجاهل الأخطاء المتعلقة بالجداول/الأعمدة الموجودة مسبقاً
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            self.logger.warning(f"⚠️ تم تجاهل خطأ (موجود مسبقاً): {str(e)}")
                        else:
                            raise e
            
            # تسجيل Migration
            self.db.execute_non_query(
                """
                INSERT OR IGNORE INTO schema_migrations (migration_file, description)
                VALUES (?, ?)
                """,
                (migration_file, f"Migration: {migration_file}")
            )
            
            self.logger.info(f"✅ تم تطبيق Migration: {migration_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل تطبيق Migration {migration_file}: {str(e)}")
            return False
    
    def apply_all_pending(self) -> Dict[str, Any]:
        """
        تطبيق جميع Migrations المعلقة
        
        Returns:
            نتيجة التطبيق
        """
        result = {
            'success': True,
            'applied': [],
            'failed': [],
            'skipped': []
        }
        
        # تهيئة جدول schema_migrations
        self.initialize()
        
        pending = self.get_pending_migrations()
        if not pending:
            self.logger.info("✅ لا توجد Migrations معلقة")
            return result
        
        self.logger.info(f"🔄 تطبيق {len(pending)} Migration معلق")
        
        for migration_file in pending:
            if self.apply_migration(migration_file):
                result['applied'].append(migration_file)
            else:
                result['failed'].append(migration_file)
                result['success'] = False
        
        return result
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        الحصول على حالة Migrations
        
        Returns:
            معلومات عن حالة Migrations
        """
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        all_migrations = self._discover_migrations()
        
        return {
            'total': len(all_migrations),
            'applied': len(applied),
            'pending': len(pending),
            'applied_list': applied,
            'pending_list': pending,
            'all_list': all_migrations
        }
