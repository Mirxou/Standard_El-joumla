"""
خدمة إدارة الصلاحيات والأدوار
Permissions & Roles Service
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import hashlib
import secrets
from datetime import datetime, timedelta

from ..core.database_manager import DatabaseManager
from ..models.permission import (
    Permission, Role, User, PermissionAction, ResourceType, UserStatus
)


class PermissionService:
    """خدمة إدارة الصلاحيات والأدوار"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self._init_default_permissions()
        self._init_default_roles()
    
    # ==================== Permissions Management ====================
    
    def _init_default_permissions(self):
        """تهيئة الصلاحيات الافتراضية"""
        default_permissions = self._get_default_permissions()
        
        for perm in default_permissions:
            existing = self.db.execute_query(
                "SELECT id FROM permissions WHERE code = ?",
                [perm['code']]
            )
            if not existing:
                self.db.execute_update(
                    """INSERT INTO permissions (name, code, resource_type, action, description, is_system)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [perm['name'], perm['code'], perm['resource_type'], 
                     perm['action'], perm['description'], 1]
                )
    
    def _get_default_permissions(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة الصلاحيات الافتراضية"""
        permissions = []
        
        # توليد صلاحيات لكل مورد
        for resource in ResourceType:
            for action in [PermissionAction.VIEW, PermissionAction.CREATE, 
                          PermissionAction.EDIT, PermissionAction.DELETE]:
                code = f"{resource.name}_{action.name}"
                name = f"{action.value} {resource.value}"
                permissions.append({
                    'name': name,
                    'code': code,
                    'resource_type': resource.name,
                    'action': action.name,
                    'description': f"صلاحية {action.value} في {resource.value}"
                })
        
        # صلاحيات خاصة
        special_perms = [
            {
                'name': 'موافقة المبيعات',
                'code': 'SALES_APPROVE',
                'resource_type': ResourceType.SALES.name,
                'action': PermissionAction.APPROVE.name,
                'description': 'موافقة على فواتير المبيعات'
            },
            {
                'name': 'تصدير التقارير',
                'code': 'REPORTS_EXPORT',
                'resource_type': ResourceType.REPORTS.name,
                'action': PermissionAction.EXPORT.name,
                'description': 'تصدير التقارير'
            },
            {
                'name': 'إدارة النظام',
                'code': 'SYSTEM_MANAGE',
                'resource_type': ResourceType.SETTINGS.name,
                'action': PermissionAction.MANAGE.name,
                'description': 'إدارة كاملة للنظام'
            }
        ]
        permissions.extend(special_perms)
        
        return permissions
    
    def create_permission(self, permission: Permission) -> int:
        """إنشاء صلاحية جديدة"""
        return self.db.execute_update(
            """INSERT INTO permissions (name, code, resource_type, action, description, is_system)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [permission.name, permission.code, permission.resource_type.name,
             permission.action.name, permission.description, int(permission.is_system)]
        )
    
    def get_permission(self, permission_id: int) -> Optional[Permission]:
        """الحصول على صلاحية بالمعرف"""
        result = self.db.execute_query(
            "SELECT * FROM permissions WHERE id = ?",
            [permission_id]
        )
        if not result:
            return None
        return Permission.from_dict(result[0])
    
    def list_permissions(self, resource_type: Optional[ResourceType] = None) -> List[Permission]:
        """قائمة جميع الصلاحيات"""
        if resource_type:
            result = self.db.execute_query(
                "SELECT * FROM permissions WHERE resource_type = ? ORDER BY name",
                [resource_type.name]
            )
        else:
            result = self.db.execute_query(
                "SELECT * FROM permissions ORDER BY resource_type, name"
            )
        
        return [Permission.from_dict(row) for row in result]
    
    # ==================== Roles Management ====================
    
    def _init_default_roles(self):
        """تهيئة الأدوار الافتراضية"""
        # دور المدير (كل الصلاحيات)
        admin_role = self.db.execute_query(
            "SELECT id FROM roles WHERE code = 'ADMIN'"
        )
        if not admin_role:
            role_id = self.db.execute_update(
                """INSERT INTO roles (name, code, description, is_system, is_active)
                   VALUES (?, ?, ?, ?, ?)""",
                ['مدير النظام', 'ADMIN', 'صلاحيات كاملة على النظام', 1, 1]
            )
            # إضافة كل الصلاحيات
            permissions = self.list_permissions()
            for perm in permissions:
                self.db.execute_update(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                    [role_id, perm.id]
                )
        
        # دور المحاسب
        accountant_role = self.db.execute_query(
            "SELECT id FROM roles WHERE code = 'ACCOUNTANT'"
        )
        if not accountant_role:
            role_id = self.db.execute_update(
                """INSERT INTO roles (name, code, description, is_system, is_active)
                   VALUES (?, ?, ?, ?, ?)""",
                ['محاسب', 'ACCOUNTANT', 'صلاحيات المحاسبة والتقارير المالية', 1, 1]
            )
            # صلاحيات محددة
            perm_codes = [
                'ACCOUNTING_VIEW', 'ACCOUNTING_CREATE', 'ACCOUNTING_EDIT',
                'REPORTS_VIEW', 'REPORTS_EXPORT',
                'SALES_VIEW', 'PURCHASES_VIEW'
            ]
            for code in perm_codes:
                perm = self.db.execute_query(
                    "SELECT id FROM permissions WHERE code = ?", [code]
                )
                if perm:
                    self.db.execute_update(
                        "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        [role_id, perm[0]['id']]
                    )
        
        # دور موظف المبيعات
        sales_role = self.db.execute_query(
            "SELECT id FROM roles WHERE code = 'SALES_STAFF'"
        )
        if not sales_role:
            role_id = self.db.execute_update(
                """INSERT INTO roles (name, code, description, is_system, is_active)
                   VALUES (?, ?, ?, ?, ?)""",
                ['موظف مبيعات', 'SALES_STAFF', 'صلاحيات المبيعات والعملاء', 1, 1]
            )
            perm_codes = [
                'SALES_VIEW', 'SALES_CREATE', 'SALES_EDIT',
                'CUSTOMERS_VIEW', 'CUSTOMERS_CREATE', 'CUSTOMERS_EDIT',
                'PRODUCTS_VIEW', 'INVENTORY_VIEW',
                'QUOTES_VIEW', 'QUOTES_CREATE', 'QUOTES_EDIT'
            ]
            for code in perm_codes:
                perm = self.db.execute_query(
                    "SELECT id FROM permissions WHERE code = ?", [code]
                )
                if perm:
                    self.db.execute_update(
                        "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        [role_id, perm[0]['id']]
                    )
    
    def create_role(self, role: Role) -> int:
        """إنشاء دور جديد"""
        role_id = self.db.execute_update(
            """INSERT INTO roles (name, code, description, is_system, is_active)
               VALUES (?, ?, ?, ?, ?)""",
            [role.name, role.code, role.description, int(role.is_system), int(role.is_active)]
        )
        
        # إضافة الصلاحيات
        for perm in role.permissions:
            self.db.execute_update(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                [role_id, perm.id]
            )
        
        return role_id
    
    def get_role(self, role_id: int) -> Optional[Role]:
        """الحصول على دور بالمعرف"""
        result = self.db.execute_query(
            "SELECT * FROM roles WHERE id = ?",
            [role_id]
        )
        if not result:
            return None
        
        role_data = result[0]
        role = Role(
            id=role_data['id'],
            name=role_data['name'],
            code=role_data['code'],
            description=role_data.get('description', ''),
            is_system=bool(role_data.get('is_system', False)),
            is_active=bool(role_data.get('is_active', True)),
            created_at=datetime.fromisoformat(role_data['created_at']) if role_data.get('created_at') else None,
            updated_at=datetime.fromisoformat(role_data['updated_at']) if role_data.get('updated_at') else None
        )
        
        # تحميل الصلاحيات
        role.permissions = self.get_role_permissions(role_id)
        return role
    
    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """الحصول على صلاحيات دور معين"""
        result = self.db.execute_query(
            """SELECT p.* FROM permissions p
               INNER JOIN role_permissions rp ON p.id = rp.permission_id
               WHERE rp.role_id = ?
               ORDER BY p.resource_type, p.name""",
            [role_id]
        )
        return [Permission.from_dict(row) for row in result]
    
    def update_role_permissions(self, role_id: int, permission_ids: List[int]) -> bool:
        """تحديث صلاحيات دور"""
        # حذف الصلاحيات الحالية
        self.db.execute_update(
            "DELETE FROM role_permissions WHERE role_id = ?",
            [role_id]
        )
        
        # إضافة الصلاحيات الجديدة
        for perm_id in permission_ids:
            self.db.execute_update(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                [role_id, perm_id]
            )
        
        return True
    
    def list_roles(self, active_only: bool = False) -> List[Role]:
        """قائمة جميع الأدوار"""
        if active_only:
            result = self.db.execute_query(
                "SELECT * FROM roles WHERE is_active = 1 ORDER BY name"
            )
        else:
            result = self.db.execute_query(
                "SELECT * FROM roles ORDER BY name"
            )
        
        roles = []
        for row in result:
            role = Role(
                id=row['id'],
                name=row['name'],
                code=row['code'],
                description=row.get('description', ''),
                is_system=bool(row.get('is_system', False)),
                is_active=bool(row.get('is_active', True)),
                created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None
            )
            role.permissions = self.get_role_permissions(role.id)
            roles.append(role)
        
        return roles
    
    # ==================== Users Management ====================
    
    def create_user(self, user: User, password: str) -> int:
        """إنشاء مستخدم جديد"""
        # تشفير كلمة المرور
        password_hash = self._hash_password(password)
        
        return self.db.execute_update(
            """INSERT INTO users (username, full_name, email, phone, password_hash, 
                                 role_id, status, failed_login_attempts, is_locked)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [user.username, user.full_name, user.email, user.phone, password_hash,
             user.role_id, user.status.name, 0, 0]
        )
    
    def get_user(self, user_id: int) -> Optional[User]:
        """الحصول على مستخدم بالمعرف"""
        result = self.db.execute_query(
            "SELECT * FROM users WHERE id = ?",
            [user_id]
        )
        if not result:
            return None
        
        return self._user_from_row(result[0])
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """الحصول على مستخدم بالاسم"""
        result = self.db.execute_query(
            "SELECT * FROM users WHERE username = ?",
            [username]
        )
        if not result:
            return None
        
        return self._user_from_row(result[0])
    
    def _user_from_row(self, row: Dict[str, Any]) -> User:
        """تحويل صف من قاعدة البيانات إلى كائن User"""
        user = User(
            id=row['id'],
            username=row['username'],
            full_name=row['full_name'],
            email=row.get('email', ''),
            phone=row.get('phone', ''),
            password_hash=row['password_hash'],
            role_id=row.get('role_id'),
            status=UserStatus[row['status']],
            last_login=datetime.fromisoformat(row['last_login']) if row.get('last_login') else None,
            failed_login_attempts=row.get('failed_login_attempts', 0),
            is_locked=bool(row.get('is_locked', False)),
            locked_until=datetime.fromisoformat(row['locked_until']) if row.get('locked_until') else None,
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None
        )
        
        # تحميل الدور
        if user.role_id:
            user.role = self.get_role(user.role_id)
        
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """مصادقة المستخدم"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        # التحقق من الحساب المقفل
        if not user.is_active():
            return None
        
        # التحقق من كلمة المرور
        if not self._verify_password(password, user.password_hash):
            # زيادة عدد المحاولات الفاشلة
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                # قفل الحساب لمدة 30 دقيقة
                user.is_locked = True
                user.locked_until = datetime.now() + timedelta(minutes=30)
            
            self.db.execute_update(
                """UPDATE users SET failed_login_attempts = ?, is_locked = ?, locked_until = ?
                   WHERE id = ?""",
                [user.failed_login_attempts, int(user.is_locked),
                 user.locked_until.isoformat() if user.locked_until else None, user.id]
            )
            return None
        
        # نجحت المصادقة - تحديث آخر دخول وإعادة تعيين المحاولات
        self.db.execute_update(
            """UPDATE users SET last_login = ?, failed_login_attempts = 0, 
                              is_locked = 0, locked_until = NULL
               WHERE id = ?""",
            [datetime.now().isoformat(), user.id]
        )
        
        user.last_login = datetime.now()
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        
        return user
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """تغيير كلمة مرور المستخدم"""
        password_hash = self._hash_password(new_password)
        self.db.execute_update(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            [password_hash, datetime.now().isoformat(), user_id]
        )
        return True
    
    def list_users(self, active_only: bool = False) -> List[User]:
        """قائمة جميع المستخدمين"""
        if active_only:
            result = self.db.execute_query(
                "SELECT * FROM users WHERE status = ? ORDER BY full_name",
                [UserStatus.ACTIVE.name]
            )
        else:
            result = self.db.execute_query(
                "SELECT * FROM users ORDER BY full_name"
            )
        
        return [self._user_from_row(row) for row in result]
    
    # ==================== Helper Methods ====================
    
    def _hash_password(self, password: str) -> str:
        """تشفير كلمة المرور"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                       salt.encode('utf-8'), 100000)
        return salt + ':' + pwd_hash.hex()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """التحقق من كلمة المرور"""
        try:
            salt, hash_value = password_hash.split(':')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                          salt.encode('utf-8'), 100000)
            return pwd_hash.hex() == hash_value
        except:
            return False
