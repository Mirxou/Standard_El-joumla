"""
نماذج الصلاحيات والأدوار
Permissions & Roles Models
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class PermissionAction(Enum):
    """أنواع العمليات"""
    VIEW = "عرض"
    CREATE = "إنشاء"
    EDIT = "تعديل"
    DELETE = "حذف"
    APPROVE = "موافقة"
    EXPORT = "تصدير"
    PRINT = "طباعة"
    MANAGE = "إدارة كاملة"


class ResourceType(Enum):
    """أنواع الموارد"""
    PRODUCTS = "المنتجات"
    CUSTOMERS = "العملاء"
    SUPPLIERS = "الموردين"
    SALES = "المبيعات"
    PURCHASES = "المشتريات"
    INVENTORY = "المخزون"
    ACCOUNTING = "المحاسبة"
    QUOTES = "عروض الأسعار"
    RETURNS = "المرتجعات"
    PURCHASE_ORDERS = "أوامر الشراء"
    PAYMENT_PLANS = "خطط الدفع"
    REPORTS = "التقارير"
    USERS = "المستخدمين"
    SETTINGS = "الإعدادات"
    DASHBOARD = "لوحة المعلومات"


class UserStatus(Enum):
    """حالة المستخدم"""
    ACTIVE = "نشط"
    INACTIVE = "غير نشط"
    SUSPENDED = "معلق"
    LOCKED = "مقفل"


@dataclass
class Permission:
    """صلاحية واحدة"""
    id: Optional[int] = None
    name: str = ""
    code: str = ""
    resource_type: ResourceType = ResourceType.PRODUCTS
    action: PermissionAction = PermissionAction.VIEW
    description: str = ""
    is_system: bool = False
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'resource_type': self.resource_type.name,
            'action': self.action.name,
            'description': self.description,
            'is_system': self.is_system,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Permission':
        return cls(
            id=data.get('id'),
            name=data['name'],
            code=data['code'],
            resource_type=ResourceType[data['resource_type']],
            action=PermissionAction[data['action']],
            description=data.get('description', ''),
            is_system=bool(data.get('is_system', False)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )


@dataclass
class Role:
    """دور (مجموعة صلاحيات)"""
    id: Optional[int] = None
    name: str = ""
    code: str = ""
    description: str = ""
    is_system: bool = False
    is_active: bool = True
    permissions: List[Permission] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def has_permission(self, permission_code: str) -> bool:
        """التحقق من وجود صلاحية معينة"""
        return any(p.code == permission_code for p in self.permissions)
    
    def can_perform(self, resource: ResourceType, action: PermissionAction) -> bool:
        """التحقق من إمكانية تنفيذ عملية على مورد"""
        return any(
            p.resource_type == resource and p.action == action
            for p in self.permissions
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'permissions': [p.to_dict() for p in self.permissions],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class User:
    """مستخدم النظام"""
    id: Optional[int] = None
    username: str = ""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    password_hash: str = ""
    role_id: Optional[int] = None
    role: Optional[Role] = None
    status: UserStatus = UserStatus.ACTIVE
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    is_locked: bool = False
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """التحقق من أن المستخدم نشط"""
        if self.is_locked:
            if self.locked_until and datetime.now() > self.locked_until:
                self.is_locked = False
                self.failed_login_attempts = 0
            else:
                return False
        return self.status == UserStatus.ACTIVE
    
    def has_permission(self, permission_code: str) -> bool:
        """التحقق من صلاحية المستخدم"""
        if not self.role:
            return False
        return self.role.has_permission(permission_code)
    
    def can_perform(self, resource: ResourceType, action: PermissionAction) -> bool:
        """التحقق من إمكانية تنفيذ عملية"""
        if not self.role:
            return False
        return self.role.can_perform(resource, action)
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role_id': self.role_id,
            'role': self.role.to_dict() if self.role else None,
            'status': self.status.name,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'failed_login_attempts': self.failed_login_attempts,
            'is_locked': self.is_locked,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_password:
            data['password_hash'] = self.password_hash
        return data


@dataclass
class AuditLog:
    """سجل التدقيق"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    username: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: Optional[int] = None
    old_value: str = ""  # JSON
    new_value: str = ""  # JSON
    ip_address: str = ""
    user_agent: str = ""
    status: str = "success"  # success, failed, warning
    error_message: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class LoginHistory:
    """سجل تسجيل الدخول"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    username: str = ""
    status: str = "success"  # success, failed
    ip_address: str = ""
    user_agent: str = ""
    failure_reason: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'status': self.status,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'failure_reason': self.failure_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
