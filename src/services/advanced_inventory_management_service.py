#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
خدمة إدارة المخزون المتقدمة - Advanced Inventory Management Service
نظام إدارة مخزون متقدم مع تتبع الدفعات والصلاحية
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.services.sales_prediction_service import SalesPredictionService
from src.utils.db_helpers import get_value
from src.utils.logger import setup_logger


@dataclass
class InventoryItem:
    """عنصر مخزون"""

    product_id: int
    warehouse_id: int
    batch_id: str
    quantity: int
    unit_cost: Decimal
    expiry_date: Optional[datetime]
    location: str
    status: str  # 'active', 'reserved', 'damaged', 'expired'
    created_at: datetime


@dataclass
class InventoryAlert:
    """تنبيه مخزون"""

    alert_id: str
    product_id: int
    alert_type: str  # 'low_stock', 'expiry_warning', 'overstock', 'damaged'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    suggested_action: str
    created_at: datetime


@dataclass
class InventoryTransaction:
    """معاملة مخزون"""

    transaction_id: str
    product_id: int
    transaction_type: str  # 'inbound', 'outbound', 'adjustment', 'transfer'
    quantity: int
    unit_cost: Decimal
    reference_id: str  # sale_id, purchase_id, etc.
    warehouse_from: Optional[int]
    warehouse_to: Optional[int]
    performed_by: int
    notes: str
    created_at: datetime


@dataclass
class Warehouse:
    """مستودع"""

    warehouse_id: int
    name: str
    location: str
    capacity: int
    current_utilization: float
    status: str  # 'active', 'inactive', 'maintenance'
    manager_id: Optional[int]


@dataclass
class InventoryOptimization:
    """تحسين المخزون"""

    product_id: int
    current_stock: int
    optimal_stock: int
    reorder_point: int
    safety_stock: int
    recommended_action: str
    expected_savings: Decimal
    confidence_score: float


