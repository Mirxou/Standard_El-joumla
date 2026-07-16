import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير قاعدة البيانات المحلية - Local Database Manager
إدارة قاعدة البيانات المحلية (Local Cache) للتطبيق المكتبي
"""

import os
import platform
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Register Decimal adapters for SQLite
sqlite3.register_adapter(Decimal, lambda d: str(d))
sqlite3.register_converter("DECIMAL", lambda s: Decimal(s.decode("utf-8")))


# Fix SQLite date/timestamp converters to handle ISO format with 'T' or space
def parse_date(b):
    s = b.decode("utf-8")
    return date.fromisoformat(s[:10])


def parse_timestamp(b):
    s = b.decode("utf-8")
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S") if " " in s else datetime.fromisoformat(s)


sqlite3.register_converter("DATE", parse_date)
sqlite3.register_converter("TIMESTAMP", parse_timestamp)


from src.core.database_encryption import DatabaseEncryption
from src.core.exceptions import DatabaseException
from src.core.keyring_manager import KeyringManager
from src.utils.logger import setup_logger


class LocalDatabaseManager:
    """مدير قاعدة البيانات المحلية (Local Cache)"""

    def __init__(self, db_path: Optional[str] = None, encryption_password: Optional[str] = None):
        """
        تهيئة مدير قاعدة البيانات المحلية

        Args:
            db_path: مسار قاعدة البيانات (اختياري - سيتم تحديده تلقائياً)
            encryption_password: كلمة مرور التشفير (اختياري - سيتم الحصول عليها من Keyring)
        """
        self.logger = setup_logger(__name__)

        # تهيئة Keyring Manager و Database Encryption
        self.keyring_manager = KeyringManager()
        self.db_encryption = DatabaseEncryption(self.keyring_manager)

        # تحديد مسار قاعدة البيانات المحلية
        if db_path is None:
            self.db_path = self._get_local_db_path()
        else:
            self.db_path = db_path

        self.encryption_password = encryption_password
        self.connection: Optional[sqlite3.Connection] = None
        self._ensure_data_directory()

    def _get_local_db_path(self) -> str:
        """
        الحصول على مسار قاعدة البيانات المحلية حسب نظام التشغيل

        Returns:
            مسار قاعدة البيانات المحلية
        """
        system = platform.system()

        if system == "Windows":
            # Windows: %APPDATA%/LogicalERP/local_cache.db
            appdata = os.getenv("APPDATA")
            if appdata:
                db_dir = Path(appdata) / "LogicalERP"
            else:
                # Fallback إلى مجلد المستخدم
                home = Path.home()
                db_dir = home / "AppData" / "Roaming" / "LogicalERP"
        elif system == "Darwin":  # macOS
            # macOS: ~/Library/Application Support/LogicalERP/local_cache.db
            home = Path.home()
            db_dir = home / "Library" / "Application Support" / "LogicalERP"
        else:  # Linux
            # Linux: ~/.local/share/logical_erp/local_cache.db
            home = Path.home()
            db_dir = home / ".local" / "share" / "logical_erp"

        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / "local_cache.db")

    def _ensure_data_directory(self):
        """التأكد من وجود مجلد قاعدة البيانات"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> bool:
        """
        تهيئة قاعدة البيانات المحلية

        Returns:
            True إذا نجحت التهيئة، False خلاف ذلك
        """
        try:
            # إنشاء الاتصال (مشفر إذا كان SQLCipher متوفر)
            if self.db_encryption.is_available():
                # استخدام SQLCipher
                password = self.encryption_password or self.db_encryption.get_encryption_password()
                self.connection = self.db_encryption.create_encrypted_connection(self.db_path, password)
                self.logger.info("✅ تم الاتصال بقاعدة البيانات المشفرة")
            else:
                # استخدام SQLite العادي
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=60.0,
                    detect_types=sqlite3.PARSE_DECLTYPES,
                )
                self.logger.warning("⚠️ SQLCipher غير متوفر - قاعدة البيانات غير مشفرة")

            # تفعيل WAL Mode للأداء والموثوقية (ACID Compliance)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=MEMORY")

            # تفعيل المفاتيح الخارجية
            self.connection.execute("PRAGMA foreign_keys=ON")

            # إنشاء الجداول
            self._create_tables()

            # إنشاء الفهارس
            self._create_indexes()

            # تطبيق Migrations
            from src.core.local_migrations.migration_manager import (
                LocalMigrationManager,
            )

            migration_manager = LocalMigrationManager(self)
            migration_manager.initialize()
            migration_manager.apply_all_pending()

            self.logger.info(f"✅ تم تهيئة قاعدة البيانات المحلية: {self.db_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ فشل تهيئة قاعدة البيانات المحلية: {str(e)}")
            raise DatabaseException(f"فشل تهيئة قاعدة البيانات المحلية: {str(e)}")

    def create_thread_connection(self, timeout: float = 30.0, read_only: bool = False) -> sqlite3.Connection:
        """إنشاء اتصال آمن للخيوط باستخدام LocalDatabaseManager"""
        if self.db_encryption.is_available():
            password = self.encryption_password or self.db_encryption.get_encryption_password()
            conn = self.db_encryption.create_encrypted_connection(self.db_path, password)
        else:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=timeout,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )

        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        if read_only:
            conn.execute("PRAGMA query_only=true")
        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Alias for legacy modules expecting get_connection()"""
        if not self.connection:
            self.initialize()
        return self.connection

    def _create_tables(self):
        """إنشاء جداول قاعدة البيانات المحلية"""

        # جدول sync_queue - لتتبع العمليات المعلقة
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                operation TEXT NOT NULL,  -- 'create', 'update', 'delete'
                data TEXT,  -- JSON data
                retry_count INTEGER DEFAULT 0,
                last_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(table_name, record_id, operation)
            )
        """)

        # جدول sync_status - حالة المزامنة العامة
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                device_id TEXT,
                server_url TEXT,
                is_online BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول products - نسخة محلية من المنتجات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
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
                tax_rate DECIMAL(5,2) DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                current_stock INTEGER DEFAULT 0,
                description TEXT,
                image_path TEXT,
                is_perishable BOOLEAN DEFAULT 0,
                expiry_date DATE,
                batch_number TEXT,
                abc_classification TEXT,
                ai_forecast_demand REAL,
                last_analysis_date DATETIME,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,  -- 0 = غير متزامن، 1 = متزامن
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,  -- Soft Delete
                deleted_at TIMESTAMP,
                parent_product_id INTEGER DEFAULT NULL,
                conversion_factor INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_product_id) REFERENCES products(id)
            )
        """)

        # جدول chart_of_accounts - شجرة الحسابات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS chart_of_accounts (
                id INTEGER PRIMARY KEY,
                account_code TEXT UNIQUE,
                account_name TEXT NOT NULL,
                account_type TEXT,
                sub_type TEXT,
                description TEXT,
                normal_side TEXT,
                is_header BOOLEAN DEFAULT 0,
                parent_account_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                is_locked BOOLEAN DEFAULT 0,
                opening_balance DECIMAL(15,2) DEFAULT 0,
                current_balance DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول general_journal - رؤوس قيود اليومية
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS general_journal (
                id INTEGER PRIMARY KEY,
                entry_number TEXT UNIQUE,
                entry_date DATE NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                description TEXT,
                notes TEXT,
                is_posted BOOLEAN DEFAULT 0,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول journal_lines - تفاصيل قيود اليومية
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS journal_lines (
                id INTEGER PRIMARY KEY,
                journal_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                account_code TEXT,
                account_name TEXT,
                description TEXT,
                debit_amount DECIMAL(15,2) DEFAULT 0,
                credit_amount DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (journal_id) REFERENCES general_journal(id),
                FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id)
            )
        """)

        # جدول journal_entries - قيود اليومية
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                reference_id INTEGER,
                reference_type TEXT,
                amount DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول webhooks - لدعم التنبيهات الخارجية
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                event_type TEXT NOT NULL,
                secret TEXT,
                is_active BOOLEAN DEFAULT 1,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول warehouses - المستودعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                name_en TEXT,
                address TEXT,
                city TEXT,
                country TEXT DEFAULT 'الجزائر',
                phone TEXT,
                email TEXT,
                manager_name TEXT,
                manager_phone TEXT,
                warehouse_type TEXT DEFAULT 'main',
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                capacity REAL DEFAULT 0.0,
                current_utilization REAL DEFAULT 0.0,
                allow_negative_stock BOOLEAN DEFAULT 0,
                notes TEXT,
                created_by INTEGER,
                updated_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول stock_movements - حركات المخزون
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                movement_type TEXT NOT NULL, -- in, out, adjustment, transfer
                quantity REAL NOT NULL,
                reference_id INTEGER,
                reference_type TEXT,
                notes TEXT,
                user_id INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        """)

        # جدول warehouse_inventory - مخزون المنتجات في المستودعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS warehouse_inventory (
                id INTEGER PRIMARY KEY,
                warehouse_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity REAL DEFAULT 0.0,
                reserved_quantity REAL DEFAULT 0.0,
                min_stock REAL DEFAULT 0.0,
                last_stock_take DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(warehouse_id, product_id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # التأكد من وجود مستودع افتراضي واحد على الأقل
        self.connection.execute("""
            INSERT OR IGNORE INTO warehouses (id, name, is_default, is_active)
            VALUES (1, 'المستودع الرئيسي', 1, 1)
        """)

        # جدول customers - نسخة محلية من العملاء
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                credit_limit DECIMAL(10,2) DEFAULT 0,
                current_balance DECIMAL(10,2) DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول sales - نسخة محلية من المبيعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                total_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                final_amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT DEFAULT 'نقدي',
                status TEXT DEFAULT 'confirmed',
                paid_amount DECIMAL(10,2) DEFAULT 0,
                remaining_amount DECIMAL(10,2) DEFAULT 0,
                sale_date DATE DEFAULT CURRENT_DATE,
                due_date DATE,
                user_id INTEGER,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول sale_items - نسخة محلية من عناصر المبيعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                cost_price DECIMAL(10,2) NOT NULL,
                profit DECIMAL(10,2) NOT NULL,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # جدول batches - نسخة محلية من الدفعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                batch_number TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                cost_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2),
                expiry_date DATE,
                purchase_date DATE DEFAULT CURRENT_DATE,
                supplier_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # جدول categories - نسخة محلية من الفئات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_en TEXT,
                description TEXT,
                parent_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
            )
        """)

        # جدول users - نسخة محلية من المستخدمين
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

        # جدول suppliers - نسخة محلية من الموردين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                phone2 TEXT,
                email TEXT,
                address TEXT,
                tax_number TEXT,
                name_en TEXT,
                website TEXT,
                city TEXT,
                country TEXT DEFAULT 'الجزائر',
                commercial_register TEXT,
                payment_terms TEXT DEFAULT 'نقدي',
                credit_limit DECIMAL(10,2) DEFAULT 0,
                current_balance DECIMAL(10,2) DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول purchases - نسخة محلية من المشتريات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                supplier_invoice_number TEXT,
                supplier_id INTEGER,
                purchase_date DATE DEFAULT CURRENT_DATE,
                expected_delivery_date DATE,
                received_date DATE,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'unpaid',
                payment_terms TEXT DEFAULT 'نقدي',
                subtotal_amount DECIMAL(10,2) DEFAULT 0,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                tax_amount DECIMAL(10,2) DEFAULT 0,
                shipping_cost DECIMAL(10,2) DEFAULT 0,
                total_amount DECIMAL(10,2) NOT NULL,
                paid_amount DECIMAL(10,2) DEFAULT 0,
                remaining_amount DECIMAL(10,2) DEFAULT 0,
                currency_id INTEGER,
                exchange_rate DECIMAL(10,4) DEFAULT 1.0,
                base_amount DECIMAL(10,2),
                converted_amount DECIMAL(10,2),
                user_id INTEGER,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # جدول purchase_items - نسخة محلية من عناصر المشتريات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity_ordered DECIMAL(10,2) NOT NULL,
                quantity_received DECIMAL(10,2) DEFAULT 0,
                unit_cost DECIMAL(10,2) NOT NULL,
                discount_percent DECIMAL(5,2) DEFAULT 0,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                tax_percent DECIMAL(5,2) DEFAULT 19,
                tax_amount DECIMAL(10,2) DEFAULT 0,
                total_amount DECIMAL(10,2) NOT NULL,
                expiry_date DATE,
                batch_number TEXT,
                notes TEXT,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # جدول stock_movements - نسخة محلية من حركات المخزون
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_id INTEGER,
                reference_type TEXT,
                notes TEXT,
                user_id INTEGER,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # جدول users - المستخدمين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                otp_secret TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # إضافة مستخدم افتراضي
        self.connection.execute("""
            INSERT OR IGNORE INTO users (id, username, password_hash, full_name, role)
            VALUES (1, 'admin', 'admin', 'Administrator', 'admin')
        """)

        # جدول categories - التصنيفات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول suppliers - الموردين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول reminders - التذكيرات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                due_date DATETIME,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول security_settings - إعدادات الأمان
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS security_settings (
                id INTEGER PRIMARY KEY,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول عروض الأسعار (Quotes)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT,
                customer_phone TEXT,
                customer_email TEXT,
                customer_address TEXT,
                quote_date DATE,
                valid_until DATE,
                sent_date DATE,
                response_date DATE,
                status TEXT DEFAULT 'draft',
                subtotal DECIMAL(15,2) DEFAULT 0,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                discount_percentage DECIMAL(15,2) DEFAULT 0,
                tax_amount DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) DEFAULT 0,
                payment_terms TEXT,
                delivery_terms TEXT,
                notes TEXT,
                internal_notes TEXT,
                terms_and_conditions TEXT,
                converted_to_sale_id INTEGER,
                converted_date DATE,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول أوامر الشراء (Purchase Orders)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER,
                supplier_name TEXT,
                supplier_contact TEXT,
                order_date DATE,
                required_date DATE,
                delivery_date DATE,
                expected_delivery_date DATE,
                status TEXT DEFAULT 'draft',
                priority TEXT DEFAULT 'normal',
                delivery_terms TEXT,
                payment_terms TEXT,
                currency TEXT DEFAULT 'DZD',
                subtotal DECIMAL(15,2) DEFAULT 0,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                tax_amount DECIMAL(15,2) DEFAULT 0,
                shipping_cost DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) DEFAULT 0,
                notes TEXT,
                terms_conditions TEXT,
                shipping_address TEXT,
                billing_address TEXT,
                approved_by INTEGER,
                approval_date DATE,
                sent_date DATE,
                confirmed_date DATE,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول عناصر أوامر الشراء (Purchase Order Items)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT,
                product_code TEXT,
                quantity_ordered DECIMAL(15,2) NOT NULL,
                quantity_received DECIMAL(15,2) DEFAULT 0,
                quantity_pending DECIMAL(15,2) DEFAULT 0,
                unit_price DECIMAL(15,2) NOT NULL,
                discount_percent DECIMAL(15,2) DEFAULT 0,
                tax_percent DECIMAL(15,2) DEFAULT 15,
                subtotal DECIMAL(15,2) NOT NULL,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                tax_amount DECIMAL(15,2) DEFAULT 0,
                net_amount DECIMAL(15,2) NOT NULL,
                required_date DATE,
                expected_delivery_date DATE,
                actual_delivery_date DATE,
                specifications TEXT,
                quality_requirements TEXT,
                packaging_requirements TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE
            )
        """)

        # جدول عناصر عروض الأسعار (Quote Items)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS quote_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT,
                product_barcode TEXT,
                description TEXT,
                quantity DECIMAL(15,2) NOT NULL,
                unit_price DECIMAL(15,2) NOT NULL,
                discount_amount DECIMAL(15,2) DEFAULT 0,
                discount_percentage DECIMAL(15,2) DEFAULT 0,
                tax_amount DECIMAL(15,2) DEFAULT 0,
                tax_percentage DECIMAL(15,2) DEFAULT 0,
                total_amount DECIMAL(15,2) NOT NULL,
                notes TEXT,
                FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE
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

        # جدول أرصدة الحسابات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS account_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                account_code TEXT NOT NULL,
                account_name TEXT NOT NULL,
                account_type TEXT NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense', 'receivable', 'payable')),
                entity_id INTEGER,
                balance DECIMAL(15,2) NOT NULL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id)
            )
        """)

        # جدول المدفوعات (Payments)
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

        # تهيئة sync_status
        self.connection.execute("""
            INSERT OR IGNORE INTO sync_status (id, last_synced_at, sync_version)
            VALUES (1, NULL, 1)
        """)

        self.connection.commit()

    def _create_indexes(self):
        """إنشاء الفهارس لتحسين الأداء"""

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_synced ON products(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_products_deleted ON products(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_customers_synced ON customers(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_customers_deleted ON customers(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_sales_synced ON sales(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_sales_deleted ON sales(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_synced ON sale_items(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_batches_synced ON batches(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_batches_deleted ON batches(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_sync_queue_table_record ON sync_queue(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_sync_queue_retry ON sync_queue(retry_count, last_retry_at)",
        ]

        for index_sql in indexes:
            try:
                self.connection.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"فشل إنشاء الفهرس: {index_sql} - {str(e)}")

        self.connection.commit()

    @contextmanager
    def transaction(self, timeout: int = 5):
        """
        Context manager للعمليات داخل Transaction مع Row-level Locking

        Args:
            timeout: مهلة الانتظار على Lock بالثواني (افتراضي: 5)
        """
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")

        try:
            # تعيين timeout للانتظار على Lock
            self.connection.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
            self.connection.execute("BEGIN IMMEDIATE")  # BEGIN IMMEDIATE للحصول على Lock فوراً
            yield
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise DatabaseException(f"فشل Transaction: {str(e)}")

    def lock_row(self, table_name: str, record_id: int) -> bool:
        """
        قفل صف معين (Row-level Locking)

        Args:
            table_name: اسم الجدول
            record_id: معرف السجل

        Returns:
            True إذا نجح القفل
        """
        try:
            # استخدام SELECT ... FOR UPDATE لـ Row-level Locking
            self.connection.execute(f"SELECT * FROM {table_name} WHERE id = ? FOR UPDATE", (record_id,))
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ فشل قفل الصف: {table_name}.{record_id} - {str(e)}")
            return False

    def execute_query(self, query: str, params: Tuple = (), exclude_deleted: bool = True) -> List[Dict[str, Any]]:
        """
        تنفيذ استعلام SELECT

        Args:
            query: استعلام SQL (يجب أن يكون parameterized)
            params: معاملات الاستعلام
            exclude_deleted: استبعاد السجلات المحذوفة منطقياً (افتراضي: True)

        Returns:
            قائمة من النتائج كـ dictionaries
        """
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")

        try:
            # التحقق من وجود is_deleted في الاستعلام
            query_upper = query.upper().strip()
            is_select = query_upper.startswith("SELECT")

            # 🔥 تحسين: إضافة فلتر is_deleted فقط إذا كان الاستعلام بسيطاً ولا يحتوي على JOIN
            # وإذا كان الجدول يحتوي فعلاً على هذا العمود (لتجنب الأخطاء)
            if exclude_deleted and is_select and "is_deleted" not in query_upper and "JOIN" not in query_upper:
                # محاولة استخراج اسم الجدول من الاستعلام
                import re

                table_match = re.search(r"FROM\s+([a-zA-Z0-9_]+)", query_upper)
                if table_match:
                    table_name = table_match.group(1).lower()
                    # التحقق من وجود العمود في الجدول لتجنب OperationalError
                    if self.table_exists(table_name):
                        cols = self.connection.execute(f"PRAGMA table_info({table_name})").fetchall()
                        has_deleted_col = any(c[1] == "is_deleted" for c in cols)

                        if has_deleted_col:
                            # Use query_upper WITHOUT strip() to find positions correctly in the original query
                            query_upper_full = query.upper()
                            if "WHERE" in query_upper_full:
                                where_pos = query_upper_full.find("WHERE") + 5
                                query = query[:where_pos] + f" {table_name}.is_deleted = 0 AND " + query[where_pos:]
                            elif "GROUP BY" in query_upper_full:
                                gb_pos = query_upper_full.find("GROUP BY")
                                query = query[:gb_pos] + f" WHERE {table_name}.is_deleted = 0 " + query[gb_pos:]
                            elif "ORDER BY" in query_upper_full:
                                ob_pos = query_upper_full.find("ORDER BY")
                                query = query[:ob_pos] + f" WHERE {table_name}.is_deleted = 0 " + query[ob_pos:]
                            elif "LIMIT" in query_upper_full:
                                l_pos = query_upper_full.find("LIMIT")
                                query = query[:l_pos] + f" WHERE {table_name}.is_deleted = 0 " + query[l_pos:]
                            else:
                                query += f" WHERE {table_name}.is_deleted = 0"

            from enum import Enum

            converted_params = tuple(p.name if isinstance(p, Enum) else p for p in params) if params else ()

            cursor = self.connection.execute(query, converted_params)

            # 🔥 Robustness Fix: If this is a write operation, commit it
            # Some legacy services use execute_query for INSERT/UPDATE/DELETE
            query_trimmed = query_upper.strip()
            if any(
                query_trimmed.startswith(word)
                for word in [
                    "INSERT",
                    "UPDATE",
                    "DELETE",
                    "ALTER",
                    "CREATE",
                    "DROP",
                    "REPLACE",
                ]
            ):
                self.connection.commit()
                return cursor  # Return cursor for write operations to allow accessing lastrowid

            if cursor.description is None:
                return []

            class DictRow(dict):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self._values = list(self.values())

                def __getitem__(self, key):
                    if isinstance(key, int):
                        return self._values[key]
                    return super().__getitem__(key)

            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(DictRow(zip(columns, row)))
            return results
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def get_connection(self):  # noqa: F811
        """الحصول على كائن الاتصال المباشر (للتوافق)"""
        return self.connection

    def get_last_insert_id(self) -> int:
        """الحصول على معرف آخر صف تم إدراجه"""
        if not self.connection:
            return 0
        cursor = self.connection.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """تنفيذ استعلام إدراج وإرجاع المعرف الجديد"""
        cursor = self.execute_query(query, params)
        if hasattr(cursor, "lastrowid"):
            return cursor.lastrowid
        return self.get_last_insert_id()

    def execute(self, query: str, params: Tuple = ()):
        """تنفيذ استعلام SQL مباشر"""
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")

        try:
            cursor = self.connection.execute(query, params)

            # 🔥 Robustness Fix: Auto-commit for write operations
            query_upper = query.strip().upper()
            if any(
                query_upper.startswith(word)
                for word in [
                    "INSERT",
                    "UPDATE",
                    "DELETE",
                    "ALTER",
                    "CREATE",
                    "DROP",
                    "REPLACE",
                ]
            ):
                self.connection.commit()

            return cursor
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def execute_non_query(self, query: str, params: Tuple = ()) -> int:
        """
        تنفيذ استعلام غير SELECT (INSERT, UPDATE, DELETE)

        Args:
            query: استعلام SQL (يجب أن يكون parameterized)
            params: معاملات الاستعلام

        Returns:
            عدد الصفوف المتأثرة
        """
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")

        try:
            cursor = self.connection.execute(query, params)
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def get_last_synced_at(self) -> Optional[datetime]:
        """الحصول على آخر وقت مزامنة"""
        results = self.execute_query("SELECT last_synced_at FROM sync_status WHERE id = 1")
        if results and results[0].get("last_synced_at"):
            return datetime.fromisoformat(results[0]["last_synced_at"])
        return None

    def set_last_synced_at(self, timestamp: datetime):
        """تعيين آخر وقت مزامنة"""
        self.execute_non_query(
            "UPDATE sync_status SET last_synced_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (timestamp.isoformat(),),
        )

    def soft_delete(self, table_name: str, record_id: int) -> bool:
        """
        حذف منطقي (Soft Delete) لسجل

        Args:
            table_name: اسم الجدول
            record_id: معرف السجل

        Returns:
            True إذا نجح الحذف
        """
        try:
            self.execute_non_query(
                """
                UPDATE {table_name}
                SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP, is_synced = 0
                WHERE id = ?
                """,
                (record_id,),
            )
            self.logger.info(f"✅ تم حذف السجل منطقياً: {table_name}.{record_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل الحذف المنطقي: {str(e)}")
            return False

    def restore_deleted(self, table_name: str, record_id: int) -> bool:
        """
        استعادة سجل محذوف منطقياً

        Args:
            table_name: اسم الجدول
            record_id: معرف السجل

        Returns:
            True إذا نجحت الاستعادة
        """
        try:
            self.execute_non_query(
                """
                UPDATE {table_name}
                SET is_deleted = 0, deleted_at = NULL, is_synced = 0
                WHERE id = ?
                """,
                (record_id,),
            )
            self.logger.info(f"✅ تم استعادة السجل: {table_name}.{record_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل استعادة السجل: {str(e)}")
            return False

    def get_pending_items(
        self, table_name: Optional[str] = None, include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        الحصول على العناصر المعلقة (غير المتزامنة)

        Args:
            table_name: اسم الجدول (اختياري - للحصول على جميع الجداول)

        Returns:
            قائمة بالعناصر المعلقة
        """
        if table_name:
            query = """
                SELECT * FROM {table_name}
                WHERE is_synced = 0 AND is_deleted = 0
                ORDER BY created_at ASC
            """
            return self.execute_query(query)
        else:
            # الحصول على جميع العناصر المعلقة من جميع الجداول
            tables = [
                "products",
                "customers",
                "sales",
                "sale_items",
                "batches",
                "categories",
                "suppliers",
            ]
            all_pending = []
            for table in tables:
                query = """
                    SELECT *, '{table}' as source_table FROM {table}
                    WHERE is_synced = 0 AND is_deleted = 0
                """
                all_pending.extend(self.execute_query(query))
            return all_pending

    def mark_as_synced(self, table_name: str, record_id: int, sync_version: int = 1):
        """
        تعليم سجل كمتزامن

        Args:
            table_name: اسم الجدول
            record_id: معرف السجل
            sync_version: إصدار المزامنة
        """
        self.execute_non_query(
            """
            UPDATE {table_name}
            SET is_synced = 1, last_synced_at = CURRENT_TIMESTAMP, sync_version = ?
            WHERE id = ?
            """,
            (sync_version, record_id),
        )

    def execute_scalar(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام وإرجاع قيمة واحدة"""
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")

        try:
            cursor = self.connection.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_scalar(query, (table_name,))
            return result is not None
        except Exception as e:
            self.logger.error(f"Error checking table {table_name} existence: {e}")
            return False

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """تنفيذ استعلام وإرجاع صف واحد"""
        results = self.execute_query(query, params)
        return results[0] if results else None

    def get_last_insert_id(self) -> int:  # noqa: F811
        """الحصول على آخر ID تم إدراجه"""
        result = self.execute_scalar("SELECT last_insert_rowid()")
        return result if result else 0

    # ========== Compatibility Aliases ==========
    # هذه الدوال تضمن التوافق مع الخدمات التي تستدعي أسماء مختلفة

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Alias لـ execute_non_query - للتوافق مع الخدمات القديمة"""
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")
        try:
            from enum import Enum

            converted_params = tuple(p.name if isinstance(p, Enum) else p for p in params) if params else ()
            cursor = self.connection.execute(query, converted_params)
            self.connection.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def execute_insert(self, query: str, params: Tuple = ()) -> int:  # noqa: F811
        """تنفيذ INSERT وإرجاع الـ ID الجديد"""
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")
        try:
            from enum import Enum

            converted_params = tuple(p.name if isinstance(p, Enum) else p for p in params) if params else ()
            cursor = self.connection.execute(query, converted_params)
            self.connection.commit()
            return cursor.lastrowid if cursor.lastrowid else 0
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Alias لـ execute_query - للتوافق مع الخدمات القديمة"""
        return self.execute_query(query, params)

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("تم إغلاق قاعدة البيانات المحلية")
