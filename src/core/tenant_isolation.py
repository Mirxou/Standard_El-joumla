#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام عزل المستأجرين - Tenant Isolation System
يضمن فصل البيانات بين الشركات المختلفة
"""

from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import threading
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.models.company import CompanyManager


class TenantContext:
    """سياق المستأجر (الشركة) الحالي"""
    
    _local = threading.local()
    
    @classmethod
    def set_current_company_id(cls, company_id: Optional[int]):
        """تعيين معرف الشركة الحالية"""
        cls._local.company_id = company_id
    
    @classmethod
    def get_current_company_id(cls) -> Optional[int]:
        """الحصول على معرف الشركة الحالية"""
        return getattr(cls._local, 'company_id', None)
    
    @classmethod
    def clear(cls):
        """مسح سياق الشركة الحالية"""
        if hasattr(cls._local, 'company_id'):
            delattr(cls._local, 'company_id')


class TenantIsolationManager:
    """مدير عزل المستأجرين"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.company_manager = CompanyManager(db_manager)
    
    def get_current_company_id(self) -> Optional[int]:
        """الحصول على معرف الشركة الحالية"""
        return TenantContext.get_current_company_id()
    
    def set_current_company_id(self, company_id: Optional[int]):
        """تعيين معرف الشركة الحالية"""
        if company_id is not None:
            # التحقق من وجود الشركة
            company = self.company_manager.get_company(company_id)
            if not company:
                raise ValueError(f"الشركة غير موجودة: {company_id}")
            if not company.is_active:
                raise ValueError(f"الشركة غير نشطة: {company_id}")
        
        TenantContext.set_current_company_id(company_id)
    
    def get_current_company(self) -> Optional['Company']:
        """الحصول على الشركة الحالية"""
        company_id = self.get_current_company_id()
        if company_id is None:
            return None
        return self.company_manager.get_company(company_id)
    
    def set_default_company(self):
        """تعيين الشركة الافتراضية كشركة حالية"""
        default_company = self.company_manager.get_default_company()
        if default_company:
            self.set_current_company_id(default_company.id)
        else:
            raise ValueError("لا توجد شركة افتراضية")
    
    @contextmanager
    def company_context(self, company_id: Optional[int]):
        """سياق الشركة (Context Manager)"""
        old_company_id = self.get_current_company_id()
        try:
            self.set_current_company_id(company_id)
            yield
        finally:
            self.set_current_company_id(old_company_id)
    
    def add_company_filter(self, query: str, company_id: Optional[int] = None, table_alias: str = "") -> str:
        """
        إضافة فلتر الشركة إلى استعلام SQL
        
        Args:
            query: استعلام SQL
            company_id: معرف الشركة (إذا كان None، يستخدم الشركة الحالية)
            table_alias: اسم الجدول أو الـ alias (مثل "p" أو "products")
        
        Returns:
            استعلام SQL مع فلتر الشركة
        """
        if company_id is None:
            company_id = self.get_current_company_id()
        
        if company_id is None:
            # إذا لم تكن هناك شركة محددة، لا نضيف فلتر
            return query
        
        # تحديد اسم العمود
        if table_alias:
            column_name = f"{table_alias}.company_id"
        else:
            # محاولة العثور على اسم الجدول من الاستعلام
            # هذا بسيط - قد نحتاج إلى تحسينه لاحقاً
            column_name = "company_id"
        
        # إضافة فلتر WHERE أو AND
        query_upper = query.upper().strip()
        
        if "WHERE" in query_upper:
            # إضافة AND إلى WHERE الموجود
            # نحتاج إلى إيجاد آخر WHERE في الاستعلام
            where_pos = query_upper.rfind("WHERE")
            if where_pos != -1:
                # إضافة AND بعد WHERE
                after_where = query[where_pos + 5:].strip()
                if not after_where.startswith("("):
                    # إضافة AND فقط إذا لم يكن هناك قوس
                    query = query[:where_pos + 5] + f" {column_name} = {company_id} AND " + after_where
                else:
                    # إذا كان هناك قوس، نضيف AND قبل القوس
                    query = query[:where_pos + 5] + f" {column_name} = {company_id} AND " + after_where
            else:
                query += f" AND {column_name} = {company_id}"
        else:
            # إضافة WHERE جديد
            query += f" WHERE {column_name} = {company_id}"
        
        return query
    
    def validate_company_access(self, company_id: int, user_id: Optional[int] = None) -> bool:
        """
        التحقق من صلاحية المستخدم للوصول إلى شركة
        
        Args:
            company_id: معرف الشركة
            user_id: معرف المستخدم (اختياري)
        
        Returns:
            True إذا كان المستخدم لديه صلاحية الوصول
        """
        # التحقق من وجود الشركة ونشاطها
        company = self.company_manager.get_company(company_id)
        if not company or not company.is_active:
            return False
        
        # إذا لم يكن هناك مستخدم محدد، نتحقق فقط من وجود الشركة
        if user_id is None:
            return True
        
        # التحقق من ربط المستخدم بالشركة
        user_companies = self.company_manager.get_user_companies(user_id)
        return any(uc.company_id == company_id and uc.is_active for uc in user_companies)
    
    def get_user_companies(self, user_id: int) -> List['Company']:
        """الحصول على شركات المستخدم"""
        user_companies = self.company_manager.get_user_companies(user_id)
        companies = []
        for uc in user_companies:
            company = self.company_manager.get_company(uc.company_id)
            if company:
                companies.append(company)
        return companies
    
    def get_user_default_company(self, user_id: int) -> Optional['Company']:
        """الحصول على الشركة الافتراضية للمستخدم"""
        user_companies = self.company_manager.get_user_companies(user_id)
        for uc in user_companies:
            if uc.is_default:
                return self.company_manager.get_company(uc.company_id)
        return None


# Singleton instance
_tenant_isolation_manager: Optional[TenantIsolationManager] = None


def get_tenant_isolation_manager(db_manager: Optional[DatabaseManager] = None) -> TenantIsolationManager:
    """الحصول على مدير عزل المستأجرين (Singleton)"""
    global _tenant_isolation_manager
    
    if _tenant_isolation_manager is None:
        if db_manager is None:
            raise ValueError("يجب توفير DatabaseManager عند أول استدعاء")
        _tenant_isolation_manager = TenantIsolationManager(db_manager)
    
    return _tenant_isolation_manager


def set_current_company(company_id: Optional[int], db_manager: Optional[DatabaseManager] = None):
    """تعيين الشركة الحالية (Helper Function)"""
    manager = get_tenant_isolation_manager(db_manager)
    manager.set_current_company_id(company_id)


def get_current_company_id(db_manager: Optional[DatabaseManager] = None) -> Optional[int]:
    """الحصول على معرف الشركة الحالية (Helper Function)"""
    manager = get_tenant_isolation_manager(db_manager)
    return manager.get_current_company_id()


@contextmanager
def company_context(company_id: Optional[int], db_manager: Optional[DatabaseManager] = None):
    """سياق الشركة (Context Manager Helper)"""
    manager = get_tenant_isolation_manager(db_manager)
    with manager.company_context(company_id):
        yield