class AdvancedInventoryManagementService:
    """خدمة إدارة المخزون المتقدمة"""

    def __init__(self, db_manager: DatabaseManager, prediction_service: SalesPredictionService):
        self.db = db_manager
        self.prediction_service = prediction_service
        self.config = ConfigManager()
        self.logger = setup_logger(__name__)

        # معلمات التكوين
        self.low_stock_threshold = self.config.get("inventory.low_stock_threshold", 0.2)  # 20% من الحد الأدنى
        self.expiry_warning_days = self.config.get("inventory.expiry_warning_days", 30)
        self.overstock_threshold = self.config.get("inventory.overstock_threshold", 1.5)  # 150% من الحد الأقصى
        self.auto_reorder_enabled = self.config.get("inventory.auto_reorder_enabled", True)

        # تحميل بيانات المستودعات
        self._load_warehouses()

    def add_inventory_item(
        self,
        product_id: int,
        warehouse_id: int,
        batch_id: str,
        quantity: int,
        unit_cost: Decimal,
        expiry_date: Optional[datetime] = None,
        location: str = "default",
        performed_by: int = 1,
    ) -> str:
        """
        إضافة عنصر مخزون جديد

        Args:
            product_id: معرف المنتج
            warehouse_id: معرف المستودع
            batch_id: معرف الدفعة
            quantity: الكمية
            unit_cost: تكلفة الوحدة
            expiry_date: تاريخ الصلاحية
            location: الموقع في المستودع
            performed_by: معرف المستخدم الذي قام بالعملية

        Returns:
            معرف المعاملة
        """
        try:
            transaction_id = f"INV_IN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # إدراج في جدول المخزون
            inventory_data = {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "batch_id": batch_id,
                "quantity": quantity,
                "unit_cost": str(unit_cost),
                "expiry_date": expiry_date.isoformat() if expiry_date else None,
                "location": location,
                "status": "active",
                "created_at": datetime.now().isoformat(),
            }

            # إدراج معاملة المخزون
            transaction_data = {
                "transaction_id": transaction_id,
                "product_id": product_id,
                "transaction_type": "inbound",
                "quantity": quantity,
                "unit_cost": str(unit_cost),
                "reference_id": batch_id,
                "warehouse_to": warehouse_id,
                "performed_by": performed_by,
                "notes": f"إضافة دفعة {batch_id} للمخزون",
                "created_at": datetime.now().isoformat(),
            }

            # تحديث كمية المنتج في المستودع
            self._update_product_stock(product_id, warehouse_id, quantity)

            # إدراج البيانات في قاعدة البيانات
            self._insert_inventory_data(inventory_data, transaction_data)

            return transaction_id

        except Exception as e:
            self.logger.error(f"Error adding inventory item: {e}", exc_info=True)
            raise

    def remove_inventory_item(
        self,
        product_id: int,
        warehouse_id: int,
        batch_id: str,
        quantity: int,
        reason: str = "sale",
        reference_id: str = "",
        performed_by: int = 1,
    ) -> str:
        """
        إزالة عنصر من المخزون

        Args:
            product_id: معرف المنتج
            warehouse_id: معرف المستودع
            batch_id: معرف الدفعة
            quantity: الكمية المراد إزالتها
            reason: سبب الإزالة
            reference_id: معرف المرجع
            performed_by: معرف المستخدم

        Returns:
            معرف المعاملة
        """
        try:
            transaction_id = f"INV_OUT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # التحقق من توفر الكمية
            available_quantity = self._get_batch_quantity(product_id, warehouse_id, batch_id)
            if available_quantity < quantity:
                raise ValueError(f"الكمية المتاحة ({available_quantity}) أقل من الكمية المطلوبة ({quantity})")

            # إدراج معاملة المخزون
            transaction_data = {
                "transaction_id": transaction_id,
                "product_id": product_id,
                "transaction_type": "outbound",
                "quantity": -quantity,  # سالب للإخراج
                "unit_cost": str(self._get_batch_cost(product_id, batch_id)),
                "reference_id": reference_id,
                "warehouse_from": warehouse_id,
                "performed_by": performed_by,
                "notes": f"{reason}: إزالة {quantity} من دفعة {batch_id}",
                "created_at": datetime.now().isoformat(),
            }

            # تحديث كمية الدفعة
            self._update_batch_quantity(product_id, warehouse_id, batch_id, -quantity)

            # تحديث كمية المنتج في المستودع
            self._update_product_stock(product_id, warehouse_id, -quantity)

            # إدراج البيانات في قاعدة البيانات
            self._insert_transaction_data(transaction_data)

            return transaction_id

        except Exception as e:
            self.logger.error(f"Error removing inventory item: {e}", exc_info=True)
            raise

    def transfer_inventory(
        self,
        product_id: int,
        batch_id: str,
        from_warehouse: int,
        to_warehouse: int,
        quantity: int,
        performed_by: int = 1,
    ) -> str:
        """
        نقل مخزون بين المستودعات

        Args:
            product_id: معرف المنتج
            batch_id: معرف الدفعة
            from_warehouse: المستودع المصدر
            to_warehouse: المستودع الوجهة
            quantity: الكمية المراد نقلها
            performed_by: معرف المستخدم

        Returns:
            معرف المعاملة
        """
        try:
            transaction_id = f"INV_TRANS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # التحقق من توفر الكمية في المستودع المصدر
            available_quantity = self._get_batch_quantity(product_id, from_warehouse, batch_id)
            if available_quantity < quantity:
                raise ValueError(
                    f"الكمية المتاحة في المستودع المصدر ({available_quantity}) أقل من الكمية المطلوبة ({quantity})"
                )

            # إدراج معاملة النقل
            transaction_data = {
                "transaction_id": transaction_id,
                "product_id": product_id,
                "transaction_type": "transfer",
                "quantity": quantity,
                "unit_cost": str(self._get_batch_cost(product_id, batch_id)),
                "reference_id": f"{from_warehouse}->{to_warehouse}",
                "warehouse_from": from_warehouse,
                "warehouse_to": to_warehouse,
                "performed_by": performed_by,
                "notes": f"نقل {quantity} من دفعة {batch_id} من مستودع {from_warehouse} إلى {to_warehouse}",
                "created_at": datetime.now().isoformat(),
            }

            # تحديث الكميات في المستودعات
            self._update_batch_quantity(product_id, from_warehouse, batch_id, -quantity)
            self._update_batch_quantity(product_id, to_warehouse, batch_id, quantity)

            # تحديث إجمالي المخزون
            self._update_product_stock(product_id, from_warehouse, -quantity)
            self._update_product_stock(product_id, to_warehouse, quantity)

            # إدراج البيانات في قاعدة البيانات
            self._insert_transaction_data(transaction_data)

            return transaction_id

        except Exception as e:
            self.logger.error(f"Error transferring inventory: {e}", exc_info=True)
            raise

    def get_inventory_alerts(self, warehouse_id: Optional[int] = None) -> List[InventoryAlert]:
        """
        الحصول على تنبيهات المخزون

        Args:
            warehouse_id: معرف المستودع (اختياري)

        Returns:
            قائمة بتنبيهات المخزون
        """
        alerts = []

        try:
            # تنبيهات المخزون المنخفض
            low_stock_alerts = self._check_low_stock_alerts(warehouse_id)
            alerts.extend(low_stock_alerts)

            # تنبيهات الصلاحية
            expiry_alerts = self._check_expiry_alerts(warehouse_id)
            alerts.extend(expiry_alerts)

            # تنبيهات الزيادة في المخزون
            overstock_alerts = self._check_overstock_alerts(warehouse_id)
            alerts.extend(overstock_alerts)

            # تنبيهات المنتجات التالفة
            damaged_alerts = self._check_damaged_stock_alerts(warehouse_id)
            alerts.extend(damaged_alerts)

            return alerts

        except Exception as e:
            self.logger.error(f"Error getting inventory alerts: {e}", exc_info=True)
            return []

    def optimize_inventory(self, product_id: Optional[int] = None) -> List[InventoryOptimization]:
        """
        تحسين مستويات المخزون

        Args:
            product_id: معرف المنتج (اختياري، None لجميع المنتجات)

        Returns:
            قائمة بتوصيات التحسين
        """
        optimizations = []

        try:
            products = self._get_products_for_optimization(product_id)

            for product in products:
                optimization = self._calculate_inventory_optimization(product)
                if optimization:
                    optimizations.append(optimization)

            return optimizations

        except Exception as e:
            self.logger.error(f"Error optimizing inventory: {e}", exc_info=True)
            return []

    def get_inventory_report(
        self,
        warehouse_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        الحصول على تقرير المخزون

        Args:
            warehouse_id: معرف المستودع
            start_date: تاريخ البداية
            end_date: تاريخ النهاية

        Returns:
            تقرير المخزون
        """
        try:
            report = {
                "summary": {},
                "by_product": [],
                "by_warehouse": [],
                "transactions": [],
                "alerts": [],
                "generated_at": datetime.now().isoformat(),
            }

            # ملخص المخزون
            report["summary"] = self._generate_inventory_summary(warehouse_id)

            # تفصيل بالمنتج
            report["by_product"] = self._generate_product_inventory_report(warehouse_id)

            # تفصيل بالمستودع
            report["by_warehouse"] = self._generate_warehouse_inventory_report()

            # معاملات المخزون
            report["transactions"] = self._generate_transaction_report(warehouse_id, start_date, end_date)

            # التنبيهات
            report["alerts"] = [alert.__dict__ for alert in self.get_inventory_alerts(warehouse_id)]

            return report

        except Exception as e:
            self.logger.error(f"Error generating inventory report: {e}", exc_info=True)
            return {}

    def get_expiring_items(self, days_ahead: int = 30, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        الحصول على المنتجات التي ستنتهي صلاحيتها قريباً

        Args:
            days_ahead: عدد الأيام المستقبلية
            warehouse_id: معرف المستودع

        Returns:
            قائمة بالمنتجات التي ستنتهي صلاحيتها
        """
        try:
            expiry_date = datetime.now() + timedelta(days=days_ahead)

            query = """
                SELECT i.product_id, p.name, i.batch_id, i.quantity, i.expiry_date,
                       i.warehouse_id, w.name as warehouse_name
                FROM inventory_items i
                JOIN products p ON i.product_id = p.id
                JOIN warehouses w ON i.warehouse_id = w.warehouse_id
                WHERE i.expiry_date IS NOT NULL
                AND i.expiry_date <= ?
                AND i.quantity > 0
                AND i.status = 'active'
            """

            params = [expiry_date.isoformat()]
            if warehouse_id:
                query += " AND i.warehouse_id = ?"
                params.append(warehouse_id)

            query += " ORDER BY i.expiry_date ASC"

            data = self.db.execute_query(query, params, fetch_all=True)

            expiring_items = []
            for row in data:
                expiry_raw = get_value(row, 'expiry_date')
                expiring_items.append(
                    {
                        "product_id": get_value(row, 'product_id'),
                        "product_name": get_value(row, 'name'),
                        "batch_id": get_value(row, 'batch_id'),
                        "quantity": get_value(row, 'quantity'),
                        "expiry_date": expiry_raw,
                        "warehouse_id": get_value(row, 'warehouse_id'),
                        "warehouse_name": get_value(row, 'warehouse_name'),
                        "days_until_expiry": (datetime.fromisoformat(expiry_raw) - datetime.now()).days if expiry_raw else None,
                    }
                )

            return expiring_items

        except Exception as e:
            self.logger.error(f"Error getting expiring items: {e}", exc_info=True)
            return []

    def get_inventory_valuation(self, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """
        حساب قيمة المخزون

        Args:
            warehouse_id: معرف المستودع

        Returns:
            قيمة المخزون
        """
        try:
            query = """
                SELECT
                    SUM(i.quantity * i.unit_cost) as total_value,
                    AVG(i.unit_cost) as avg_cost,
                    COUNT(DISTINCT i.product_id) as product_count,
                    SUM(i.quantity) as total_quantity
                FROM inventory_items i
                WHERE i.status = 'active'
            """

            params = []
            if warehouse_id:
                query += " AND i.warehouse_id = ?"
                params.append(warehouse_id)

            data = self.db.execute_query(query, params, fetch_one=True)

            valuation = {
                "total_value": float(data[0] or 0) if data else 0,
                "average_cost": float(data[1] or 0) if data else 0,
                "product_count": data[2] or 0 if data else 0,
                "total_quantity": data[3] or 0 if data else 0,
                "warehouse_id": warehouse_id,
                "calculated_at": datetime.now().isoformat(),
            }

            return valuation

        except Exception as e:
            self.logger.error(f"Error calculating inventory valuation: {e}", exc_info=True)
            return {}

    def _load_warehouses(self):
        """تحميل بيانات المستودعات"""
        try:
            self.warehouses = {}
            query = "SELECT warehouse_id, name, location, capacity, status FROM warehouses WHERE status = 'active'"
            data = self.db.execute_query(query, fetch_all=True)

            for row in data:
                wh_id = get_value(row, 'warehouse_id')
                self.warehouses[wh_id] = {
                    "name": get_value(row, 'name'),
                    "location": get_value(row, 'location'),
                    "capacity": get_value(row, 'capacity'),
                    "status": get_value(row, 'status'),
                }

        except Exception as e:
            self.logger.error(f"Error loading warehouses: {e}", exc_info=True)
            self.warehouses = {}

    def _get_batch_quantity(self, product_id: int, warehouse_id: int, batch_id: str) -> int:
        """الحصول على كمية دفعة محددة"""
        try:
            query = """
                SELECT quantity FROM inventory_items
                WHERE product_id = ? AND warehouse_id = ? AND batch_id = ? AND status = 'active'
            """
            data = self.db.execute_query(query, (product_id, warehouse_id, batch_id), fetch_one=True)
            return data[0] if data else 0

        except Exception as e:
            self.logger.error(f"Error getting batch quantity: {e}", exc_info=True)
            return 0

    def _get_batch_cost(self, product_id: int, batch_id: str) -> Decimal:
        """الحصول على تكلفة دفعة محددة"""
        try:
            query = """
                SELECT unit_cost FROM inventory_items
                WHERE product_id = ? AND batch_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """
            data = self.db.execute_query(query, (product_id, batch_id), fetch_one=True)
            return Decimal(str(data[0])) if data else Decimal("0")

        except Exception as e:
            self.logger.error(f"Error getting batch cost: {e}", exc_info=True)
            return Decimal("0")

    def _update_batch_quantity(self, product_id: int, warehouse_id: int, batch_id: str, quantity_change: int):
        """تحديث كمية دفعة محددة"""
        try:
            # إذا كانت الدفعة موجودة، حدث الكمية
            existing_quantity = self._get_batch_quantity(product_id, warehouse_id, batch_id)

            if existing_quantity > 0:
                new_quantity = existing_quantity + quantity_change
                if new_quantity <= 0:
                    # حذف الدفعة إذا أصبحت الكمية صفر أو سالبة
                    query = """
                        DELETE FROM inventory_items
                        WHERE product_id = ? AND warehouse_id = ? AND batch_id = ?
                    """
                    self.db.execute_query(query, (product_id, warehouse_id, batch_id))
                else:
                    # تحديث الكمية
                    query = """
                        UPDATE inventory_items
                        SET quantity = ?
                        WHERE product_id = ? AND warehouse_id = ? AND batch_id = ?
                    """
                    self.db.execute_query(query, (new_quantity, product_id, warehouse_id, batch_id))
            else:
                # إدراج دفعة جديدة (للنقل بين المستودعات)
                # نحتاج للبيانات من المعاملة السابقة
                pass

        except Exception as e:
            self.logger.error(f"Error updating batch quantity: {e}", exc_info=True)

    def _update_product_stock(self, product_id: int, warehouse_id: int, quantity_change: int):
        """تحديث إجمالي مخزون المنتج في المستودع"""
        try:
            # تحديث جدول products
            query = """
                UPDATE products
                SET current_stock = current_stock + ?
                WHERE id = ?
            """
            self.db.execute_query(query, (quantity_change, product_id))

        except Exception as e:
            self.logger.error(f"Error updating product stock: {e}", exc_info=True)

    def _insert_inventory_data(self, inventory_data: Dict[str, Any], transaction_data: Dict[str, Any]):
        """إدراج بيانات المخزون والمعاملة"""
        try:
            # إدراج في جدول inventory_items
            inventory_query = """
                INSERT INTO inventory_items
                (product_id, warehouse_id, batch_id, quantity, unit_cost, expiry_date, location, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(
                inventory_query,
                (
                    inventory_data["product_id"],
                    inventory_data["warehouse_id"],
                    inventory_data["batch_id"],
                    inventory_data["quantity"],
                    inventory_data["unit_cost"],
                    inventory_data["expiry_date"],
                    inventory_data["location"],
                    inventory_data["status"],
                    inventory_data["created_at"],
                ),
            )

            # إدراج المعاملة
            self._insert_transaction_data(transaction_data)

        except Exception as e:
            self.logger.error(f"Error inserting inventory data: {e}", exc_info=True)
            raise

    def _insert_transaction_data(self, transaction_data: Dict[str, Any]):
        """إدراج بيانات المعاملة"""
        try:
            transaction_query = """
                INSERT INTO inventory_transactions
                (transaction_id, product_id, transaction_type, quantity, unit_cost, reference_id,
                 warehouse_from, warehouse_to, performed_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(
                transaction_query,
                (
                    transaction_data["transaction_id"],
                    transaction_data["product_id"],
                    transaction_data["transaction_type"],
                    transaction_data["quantity"],
                    transaction_data["unit_cost"],
                    transaction_data["reference_id"],
                    transaction_data.get("warehouse_from"),
                    transaction_data.get("warehouse_to"),
                    transaction_data["performed_by"],
                    transaction_data["notes"],
                    transaction_data["created_at"],
                ),
            )

        except Exception as e:
            self.logger.error(f"Error inserting transaction data: {e}", exc_info=True)
            raise

    def _check_low_stock_alerts(self, warehouse_id: Optional[int] = None) -> List[InventoryAlert]:
        """فحص تنبيهات المخزون المنخفض"""
        alerts = []

        try:
            query = """
                SELECT p.id, p.name, p.current_stock, p.min_stock, p.warehouse_id
                FROM products p
                WHERE p.is_active = 1
            """

            params = []
            if warehouse_id:
                query += " AND p.warehouse_id = ?"
                params.append(warehouse_id)

            data = self.db.execute_query(query, params, fetch_all=True)

            for row in data:
                product_id, name, current_stock, min_stock, wh_id = row
                if min_stock and current_stock <= min_stock * self.low_stock_threshold:
                    severity = (
                        "critical"
                        if current_stock <= min_stock * 0.5
                        else "high" if current_stock <= min_stock else "medium"
                    )

                    alert = InventoryAlert(
                        alert_id=f"LOW_STOCK_{product_id}_{wh_id}",
                        product_id=product_id,
                        alert_type="low_stock",
                        severity=severity,
                        message=f"مخزون منخفض للمنتج {name}: {current_stock} (الحد الأدنى: {min_stock})",
                        suggested_action=(
                            "إعادة طلب المنتج فوراً" if severity == "critical" else "مراجعة مستوى المخزون"
                        ),
                        created_at=datetime.now(),
                    )
                    alerts.append(alert)

        except Exception as e:
            self.logger.error(f"Error checking low stock alerts: {e}", exc_info=True)

        return alerts

    def _check_expiry_alerts(self, warehouse_id: Optional[int] = None) -> List[InventoryAlert]:
        """فحص تنبيهات الصلاحية"""
        alerts = []

        try:
            expiring_items = self.get_expiring_items(self.expiry_warning_days, warehouse_id)

            for item in expiring_items:
                severity = (
                    "critical"
                    if item["days_until_expiry"] <= 7
                    else "high" if item["days_until_expiry"] <= 14 else "medium"
                )

                alert = InventoryAlert(
                    alert_id=f"EXPIRY_{item['product_id']}_{item['batch_id']}",
                    product_id=item["product_id"],
                    alert_type="expiry_warning",
                    severity=severity,
                    message=f"ينتهي صلاحية {item['product_name']} (دفعة {item['batch_id']}) خلال {item['days_until_expiry']} يوم",  # noqa: E501
                    suggested_action=(
                        "ترتيب بيع المنتج أو التخلص منه" if severity == "critical" else "مراجعة خطة البيع"
                    ),
                    created_at=datetime.now(),
                )
                alerts.append(alert)

        except Exception as e:
            self.logger.error(f"Error checking expiry alerts: {e}", exc_info=True)

        return alerts

    def _check_overstock_alerts(self, warehouse_id: Optional[int] = None) -> List[InventoryAlert]:
        """فحص تنبيهات الزيادة في المخزون"""
        alerts = []

        try:
            query = """
                SELECT p.id, p.name, p.current_stock, p.max_stock, p.warehouse_id
                FROM products p
                WHERE p.is_active = 1 AND p.max_stock > 0
            """

            params = []
            if warehouse_id:
                query += " AND p.warehouse_id = ?"
                params.append(warehouse_id)

            data = self.db.execute_query(query, params, fetch_all=True)

            for row in data:
                product_id, name, current_stock, max_stock, wh_id = row
                if current_stock >= max_stock * self.overstock_threshold:
                    alert = InventoryAlert(
                        alert_id=f"OVERSTOCK_{product_id}_{wh_id}",
                        product_id=product_id,
                        alert_type="overstock",
                        severity="medium",
                        message=f"زيادة في مخزون {name}: {current_stock} (الحد الأقصى: {max_stock})",
                        suggested_action="مراجعة خطة البيع أو التخفيضات",
                        created_at=datetime.now(),
                    )
                    alerts.append(alert)

        except Exception as e:
            self.logger.error(f"Error checking overstock alerts: {e}", exc_info=True)

        return alerts

    def _check_damaged_stock_alerts(self, warehouse_id: Optional[int] = None) -> List[InventoryAlert]:
        """فحص تنبيهات المنتجات التالفة"""
        alerts = []

        try:
            query = """
                SELECT i.product_id, p.name, SUM(i.quantity) as damaged_quantity, i.warehouse_id
                FROM inventory_items i
                JOIN products p ON i.product_id = p.id
                WHERE i.status = 'damaged'
            """

            params = []
            if warehouse_id:
                query += " AND i.warehouse_id = ?"
                params.append(warehouse_id)

            query += " GROUP BY i.product_id, p.name, i.warehouse_id HAVING damaged_quantity > 0"

            data = self.db.execute_query(query, params, fetch_all=True)

            for row in data:
                product_id, name, damaged_quantity, wh_id = row
                alert = InventoryAlert(
                    alert_id=f"DAMAGED_{product_id}_{wh_id}",
                    product_id=product_id,
                    alert_type="damaged",
                    severity="high",
                    message=f"منتجات تالفة: {damaged_quantity} من {name}",
                    suggested_action="مراجعة المنتجات التالفة واتخاذ الإجراء المناسب",
                    created_at=datetime.now(),
                )
                alerts.append(alert)

        except Exception as e:
            self.logger.error(f"Error checking damaged stock alerts: {e}", exc_info=True)

        return alerts

    def _get_products_for_optimization(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """الحصول على المنتجات للتحسين"""
        try:
            query = """
                SELECT id, name, current_stock, min_stock, max_stock, selling_price
                FROM products
                WHERE is_active = 1
            """

            params = []
            if product_id:
                query += " AND id = ?"
                params.append(product_id)

            data = self.db.execute_query(query, params, fetch_all=True)

            products = []
            for row in data:
                products.append(
                    {
                        "id": get_value(row, 'id'),
                        "name": get_value(row, 'name'),
                        "current_stock": get_value(row, 'current_stock', 0) or 0,
                        "min_stock": get_value(row, 'min_stock', 0) or 0,
                        "max_stock": get_value(row, 'max_stock', 0) or 0,
                        "selling_price": float(get_value(row, 'selling_price') or 0),
                    }
                )

            return products

        except Exception as e:
            self.logger.error(f"Error getting products for optimization: {e}", exc_info=True)
            return []

    def _calculate_inventory_optimization(self, product: Dict[str, Any]) -> Optional[InventoryOptimization]:
        """حساب تحسين مخزون منتج محدد"""
        try:
            product_id = product["id"]
            current_stock = product["current_stock"]
            product["min_stock"]
            max_stock = product["max_stock"]

            # الحصول على تنبؤ الطلب
            forecast = self.prediction_service.forecast_demand(product_id, days_ahead=90)
            daily_demand = forecast.predicted_demand / 90

            # حساب المخزون الأمثل
            lead_time_days = 7  # افتراضي
            safety_stock = daily_demand * lead_time_days * 1.5  # عامل أمان 1.5
            reorder_point = (daily_demand * lead_time_days) + safety_stock
            optimal_stock = reorder_point + (daily_demand * 30)  # 30 يوم من المخزون

            # تحديد التوصية
            if current_stock < reorder_point:
                recommended_action = f"إعادة طلب فوراً - مطلوب {int(optimal_stock - current_stock)} وحدة"
            elif current_stock > max_stock:
                recommended_action = f"تخفيض المخزون - زيادة {int(current_stock - optimal_stock)} وحدة"
            else:
                recommended_action = "المخزون متوازن"

            # حساب التوفير المتوقع
            expected_savings = Decimal("0")
            if current_stock < reorder_point:
                # تكلفة نقص المخزون
                stockout_cost = (reorder_point - current_stock) * product["selling_price"] * Decimal("0.1")
                expected_savings = -stockout_cost  # توفير سلبي = خسارة
            elif current_stock > max_stock:
                # تكلفة الزيادة في المخزون
                holding_cost = (current_stock - optimal_stock) * product["selling_price"] * Decimal("0.05")
                expected_savings = holding_cost

            return InventoryOptimization(
                product_id=product_id,
                current_stock=current_stock,
                optimal_stock=int(optimal_stock),
                reorder_point=int(reorder_point),
                safety_stock=int(safety_stock),
                recommended_action=recommended_action,
                expected_savings=expected_savings,
                confidence_score=forecast.confidence_score,
            )

        except Exception as e:
            self.logger.error(f"Error calculating inventory optimization: {e}", exc_info=True)
            return None

    def _generate_inventory_summary(self, warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """توليد ملخص المخزون"""
        try:
            valuation = self.get_inventory_valuation(warehouse_id)

            query = """
                SELECT
                    COUNT(DISTINCT product_id) as total_products,
                    SUM(quantity) as total_quantity,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_items,
                    COUNT(CASE WHEN status = 'damaged' THEN 1 END) as damaged_items
                FROM inventory_items
                WHERE 1=1
            """

            params = []
            if warehouse_id:
                query += " AND warehouse_id = ?"
                params.append(warehouse_id)

            data = self.db.execute_query(query, params, fetch_one=True)

            summary = {
                "total_products": data[0] or 0 if data else 0,
                "total_quantity": data[1] or 0 if data else 0,
                "active_items": data[2] or 0 if data else 0,
                "damaged_items": data[3] or 0 if data else 0,
                "total_value": valuation.get("total_value", 0),
                "warehouse_id": warehouse_id,
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error generating inventory summary: {e}", exc_info=True)
            return {}

    def _generate_product_inventory_report(self, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """توليد تقرير مخزون المنتجات"""
        try:
            query = """
                SELECT
                    p.id, p.name, p.current_stock, p.min_stock, p.max_stock,
                    SUM(i.quantity) as inventory_quantity,
                    AVG(i.unit_cost) as avg_cost,
                    COUNT(DISTINCT i.batch_id) as batch_count
                FROM products p
                LEFT JOIN inventory_items i ON p.id = i.product_id AND i.status = 'active'
                WHERE p.is_active = 1
            """

            params = []
            if warehouse_id:
                query += " AND i.warehouse_id = ?"
                params.append(warehouse_id)

            query += " GROUP BY p.id, p.name, p.current_stock, p.min_stock, p.max_stock"

            data = self.db.execute_query(query, params, fetch_all=True)

            products = []
            for row in data:
                products.append(
                    {
                        "product_id": get_value(row, 'id'),
                        "product_name": get_value(row, 'name'),
                        "current_stock": get_value(row, 'current_stock', 0) or 0,
                        "min_stock": get_value(row, 'min_stock', 0) or 0,
                        "max_stock": get_value(row, 'max_stock', 0) or 0,
                        "inventory_quantity": get_value(row, 'inventory_quantity', 0) or 0,
                        "avg_cost": float(get_value(row, 'avg_cost') or 0),
                        "batch_count": get_value(row, 'batch_count', 0) or 0,
                    }
                )

            return products

        except Exception as e:
            self.logger.error(f"Error generating product inventory report: {e}", exc_info=True)
            return []

    def _generate_warehouse_inventory_report(self) -> List[Dict[str, Any]]:
        """توليد تقرير مخزون المستودعات"""
        try:
            warehouses = []
            for wh_id, wh_data in self.warehouses.items():
                valuation = self.get_inventory_valuation(wh_id)
                summary = self._generate_inventory_summary(wh_id)

                warehouse_info = {
                    "warehouse_id": wh_id,
                    "name": wh_data["name"],
                    "location": wh_data["location"],
                    "capacity": wh_data["capacity"],
                    "status": wh_data["status"],
                    **summary,
                    **valuation,
                }
                warehouses.append(warehouse_info)

            return warehouses

        except Exception as e:
            self.logger.error(f"Error generating warehouse inventory report: {e}", exc_info=True)
            return []

    def _generate_transaction_report(
        self,
        warehouse_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """توليد تقرير المعاملات"""
        try:
            query = """
                SELECT transaction_id, product_id, transaction_type, quantity, unit_cost,
                       reference_id, warehouse_from, warehouse_to, performed_by, notes, created_at
                FROM inventory_transactions
                WHERE 1=1
            """

            params = []
            if warehouse_id:
                query += " AND (warehouse_from = ? OR warehouse_to = ?)"
                params.extend([warehouse_id, warehouse_id])

            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY created_at DESC LIMIT 100"

            data = self.db.execute_query(query, params, fetch_all=True)

            transactions = []
            for row in data:
                transactions.append(
                    {
                        "transaction_id": get_value(row, 'transaction_id'),
                        "product_id": get_value(row, 'product_id'),
                        "transaction_type": get_value(row, 'transaction_type'),
                        "quantity": get_value(row, 'quantity'),
                        "unit_cost": float(get_value(row, 'unit_cost') or 0),
                        "reference_id": get_value(row, 'reference_id'),
                        "warehouse_from": get_value(row, 'warehouse_from'),
                        "warehouse_to": get_value(row, 'warehouse_to'),
                        "performed_by": get_value(row, 'performed_by'),
                        "notes": get_value(row, 'notes'),
                        "created_at": get_value(row, 'created_at'),
                    }
                )

            return transactions

        except Exception as e:
            self.logger.error(f"Error generating transaction report: {e}", exc_info=True)
            return []
