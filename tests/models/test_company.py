#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج الشركات - Company Model Tests
"""

import unittest
from datetime import datetime, date
from decimal import Decimal
from src.models.company import Company, UserCompany


class TestCompanyCreation(unittest.TestCase):
    """اختبارات إنشاء الشركة"""
    
    def test_company_creation_default_values(self):
        """اختبار إنشاء شركة بالقيم الافتراضية"""
        company = Company()
        
        self.assertIsNone(company.id)
        self.assertEqual(company.code, "")
        self.assertEqual(company.name, "")
        self.assertTrue(company.is_active)
        self.assertFalse(company.is_default)
        self.assertEqual(company.country, "الجزائر")
        self.assertEqual(company.timezone, "Africa/Algiers")
        self.assertEqual(company.locale, "ar_DZ")
        self.assertEqual(company.tax_rate, Decimal('19.00'))
    
    def test_company_creation_with_values(self):
        """اختبار إنشاء شركة مع قيم"""
        company = Company(
            id=1,
            code="ABC",
            name="شركة ABC",
            name_en="ABC Company",
            tax_id="123456",
            email="info@abc.com"
        )
        
        self.assertEqual(company.id, 1)
        self.assertEqual(company.code, "ABC")
        self.assertEqual(company.name, "شركة ABC")
        self.assertEqual(company.name_en, "ABC Company")
        self.assertEqual(company.tax_id, "123456")
        self.assertEqual(company.email, "info@abc.com")
    
    def test_company_with_dates(self):
        """اختبار الشركة مع التواريخ"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        company = Company(
            name="Test Company",
            fiscal_year_start=start_date,
            fiscal_year_end=end_date
        )
        
        self.assertEqual(company.fiscal_year_start, start_date)
        self.assertEqual(company.fiscal_year_end, end_date)
    
    def test_company_is_default(self):
        """اختبار خاصية الشركة الافتراضية"""
        company = Company(
            name="Default Company",
            is_default=True
        )
        
        self.assertTrue(company.is_default)
    
    def test_company_is_inactive(self):
        """اختبار شركة غير نشطة"""
        company = Company(
            name="Inactive Company",
            is_active=False
        )
        
        self.assertFalse(company.is_active)


class TestCompanyLocation(unittest.TestCase):
    """اختبارات معلومات الموقع"""
    
    def test_company_address(self):
        """اختبار عنوان الشركة"""
        company = Company(
            address="شارع الاستقلال",
            city="الجزائر",
            state="ولاية الجزائر",
            country="الجزائر",
            postal_code="16000"
        )
        
        self.assertEqual(company.address, "شارع الاستقلال")
        self.assertEqual(company.city, "الجزائر")
        self.assertEqual(company.state, "ولاية الجزائر")
        self.assertEqual(company.postal_code, "16000")
    
    def test_company_contact(self):
        """اختبار بيانات الاتصال"""
        company = Company(
            phone="0123456789",
            phone2="0987654321",
            email="info@company.com",
            website="www.company.com"
        )
        
        self.assertEqual(company.phone, "0123456789")
        self.assertEqual(company.phone2, "0987654321")
        self.assertEqual(company.email, "info@company.com")
        self.assertEqual(company.website, "www.company.com")
    
    def test_company_international(self):
        """اختبار شركة دولية"""
        company = Company(
            name="International Company",
            country="فرنسا",
            timezone="Europe/Paris",
            locale="fr_FR"
        )
        
        self.assertEqual(company.country, "فرنسا")
        self.assertEqual(company.timezone, "Europe/Paris")
        self.assertEqual(company.locale, "fr_FR")


class TestCompanyFinancial(unittest.TestCase):
    """اختبارات المعلومات المالية"""
    
    def test_company_tax_rate(self):
        """اختبار معدل الضريبة"""
        company = Company(
            name="Test Company",
            tax_rate=Decimal('21.00')
        )
        
        self.assertEqual(company.tax_rate, Decimal('21.00'))
    
    def test_company_with_currency(self):
        """اختبار الشركة مع العملة"""
        company = Company(
            name="Multi Currency Company",
            base_currency_id=1
        )
        
        self.assertEqual(company.base_currency_id, 1)
    
    def test_company_fiscal_year(self):
        """اختبار السنة المالية"""
        start = date(2024, 4, 1)
        end = date(2025, 3, 31)
        
        company = Company(
            name="Test Company",
            fiscal_year_start=start,
            fiscal_year_end=end
        )
        
        self.assertEqual(company.fiscal_year_start, start)
        self.assertEqual(company.fiscal_year_end, end)


