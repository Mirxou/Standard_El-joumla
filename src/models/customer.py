#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج العميل - Customer Model
يحتوي على جميع العمليات المتعلقة بالعملاء
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

@dataclass
class Customer:
    """نموذج بيانات العميل"""
    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "الجزائر"
    tax_number: Optional[str] = None
    credit_limit: Decimal = Decimal('0.00')
    current_balance: Decimal = Decimal('0.00')
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_purchase_date: Optional[date] = None
    total_purchases: Decimal = Decimal('0.00')
    purchases_count: int = 0
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        for field in ['credit_limit', 'current_balance', 'total_purchases']:
            value = getattr(self, field)
            if isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))
    
    @property
    def available_credit(self) -> Decimal:
        """الائتمان المتاح"""
        return self.credit_limit - self.current_balance
    
    @property
    def is_credit_exceeded(self) -> bool:
        """هل تم تجاوز حد الائتمان؟"""
        return self.current_balance > self.credit_limit
    
    @property
    def full_address(self) -> str:
        """العنوان الكامل"""
        parts = [self.address, self.city, self.country]
        return ", ".join([part for part in parts if part])
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'phone': self.phone,
            'phone2': self.phone2,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'tax_number': self.tax_number,
            'credit_limit': float(self.credit_limit),
            'current_balance': float(self.current_balance),
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_purchase_date': self.last_purchase_date.isoformat() if self.last_purchase_date else None,
            'total_purchases': float(self.total_purchases),
            'purchases_count': self.purchases_count,
            'available_credit': float(self.available_credit),
            'is_credit_exceeded': self.is_credit_exceeded,
            'full_address': self.full_address
        }

