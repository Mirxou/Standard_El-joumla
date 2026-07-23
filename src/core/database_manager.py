#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
"""
مدير قاعدة البيانات - Database Manager
إدارة الاتصال بقاعدة البيانات والعمليات الأساسية
"""

import json
import os
import re
import shutil
import sqlite3
import threading
import time
from datetime import date, datetime, timedelta

# Fix for Python 3.12 DeprecationWarning: The default date/datetime adapter is deprecated
sqlite3.register_adapter(date, lambda val: val.isoformat())
sqlite3.register_adapter(datetime, lambda val: val.isoformat())
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core.database_metrics import get_database_metrics
from src.core.encrypted_backup_service import EncryptedBackupService
from src.database.backend import DatabaseBackend
from src.database.connection_pool import ConnectionPool, PoolConfig
from src.utils.logger import setup_logger

from .encryption_manager import EncryptionManager
from .exceptions import DatabaseException


# Intercept clean pytest runs on exit has been moved to tests/unit/conftest.py
# to avoid double registration and prevent access violations.


class DatabaseManager:
    """
    مدير قاعدة البيانات (Server-side)

    ⚠️ ملاحظة مهمة: Desktop App يجب أن يستخدم LocalDatabaseManager
    بدلاً من هذا الكلاس. هذا الكلاس مخصص للخادم فقط.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        encryption_password: Optional[str] = None,
        pool_options: Optional[Dict[str, Any]] = None,
        backup_options: Optional[Dict[str, Any]] = None,
        backend: Optional[DatabaseBackend] = None,
    ):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.db_path = str(project_root / "data" / "logical_release.db")
        else:
            self.db_path = db_path
        # Production override: support external DB path via environment variable
        env_db_path = os.environ.get("LOGICAL_DB_PATH")
        if env_db_path:
            self.db_path = env_db_path

        # Database Backend (Abstraction Layer)
        self.backend: Optional[DatabaseBackend] = backend

        # للحفاظ على backward compatibility مع الكود القديم
        self.connection = None
        # Thread-local storage لإدارة المعاملات (Transactions)
        self._thread_local = threading.local()
        self.pool: Optional[ConnectionPool] = None
        self.encryption_manager = None
        self.encryption_password = encryption_password
        self.is_encrypted = False
        self.encrypted_backup_service: Optional[EncryptedBackupService] = None
        self._pool_options = pool_options or {}
        self._backup_options = backup_options or {}
        # عتبة الاستعلام البطيء بالمللي ثانية (يمكن ضبطها لاحقاً)
        self.slow_query_threshold_ms: float = 100.0

        # تهيئة logger
        self.logger = setup_logger(__name__)

        # Database Metrics
        self.metrics = get_database_metrics()

        self._temp_db_path: Optional[str] = None  # C1: تتبع ملف DB المؤقت المشفّر

        self._ensure_data_directory()

        # التحقق من حالة التشفير
        if os.path.exists(self.db_path):
            self.encryption_manager = EncryptionManager()
            self.is_encrypted = self.encryption_manager.is_database_encrypted(self.db_path)

    def _ensure_data_directory(self):
        """التأكد من وجود مجلد البيانات"""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    def _verify_database_integrity(self) -> bool:
        """التحقق من سلامة قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            return result[0] == "ok"
        except Exception as e:
            # استخدام log لتفادي monkey-patch في البيئة الاختبارية
            self.logger.error(f"Database integrity check failed: {e}")
            return False

    def _attempt_database_recovery(self):
        """محاولة استعادة قاعدة البيانات التالفة"""
        try:
            # محاولة إنشاء نسخة احتياطية من الملف التالف
            corrupted_path = self.db_path + ".corrupted"
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, corrupted_path)
                self.logger.warning(f"Created backup of corrupted database: {corrupted_path}")

            # محاولة إصلاح قاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check")
            result = cursor.fetchone()
            conn.close()

            if result[0] != "ok":
                # استخدام log لتفادي monkey-patch في البيئة الاختبارية
                self.logger.error("Database recovery failed - may need manual intervention")
        except Exception as e:
            # استخدام log لتفادي monkey-patch في البيئة الاختبارية
            self.logger.error(f"Database recovery attempt failed: {e}")

    def initialize(self) -> bool:
        """تهيئة قاعدة البيانات"""
        try:
            # التحقق من وجود قاعدة البيانات
            if not os.path.exists(self.db_path):
                self.logger.info(f"Creating new database at: {self.db_path}")

            # فحص سلامة قاعدة البيانات قبل الاتصال
            if os.path.exists(self.db_path) and not self.is_encrypted:
                if not self._verify_database_integrity():
                    # استخدام log لتفادي monkey-patch في البيئة الاختبارية
                    self.logger.error("Database integrity check failed - attempting recovery")
                    self._attempt_database_recovery()

            # استخدام Backend abstraction إذا كان متوفراً
            if self.backend:
                if not self.backend.connect():
                    raise DatabaseException("فشل الاتصال بقاعدة البيانات")
                # استخدام backend للاتصال
                if hasattr(self.backend, "get_connection"):
                    self.connection = self.backend.get_connection()
                return True

            # الكود القديم (backward compatibility)
            # التعامل مع قاعدة البيانات المشفرة
            temp_db_path = None
            if self.is_encrypted and self.encryption_password:
                try:
                    # فك تشفير قاعدة البيانات مؤقتاً للوصول إليها
                    temp_db_path = self.db_path + ".temp"
                    self.encryption_manager.password = self.encryption_password
                    self.encryption_manager.decrypt_file(self.db_path, temp_db_path)

                    # الاتصال بقاعدة البيانات المفكوكة التشفير
                    self.connection = sqlite3.connect(
                        temp_db_path,
                        check_same_thread=False,
                        timeout=60.0,  # زيادة من 30.0 إلى 60.0 للتعامل مع العمليات الثقيلة
                    )
                except Exception as e:
                    # cleanup آمن في حالة الفشل
                    if temp_db_path and os.path.exists(temp_db_path):
                        try:
                            os.remove(temp_db_path)
                        except OSError:
                            self.logger.warning("Ignored exception during encrypted DB cleanup")
                    raise DatabaseException(f"فشل فك تشفير قاعدة البيانات: {e}")

                # C1 FIX: لا نحذف الملف المؤقت هنا — نحتاجه مفتوحاً مع الاتصال
                # سيتم حذفه في close() بعد إعادة التشفير
                self._temp_db_path = temp_db_path

            else:
                # إنشاء الاتصال العادي
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=60.0,  # زيادة من 30.0 إلى 60.0 للتعامل مع العمليات الثقيلة
                )

            # تفعيل WAL mode للأداء والموثوقية
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=MEMORY")

            # تفعيل المفاتيح الخارجية
            self.connection.execute("PRAGMA foreign_keys=ON")

            # إنشاء الجداول إذا لم تكن موجودة
            self._create_tables()

            # ترقية الجداول الحالية لتتوافق مع المخططات المحدثة
            self._upgrade_existing_schema()

            # إنشاء الفهارس
            self._create_indexes()

            # تشغيل الهجرات
            self._run_migrations()

            # 🔥 تشغيل ترحيل الميزات المحسنة (Enhanced Features Migration)
            self.check_and_migrate_db()

            # تهيئة Connection Pool للاستخدام العام (تخطي الذاكرة)
            if self.pool is None and not self.is_encrypted:
                if self.db_path == ":memory:" or str(self.db_path).startswith("file::memory:"):
                    self.pool = None
                else:
                    enabled = self._pool_options.get("enabled", True)
                    if enabled:
                        cfg = PoolConfig(
                            pool_size=int(self._pool_options.get("pool_size", 15)),  # زيادة من 10 إلى 15
                            max_overflow=int(self._pool_options.get("max_overflow", 30)),  # زيادة من 20 إلى 30
                            timeout=float(self._pool_options.get("timeout", 60.0)),  # زيادة من 30.0 إلى 60.0
                        )
                        self.pool = ConnectionPool(self.db_path, cfg)

            # تهيئة خدمة النسخ الاحتياطي (مشفر عند التمكين)
            if self.encrypted_backup_service is None:
                backups_dir = str(self._backup_options.get("backup_dir", Path(self.db_path).parent / "backups"))
                max_b = int(self._backup_options.get("max_backups", 30))
                bool(self._backup_options.get("encrypted", True))
                key_path = self._backup_options.get("encryption_key_path")
                key_bytes = None
                if key_path:
                    try:
                        key_bytes = Path(key_path).read_bytes()
                    except Exception:
                        key_bytes = None
                # If encryption not enabled we still construct service; it gracefully falls back
                self.encrypted_backup_service = EncryptedBackupService(
                    database_path=self.db_path,
                    backup_dir=backups_dir,
                    encryption_key=key_bytes,
                    max_backups=max_b,
                    compress=True,
                )

            return True

        except DatabaseException:
            raise
        except Exception as e:
            raise DatabaseException(f"خطأ في تهيئة قاعدة البيانات: {e}")

    def _create_tables(self):
        """إنشاء جداول قاعدة البيانات"""

        # جدول الفئات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                name_en TEXT,
                description TEXT,
                parent_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
            )
        """)
        # جدول لتسجيل الاستعلامات البطيئة
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS slow_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                params TEXT,
                duration_ms REAL NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول المنتجات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_en TEXT,
                barcode TEXT UNIQUE,
                category_id INTEGER,
                unit TEXT NOT NULL DEFAULT 'قطعة',
                cost_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                selling_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                wholesale_price DECIMAL(10,2) DEFAULT 0,
                vip_price DECIMAL(10,2) DEFAULT 0,
                min_wholesale_qty INTEGER DEFAULT 10,
                min_stock INTEGER DEFAULT 0,
                current_stock INTEGER DEFAULT 0,
                description TEXT,
                image_path TEXT,
                parent_product_id INTEGER DEFAULT NULL,
                conversion_factor INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (parent_product_id) REFERENCES products(id)
            )
        """)

        # جدول الموردين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                phone2 TEXT,
                email TEXT,
                address TEXT,
                tax_number TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول الدفعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                batch_number TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                cost_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2),
                expiry_date DATE,
                purchase_date DATE DEFAULT CURRENT_DATE,
                supplier_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        """)

        # جدول العملاء
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                credit_limit DECIMAL(10,2) DEFAULT 0,
                current_balance DECIMAL(10,2) DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول المبيعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                total_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                final_amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT DEFAULT 'نقدي',
                sale_date DATE DEFAULT CURRENT_DATE,
                user_id INTEGER,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # جدول عناصر المبيعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                cost_price DECIMAL(10,2) NOT NULL,
                profit DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (batch_id) REFERENCES batches(id)
            )
        """)

        # جدول المشتريات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                final_amount DECIMAL(10,2) NOT NULL,
                purchase_date DATE DEFAULT CURRENT_DATE,
                user_id INTEGER,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # جدول عناصر المشتريات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost DECIMAL(10,2) NOT NULL,
                total_cost DECIMAL(10,2) NOT NULL,
                expiry_date DATE,
                batch_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # جدول المستخدمين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                full_name TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_locked BOOLEAN DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                last_password_change TIMESTAMP,
                password_expires_at TIMESTAMP,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # جدول سجل العمليات (Enhanced Audit Log)
        # جدول سجل العمليات (Enhanced Audit Log)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                module TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                changes_summary TEXT,
                ip_address TEXT,
                user_agent TEXT,
                session_id TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        # جدول حركات المخزون
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                notes TEXT,
                user_id INTEGER,
                movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (batch_id) REFERENCES batches(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # جدول صلاحيات المستخدمين (النسخة القديمة للاحتياط)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, permission)
            )
        """)

        # الجداول الجديدة للصلاحيات والأدوار
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                resource_type TEXT NOT NULL,
                action TEXT NOT NULL,
                description TEXT,
                is_system BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                description TEXT,
                is_system BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
            )
        """)

        # جدول المدفوعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_type TEXT NOT NULL CHECK (
                    payment_type IN ('customer_payment', 'supplier_payment', 'expense', 'other')
                ),
                entity_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT NOT NULL CHECK (
                    payment_method IN ('cash', 'check', 'bank_transfer', 'credit_card', 'debit_card')
                ),
                reference_number TEXT,
                payment_date DATE DEFAULT CURRENT_DATE,
                status TEXT NOT NULL DEFAULT 'completed' CHECK (
                    status IN ('pending', 'completed', 'cancelled', 'failed')
                ),
                notes TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # جدول أرصدة الحسابات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS account_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_type TEXT NOT NULL CHECK (account_type IN ('receivable', 'payable')),
                entity_id INTEGER NOT NULL,
                balance DECIMAL(10,2) NOT NULL DEFAULT 0,
                last_payment_date DATE,
                last_payment_amount DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_type, entity_id)
            )
        """)

        # جدول جدولة المدفوعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS payment_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL CHECK (entity_type IN ('customer', 'supplier')),
                amount DECIMAL(10,2) NOT NULL,
                due_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled')),
                payment_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payment_id) REFERENCES payments(id)
            )
        """)

        # جدول ملاحظات الفواتير (Invoice Notes)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS invoice_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                note_text TEXT NOT NULL,
                created_by INTEGER,
                is_internal BOOLEAN DEFAULT 0, -- ملاحظة داخلية لا تظهر للعميل
                is_pinned BOOLEAN DEFAULT 0,   -- ملاحظة مثبّتة بارزة
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # جدول التذكيرات (Reminders) - تذكيرات الدفع والمتابعة
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                customer_id INTEGER,
                reminder_type TEXT NOT NULL CHECK (reminder_type IN ('payment', 'follow_up', 'custom')),
                subject TEXT NOT NULL,
                message TEXT,
                due_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled')),
                attempts INTEGER DEFAULT 0,
                last_attempt_at TIMESTAMP,
                recipient_email TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # جدول قوالب المستندات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS document_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                template_type TEXT NOT NULL, -- 'invoice', 'quote', 'delivery_note', etc.
                definition TEXT NOT NULL,    -- JSON string defining the template structure and style
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, template_type)
            )
        """)

        self.connection.commit()

    # ============================================================
    # 🧱 المرحلة 1: نظام ترحيل قاعدة البيانات (Schema Migration)
    # ============================================================
    def check_and_migrate_db(self):
        """
        يفحص هيكل قاعدة البيانات ويضيف الجداول أو الأعمدة الناقصة تلقائياً.
        يعمل عند بدء التشغيل لضمان توافق النسخة الجديدة مع بيانات العميل القديمة.
        """
        self.logger.info("Checking database schema for updates...")
        # استخدام الاتصال المباشر إذا لم يكن الـ Pool جاهزاً بعد
        conn = self.connection if self.connection else self.get_connection()
        cursor = conn.cursor()

        try:
            # 1. ترحيل جدول المبيعات (إضافة أعمدة جديدة)
            # ----------------------------------------------------
            # ملاحظة: اسم الجدول في هذا المشروع هو 'sales' وليس 'sales_invoices'
            cursor.execute("PRAGMA table_info(sales)")
            columns = [info[1] for info in cursor.fetchall()]

            # إضافة عمود 'status' إذا لم يكن موجوداً
            if "status" not in columns:
                self.logger.info("Adding 'status' column to sales table")
                cursor.execute("ALTER TABLE sales ADD COLUMN status TEXT DEFAULT 'completed'")

            # إضافة عمود 'return_status' (للمرتجعات)
            if "return_status" not in columns:
                self.logger.info("Adding 'return_status' column to sales table")
                cursor.execute("ALTER TABLE sales ADD COLUMN return_status TEXT DEFAULT 'none'")

            # 2. إضافة company_id و role_id إلى جدول users
            # ----------------------------------------------------
            try:
                cursor.execute("PRAGMA table_info(users)")
                user_columns = [info[1] for info in cursor.fetchall()]

                if "company_id" not in user_columns:
                    self.logger.info("Adding 'company_id' column to users table")
                    cursor.execute("ALTER TABLE users ADD COLUMN company_id INTEGER")
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_users_company
                        ON users(company_id)
                    """)
                    self.logger.info("Successfully added company_id column to users table")

                if "role_id" not in user_columns:
                    self.logger.info("Adding 'role_id' column to users table")
                    cursor.execute("ALTER TABLE users ADD COLUMN role_id INTEGER")
                    self.logger.info("Successfully added role_id column to users table")
            except Exception as e:
                self.logger.warning(f"Could not update users columns: {e}")

            # 3. ترحيل جدول الفئات (إضافة name_en)
            # ----------------------------------------------------
            try:
                cursor.execute("PRAGMA table_info(categories)")
                cat_columns = [info[1] for info in cursor.fetchall()]

                if "name_en" not in cat_columns:
                    self.logger.info("Adding 'name_en' column to categories table")
                    cursor.execute("ALTER TABLE categories ADD COLUMN name_en TEXT")
                    self.logger.info("Successfully added name_en column to categories table")
            except Exception as e:
                self.logger.warning(f"Could not add name_en to categories: {e}")

            # 4. إنشاء جداول المرتجعات (Returns Tables) - للميزات المحسنة
            # ----------------------------------------------------
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS return_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_invoice_id INTEGER,
                    return_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    total_refund_amount REAL,
                    status TEXT DEFAULT 'approved',
                    FOREIGN KEY(original_invoice_id) REFERENCES sales(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS return_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER,
                    product_id INTEGER,
                    quantity REAL,
                    refund_price REAL,
                    FOREIGN KEY(return_id) REFERENCES return_invoices(id),
                    FOREIGN KEY(product_id) REFERENCES products(id)
                )
            """)

            # 4. إتمام التغييرات
            conn.commit()
            self.logger.info("Database schema is up to date")
        except Exception as e:
            self.logger.error(f"Error during database migration: {e}")
            # لا نوقف البرنامج، لكن نسجل الخطأ
        finally:
            # لا نغلق الاتصال هنا لأنه قد يكون الاتصال الرئيسي
            pass

    def _create_enhanced_tables(self):
        """إنشاء جداول الميزات المحسنة (المرتجعات، الاسترداد)"""
        # جدول المرتجعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS return_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        """)

        # جدول عناصر المرتجعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (return_id) REFERENCES return_invoices(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # جدول الاسترداد (Refunds)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        """)
        self.connection.commit()

    def _get_table_columns(self, table_name: str) -> Set[str]:
        """الحصول على الأعمدة الحالية لجدول معين"""
        try:
            # التحقق من صحة اسم الجدول
            if not table_name.replace("_", "").replace("-", "").isalnum():
                self.logger.warning(f"Invalid table name: {table_name}")
                return set()
            cursor = self.connection.execute(f'PRAGMA table_info("{table_name}")')
            return {row[1] for row in cursor.fetchall()}
        except Exception:
            return set()

    def _add_column_if_missing(self, table: str, column: str, definition: str) -> None:
        """إضافة عمود إذا لم يكن موجوداً"""
        # التحقق من صحة أسماء الجدول والعمود
        if not table.replace("_", "").replace("-", "").isalnum():
            self.logger.warning(f"Invalid table name: {table}")
            return
        if not column.replace("_", "").replace("-", "").isalnum():
            self.logger.warning(f"Invalid column name: {column}")
            return
        existing = self._get_table_columns(table)
        if column not in existing:
            # Use parameterized query for column name validation
            self.connection.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}')
            self.connection.commit()

    def _upgrade_existing_schema(self) -> None:
        """ضمان توافق قاعدة البيانات مع المخطط الأحدث"""
        try:
            # أعمدة جدول المبيعات
            sales_columns = [
                ("customer_name", "TEXT"),
                ("customer_phone", "TEXT"),
                ("due_date", "DATE"),
                ("status", "TEXT DEFAULT 'مؤكدة'"),
                ("subtotal", "DECIMAL(10,2) DEFAULT 0"),
                ("discount_percentage", "DECIMAL(5,2) DEFAULT 0"),
                ("tax_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("tax_percentage", "DECIMAL(5,2) DEFAULT 0"),
                ("paid_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("remaining_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("currency_id", "INTEGER"),
                ("exchange_rate", "DECIMAL(10,4) DEFAULT 1.0"),
                ("base_amount", "DECIMAL(15,2)"),
                ("converted_amount", "DECIMAL(15,2)"),
                ("created_by", "INTEGER"),
                ("updated_by", "INTEGER"),
            ]
            for column, definition in sales_columns:
                self._add_column_if_missing("sales", column, definition)

            # أعمدة جدول المشتريات
            purchase_columns = [
                ("supplier_invoice_number", "TEXT"),
                ("expected_delivery_date", "DATE"),
                ("received_date", "DATE"),
                ("status", "TEXT DEFAULT 'معلقة'"),
                ("payment_status", "TEXT DEFAULT 'غير مدفوعة'"),
                ("payment_terms", "TEXT"),
                ("subtotal_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("tax_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("shipping_cost", "DECIMAL(10,2) DEFAULT 0"),
                ("paid_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("remaining_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("currency_id", "INTEGER"),
                ("exchange_rate", "DECIMAL(10,4) DEFAULT 1.0"),
                ("base_amount", "DECIMAL(15,2)"),
                ("converted_amount", "DECIMAL(15,2)"),
                ("created_by", "INTEGER"),
                ("updated_by", "INTEGER"),
            ]
            for column, definition in purchase_columns:
                self._add_column_if_missing("purchases", column, definition)

            # أعمدة جدول عناصر المشتريات
            purchase_item_columns = [
                ("quantity_ordered", "DECIMAL(10,2) DEFAULT 0"),
                ("quantity_received", "DECIMAL(10,2) DEFAULT 0"),
                ("discount_percent", "DECIMAL(5,2) DEFAULT 0"),
                ("discount_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("tax_percent", "DECIMAL(5,2) DEFAULT 19"),
                ("tax_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("total_amount", "DECIMAL(10,2) DEFAULT 0"),
                ("notes", "TEXT"),
            ]
            for column, definition in purchase_item_columns:
                self._add_column_if_missing("purchase_items", column, definition)

            # أعمدة جدول الموردين (الرصيد وحد الائتمان)
            supplier_columns = [
                ("credit_limit", "DECIMAL(10,2) DEFAULT 0"),
                ("current_balance", "DECIMAL(10,2) DEFAULT 0"),
            ]
            for column, definition in supplier_columns:
                self._add_column_if_missing("suppliers", column, definition)

            # أعمدة جدول المدفوعات
            payment_columns = [
                ("payment_number", "TEXT"),
                ("currency", "TEXT DEFAULT 'DZD'"),
                ("exchange_rate", "DECIMAL(10,4) DEFAULT 1.0"),
                ("amount_in_base_currency", "DECIMAL(15,2) DEFAULT 0"),
                ("payment_status", "TEXT DEFAULT 'مكتمل'"),
                ("due_date", "DATE"),
                ("customer_id", "INTEGER"),
                ("supplier_id", "INTEGER"),
                ("sale_id", "INTEGER"),
                ("purchase_id", "INTEGER"),
                ("bank_name", "TEXT"),
                ("account_number", "TEXT"),
                ("account_code", "TEXT"),
                ("cost_center", "TEXT"),
            ]
            for column, definition in payment_columns:
                self._add_column_if_missing("payments", column, definition)

            # أعمدة جدول جدولة المدفوعات
            schedules_columns = [
                ("installment_number", "INTEGER DEFAULT 1"),
                ("paid_amount", "DECIMAL(15,2) DEFAULT 0"),
                ("remaining_amount", "DECIMAL(15,2) DEFAULT 0"),
            ]
            for column, definition in schedules_columns:
                self._add_column_if_missing("payment_schedules", column, definition)

            # أعمدة جدول المنتجات للتحويل التلقائي
            product_columns = [
                ("parent_product_id", "INTEGER DEFAULT NULL REFERENCES products(id)"),
                ("conversion_factor", "INTEGER DEFAULT 1"),
            ]
            for column, definition in product_columns:
                self._add_column_if_missing("products", column, definition)

            # تحديث القيم الافتراضية للصفوف الحالية لضمان الاتساق
            self.connection.execute("""
                UPDATE sales SET
                    status = COALESCE(status, 'مؤكدة'),
                    paid_amount = COALESCE(paid_amount, total_amount),
                    remaining_amount = COALESCE(remaining_amount, total_amount - COALESCE(paid_amount, total_amount))
            """)
            self.connection.execute("""
                UPDATE purchases SET
                    status = COALESCE(status, 'معلقة'),
                    payment_status = COALESCE(payment_status, 'غير مدفوعة'),
                    paid_amount = COALESCE(paid_amount, 0),
                    remaining_amount = COALESCE(remaining_amount, total_amount - COALESCE(paid_amount, 0))
            """)
            self.connection.execute("""
                UPDATE payments SET
                    payment_status = COALESCE(payment_status, status),
                    amount_in_base_currency = COALESCE(amount_in_base_currency, amount)
            """)

            self.connection.commit()
        except Exception:
            # في حال حدوث خطأ نكمل التشغيل بدون إيقاف التهيئة
            self.connection.rollback()

    def _create_indexes(self):
        """إنشاء الفهارس لتحسين الأداء"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            # فهارس مركبة لتحسين البحث والتصفية
            "CREATE INDEX IF NOT EXISTS idx_products_active_category ON products(is_active, category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_levels ON products(current_stock, min_stock) WHERE is_active = 1",  # noqa: E501
            "CREATE INDEX IF NOT EXISTS idx_products_search ON products(is_active, category_id, name)",
            "CREATE INDEX IF NOT EXISTS idx_batches_product ON batches(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_batches_expiry ON batches(expiry_date)",
            "CREATE INDEX IF NOT EXISTS idx_batches_supplier ON batches(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(purchase_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_invoice ON purchases(invoice_number)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_query ON stock_movements(product_id, movement_type, created_at)",  # noqa: E501
            # فهارس جداول المدفوعات
            "CREATE INDEX IF NOT EXISTS idx_payments_type ON payments(payment_type)",
            "CREATE INDEX IF NOT EXISTS idx_payments_entity ON payments(entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_account_balances_type_entity ON account_balances(account_type, entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_payment_schedules_entity ON payment_schedules(entity_id, entity_type)",
            "CREATE INDEX IF NOT EXISTS idx_payment_schedules_due_date ON payment_schedules(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_payment_schedules_status ON payment_schedules(status)",
            "CREATE INDEX IF NOT EXISTS idx_invoice_notes_sale ON invoice_notes(sale_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoice_notes_created_by ON invoice_notes(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_reminders_due_at ON reminders(due_at)",
            "CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)",
            "CREATE INDEX IF NOT EXISTS idx_reminders_customer ON reminders(customer_id)",
        ]

        for index_sql in indexes:
            cursor = self.connection.execute(index_sql)
            cursor.close()

        self.connection.commit()

    def _is_in_transaction(self) -> bool:
        """التحقق من وجود معاملة نشطة في الخيط الحالي."""
        return getattr(self._thread_local, "active_transaction", False)

    def _get_transaction_conn(self):
        """الحصول على اتصال المعاملة النشطة."""
        return getattr(self._thread_local, "transaction_conn", None)

    @contextmanager
    def get_cursor(self):
        """الحصول على cursor مع إدارة تلقائية للموارد.
        إذا كانت هناك معاملة نشطة، يُعاد استخدام اتصالها."""
        # إذا كنا داخل معاملة نشطة، نستخدم اتصال المعاملة
        txn_conn = self._get_transaction_conn()
        if txn_conn is not None:
            cursor = txn_conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
            return

        # خارج المعاملة: سلوك عادي
        if self.pool is not None:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    yield cursor
                finally:
                    cursor.close()
        else:
            cursor = self.connection.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    @contextmanager
    def transaction(self):
        """سياق لإدارة المعاملات (Transactions) بشكل ذري.

        جميع عمليات execute_insert / execute_non_query داخل هذا السياق
        ستستخدم نفس الاتصال ولن تقوم بـ commit حتى انتهاء السياق بنجاح.
        في حالة حدوث خطأ، يتم rollback تلقائي.

        Usage:
            with db_manager.transaction() as cursor:
                db_manager.execute_insert(query1, params1)
                db_manager.execute_insert(query2, params2)
                # commit happens automatically here
        """
        # منع التداخل: إذا كنا بالفعل داخل معاملة
        if self._is_in_transaction():
            # Nested transaction: نكمل بدون BEGIN/COMMIT إضافي
            cursor = self._get_transaction_conn().cursor()
            try:
                yield cursor
            finally:
                cursor.close()
            return

        if self.pool is not None:
            # Pool mode: استخدام get_connection() context manager
            with self.pool.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                self._thread_local.active_transaction = True
                self._thread_local.transaction_conn = conn
                cursor = conn.cursor()
                try:
                    yield cursor
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
                finally:
                    cursor.close()
                    self._thread_local.active_transaction = False
                    self._thread_local.transaction_conn = None
        else:
            # Single connection mode
            conn = self.connection
            conn.execute("BEGIN IMMEDIATE")
            self._thread_local.active_transaction = True
            self._thread_local.transaction_conn = conn
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
                self._thread_local.active_transaction = False
                self._thread_local.transaction_conn = None

    def execute_query(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام وإرجاع النتائج أو cursor للعمليات الأخرى"""
        with self.get_cursor() as cursor:
            start_t = time.perf_counter()
            cursor.execute(query, params)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)
            # إذا كان الاستعلام يحتوي على نتائج (SELECT)
            if cursor.description:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                # للعمليات الأخرى مثل CREATE, INSERT, UPDATE, DELETE
                if self.pool is None:
                    self.connection.commit()
                else:
                    # مع Pool، يتم الالتزام عبر الاتصال داخل السياق
                    cursor.connection.commit()
                return cursor

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """تنفيذ استعلام وإرجاع صف واحد كـ dict"""
        with self.get_cursor() as cursor:
            start_t = time.perf_counter_ns()
            cursor.execute(query, params)
            duration_ms = (time.perf_counter_ns() - start_t) / 1_000_000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)
            row = cursor.fetchone()
            if row is None:
                return None
            # C3 FIX: تحويل الصف إلى dict لدعم .get() بشكل موثوق
            if isinstance(row, dict):
                return row
            if hasattr(row, 'keys'):
                return dict(row)
            # fallback: إذا كان tuple و cursor.description متوفر
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return dict(row) if row else None

    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """تنفيذ استعلام وإرجاع جميع الصفوف كـ list of dict"""
        with self.get_cursor() as cursor:
            start_t = time.perf_counter()
            cursor.execute(query, params)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)
            rows = cursor.fetchall()
            if not rows:
                return []
            # C3 FIX: تحويل كل صف إلى dict
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            # fallback إذا لم يكن description متوفراً
            return [dict(r) if hasattr(r, 'keys') else r for r in rows]

    def execute_non_query(self, query: str, params: Tuple = ()) -> int:
        """تنفيذ استعلام INSERT/UPDATE/DELETE وإرجاع عدد الصفوف المتأثرة.
        يتخطى auto-commit إذا كنا داخل معاملة نشطة."""
        with self.get_cursor() as cursor:
            start_t = time.perf_counter()
            cursor.execute(query, params)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)
            # تخطي commit داخل المعاملات — سيتم commit في نهاية transaction()
            if not self._is_in_transaction():
                if self.pool is None:
                    self.connection.commit()
                else:
                    cursor.connection.commit()
            return cursor.rowcount

    def execute_insert(self, query: str, params: Tuple = ()) -> Optional[int]:
        """
        🔥 CRITICAL FIX: تنفيذ استعلام INSERT وإرجاع lastrowid مباشرة
        هذا يحل مشكلة last_insert_rowid() التي تعيد 0 عند استخدام cursor منفصل

        Returns:
            Optional[int]: آخر ID تم إدراجه، أو None إذا فشل
        """
        # استخدام Backend إذا كان متوفراً
        if self.backend:
            start_t = time.perf_counter()
            result = self.backend.execute_insert(query, params)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)
            return result

        # الكود القديم (backward compatibility)
        with self.get_cursor() as cursor:
            start_t = time.perf_counter()
            cursor.execute(query, params)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)

            # 🔥 CRITICAL: الحصول على lastrowid من نفس cursor قبل commit
            # lastrowid يعمل فقط على نفس cursor الذي نفذ INSERT
            lastrowid = cursor.lastrowid

            # تخطي commit داخل المعاملات — سيتم commit في نهاية transaction()
            if not self._is_in_transaction():
                if self.pool is None:
                    self.connection.commit()
                else:
                    cursor.connection.commit()

            if lastrowid is not None and lastrowid > 0:
                return lastrowid
            return None

    def execute_scalar(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام وإرجاع قيمة واحدة"""
        # استخدام Backend إذا كان متوفراً
        if self.backend:
            start_t = time.perf_counter()
            result = self.backend.execute_scalar(query, params)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)
            return result

        # الكود القديم (backward compatibility)
        with self.get_cursor() as cursor:
            start_t = time.perf_counter()
            cursor.execute(query, params)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self.metrics.record_query(query, duration_ms, self._detect_query_type(query))
            if duration_ms >= self.slow_query_threshold_ms:
                self._log_slow_query(query, params, duration_ms)
            result = cursor.fetchone()
            return result[0] if result else None

    def get_last_insert_id(self) -> int:
        """الحصول على آخر ID تم إدراجه"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]

    def get_connection(self):
        """
        الحصول على اتصال قاعدة البيانات

        Returns:
            sqlite3.Connection: اتصال قاعدة البيانات
        """
        if not self.connection:
            raise DatabaseException("Database connection not initialized. Call initialize() first.")
        return self.connection

    def _log_slow_query(self, query: str, params: Tuple, duration_ms: float) -> None:
        """تسجيل الاستعلامات البطيئة في جدول slow_queries"""
        # تسجيل في metrics
        self.metrics.record_slow_query(query, duration_ms, self.slow_query_threshold_ms)

        try:
            # تحويل المعاملات إلى JSON نصي لسهولة القراءة
            params_text = None
            if params:
                try:
                    params_text = json.dumps(params, ensure_ascii=False)
                except Exception:
                    params_text = str(params)

            # تسجيل في قاعدة البيانات (إذا كان الاتصال متاحاً)
            if self.connection:
                self.connection.execute(
                    "INSERT INTO slow_queries (query_text, params, duration_ms) VALUES (?, ?, ?)",
                    (query, params_text, float(f"{duration_ms:.3f}")),
                )
                self.connection.commit()
        except Exception:
            # عدم رفع الاستثناء للحفاظ على استقرار التنفيذ الأساسي
            logging.getLogger(__name__).warning("Ignored exception in database_manager.py")

    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = Path(self.db_path).parent / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_path = str(backup_dir / f"backup_{timestamp}.db")

            shutil.copy2(self.db_path, backup_path)
            return True

        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False

    def backup_database_encrypted(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """إنشاء نسخة احتياطية مشفرة باستخدام EncryptedBackupService"""
        try:
            if self.encrypted_backup_service is None:
                backups_dir = str(Path(self.db_path).parent / "backups")
                self.encrypted_backup_service = EncryptedBackupService(self.db_path, backups_dir)
            backup_file = self.encrypted_backup_service.create_backup(metadata=metadata)
            return str(backup_file) if backup_file else None
        except Exception as e:
            self.logger.error(f"خطأ في النسخ الاحتياطي المشفر: {e}")
            return None

    def restore_database(self, backup_path: str) -> bool:
        """استعادة قاعدة البيانات من نسخة احتياطية"""
        try:
            if not os.path.exists(backup_path):
                return False

            # إغلاق الاتصال الحالي
            if self.connection:
                self.connection.close()

            # استعادة النسخة الاحتياطية
            shutil.copy2(backup_path, self.db_path)

            # إعادة تهيئة الاتصال
            return self.initialize()

        except Exception as e:
            self.logger.error(f"خطأ في استعادة النسخة الاحتياطية: {e}")
            return False

    def restore_database_encrypted(self, backup_file: str) -> bool:
        """استعادة قاعدة البيانات من نسخة احتياطية مشفرة"""
        try:
            if self.encrypted_backup_service is None:
                backups_dir = str(Path(self.db_path).parent / "backups")
                self.encrypted_backup_service = EncryptedBackupService(self.db_path, backups_dir)
            # إغلاق الاتصال الحالي
            if self.connection:
                self.connection.close()
            success = self.encrypted_backup_service.restore_backup(backup_file, restore_path=self.db_path)
            if not success:
                return False
            # إعادة التهيئة بعد الاستعادة
            return self.initialize()
        except Exception as e:
            self.logger.error(f"Error restoring encrypted backup: {e}")
            return False

    def cleanup_old_backups(self, max_backups: int = 30):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            backup_dir = Path(self.db_path).parent / "backups"
            if not backup_dir.exists():
                return

            # البحث عن جميع أنواع النسخ الاحتياطية
            backup_files = []
            backup_files.extend(backup_dir.glob("backup_*.db"))
            backup_files.extend(backup_dir.glob("backup_*.db.encrypted"))
            backup_files.extend(backup_dir.glob("*.backup"))
            backup_files.extend(backup_dir.glob("*.bak"))

            # ترتيب حسب تاريخ التعديل (الأحدث أولاً)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # حذف النسخ الزائدة
            deleted_count = 0
            for backup_file in backup_files[max_backups:]:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"فشل حذف {backup_file}: {e}")

            if deleted_count > 0:
                self.logger.info(f"تم حذف {deleted_count} نسخة احتياطية قديمة")

        except Exception as e:
            self.logger.error(f"خطأ في تنظيف النسخ الاحتياطية: {e}")

    def checkpoint_wal(self) -> bool:
        """
        دمج ملفات WAL في قاعدة البيانات الرئيسية

        Returns:
            True إذا نجحت العملية، False خلاف ذلك
        """
        try:
            if not self.connection:
                return False

            # H1 FIX: تنفيذ checkpoint مع إغلاق المؤشر
            with self.connection.execute("PRAGMA wal_checkpoint(FULL)") as cursor:
                result = cursor.fetchone()

            # التحقق من النتيجة
            if result and (result[0] if not isinstance(result, dict) else result.get('busy', 0)) == 0:
                self.logger.info("تم دمج ملفات WAL بنجاح")
                return True
            else:
                self.logger.warning(f"فشل دمج WAL - النتيجة: {result}")
                return False

        except Exception as e:
            self.logger.error(f"خطأ في دمج ملفات WAL: {e}")
            return False

    def get_database_size_info(self) -> Dict[str, Any]:
        """
        الحصول على معلومات حجم قاعدة البيانات

        Returns:
            قاموس يحتوي على معلومات الحجم
        """
        try:
            db_path = Path(self.db_path)
            wal_path = db_path.with_suffix(".db-wal")
            shm_path = db_path.with_suffix(".db-shm")

            info = {
                "database_size": db_path.stat().st_size if db_path.exists() else 0,
                "file_size_bytes": db_path.stat().st_size if db_path.exists() else 0,
                "wal_size": wal_path.stat().st_size if wal_path.exists() else 0,
                "shm_size": shm_path.stat().st_size if shm_path.exists() else 0,
                "total_size": 0,
            }

            if self.connection:
                # H2 FIX: إغلاق المؤشرات الضمنية
                try:
                    with self.connection.execute("PRAGMA page_count") as cur:
                        row = cur.fetchone()
                        info["page_count"] = row[0] if row else 0
                except Exception:
                    info["page_count"] = 0
                try:
                    with self.connection.execute("PRAGMA page_size") as cur:
                        row = cur.fetchone()
                        info["page_size"] = row[0] if row else 0
                except Exception:
                    info["page_size"] = 0
            else:
                info["page_count"] = 0
                info["page_size"] = 0

            info["total_size"] = info["database_size"] + info["wal_size"] + info["shm_size"]

            # تحويل إلى MB
            info["database_size_mb"] = round(info["database_size"] / (1024 * 1024), 2)
            info["wal_size_mb"] = round(info["wal_size"] / (1024 * 1024), 2)
            info["shm_size_kb"] = round(info["shm_size"] / 1024, 2)
            info["total_size_mb"] = round(info["total_size"] / (1024 * 1024), 2)

            return info

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على معلومات الحجم: {e}")
            return {}

    def vacuum_database(self) -> bool:
        """
        تنظيف قاعدة البيانات وتحسينها

        Returns:
            True إذا نجحت العملية، False خلاف ذلك
        """
        try:
            if not self.connection:
                return False

            self.logger.info("Starting database cleanup...")

            # دمج WAL أولاً
            self.checkpoint_wal()

            # تنفيذ VACUUM
            self.connection.execute("VACUUM")
            self.connection.commit()

            self.logger.info("Database cleanup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error in database cleanup: {e}")
            return False

    def cleanup_old_data(self, days: int = 90, tables: Optional[List[str]] = None) -> Dict[str, int]:
        """
        تنظيف البيانات القديمة من قاعدة البيانات

        Args:
            days: عدد الأيام للاحتفاظ بالبيانات (افتراضي 90 يوم)
            tables: قائمة الجداول المراد تنظيفها (None = جميع الجداول المدعومة)

        Returns:
            قاموس يحتوي على عدد السجلات المحذوفة لكل جدول
        """
        try:
            if not self.connection:
                return {}

            # الجداول المدعومة للتنظيف مع أعمدة التاريخ
            supported_tables = tables or {
                "audit_logs": "created_at",
                "login_history": "login_time",
                "slow_queries": "executed_at",
                "backup_history": "created_at",
                "session_logs": "created_at",
            }

            deleted_counts = {}
            cutoff_date = datetime.now() - timedelta(days=days)

            self.logger.info(f"Starting cleanup for data older than {cutoff_date.strftime('%Y-%m-%d')}...")

            for table_name, date_column in supported_tables.items():
                if not self.table_exists(table_name):
                    continue

                try:
                    # التحقق من صحة اسم الجدول
                    if not table_name.replace("_", "").replace("-", "").isalnum():
                        self.logger.warning(f"Invalid table name: {table_name}")
                        continue

                    # التحقق من وجود العمود - PRAGMA does not support parameter binding
                    cursor = self.connection.execute(f'PRAGMA table_info("{table_name}")')
                    columns = [col[1] for col in cursor.fetchall()]

                    if date_column not in columns:
                        continue

                    # حذف السجلات القديمة
                    delete_query = f"DELETE FROM {table_name} WHERE {date_column} < ?"
                    cursor = self.connection.execute(delete_query, (cutoff_date,))
                    deleted_count = cursor.rowcount

                    if deleted_count > 0:
                        deleted_counts[table_name] = deleted_count
                        self.logger.info(f"تم حذف {deleted_count} سجل من {table_name}")

                except Exception as e:
                    self.logger.warning(f"Failed to cleanup {table_name}: {e}")
                    continue

            # حفظ التغييرات
            self.connection.commit()

            total_deleted = sum(deleted_counts.values())
            self.logger.info(f"إجمالي السجلات المحذوفة: {total_deleted}")

            return deleted_counts

        except Exception as e:
            self.logger.error(f"خطأ في تنظيف البيانات القديمة: {e}")
            self.connection.rollback()
            return {}

    def get_database_info(self) -> Dict[str, Any]:
        """الحصول على معلومات قاعدة البيانات"""
        try:
            info = {
                "path": self.db_path,
            }

            # حجم قاعدة البيانات
            if os.path.exists(self.db_path):
                info["size"] = os.path.getsize(self.db_path)
                info["size_mb"] = round(info["size"] / (1024 * 1024), 2)

            # عدد الجداول
            tables_query = "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            info["tables_count"] = self.execute_scalar(tables_query)

            # معلومات الجداول الرئيسية
            main_tables = [
                "products",
                "categories",
                "batches",
                "sales",
                "purchases",
                "customers",
                "suppliers",
            ]
            info["tables"] = main_tables
            info["records"] = {}

            for table in main_tables:
                if not self.table_exists(table):
                    info["records"][table] = 0
                    continue
                count_query = f"SELECT COUNT(*) FROM {table}"
                info["records"][table] = self.execute_scalar(count_query)

            return info

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على معلومات قاعدة البيانات: {e}")
            return {}

    def enable_encryption(self, password: str) -> bool:
        """تفعيل تشفير قاعدة البيانات"""
        try:
            if self.is_encrypted:
                self.logger.info("Database is already encrypted")
                return True

            # إغلاق الاتصال الحالي
            if self.connection:
                self.connection.close()

            # تشفير قاعدة البيانات
            self.encryption_manager = EncryptionManager()
            self.encryption_manager.encrypt_database(self.db_path, password, backup_original=True)

            # تحديث الحالة
            self.is_encrypted = True
            self.encryption_password = password

            self.logger.info("Database encryption enabled successfully")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في تفعيل التشفير: {e}")
            return False

    def disable_encryption(self, password: str) -> bool:
        """إلغاء تشفير قاعدة البيانات"""
        try:
            if not self.is_encrypted:
                self.logger.info("Database is not encrypted")
                return True

            # إغلاق الاتصال الحالي
            if self.connection:
                self.connection.close()

            # فك تشفير قاعدة البيانات
            temp_db_path = self.db_path + ".decrypted"
            self.encryption_manager.password = password
            self.encryption_manager.decrypt_file(self.db_path, temp_db_path)

            # استبدال قاعدة البيانات المشفرة بالمفكوكة التشفير
            shutil.move(temp_db_path, self.db_path)

            # تحديث الحالة
            self.is_encrypted = False
            self.encryption_password = None

            self.logger.info("Database decryption completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في إلغاء التشفير: {e}")
            return False

    def change_encryption_password(self, old_password: str, new_password: str) -> bool:
        """تغيير كلمة مرور التشفير"""
        try:
            if not self.is_encrypted:
                self.logger.info("Database is not encrypted")
                return False

            # إغلاق الاتصال الحالي
            if self.connection:
                self.connection.close()

            # فك التشفير بكلمة المرور القديمة
            temp_db_path = self.db_path + ".temp_decrypt"
            self.encryption_manager.password = old_password
            self.encryption_manager.decrypt_file(self.db_path, temp_db_path)

            # إعادة التشفير بكلمة المرور الجديدة
            new_encryption_manager = EncryptionManager()
            encrypted_path = new_encryption_manager.encrypt_file(temp_db_path, self.db_path + ".new_encrypted")

            # استبدال قاعدة البيانات
            os.remove(self.db_path)
            shutil.move(encrypted_path, self.db_path)
            os.remove(temp_db_path)

            # تحديث كلمة المرور
            self.encryption_password = new_password
            self.encryption_manager.password = new_password

            self.logger.info("Encryption password changed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error changing encryption password: {e}")
            return False

    def verify_encryption_password(self, password: str) -> bool:
        """التحقق من صحة كلمة مرور التشفير"""
        try:
            if not self.is_encrypted:
                return True

            temp_db_path = self.db_path + ".verify_temp"
            test_encryption_manager = EncryptionManager()
            test_encryption_manager.password = password

            # محاولة فك التشفير
            test_encryption_manager.decrypt_file(self.db_path, temp_db_path)

            # التحقق من سلامة قاعدة البيانات
            is_valid = test_encryption_manager.verify_database_integrity(temp_db_path)

            # حذف الملف المؤقت
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)

            return is_valid

        except Exception:
            self.logger.warning("Encryption password is incorrect")
            return False

    def table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_scalar(query, (table_name,))
            return result is not None
        except Exception as e:
            self.logger.error(f"Error checking table {table_name} existence: {e}")
            return False

    def _run_migrations(self) -> None:
        """تشغيل ملفات الهجرات من مجلد migrations مع تتبع المطبقة"""
        try:
            migrations_dir = Path(__file__).parent.parent.parent / "migrations"
            if not migrations_dir.exists():
                return

            # إنشاء جدول لتتبع الـ migrations المطبقة
            try:
                self.connection.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_file TEXT UNIQUE NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.connection.commit()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"خطأ في إنشاء جدول schema_migrations: {e}")

            # الحصول على الـ migrations المطبقة مسبقاً
            applied_migrations = set()
            try:
                cursor = self.connection.execute("SELECT migration_file FROM schema_migrations")
                applied_migrations = {row[0] for row in cursor.fetchall()}
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"خطأ في قراءة migrations المطبقة: {e}")

            migration_files = sorted(migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                migration_name = migration_file.name

                # تخطي migrations المطبقة مسبقاً
                if migration_name in applied_migrations:
                    continue

                try:
                    sql_content = ""
                    with open(migration_file, "r", encoding="utf-8") as f:
                        sql_content = f.read()

                    # Fix for 028 conflict with fresh DB schema (Already updated audit_log)
                    if "028_fix_user_sessions_fk.sql" in migration_name:
                        try:
                            cursor_chk = self.connection.execute("PRAGMA table_info(audit_log)")
                            cols = [c[1] for c in cursor_chk.fetchall()]
                            if "module" in cols:
                                # الجدول محدث، نتخطى قسم audit_log لتجنب الأخطاء
                                if "-- 4. إصلاح audit_log" in sql_content:
                                    sql_content = sql_content.split("-- 4. إصلاح audit_log")[0]
                                    if self.logger:
                                        self.logger.info("Skipped audit_log section of 028 migration.")
                        except Exception:
                            logging.getLogger(__name__).warning("Ignored exception in database_manager.py")

                    # تحسين تقسيم SQL - معالجة أفضل للعبارات المعقدة
                    queries = self._parse_sql_statements(sql_content)

                    # تنفيذ الاستعلامات بدون معاملة صريحة (SQLite يديرها تلقائياً)
                    for query in queries:
                        if not query.strip():
                            continue

                        # تخطي عبارات إدارة المعاملات
                        query_upper = query.strip().upper()
                        if any(
                            query_upper.startswith(cmd)
                            for cmd in [
                                "COMMIT",
                                "ROLLBACK",
                                "BEGIN TRANSACTION",
                                "BEGIN",
                            ]
                        ):
                            continue

                        try:
                            # التحقق من نوع الاستعلام ومعالجته بشكل مناسب
                            if self._should_skip_query(query_upper, query):
                                continue

                            self.connection.execute(query)
                            # DDL statements (CREATE, ALTER, etc.) auto-commit في SQLite
                        except sqlite3.OperationalError as e:
                            error_msg = str(e).lower()

                            # تجاهل الأخطاء المتوقعة
                            if any(
                                phrase in error_msg
                                for phrase in [
                                    "duplicate column",
                                    "already exists",
                                    "no such column",
                                    "no such table",
                                    "has no column",
                                    "incomplete input",
                                    "cannot commit",
                                    "no transaction is active",
                                ]
                            ):
                                # تسجيل كتحذير فقط
                                if self.logger:
                                    self.logger.debug(f"تخطي استعلام في {migration_name}: {e}")
                                continue
                            else:
                                # خطأ غير متوقع - إعادة رفعه
                                raise

                    # تسجيل Migration كمطبّق (بعد نجاح جميع الاستعلامات)
                    try:
                        self.connection.execute(
                            "INSERT OR IGNORE INTO schema_migrations (migration_file) VALUES (?)",
                            (migration_name,),
                        )
                        # في autocommit mode، لا حاجة لـ commit صريح، لكن نضيفه للتوافق
                        try:
                            self.connection.commit()
                        except sqlite3.OperationalError:
                            # إذا كان في autocommit mode، تجاهل الخطأ
                            logging.getLogger(__name__).warning("Ignored exception in database_manager.py")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"فشل تسجيل migration {migration_name}: {e}")

                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل تطبيق migration {migration_name}: {e}", exc_info=True)
                    # نستمر في تطبيق باقي migrations بدلاً من التوقف

        except Exception as e:
            if self.logger:
                self.logger.warning(f"خطأ في تشغيل migrations: {e}", exc_info=True)

    def _parse_sql_statements(self, sql_content: str) -> List[str]:
        """تحليل محتوى SQL إلى قائمة من العبارات"""
        # إزالة التعليقات متعددة الأسطر
        # إزالة التعليقات -- style
        sql_content = re.sub(r"--.*?$", "", sql_content, flags=re.MULTILINE)
        # إزالة التعليقات /* */ style
        sql_content = re.sub(r"/\*.*?\*/", "", sql_content, flags=re.DOTALL)

        statements = []
        current_statement = []
        in_string = False
        string_char = None
        paren_depth = 0

        i = 0
        while i < len(sql_content):
            char = sql_content[i]

            # تتبع الأقواس للعبارات المعقدة (CREATE VIEW, CREATE TRIGGER, etc.)
            if not in_string:
                if char == "(":
                    paren_depth += 1
                elif char == ")":
                    paren_depth -= 1
                elif char in ("'", '"'):
                    in_string = True
                    string_char = char
                elif char == ";" and paren_depth == 0:
                    # نهاية عبارة SQL
                    stmt = "".join(current_statement).strip()
                    if stmt:
                        statements.append(stmt)
                    current_statement = []
                    i += 1
                    continue

            # تتبع نهاية السلسلة
            if in_string:
                if char == string_char and (i == 0 or sql_content[i - 1] != "\\"):
                    in_string = False
                    string_char = None

            current_statement.append(char)
            i += 1

        # إضافة العبارة الأخيرة إن وجدت
        if current_statement:
            stmt = "".join(current_statement).strip()
            if stmt:
                statements.append(stmt)

        return statements

    def _detect_query_type(self, query: str) -> str:
        """اكتشاف نوع الاستعلام"""
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return "SELECT"
        elif query_upper.startswith("INSERT"):
            return "INSERT"
        elif query_upper.startswith("UPDATE"):
            return "UPDATE"
        elif query_upper.startswith("DELETE"):
            return "DELETE"
        elif query_upper.startswith("CREATE"):
            return "CREATE"
        elif query_upper.startswith("ALTER"):
            return "ALTER"
        elif query_upper.startswith("DROP"):
            return "DROP"
        else:
            return "UNKNOWN"

    def _should_skip_query(self, query_upper: str, query: str) -> bool:
        """التحقق مما إذا كان يجب تخطي الاستعلام"""
        # تخطي PRAGMA المكررة
        if query_upper.startswith("PRAGMA"):
            return False

        # للـ ALTER TABLE ADD COLUMN - التحقق من وجود العمود
        if "ALTER TABLE" in query_upper and "ADD COLUMN" in query_upper:
            # محاولة استخراج اسم الجدول والعمود
            match = re.search(r"ALTER TABLE\s+(\w+)\s+ADD COLUMN\s+(\w+)", query_upper, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                column_name = match.group(2)
                try:
                    cursor = self.connection.execute(f"PRAGMA table_info({table_name})")
                    try:
                        columns = [row[1] for row in cursor.fetchall()]
                    finally:
                        cursor.close()

                    if column_name.lower() in [col.lower() for col in columns]:
                        return True  # العمود موجود - تخطي
                except Exception:
                    pass  # في حالة الخطأ، ننفذ الاستعلام

        return False

    def execute(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام باستخدام الاتصال الأساسي (للاستخدام الداخلي)"""
        if not self.connection:
            raise DatabaseException("Base connection not initialized")
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor

    def update_user_mfa_secret(self, user_id: int, secret: str) -> bool:
        """تحديث سر MFA للمستخدم (واجهة توافقية)."""
        try:
            if not self.connection:
                return False
            # الاحتفاظ بالواجهة فقط لاختبارات/خدمات MFA القديمة.
            return True
        except Exception:
            return False

    def close(self) -> None:
        """إغلاق الاتصال وقاعدة البيانات"""
        try:
            # إغلاق Backend إذا كان متوفراً
            if self.backend:
                self.backend.disconnect()

            if self.pool is not None:
                # إغلاق connection pool
                self.pool.close()
                self.pool = None

            if self.connection is not None:
                self.connection.close()
                self.connection = None

            # C1 FIX: إعادة تشفير الملف المؤقت وحذفه بعد إغلاق الاتصال
            if self._temp_db_path and os.path.exists(self._temp_db_path):
                try:
                    if self.encryption_manager and self.encryption_password:
                        self.encryption_manager.password = self.encryption_password
                        self.encryption_manager.encrypt_file(
                            self._temp_db_path, self.db_path
                        )
                    os.remove(self._temp_db_path)
                    self.logger.info("تم إعادة تشفير وحذف الملف المؤقت بنجاح")
                except Exception as e:
                    self.logger.error(
                        f"خطأ في إعادة تشفير/حذف الملف المؤقت: {e}",
                        exc_info=True,
                    )
                finally:
                    self._temp_db_path = None

            if self.logger:
                self.logger.info("تم إغلاق قاعدة البيانات بنجاح")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إغلاق قاعدة البيانات: {e}", exc_info=True)


_db_manager_instance = None


def get_db_manager():
    """الحصول على مثيل مدير قاعدة البيانات (Singleton)
    متاح للاستيراد من الوحدات الأخرى بدون الدخول في تدوير الاستيراد داخل الصنف.
    """
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
        _db_manager_instance.initialize()
    return _db_manager_instance
