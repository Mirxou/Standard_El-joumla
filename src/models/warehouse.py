#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المستودعات - Warehouse Model (Unified)
إدارة المستودعات والمخزون متعدد المستودعات
تم دمج ميزات Standard (الأنواع والسعة) مع ميزات Trae (التحويلات والجرد)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger

# ==================== Enums (إضافات Standard) ====================

class WarehouseType(Enum):
    """أنواع المستودعات"""
    MAIN = "main"           # مخزن رئيسي
    SHOP = "shop"           # نقطة بيع / محل
    DAMAGED = "damaged"     # مخزن تالف
    TRANSIT = "transit"     # مخزن عبور (للنقل)

# ==================== Models ====================

@dataclass
class Warehouse:
    """نموذج بيانات المستودع"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    name_en: Optional[str] = None
    
    # --- حقول Standard الجديدة ---
    warehouse_type: str = WarehouseType.MAIN.value
    capacity: Decimal = Decimal('0.00')      # السعة الكلية
    current_utilization: Decimal = Decimal('0.00') # المستغل حالياً
    
    # --- البيانات الأساسية ---
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "الجزائر"
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    allow_negative_stock: bool = False # حقل جديد للكاشير
    notes: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    def __post_init__(self):
        """ضمان تحويل الأرقام إلى Decimal"""
        if isinstance(self.capacity, (int, float, str)):
            self.capacity = Decimal(str(self.capacity))
        if isinstance(self.current_utilization, (int, float, str)):
            self.current_utilization = Decimal(str(self.current_utilization))

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'name_en': self.name_en,
            'warehouse_type': self.warehouse_type,
            'capacity': float(self.capacity),
            'current_utilization': float(self.current_utilization),
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'phone': self.phone,
            'email': self.email,
            'manager_name': self.manager_name,
            'manager_phone': self.manager_phone,
            'is_active': 1 if self.is_active else 0,
            'is_default': 1 if self.is_default else 0,
            'allow_negative_stock': 1 if self.allow_negative_stock else 0,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Warehouse':
        """إنشاء من قاموس"""
        return cls(
            id=data.get('id'),
            code=data.get('code', ''),
            name=data.get('name', ''),
            name_en=data.get('name_en'),
            warehouse_type=data.get('warehouse_type', WarehouseType.MAIN.value),
            capacity=Decimal(str(data.get('capacity', 0))),
            current_utilization=Decimal(str(data.get('current_utilization', 0))),
            address=data.get('address'),
            city=data.get('city'),
            country=data.get('country', 'الجزائر'),
            phone=data.get('phone'),
            email=data.get('email'),
            manager_name=data.get('manager_name'),
            manager_phone=data.get('manager_phone'),
            is_active=bool(data.get('is_active', 1)),
            is_default=bool(data.get('is_default', 0)),
            allow_negative_stock=bool(data.get('allow_negative_stock', 0)),
            notes=data.get('notes'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by')
        )


@dataclass
class WarehouseInventory:
    """نموذج مخزون المنتج في مستودع معين"""
    id: Optional[int] = None
    warehouse_id: int = 0
    product_id: int = 0
    quantity: float = 0.0
    reserved_quantity: float = 0.0
    available_quantity: float = 0.0
    min_stock: float = 0.0
    max_stock: float = 0.0
    reorder_point: float = 0.0
    last_movement_date: Optional[datetime] = None
    last_count_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # معلومات إضافية من JOIN
    warehouse_name: Optional[str] = None
    product_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'min_stock': self.min_stock,
            'max_stock': self.max_stock,
            'reorder_point': self.reorder_point,
            'last_movement_date': self.last_movement_date.isoformat() if self.last_movement_date else None,
            'last_count_date': self.last_count_date.isoformat() if self.last_count_date else None,
            'notes': self.notes,
            'warehouse_name': self.warehouse_name,
            'product_name': self.product_name
        }


@dataclass
class WarehouseTransfer:
    """نموذج نقل المخزون بين المستودعات"""
    id: Optional[int] = None
    transfer_number: str = ""
    from_warehouse_id: int = 0
    to_warehouse_id: int = 0
    product_id: int = 0
    quantity: float = 0.0
    status: str = "pending"  # pending, in_transit, completed, cancelled
    transfer_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    received_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # معلومات إضافية من JOIN
    from_warehouse_name: Optional[str] = None
    to_warehouse_name: Optional[str] = None
    product_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'transfer_number': self.transfer_number,
            'from_warehouse_id': self.from_warehouse_id,
            'to_warehouse_id': self.to_warehouse_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'status': self.status,
            'transfer_date': self.transfer_date.isoformat() if self.transfer_date else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'notes': self.notes,
            'created_by': self.created_by,
            'received_by': self.received_by,
            'from_warehouse_name': self.from_warehouse_name,
            'to_warehouse_name': self.to_warehouse_name,
            'product_name': self.product_name
        }


class WarehouseManager:
    """مدير المستودعات - CRUD Operations"""
    
    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
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
    
    # ===== CRUD Operations =====
    
    def create_warehouse(self, warehouse: Warehouse) -> Optional[int]:
        """إنشاء مستودع جديد"""
        try:
            # التحقق من عدم تكرار الكود
            if warehouse.code and self.get_warehouse_by_code(warehouse.code):
                if self.logger:
                    self.logger.warning(f"رمز المستودع {warehouse.code} موجود بالفعل")
                return None
            
            # إذا كان هذا المستودع الافتراضي، إلغاء الافتراضي من الآخرين
            if warehouse.is_default:
                self._unset_default_warehouse()
            
            # تم تحديث الاستعلام ليشمل الحقول الجديدة
            query = """
                INSERT INTO warehouses (
                    code, name, name_en, warehouse_type, capacity, current_utilization,
                    address, city, country, phone, email,
                    manager_name, manager_phone, is_active, is_default, allow_negative_stock,
                    notes, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            params = (
                warehouse.code,
                warehouse.name,
                warehouse.name_en,
                warehouse.warehouse_type,
                float(warehouse.capacity),
                float(warehouse.current_utilization),
                warehouse.address,
                warehouse.city,
                warehouse.country,
                warehouse.phone,
                warehouse.email,
                warehouse.manager_name,
                warehouse.manager_phone,
                1 if warehouse.is_active else 0,
                1 if warehouse.is_default else 0,
                1 if warehouse.allow_negative_stock else 0,
                warehouse.notes,
                warehouse.created_by
            )
            
            # استخدام execute_insert إذا كانت متاحة، أو الطريقة القديمة
            if hasattr(self.db_manager, 'execute_insert'):
                warehouse_id = self.db_manager.execute_insert(query, params)
            else:
                self.db_manager.execute_query(query, params)
                warehouse_id = self.db_manager.get_last_insert_id()
            
            if self.logger:
                self.logger.info(f"تم إنشاء مستودع جديد: {warehouse.name} (ID: {warehouse_id})")
            
            return warehouse_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء المستودع: {str(e)}")
            return None
    
    def get_warehouse_by_id(self, warehouse_id: int) -> Optional[Warehouse]:
        """الحصول على مستودع بالمعرف"""
        try:
            query = "SELECT * FROM warehouses WHERE id = ?"
            result = self.db_manager.execute_query(query, (warehouse_id,))
            
            if result and len(result) > 0:
                # التحويل إلى قاموس إذا كانت النتيجة tuple
                data = result[0]
                if isinstance(data, tuple):
                    # هنا نفترض ترتيب الأعمدة - يفضل استخدام fetch_dict في المستقبل
                    # للتبسيط، إذا كانت tuple نستخدم from_db_row
                    # لكن بما أن الكود الأصلي يستخدم from_dict، سنفترض أن execute_query يرجع dicts
                    # أو أن هناك آلية mapping
                    pass
                return Warehouse.from_dict(data)
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المستودع {warehouse_id}: {str(e)}")
            return None
    
    def get_warehouse_by_code(self, code: str, company_id: Optional[int] = None) -> Optional[Warehouse]:
        """الحصول على مستودع بالرمز"""
        try:
            query = "SELECT * FROM warehouses WHERE code = ?"
            params = [code]
            
            # إضافة فلتر الشركة
            query, params = self._add_company_filter(query, params, company_id)
            
            result = self.db_manager.execute_query(query, tuple(params))
            
            if result and len(result) > 0:
                return Warehouse.from_dict(result[0])
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المستودع {code}: {str(e)}")
            return None
    
    def get_default_warehouse(self) -> Optional[Warehouse]:
        """الحصول على المستودع الافتراضي"""
        try:
            query = "SELECT * FROM warehouses WHERE is_default = 1 AND is_active = 1 LIMIT 1"
            result = self.db_manager.execute_query(query)
            
            if result and len(result) > 0:
                return Warehouse.from_dict(result[0])
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المستودع الافتراضي: {str(e)}")
            return None
    
    def get_all_warehouses(self, include_inactive: bool = False) -> List[Warehouse]:
        """الحصول على جميع المستودعات"""
        try:
            query = "SELECT * FROM warehouses"
            if not include_inactive:
                query += " WHERE is_active = 1"
            query += " ORDER BY is_default DESC, name ASC"
            
            result = self.db_manager.execute_query(query)
            return [Warehouse.from_dict(row) for row in result]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المستودعات: {str(e)}")
            return []
    
    def update_warehouse(self, warehouse: Warehouse) -> bool:
        """تحديث مستودع"""
        try:
            if not warehouse.id:
                return False
            
            # إذا كان هذا المستودع الافتراضي، إلغاء الافتراضي من الآخرين
            if warehouse.is_default:
                self._unset_default_warehouse(exclude_id=warehouse.id)
            
            query = """
                UPDATE warehouses SET
                    code = ?, name = ?, name_en = ?, 
                    warehouse_type = ?, capacity = ?,
                    address = ?, city = ?, country = ?,
                    phone = ?, email = ?, manager_name = ?, manager_phone = ?,
                    is_active = ?, is_default = ?, allow_negative_stock = ?,
                    notes = ?, updated_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            params = (
                warehouse.code,
                warehouse.name,
                warehouse.name_en,
                warehouse.warehouse_type,
                float(warehouse.capacity),
                warehouse.address,
                warehouse.city,
                warehouse.country,
                warehouse.phone,
                warehouse.email,
                warehouse.manager_name,
                warehouse.manager_phone,
                1 if warehouse.is_active else 0,
                1 if warehouse.is_default else 0,
                1 if warehouse.allow_negative_stock else 0,
                warehouse.notes,
                warehouse.updated_by,
                warehouse.id
            )
            
            self.db_manager.execute_query(query, params)
            
            if self.logger:
                self.logger.info(f"تم تحديث المستودع: {warehouse.name} (ID: {warehouse.id})")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المستودع {warehouse.id}: {str(e)}")
            return False
    
    def delete_warehouse(self, warehouse_id: int) -> bool:
        """حذف مستودع"""
        try:
            # التحقق من وجود مخزون في المستودع
            query = "SELECT COUNT(*) as count FROM warehouse_inventory WHERE warehouse_id = ? AND quantity > 0"
            result = self.db_manager.execute_query(query, (warehouse_id,))
            
            count = 0
            if result:
                # التعامل مع أنواع النتائج المختلفة (dict أو tuple)
                row = result[0]
                if isinstance(row, dict):
                    count = row.get('count', 0)
                elif isinstance(row, tuple) or isinstance(row, list):
                    count = row[0]
            
            if count > 0:
                if self.logger:
                    self.logger.warning(f"لا يمكن حذف المستودع {warehouse_id}: يحتوي على مخزون")
                return False
            
            query = "DELETE FROM warehouses WHERE id = ?"
            self.db_manager.execute_query(query, (warehouse_id,))
            
            if self.logger:
                self.logger.info(f"تم حذف المستودع: ID={warehouse_id}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف المستودع {warehouse_id}: {str(e)}")
            return False
    
    def _unset_default_warehouse(self, exclude_id: Optional[int] = None):
        """إلغاء الافتراضي من جميع المستودعات (عدا المستودع المحدد)"""
        try:
            query = "UPDATE warehouses SET is_default = 0"
            params = []
            
            if exclude_id:
                query += " WHERE id != ?"
                params.append(exclude_id)
            
            self.db_manager.execute_query(query, params)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء الافتراضي: {str(e)}")


class WarehouseInventoryManager:
    """مدير مخزون المستودعات"""
    
    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
    
    def get_inventory(self, warehouse_id: int, product_id: int) -> Optional[WarehouseInventory]:
        """الحصول على مخزون منتج في مستودع معين"""
        try:
            query = """
                SELECT wi.*, w.name as warehouse_name, p.name as product_name
                FROM warehouse_inventory wi
                JOIN warehouses w ON wi.warehouse_id = w.id
                JOIN products p ON wi.product_id = p.id
                WHERE wi.warehouse_id = ? AND wi.product_id = ?
            """
            result = self.db_manager.execute_query(query, (warehouse_id, product_id))
            
            if result and len(result) > 0:
                return self._dict_to_inventory(result[0])
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المخزون: {str(e)}")
            return None
    
    def get_warehouse_inventory(self, warehouse_id: int) -> List[WarehouseInventory]:
        """الحصول على جميع المخزون في مستودع معين"""
        try:
            query = """
                SELECT wi.*, w.name as warehouse_name, p.name as product_name
                FROM warehouse_inventory wi
                JOIN warehouses w ON wi.warehouse_id = w.id
                JOIN products p ON wi.product_id = p.id
                WHERE wi.warehouse_id = ?
                ORDER BY p.name
            """
            result = self.db_manager.execute_query(query, (warehouse_id,))
            return [self._dict_to_inventory(row) for row in result]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على مخزون المستودع {warehouse_id}: {str(e)}")
            return []
    
    def get_product_inventory(self, product_id: int) -> List[WarehouseInventory]:
        """الحصول على مخزون منتج في جميع المستودعات"""
        try:
            query = """
                SELECT wi.*, w.name as warehouse_name, p.name as product_name
                FROM warehouse_inventory wi
                JOIN warehouses w ON wi.warehouse_id = w.id
                JOIN products p ON wi.product_id = p.id
                WHERE wi.product_id = ?
                ORDER BY w.name
            """
            result = self.db_manager.execute_query(query, (product_id,))
            return [self._dict_to_inventory(row) for row in result]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على مخزون المنتج {product_id}: {str(e)}")
            return []
    
    def update_quantity(self, warehouse_id: int, product_id: int, quantity: float, 
                        reserved_quantity: float = 0.0) -> bool:
        """تحديث كمية المخزون"""
        try:
            # التحقق من وجود السجل
            existing = self.get_inventory(warehouse_id, product_id)
            
            if existing:
                # تحديث موجود
                query = """
                    UPDATE warehouse_inventory SET
                        quantity = ?,
                        reserved_quantity = ?,
                        last_movement_date = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE warehouse_id = ? AND product_id = ?
                """
                params = (quantity, reserved_quantity, warehouse_id, product_id)
            else:
                # إنشاء جديد
                query = """
                    INSERT INTO warehouse_inventory (
                        warehouse_id, product_id, quantity, reserved_quantity,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                params = (warehouse_id, product_id, quantity, reserved_quantity)
            
            self.db_manager.execute_query(query, params)
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث كمية المخزون: {str(e)}")
            return False
    
    def adjust_quantity(self, warehouse_id: int, product_id: int, quantity_diff: float) -> bool:
        """تعديل كمية المخزون (إضافة أو طرح)"""
        try:
            existing = self.get_inventory(warehouse_id, product_id)
            
            if existing:
                new_quantity = existing.quantity + quantity_diff
                if new_quantity < 0:
                    if self.logger:
                        self.logger.warning(f"الكمية الناتجة سالبة: {new_quantity}")
                    return False
                return self.update_quantity(warehouse_id, product_id, new_quantity, existing.reserved_quantity)
            else:
                if quantity_diff < 0:
                    if self.logger:
                        self.logger.warning(f"لا يمكن طرح من مخزون غير موجود")
                    return False
                return self.update_quantity(warehouse_id, product_id, quantity_diff)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعديل كمية المخزون: {str(e)}")
            return False
    
    def reserve_quantity(self, warehouse_id: int, product_id: int, quantity: float) -> bool:
        """حجز كمية من المخزون"""
        try:
            existing = self.get_inventory(warehouse_id, product_id)
            if not existing:
                return False
            
            new_reserved = existing.reserved_quantity + quantity
            if new_reserved > existing.quantity:
                if self.logger:
                    self.logger.warning(f"الكمية المحجوزة تتجاوز المخزون المتاح")
                return False
            
            query = """
                UPDATE warehouse_inventory SET
                    reserved_quantity = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE warehouse_id = ? AND product_id = ?
            """
            self.db_manager.execute_query(query, (new_reserved, warehouse_id, product_id))
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حجز الكمية: {str(e)}")
            return False
    
    def release_reserved(self, warehouse_id: int, product_id: int, quantity: float) -> bool:
        """إلغاء حجز كمية"""
        try:
            existing = self.get_inventory(warehouse_id, product_id)
            if not existing:
                return False
            
            new_reserved = max(0, existing.reserved_quantity - quantity)
            
            query = """
                UPDATE warehouse_inventory SET
                    reserved_quantity = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE warehouse_id = ? AND product_id = ?
            """
            self.db_manager.execute_query(query, (new_reserved, warehouse_id, product_id))
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء الحجز: {str(e)}")
            return False
    
    def _dict_to_inventory(self, data: Dict[str, Any]) -> WarehouseInventory:
        """تحويل قاموس إلى WarehouseInventory"""
        return WarehouseInventory(
            id=data.get('id'),
            warehouse_id=data.get('warehouse_id', 0),
            product_id=data.get('product_id', 0),
            quantity=data.get('quantity', 0.0),
            reserved_quantity=data.get('reserved_quantity', 0.0),
            available_quantity=data.get('available_quantity', 0.0),
            min_stock=data.get('min_stock', 0.0),
            max_stock=data.get('max_stock', 0.0),
            reorder_point=data.get('reorder_point', 0.0),
            last_movement_date=datetime.fromisoformat(data['last_movement_date']) if data.get('last_movement_date') else None,
            last_count_date=datetime.fromisoformat(data['last_count_date']) if data.get('last_count_date') else None,
            notes=data.get('notes'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            warehouse_name=data.get('warehouse_name'),
            product_name=data.get('product_name')
        )


class WarehouseTransferManager:
    """مدير نقل المخزون بين المستودعات"""
    
    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.inventory_manager = WarehouseInventoryManager(db_manager, logger)
    
    def generate_transfer_number(self) -> str:
        """إنشاء رقم تحويل فريد"""
        try:
            # الحصول على آخر رقم تحويل
            query = "SELECT transfer_number FROM warehouse_transfers ORDER BY id DESC LIMIT 1"
            result = self.db_manager.execute_query(query)
            
            if result and result[0].get('transfer_number'):
                last_number = result[0]['transfer_number']
                # استخراج الرقم وزيادته
                if last_number.startswith('TRF-'):
                    try:
                        num = int(last_number.split('-')[1])
                        return f"TRF-{num + 1:06d}"
                    except:
                        pass
            
            # رقم جديد
            return "TRF-000001"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء رقم التحويل: {str(e)}")
            return f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def create_transfer(self, transfer: WarehouseTransfer) -> Optional[int]:
        """إنشاء تحويل جديد"""
        try:
            # التحقق من توفر الكمية في المستودع المصدر
            source_inventory = self.inventory_manager.get_inventory(
                transfer.from_warehouse_id, transfer.product_id
            )
            
            if not source_inventory or source_inventory.available_quantity < transfer.quantity:
                if self.logger:
                    self.logger.warning(f"كمية غير كافية في المستودع المصدر")
                return None
            
            # إنشاء رقم التحويل إذا لم يكن موجوداً
            if not transfer.transfer_number:
                transfer.transfer_number = self.generate_transfer_number()
            
            query = """
                INSERT INTO warehouse_transfers (
                    transfer_number, from_warehouse_id, to_warehouse_id,
                    product_id, quantity, status, transfer_date, notes,
                    created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            params = (
                transfer.transfer_number,
                transfer.from_warehouse_id,
                transfer.to_warehouse_id,
                transfer.product_id,
                transfer.quantity,
                transfer.status,
                transfer.transfer_date or datetime.now(),
                transfer.notes,
                transfer.created_by
            )
            
            # استخدام execute_insert إذا كانت متاحة، أو الطريقة القديمة
            if hasattr(self.db_manager, 'execute_insert'):
                transfer_id = self.db_manager.execute_insert(query, params)
            else:
                self.db_manager.execute_query(query, params)
                transfer_id = self.db_manager.get_last_insert_id()
            
            # حجز الكمية في المستودع المصدر
            self.inventory_manager.reserve_quantity(
                transfer.from_warehouse_id, transfer.product_id, transfer.quantity
            )
            
            if self.logger:
                self.logger.info(f"تم إنشاء تحويل: {transfer.transfer_number} (ID: {transfer_id})")
            
            return transfer_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء التحويل: {str(e)}")
            return None
    
    def complete_transfer(self, transfer_id: int, received_by: Optional[int] = None) -> bool:
        """إكمال التحويل (استلام في المستودع الهدف)"""
        try:
            # الحصول على التحويل
            transfer = self.get_transfer_by_id(transfer_id)
            if not transfer:
                return False
            
            if transfer.status != 'pending' and transfer.status != 'in_transit':
                if self.logger:
                    self.logger.warning(f"التحويل في حالة {transfer.status} ولا يمكن إكماله")
                return False
            
            # استخدام Transaction لضمان Atomicity
            if hasattr(self.db_manager, 'get_cursor'):
                with self.db_manager.get_cursor() as cursor:
                    try:
                        # 1. إلغاء الحجز من المصدر
                        release_query = """
                            UPDATE warehouse_inventory SET
                                reserved_quantity = reserved_quantity - ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE warehouse_id = ? AND product_id = ?
                        """
                        cursor.execute(release_query, (
                            transfer.quantity,
                            transfer.from_warehouse_id,
                            transfer.product_id
                        ))
                        
                        # 2. طرح الكمية من المصدر
                        subtract_query = """
                            UPDATE warehouse_inventory SET
                                quantity = quantity - ?,
                                last_movement_date = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE warehouse_id = ? AND product_id = ?
                        """
                        cursor.execute(subtract_query, (
                            transfer.quantity,
                            transfer.from_warehouse_id,
                            transfer.product_id
                        ))
                        
                        # 3. إضافة الكمية إلى الهدف (INSERT OR UPDATE)
                        check_query = """
                            SELECT id FROM warehouse_inventory 
                            WHERE warehouse_id = ? AND product_id = ?
                        """
                        cursor.execute(check_query, (transfer.to_warehouse_id, transfer.product_id))
                        exists = cursor.fetchone()
                        
                        if exists:
                            add_query = """
                                UPDATE warehouse_inventory SET
                                    quantity = quantity + ?,
                                    last_movement_date = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE warehouse_id = ? AND product_id = ?
                            """
                            cursor.execute(add_query, (
                                transfer.quantity,
                                transfer.to_warehouse_id,
                                transfer.product_id
                            ))
                        else:
                            insert_query = """
                                INSERT INTO warehouse_inventory (
                                    warehouse_id, product_id, quantity,
                                    created_at, updated_at
                                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """
                            cursor.execute(insert_query, (
                                transfer.to_warehouse_id,
                                transfer.product_id,
                                transfer.quantity
                            ))
                        
                        # 4. تحديث حالة التحويل
                        update_query = """
                            UPDATE warehouse_transfers SET
                                status = 'completed',
                                received_date = CURRENT_TIMESTAMP,
                                received_by = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """
                        cursor.execute(update_query, (received_by, transfer_id))
                        
                        cursor.connection.commit()
                        
                        if self.logger:
                            self.logger.info(f"تم إكمال التحويل: ID={transfer_id}")
                        
                        return True
                        
                    except Exception as e:
                        cursor.connection.rollback()
                        if self.logger:
                            self.logger.error(f"خطأ في إكمال التحويل {transfer_id}: {str(e)}")
                        return False
            else:
                # Fallback implementation omitted for brevity, assuming DB manager has cursor support
                if self.logger:
                    self.logger.error("لا يمكن إكمال التحويل: قاعدة البيانات لا تدعم المعاملات (Transactions)")
                return False
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ عام في إكمال التحويل {transfer_id}: {str(e)}")
            return False
    
    def get_transfer_by_id(self, transfer_id: int) -> Optional[WarehouseTransfer]:
        """الحصول على تحويل بالمعرف"""
        try:
            query = """
                SELECT wt.*, 
                       w1.name as from_warehouse_name,
                       w2.name as to_warehouse_name,
                       p.name as product_name
                FROM warehouse_transfers wt
                JOIN warehouses w1 ON wt.from_warehouse_id = w1.id
                JOIN warehouses w2 ON wt.to_warehouse_id = w2.id
                JOIN products p ON wt.product_id = p.id
                WHERE wt.id = ?
            """
            result = self.db_manager.execute_query(query, (transfer_id,))
            
            if result and len(result) > 0:
                return self._dict_to_transfer(result[0])
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على التحويل {transfer_id}: {str(e)}")
            return None
    
    def get_transfers(self, warehouse_id: Optional[int] = None, 
                      status: Optional[str] = None) -> List[WarehouseTransfer]:
        """الحصول على قائمة التحويلات"""
        try:
            query = """
                SELECT wt.*, 
                       w1.name as from_warehouse_name,
                       w2.name as to_warehouse_name,
                       p.name as product_name
                FROM warehouse_transfers wt
                JOIN warehouses w1 ON wt.from_warehouse_id = w1.id
                JOIN warehouses w2 ON wt.to_warehouse_id = w2.id
                JOIN products p ON wt.product_id = p.id
                WHERE 1=1
            """
            params = []
            
            if warehouse_id:
                query += " AND (wt.from_warehouse_id = ? OR wt.to_warehouse_id = ?)"
                params.extend([warehouse_id, warehouse_id])
            
            if status:
                query += " AND wt.status = ?"
                params.append(status)
            
            query += " ORDER BY wt.transfer_date DESC"
            
            result = self.db_manager.execute_query(query, params)
            return [self._dict_to_transfer(row) for row in result]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على التحويلات: {str(e)}")
            return []
    
    def _dict_to_transfer(self, data: Dict[str, Any]) -> WarehouseTransfer:
        """تحويل قاموس إلى WarehouseTransfer"""
        return WarehouseTransfer(
            id=data.get('id'),
            transfer_number=data.get('transfer_number', ''),
            from_warehouse_id=data.get('from_warehouse_id', 0),
            to_warehouse_id=data.get('to_warehouse_id', 0),
            product_id=data.get('product_id', 0),
            quantity=data.get('quantity', 0.0),
            status=data.get('status', 'pending'),
            transfer_date=datetime.fromisoformat(data['transfer_date']) if data.get('transfer_date') else None,
            received_date=datetime.fromisoformat(data['received_date']) if data.get('received_date') else None,
            notes=data.get('notes'),
            created_by=data.get('created_by'),
            received_by=data.get('received_by'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            from_warehouse_name=data.get('from_warehouse_name'),
            to_warehouse_name=data.get('to_warehouse_name'),
            product_name=data.get('product_name')
        )