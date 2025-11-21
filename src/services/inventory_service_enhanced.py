#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المخزون المحسّنة - Enhanced Inventory Service
توفر عمليات متقدمة لإدارة المخزون والحركات والتحليلات
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class MovementType(Enum):
    """أنواع حركات المخزون"""
    PURCHASE = "شراء"  # إضافة مخزون من شراء
    SALE = "بيع"  # تقليل مخزون من بيع
    ADJUSTMENT = "تعديل"  # تعديل يدوي
    TRANSFER = "تحويل"  # تحويل بين مخازن
    LOSS = "خسارة"  # خسارة أو تلف
    RETURN = "إرجاع"  # إرجاع من عميل
    INVENTORY_COUNT = "جرد"  # جرد دوري
    RESERVATION = "حجز"  # حجز مخزون
    RELEASE = "تحرير"  # تحرير مخزون محجوز

class InventoryStatus(Enum):
    """حالات المخزون"""
    NORMAL = "طبيعي"  # مخزون طبيعي
    LOW = "منخفض"  # مخزون منخفض
    CRITICAL = "حرج"  # مخزون حرج
    OUT_OF_STOCK = "نفاد"  # المنتج نفد من المخزون
    OVERSTOCK = "فائض"  # مخزون فائض

class ABCAnalysisCategory(Enum):
    """فئات تحليل ABC"""
    A = "A"  # المنتجات ذات القيمة العالية (80% من القيمة بـ 20% من الكمية)
    B = "B"  # المنتجات المتوسطة (15% من القيمة بـ 30% من الكمية)
    C = "C"  # المنتجات منخفضة القيمة (5% من القيمة بـ 50% من الكمية)

class StockMovement:
    """حركة المخزون"""
    
    def __init__(
        self,
        product_id: int,
        movement_type: str,
        quantity: int,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        notes: Optional[str] = None,
        from_location: Optional[str] = None,
        to_location: Optional[str] = None,
        barcode_scanned: bool = False,
        created_at: Optional[datetime] = None
    ):
        self.id: Optional[int] = None
        self.product_id = product_id
        self.movement_type = movement_type
        self.quantity = quantity
        self.reference_id = reference_id  # معرف الفاتورة أو الجرد
        self.reference_type = reference_type  # نوع المرجع
        self.notes = notes
        self.from_location = from_location
        self.to_location = to_location
        self.barcode_scanned = barcode_scanned
        self.created_at = created_at or datetime.now()
        self.created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'reference_id': self.reference_id,
            'reference_type': self.reference_type,
            'notes': self.notes,
            'from_location': self.from_location,
            'to_location': self.to_location,
            'barcode_scanned': self.barcode_scanned,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }

@dataclass
class InventoryReport:
    """تقرير المخزون"""
    total_products: int = 0
    total_categories: int = 0
    total_stock_value: float = 0.0
    low_stock_items: int = 0
    out_of_stock_items: int = 0
    expired_items: int = 0
    total_quantity: int = 0
    low_stock_count: int = 0
    out_of_stock_count: int = 0
    total_value: float = 0.0
    total_reserved: int = 0
    overstock_count: int = 0

