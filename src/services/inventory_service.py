#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة المخزون - Inventory Service
تحتوي على جميع العمليات المتعلقة بإدارة المخزون والمنتجات
محسنة لاستخدام DatabaseManager المطور مع معالجة مرنة للبيانات
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.models.category import CategoryManager
from src.models.product import Product, ProductManager
from src.models.supplier import SupplierManager
from src.utils.logger import setup_logger


def get_value(row: Any, key: Any, default: Any = None) -> Any:
    """استخراج قيمة من صف نتيجة قاعدة بيانات (tuple أو dict) بأمان.

    يعالج الحالة التي قد يكون فيها الصف tuple أو dict
    بدون الحاجة لفحص النوع في كل مكان.

    Args:
        row: صف نتيجة من قاعدة البيانات (tuple أو dict)
        key: مفتاح (فهرس رقمي لـ tuple، أو مفتاح نصي لـ dict)
        default: القيمة الافتراضية إذا لم يُعثر على القيمة

    Returns:
        القيمة المطلوبة أو القيمة الافتراضية
    """
    if isinstance(row, (list, tuple)):
        try:
            return row[key] if 0 <= key < len(row) else default
        except (IndexError, TypeError):
            return default
    if isinstance(row, dict):
        return row.get(key, default)
    return default


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
    product_name: Optional[str] = None  # اسم المنتج (من JOIN)


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
        self.logger = logger or setup_logger(__name__)
        self.product_manager = ProductManager(db_manager, self.logger)
        self.category_manager = CategoryManager(db_manager, self.logger)
        self.supplier_manager = SupplierManager(db_manager, self.logger)

        # Multi-Warehouse Support (Optional - يتم تحميله عند الحاجة)
        self._warehouse_service = None

    @property
    def warehouse_service(self):
        """Lazy loading لـ WarehouseService"""
        if self._warehouse_service is None:
            try:
                from src.services.warehouse_service import WarehouseService

                self._warehouse_service = WarehouseService(self.db_manager, self.logger)
            except ImportError:
                if self.logger:
                    self.logger.warning("WarehouseService غير متاح - Multi-Warehouse غير مفعل")
        return self._warehouse_service

    def is_multi_warehouse_enabled(self) -> bool:
        """التحقق من تفعيل Multi-Warehouse"""
        return self.warehouse_service is not None

    def _parse_datetime(self, val):
        """معالجة التواريخ بشكل موحد"""
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception:
                try:
                    return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return None
        return None

    def search_products(
        self,
        query: str = "",
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Product]:
        """البحث عن المنتجات مع فلاتر"""
        try:
            return self.product_manager.search_products(query, category_id, active_only, limit)
        except Exception as e:
            self.logger.warning(f"خطأ في البحث عن المنتجات: {str(e)}")
            return []

    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        """الحصول على منتج بالباركود"""
        try:
            return self.product_manager.get_product_by_barcode(barcode)
        except Exception as e:
            self.logger.warning(f"خطأ في الحصول على المنتج بالباركود: {str(e)}")
            return None

    def update_product(self, product: Product) -> bool:
        """تحديث منتج مع تتبع تغيير المخزون"""
        try:
            old_product = self.product_manager.get_product_by_id(product.id)
            if old_product is None:
                self.logger.warning(f"المنتج {product.id} غير موجود")
                return False
            if self.product_manager.update_product(product):
                if old_product and product.current_stock != old_product.current_stock:
                    diff = product.current_stock - old_product.current_stock
                    self._record_stock_movement(
                        product_id=product.id,
                        movement_type="in" if diff > 0 else "out",
                        quantity=abs(diff),
                        reference_type="adjustment",
                        notes="تحديث المخزون عبر تحديث المنتج",
                    )
                return True
            return False
        except Exception as e:
            self.logger.warning(f"خطأ في تحديث المنتج: {str(e)}")
            return False

    def delete_product(self, product_id: int, hard_delete: bool = False) -> bool:
        """حذف منتج"""
        try:
            return self.product_manager.delete_product(product_id, hard_delete)
        except Exception as e:
            self.logger.warning(f"خطأ في حذف المنتج: {str(e)}")
            return False

    def transfer_stock(self, from_product_id: int, to_product_id: int, quantity: float) -> bool:
        """نقل مخزون بين منتجين"""
        try:
            if from_product_id == to_product_id:
                self.logger.warning("لا يمكن نقل المخزون لنفس المنتج")
                return False
            from_product = self.product_manager.get_product_by_id(from_product_id)
            to_product = self.product_manager.get_product_by_id(to_product_id)
            if not from_product or not to_product:
                return False
            if from_product.current_stock < quantity:
                return False
            if not self.product_manager.update_stock(from_product_id, round(from_product.current_stock - quantity, 2)):
                return False
            if not self.product_manager.update_stock(to_product_id, round(to_product.current_stock + quantity, 2)):
                self.product_manager.update_stock(from_product_id, round(from_product.current_stock, 2))
                return False
            self._record_stock_movement(
                from_product_id,
                "out",
                quantity,
                reference_type="transfer",
                notes=f"تحويل إلى المنتج {to_product_id}",
            )
            self._record_stock_movement(
                to_product_id,
                "in",
                quantity,
                reference_type="transfer",
                notes=f"تحويل من المنتج {from_product_id}",
            )
            return True
        except Exception as e:
            self.logger.warning(f"خطأ في نقل المخزون: {str(e)}")
            return False

    def add_category(self, category) -> Optional[int]:
        """إضافة فئة جديدة"""
        try:
            return self.category_manager.create_category(category)
        except Exception as e:
            self.logger.warning(f"خطأ في إضافة الفئة: {str(e)}")
            return None

    def get_category_tree(self) -> List[Dict[str, Any]]:
        """الحصول على شجرة الفئات"""
        try:
            return self.category_manager.get_category_tree()
        except Exception as e:
            self.logger.warning(f"خطأ في الحصول على شجرة الفئات: {str(e)}")
            return []

    # ===== إدارة المنتجات =====

    def add_product(self, product: Product) -> Optional[int]:
        """إضافة منتج جديد"""
        try:
            if product.barcode and self.product_manager.get_product_by_barcode(product.barcode):
                self.logger.warning(f"الباركود {product.barcode} موجود بالفعل")
                return None

            product_id = self.product_manager.create_product(product)
            if product_id and product.current_stock > 0:
                self._record_stock_movement(
                    product_id=product_id,
                    movement_type="in",
                    quantity=product.current_stock,
                    reference_type="initial",
                    notes="رصيد أولي",
                )
            return product_id
        except Exception as e:
            self.logger.warning(f"خطأ في إضافة المنتج: {str(e)}")
            return None

    def adjust_stock(
        self,
        product_id: int,
        new_quantity: float,
        reason: str = "",
        user_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
    ) -> bool:
        """تعديل كمية المخزون مع دعم المستودعات المتعددة"""
        try:
            if self.is_multi_warehouse_enabled():
                if warehouse_id is None:
                    default_wh = self.warehouse_service.get_default_warehouse()
                    warehouse_id = default_wh.id if default_wh else None

                if warehouse_id is not None:
                    inventory = self.warehouse_service.inventory_manager.get_inventory(warehouse_id, product_id)
                    old_qty = inventory.quantity if inventory else 0.0
                    diff = new_quantity - old_qty

                    if self.warehouse_service.adjust_stock(warehouse_id, product_id, diff):
                        self._record_stock_movement(
                            product_id=product_id,
                            movement_type="in" if diff > 0 else "out",
                            quantity=abs(diff),
                            reference_type="adjustment",
                            notes=f"تعديل المخزون (مستودع {warehouse_id}): {reason}",
                            created_by=user_id,
                        )
                        # تحديث المخزون الإجمالي للتوافق
                        total_stock = self.warehouse_service.get_total_stock(product_id)
                        self.product_manager.update_stock(product_id, round(total_stock, 2))
                        return True

            # الحالة الافتراضية (Single Warehouse)
            product = self.product_manager.get_product_by_id(product_id)
            if not product:
                return False

            diff = new_quantity - product.current_stock
            if self.product_manager.update_stock(product_id, round(new_quantity, 2)):
                self._record_stock_movement(
                    product_id=product_id,
                    movement_type="in" if diff > 0 else "out",
                    quantity=abs(diff),
                    reference_type="adjustment",
                    notes=f"تعديل المخزون: {reason}",
                    created_by=user_id,
                )
                return True
            return False
        except Exception as e:
            self.logger.warning(f"خطأ في تعديل مخزون المنتج {product_id}: {str(e)}")
            return False

    def adjust_stock_relative(
        self,
        product_id: int,
        diff: float,
        reason: str = "",
        user_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
    ) -> bool:
        """تعديل المخزون بشكل نسبي (ذري)"""
        try:
            if self.is_multi_warehouse_enabled():
                if warehouse_id is None:
                    default_wh = self.warehouse_service.get_default_warehouse()
                    warehouse_id = default_wh.id if default_wh else None

                if warehouse_id is not None:
                    if self.warehouse_service.adjust_stock(warehouse_id, product_id, diff):
                        self._record_stock_movement(
                            product_id=product_id,
                            movement_type="in" if diff > 0 else "out",
                            quantity=abs(diff),
                            reference_type="adjustment",
                            notes=f"تعديل المخزون النسبي (مستودع {warehouse_id}): {reason}",
                            created_by=user_id,
                        )
                        # تحديث المخزون الإجمالي للتوافق بشكل نسبي
                        self.product_manager.adjust_stock_relative(product_id, diff)
                        return True

            # الحالة الافتراضية (Single Warehouse)
            if self.product_manager.adjust_stock_relative(product_id, diff):
                self._record_stock_movement(
                    product_id=product_id,
                    movement_type="in" if diff > 0 else "out",
                    quantity=abs(diff),
                    reference_type="adjustment",
                    notes=f"تعديل المخزون النسبي: {reason}",
                    created_by=user_id,
                )
                return True
            return False
        except Exception as e:
            self.logger.warning(f"خطأ في التعديل النسبي للمخزون {product_id}: {str(e)}")
            return False

    def get_stock_movements(
        self,
        product_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[StockMovement]:
        """الحصول على حركات المخزون بنمط Mapping مرن"""
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

            rows = self.db_manager.fetch_all(query, params)
            movements = []
            for row in rows:
                movements.append(
                    StockMovement(
                        id=get_value(row, "id" if isinstance(row, dict) else 0),
                        product_id=get_value(row, "product_id" if isinstance(row, dict) else 1, 0),
                        movement_type=get_value(row, "movement_type" if isinstance(row, dict) else 2, ""),
                        quantity=float(get_value(row, "quantity" if isinstance(row, dict) else 3, 0)),
                        reference_id=get_value(row, "reference_id" if isinstance(row, dict) else 4),
                        reference_type=get_value(row, "reference_type" if isinstance(row, dict) else 5),
                        notes=get_value(row, "notes" if isinstance(row, dict) else 6),
                        created_by=get_value(row, "user_id" if isinstance(row, dict) else 7),
                        created_at=self._parse_datetime(get_value(row, "created_at" if isinstance(row, dict) else 8)),
                        product_name=get_value(row, "product_name" if isinstance(row, dict) else 9),
                    )
                )
            return movements
        except Exception as e:
            self.logger.warning(f"خطأ في الحصول على حركات المخزون: {str(e)}")
            return []

    def get_stock_alerts(self) -> List[StockAlert]:
        """تنبيهات المخزون بنمط Mapping مرن"""
        try:
            query = """
            SELECT id, name, current_stock, min_stock
            FROM products
            WHERE is_active = 1 AND current_stock <= min_stock
            ORDER BY current_stock ASC, name LIMIT 100
            """
            rows = self.db_manager.fetch_all(query)
            alerts = []
            for row in rows:
                pid = get_value(row, "id" if isinstance(row, dict) else 0)
                name_val = get_value(row, "name" if isinstance(row, dict) else 1)
                curr = float(get_value(row, "current_stock" if isinstance(row, dict) else 2, 0))
                mins = float(get_value(row, "min_stock" if isinstance(row, dict) else 3, 0))

                alerts.append(
                    StockAlert(
                        product_id=pid,
                        product_name=name_val,
                        current_stock=curr,
                        minimum_stock=mins,
                        alert_type="out_of_stock" if curr <= 0 else "low_stock",
                        severity="critical" if curr <= 0 else "high",
                        message=f"المنتج {name_val} {'نفد من المخزون' if curr <= 0 else f'مخزون منخفض ({curr})'}",
                    )
                )
            return alerts
        except Exception as e:
            self.logger.warning(f"خطأ في تنبيهات المخزون: {str(e)}")
            return []

    def generate_inventory_report(self, include_movements: bool = True) -> InventoryReport:
        """إنشاء تقرير شامل للمخزون"""
        try:
            stock_report = self.product_manager.get_stock_report()

            # إحصائيات إضافية
            cat_count = self.db_manager.fetch_one("SELECT COUNT(*) FROM categories")[0]
            out_count = self.db_manager.fetch_one(
                "SELECT COUNT(*) FROM products WHERE is_active=1 AND current_stock<=0"
            )[0]

            report = InventoryReport(
                total_products=stock_report.get("total_products", 0),
                total_categories=cat_count,
                total_stock_value=stock_report.get("total_stock_value", 0.0),
                low_stock_items=stock_report.get("low_stock_products", 0),
                out_of_stock_items=out_count,
                expired_items=0,  # قيد التطوير
                top_products=self._get_top_products_by_value(limit=10),
                stock_movements=([m.__dict__ for m in self.get_stock_movements(limit=50)] if include_movements else []),
                alerts=self.get_stock_alerts(),
            )
            return report
        except Exception as e:
            self.logger.warning(f"خطأ في تقرير المخزون: {str(e)}")
            return InventoryReport(0, 0, 0, 0, 0, 0, [], [], [])

    def _get_expired_products(self) -> List[Product]:
        """الحصول على المنتجات المنتهية الصلاحية"""
        return []

    def _record_stock_movement(
        self,
        product_id: int,
        movement_type: str,
        quantity: float,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[int] = None,
    ):
        """تسجيل حركة مخزون باستخدام execute_insert لضمان التوافق"""
        try:
            query = """
            INSERT INTO stock_movements (
                product_id, movement_type, quantity, reference_id,
                reference_type, notes, user_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                product_id,
                movement_type,
                quantity,
                reference_id,
                reference_type,
                notes,
                created_by,
            )
            self.db_manager.execute_insert(query, params)
        except Exception as e:
            self.logger.warning(f"خطأ في تسجيل حركة المخزون: {str(e)}")

    def _get_top_products_by_value(self, limit: int = 10) -> List[Dict[str, Any]]:
        """أفضل المنتجات حسب القيمة مع Mapping مرن"""
        try:
            query = """
            SELECT id, name, current_stock, cost_price, selling_price,
                   COALESCE(current_stock * cost_price, current_stock * selling_price * 0.7, 0) as stock_value
            FROM products WHERE is_active = 1 AND current_stock > 0
            ORDER BY stock_value DESC LIMIT ?
            """
            rows = self.db_manager.fetch_all(query, (limit,))
            results = []
            for row in rows:
                results.append(
                    {
                        "id": get_value(row, "id" if isinstance(row, dict) else 0),
                        "name": get_value(row, "name" if isinstance(row, dict) else 1),
                        "current_stock": get_value(row, "current_stock" if isinstance(row, dict) else 2),
                        "cost_price": get_value(row, "cost_price" if isinstance(row, dict) else 3),
                        "selling_price": get_value(row, "selling_price" if isinstance(row, dict) else 4),
                        "stock_value": get_value(row, "stock_value" if isinstance(row, dict) else 5),
                    }
                )
            return results
        except Exception as e:
            self.logger.warning(f"خطأ في جلب أفضل المنتجات: {str(e)}")
            return []
