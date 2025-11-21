"""
نظام إدارة الصلاحيات والأدوار المتقدم
Advanced Roles & Permissions Management System

يوفر نظام شامل لإدارة المستخدمين والصلاحيات مع تدقيق كامل
Provides comprehensive user and permission management with full audit trail
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from enum import Enum
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)


class Permission(Enum):
    """الصلاحيات المتاحة في النظام"""
    
    # صلاحيات المبيعات
    SALES_VIEW = "sales.view"
    SALES_CREATE = "sales.create"
    SALES_EDIT = "sales.edit"
    SALES_DELETE = "sales.delete"
    SALES_APPROVE = "sales.approve"
    SALES_VOID = "sales.void"
    
    # صلاحيات المنتجات
    PRODUCTS_VIEW = "products.view"
    PRODUCTS_CREATE = "products.create"
    PRODUCTS_EDIT = "products.edit"
    PRODUCTS_DELETE = "products.delete"
    PRODUCTS_ADJUST_STOCK = "products.adjust_stock"
    PRODUCTS_ADJUST_PRICE = "products.adjust_price"
    
    # صلاحيات العملاء
    CUSTOMERS_VIEW = "customers.view"
    CUSTOMERS_CREATE = "customers.create"
    CUSTOMERS_EDIT = "customers.edit"
    CUSTOMERS_DELETE = "customers.delete"
    CUSTOMERS_VIEW_BALANCE = "customers.view_balance"
    CUSTOMERS_ADJUST_BALANCE = "customers.adjust_balance"
    
    # صلاحيات الموردين
    SUPPLIERS_VIEW = "suppliers.view"
    SUPPLIERS_CREATE = "suppliers.create"
    SUPPLIERS_EDIT = "suppliers.edit"
    SUPPLIERS_DELETE = "suppliers.delete"
    
    # صلاحيات المشتريات
    PURCHASES_VIEW = "purchases.view"
    PURCHASES_CREATE = "purchases.create"
    PURCHASES_EDIT = "purchases.edit"
    PURCHASES_DELETE = "purchases.delete"
    PURCHASES_APPROVE = "purchases.approve"
    
    # صلاحيات المحاسبة
    ACCOUNTING_VIEW = "accounting.view"
    ACCOUNTING_CREATE_JOURNAL = "accounting.create_journal"
    ACCOUNTING_EDIT_JOURNAL = "accounting.edit_journal"
    ACCOUNTING_DELETE_JOURNAL = "accounting.delete_journal"
    ACCOUNTING_CLOSE_PERIOD = "accounting.close_period"
    ACCOUNTING_VIEW_REPORTS = "accounting.view_reports"
    
    # صلاحيات التقارير
    REPORTS_SALES = "reports.sales"
    REPORTS_INVENTORY = "reports.inventory"
    REPORTS_FINANCIAL = "reports.financial"
    REPORTS_ACCOUNTING = "reports.accounting"
    REPORTS_EXPORT = "reports.export"
    
    # صلاحيات النظام
    SYSTEM_SETTINGS = "system.settings"
    SYSTEM_USERS = "system.users"
    SYSTEM_ROLES = "system.roles"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_AUDIT = "system.audit"
    
    # صلاحيات عروض الأسعار
    QUOTES_VIEW = "quotes.view"
    QUOTES_CREATE = "quotes.create"
    QUOTES_EDIT = "quotes.edit"
    QUOTES_DELETE = "quotes.delete"
    QUOTES_CONVERT = "quotes.convert"
    
    # صلاحيات المرتجعات
    RETURNS_VIEW = "returns.view"
    RETURNS_CREATE = "returns.create"
    RETURNS_APPROVE = "returns.approve"
    
    # صلاحيات خطط الدفع
    PAYMENT_PLANS_VIEW = "payment_plans.view"
    PAYMENT_PLANS_CREATE = "payment_plans.create"
    PAYMENT_PLANS_EDIT = "payment_plans.edit"
    PAYMENT_PLANS_DELETE = "payment_plans.delete"
    
    # صلاحيات الجرد
    CYCLE_COUNT_VIEW = "cycle_count.view"
    CYCLE_COUNT_CREATE = "cycle_count.create"
    CYCLE_COUNT_EXECUTE = "cycle_count.execute"
    CYCLE_COUNT_APPROVE = "cycle_count.approve"


class Role:
    """دور مستخدم مع صلاحيات محددة"""
    
    def __init__(
        self,
        role_id: Optional[int] = None,
        name: str = "",
        description: str = "",
        permissions: Optional[Set[str]] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None
    ):
        self.role_id = role_id
        self.name = name
        self.description = description
        self.permissions = permissions or set()
        self.is_active = is_active
        self.created_at = created_at or datetime.now()
        
    def has_permission(self, permission: str) -> bool:
        """التحقق من وجود صلاحية"""
        return permission in self.permissions
        
    def add_permission(self, permission: str):
        """إضافة صلاحية"""
        self.permissions.add(permission)
        
    def remove_permission(self, permission: str):
        """إزالة صلاحية"""
        self.permissions.discard(permission)
        
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'role_id': self.role_id,
            'name': self.name,
            'description': self.description,
            'permissions': list(self.permissions),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User:
    """مستخدم النظام"""
    
    def __init__(
        self,
        user_id: Optional[int] = None,
        username: str = "",
        email: str = "",
        full_name: str = "",
        role_id: Optional[int] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        last_login: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role_id = role_id
        self.is_active = is_active
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
        
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role_id': self.role_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class PermissionManager:
    """
    مدير الصلاحيات والأدوار
    
    يوفر:
    - إنشاء وإدارة الأدوار
    - تعيين الصلاحيات للأدوار
    - التحقق من صلاحيات المستخدمين
    - أدوار افتراضية جاهزة
    """
    
    def __init__(self, db_manager):
        """
        تهيئة مدير الصلاحيات
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self._create_tables()
        self._initialize_default_roles()
        
    def _create_tables(self):
        """إنشاء جداول الصلاحيات"""
        
        # جدول الأدوار
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                permissions TEXT NOT NULL,  -- JSON array
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول المستخدمين
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                full_name TEXT NOT NULL,
                role_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles(role_id)
            )
        """)
        
        # فهارس
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)")
        
    def _initialize_default_roles(self):
        """تهيئة الأدوار الافتراضية"""
        
        default_roles = [
            {
                'name': 'Admin',
                'description': 'مدير النظام - صلاحيات كاملة',
                'permissions': [p.value for p in Permission]  # كل الصلاحيات
            },
            {
                'name': 'Accountant',
                'description': 'محاسب - صلاحيات محاسبية كاملة',
                'permissions': [
                    Permission.ACCOUNTING_VIEW.value,
                    Permission.ACCOUNTING_CREATE_JOURNAL.value,
                    Permission.ACCOUNTING_EDIT_JOURNAL.value,
                    Permission.ACCOUNTING_VIEW_REPORTS.value,
                    Permission.REPORTS_FINANCIAL.value,
                    Permission.REPORTS_ACCOUNTING.value,
                    Permission.SALES_VIEW.value,
                    Permission.PURCHASES_VIEW.value,
                ]
            },
            {
                'name': 'Sales Manager',
                'description': 'مدير المبيعات - إدارة المبيعات والعملاء',
                'permissions': [
                    Permission.SALES_VIEW.value,
                    Permission.SALES_CREATE.value,
                    Permission.SALES_EDIT.value,
                    Permission.SALES_APPROVE.value,
                    Permission.CUSTOMERS_VIEW.value,
                    Permission.CUSTOMERS_CREATE.value,
                    Permission.CUSTOMERS_EDIT.value,
                    Permission.CUSTOMERS_VIEW_BALANCE.value,
                    Permission.PRODUCTS_VIEW.value,
                    Permission.QUOTES_VIEW.value,
                    Permission.QUOTES_CREATE.value,
                    Permission.QUOTES_EDIT.value,
                    Permission.QUOTES_CONVERT.value,
                    Permission.RETURNS_VIEW.value,
                    Permission.RETURNS_CREATE.value,
                    Permission.PAYMENT_PLANS_VIEW.value,
                    Permission.PAYMENT_PLANS_CREATE.value,
                    Permission.REPORTS_SALES.value,
                ]
            },
            {
                'name': 'Sales Representative',
                'description': 'مندوب مبيعات - إنشاء الفواتير',
                'permissions': [
                    Permission.SALES_VIEW.value,
                    Permission.SALES_CREATE.value,
                    Permission.CUSTOMERS_VIEW.value,
                    Permission.CUSTOMERS_CREATE.value,
                    Permission.PRODUCTS_VIEW.value,
                    Permission.QUOTES_VIEW.value,
                    Permission.QUOTES_CREATE.value,
                    Permission.PAYMENT_PLANS_VIEW.value,
                ]
            },
            {
                'name': 'Inventory Manager',
                'description': 'مدير المخزون - إدارة كاملة للمخزون',
                'permissions': [
                    Permission.PRODUCTS_VIEW.value,
                    Permission.PRODUCTS_CREATE.value,
                    Permission.PRODUCTS_EDIT.value,
                    Permission.PRODUCTS_ADJUST_STOCK.value,
                    Permission.PRODUCTS_ADJUST_PRICE.value,
                    Permission.PURCHASES_VIEW.value,
                    Permission.PURCHASES_CREATE.value,
                    Permission.PURCHASES_EDIT.value,
                    Permission.SUPPLIERS_VIEW.value,
                    Permission.SUPPLIERS_CREATE.value,
                    Permission.SUPPLIERS_EDIT.value,
                    Permission.CYCLE_COUNT_VIEW.value,
                    Permission.CYCLE_COUNT_CREATE.value,
                    Permission.CYCLE_COUNT_EXECUTE.value,
                    Permission.RETURNS_VIEW.value,
                    Permission.REPORTS_INVENTORY.value,
                ]
            },
            {
                'name': 'Viewer',
                'description': 'عارض - عرض البيانات فقط',
                'permissions': [
                    Permission.SALES_VIEW.value,
                    Permission.PRODUCTS_VIEW.value,
                    Permission.CUSTOMERS_VIEW.value,
                    Permission.SUPPLIERS_VIEW.value,
                    Permission.PURCHASES_VIEW.value,
                    Permission.QUOTES_VIEW.value,
                    Permission.REPORTS_SALES.value,
                    Permission.REPORTS_INVENTORY.value,
                ]
            }
        ]
        
        for role_data in default_roles:
            try:
                # التحقق من وجود الدور
                existing = self.db.fetch_one(
                    "SELECT role_id FROM roles WHERE name = ?",
                    (role_data['name'],)
                )
                
                if not existing:
                    self.create_role(
                        name=role_data['name'],
                        description=role_data['description'],
                        permissions=set(role_data['permissions'])
                    )
            except Exception as e:
                logger.debug(f"Role {role_data['name']} may already exist: {str(e)}")
                
    def create_role(
        self,
        name: str,
        description: str = "",
        permissions: Optional[Set[str]] = None
    ) -> Optional[int]:
        """
        إنشاء دور جديد
        
        Args:
            name: اسم الدور
            description: وصف الدور
            permissions: مجموعة الصلاحيات
            
        Returns:
            معرف الدور أو None
        """
        try:
            permissions = permissions or set()
            permissions_json = json.dumps(list(permissions))
            
            cursor = self.db.execute(
                """INSERT INTO roles (name, description, permissions)
                   VALUES (?, ?, ?)""",
                (name, description, permissions_json)
            )
            
            logger.info(f"Role created: {name}")
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            return None
            
    def get_role(self, role_id: int) -> Optional[Role]:
        """
        الحصول على دور بالمعرف
        
        Args:
            role_id: معرف الدور
            
        Returns:
            كائن الدور أو None
        """
        row = self.db.fetch_one(
            "SELECT * FROM roles WHERE role_id = ?",
            (role_id,)
        )
        
        if row:
            permissions = set(json.loads(row[3]))  # permissions column
            return Role(
                role_id=row[0],
                name=row[1],
                description=row[2],
                permissions=permissions,
                is_active=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]) if row[5] else None
            )
        return None
        
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """الحصول على دور بالاسم"""
        row = self.db.fetch_one(
            "SELECT * FROM roles WHERE name = ?",
            (name,)
        )
        
        if row:
            permissions = set(json.loads(row[3]))
            return Role(
                role_id=row[0],
                name=row[1],
                description=row[2],
                permissions=permissions,
                is_active=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]) if row[5] else None
            )
        return None
        
    def list_roles(self, active_only: bool = True) -> List[Role]:
        """
        قائمة جميع الأدوار
        
        Args:
            active_only: فقط الأدوار النشطة
            
        Returns:
            قائمة الأدوار
        """
        query = "SELECT * FROM roles"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        
        rows = self.db.fetch_all(query)
        
        roles = []
        for row in rows:
            permissions = set(json.loads(row[3]))
            roles.append(Role(
                role_id=row[0],
                name=row[1],
                description=row[2],
                permissions=permissions,
                is_active=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]) if row[5] else None
            ))
            
        return roles
        
    def update_role_permissions(self, role_id: int, permissions: Set[str]) -> bool:
        """
        تحديث صلاحيات دور
        
        Args:
            role_id: معرف الدور
            permissions: الصلاحيات الجديدة
            
        Returns:
            True إذا نجح التحديث
        """
        try:
            permissions_json = json.dumps(list(permissions))
            
            self.db.execute(
                """UPDATE roles 
                   SET permissions = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE role_id = ?""",
                (permissions_json, role_id)
            )
            
            logger.info(f"Role {role_id} permissions updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update role permissions: {str(e)}")
            return False
            
    def check_permission(self, user_id: int, permission: str) -> bool:
        """
        التحقق من صلاحية مستخدم
        
        Args:
            user_id: معرف المستخدم
            permission: الصلاحية المطلوبة
            
        Returns:
            True إذا كان لديه الصلاحية
        """
        try:
            # الحصول على دور المستخدم
            row = self.db.fetch_one(
                """SELECT r.permissions 
                   FROM users u
                   JOIN roles r ON u.role_id = r.role_id
                   WHERE u.user_id = ? AND u.is_active = 1 AND r.is_active = 1""",
                (user_id,)
            )
            
            if row:
                permissions = set(json.loads(row[0]))
                return permission in permissions
                
            return False
            
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            return False
            
    def get_user_permissions(self, user_id: int) -> Set[str]:
        """
        الحصول على جميع صلاحيات مستخدم
        
        Args:
            user_id: معرف المستخدم
            
        Returns:
            مجموعة الصلاحيات
        """
        try:
            row = self.db.fetch_one(
                """SELECT r.permissions 
                   FROM users u
                   JOIN roles r ON u.role_id = r.role_id
                   WHERE u.user_id = ? AND u.is_active = 1 AND r.is_active = 1""",
                (user_id,)
            )
            
            if row:
                return set(json.loads(row[0]))
                
            return set()
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {str(e)}")
            return set()


# مثيل عام
global_permission_manager: Optional[PermissionManager] = None


def initialize_permission_manager(db_manager) -> PermissionManager:
    """تهيئة مدير الصلاحيات العام"""
    global global_permission_manager
    global_permission_manager = PermissionManager(db_manager)
    return global_permission_manager


def get_permission_manager() -> Optional[PermissionManager]:
    """الحصول على مدير الصلاحيات العام"""
    return global_permission_manager
