#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المنتج - Product Model
يحتوي على جميع العمليات المتعلقة بالمنتجات
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import sqlite3
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

@dataclass
class Product:
    """نموذج بيانات المنتج"""
    id: Optional[int] = None
    name: str = ""
    name_en: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    unit: str = "قطعة"
    cost_price: Decimal = Decimal('0.00')
    selling_price: Decimal = Decimal('0.00')
    min_stock: int = 0
    current_stock: int = 0
    description: Optional[str] = None
    image_path: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        if isinstance(self.cost_price, (int, float, str)):
            self.cost_price = Decimal(str(self.cost_price))
        if isinstance(self.selling_price, (int, float, str)):
            self.selling_price = Decimal(str(self.selling_price))
    
    @property
    def profit_margin(self) -> Decimal:
        """حساب هامش الربح"""
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return Decimal('0.00')
    
    @property
    def profit_amount(self) -> Decimal:
        """مبلغ الربح للوحدة الواحدة"""
        return self.selling_price - self.cost_price
    
    @property
    def stock_value(self) -> Decimal:
        """قيمة المخزون الحالي"""
        return self.cost_price * self.current_stock
    
    @property
    def is_low_stock(self) -> bool:
        """هل المخزون منخفض؟"""
        return self.current_stock <= self.min_stock
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'barcode': self.barcode,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'unit': self.unit,
            'cost_price': float(self.cost_price),
            'selling_price': float(self.selling_price),
            'min_stock': self.min_stock,
            'current_stock': self.current_stock,
            'description': self.description,
            'image_path': self.image_path,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'profit_margin': float(self.profit_margin),
            'profit_amount': float(self.profit_amount),
            'stock_value': float(self.stock_value),
            'is_low_stock': self.is_low_stock
        }