class InventoryService:
    """خدمة شاملة لإدارة المخزون"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        # إضافة المدراء المتوافقين
        from models.category import CategoryManager
        from models.product import ProductManager
        self.category_manager = CategoryManager(db_manager)
        self.product_manager = ProductManager(db_manager, logger)
    
    # ==================== عمليات حركات المخزون ====================
    
    def record_stock_movement(self, movement: StockMovement) -> Optional[int]:
        """تسجيل حركة مخزون"""
        try:
            query = """
            INSERT INTO stock_movements (
                product_id, movement_type, quantity, reference_id, reference_type,
                notes, from_location, to_location, barcode_scanned,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                movement.product_id,
                movement.movement_type,
                movement.quantity,
                movement.reference_id,
                movement.reference_type,
                movement.notes,
                movement.from_location,
                movement.to_location,
                movement.barcode_scanned,
                movement.created_at,
                movement.created_by
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                movement_id = result.lastrowid
                
                # تحديث المخزون تلقائياً
                self._update_product_stock(movement)
                
                if self.logger:
                    self.logger.info(f"تم تسجيل حركة مخزون - النوع: {movement.movement_type}, المنتج: {movement.product_id}")
                
                return movement_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تسجيل حركة المخزون: {str(e)}")
        
        return None
    
    def get_stock_movements(
        self,
        product_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StockMovement]:
        """الحصول على حركات المخزون"""
        try:
            query = """
            SELECT id, product_id, movement_type, quantity, reference_id, reference_type,
                   notes, from_location, to_location, barcode_scanned, created_at, created_by
            FROM stock_movements
            WHERE 1=1
            """
            
            params = []
            
            if product_id:
                query += " AND product_id = ?"
                params.append(product_id)
            
            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            results = self.db_manager.fetch_all(query, params)
            movements = []
            
            for row in results:
                movement = StockMovement(
                    product_id=row[1],
                    movement_type=row[2],
                    quantity=row[3],
                    reference_id=row[4],
                    reference_type=row[5],
                    notes=row[6],
                    from_location=row[7],
                    to_location=row[8],
                    barcode_scanned=bool(row[9]),
                    created_at=datetime.fromisoformat(row[10]) if row[10] else None
                )
                movement.id = row[0]
                movement.created_by = row[11]
                movements.append(movement)
            
            return movements
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على حركات المخزون: {str(e)}")
            return []
    
    # ==================== تحديث المخزون ====================
    
    def _update_product_stock(self, movement: StockMovement) -> bool:
        """تحديث مخزون المنتج بناءً على الحركة"""
        try:
            # تحديد تأثير الحركة على المخزون
            quantity_change = 0
            reserved_change = 0
            
            if movement.movement_type == MovementType.PURCHASE.value:
                quantity_change = movement.quantity
            elif movement.movement_type == MovementType.SALE.value:
                quantity_change = -movement.quantity
            elif movement.movement_type == MovementType.RETURN.value:
                quantity_change = movement.quantity
            elif movement.movement_type == MovementType.LOSS.value:
                quantity_change = -movement.quantity
            elif movement.movement_type == MovementType.ADJUSTMENT.value:
                quantity_change = movement.quantity  # يمكن أن يكون موجب أو سالب
            elif movement.movement_type == MovementType.RESERVATION.value:
                reserved_change = movement.quantity
            elif movement.movement_type == MovementType.RELEASE.value:
                reserved_change = -movement.quantity
            
            if quantity_change != 0:
                query = """
                UPDATE products
                SET current_stock = current_stock + ?, updated_at = ?
                WHERE id = ?
                """
                params = (quantity_change, datetime.now(), movement.product_id)
                self.db_manager.execute_query(query, params)
            
            if reserved_change != 0:
                query = """
                UPDATE products
                SET reserved_stock = reserved_stock + ?, updated_at = ?
                WHERE id = ?
                """
                params = (reserved_change, datetime.now(), movement.product_id)
                self.db_manager.execute_query(query, params)
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث مخزون المنتج: {str(e)}")
            return False
    
    # ==================== عمليات النقل والتحويل ====================
    
    def transfer_stock(
        self,
        product_id: int,
        quantity: int,
        from_location: str,
        to_location: str,
        notes: Optional[str] = None
    ) -> bool:
        """نقل مخزون بين مواقع"""
        try:
            movement = StockMovement(
                product_id=product_id,
                movement_type=MovementType.TRANSFER.value,
                quantity=quantity,
                from_location=from_location,
                to_location=to_location,
                notes=notes
            )
            
            movement_id = self.record_stock_movement(movement)
            return movement_id is not None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في نقل المخزون: {str(e)}")
            return False
    
    # ==================== عمليات الحجز والتحرير ====================
    
    def reserve_stock(
        self,
        product_id: int,
        quantity: int,
        reference_id: Optional[int] = None,
        reference_type: str = "order"
    ) -> bool:
        """حجز مخزون"""
        try:
            movement = StockMovement(
                product_id=product_id,
                movement_type=MovementType.RESERVATION.value,
                quantity=quantity,
                reference_id=reference_id,
                reference_type=reference_type
            )
            
            movement_id = self.record_stock_movement(movement)
            return movement_id is not None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حجز المخزون: {str(e)}")
            return False
    
    def release_reserved_stock(
        self,
        product_id: int,
        quantity: int,
        reference_id: Optional[int] = None
    ) -> bool:
        """تحرير مخزون محجوز"""
        try:
            movement = StockMovement(
                product_id=product_id,
                movement_type=MovementType.RELEASE.value,
                quantity=quantity,
                reference_id=reference_id
            )
            
            movement_id = self.record_stock_movement(movement)
            return movement_id is not None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحرير المخزون المحجوز: {str(e)}")
            return False
    
    # ==================== عمليات الجرد ====================
    
    def create_inventory_count(
        self,
        count_date: datetime,
        counted_by: str,
        notes: Optional[str] = None
    ) -> Optional[int]:
        """إنشاء عملية جرد"""
        try:
            query = """
            INSERT INTO inventory_counts (
                count_date, counted_by, notes, created_at
            ) VALUES (?, ?, ?, ?)
            """
            
            params = (count_date, counted_by, notes, datetime.now())
            result = self.db_manager.execute_query(query, params)
            
            if result and hasattr(result, 'lastrowid'):
                if self.logger:
                    self.logger.info(f"تم إنشاء عملية جرد جديدة")
                return result.lastrowid
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء عملية جرد: {str(e)}")
        
        return None
    
    def record_inventory_count_item(
        self,
        count_id: int,
        product_id: int,
        counted_quantity: int,
        actual_quantity: int
    ) -> Optional[int]:
        """تسجيل بند من الجرد"""
        try:
            variance = actual_quantity - counted_quantity
            
            query = """
            INSERT INTO inventory_count_items (
                count_id, product_id, counted_quantity, actual_quantity, variance
            ) VALUES (?, ?, ?, ?, ?)
            """
            
            params = (count_id, product_id, counted_quantity, actual_quantity, variance)
            result = self.db_manager.execute_query(query, params)
            
            if result and hasattr(result, 'lastrowid'):
                return result.lastrowid
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تسجيل بند الجرد: {str(e)}")
        
        return None
    
    def finalize_inventory_count(self, count_id: int) -> bool:
        """إنهاء عملية جرد وتطبيق التعديلات"""
        try:
            # الحصول على جميع بنود الجرد
            query = """
            SELECT product_id, variance
            FROM inventory_count_items
            WHERE count_id = ?
            """
            
            results = self.db_manager.fetch_all(query, (count_id,))
            
            for row in results:
                product_id = row[0]
                variance = row[1]
                
                if variance != 0:
                    # تسجيل تعديل للفرق
                    movement = StockMovement(
                        product_id=product_id,
                        movement_type=MovementType.ADJUSTMENT.value,
                        quantity=abs(variance),
                        reference_id=count_id,
                        reference_type="inventory_count"
                    )
                    
                    # التعامل مع الفرق السالب
                    if variance < 0:
                        movement.quantity = abs(variance)
                        movement.movement_type = MovementType.LOSS.value
                    
                    self.record_stock_movement(movement)
            
            # تحديث حالة الجرد
            update_query = "UPDATE inventory_counts SET status = 'completed', completed_at = ? WHERE id = ?"
            self.db_manager.execute_query(update_query, (datetime.now(), count_id))
            
            if self.logger:
                self.logger.info(f"تم إنهاء عملية الجرد {count_id}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنهاء عملية الجرد: {str(e)}")
            return False
    
    # ==================== تحليل ABC ====================
    
    def perform_abc_analysis(self) -> Dict[str, List[Dict[str, Any]]]:
        """إجراء تحليل ABC للمخزون"""
        try:
            # الحصول على المنتجات مع قيمتها
            query = """
            SELECT id, name, sku, base_price, current_stock,
                   (base_price * current_stock) as total_value
            FROM products
            WHERE is_active = 1 AND current_stock > 0
            ORDER BY total_value DESC
            """
            
            results = self.db_manager.fetch_all(query)
            
            if not results:
                return {'A': [], 'B': [], 'C': []}
            
            # حساب إجمالي القيمة
            total_value = sum(row[5] for row in results if row[5])
            
            # تصنيف المنتجات
            running_value = 0
            analysis = {'A': [], 'B': [], 'C': []}
            
            for row in results:
                product_value = row[5] or 0
                running_value += product_value
                percentage = (running_value / total_value * 100) if total_value > 0 else 0
                
                # تحديد الفئة
                if percentage <= 80:
                    category = 'A'
                elif percentage <= 95:
                    category = 'B'
                else:
                    category = 'C'
                
                product_info = {
                    'id': row[0],
                    'name': row[1],
                    'sku': row[2],
                    'price': float(row[3]),
                    'stock': row[4],
                    'total_value': float(product_value),
                    'percentage': float(percentage)
                }
                
                analysis[category].append(product_info)
            
            return analysis
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحليل ABC: {str(e)}")
            return {'A': [], 'B': [], 'C': []}
    
    # ==================== عمليات إحصائية ====================
    
    def get_inventory_status(self, product_id: int) -> Dict[str, Any]:
        """الحصول على حالة المخزون للمنتج"""
        try:
            query = """
            SELECT id, name, current_stock, reserved_stock, min_stock,
                   reorder_point, max_stock, base_price
            FROM products
            WHERE id = ?
            """
            
            row = self.db_manager.fetch_one(query, (product_id,))
            if not row:
                return {}
            
            current_stock = row[2]
            reserved_stock = row[3]
            min_stock = row[4]
            reorder_point = row[5]
            available_stock = current_stock - reserved_stock
            
            # تحديد الحالة
            if available_stock <= 0:
                status = InventoryStatus.OUT_OF_STOCK.value
            elif available_stock <= min_stock:
                status = InventoryStatus.CRITICAL.value
            elif available_stock <= reorder_point:
                status = InventoryStatus.LOW.value
            elif current_stock > row[6]:  # max_stock
                status = InventoryStatus.OVERSTOCK.value
            else:
                status = InventoryStatus.NORMAL.value
            
            return {
                'product_id': product_id,
                'product_name': row[1],
                'current_stock': current_stock,
                'reserved_stock': reserved_stock,
                'available_stock': available_stock,
                'min_stock': min_stock,
                'reorder_point': reorder_point,
                'max_stock': row[6],
                'status': status,
                'inventory_value': float(available_stock * row[7])
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على حالة المخزون: {str(e)}")
            return {}
    
    def get_inventory_turnover_rate(self, product_id: int, days: int = 30) -> Decimal:
        """حساب معدل دوران المخزون"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            query = """
            SELECT SUM(quantity)
            FROM stock_movements
            WHERE product_id = ? AND movement_type = ? AND created_at >= ?
            """
            
            result = self.db_manager.fetch_one(
                query,
                (product_id, MovementType.SALE.value, start_date)
            )
            
            if result and result[0]:
                return Decimal(str(result[0]))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب معدل دوران المخزون: {str(e)}")
        
        return Decimal('0.00')
    
    def get_inventory_report(self) -> InventoryReport:
        """تقرير شامل عن المخزون"""
        try:
            # التحقق من الأعمدة المتاحة
            cols_info = self.db_manager.fetch_all("PRAGMA table_info(products)")
            available_cols = {row[1] for row in cols_info} if cols_info else set()
            
            # بناء الاستعلام ديناميكياً بناءً على الأعمدة المتاحة
            base_reserved = "reserved_stock" if "reserved_stock" in available_cols else "0 as reserved_stock"
            base_max = "max_stock" if "max_stock" in available_cols else "999999 as max_stock"
            base_price = "base_price" if "base_price" in available_cols else ("selling_price" if "selling_price" in available_cols else "0")
            
            query = f"""
            SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN current_stock <= COALESCE(min_stock, 0) THEN 1 END) as low_stock_count,
                COUNT(CASE WHEN current_stock <= 0 THEN 1 END) as out_of_stock_count,
                SUM(current_stock) as total_quantity,
                SUM(COALESCE(current_stock, 0) * COALESCE({base_price}, 0)) as total_value,
                0 as total_reserved,
                0 as overstock_count
            FROM products
            WHERE is_active = 1
            """
            
            # احصل على عدد الفئات
            categories_count = 0
            try:
                cat_result = self.db_manager.fetch_one("SELECT COUNT(*) FROM categories")
                categories_count = cat_result[0] if cat_result else 0
            except:
                categories_count = 0
            
            result = self.db_manager.fetch_one(query)
            if result:
                return InventoryReport(
                    total_products=result[0] or 0,
                    total_categories=categories_count,
                    total_stock_value=float(result[4] or 0),
                    low_stock_items=result[1] or 0,
                    out_of_stock_items=result[2] or 0,
                    expired_items=0,
                    total_quantity=result[3] or 0,
                    low_stock_count=result[1] or 0,
                    out_of_stock_count=result[2] or 0,
                    total_value=float(result[4] or 0),
                    total_reserved=result[5] or 0,
                    overstock_count=result[6] or 0
                )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على تقرير المخزون: {str(e)}")
        
        return InventoryReport()

    # Alias for compatibility
    def generate_inventory_report(self) -> InventoryReport:
        """تقرير شامل عن المخزون (اسم بديل للتوافق)"""
        return self.get_inventory_report()
