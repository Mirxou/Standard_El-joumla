#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المستخدم - User Model
يحتوي على جميع العمليات المتعلقة بالمستخدمين والصلاحيات
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, date, timedelta
from enum import Enum
import hashlib
import secrets
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

class UserRole(Enum):
    """أدوار المستخدمين"""
    ADMIN = "مدير"
    MANAGER = "مدير فرع"
    CASHIER = "كاشير"
    INVENTORY = "مسؤول مخزون"
    ACCOUNTANT = "محاسب"
    VIEWER = "مشاهد"

class Permission(Enum):
    """الصلاحيات"""
    # صلاحيات المنتجات
    PRODUCTS_VIEW = "عرض_المنتجات"
    PRODUCTS_CREATE = "إنشاء_المنتجات"
    PRODUCTS_EDIT = "تعديل_المنتجات"
    PRODUCTS_DELETE = "حذف_المنتجات"
    
    # صلاحيات المبيعات
    SALES_VIEW = "عرض_المبيعات"
    SALES_CREATE = "إنشاء_المبيعات"
    SALES_EDIT = "تعديل_المبيعات"
    SALES_DELETE = "حذف_المبيعات"
    SALES_CANCEL = "إلغاء_المبيعات"
    
    # صلاحيات المشتريات
    PURCHASES_VIEW = "عرض_المشتريات"
    PURCHASES_CREATE = "إنشاء_المشتريات"
    PURCHASES_EDIT = "تعديل_المشتريات"
    PURCHASES_DELETE = "حذف_المشتريات"
    PURCHASES_RECEIVE = "استلام_المشتريات"
    
    # صلاحيات العملاء والموردين
    CUSTOMERS_VIEW = "عرض_العملاء"
    CUSTOMERS_MANAGE = "إدارة_العملاء"
    SUPPLIERS_VIEW = "عرض_الموردين"
    SUPPLIERS_MANAGE = "إدارة_الموردين"
    
    # صلاحيات التقارير
    REPORTS_VIEW = "عرض_التقارير"
    REPORTS_EXPORT = "تصدير_التقارير"
    REPORTS_FINANCIAL = "التقارير_المالية"
    
    # صلاحيات النظام
    USERS_VIEW = "عرض_المستخدمين"
    USERS_MANAGE = "إدارة_المستخدمين"
    SETTINGS_VIEW = "عرض_الإعدادات"
    SETTINGS_MANAGE = "إدارة_الإعدادات"
    BACKUP_RESTORE = "النسخ_الاحتياطي"
    
    # صلاحيات المخزون
    INVENTORY_VIEW = "عرض_المخزون"
    INVENTORY_ADJUST = "تعديل_المخزون"
    INVENTORY_TRANSFER = "نقل_المخزون"

@dataclass
class User:
    """نموذج بيانات المستخدم"""
    id: Optional[int] = None
    username: str = ""
    email: Optional[str] = None
    full_name: str = ""
    phone: Optional[str] = None
    role: str = UserRole.VIEWER.value
    password_hash: Optional[str] = None
    salt: Optional[str] = None
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    last_password_change: Optional[datetime] = None
    password_expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    permissions: Set[str] = None
    
    def __post_init__(self):
        """تهيئة بعد الإنشاء"""
        if self.permissions is None:
            self.permissions = set()
    
    @property
    def is_admin(self) -> bool:
        """هل المستخدم مدير؟"""
        return self.role == UserRole.ADMIN.value
    
    @property
    def is_password_expired(self) -> bool:
        """هل انتهت صلاحية كلمة المرور؟"""
        if not self.password_expires_at:
            return False
        return datetime.now() > self.password_expires_at
    
    @property
    def days_until_password_expires(self) -> Optional[int]:
        """عدد الأيام المتبقية لانتهاء كلمة المرور"""
        if not self.password_expires_at:
            return None
        
        delta = self.password_expires_at - datetime.now()
        return max(0, delta.days)
    
    def has_permission(self, permission: str) -> bool:
        """التحقق من وجود صلاحية"""
        if self.is_admin:
            return True
        return permission in self.permissions
    
    def add_permission(self, permission: str):
        """إضافة صلاحية"""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: str):
        """حذف صلاحية"""
        self.permissions.discard(permission)
    
    def set_permissions(self, permissions: List[str]):
        """تعيين الصلاحيات"""
        self.permissions = set(permissions)
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'failed_login_attempts': self.failed_login_attempts,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_password_change': self.last_password_change.isoformat() if self.last_password_change else None,
            'password_expires_at': self.password_expires_at.isoformat() if self.password_expires_at else None,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'permissions': list(self.permissions),
            'is_admin': self.is_admin,
            'is_password_expired': self.is_password_expired,
            'days_until_password_expires': self.days_until_password_expires
        }

