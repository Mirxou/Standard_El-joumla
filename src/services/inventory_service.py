#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة المخزون - Inventory Service
تحتوي على جميع العمليات المتعلقة بإدارة المخزون والمنتجات
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.product import Product, ProductManager
from models.category import Category, CategoryManager
from models.supplier import Supplier, SupplierManager

@dataclass
class StockMovement:
    """حركة المخزون"""
    id: Optional[int] = None
    product_id: int = 0
    movement_type: str = ""  # in, out, adjustment, transfer
    quantity: float = 0.0
    reference_id: Optional[int] = None  # معرف المرجع (فاتورة، تحويل، إلخ)
    reference_type: Optional[str] = None  # sale, purchase, adjustment, transfer
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass
class StockAlert:
    """تنبيه المخزون"""
    product_id: int
    product_name: str
    current_stock: float
    minimum_stock: float
    alert_type: str  # low_stock, out_of_stock, expired
    severity: str  # low, medium, high, critical
    message: str

@dataclass
class InventoryReport:
    """تقرير المخزون"""
    total_products: int
    total_categories: int
    total_stock_value: float
    low_stock_items: int
    out_of_stock_items: int
    expired_items: int
    top_products: List[Dict[str, Any]]
    stock_movements: List[Dict[str, Any]]
    alerts: List[StockAlert]

