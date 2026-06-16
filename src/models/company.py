import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج الشركات - Company Model
يحتوي على جميع العمليات المتعلقة بالشركات
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager


@dataclass
class Company:
    """نموذج بيانات الشركة"""

    id: Optional[int] = None
    code: str = ""  # رمز الشركة
    name: str = ""  # اسم الشركة
    name_en: str = ""  # الاسم بالإنجليزية
    legal_name: str = ""  # الاسم القانوني
    tax_id: str = ""  # الرقم الضريبي
    registration_number: str = ""  # رقم التسجيل التجاري

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
    base_currency_id: Optional[int] = None  # العملة الأساسية
    fiscal_year_start: Optional[date] = None  # بداية السنة المالية
    fiscal_year_end: Optional[date] = None  # نهاية السنة المالية
    tax_rate: Decimal = Decimal("19.00")  # معدل الضريبة الافتراضي

    # إعدادات
    is_active: bool = True  # نشط/غير نشط
    is_default: bool = False  # الشركة الافتراضية
    timezone: str = "Africa/Algiers"  # المنطقة الزمنية
    locale: str = "ar_DZ"  # اللغة/المنطقة
    date_format: str = "YYYY-MM-DD"  # تنسيق التاريخ
    time_format: str = "HH:mm:ss"  # تنسيق الوقت

    # معلومات إضافية
    logo_path: str = ""
    notes: str = ""
    metadata: str = ""  # بيانات إضافية (JSON)

    # الطوابع الزمنية
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "name_en": self.name_en,
            "legal_name": self.legal_name,
            "tax_id": self.tax_id,
            "registration_number": self.registration_number,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "phone": self.phone,
            "phone2": self.phone2,
            "email": self.email,
            "website": self.website,
            "base_currency_id": self.base_currency_id,
            "fiscal_year_start": (self.fiscal_year_start.isoformat() if self.fiscal_year_start else None),
            "fiscal_year_end": (self.fiscal_year_end.isoformat() if self.fiscal_year_end else None),
            "tax_rate": float(self.tax_rate),
            "is_active": 1 if self.is_active else 0,
            "is_default": 1 if self.is_default else 0,
            "timezone": self.timezone,
            "locale": self.locale,
            "date_format": self.date_format,
            "time_format": self.time_format,
            "logo_path": self.logo_path,
            "notes": self.notes,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Company":
        """إنشاء من قاموس"""
        fiscal_year_start = None
        fiscal_year_end = None
        if data.get("fiscal_year_start"):
            if isinstance(data["fiscal_year_start"], str):
                fiscal_year_start = date.fromisoformat(data["fiscal_year_start"])
            else:
                fiscal_year_start = data["fiscal_year_start"]
        if data.get("fiscal_year_end"):
            if isinstance(data["fiscal_year_end"], str):
                fiscal_year_end = date.fromisoformat(data["fiscal_year_end"])
            else:
                fiscal_year_end = data["fiscal_year_end"]

        return cls(
            id=data.get("id"),
            code=data.get("code", ""),
            name=data.get("name", ""),
            name_en=data.get("name_en", ""),
            legal_name=data.get("legal_name", ""),
            tax_id=data.get("tax_id", ""),
            registration_number=data.get("registration_number", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            country=data.get("country", "الجزائر"),
            postal_code=data.get("postal_code", ""),
            phone=data.get("phone", ""),
            phone2=data.get("phone2", ""),
            email=data.get("email", ""),
            website=data.get("website", ""),
            base_currency_id=data.get("base_currency_id"),
            fiscal_year_start=fiscal_year_start,
            fiscal_year_end=fiscal_year_end,
            tax_rate=Decimal(str(data.get("tax_rate", 19.00))),
            is_active=bool(data.get("is_active", 1)),
            is_default=bool(data.get("is_default", 0)),
            timezone=data.get("timezone", "Africa/Algiers"),
            locale=data.get("locale", "ar_DZ"),
            date_format=data.get("date_format", "YYYY-MM-DD"),
            time_format=data.get("time_format", "HH:mm:ss"),
            logo_path=data.get("logo_path", ""),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", ""),
            created_at=(datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None),
            updated_at=(datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
        )


@dataclass
class UserCompany:
    """نموذج بيانات ربط المستخدم بالشركة"""

    id: Optional[int] = None
    user_id: int = 0
    company_id: int = 0
    is_default: bool = False  # الشركة الافتراضية للمستخدم
    is_active: bool = True  # نشط/غير نشط
    role: str = ""  # دور المستخدم في هذه الشركة
    permissions: str = ""  # الصلاحيات الخاصة (JSON)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "is_default": 1 if self.is_default else 0,
            "is_active": 1 if self.is_active else 0,
            "role": self.role,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CompanyManager:
    """مدير الشركات"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger

    def get_company(self, company_id: int) -> Optional[Company]:
        """الحصول على شركة بالمعرف"""
        try:
            query = """
                SELECT * FROM companies WHERE id = ?
            """
            row = self.db_manager.fetch_one(query, (company_id,))
            return self._row_to_company(row) if row else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting company {company_id}: {e}")
            return None

    def get_company_by_code(self, code: str) -> Optional[Company]:
        """الحصول على شركة بالرمز"""
        try:
            query = """
                SELECT * FROM companies WHERE code = ?
            """
            row = self.db_manager.fetch_one(query, (code,))
            return self._row_to_company(row) if row else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting company by code {code}: {e}")
            return None

    def get_default_company(self) -> Optional[Company]:
        """الحصول على الشركة الافتراضية"""
        try:
            query = """
                SELECT * FROM companies WHERE is_default = 1 AND is_active = 1 LIMIT 1
            """
            row = self.db_manager.fetch_one(query)
            return self._row_to_company(row) if row else None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting default company: {e}")
            return None

    def get_all_companies(self, active_only: bool = True) -> List[Company]:
        """الحصول على جميع الشركات"""
        try:
            query = "SELECT * FROM companies"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY is_default DESC, name ASC"

            rows = self.db_manager.fetch_all(query)
            return [self._row_to_company(row) for row in rows]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting all companies: {e}")
            return []

    def add_company(self, company: Company) -> Optional[int]:
        """إضافة شركة جديدة"""
        try:
            # إذا كانت هذه الشركة هي الافتراضية، إلغاء الافتراضية من الشركات الأخرى
            if company.is_default:
                self.db_manager.execute_non_query("UPDATE companies SET is_default = 0 WHERE is_default = 1")

            query = """
                INSERT INTO companies (
                    code, name, name_en, legal_name, tax_id, registration_number,
                    address, city, state, country, postal_code, phone, phone2, email, website,
                    base_currency_id, fiscal_year_start, fiscal_year_end, tax_rate,
                    is_active, is_default, timezone, locale, date_format, time_format,
                    logo_path, notes, metadata,
                    created_at, updated_at, created_by, updated_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  # noqa: E501
            """
            params = (
                company.code,
                company.name,
                company.name_en,
                company.legal_name,
                company.tax_id,
                company.registration_number,
                company.address,
                company.city,
                company.state,
                company.country,
                company.postal_code,
                company.phone,
                company.phone2,
                company.email,
                company.website,
                company.base_currency_id,
                company.fiscal_year_start,
                company.fiscal_year_end,
                float(company.tax_rate),
                1 if company.is_active else 0,
                1 if company.is_default else 0,
                company.timezone,
                company.locale,
                company.date_format,
                company.time_format,
                company.logo_path,
                company.notes,
                company.metadata,
                datetime.now(),
                datetime.now(),
                company.created_by,
                company.updated_by,
            )
            return self.db_manager.execute_insert(query, params)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adding company: {e}")
            return None

    def update_company(self, company: Company) -> bool:
        """تحديث شركة موجودة"""
        try:
            # إذا كانت هذه الشركة هي الافتراضية، إلغاء الافتراضية من الشركات الأخرى
            if company.is_default:
                self.db_manager.execute_non_query(
                    "UPDATE companies SET is_default = 0 WHERE is_default = 1 AND id != ?",
                    (company.id,),
                )

            query = """
                UPDATE companies SET
                    code = ?, name = ?, name_en = ?, legal_name = ?, tax_id = ?, registration_number = ?,
                    address = ?, city = ?, state = ?, country = ?, postal_code = ?, phone = ?, phone2 = ?, email = ?, website = ?,  # noqa: E501
                    base_currency_id = ?, fiscal_year_start = ?, fiscal_year_end = ?, tax_rate = ?,
                    is_active = ?, is_default = ?, timezone = ?, locale = ?, date_format = ?, time_format = ?,
                    logo_path = ?, notes = ?, metadata = ?,
                    updated_at = ?, updated_by = ?
                WHERE id = ?
            """
            params = (
                company.code,
                company.name,
                company.name_en,
                company.legal_name,
                company.tax_id,
                company.registration_number,
                company.address,
                company.city,
                company.state,
                company.country,
                company.postal_code,
                company.phone,
                company.phone2,
                company.email,
                company.website,
                company.base_currency_id,
                company.fiscal_year_start,
                company.fiscal_year_end,
                float(company.tax_rate),
                1 if company.is_active else 0,
                1 if company.is_default else 0,
                company.timezone,
                company.locale,
                company.date_format,
                company.time_format,
                company.logo_path,
                company.notes,
                company.metadata,
                datetime.now(),
                company.updated_by,
                company.id,
            )
            result = self.db_manager.execute_non_query(query, params)
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating company {company.id}: {e}")
            return False

    def delete_company(self, company_id: int) -> bool:
        """حذف شركة (لا يمكن حذف الشركة الافتراضية)"""
        try:
            # التحقق من أن الشركة ليست الافتراضية
            company = self.get_company(company_id)
            if not company:
                return False
            if company.is_default:
                raise ValueError("لا يمكن حذف الشركة الافتراضية")

            result = self.db_manager.execute_non_query("DELETE FROM companies WHERE id = ?", (company_id,))
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting company {company_id}: {e}")
            return False

    def get_user_companies(self, user_id: int) -> List[UserCompany]:
        """الحصول على شركات المستخدم"""
        try:
            query = """
                SELECT * FROM user_companies
                WHERE user_id = ? AND is_active = 1
                ORDER BY is_default DESC
            """
            rows = self.db_manager.fetch_all(query, (user_id,))
            return [self._row_to_user_company(row) for row in rows]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting user companies for user {user_id}: {e}")
            return []

    def add_user_company(self, user_company: UserCompany) -> Optional[int]:
        """ربط مستخدم بشركة"""
        try:
            # إذا كانت هذه الشركة هي الافتراضية للمستخدم، إلغاء الافتراضية من الشركات الأخرى
            if user_company.is_default:
                self.db_manager.execute_non_query(
                    """
                    UPDATE user_companies
                    SET is_default = 0
                    WHERE user_id = ? AND is_default = 1
                """,
                    (user_company.user_id,),
                )

            query = """
                INSERT INTO user_companies (
                    user_id, company_id, is_default, is_active, role, permissions,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                user_company.user_id,
                user_company.company_id,
                1 if user_company.is_default else 0,
                1 if user_company.is_active else 0,
                user_company.role,
                user_company.permissions,
                datetime.now(),
                datetime.now(),
            )
            return self.db_manager.execute_insert(query, params)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adding user company: {e}")
            return None

    def remove_user_company(self, user_id: int, company_id: int) -> bool:
        """إلغاء ربط مستخدم بشركة"""
        try:
            result = self.db_manager.execute_non_query(
                """
                DELETE FROM user_companies
                WHERE user_id = ? AND company_id = ?
            """,
                (user_id, company_id),
            )
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error removing user company: {e}")
            return False

    def _row_to_company(self, row) -> Optional[Company]:
        """تحويل صف قاعدة البيانات إلى Company"""
        if not row:
            return None
        try:
            is_dict = isinstance(row, dict)

            def get_val(key, idx, default=None):
                if is_dict:
                    return row.get(key, default)
                return row[idx] if len(row) > idx else default

            return Company(
                id=get_val("id", 0),
                code=get_val("code", 1, ""),
                name=get_val("name", 2, ""),
                name_en=get_val("name_en", 3, ""),
                legal_name=get_val("legal_name", 4, ""),
                tax_id=get_val("tax_id", 5, ""),
                registration_number=get_val("registration_number", 6, ""),
                address=get_val("address", 7, ""),
                city=get_val("city", 8, ""),
                state=get_val("state", 9, ""),
                country=get_val("country", 10, "الجزائر"),
                postal_code=get_val("postal_code", 11, ""),
                phone=get_val("phone", 12, ""),
                phone2=get_val("phone2", 13, ""),
                email=get_val("email", 14, ""),
                website=get_val("website", 15, ""),
                base_currency_id=get_val("base_currency_id", 16),
                fiscal_year_start=self._parse_date(get_val("fiscal_year_start", 17)),
                fiscal_year_end=self._parse_date(get_val("fiscal_year_end", 18)),
                tax_rate=Decimal(str(get_val("tax_rate", 19, 19.00))),
                is_active=bool(get_val("is_active", 20)),
                is_default=bool(get_val("is_default", 21)),
                timezone=get_val("timezone", 22, "Africa/Algiers"),
                locale=get_val("locale", 23, "ar_DZ"),
                date_format=get_val("date_format", 24, "YYYY-MM-DD"),
                time_format=get_val("time_format", 25, "HH:mm:ss"),
                logo_path=get_val("logo_path", 26, ""),
                notes=get_val("notes", 27, ""),
                metadata=get_val("metadata", 28, ""),
                created_at=self._parse_datetime(get_val("created_at", 29)),
                updated_at=self._parse_datetime(get_val("updated_at", 30)),
                created_by=get_val("created_by", 31),
                updated_by=get_val("updated_by", 32),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error mapping company: {e}")
            return None

    def _row_to_user_company(self, row) -> Optional[UserCompany]:
        """تحويل صف قاعدة البيانات إلى UserCompany"""
        if not row:
            return None
        try:
            is_dict = isinstance(row, dict)

            def get_val(key, idx, default=None):
                if is_dict:
                    return row.get(key, default)
                return row[idx] if len(row) > idx else default

            return UserCompany(
                id=get_val("id", 0),
                user_id=get_val("user_id", 1),
                company_id=get_val("company_id", 2),
                is_default=bool(get_val("is_default", 3)),
                is_active=bool(get_val("is_active", 4)),
                role=get_val("role", 5, ""),
                permissions=get_val("permissions", 6, ""),
                created_at=self._parse_datetime(get_val("created_at", 7)),
                updated_at=self._parse_datetime(get_val("updated_at", 8)),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error mapping user company: {e}")
            return None

    def _parse_datetime(self, val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            return None

    def _parse_date(self, val):
        if not val:
            return None
        if isinstance(val, date):
            return val
        try:
            return date.fromisoformat(str(val))
        except Exception:
            return None
