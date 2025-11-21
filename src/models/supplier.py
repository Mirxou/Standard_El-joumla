#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المورد - Supplier Model
يحتوي على جميع العمليات المتعلقة بالموردين
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
class Supplier:
    """نموذج بيانات المورد"""
    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "الجزائر"
    tax_number: Optional[str] = None
    commercial_register: Optional[str] = None
    payment_terms: str = "نقدي"  # نقدي، آجل 30 يوم، آجل 60 يوم
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
    
    @property
    def display_name(self) -> str:
        """الاسم للعرض"""
        if self.contact_person:
            return f"{self.name} ({self.contact_person})"
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'phone2': self.phone2,
            'email': self.email,
            'website': self.website,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'tax_number': self.tax_number,
            'commercial_register': self.commercial_register,
            'payment_terms': self.payment_terms,
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
            'full_address': self.full_address,
            'display_name': self.display_name
        }

class SupplierManager:
    """مدير الموردين"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def create_supplier(self, supplier: Supplier) -> Optional[int]:
        """إنشاء مورد جديد"""
        try:
            query = """
            INSERT INTO suppliers (
                name, name_en, contact_person, phone, phone2, email, website,
                address, city, country, tax_number, commercial_register,
                payment_terms, credit_limit, current_balance, notes, is_active,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                supplier.name,
                supplier.name_en,
                supplier.contact_person,
                supplier.phone,
                supplier.phone2,
                supplier.email,
                supplier.website,
                supplier.address,
                supplier.city,
                supplier.country,
                supplier.tax_number,
                supplier.commercial_register,
                supplier.payment_terms,
                float(supplier.credit_limit),
                float(supplier.current_balance),
                supplier.notes,
                supplier.is_active,
                now,
                now
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                supplier_id = result.lastrowid
                if self.logger:
                    self.logger.info(f"تم إنشاء مورد جديد: {supplier.name} (ID: {supplier_id})")
                return supplier_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء المورد: {str(e)}")
            return None
    
    def get_supplier_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """الحصول على مورد بالمعرف"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.id = ?
            """
            
            result = self.db_manager.fetch_one(query, (supplier_id,))
            if result:
                return self._row_to_supplier(result)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المورد {supplier_id}: {str(e)}")
        
        return None
    
    def get_supplier_by_name(self, name: str) -> Optional[Supplier]:
        """الحصول على مورد بالاسم"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.name = ? OR s.name_en = ?
            """
            
            result = self.db_manager.fetch_one(query, (name, name))
            if result:
                return self._row_to_supplier(result)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالاسم {name}: {str(e)}")
        
        return None
    
    def search_suppliers(self, search_term: str = "", active_only: bool = True) -> List[Supplier]:
        """البحث في الموردين"""
        try:
            # التحقق من الأعمدة المتاحة في جدول purchases
            cols_info = self.db_manager.fetch_all("PRAGMA table_info(purchases)")
            available_cols = {row[1] for row in cols_info} if cols_info else set()
            
            # بناء شروط الفلتر بناءً على الأعمدة المتاحة
            total_purchases_filter = ""
            purchases_count_filter = ""
            if "status" in available_cols:
                total_purchases_filter = "AND status != 'ملغية'"
                purchases_count_filter = "AND status != 'ملغية'"
            
            query = f"""
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id {total_purchases_filter}) as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id {purchases_count_filter}) as purchases_count
            FROM suppliers s
            WHERE 1=1
            """
            params = []
            
            if search_term:
                query += """ AND (s.name LIKE ? OR s.name_en LIKE ? OR s.contact_person LIKE ? 
                            OR s.phone LIKE ? OR s.phone2 LIKE ? OR s.email LIKE ?)"""
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern] * 6)
            
            if active_only:
                query += " AND s.is_active = 1"
            
            query += " ORDER BY s.name"
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_supplier(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في الموردين: {str(e)}")
            return []
    
    def get_all_suppliers(self, active_only: bool = True) -> List[Supplier]:
        """الحصول على جميع الموردين"""
        return self.search_suppliers(active_only=active_only)
    
    def update_supplier(self, supplier: Supplier) -> bool:
        """تحديث مورد"""
        try:
            query = """
            UPDATE suppliers SET
                name = ?, name_en = ?, contact_person = ?, phone = ?, phone2 = ?,
                email = ?, website = ?, address = ?, city = ?, country = ?,
                tax_number = ?, commercial_register = ?, payment_terms = ?,
                credit_limit = ?, current_balance = ?, notes = ?,
                is_active = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (
                supplier.name,
                supplier.name_en,
                supplier.contact_person,
                supplier.phone,
                supplier.phone2,
                supplier.email,
                supplier.website,
                supplier.address,
                supplier.city,
                supplier.country,
                supplier.tax_number,
                supplier.commercial_register,
                supplier.payment_terms,
                float(supplier.credit_limit),
                float(supplier.current_balance),
                supplier.notes,
                supplier.is_active,
                datetime.now(),
                supplier.id
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث المورد: {supplier.name} (ID: {supplier.id})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المورد {supplier.id}: {str(e)}")
        
        return False
    
    def delete_supplier(self, supplier_id: int, soft_delete: bool = True) -> bool:
        """حذف مورد"""
        try:
            # التحقق من وجود مشتريات للمورد
            purchases_count = self.get_supplier_purchases_count(supplier_id)
            if purchases_count > 0:
                if self.logger:
                    self.logger.warning(f"لا يمكن حذف المورد {supplier_id} - يحتوي على {purchases_count} فاتورة شراء")
                return False
            
            # التحقق من وجود منتجات مرتبطة بالمورد
            products_count = self.get_supplier_products_count(supplier_id)
            if products_count > 0:
                if self.logger:
                    self.logger.warning(f"لا يمكن حذف المورد {supplier_id} - يحتوي على {products_count} منتج")
                return False
            
            if soft_delete:
                # حذف ناعم - تعطيل المورد فقط
                query = "UPDATE suppliers SET is_active = 0, updated_at = ? WHERE id = ?"
                params = (datetime.now(), supplier_id)
            else:
                # حذف صلب - حذف نهائي
                query = "DELETE FROM suppliers WHERE id = ?"
                params = (supplier_id,)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    action = "تعطيل" if soft_delete else "حذف"
                    self.logger.info(f"تم {action} المورد (ID: {supplier_id})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المورد {supplier_id}: {str(e)}")
        
        return False
    
    def update_supplier_balance(self, supplier_id: int, amount_change: Decimal, 
                              operation_type: str = "manual") -> bool:
        """تحديث رصيد المورد"""
        try:
            supplier = self.get_supplier_by_id(supplier_id)
            if not supplier:
                return False
            
            new_balance = supplier.current_balance + amount_change
            
            query = "UPDATE suppliers SET current_balance = ?, updated_at = ? WHERE id = ?"
            params = (float(new_balance), datetime.now(), supplier_id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث رصيد المورد {supplier_id}: {amount_change:+} ({operation_type})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث رصيد المورد {supplier_id}: {str(e)}")
        
        return False
    
    def get_supplier_purchases_count(self, supplier_id: int) -> int:
        """الحصول على عدد فواتير الشراء للمورد"""
        try:
            query = "SELECT COUNT(*) FROM purchases WHERE supplier_id = ? AND status != 'ملغية'"
            result = self.db_manager.fetch_one(query, (supplier_id,))
            return result[0] if result else 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب فواتير المورد {supplier_id}: {str(e)}")
            return 0
    
    def get_supplier_products_count(self, supplier_id: int) -> int:
        """الحصول على عدد منتجات المورد"""
        try:
            query = "SELECT COUNT(*) FROM products WHERE supplier_id = ? AND is_active = 1"
            result = self.db_manager.fetch_one(query, (supplier_id,))
            return result[0] if result else 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب منتجات المورد {supplier_id}: {str(e)}")
            return 0
    
    def get_supplier_purchases_history(self, supplier_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على تاريخ مشتريات المورد"""
        try:
            query = """
            SELECT invoice_number, purchase_date, total_amount, paid_amount, 
                   remaining_amount, status
            FROM purchases
            WHERE supplier_id = ? AND status != 'ملغية'
            ORDER BY purchase_date DESC, id DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (supplier_id, limit))
            return [
                {
                    'invoice_number': row[0],
                    'purchase_date': row[1],
                    'total_amount': float(row[2]),
                    'paid_amount': float(row[3]),
                    'remaining_amount': float(row[4]),
                    'status': row[5]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على تاريخ مشتريات المورد {supplier_id}: {str(e)}")
            return []
    
    def get_suppliers_with_outstanding_balance(self) -> List[Supplier]:
        """الحصول على الموردين الذين لديهم رصيد مستحق"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.current_balance > 0 AND s.is_active = 1
            ORDER BY s.current_balance DESC
            """
            
            results = self.db_manager.fetch_all(query)
            return [self._row_to_supplier(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الموردين ذوي الرصيد المستحق: {str(e)}")
            return []
    
    def get_top_suppliers(self, limit: int = 10) -> List[Supplier]:
        """الحصول على أفضل الموردين حسب المشتريات"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.is_active = 1
            AND (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') > 0
            ORDER BY (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (limit,))
            return [self._row_to_supplier(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على أفضل الموردين: {str(e)}")
            return []
    
    def get_suppliers_by_payment_terms(self, payment_terms: str) -> List[Supplier]:
        """الحصول على الموردين حسب شروط الدفع"""
        try:
            query = """
            SELECT s.*,
                   (SELECT MAX(purchase_date) FROM purchases WHERE supplier_id = s.id) as last_purchase_date,
                   (SELECT SUM(total_amount) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as total_purchases,
                   (SELECT COUNT(*) FROM purchases WHERE supplier_id = s.id AND status != 'ملغية') as purchases_count
            FROM suppliers s
            WHERE s.payment_terms = ? AND s.is_active = 1
            ORDER BY s.name
            """
            
            results = self.db_manager.fetch_all(query, (payment_terms,))
            return [self._row_to_supplier(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الموردين بشروط الدفع {payment_terms}: {str(e)}")
            return []
    
    def get_suppliers_report(self) -> Dict[str, Any]:
        """تقرير الموردين"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_suppliers,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_suppliers,
                COUNT(CASE WHEN current_balance > 0 AND is_active = 1 THEN 1 END) as suppliers_with_balance,
                COUNT(CASE WHEN current_balance > credit_limit AND is_active = 1 THEN 1 END) as suppliers_over_limit,
                SUM(CASE WHEN is_active = 1 THEN current_balance ELSE 0 END) as total_outstanding_balance,
                AVG(CASE WHEN is_active = 1 THEN credit_limit ELSE NULL END) as avg_credit_limit
            FROM suppliers
            """
            
            result = self.db_manager.fetch_one(query)
            if result:
                return {
                    'total_suppliers': result[0] or 0,
                    'active_suppliers': result[1] or 0,
                    'suppliers_with_balance': result[2] or 0,
                    'suppliers_over_limit': result[3] or 0,
                    'total_outstanding_balance': float(result[4] or 0),
                    'avg_credit_limit': float(result[5] or 0)
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير الموردين: {str(e)}")
        
        return {
            'total_suppliers': 0,
            'active_suppliers': 0,
            'suppliers_with_balance': 0,
            'suppliers_over_limit': 0,
            'total_outstanding_balance': 0.0,
            'avg_credit_limit': 0.0
        }
    
    def _row_to_supplier(self, row) -> Supplier:
        """تحويل صف قاعدة البيانات إلى كائن مورد"""
        return Supplier(
            id=row[0],
            name=row[1],
            name_en=row[2],
            contact_person=row[3],
            phone=row[4],
            phone2=row[5],
            email=row[6],
            website=row[7],
            address=row[8],
            city=row[9],
            country=row[10],
            tax_number=row[11],
            commercial_register=row[12],
            payment_terms=row[13],
            credit_limit=Decimal(str(row[14])),
            current_balance=Decimal(str(row[15])),
            notes=row[16],
            is_active=bool(row[17]),
            created_at=datetime.fromisoformat(row[18]) if row[18] else None,
            updated_at=datetime.fromisoformat(row[19]) if row[19] else None,
            last_purchase_date=date.fromisoformat(row[20]) if row[20] else None,
            total_purchases=Decimal(str(row[21] or 0)),
            purchases_count=row[22] or 0
        )