class TestCompanyMetadata(unittest.TestCase):
    """اختبارات بيانات الشركة الإضافية"""
    
    def test_company_metadata(self):
        """اختبار البيانات الوصفية"""
        company = Company(
            name="Test Company",
            metadata='{"key": "value"}'
        )
        
        self.assertEqual(company.metadata, '{"key": "value"}')
    
    def test_company_notes(self):
        """اختبار ملاحظات الشركة"""
        company = Company(
            name="Test Company",
            notes="هذه شركة تجريبية"
        )
        
        self.assertEqual(company.notes, "هذه شركة تجريبية")
    
    def test_company_logo(self):
        """اختبار شعار الشركة"""
        company = Company(
            name="Test Company",
            logo_path="/path/to/logo.png"
        )
        
        self.assertEqual(company.logo_path, "/path/to/logo.png")


class TestCompanyDateFormats(unittest.TestCase):
    """اختبارات تنسيقات التاريخ والوقت"""
    
    def test_default_date_format(self):
        """اختبار تنسيق التاريخ الافتراضي"""
        company = Company(name="Test")
        
        self.assertEqual(company.date_format, "YYYY-MM-DD")
        self.assertEqual(company.time_format, "HH:mm:ss")
    
    def test_custom_date_format(self):
        """اختبار تنسيق تاريخ مخصص"""
        company = Company(
            name="Test",
            date_format="DD/MM/YYYY",
            time_format="HH:mm"
        )
        
        self.assertEqual(company.date_format, "DD/MM/YYYY")
        self.assertEqual(company.time_format, "HH:mm")


class TestCompanyToDict(unittest.TestCase):
    """اختبارات تحويل الشركة إلى قاموس"""
    
    def test_company_to_dict_basic(self):
        """اختبار تحويل شركة أساسية إلى قاموس"""
        company = Company(
            id=1,
            code="ABC",
            name="Test Company",
            name_en="Test",
            tax_id="123456"
        )
        
        company_dict = company.to_dict()
        
        self.assertEqual(company_dict['id'], 1)
        self.assertEqual(company_dict['code'], "ABC")
        self.assertEqual(company_dict['name'], "Test Company")
        self.assertEqual(company_dict['name_en'], "Test")
        self.assertEqual(company_dict['tax_id'], "123456")
    
    def test_company_to_dict_with_dates(self):
        """اختبار تحويل شركة مع تواريخ إلى قاموس"""
        start_date = date(2024, 1, 1)
        created_at = datetime(2024, 1, 1, 10, 0, 0)
        
        company = Company(
            id=1,
            name="Test",
            fiscal_year_start=start_date,
            created_at=created_at
        )
        
        company_dict = company.to_dict()
        
        self.assertEqual(company_dict['fiscal_year_start'], "2024-01-01")
        self.assertIn("2024-01-01T10:00:00", company_dict['created_at'])
    
    def test_company_to_dict_boolean_conversion(self):
        """اختبار تحويل القيم المنطقية في القاموس"""
        company = Company(
            id=1,
            name="Test",
            is_active=True,
            is_default=False
        )
        
        company_dict = company.to_dict()
        
        self.assertEqual(company_dict['is_active'], 1)
        self.assertEqual(company_dict['is_default'], 0)