class UserManager:
    """مدير المستخدمين"""
    
    # الصلاحيات الافتراضية لكل دور
    DEFAULT_PERMISSIONS = {
        UserRole.ADMIN.value: [p.value for p in Permission],
        UserRole.MANAGER.value: [
            Permission.PRODUCTS_VIEW.value, Permission.PRODUCTS_CREATE.value, Permission.PRODUCTS_EDIT.value,
            Permission.SALES_VIEW.value, Permission.SALES_CREATE.value, Permission.SALES_EDIT.value,
            Permission.PURCHASES_VIEW.value, Permission.PURCHASES_CREATE.value, Permission.PURCHASES_EDIT.value,
            Permission.CUSTOMERS_VIEW.value, Permission.CUSTOMERS_MANAGE.value,
            Permission.SUPPLIERS_VIEW.value, Permission.SUPPLIERS_MANAGE.value,
            Permission.REPORTS_VIEW.value, Permission.REPORTS_EXPORT.value,
            Permission.INVENTORY_VIEW.value, Permission.INVENTORY_ADJUST.value
        ],
        UserRole.CASHIER.value: [
            Permission.PRODUCTS_VIEW.value,
            Permission.SALES_VIEW.value, Permission.SALES_CREATE.value,
            Permission.CUSTOMERS_VIEW.value,
            Permission.INVENTORY_VIEW.value
        ],
        UserRole.INVENTORY.value: [
            Permission.PRODUCTS_VIEW.value, Permission.PRODUCTS_CREATE.value, Permission.PRODUCTS_EDIT.value,
            Permission.PURCHASES_VIEW.value, Permission.PURCHASES_CREATE.value, Permission.PURCHASES_RECEIVE.value,
            Permission.SUPPLIERS_VIEW.value,
            Permission.INVENTORY_VIEW.value, Permission.INVENTORY_ADJUST.value, Permission.INVENTORY_TRANSFER.value
        ],
        UserRole.ACCOUNTANT.value: [
            Permission.SALES_VIEW.value, Permission.PURCHASES_VIEW.value,
            Permission.CUSTOMERS_VIEW.value, Permission.SUPPLIERS_VIEW.value,
            Permission.REPORTS_VIEW.value, Permission.REPORTS_EXPORT.value, Permission.REPORTS_FINANCIAL.value
        ],
        UserRole.VIEWER.value: [
            Permission.PRODUCTS_VIEW.value, Permission.SALES_VIEW.value,
            Permission.CUSTOMERS_VIEW.value, Permission.INVENTORY_VIEW.value
        ]
    }
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.max_failed_attempts = 5
        self.password_expiry_days = 90
    
    def create_user(self, user: User, password: str) -> Optional[int]:
        """إنشاء مستخدم جديد"""
        try:
            if self.logger:
                self.logger.info(f"بدء إنشاء المستخدم: {user.username}")
            
            # التحقق من عدم وجود اسم المستخدم
            if self.get_user_by_username(user.username):
                if self.logger:
                    self.logger.warning(f"اسم المستخدم {user.username} موجود بالفعل")
                return None
            
            # تشفير كلمة المرور
            user.salt = secrets.token_hex(32)
            user.password_hash = self._hash_password(password, user.salt)
            user.last_password_change = datetime.now()
            user.password_expires_at = datetime.now() + timedelta(days=self.password_expiry_days) if self.password_expiry_days > 0 else None
            
            # تعيين الصلاحيات الافتراضية
            if not user.permissions:
                user.set_permissions(self.DEFAULT_PERMISSIONS.get(user.role, []))
            
            if self.logger:
                self.logger.info(f"تحضير إدراج المستخدم في قاعدة البيانات")
            
            # إدراج المستخدم
            query = """
            INSERT INTO users (
                username, email, full_name, phone, role, password_hash, salt,
                is_active, last_password_change, password_expires_at, notes,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                user.username,
                user.email,
                user.full_name,
                user.phone,
                user.role,
                user.password_hash,
                user.salt,
                user.is_active,
                user.last_password_change,
                user.password_expires_at,
                user.notes,
                user.created_by,
                now,
                now
            )
            
            if self.logger:
                self.logger.info(f"تنفيذ استعلام الإدراج مع المعاملات: {params[:5]}...")  # عرض أول 5 معاملات فقط
            
            result = self.db_manager.execute_non_query(query, params)
            if self.logger:
                self.logger.info(f"نتيجة الإدراج: {result} صف متأثر")
            
            if result > 0:
                user_id = self.db_manager.get_last_insert_id()
                if self.logger:
                    self.logger.info(f"تم الحصول على ID الجديد: {user_id}")
                
                user.id = user_id
                
                # حفظ الصلاحيات
                if self.logger:
                    self.logger.info(f"حفظ الصلاحيات للمستخدم {user_id}")
                self._save_user_permissions(user_id, user.permissions)
                
                if self.logger:
                    self.logger.info(f"تم إنشاء مستخدم جديد: {user.username} (ID: {user_id})")
                
                return user_id
            else:
                if self.logger:
                    self.logger.error(f"فشل في إدراج المستخدم - لم يتأثر أي صف")
                return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء المستخدم: {str(e)}")
                import traceback
                self.logger.error(f"تفاصيل الخطأ: {traceback.format_exc()}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """التحقق من صحة بيانات المستخدم"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return None
            
            # التحقق من حالة المستخدم
            if not user.is_active:
                if self.logger:
                    self.logger.warning(f"محاولة دخول لمستخدم غير نشط: {username}")
                return None
            
            if user.is_locked:
                if self.logger:
                    self.logger.warning(f"محاولة دخول لمستخدم مقفل: {username}")
                return None
            
            # التحقق من كلمة المرور
            if not self._verify_password(password, user.password_hash, user.salt):
                # زيادة عدد المحاولات الفاشلة
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= self.max_failed_attempts:
                    user.is_locked = True
                    if self.logger:
                        self.logger.warning(f"تم قفل المستخدم {username} بسبب المحاولات الفاشلة")
                
                self._update_failed_attempts(user.id, user.failed_login_attempts, user.is_locked)
                return None
            
            # تسجيل دخول ناجح
            user.last_login = datetime.now()
            user.failed_login_attempts = 0
            self._update_last_login(user.id, user.last_login)
            
            if self.logger:
                self.logger.info(f"تسجيل دخول ناجح: {username}")
            
            return user
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في التحقق من المستخدم {username}: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """الحصول على مستخدم بالمعرف"""
        try:
            query = "SELECT * FROM users WHERE id = ?"
            result = self.db_manager.fetch_one(query, (user_id,))
            
            if result:
                user = self._row_to_user(result)
                user.permissions = self._load_user_permissions(user_id)
                return user
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المستخدم {user_id}: {str(e)}")
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """الحصول على مستخدم باسم المستخدم"""
        try:
            query = "SELECT * FROM users WHERE username = ?"
            result = self.db_manager.fetch_one(query, (username,))
            
            if result:
                user = self._row_to_user(result)
                user.permissions = self._load_user_permissions(user.id)
                return user
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث عن المستخدم {username}: {str(e)}")
        
        return None
    
    def get_all_users(self, active_only: bool = True) -> List[User]:
        """الحصول على جميع المستخدمين"""
        try:
            query = "SELECT * FROM users"
            params = []
            
            if active_only:
                query += " WHERE is_active = 1"
            
            query += " ORDER BY full_name"
            
            results = self.db_manager.fetch_all(query, params)
            users = []
            
            for row in results:
                user = self._row_to_user(row)
                user.permissions = self._load_user_permissions(user.id)
                users.append(user)
            
            return users
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المستخدمين: {str(e)}")
            return []
    
    def update_user(self, user: User) -> bool:
        """تحديث مستخدم"""
        try:
            query = """
            UPDATE users SET
                email = ?, full_name = ?, phone = ?, role = ?,
                is_active = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (
                user.email,
                user.full_name,
                user.phone,
                user.role,
                user.is_active,
                user.notes,
                datetime.now(),
                user.id
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                # تحديث الصلاحيات
                self._save_user_permissions(user.id, user.permissions)
                
                if self.logger:
                    self.logger.info(f"تم تحديث المستخدم: {user.username}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المستخدم {user.id}: {str(e)}")
        
        return False
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """تغيير كلمة المرور"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # التحقق من كلمة المرور القديمة
            if not self._verify_password(old_password, user.password_hash, user.salt):
                if self.logger:
                    self.logger.warning(f"محاولة تغيير كلمة مرور خاطئة للمستخدم {user_id}")
                return False
            
            # تشفير كلمة المرور الجديدة
            new_salt = secrets.token_hex(32)
            new_hash = self._hash_password(new_password, new_salt)
            
            query = """
            UPDATE users SET
                password_hash = ?, salt = ?, last_password_change = ?,
                password_expires_at = ?, updated_at = ?
            WHERE id = ?
            """
            
            now = datetime.now()
            expires_at = now + timedelta(days=self.password_expiry_days) if self.password_expiry_days > 0 else None
            
            params = (new_hash, new_salt, now, expires_at, now, user_id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تغيير كلمة مرور المستخدم {user_id}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تغيير كلمة المرور للمستخدم {user_id}: {str(e)}")
        
        return False
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """إعادة تعيين كلمة المرور (للمدير)"""
        try:
            # تشفير كلمة المرور الجديدة
            new_salt = secrets.token_hex(32)
            new_hash = self._hash_password(new_password, new_salt)
            
            query = """
            UPDATE users SET
                password_hash = ?, salt = ?, last_password_change = ?,
                password_expires_at = ?, failed_login_attempts = 0,
                is_locked = 0, updated_at = ?
            WHERE id = ?
            """
            
            now = datetime.now()
            expires_at = now + timedelta(days=self.password_expiry_days) if self.password_expiry_days > 0 else None
            
            params = (new_hash, new_salt, now, expires_at, now, user_id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم إعادة تعيين كلمة مرور المستخدم {user_id}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إعادة تعيين كلمة المرور للمستخدم {user_id}: {str(e)}")
        
        return False
    
    def unlock_user(self, user_id: int) -> bool:
        """إلغاء قفل المستخدم"""
        try:
            query = """
            UPDATE users SET
                is_locked = 0, failed_login_attempts = 0, updated_at = ?
            WHERE id = ?
            """
            
            result = self.db_manager.execute_query(query, (datetime.now(), user_id))
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم إلغاء قفل المستخدم {user_id}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء قفل المستخدم {user_id}: {str(e)}")
        
        return False
    
    def delete_user(self, user_id: int) -> bool:
        """حذف مستخدم"""
        try:
            # حذف الصلاحيات أولاً
            self.db_manager.execute_non_query("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
            
            # حذف المستخدم
            query = "DELETE FROM users WHERE id = ?"
            result = self.db_manager.execute_query(query, (user_id,))
            
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم حذف المستخدم {user_id}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المستخدم {user_id}: {str(e)}")
        
        return False
    
    def create_default_admin(self) -> bool:
        """إنشاء مدير افتراضي"""
        try:
            # التحقق من وجود مدير
            existing_admin = self.db_manager.fetch_one(
                "SELECT id FROM users WHERE role = ? LIMIT 1", 
                (UserRole.ADMIN.value,)
            )
            
            if existing_admin:
                return True  # يوجد مدير بالفعل
            
            # إنشاء مدير افتراضي
            admin = User(
                username="admin",
                email="admin@company.com",
                full_name="مدير النظام",
                role=UserRole.ADMIN.value,
                is_active=True
            )
            
            admin_id = self.create_user(admin, "admin123")
            if admin_id:
                if self.logger:
                    self.logger.info("تم إنشاء المدير الافتراضي")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء المدير الافتراضي: {str(e)}")
        
        return False
    
    def _hash_password(self, password: str, salt: str) -> str:
        """تشفير كلمة المرور"""
        import hashlib
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """التحقق من كلمة المرور"""
        return self._hash_password(password, salt) == hash_value
    
    def _save_user_permissions(self, user_id: int, permissions: Set[str]):
        """حفظ صلاحيات المستخدم"""
        try:
            # حذف الصلاحيات الحالية
            self.db_manager.execute_non_query("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
            
            # إدراج الصلاحيات الجديدة
            for permission in permissions:
                self.db_manager.execute_query(
                    "INSERT INTO user_permissions (user_id, permission) VALUES (?, ?)",
                    (user_id, permission)
                )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حفظ صلاحيات المستخدم {user_id}: {str(e)}")
    
    def _load_user_permissions(self, user_id: int) -> Set[str]:
        """تحميل صلاحيات المستخدم"""
        try:
            query = "SELECT permission FROM user_permissions WHERE user_id = ?"
            results = self.db_manager.fetch_all(query, (user_id,))
            return {row[0] for row in results}
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل صلاحيات المستخدم {user_id}: {str(e)}")
            return set()
    
    def _update_failed_attempts(self, user_id: int, attempts: int, is_locked: bool):
        """تحديث المحاولات الفاشلة"""
        try:
            query = "UPDATE users SET failed_login_attempts = ?, is_locked = ? WHERE id = ?"
            self.db_manager.execute_query(query, (attempts, is_locked, user_id))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المحاولات الفاشلة للمستخدم {user_id}: {str(e)}")
    
    def _update_last_login(self, user_id: int, last_login: datetime):
        """تحديث آخر تسجيل دخول"""
        try:
            query = "UPDATE users SET last_login = ?, failed_login_attempts = 0 WHERE id = ?"
            self.db_manager.execute_query(query, (last_login, user_id))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث آخر تسجيل دخول للمستخدم {user_id}: {str(e)}")
    
    def _row_to_user(self, row) -> User:
        """تحويل صف قاعدة البيانات إلى كائن مستخدم"""
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            full_name=row[3],
            phone=row[4],
            role=row[5],
            password_hash=row[6],
            salt=row[7],
            is_active=bool(row[8]),
            is_locked=bool(row[9]),
            failed_login_attempts=row[10],
            last_login=datetime.fromisoformat(row[11]) if row[11] else None,
            last_password_change=datetime.fromisoformat(row[12]) if row[12] else None,
            password_expires_at=datetime.fromisoformat(row[13]) if row[13] else None,
            notes=row[14],
            created_by=row[15],
            created_at=datetime.fromisoformat(row[16]) if row[16] else None,
            updated_at=datetime.fromisoformat(row[17]) if row[17] else None
        )