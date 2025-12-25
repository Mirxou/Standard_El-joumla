#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الشركات - Company Model
يحتوي على جميع العمليات المتعلقة بالشركات
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager


@dataclass
class Company:
    """نموذج بيانات الشركة"""
    id: Optional[int] = None
    code: str = ""                              # رمز الشركة
    name: str = ""                              # اسم الشركة
    name_en: str = ""                           # الاسم بالإنجليزية
    legal_name: str = ""                        # الاسم القانوني
    tax_id: str = ""                            # الرقم الضريبي
    registration_number: str = ""               # رقم التسجيل التجاري
    
    # معلومات الاتصال
    address: str = ""
    city: str = ""
    state: str = ""
    country: str = "الجزائر"
    postal_code: str = ""
    phone: str = ""
    phone2: str = ""
    email: str = ""
    website: str = ""
    
    # معلومات مالية
    base_currency_id: Optional[int] = None      # العملة الأساسية
    fiscal_year_start: Optional[date] = None    # بداية السنة المالية
    fiscal_year_end: Optional[date] = None       # نهاية السنة المالية
    tax_rate: Decimal = Decimal('19.00')         # معدل الضريبة الافتراضي
    
    # إعدادات
    is_active: bool = True                      # نشط/غير نشط
    is_default: bool = False                     # الشركة الافتراضية
    timezone: str = "Africa/Algiers"           # المنطقة الزمنية
    locale: str = "ar_DZ"                      # اللغة/المنطقة
    date_format: str = "YYYY-MM-DD"            # تنسيق التاريخ
    time_format: str = "HH:mm:ss"               # تنسيق الوقت
    
    # معلومات إضافية
    logo_path: str = ""
    notes: str = ""
    metadata: str = ""                          # بيانات إضافية (JSON)
    
    # الطوابع الزمنية
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'name_en': self.name_en,
            'legal_name': self.legal_name,
            'tax_id': self.tax_id,
            'registration_number': self.registration_number,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'phone2': self.phone2,
            'email': self.email,
            'website': self.website,
            'base_currency_id': self.base_currency_id,
            'fiscal_year_start': self.fiscal_year_start.isoformat() if self.fiscal_year_start else None,
            'fiscal_year_end': self.fiscal_year_end.isoformat() if self.fiscal_year_end else None,
            'tax_rate': float(self.tax_rate),
            'is_active': 1 if self.is_active else 0,
            'is_default': 1 if self.is_default else 0,
            'timezone': self.timezone,
            'locale': self.locale,
            'date_format': self.date_format,
            'time_format': self.time_format,
            'logo_path': self.logo_path,
            'notes': self.notes,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Company':
        """إنشاء من قاموس"""
        fiscal_year_start = None
        fiscal_year_end = None
        if data.get('fiscal_year_start'):
            if isinstance(data['fiscal_year_start'], str):
                fiscal_year_start = date.fromisoformat(data['fiscal_year_start'])
            else:
                fiscal_year_start = data['fiscal_year_start']
        if data.get('fiscal_year_end'):
            if isinstance(data['fiscal_year_end'], str):
                fiscal_year_end = date.fromisoformat(data['fiscal_year_end'])
            else:
                fiscal_year_end = data['fiscal_year_end']
        
        return cls(
            id=data.get('id'),
            code=data.get('code', ''),
            name=data.get('name', ''),
            name_en=data.get('name_en', ''),
            legal_name=data.get('legal_name', ''),
            tax_id=data.get('tax_id', ''),
            registration_number=data.get('registration_number', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            country=data.get('country', 'الجزائر'),
            postal_code=data.get('postal_code', ''),
            phone=data.get('phone', ''),
            phone2=data.get('phone2', ''),
            email=data.get('email', ''),
            website=data.get('website', ''),
            base_currency_id=data.get('base_currency_id'),
            fiscal_year_start=fiscal_year_start,
            fiscal_year_end=fiscal_year_end,
            tax_rate=Decimal(str(data.get('tax_rate', 19.00))),
            is_active=bool(data.get('is_active', 1)),
            is_default=bool(data.get('is_default', 0)),
            timezone=data.get('timezone', 'Africa/Algiers'),
            locale=data.get('locale', 'ar_DZ'),
            date_format=data.get('date_format', 'YYYY-MM-DD'),
            time_format=data.get('time_format', 'HH:mm:ss'),
            logo_path=data.get('logo_path', ''),
            notes=data.get('notes', ''),
            metadata=data.get('metadata', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by')
        )


@dataclass
class UserCompany:
    """نموذج بيانات ربط المستخدم بالشركة"""
    id: Optional[int] = None
    user_id: int = 0
    company_id: int = 0
    is_default: bool = False                    # الشركة الافتراضية للمستخدم
    is_active: bool = True                      # نشط/غير نشط
    role: str = ""                              # دور المستخدم في هذه الشركة
    permissions: str = ""                       # الصلاحيات الخاصة (JSON)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'is_default': 1 if self.is_default else 0,
            'is_active': 1 if self.is_active else 0,
            'role': self.role,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CompanyManager:
    """مدير الشركات"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_company(self, company_id: int) -> Optional[Company]:
        """الحصول على شركة بالمعرف"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, code, name, name_en, legal_name, tax_id, registration_number,
                   address, city, state, country, postal_code, phone, phone2, email, website,
                   base_currency_id, fiscal_year_start, fiscal_year_end, tax_rate,
                   is_active, is_default, timezone, locale, date_format, time_format,
                   logo_path, notes, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM companies
            WHERE id = ?
        """, (company_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_company(row)
    
    def get_company_by_code(self, code: str) -> Optional[Company]:
        """الحصول على شركة بالرمز"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, code, name, name_en, legal_name, tax_id, registration_number,
                   address, city, state, country, postal_code, phone, phone2, email, website,
                   base_currency_id, fiscal_year_start, fiscal_year_end, tax_rate,
                   is_active, is_default, timezone, locale, date_format, time_format,
                   logo_path, notes, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM companies
            WHERE code = ?
        """, (code,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_company(row)
    
    def get_default_company(self) -> Optional[Company]:
        """الحصول على الشركة الافتراضية"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, code, name, name_en, legal_name, tax_id, registration_number,
                   address, city, state, country, postal_code, phone, phone2, email, website,
                   base_currency_id, fiscal_year_start, fiscal_year_end, tax_rate,
                   is_active, is_default, timezone, locale, date_format, time_format,
                   logo_path, notes, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM companies
            WHERE is_default = 1 AND is_active = 1
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_company(row)
    
    def get_all_companies(self, active_only: bool = True) -> List[Company]:
        """الحصول على جميع الشركات"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, code, name, name_en, legal_name, tax_id, registration_number,
                   address, city, state, country, postal_code, phone, phone2, email, website,
                   base_currency_id, fiscal_year_start, fiscal_year_end, tax_rate,
                   is_active, is_default, timezone, locale, date_format, time_format,
                   logo_path, notes, metadata,
                   created_at, updated_at, created_by, updated_by
            FROM companies
        """
        
        if active_only:
            query += " WHERE is_active = 1"
        
        query += " ORDER BY is_default DESC, name ASC"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        return [self._row_to_company(row) for row in rows]
    
    def add_company(self, company: Company) -> int:
        """إضافة شركة جديدة"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # إذا كانت هذه الشركة هي الافتراضية، إلغاء الافتراضية من الشركات الأخرى
        if company.is_default:
            cursor.execute("UPDATE companies SET is_default = 0 WHERE is_default = 1")
        
        cursor.execute("""
            INSERT INTO companies (
                code, name, name_en, legal_name, tax_id, registration_number,
                address, city, state, country, postal_code, phone, phone2, email, website,
                base_currency_id, fiscal_year_start, fiscal_year_end, tax_rate,
                is_active, is_default, timezone, locale, date_format, time_format,
                logo_path, notes, metadata,
                created_at, updated_at, created_by, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company.code, company.name, company.name_en, company.legal_name,
            company.tax_id, company.registration_number,
            company.address, company.city, company.state, company.country,
            company.postal_code, company.phone, company.phone2, company.email, company.website,
            company.base_currency_id, company.fiscal_year_start, company.fiscal_year_end,
            float(company.tax_rate),
            1 if company.is_active else 0, 1 if company.is_default else 0,
            company.timezone, company.locale, company.date_format, company.time_format,
            company.logo_path, company.notes, company.metadata,
            datetime.now(), datetime.now(), company.created_by, company.updated_by
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def update_company(self, company: Company) -> bool:
        """تحديث شركة موجودة"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # إذا كانت هذه الشركة هي الافتراضية، إلغاء الافتراضية من الشركات الأخرى
        if company.is_default:
            cursor.execute("UPDATE companies SET is_default = 0 WHERE is_default = 1 AND id != ?", (company.id,))
        
        cursor.execute("""
            UPDATE companies SET
                code = ?, name = ?, name_en = ?, legal_name = ?, tax_id = ?, registration_number = ?,
                address = ?, city = ?, state = ?, country = ?, postal_code = ?, phone = ?, phone2 = ?, email = ?, website = ?,
                base_currency_id = ?, fiscal_year_start = ?, fiscal_year_end = ?, tax_rate = ?,
                is_active = ?, is_default = ?, timezone = ?, locale = ?, date_format = ?, time_format = ?,
                logo_path = ?, notes = ?, metadata = ?,
                updated_at = ?, updated_by = ?
            WHERE id = ?
        """, (
            company.code, company.name, company.name_en, company.legal_name,
            company.tax_id, company.registration_number,
            company.address, company.city, company.state, company.country,
            company.postal_code, company.phone, company.phone2, company.email, company.website,
            company.base_currency_id, company.fiscal_year_start, company.fiscal_year_end,
            float(company.tax_rate),
            1 if company.is_active else 0, 1 if company.is_default else 0,
            company.timezone, company.locale, company.date_format, company.time_format,
            company.logo_path, company.notes, company.metadata,
            datetime.now(), company.updated_by,
            company.id
        ))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def delete_company(self, company_id: int) -> bool:
        """حذف شركة (لا يمكن حذف الشركة الافتراضية)"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # التحقق من أن الشركة ليست الافتراضية
        cursor.execute("SELECT is_default FROM companies WHERE id = ?", (company_id,))
        row = cursor.fetchone()
        if row and row[0]:
            raise ValueError("لا يمكن حذف الشركة الافتراضية")
        
        cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def get_user_companies(self, user_id: int) -> List[UserCompany]:
        """الحصول على شركات المستخدم"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, company_id, is_default, is_active, role, permissions,
                   created_at, updated_at
            FROM user_companies
            WHERE user_id = ? AND is_active = 1
            ORDER BY is_default DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        return [self._row_to_user_company(row) for row in rows]
    
    def add_user_company(self, user_company: UserCompany) -> int:
        """ربط مستخدم بشركة"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # إذا كانت هذه الشركة هي الافتراضية للمستخدم، إلغاء الافتراضية من الشركات الأخرى
        if user_company.is_default:
            cursor.execute("""
                UPDATE user_companies 
                SET is_default = 0 
                WHERE user_id = ? AND is_default = 1
            """, (user_company.user_id,))
        
        cursor.execute("""
            INSERT INTO user_companies (
                user_id, company_id, is_default, is_active, role, permissions,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_company.user_id, user_company.company_id,
            1 if user_company.is_default else 0,
            1 if user_company.is_active else 0,
            user_company.role, user_company.permissions,
            datetime.now(), datetime.now()
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def remove_user_company(self, user_id: int, company_id: int) -> bool:
        """إلغاء ربط مستخدم بشركة"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM user_companies 
            WHERE user_id = ? AND company_id = ?
        """, (user_id, company_id))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def _row_to_company(self, row) -> Company:
        """تحويل صف قاعدة البيانات إلى Company"""
        fiscal_year_start = None
        fiscal_year_end = None
        if row[17]:  # fiscal_year_start
            if isinstance(row[17], str):
                fiscal_year_start = date.fromisoformat(row[17])
            else:
                fiscal_year_start = row[17]
        if row[18]:  # fiscal_year_end
            if isinstance(row[18], str):
                fiscal_year_end = date.fromisoformat(row[18])
            else:
                fiscal_year_end = row[18]
        
        return Company(
            id=row[0],
            code=row[1] or "",
            name=row[2] or "",
            name_en=row[3] or "",
            legal_name=row[4] or "",
            tax_id=row[5] or "",
            registration_number=row[6] or "",
            address=row[7] or "",
            city=row[8] or "",
            state=row[9] or "",
            country=row[10] or "الجزائر",
            postal_code=row[11] or "",
            phone=row[12] or "",
            phone2=row[13] or "",
            email=row[14] or "",
            website=row[15] or "",
            base_currency_id=row[16],
            fiscal_year_start=fiscal_year_start,
            fiscal_year_end=fiscal_year_end,
            tax_rate=Decimal(str(row[19] or 19.00)),
            is_active=bool(row[20]),
            is_default=bool(row[21]),
            timezone=row[22] or "Africa/Algiers",
            locale=row[23] or "ar_DZ",
            date_format=row[24] or "YYYY-MM-DD",
            time_format=row[25] or "HH:mm:ss",
            logo_path=row[26] or "",
            notes=row[27] or "",
            metadata=row[28] or "",
            created_at=datetime.fromisoformat(row[29]) if row[29] else None,
            updated_at=datetime.fromisoformat(row[30]) if row[30] else None,
            created_by=row[31],
            updated_by=row[32]
        )
    
    def _row_to_user_company(self, row) -> UserCompany:
        """تحويل صف قاعدة البيانات إلى UserCompany"""
        return UserCompany(
            id=row[0],
            user_id=row[1],
            company_id=row[2],
            is_default=bool(row[3]),
            is_active=bool(row[4]),
            role=row[5] or "",
            permissions=row[6] or "",
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None
        )

