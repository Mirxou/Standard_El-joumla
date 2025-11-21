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
    country: str = "السعودية"
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
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def create_customer(self, customer: Customer) -> Optional[int]:
        """إنشاء عميل جديد"""
        try:
            query = """
            INSERT INTO customers (
                name, name_en, phone, phone2, email, address, city, country,
                tax_number, credit_limit, current_balance, notes, is_active,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                customer.name,
                customer.name_en,
                customer.phone,
                customer.phone2,
                customer.email,
                customer.address,
                customer.city,
                customer.country,
                customer.tax_number,
                float(customer.credit_limit),
                float(customer.current_balance),
                customer.notes,
                customer.is_active,
                now,
                now
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                customer_id = result.lastrowid
                if self.logger:
                    self.logger.info(f"تم إنشاء عميل جديد: {customer.name} (ID: {customer_id})")
                return customer_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء العميل: {str(e)}")
            return None
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """الحصول على عميل بالمعرف"""
        try:
            query = """
            SELECT c.*,
                   (SELECT MAX(sale_date) FROM sales WHERE customer_id = c.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as purchases_count
            FROM customers c
            WHERE c.id = ?
            """
            
            result = self.db_manager.fetch_one(query, (customer_id,))
            if result:
                return self._row_to_customer(result)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العميل {customer_id}: {str(e)}")
        
        return None
    
    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """الحصول على عميل برقم الهاتف"""
        try:
            query = """
            SELECT c.*,
                   (SELECT MAX(sale_date) FROM sales WHERE customer_id = c.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as purchases_count
            FROM customers c
            WHERE c.phone = ? OR c.phone2 = ?
            """
            
            result = self.db_manager.fetch_one(query, (phone, phone))
            if result:
                return self._row_to_customer(result)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالهاتف {phone}: {str(e)}")
        
        return None
    
    def search_customers(self, search_term: str = "", active_only: bool = True) -> List[Customer]:
        """البحث في العملاء"""
        try:
            # التحقق من الأعمدة المتاحة في جدول sales
            cols_info = self.db_manager.fetch_all("PRAGMA table_info(sales)")
            available_cols = {row[1] for row in cols_info} if cols_info else set()
            
            # بناء شروط الفلتر بناءً على الأعمدة المتاحة
            total_purchases_filter = ""
            purchases_count_filter = ""
            if "status" in available_cols:
                total_purchases_filter = "AND status != 'ملغية'"
                purchases_count_filter = "AND status != 'ملغية'"
            
            query = f"""
            SELECT c.*,
                   (SELECT MAX(sale_date) FROM sales WHERE customer_id = c.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM sales WHERE customer_id = c.id {total_purchases_filter}) as total_purchases,
                   (SELECT COUNT(*) FROM sales WHERE customer_id = c.id {purchases_count_filter}) as purchases_count
            FROM customers c
            WHERE 1=1
            """
            params = []
            
            if search_term:
                query += " AND (c.name LIKE ? OR c.name_en LIKE ? OR c.phone LIKE ? OR c.phone2 LIKE ? OR c.email LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern] * 5)
            
            if active_only:
                query += " AND c.is_active = 1"
            
            query += " ORDER BY c.name"
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_customer(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في العملاء: {str(e)}")
            return []
    
    def get_all_customers(self, active_only: bool = True) -> List[Customer]:
        """الحصول على جميع العملاء"""
        return self.search_customers(active_only=active_only)
    
    def update_customer(self, customer: Customer) -> bool:
        """تحديث عميل"""
        try:
            query = """
            UPDATE customers SET
                name = ?, name_en = ?, phone = ?, phone2 = ?, email = ?,
                address = ?, city = ?, country = ?, tax_number = ?,
                credit_limit = ?, current_balance = ?, notes = ?,
                is_active = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (
                customer.name,
                customer.name_en,
                customer.phone,
                customer.phone2,
                customer.email,
                customer.address,
                customer.city,
                customer.country,
                customer.tax_number,
                float(customer.credit_limit),
                float(customer.current_balance),
                customer.notes,
                customer.is_active,
                datetime.now(),
                customer.id
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث العميل: {customer.name} (ID: {customer.id})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث العميل {customer.id}: {str(e)}")
        
        return False
    
    def delete_customer(self, customer_id: int, soft_delete: bool = True) -> bool:
        """حذف عميل"""
        try:
            # التحقق من وجود مبيعات للعميل
            sales_count = self.get_customer_sales_count(customer_id)
            if sales_count > 0:
                if self.logger:
                    self.logger.warning(f"لا يمكن حذف العميل {customer_id} - يحتوي على {sales_count} فاتورة")
                return False
            
            if soft_delete:
                # حذف ناعم - تعطيل العميل فقط
                query = "UPDATE customers SET is_active = 0, updated_at = ? WHERE id = ?"
                params = (datetime.now(), customer_id)
            else:
                # حذف صلب - حذف نهائي
                query = "DELETE FROM customers WHERE id = ?"
                params = (customer_id,)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    action = "تعطيل" if soft_delete else "حذف"
                    self.logger.info(f"تم {action} العميل (ID: {customer_id})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف العميل {customer_id}: {str(e)}")
        
        return False
    
    def update_customer_balance(self, customer_id: int, amount_change: Decimal, 
                              operation_type: str = "manual") -> bool:
        """تحديث رصيد العميل"""
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False
            
            new_balance = customer.current_balance + amount_change
            
            query = "UPDATE customers SET current_balance = ?, updated_at = ? WHERE id = ?"
            params = (float(new_balance), datetime.now(), customer_id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث رصيد العميل {customer_id}: {amount_change:+} ({operation_type})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث رصيد العميل {customer_id}: {str(e)}")
        
        return False
    
    def get_customer_sales_count(self, customer_id: int) -> int:
        """الحصول على عدد فواتير العميل"""
        try:
            query = "SELECT COUNT(*) FROM sales WHERE customer_id = ? AND status != 'ملغية'"
            result = self.db_manager.fetch_one(query, (customer_id,))
            return result[0] if result else 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب فواتير العميل {customer_id}: {str(e)}")
            return 0
    
    def get_customer_sales_history(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على تاريخ مبيعات العميل"""
        try:
            query = """
            SELECT invoice_number, sale_date, total_amount, paid_amount, 
                   remaining_amount, status
            FROM sales
            WHERE customer_id = ? AND status != 'ملغية'
            ORDER BY sale_date DESC, id DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (customer_id, limit))
            return [
                {
                    'invoice_number': row[0],
                    'sale_date': row[1],
                    'total_amount': float(row[2]),
                    'paid_amount': float(row[3]),
                    'remaining_amount': float(row[4]),
                    'status': row[5]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على تاريخ مبيعات العميل {customer_id}: {str(e)}")
            return []
    
    def get_customers_with_outstanding_balance(self) -> List[Customer]:
        """الحصول على العملاء الذين لديهم رصيد مستحق"""
        try:
            query = """
            SELECT c.*,
                   (SELECT MAX(sale_date) FROM sales WHERE customer_id = c.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as purchases_count
            FROM customers c
            WHERE c.current_balance > 0 AND c.is_active = 1
            ORDER BY c.current_balance DESC
            """
            
            results = self.db_manager.fetch_all(query)
            return [self._row_to_customer(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العملاء ذوي الرصيد المستحق: {str(e)}")
            return []
    
    def get_top_customers(self, limit: int = 10) -> List[Customer]:
        """الحصول على أفضل العملاء حسب المبيعات"""
        try:
            query = """
            SELECT c.*,
                   (SELECT MAX(sale_date) FROM sales WHERE customer_id = c.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM sales WHERE customer_id = c.id AND status != 'ملغية') as purchases_count
            FROM customers c
            WHERE c.is_active = 1
            AND (SELECT COUNT(*) FROM sales WHERE customer_id = c.id AND status != 'ملغية') > 0
            ORDER BY (SELECT SUM(total_amount) FROM sales WHERE customer_id = c.id AND status != 'ملغية') DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (limit,))
            return [self._row_to_customer(row) for row in results]
            
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
    
    def _row_to_customer(self, row) -> Customer:
        """تحويل صف قاعدة البيانات إلى كائن عميل"""
        return Customer(
            id=row[0],
            name=row[1],
            name_en=row[2],
            phone=row[3],
            phone2=row[4],
            email=row[5],
            address=row[6],
            city=row[7],
            country=row[8],
            tax_number=row[9],
            credit_limit=Decimal(str(row[10])),
            current_balance=Decimal(str(row[11])),
            notes=row[12],
            is_active=bool(row[13]),
            created_at=datetime.fromisoformat(row[14]) if row[14] else None,
            updated_at=datetime.fromisoformat(row[15]) if row[15] else None,
            last_purchase_date=date.fromisoformat(row[16]) if row[16] else None,
            total_purchases=Decimal(str(row[17] or 0)),
            purchases_count=row[18] or 0
        )