class InventoryService:
    """خدمة إدارة المخزون"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.product_manager = ProductManager(db_manager, logger)
        self.category_manager = CategoryManager(db_manager, logger)
        self.supplier_manager = SupplierManager(db_manager, logger)
    
    # ===== إدارة المنتجات =====
    
    def add_product(self, product: Product) -> Optional[int]:
        """إضافة منتج جديد"""
        try:
            # التحقق من عدم تكرار الباركود
            if product.barcode and self.product_manager.get_product_by_barcode(product.barcode):
                if self.logger:
                    self.logger.warning(f"الباركود {product.barcode} موجود بالفعل")
                return None
            
            product_id = self.product_manager.create_product(product)
            if product_id:
                # تسجيل حركة المخزون الأولية
                if product.current_stock > 0:
                    self._record_stock_movement(
                        product_id=product_id,
                        movement_type="in",
                        quantity=product.current_stock,
                        reference_type="initial",
                        notes="رصيد أولي"
                    )
                
                if self.logger:
                    self.logger.info(f"تم إضافة منتج جديد: {product.name} (ID: {product_id})")
            
            return product_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة المنتج: {str(e)}")
            return None
    
    def update_product(self, product: Product) -> bool:
        """تحديث منتج"""
        try:
            # الحصول على المنتج الحالي لمقارنة الكمية
            current_product = self.product_manager.get_product_by_id(product.id)
            if not current_product:
                return False
            
            # تحديث المنتج
            success = self.product_manager.update_product(product)
            if success:
                # تسجيل تغيير الكمية إذا حدث
                if current_product.current_stock != product.current_stock:
                    quantity_diff = product.current_stock - current_product.current_stock
                    movement_type = "in" if quantity_diff > 0 else "out"
                    
                    self._record_stock_movement(
                        product_id=product.id,
                        movement_type=movement_type,
                        quantity=abs(quantity_diff),
                        reference_type="adjustment",
                        notes="تعديل يدوي للكمية"
                    )
                
                if self.logger:
                    self.logger.info(f"تم تحديث المنتج: {product.name}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المنتج {product.id}: {str(e)}")
            return False
    
    def delete_product(self, product_id: int, hard_delete: bool = False) -> bool:
        """حذف منتج"""
        try:
            success = self.product_manager.delete_product(product_id, hard_delete)
            if success and self.logger:
                delete_type = "نهائي" if hard_delete else "مؤقت"
                self.logger.info(f"تم حذف المنتج {product_id} ({delete_type})")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المنتج {product_id}: {str(e)}")
            return False
    
    def search_products(self, query: str, category_id: Optional[int] = None, 
                       supplier_id: Optional[int] = None, active_only: bool = True) -> List[Product]:
        """البحث عن المنتجات"""
        try:
            return self.product_manager.search_products(query, category_id, supplier_id, active_only)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث عن المنتجات: {str(e)}")
            return []
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        """الحصول على منتج بالباركود"""
        try:
            return self.product_manager.get_product_by_barcode(barcode)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالباركود {barcode}: {str(e)}")
            return None
    
    # ===== إدارة الفئات =====
    
    def add_category(self, category: Category) -> Optional[int]:
        """إضافة فئة جديدة"""
        try:
            category_id = self.category_manager.create_category(category)
            if category_id and self.logger:
                self.logger.info(f"تم إضافة فئة جديدة: {category.name} (ID: {category_id})")
            return category_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة الفئة: {str(e)}")
            return None
    
    def get_category_tree(self) -> List[Dict[str, Any]]:
        """الحصول على شجرة الفئات"""
        try:
            return self.category_manager.get_category_tree()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على شجرة الفئات: {str(e)}")
            return []
    
    # ===== إدارة المخزون =====
    
    def adjust_stock(self, product_id: int, new_quantity: float, 
                    reason: str = "", user_id: Optional[int] = None) -> bool:
        """تعديل كمية المخزون"""
        try:
            product = self.product_manager.get_product_by_id(product_id)
            if not product:
                return False
            
            old_quantity = product.current_stock
            quantity_diff = new_quantity - old_quantity
            
            # تحديث الكمية
            success = self.product_manager.update_stock(product_id, new_quantity)
            if success:
                # تسجيل حركة المخزون
                movement_type = "in" if quantity_diff > 0 else "out"
                self._record_stock_movement(
                    product_id=product_id,
                    movement_type=movement_type,
                    quantity=abs(quantity_diff),
                    reference_type="adjustment",
                    notes=f"تعديل المخزون: {reason}",
                    created_by=user_id
                )
                
                if self.logger:
                    self.logger.info(f"تم تعديل مخزون المنتج {product_id}: {old_quantity} -> {new_quantity}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعديل مخزون المنتج {product_id}: {str(e)}")
            return False
    
    def transfer_stock(self, from_product_id: int, to_product_id: int, 
                      quantity: float, reason: str = "", user_id: Optional[int] = None) -> bool:
        """نقل المخزون بين المنتجات"""
        try:
            # التحقق من وجود المنتجات
            from_product = self.product_manager.get_product_by_id(from_product_id)
            to_product = self.product_manager.get_product_by_id(to_product_id)
            
            if not from_product or not to_product:
                return False
            
            # التحقق من توفر الكمية
            if from_product.current_stock < quantity:
                if self.logger:
                    self.logger.warning(f"كمية غير كافية للنقل من المنتج {from_product_id}")
                return False
            
            # تحديث المخزون
            success1 = self.product_manager.update_stock(
                from_product_id, from_product.current_stock - quantity
            )
            success2 = self.product_manager.update_stock(
                to_product_id, to_product.current_stock + quantity
            )
            
            if success1 and success2:
                # تسجيل حركات المخزون
                transfer_ref = int(datetime.now().timestamp())
                
                self._record_stock_movement(
                    product_id=from_product_id,
                    movement_type="out",
                    quantity=quantity,
                    reference_id=transfer_ref,
                    reference_type="transfer",
                    notes=f"نقل إلى المنتج {to_product_id}: {reason}",
                    created_by=user_id
                )
                
                self._record_stock_movement(
                    product_id=to_product_id,
                    movement_type="in",
                    quantity=quantity,
                    reference_id=transfer_ref,
                    reference_type="transfer",
                    notes=f"نقل من المنتج {from_product_id}: {reason}",
                    created_by=user_id
                )
                
                if self.logger:
                    self.logger.info(f"تم نقل {quantity} من المنتج {from_product_id} إلى {to_product_id}")
                
                return True
            
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في نقل المخزون: {str(e)}")
            return False
    
    def get_stock_movements(self, product_id: Optional[int] = None, 
                           start_date: Optional[date] = None, 
                           end_date: Optional[date] = None,
                           limit: int = 100) -> List[StockMovement]:
        """الحصول على حركات المخزون"""
        try:
            query = """
            SELECT sm.*, p.name as product_name
            FROM stock_movements sm
            LEFT JOIN products p ON sm.product_id = p.id
            WHERE 1=1
            """
            params = []
            
            if product_id:
                query += " AND sm.product_id = ?"
                params.append(product_id)
            
            if start_date:
                query += " AND DATE(sm.created_at) >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND DATE(sm.created_at) <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY sm.created_at DESC LIMIT ?"
            params.append(limit)
            
            results = self.db_manager.fetch_all(query, params)
            movements = []
            
            for row in results:
                movement = StockMovement(
                    id=row[0],
                    product_id=row[1],
                    movement_type=row[2],
                    quantity=row[3],
                    reference_id=row[4],
                    reference_type=row[5],
                    notes=row[6],
                    created_by=row[7],
                    created_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
                movements.append(movement)
            
            return movements
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على حركات المخزون: {str(e)}")
            return []
    
    # ===== التنبيهات والتقارير =====
    
    def get_stock_alerts(self) -> List[StockAlert]:
        """الحصول على تنبيهات المخزون"""
        try:
            alerts = []
            
            # منتجات منخفضة المخزون
            low_stock_products = self.product_manager.get_low_stock_products()
            for product in low_stock_products:
                severity = "critical" if product.current_stock == 0 else "high"
                alert_type = "out_of_stock" if product.current_stock == 0 else "low_stock"
                
                message = f"المنتج {product.name} "
                if product.current_stock == 0:
                    message += "نفد من المخزون"
                else:
                    message += f"مخزون منخفض ({product.current_stock} متبقي)"
                
                alert = StockAlert(
                    product_id=product.id,
                    product_name=product.name,
                    current_stock=product.current_stock,
                    minimum_stock=product.minimum_stock,
                    alert_type=alert_type,
                    severity=severity,
                    message=message
                )
                alerts.append(alert)
            
            # منتجات منتهية الصلاحية (إذا كانت متوفرة)
            expired_products = self._get_expired_products()
            for product in expired_products:
                alert = StockAlert(
                    product_id=product['id'],
                    product_name=product['name'],
                    current_stock=product['current_stock'],
                    minimum_stock=product.get('minimum_stock', 0),
                    alert_type="expired",
                    severity="high",
                    message=f"المنتج {product['name']} منتهي الصلاحية"
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على تنبيهات المخزون: {str(e)}")
            return []
    
    def generate_inventory_report(self, include_movements: bool = True) -> InventoryReport:
        """إنشاء تقرير شامل للمخزون"""
        try:
            # إحصائيات عامة
            total_products = len(self.product_manager.get_all_products())
            total_categories = len(self.category_manager.get_all_categories())
            
            # قيمة المخزون الإجمالية
            stock_report = self.product_manager.get_stock_report()
            total_stock_value = stock_report.get('total_value', 0)
            
            # المنتجات منخفضة المخزون
            low_stock_products = self.product_manager.get_low_stock_products()
            low_stock_count = len(low_stock_products)
            out_of_stock_count = len([p for p in low_stock_products if p.current_stock == 0])
            
            # المنتجات منتهية الصلاحية
            expired_products = self._get_expired_products()
            expired_count = len(expired_products)
            
            # أفضل المنتجات (حسب القيمة)
            top_products = self._get_top_products_by_value()
            
            # حركات المخزون الأخيرة
            stock_movements = []
            if include_movements:
                movements = self.get_stock_movements(limit=50)
                stock_movements = [
                    {
                        'product_id': m.product_id,
                        'movement_type': m.movement_type,
                        'quantity': m.quantity,
                        'reference_type': m.reference_type,
                        'notes': m.notes,
                        'created_at': m.created_at.isoformat() if m.created_at else None
                    }
                    for m in movements
                ]
            
            # التنبيهات
            alerts = self.get_stock_alerts()
            
            report = InventoryReport(
                total_products=total_products,
                total_categories=total_categories,
                total_stock_value=total_stock_value,
                low_stock_items=low_stock_count,
                out_of_stock_items=out_of_stock_count,
                expired_items=expired_count,
                top_products=top_products,
                stock_movements=stock_movements,
                alerts=alerts
            )
            
            return report
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المخزون: {str(e)}")
            return InventoryReport(
                total_products=0, total_categories=0, total_stock_value=0,
                low_stock_items=0, out_of_stock_items=0, expired_items=0,
                top_products=[], stock_movements=[], alerts=[]
            )
    
    # ===== الدوال المساعدة =====
    
    def _record_stock_movement(self, product_id: int, movement_type: str, quantity: float,
                              reference_id: Optional[int] = None, reference_type: Optional[str] = None,
                              notes: Optional[str] = None, created_by: Optional[int] = None):
        """تسجيل حركة مخزون"""
        try:
            query = """
            INSERT INTO stock_movements (
                product_id, movement_type, quantity, reference_id, 
                reference_type, notes, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                product_id, movement_type, quantity, reference_id,
                reference_type, notes, created_by, datetime.now()
            )
            
            self.db_manager.execute_query(query, params)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تسجيل حركة المخزون: {str(e)}")
    
    def _get_expired_products(self) -> List[Dict[str, Any]]:
        """الحصول على المنتجات منتهية الصلاحية"""
        try:
            # هذا يتطلب جدول batches أو حقل expiry_date في products
            # سنعيد قائمة فارغة حالياً
            return []
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتجات منتهية الصلاحية: {str(e)}")
            return []
    
    def _get_top_products_by_value(self, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على أفضل المنتجات حسب القيمة"""
        try:
            query = """
            SELECT id, name, current_stock, selling_price,
                   (current_stock * selling_price) as stock_value
            FROM products
            WHERE is_active = 1 AND current_stock > 0
            ORDER BY stock_value DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (limit,))
            
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'current_stock': row[2],
                    'selling_price': row[3],
                    'stock_value': row[4]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على أفضل المنتجات: {str(e)}")
            return []