#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير قاعدة البيانات - Database Manager
إدارة الاتصال بقاعدة البيانات والعمليات الأساسية
"""

import sqlite3
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from .encryption_manager import EncryptionManager
from .exceptions import DatabaseException
from src.database.connection_pool import ConnectionPool, PoolConfig
from src.core.encrypted_backup_service import EncryptedBackupService

class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        encryption_password: Optional[str] = None,
        pool_options: Optional[Dict[str, Any]] = None,
        backup_options: Optional[Dict[str, Any]] = None
    ):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.db_path = str(project_root / "data" / "logical_release.db")
        else:
            self.db_path = db_path
        
        self.connection = None
        self.pool: Optional[ConnectionPool] = None
        self.encryption_manager = None
        self.encryption_password = encryption_password
        self.is_encrypted = False
        self.encrypted_backup_service: Optional[EncryptedBackupService] = None
        self._pool_options = pool_options or {}
        self._backup_options = backup_options or {}
        
        self._ensure_data_directory()
        
        # التحقق من حالة التشفير
        if os.path.exists(self.db_path):
            self.encryption_manager = EncryptionManager()
            self.is_encrypted = self.encryption_manager.is_database_encrypted(self.db_path)
    
    def _ensure_data_directory(self):
        """التأكد من وجود مجلد البيانات"""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """تهيئة قاعدة البيانات"""
        try:
            # التعامل مع قاعدة البيانات المشفرة
            if self.is_encrypted and self.encryption_password:
                # فك تشفير قاعدة البيانات مؤقتاً للوصول إليها
                temp_db_path = self.db_path + ".temp"
                self.encryption_manager.password = self.encryption_password
                self.encryption_manager.decrypt_file(self.db_path, temp_db_path)
                
                # الاتصال بقاعدة البيانات المفكوكة التشفير
                self.connection = sqlite3.connect(
                    temp_db_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                
                # حذف الملف المؤقت بعد الاتصال
                os.remove(temp_db_path)
                
            else:
                # إنشاء الاتصال العادي
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30.0
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
            
            # إنشاء الفهارس
            self._create_indexes()
            
            # تشغيل الهجرات
            self._run_migrations()

            # تهيئة Connection Pool للاستخدام العام (تخطي الذاكرة)
            if self.pool is None:
                if self.db_path == ':memory:' or str(self.db_path).startswith('file::memory:'):
                    self.pool = None
                else:
                    enabled = self._pool_options.get('enabled', True)
                    if enabled:
                        cfg = PoolConfig(
                            pool_size=int(self._pool_options.get('pool_size', 10)),
                            max_overflow=int(self._pool_options.get('max_overflow', 20)),
                            timeout=float(self._pool_options.get('timeout', 30.0))
                        )
                        self.pool = ConnectionPool(self.db_path, cfg)

            # تهيئة خدمة النسخ الاحتياطي (مشفر عند التمكين)
            if self.encrypted_backup_service is None:
                backups_dir = str(self._backup_options.get('backup_dir', Path(self.db_path).parent / "backups"))
                max_b = int(self._backup_options.get('max_backups', 30))
                enc_enabled = bool(self._backup_options.get('encrypted', True))
                key_path = self._backup_options.get('encryption_key_path')
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
                    compress=True
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
                description TEXT,
                parent_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
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
                min_stock INTEGER DEFAULT 0,
                current_stock INTEGER DEFAULT 0,
                description TEXT,
                image_path TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # جدول الموردين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
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
        
        # جدول سجل العمليات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
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
        
        # جدول صلاحيات المستخدمين
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
        
        # جدول المدفوعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_type TEXT NOT NULL CHECK (payment_type IN ('customer_payment', 'supplier_payment', 'expense', 'other')),
                entity_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT NOT NULL CHECK (payment_method IN ('cash', 'check', 'bank_transfer', 'credit_card', 'debit_card')),
                reference_number TEXT,
                payment_date DATE DEFAULT CURRENT_DATE,
                status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'cancelled', 'failed')),
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

        self.connection.commit()
    
    def _create_indexes(self):
        """إنشاء الفهارس لتحسين الأداء"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
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
            # فهارس جداول المدفوعات
            "CREATE INDEX IF NOT EXISTS idx_payments_type ON payments(payment_type)",
            "CREATE INDEX IF NOT EXISTS idx_payments_entity ON payments(entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_account_balances_type_entity ON account_balances(account_type, entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_payment_schedules_entity ON payment_schedules(entity_id, entity_type)",
            "CREATE INDEX IF NOT EXISTS idx_payment_schedules_due_date ON payment_schedules(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_payment_schedules_status ON payment_schedules(status)"
            ,"CREATE INDEX IF NOT EXISTS idx_invoice_notes_sale ON invoice_notes(sale_id)"
            ,"CREATE INDEX IF NOT EXISTS idx_invoice_notes_created_by ON invoice_notes(created_by)"
            ,"CREATE INDEX IF NOT EXISTS idx_reminders_due_at ON reminders(due_at)"
            ,"CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)"
            ,"CREATE INDEX IF NOT EXISTS idx_reminders_customer ON reminders(customer_id)"
        ]
        
        for index_sql in indexes:
            self.connection.execute(index_sql)
        
        self.connection.commit()
    
    @contextmanager
    def get_cursor(self):
        """الحصول على cursor مع إدارة تلقائية للموارد (يدعم الـ Pool)."""
        # استخدام Pool إن توفر
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
    
    def execute_query(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام وإرجاع النتائج أو cursor للعمليات الأخرى"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
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
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """تنفيذ استعلام وإرجاع صف واحد"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Any]:
        """تنفيذ استعلام وإرجاع جميع الصفوف"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_non_query(self, query: str, params: Tuple = ()) -> int:
        """تنفيذ استعلام INSERT/UPDATE/DELETE وإرجاع عدد الصفوف المتأثرة"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if self.pool is None:
                self.connection.commit()
            else:
                cursor.connection.commit()
            return cursor.rowcount
    
    def execute_scalar(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام وإرجاع قيمة واحدة"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_last_insert_id(self) -> int:
        """الحصول على آخر ID تم إدراجه"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]
    
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
            print(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
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
            print(f"خطأ في النسخ الاحتياطي المشفر: {e}")
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
            print(f"خطأ في استعادة النسخة الاحتياطية: {e}")
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
            print(f"خطأ في استعادة النسخة الاحتياطية المشفرة: {e}")
            return False
    
    def cleanup_old_backups(self, max_backups: int = 30):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            backup_dir = Path(self.db_path).parent / "backups"
            if not backup_dir.exists():
                return
            
            backup_files = list(backup_dir.glob("backup_*.db"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # حذف النسخ الزائدة
            for backup_file in backup_files[max_backups:]:
                backup_file.unlink()
                
        except Exception as e:
            print(f"خطأ في تنظيف النسخ الاحتياطية: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """الحصول على معلومات قاعدة البيانات"""
        try:
            info = {}
            
            # حجم قاعدة البيانات
            if os.path.exists(self.db_path):
                info['size'] = os.path.getsize(self.db_path)
                info['size_mb'] = round(info['size'] / (1024 * 1024), 2)
            
            # عدد الجداول
            tables_query = "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            info['tables_count'] = self.execute_scalar(tables_query)
            
            # معلومات الجداول الرئيسية
            main_tables = ['products', 'categories', 'batches', 'sales', 'purchases', 'customers', 'suppliers']
            info['records'] = {}
            
            for table in main_tables:
                count_query = f"SELECT COUNT(*) FROM {table}"
                info['records'][table] = self.execute_scalar(count_query)
            
            return info
            
        except Exception as e:
            print(f"خطأ في الحصول على معلومات قاعدة البيانات: {e}")
            return {}
    
    def enable_encryption(self, password: str) -> bool:
        """تفعيل تشفير قاعدة البيانات"""
        try:
            if self.is_encrypted:
                print("قاعدة البيانات مشفرة بالفعل")
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
            
            print("تم تفعيل تشفير قاعدة البيانات بنجاح")
            return True
            
        except Exception as e:
            print(f"خطأ في تفعيل التشفير: {e}")
            return False
    
    def disable_encryption(self, password: str) -> bool:
        """إلغاء تشفير قاعدة البيانات"""
        try:
            if not self.is_encrypted:
                print("قاعدة البيانات غير مشفرة")
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
            
            print("تم إلغاء تشفير قاعدة البيانات بنجاح")
            return True
            
        except Exception as e:
            print(f"خطأ في إلغاء التشفير: {e}")
            return False
    
    def change_encryption_password(self, old_password: str, new_password: str) -> bool:
        """تغيير كلمة مرور التشفير"""
        try:
            if not self.is_encrypted:
                print("قاعدة البيانات غير مشفرة")
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
            
            print("تم تغيير كلمة مرور التشفير بنجاح")
            return True
            
        except Exception as e:
            print(f"خطأ في تغيير كلمة مرور التشفير: {e}")
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

        except Exception as e:
            print(f"كلمة مرور التشفير غير صحيحة: {e}")
            return False

    def table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_scalar(query, (table_name,))
            return result is not None
        except Exception as e:
            print(f"خطأ في التحقق من وجود الجدول {table_name}: {e}")
            return False
    
    def _run_migrations(self) -> None:
        """تشغيل ملفات الهجرات من مجلد migrations"""
        try:
            migrations_dir = Path(__file__).parent.parent.parent / "migrations"
            if not migrations_dir.exists():
                return
            migration_files = sorted(migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                try:
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    queries = [q.strip() for q in sql_content.split(';') if q.strip()]
                    for query in queries:
                        self.connection.execute(query)
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()
        except Exception as e:
            pass
    def execute(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام وإرجاع cursor"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.pool is not None:
            self.pool.close()
            self.pool = None