class TestCompanyFromDict(unittest.TestCase):
    """اختبارات إنشاء شركة من قاموس"""
    
    def test_company_from_dict_basic(self):
        """اختبار إنشاء شركة من قاموس أساسي"""
        data = {
            'id': 1,
            'code': 'ABC',
            'name': 'Test Company',
            'name_en': 'Test',
            'tax_id': '123456'
        }
        
        company = Company.from_dict(data)
        
        self.assertEqual(company.id, 1)
        self.assertEqual(company.code, 'ABC')
        self.assertEqual(company.name, 'Test Company')
        self.assertEqual(company.tax_id, '123456')
    
    def test_company_from_dict_with_dates(self):
        """اختبار إنشاء شركة من قاموس مع تواريخ"""
        data = {
            'id': 1,
            'name': 'Test',
            'fiscal_year_start': '2024-01-01',
            'fiscal_year_end': '2024-12-31',
            'created_at': '2024-01-01T10:00:00'
        }
        
        company = Company.from_dict(data)
        
        self.assertEqual(company.fiscal_year_start, date(2024, 1, 1))
        self.assertEqual(company.fiscal_year_end, date(2024, 12, 31))
        self.assertEqual(company.created_at, datetime(2024, 1, 1, 10, 0, 0))
    
    def test_company_from_dict_with_date_objects(self):
        """اختبار إنشاء شركة من قاموس مع كائنات التاريخ"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        data = {
            'id': 1,
            'name': 'Test',
            'fiscal_year_start': start_date,
            'fiscal_year_end': end_date
        }
        
        company = Company.from_dict(data)
        
        self.assertEqual(company.fiscal_year_start, start_date)
        self.assertEqual(company.fiscal_year_end, end_date)
    
    def test_company_from_dict_boolean_conversion(self):
        """اختبار تحويل القيم المنطقية من القاموس"""
        data = {
            'id': 1,
            'name': 'Test',
            'is_active': 1,
            'is_default': 0
        }
        
        company = Company.from_dict(data)
        
        self.assertTrue(company.is_active)
        self.assertFalse(company.is_default)
    
    def test_company_from_dict_missing_fields(self):
        """اختبار إنشاء شركة من قاموس ناقص"""
        data = {'id': 1, 'name': 'Test'}
        
        company = Company.from_dict(data)
        
        self.assertEqual(company.id, 1)
        self.assertEqual(company.name, 'Test')
        self.assertEqual(company.code, '')
        self.assertEqual(company.country, 'الجزائر')


class TestUserCompanyCreation(unittest.TestCase):
    """اختبارات إنشاء ربط المستخدم بالشركة"""
    
    def test_user_company_creation_basic(self):
        """اختبار إنشاء ربط أساسي"""
        user_company = UserCompany(
            id=1,
            user_id=1,
            company_id=1,
            role="admin"
        )
        
        self.assertEqual(user_company.id, 1)
        self.assertEqual(user_company.user_id, 1)
        self.assertEqual(user_company.company_id, 1)
        self.assertEqual(user_company.role, "admin")
    
    def test_user_company_default_values(self):
        """اختبار القيم الافتراضية"""
        user_company = UserCompany()
        
        self.assertIsNone(user_company.id)
        self.assertEqual(user_company.user_id, 0)
        self.assertEqual(user_company.company_id, 0)
        self.assertFalse(user_company.is_default)
        self.assertTrue(user_company.is_active)
    
    def test_user_company_is_default(self):
        """اختبار خاصية الشركة الافتراضية للمستخدم"""
        user_company = UserCompany(
            user_id=1,
            company_id=1,
            is_default=True
        )
        
        self.assertTrue(user_company.is_default)
    
    def test_user_company_permissions(self):
        """اختبار الصلاحيات الخاصة"""
        user_company = UserCompany(
            user_id=1,
            company_id=1,
            permissions='{"read": true, "write": false}'
        )
        
        self.assertEqual(user_company.permissions, '{"read": true, "write": false}')


class TestUserCompanyToDict(unittest.TestCase):
    """اختبارات تحويل ربط المستخدم بالشركة إلى قاموس"""
    
    def test_user_company_to_dict_basic(self):
        """اختبار التحويل الأساسي"""
        user_company = UserCompany(
            id=1,
            user_id=1,
            company_id=1,
            role="manager"
        )
        
        uc_dict = user_company.to_dict()
        
        self.assertEqual(uc_dict['id'], 1)
        self.assertEqual(uc_dict['user_id'], 1)
        self.assertEqual(uc_dict['company_id'], 1)
        self.assertEqual(uc_dict['role'], "manager")
    
    def test_user_company_to_dict_with_dates(self):
        """اختبار التحويل مع التواريخ"""
        created = datetime(2024, 1, 1, 10, 0, 0)
        user_company = UserCompany(
            id=1,
            user_id=1,
            company_id=1,
            created_at=created
        )
        
        uc_dict = user_company.to_dict()
        
        self.assertIn("2024-01-01T10:00:00", uc_dict['created_at'])
    
    def test_user_company_to_dict_boolean_conversion(self):
        """اختبار تحويل القيم المنطقية"""
        user_company = UserCompany(
            id=1,
            user_id=1,
            company_id=1,
            is_default=True,
            is_active=False
        )
        
        uc_dict = user_company.to_dict()
        
        self.assertEqual(uc_dict['is_default'], 1)
        self.assertEqual(uc_dict['is_active'], 0)


class TestCompanyEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""
    
    def test_company_empty_name(self):
        """اختبار شركة بدون اسم"""
        company = Company(id=1)
        
        self.assertEqual(company.name, "")
        self.assertEqual(company.id, 1)
    
    def test_company_special_characters(self):
        """اختبار الأحرف الخاصة والرموز"""
        company = Company(
            name="شركة ABC & XYZ",
            notes="ملاحظات مع رموز: !@#$%"
        )
        
        self.assertIn("ABC & XYZ", company.name)
        self.assertIn("!@#$%", company.notes)
    
    def test_company_very_long_name(self):
        """اختبار اسم طويل جداً"""
        long_name = "ا" * 500
        company = Company(name=long_name)
        
        self.assertEqual(len(company.name), 500)
        self.assertEqual(company.name, long_name)
    
    def test_company_null_dates(self):
        """اختبار القيم الفارغة للتواريخ"""
        company = Company(
            name="Test",
            fiscal_year_start=None,
            fiscal_year_end=None
        )
        
        self.assertIsNone(company.fiscal_year_start)
        self.assertIsNone(company.fiscal_year_end)
    
    def test_company_zero_tax_rate(self):
        """اختبار معدل ضريبة صفر"""
        company = Company(
            name="Test",
            tax_rate=Decimal('0.00')
        )
        
        self.assertEqual(company.tax_rate, Decimal('0.00'))
    
    def test_company_very_high_tax_rate(self):
        """اختبار معدل ضريبة عالي جداً"""
        company = Company(
            name="Test",
            tax_rate=Decimal('99.99')
        )
        
        self.assertEqual(company.tax_rate, Decimal('99.99'))
    
    def test_user_company_both_default_and_inactive(self):
        """اختبار ربط افتراضي وغير نشط في نفس الوقت"""
        user_company = UserCompany(
            user_id=1,
            company_id=1,
            is_default=True,
            is_active=False
        )
        
        self.assertTrue(user_company.is_default)
        self.assertFalse(user_company.is_active)
    
    def test_company_to_dict_null_dates(self):
        """اختبار تحويل شركة بدون تواريخ"""
        company = Company(
            id=1,
            name="Test",
            fiscal_year_start=None,
            created_at=None
        )
        
        company_dict = company.to_dict()
        
        self.assertIsNone(company_dict['fiscal_year_start'])
        self.assertIsNone(company_dict['created_at'])


class TestCompanyLegal(unittest.TestCase):
    """اختبارات البيانات القانونية"""
    
    def test_company_legal_name(self):
        """اختبار الاسم القانوني"""
        company = Company(
            name="شركة التجارة",
            legal_name="شركة التجارة والصناعات المحدودة"
        )
        
        self.assertEqual(company.legal_name, "شركة التجارة والصناعات المحدودة")
    
    def test_company_tax_id(self):
        """اختبار الرقم الضريبي"""
        company = Company(
            name="Test",
            tax_id="123456789"
        )
        
        self.assertEqual(company.tax_id, "123456789")
    
    def test_company_registration_number(self):
        """اختبار رقم التسجيل التجاري"""
        company = Company(
            name="Test",
            registration_number="RC12345"
        )
        
        self.assertEqual(company.registration_number, "RC12345")


if __name__ == '__main__':
    unittest.main()