class ProductManager:
    """مدير المنتجات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def create_product(self, product: Product) -> Optional[int]:
        """إنشاء منتج جديد"""
        try:
            query = """
            INSERT INTO products (
                name, name_en, barcode, category_id, unit,
                cost_price, selling_price, min_stock, current_stock,
                description, image_path, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                product.name,
                product.name_en,
                product.barcode,
                product.category_id,
                product.unit,
                float(product.cost_price),
                float(product.selling_price),
                product.min_stock,
                product.current_stock,
                product.description,
                product.image_path,
                product.is_active,
                now,
                now
            )
            
            print(f"تنفيذ الاستعلام: {query}")
            print(f"المعاملات: {params}")
            
            # استخدام execute_non_query بدلاً من execute_query
            rowcount = self.db_manager.execute_non_query(query, params)
            print(f"عدد الصفوف المتأثرة: {rowcount}")
            
            if rowcount > 0:
                # الحصول على آخر ID مُدرج
                product_id = self.db_manager.execute_scalar("SELECT last_insert_rowid()")
                print(f"آخر ID مُدرج: {product_id}")
                if self.logger:
                    self.logger.info(f"تم إنشاء منتج جديد: {product.name} (ID: {product_id})")
                return product_id
            else:
                print("لم يتم إدراج أي صفوف")
            
        except Exception as e:
            print(f"خطأ في إنشاء المنتج: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.logger:
                self.logger.error(f"خطأ في إنشاء المنتج: {str(e)}")
            return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """الحصول على منتج بالمعرف"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
            """
            
            result = self.db_manager.fetch_one(query, (product_id,))
            if result:
                return self._row_to_product(result)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتج {product_id}: {str(e)}")
        
        return None
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        """الحصول على منتج بالباركود"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.barcode = ? AND p.is_active = 1
            """
            
            result = self.db_manager.fetch_one(query, (barcode,))
            if result:
                return self._row_to_product(result)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالباركود {barcode}: {str(e)}")
        
        return None
    
    def search_products(self, search_term: str = "", category_id: Optional[int] = None, 
                       active_only: bool = True) -> List[Product]:
        """البحث في المنتجات"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
            """
            params = []
            
            if search_term:
                query += " AND (p.name LIKE ? OR p.name_en LIKE ? OR p.barcode LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if category_id:
                query += " AND p.category_id = ?"
                params.append(category_id)
            
            if active_only:
                query += " AND p.is_active = 1"
            
            query += " ORDER BY p.name"
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_product(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في المنتجات: {str(e)}")
            return []
    
    def get_all_products(self, active_only: bool = True) -> List[Product]:
        """الحصول على جميع المنتجات"""
        return self.search_products(active_only=active_only)
    
    def update_product(self, product: Product) -> bool:
        """تحديث منتج"""
        try:
            query = """
            UPDATE products SET
                name = ?, name_en = ?, barcode = ?, category_id = ?,
                unit = ?, cost_price = ?, selling_price = ?, min_stock = ?,
                current_stock = ?, description = ?, image_path = ?,
                is_active = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (
                product.name,
                product.name_en,
                product.barcode,
                product.category_id,
                product.unit,
                float(product.cost_price),
                float(product.selling_price),
                product.min_stock,
                product.current_stock,
                product.description,
                product.image_path,
                product.is_active,
                datetime.now(),
                product.id
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث المنتج: {product.name} (ID: {product.id})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المنتج {product.id}: {str(e)}")
        
        return False
    
    def delete_product(self, product_id: int, soft_delete: bool = True) -> bool:
        """حذف منتج"""
        try:
            if soft_delete:
                # حذف ناعم - تعطيل المنتج فقط
                query = "UPDATE products SET is_active = 0, updated_at = ? WHERE id = ?"
                params = (datetime.now(), product_id)
            else:
                # حذف صلب - حذف نهائي
                query = "DELETE FROM products WHERE id = ?"
                params = (product_id,)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    action = "تعطيل" if soft_delete else "حذف"
                    self.logger.info(f"تم {action} المنتج (ID: {product_id})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المنتج {product_id}: {str(e)}")
        
        return False
    
    def update_stock(self, product_id: int, quantity_change: int, 
                    operation_type: str = "manual") -> bool:
        """تحديث المخزون"""
        try:
            # الحصول على المخزون الحالي
            current_product = self.get_product_by_id(product_id)
            if not current_product:
                return False
            
            new_stock = current_product.current_stock + quantity_change
            
            # التأكد من عدم السماح بمخزون سالب
            if new_stock < 0:
                if self.logger:
                    self.logger.warning(f"محاولة جعل المخزون سالب للمنتج {product_id}")
                return False
            
            query = "UPDATE products SET current_stock = ?, updated_at = ? WHERE id = ?"
            params = (new_stock, datetime.now(), product_id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث مخزون المنتج {product_id}: {quantity_change:+d} ({operation_type})")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث مخزون المنتج {product_id}: {str(e)}")
        
        return False
    
    def get_low_stock_products(self) -> List[Product]:
        """الحصول على المنتجات ذات المخزون المنخفض"""
        try:
            query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock <= p.min_stock AND p.is_active = 1
            ORDER BY (p.current_stock - p.min_stock), p.name
            """
            
            results = self.db_manager.fetch_all(query)
            return [self._row_to_product(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتجات منخفضة المخزون: {str(e)}")
            return []
    
    def get_products_by_category(self, category_id: int) -> List[Product]:
        """الحصول على منتجات فئة معينة"""
        return self.search_products(category_id=category_id)
    
    def get_stock_report(self) -> Dict[str, Any]:
        """تقرير المخزون"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_products,
                COUNT(CASE WHEN current_stock <= min_stock AND is_active = 1 THEN 1 END) as low_stock_products,
                SUM(CASE WHEN is_active = 1 THEN current_stock * cost_price ELSE 0 END) as total_stock_value,
                AVG(CASE WHEN is_active = 1 THEN current_stock ELSE NULL END) as avg_stock_level
            FROM products
            """
            
            result = self.db_manager.fetch_one(query)
            if result:
                return {
                    'total_products': result[0] or 0,
                    'active_products': result[1] or 0,
                    'low_stock_products': result[2] or 0,
                    'total_stock_value': float(result[3] or 0),
                    'avg_stock_level': float(result[4] or 0)
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المخزون: {str(e)}")
        
        return {
            'total_products': 0,
            'active_products': 0,
            'low_stock_products': 0,
            'total_stock_value': 0.0,
            'avg_stock_level': 0.0
        }
    
    def _row_to_product(self, row) -> Product:
        """تحويل صف قاعدة البيانات إلى كائن منتج"""
        return Product(
            id=row[0],
            name=row[1],
            name_en=row[2],
            barcode=row[3],
            category_id=row[4],
            unit=row[5],
            cost_price=Decimal(str(row[6])),
            selling_price=Decimal(str(row[7])),
            min_stock=row[8],
            current_stock=row[9],
            description=row[10],
            image_path=row[11],
            is_active=bool(row[12]),
            created_at=datetime.fromisoformat(row[13]) if row[13] else None,
            updated_at=datetime.fromisoformat(row[14]) if row[14] else None,
            category_name=row[15] if len(row) > 15 else None
        )