class CustomerManager:
    """مدير العملاء"""
    
    # القائمة الذهبية: ترتيب ثابت للأعمدة نلتزم به في القراءة والكتابة
    DB_COLUMNS = [
        'id', 'name', 'name_en', 'phone', 'phone2', 'email', 
        'address', 'city', 'country', 'tax_number', 
        'credit_limit', 'current_balance', 'notes', 'is_active', 
        'created_at', 'updated_at'
    ]
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self._available_columns = None  # سيتم التخزين المؤقت للأعمدة المتاحة
        # Multi-Company Support
        self._tenant_manager = None
    
    @property
    def tenant_manager(self):
        """Lazy loading لـ TenantIsolationManager"""
        if self._tenant_manager is None:
            try:
                from src.core.tenant_isolation import TenantIsolationManager
                self._tenant_manager = TenantIsolationManager(self.db_manager)
            except ImportError:
                if self.logger:
                    self.logger.warning("TenantIsolationManager غير متاح - Multi-Company غير مفعل")
        return self._tenant_manager
    
    def _get_company_id(self) -> Optional[int]:
        """الحصول على معرف الشركة الحالية"""
        if self.tenant_manager:
            return self.tenant_manager.get_current_company_id()
        return None
    
    def _add_company_filter(self, query: str, params: list, company_id: Optional[int] = None) -> tuple:
        """إضافة فلتر الشركة إلى الاستعلام"""
        if company_id is None:
            company_id = self._get_company_id()
        
        if company_id is not None:
            if "WHERE" in query.upper():
                query += " AND company_id = ?"
            else:
                query += " WHERE company_id = ?"
            params.append(company_id)
        
        return query, params
    
    def _get_available_columns(self) -> List[str]:
        """الحصول على الأعمدة المتاحة في جدول customers مع التخزين المؤقت"""
        if self._available_columns is None:
            try:
                table_info = self.db_manager.fetch_all("PRAGMA table_info(customers)")
                self._available_columns = [row[1] for row in table_info] if table_info else []
            except Exception:
                # في حالة الخطأ، نستخدم الأعمدة الأساسية فقط
                self._available_columns = ['id', 'name', 'phone', 'email', 'address', 
                                          'credit_limit', 'current_balance', 'is_active', 
                                          'created_at', 'updated_at']
        return self._available_columns
    
    def _get_select_columns(self) -> List[str]:
        """الحصول على قائمة الأعمدة المتاحة فقط من DB_COLUMNS"""
        available = set(self._get_available_columns())
        return [col for col in self.DB_COLUMNS if col in available]
    
    def create_customer(self, customer: Customer) -> Optional[int]:
        """إنشاء عميل جديد"""
        try:
            # بناء الاستعلام ديناميكياً بناءً على الأعمدة الموجودة
            columns = ['name', 'phone', 'email', 'address', 'credit_limit', 'current_balance', 'is_active', 'created_at', 'updated_at']
            placeholders = ['?'] * len(columns)
            
            now = datetime.now()
            params = [
                customer.name,
                customer.phone,
                customer.email,
                customer.address,
                float(customer.credit_limit),
                float(customer.current_balance),
                customer.is_active,
                now,
                now
            ]
            
            # محاولة إضافة الأعمدة الاختيارية إذا كانت موجودة
            try:
                table_info = self.db_manager.fetch_all("PRAGMA table_info(customers)")
                available_columns = {row[1] for row in table_info} if table_info else set()
                
                optional_fields = [
                    ('name_en', customer.name_en),
                    ('phone2', customer.phone2),
                    ('city', customer.city),
                    ('country', customer.country),
                    ('tax_number', customer.tax_number),
                    ('notes', customer.notes)
                ]
                
                for col_name, col_value in optional_fields:
                    if col_name in available_columns:
                        columns.append(col_name)
                        placeholders.append('?')
                        params.append(col_value)
            except Exception:
                pass
            
            query = f"""
            INSERT INTO customers ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            """
            
            # استخدام execute_insert للحصول على lastrowid
            customer_id = self.db_manager.execute_insert(query, tuple(params))
            if customer_id:
                if self.logger:
                    self.logger.info(f"تم إنشاء عميل جديد: {customer.name} (ID: {customer_id})")
                
                # 🔔 إطلاق Webhook: إرسال Webhook عند إنشاء عميل
                try:
                    from ...services.webhook_service import WebhookService
                    webhook_service = WebhookService(self.db_manager, self.logger)
                    
                    # بناء Payload للـ Webhook
                    webhook_payload = {
                        "event": "customer_created",
                        "customer_id": customer_id,
                        "name": customer.name,
                        "phone": customer.phone,
                        "email": customer.email,
                        "created_at": datetime.now().isoformat(),
                        "customer": customer.to_dict() if hasattr(customer, 'to_dict') else {}
                    }
                    
                    webhook_service.trigger_webhook(
                        event_type="customer_created",
                        payload=webhook_payload,
                        entity_id=customer_id,
                        company_id=customer.company_id if hasattr(customer, 'company_id') else None
                    )
                    
                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق Webhook: customer_created (Customer ID: {customer_id})")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")
                
                return customer_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء العميل: {str(e)}")
            return None
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """الحصول على عميل بالمعرف - باستخدام التحديد الصريح"""
        try:
            # نطلب الأعمدة المتاحة فقط بالاسم وبالترتيب المحدد
            columns = self._get_select_columns()
            columns_str = ", ".join(columns)
            query = f"SELECT {columns_str} FROM customers WHERE id = ?"
            
            # استخدام fetch_one للحصول على صف واحد
            row = self.db_manager.fetch_one(query, (customer_id,))
            
            if row:
                # نحول الصف الأساسي إلى قاموس
                customer_data = self._map_row_to_dict(row, columns)
                
                # جلب البيانات الإضافية (المبيعات)
                self._enrich_with_sales_data(customer_id, customer_data)
                
                return self._dict_to_object(customer_data)
                
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العميل {customer_id}: {str(e)}")
            return None
    
    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """الحصول على عميل برقم الهاتف - باستخدام التحديد الصريح"""
        try:
            columns = self._get_select_columns()
            columns_str = ", ".join(columns)
            
            # التحقق من وجود عمود phone2 قبل استخدامه
            available_cols = set(self._get_available_columns())
            if 'phone2' in available_cols:
                query = f"SELECT {columns_str} FROM customers WHERE phone = ? OR phone2 = ?"
                params = (phone, phone)
            else:
                query = f"SELECT {columns_str} FROM customers WHERE phone = ?"
                params = (phone,)
            
            row = self.db_manager.fetch_one(query, params)
            
            if row:
                customer_data = self._map_row_to_dict(row, columns)
                customer_id = customer_data.get('id')
                
                # إضافة بيانات المبيعات
                self._enrich_with_sales_data(customer_id, customer_data)
                
                return self._dict_to_object(customer_data)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالهاتف {phone}: {str(e)}")
        
        return None
    
    def search_customers(self, search_term: str = "", active_only: bool = True) -> List[Customer]:
        """البحث في العملاء - باستخدام التحديد الصريح"""
        try:
            columns = self._get_select_columns()
            columns_str = ", ".join(columns)
            query = f"SELECT {columns_str} FROM customers WHERE 1=1"
            params = []
            
            if search_term:
                query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
                pattern = f"%{search_term}%"
                params.extend([pattern] * 3)
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY name"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            customers = []
            for row in rows:
                customer_data = self._map_row_to_dict(row, columns)
                customer_id = customer_data.get('id')
                
                # يمكن هنا إضافة بيانات المبيعات إذا تطلب الأمر (قد يبطئ البحث)
                # self._enrich_with_sales_data(customer_id, customer_data)
                
                # تعيين قيم افتراضية للمبيعات لتجنب الأخطاء
                customer_data.setdefault('last_purchase_date', None)
                customer_data.setdefault('total_purchases', 0)
                customer_data.setdefault('purchases_count', 0)
                
                customers.append(self._dict_to_object(customer_data))
                
            return customers
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث: {str(e)}")
            return []
    
    def get_all_customers(self, active_only: bool = True) -> List[Customer]:
        """الحصول على جميع العملاء"""
        return self.search_customers(active_only=active_only)
    
    def update_customer(self, customer: Customer) -> bool:
        """تحديث عميل"""
        try:
            # بناء الاستعلام ديناميكياً بناءً على الأعمدة الموجودة
            updates = ['name = ?', 'phone = ?', 'email = ?', 'address = ?', 
                      'credit_limit = ?', 'current_balance = ?', 'is_active = ?', 'updated_at = ?']
            params = [
                customer.name,
                customer.phone,
                customer.email,
                customer.address,
                float(customer.credit_limit),
                float(customer.current_balance),
                customer.is_active,
                datetime.now()
            ]
            
            # محاولة إضافة الأعمدة الاختيارية إذا كانت موجودة
            try:
                table_info = self.db_manager.fetch_all("PRAGMA table_info(customers)")
                available_columns = {row[1] for row in table_info} if table_info else set()
                
                optional_updates = [
                    ('name_en', customer.name_en),
                    ('phone2', customer.phone2),
                    ('city', customer.city),
                    ('country', customer.country),
                    ('tax_number', customer.tax_number),
                    ('notes', customer.notes)
                ]
                
                for col_name, col_value in optional_updates:
                    if col_name in available_columns:
                        updates.append(f'{col_name} = ?')
                        params.append(col_value)
            except Exception:
                pass
            
            query = f"""
            UPDATE customers SET {', '.join(updates)}
            WHERE id = ?
            """
            params.append(customer.id)
            
            result = self.db_manager.execute_non_query(query, tuple(params))
            return result > 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث العميل {customer.id}: {str(e)}")
            return False
    
    def delete_customer(self, customer_id: int) -> bool:
        """حذف عميل (soft delete)"""
        try:
            query = "UPDATE customers SET is_active = 0, updated_at = ? WHERE id = ?"
            result = self.db_manager.execute_non_query(query, (datetime.now(), customer_id))
            return result > 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف العميل {customer_id}: {str(e)}")
            return False
    
    def get_customers_with_balance(self) -> List[Customer]:
        """الحصول على العملاء ذوي الرصيد المستحق"""
        try:
            columns = self._get_select_columns()
            columns_str = ", ".join(columns)
            query = f"""
            SELECT {columns_str}
            FROM customers
            WHERE current_balance > 0 AND is_active = 1
            ORDER BY current_balance DESC
            """
            
            rows = self.db_manager.fetch_all(query)
            customers = []
            for row in rows:
                customer_data = self._map_row_to_dict(row, columns)
                customer_data.setdefault('last_purchase_date', None)
                customer_data.setdefault('total_purchases', 0)
                customer_data.setdefault('purchases_count', 0)
                customers.append(self._dict_to_object(customer_data))
            
            return customers
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العملاء ذوي الرصيد المستحق: {str(e)}")
            return []
    
    def get_top_customers(self, limit: int = 10) -> List[Customer]:
        """الحصول على أفضل العملاء حسب المبيعات"""
        try:
            columns = self._get_select_columns()
            columns_str = ", ".join(columns)
            query = f"""
            SELECT {columns_str}
            FROM customers
            WHERE is_active = 1
            ORDER BY credit_limit DESC
            LIMIT ?
            """
            
            rows = self.db_manager.fetch_all(query, (limit,))
            customers = []
            for row in rows:
                customer_data = self._map_row_to_dict(row, columns)
                customer_id = customer_data.get('id')
                self._enrich_with_sales_data(customer_id, customer_data)
                customers.append(self._dict_to_object(customer_data))
            
            # ترتيب حسب المبيعات
            customers.sort(key=lambda c: float(c.total_purchases), reverse=True)
            return customers[:limit]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على أفضل العملاء: {str(e)}")
            return []
    
    def get_customers_report(self) -> Dict[str, Any]:
        """تقرير العملاء"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_customers,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_customers,
                COUNT(CASE WHEN current_balance > 0 AND is_active = 1 THEN 1 END) as customers_with_balance,
                COUNT(CASE WHEN current_balance > credit_limit AND is_active = 1 THEN 1 END) as customers_over_limit,
                SUM(CASE WHEN is_active = 1 THEN current_balance ELSE 0 END) as total_outstanding_balance,
                AVG(CASE WHEN is_active = 1 THEN credit_limit ELSE NULL END) as avg_credit_limit
            FROM customers
            """
            
            result = self.db_manager.fetch_one(query)
            if result:
                return {
                    'total_customers': result[0] or 0,
                    'active_customers': result[1] or 0,
                    'customers_with_balance': result[2] or 0,
                    'customers_over_limit': result[3] or 0,
                    'total_outstanding_balance': float(result[4] or 0),
                    'avg_credit_limit': float(result[5] or 0)
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير العملاء: {str(e)}")
        
        return {
            'total_customers': 0,
            'active_customers': 0,
            'customers_with_balance': 0,
            'customers_over_limit': 0,
            'total_outstanding_balance': 0.0,
            'avg_credit_limit': 0.0
        }
    
    # --- دوال مساعدة (Helper Methods) لجعل الكود نظيفاً ---
    
    def _map_row_to_dict(self, row, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """تحويل الصف (Tuple) إلى قاموس بناءً على الترتيب الثابت"""
        if isinstance(row, dict):
            # إذا كان dict، نضيف القيم المفقودة من DB_COLUMNS
            result = dict(row)
            for col in self.DB_COLUMNS:
                if col not in result:
                    result[col] = None
            return result
        
        # استخدام الأعمدة المحددة أو DB_COLUMNS
        if columns is None:
            columns = self.DB_COLUMNS
        
        # الحل السحري: دمج أسماء الأعمدة مع القيم
        # zip يربط الاسم بالقيمة: id=row[0], name=row[1]...
        row_dict = {}
        for i, col_name in enumerate(columns):
            if i < len(row):
                row_dict[col_name] = row[i]
            else:
                row_dict[col_name] = None
        
        # إضافة القيم المفقودة من DB_COLUMNS كـ None
        for col in self.DB_COLUMNS:
            if col not in row_dict:
                row_dict[col] = None
        
        return row_dict
    
    def _enrich_with_sales_data(self, customer_id: int, customer_data: Dict[str, Any]):
        """إضافة بيانات المبيعات للقاموس"""
        try:
            sales_query = """
                SELECT MAX(sale_date), SUM(total_amount), COUNT(*)
                FROM sales 
                WHERE customer_id = ? AND status != 'ملغية'
            """
            sales_row = self.db_manager.fetch_one(sales_query, (customer_id,))
            
            if sales_row:
                # التعامل مع القيم التي قد تكون None
                customer_data['last_purchase_date'] = sales_row[0]
                customer_data['total_purchases'] = sales_row[1] or 0
                customer_data['purchases_count'] = sales_row[2] or 0
            else:
                customer_data['last_purchase_date'] = None
                customer_data['total_purchases'] = 0
                customer_data['purchases_count'] = 0
                
        except Exception:
            # قيم افتراضية في حالة الخطأ
            customer_data['last_purchase_date'] = None
            customer_data['total_purchases'] = 0
            customer_data['purchases_count'] = 0
    
    def _dict_to_object(self, data: Dict[str, Any]) -> Customer:
        """تحويل القاموس النهائي إلى كائن Customer"""
        return Customer(
            id=data.get('id'),
            name=data.get('name', ''),
            name_en=data.get('name_en'),
            phone=data.get('phone'),
            phone2=data.get('phone2'),
            email=data.get('email'),
            address=data.get('address'),
            city=data.get('city'),
            country=data.get('country', 'الجزائر'),
            tax_number=data.get('tax_number'),
            credit_limit=Decimal(str(data.get('credit_limit', 0))),
            current_balance=Decimal(str(data.get('current_balance', 0))),
            notes=data.get('notes'),
            is_active=bool(data.get('is_active', True)),
            # تحويل آمن للتواريخ
            created_at=self._parse_datetime(data.get('created_at')),
            updated_at=self._parse_datetime(data.get('updated_at')),
            last_purchase_date=self._parse_date(data.get('last_purchase_date')),
            total_purchases=Decimal(str(data.get('total_purchases', 0))),
            purchases_count=int(data.get('purchases_count', 0))
        )
    
    def _parse_datetime(self, val):
        """تحويل آمن للتاريخ والوقت"""
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except:
            return None
    
    def _parse_date(self, val):
        """تحويل آمن للتاريخ"""
        if not val:
            return None
        if isinstance(val, date):
            return val
        try:
            if isinstance(val, datetime):
                return val.date()
            return datetime.fromisoformat(str(val)).date()
        except:
            return None
    
    def _row_to_customer(self, row) -> Customer:
        """تحويل صف قاعدة البيانات إلى كائن عميل (للتوافق مع الكود القديم)"""
        # استخدام الدوال المساعدة الجديدة
        if isinstance(row, dict):
            return self._dict_to_object(row)
        else:
            customer_data = self._map_row_to_dict(row)
            return self._dict_to_object(customer_data)
