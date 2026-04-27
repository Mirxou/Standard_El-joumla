#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة المخازن المتعددة - Multi-Warehouse Management Service
إدارة المخازن المتعددة، النقل بين المخازن، والتوزيع الذكي
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager
from src.services.advanced_inventory_management_service import AdvancedInventoryManagementService
from src.services.supply_chain_integration_service import SupplyChainIntegrationService
from src.utils.logger import setup_logger

@dataclass
class Warehouse:
    """فئة تمثل المخزن"""
    warehouse_id: str
    name: str
    location: str
    type: str  # 'central', 'regional', 'retail', 'distribution'
    capacity: int
    current_utilization: float
    status: str  # 'active', 'inactive', 'maintenance'
    manager_id: Optional[int] = None
    contact_info: Optional[Dict[str, Any]] = None
    operating_hours: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class WarehouseTransfer:
    """فئة تمثل نقل بين المخازن"""
    transfer_id: str
    from_warehouse_id: str
    to_warehouse_id: str
    items: List[Dict[str, Any]]
    status: str  # 'draft', 'approved', 'in_transit', 'received', 'cancelled'
    transfer_type: str  # 'replenishment', 'redistribution', 'returns'
    priority: str  # 'low', 'medium', 'high', 'urgent'
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    total_value: Optional[Decimal] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class WarehouseZone:
    """فئة تمثل منطقة داخل المخزن"""
    zone_id: str
    warehouse_id: str
    zone_name: str
    zone_type: str  # 'storage', 'picking', 'shipping', 'receiving', 'quarantine'
    capacity: int
    current_occupancy: int
    temperature_controlled: bool
    security_level: str  # 'low', 'medium', 'high'
    coordinates: Optional[Dict[str, Any]] = None

@dataclass
class InventoryDistribution:
    """فئة تمثل توزيع المخزون"""
    product_id: int
    total_stock: int
    distribution: Dict[str, int]  # warehouse_id -> quantity
    optimal_distribution: Dict[str, int]
    redistribution_needed: bool
    recommendations: List[str]

class MultiWarehouseManagementService:
    """
    خدمة إدارة المخازن المتعددة
    """

    def __init__(self, db_manager: DatabaseManager, inventory_service: AdvancedInventoryManagementService):
        self.db = db_manager
        self.inventory_service = inventory_service
        self.logger = setup_logger(__name__)

    def create_warehouse(self, warehouse: Warehouse) -> str:
        """
        إنشاء مخزن جديد

        Args:
            warehouse: بيانات المخزن

        Returns:
            str: معرف المخزن الجديد
        """
        try:
            warehouse_id = f"WH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            data = {
                'warehouse_id': warehouse_id,
                'name': warehouse.name,
                'location': warehouse.location,
                'type': warehouse.type,
                'capacity': warehouse.capacity,
                'current_utilization': warehouse.current_utilization,
                'status': warehouse.status,
                'manager_id': warehouse.manager_id,
                'contact_info': json.dumps(warehouse.contact_info) if warehouse.contact_info else None,
                'operating_hours': json.dumps(warehouse.operating_hours) if warehouse.operating_hours else None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self._insert_warehouse(data)

            # إنشاء مناطق افتراضية للمخزن
            self._create_default_zones(warehouse_id)

            self.logger.info(f"تم إنشاء المخزن: {warehouse_id}")
            return warehouse_id

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء المخزن: {e}")
            raise

    def create_transfer_request(self, transfer: WarehouseTransfer) -> str:
        """
        إنشاء طلب نقل بين المخازن

        Args:
            transfer: بيانات النقل

        Returns:
            str: معرف طلب النقل
        """
        try:
            transfer_id = f"WT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # حساب القيمة الإجمالية
            total_value = Decimal('0')
            for item in transfer.items:
                total_value += Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))

            # تحويل العناصر إلى JSON
            serializable_items = []
            for item in transfer.items:
                serializable_item = {
                    'product_id': item['product_id'],
                    'batch_id': item.get('batch_id'),
                    'quantity': str(item['quantity']),
                    'unit_price': str(item['unit_price'])
                }
                serializable_items.append(serializable_item)

            data = {
                'transfer_id': transfer_id,
                'from_warehouse_id': transfer.from_warehouse_id,
                'to_warehouse_id': transfer.to_warehouse_id,
                'items': json.dumps(serializable_items),
                'status': transfer.status,
                'transfer_type': transfer.transfer_type,
                'priority': transfer.priority,
                'estimated_delivery': transfer.estimated_delivery.isoformat() if transfer.estimated_delivery else None,
                'total_value': str(total_value),
                'created_by': transfer.created_by,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self._insert_transfer(data)

            self.logger.info(f"تم إنشاء طلب النقل: {transfer_id}")
            return transfer_id

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء طلب النقل: {e}")
            raise

    def approve_transfer(self, transfer_id: str, approved_by: int) -> bool:
        """
        الموافقة على طلب النقل

        Args:
            transfer_id: معرف طلب النقل
            approved_by: معرف الموافق

        Returns:
            bool: نجاح العملية
        """
        try:
            # التحقق من وجود طلب النقل
            transfer_data = self._get_transfer(transfer_id)
            if not transfer_data:
                raise ValueError(f"طلب النقل غير موجود: {transfer_id}")

            if transfer_data['status'] != 'draft':
                raise ValueError(f"لا يمكن الموافقة على طلب النقل في حالة: {transfer_data['status']}")

            # التحقق من توفر المخزون
            items = json.loads(transfer_data['items'])
            for item in items:
                available_stock = self._get_warehouse_stock(
                    transfer_data['from_warehouse_id'],
                    item['product_id'],
                    item.get('batch_id')
                )
                if available_stock < int(item['quantity']):
                    raise ValueError(f"مخزون غير كافٍ للمنتج {item['product_id']} في المخزن {transfer_data['from_warehouse_id']}")

            # تحديث حالة الطلب
            self._update_transfer_status(transfer_id, 'approved', approved_by)

            self.logger.info(f"تمت الموافقة على طلب النقل: {transfer_id}")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في الموافقة على طلب النقل: {e}")
            raise

    def execute_transfer(self, transfer_id: str, executed_by: int) -> bool:
        """
        تنفيذ النقل بين المخازن

        Args:
            transfer_id: معرف طلب النقل
            executed_by: معرف المنفذ

        Returns:
            bool: نجاح العملية
        """
        try:
            # التحقق من حالة الطلب
            transfer_data = self._get_transfer(transfer_id)
            if not transfer_data or transfer_data['status'] != 'approved':
                raise ValueError(f"لا يمكن تنفيذ طلب النقل في حالة: {transfer_data['status']}")

            # تحديث الحالة إلى قيد النقل
            self._update_transfer_status(transfer_id, 'in_transit', executed_by)

            # إزالة المخزون من المخزن المصدر
            items = json.loads(transfer_data['items'])
            for item in items:
                self.inventory_service.remove_inventory_item(
                    product_id=item['product_id'],
                    warehouse_id=transfer_data['from_warehouse_id'],
                    batch_id=item.get('batch_id'),
                    quantity=int(item['quantity']),
                    reason=f"transfer_to_{transfer_data['to_warehouse_id']}"
                )

            # تحديث الحالة إلى تم الاستلام
            self._update_transfer_status(transfer_id, 'received', executed_by)
            self._update_transfer_delivery(transfer_id, datetime.now())

            # إضافة المخزون إلى المخزن الوجهة
            for item in items:
                self.inventory_service.add_inventory_item(
                    product_id=item['product_id'],
                    warehouse_id=transfer_data['to_warehouse_id'],
                    batch_id=item.get('batch_id'),
                    quantity=int(item['quantity']),
                    unit_cost=Decimal(item['unit_price']),
                    expiry_date=None  # سيتم تحديده لاحقاً
                )

            self.logger.info(f"تم تنفيذ النقل: {transfer_id}")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ النقل: {e}")
            raise

    def get_inventory_distribution(self, product_id: int) -> InventoryDistribution:
        """
        الحصول على توزيع المخزون لمنتج معين

        Args:
            product_id: معرف المنتج

        Returns:
            InventoryDistribution: توزيع المخزون
        """
        try:
            # الحصول على إجمالي المخزون
            total_stock = self._get_total_product_stock(product_id)

            # الحصول على توزيع المخزون الحالي
            current_distribution = self._get_current_distribution(product_id)

            # حساب التوزيع الأمثل
            optimal_distribution = self._calculate_optimal_distribution(product_id, total_stock)

            # تحديد الحاجة لإعادة التوزيع
            redistribution_needed = self._check_redistribution_needed(current_distribution, optimal_distribution)

            # توليد التوصيات
            recommendations = self._generate_distribution_recommendations(
                product_id, current_distribution, optimal_distribution
            )

            distribution = InventoryDistribution(
                product_id=product_id,
                total_stock=total_stock,
                distribution=current_distribution,
                optimal_distribution=optimal_distribution,
                redistribution_needed=redistribution_needed,
                recommendations=recommendations
            )

            return distribution

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على توزيع المخزون: {e}")
            raise

    def optimize_inventory_distribution(self) -> List[Dict[str, Any]]:
        """
        تحسين توزيع المخزون عبر جميع المخازن

        Returns:
            List[Dict[str, Any]]: قائمة بالتوصيات
        """
        try:
            recommendations = []

            # الحصول على جميع المنتجات النشطة
            products = self._get_active_products()

            for product in products:
                distribution = self.get_inventory_distribution(product['id'])

                if distribution.redistribution_needed:
                    recommendations.append({
                        'product_id': distribution.product_id,
                        'product_name': product['name'],
                        'current_distribution': distribution.distribution,
                        'optimal_distribution': distribution.optimal_distribution,
                        'recommendations': distribution.recommendations,
                        'priority': self._calculate_redistribution_priority(distribution)
                    })

            # ترتيب التوصيات حسب الأولوية
            recommendations.sort(key=lambda x: x['priority'], reverse=True)

            self.logger.info(f"تم تحليل توزيع المخزون لـ {len(products)} منتج")
            return recommendations

        except Exception as e:
            self.logger.error(f"خطأ في تحسين توزيع المخزون: {e}")
            raise

    def get_warehouse_performance_report(self, warehouse_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        الحصول على تقرير أداء المخزن

        Args:
            warehouse_id: معرف المخزن
            start_date: تاريخ البداية
            end_date: تاريخ النهاية

        Returns:
            Dict[str, Any]: تقرير الأداء
        """
        try:
            report = {
                'warehouse_id': warehouse_id,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'metrics': {},
                'transfers': {},
                'alerts': []
            }

            # مقاييس الأداء الأساسية
            report['metrics'] = self._calculate_warehouse_metrics(warehouse_id, start_date, end_date)

            # إحصائيات النقل
            report['transfers'] = self._calculate_transfer_statistics(warehouse_id, start_date, end_date)

            # التنبيهات والمشاكل
            report['alerts'] = self._get_warehouse_alerts(warehouse_id)

            return report

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء تقرير أداء المخزن: {e}")
            raise

    def get_multi_warehouse_report(self) -> Dict[str, Any]:
        """
        الحصول على تقرير شامل لجميع المخازن

        Returns:
            Dict[str, Any]: التقرير الشامل
        """
        try:
            # الحصول على جميع المخازن
            warehouses = self._get_all_warehouses()

            report = {
                'generated_at': datetime.now().isoformat(),
                'total_warehouses': len(warehouses),
                'warehouses': [],
                'network_overview': {},
                'recommendations': []
            }

            for warehouse in warehouses:
                warehouse_report = {
                    'warehouse_id': warehouse['warehouse_id'],
                    'name': warehouse['name'],
                    'type': warehouse['type'],
                    'location': warehouse['location'],
                    'status': warehouse['status'],
                    'utilization': warehouse['current_utilization'],
                    'capacity': warehouse['capacity']
                }

                # إضافة مقاييس سريعة
                metrics = self._calculate_warehouse_metrics(
                    warehouse['warehouse_id'],
                    datetime.now() - timedelta(days=30),
                    datetime.now()
                )
                warehouse_report['recent_metrics'] = metrics

                report['warehouses'].append(warehouse_report)

            # نظرة عامة على الشبكة
            report['network_overview'] = self._calculate_network_overview()

            # التوصيات العامة
            report['recommendations'] = self._generate_network_recommendations()

            return report

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء التقرير الشامل: {e}")
            raise

    # طرق مساعدة لقاعدة البيانات
    def _insert_warehouse(self, data: Dict[str, Any]) -> None:
        """إدراج مخزن في قاعدة البيانات"""
        query = """
            INSERT INTO warehouses (
                warehouse_id, name, location, type, capacity,
                current_utilization, status, manager_id, contact_info,
                operating_hours, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['warehouse_id'], data['name'], data['location'], data['type'],
            data['capacity'], data['current_utilization'], data['status'],
            data['manager_id'], data['contact_info'], data['operating_hours'],
            data['created_at'], data['updated_at']
        )
        self.db.execute_non_query(query, params)

    def _insert_transfer(self, data: Dict[str, Any]) -> None:
        """إدراج طلب نقل في قاعدة البيانات"""
        query = """
            INSERT INTO warehouse_transfers (
                transfer_id, from_warehouse_id, to_warehouse_id, items,
                status, transfer_type, priority, estimated_delivery,
                total_value, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['transfer_id'], data['from_warehouse_id'], data['to_warehouse_id'],
            data['items'], data['status'], data['transfer_type'], data['priority'],
            data['estimated_delivery'], data['total_value'], data['created_by'],
            data['created_at'], data['updated_at']
        )
        self.db.execute_non_query(query, params)

    def _create_default_zones(self, warehouse_id: str) -> None:
        """إنشاء مناطق افتراضية للمخزن"""
        default_zones = [
            {'name': 'Receiving', 'type': 'receiving'},
            {'name': 'Storage', 'type': 'storage'},
            {'name': 'Picking', 'type': 'picking'},
            {'name': 'Shipping', 'type': 'shipping'}
        ]

        for zone in default_zones:
            zone_id = f"{warehouse_id}_{zone['type']}_{datetime.now().strftime('%H%M%S')}"
            query = """
                INSERT INTO warehouse_zones (
                    zone_id, warehouse_id, zone_name, zone_type,
                    capacity, current_occupancy, temperature_controlled, security_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                zone_id, warehouse_id, zone['name'], zone['type'],
                1000, 0, False, 'medium'
            )
            self.db.execute_non_query(query, params)

    def _get_transfer(self, transfer_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات طلب النقل"""
        query = "SELECT * FROM warehouse_transfers WHERE transfer_id = ?"
        result = self.db.fetch_one(query, (transfer_id,))
        return dict(result) if result else None

    def _update_transfer_status(self, transfer_id: str, status: str, updated_by: int) -> None:
        """تحديث حالة طلب النقل"""
        query = """
            UPDATE warehouse_transfers
            SET status = ?, updated_at = ?, approved_by = ?
            WHERE transfer_id = ?
        """
        params = (status, datetime.now().isoformat(), updated_by, transfer_id)
        self.db.execute_non_query(query, params)

    def _update_transfer_delivery(self, transfer_id: str, delivery_date: datetime) -> None:
        """تحديث تاريخ التسليم الفعلي"""
        query = "UPDATE warehouse_transfers SET actual_delivery = ? WHERE transfer_id = ?"
        params = (delivery_date.isoformat(), transfer_id)
        self.db.execute_non_query(query, params)

    def _get_warehouse_stock(self, warehouse_id: str, product_id: int, batch_id: Optional[str] = None) -> int:
        """الحصول على مخزون منتج في مخزن معين"""
        if batch_id:
            query = """
                SELECT COALESCE(SUM(quantity), 0)
                FROM advanced_inventory
                WHERE product_id = ? AND warehouse_id = ? AND batch_id = ?
            """
            params = (product_id, warehouse_id, batch_id)
        else:
            query = """
                SELECT COALESCE(SUM(quantity), 0)
                FROM advanced_inventory
                WHERE product_id = ? AND warehouse_id = ?
            """
            params = (product_id, warehouse_id)

        result = self.db.fetch_one(query, params)
        return result[0] if result else 0

    def _get_total_product_stock(self, product_id: int) -> int:
        """الحصول على إجمالي مخزون منتج عبر جميع المخازن"""
        query = "SELECT COALESCE(SUM(quantity), 0) FROM advanced_inventory WHERE product_id = ?"
        result = self.db.fetch_one(query, (product_id,))
        return result[0] if result else 0

    def _get_current_distribution(self, product_id: int) -> Dict[str, int]:
        """الحصول على التوزيع الحالي للمنتج"""
        query = """
            SELECT warehouse_id, SUM(quantity) as total_quantity
            FROM advanced_inventory
            WHERE product_id = ?
            GROUP BY warehouse_id
        """
        results = self.db.fetch_all(query, (product_id,))
        return {row[0]: row[1] for row in results} if results else {}

    def _calculate_optimal_distribution(self, product_id: int, total_stock: int) -> Dict[str, int]:
        """حساب التوزيع الأمثل للمنتج"""
        # الحصول على جميع المخازن النشطة
        warehouses = self._get_active_warehouses()

        if not warehouses:
            return {}

        # توزيع متساوٍ بين المخازن (يمكن تحسينه لاحقاً)
        base_quantity = total_stock // len(warehouses)
        remainder = total_stock % len(warehouses)

        optimal = {}
        for i, warehouse in enumerate(warehouses):
            quantity = base_quantity + (1 if i < remainder else 0)
            optimal[warehouse['warehouse_id']] = quantity

        return optimal

    def _check_redistribution_needed(self, current: Dict[str, int], optimal: Dict[str, int]) -> bool:
        """التحقق من الحاجة لإعادة التوزيع"""
        # حساب الفرق المطلق
        all_warehouses = set(current.keys()) | set(optimal.keys())
        total_difference = 0

        for warehouse_id in all_warehouses:
            current_qty = current.get(warehouse_id, 0)
            optimal_qty = optimal.get(warehouse_id, 0)
            total_difference += abs(current_qty - optimal_qty)

        # إذا كان الفرق أكبر من 10% من إجمالي المخزون
        total_stock = sum(current.values())
        return total_difference > (total_stock * 0.1) if total_stock > 0 else False

    def _generate_distribution_recommendations(self, product_id: int, current: Dict[str, int], optimal: Dict[str, int]) -> List[str]:
        """توليد توصيات إعادة التوزيع"""
        recommendations = []

        for warehouse_id, optimal_qty in optimal.items():
            current_qty = current.get(warehouse_id, 0)
            if abs(current_qty - optimal_qty) > 0:
                if current_qty > optimal_qty:
                    recommendations.append(f"نقل {current_qty - optimal_qty} وحدة من المخزن {warehouse_id}")
                else:
                    recommendations.append(f"إضافة {optimal_qty - current_qty} وحدة إلى المخزن {warehouse_id}")

        return recommendations

    def _calculate_redistribution_priority(self, distribution: InventoryDistribution) -> float:
        """حساب أولوية إعادة التوزيع"""
        if not distribution.redistribution_needed:
            return 0.0

        # حساب الفرق المطلق
        total_difference = 0
        for warehouse_id in set(distribution.distribution.keys()) | set(distribution.optimal_distribution.keys()):
            current = distribution.distribution.get(warehouse_id, 0)
            optimal = distribution.optimal_distribution.get(warehouse_id, 0)
            total_difference += abs(current - optimal)

        # الأولوية تعتمد على نسبة الفرق من إجمالي المخزون
        if distribution.total_stock > 0:
            priority = (total_difference / distribution.total_stock) * 100
            return min(priority, 100.0)  # الحد الأقصى 100
        return 0.0

    def _get_active_products(self) -> List[Dict[str, Any]]:
        """الحصول على المنتجات النشطة"""
        query = "SELECT id, name FROM products WHERE is_active = 1"
        results = self.db.fetch_all(query)
        return [dict(row) for row in results] if results else []

    def _get_active_warehouses(self) -> List[Dict[str, Any]]:
        """الحصول على المخازن النشطة"""
        query = "SELECT warehouse_id, name, capacity FROM warehouses WHERE status = 'active'"
        results = self.db.fetch_all(query)
        return [dict(row) for row in results] if results else []

    def _get_all_warehouses(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المخازن"""
        query = "SELECT * FROM warehouses ORDER BY type, name"
        results = self.db.fetch_all(query)
        return [dict(row) for row in results] if results else []

    def _calculate_warehouse_metrics(self, warehouse_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """حساب مقاييس أداء المخزن"""
        metrics = {
            'total_transfers_out': 0,
            'total_transfers_in': 0,
            'on_time_delivery_rate': 0.0,
            'average_transfer_value': 0.0,
            'current_utilization': 0.0
        }

        # عدد النقل الصادر
        query_out = """
            SELECT COUNT(*) FROM warehouse_transfers
            WHERE from_warehouse_id = ? AND created_at BETWEEN ? AND ?
        """
        result_out = self.db.fetch_one(query_out, (warehouse_id, start_date.isoformat(), end_date.isoformat()))
        metrics['total_transfers_out'] = result_out[0] if result_out else 0

        # عدد النقل الوارد
        query_in = """
            SELECT COUNT(*) FROM warehouse_transfers
            WHERE to_warehouse_id = ? AND created_at BETWEEN ? AND ?
        """
        result_in = self.db.fetch_one(query_in, (warehouse_id, start_date.isoformat(), end_date.isoformat()))
        metrics['total_transfers_in'] = result_in[0] if result_in else 0

        # معدل التسليم في الوقت المحدد
        query_ontime = """
            SELECT COUNT(*) FROM warehouse_transfers
            WHERE (from_warehouse_id = ? OR to_warehouse_id = ?)
            AND status = 'received' AND actual_delivery <= estimated_delivery
            AND created_at BETWEEN ? AND ?
        """
        result_ontime = self.db.fetch_one(query_ontime, (warehouse_id, warehouse_id, start_date.isoformat(), end_date.isoformat()))
        total_completed = metrics['total_transfers_out'] + metrics['total_transfers_in']
        if total_completed > 0:
            metrics['on_time_delivery_rate'] = (result_ontime[0] / total_completed) * 100 if result_ontime else 0

        # متوسط قيمة النقل
        query_value = """
            SELECT AVG(CAST(total_value AS DECIMAL)) FROM warehouse_transfers
            WHERE (from_warehouse_id = ? OR to_warehouse_id = ?)
            AND created_at BETWEEN ? AND ?
        """
        result_value = self.db.fetch_one(query_value, (warehouse_id, warehouse_id, start_date.isoformat(), end_date.isoformat()))
        metrics['average_transfer_value'] = float(result_value[0]) if result_value and result_value[0] else 0.0

        # معدل الاستغلال الحالي
        warehouse_info = self.db.fetch_one("SELECT capacity, current_utilization FROM warehouses WHERE warehouse_id = ?", (warehouse_id,))
        if warehouse_info:
            metrics['current_utilization'] = warehouse_info[1]

        return metrics

    def _calculate_transfer_statistics(self, warehouse_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """حساب إحصائيات النقل"""
        stats = {
            'by_status': {},
            'by_type': {},
            'by_priority': {},
            'total_value': 0.0
        }

        # إحصائيات حسب الحالة
        query_status = """
            SELECT status, COUNT(*) FROM warehouse_transfers
            WHERE (from_warehouse_id = ? OR to_warehouse_id = ?)
            AND created_at BETWEEN ? AND ?
            GROUP BY status
        """
        results_status = self.db.fetch_all(query_status, (warehouse_id, warehouse_id, start_date.isoformat(), end_date.isoformat()))
        stats['by_status'] = {row[0]: row[1] for row in results_status} if results_status else {}

        # إحصائيات حسب النوع
        query_type = """
            SELECT transfer_type, COUNT(*) FROM warehouse_transfers
            WHERE (from_warehouse_id = ? OR to_warehouse_id = ?)
            AND created_at BETWEEN ? AND ?
            GROUP BY transfer_type
        """
        results_type = self.db.fetch_all(query_type, (warehouse_id, warehouse_id, start_date.isoformat(), end_date.isoformat()))
        stats['by_type'] = {row[0]: row[1] for row in results_type} if results_type else {}

        # إحصائيات حسب الأولوية
        query_priority = """
            SELECT priority, COUNT(*) FROM warehouse_transfers
            WHERE (from_warehouse_id = ? OR to_warehouse_id = ?)
            AND created_at BETWEEN ? AND ?
            GROUP BY priority
        """
        results_priority = self.db.fetch_all(query_priority, (warehouse_id, warehouse_id, start_date.isoformat(), end_date.isoformat()))
        stats['by_priority'] = {row[0]: row[1] for row in results_priority} if results_priority else {}

        # إجمالي القيمة
        query_value = """
            SELECT SUM(CAST(total_value AS DECIMAL)) FROM warehouse_transfers
            WHERE (from_warehouse_id = ? OR to_warehouse_id = ?)
            AND created_at BETWEEN ? AND ?
        """
        result_value = self.db.fetch_one(query_value, (warehouse_id, warehouse_id, start_date.isoformat(), end_date.isoformat()))
        stats['total_value'] = float(result_value[0]) if result_value and result_value[0] else 0.0

        return stats

    def _get_warehouse_alerts(self, warehouse_id: str) -> List[Dict[str, Any]]:
        """الحصول على تنبيهات المخزن"""
        alerts = []

        # التحقق من معدل الاستغلال
        warehouse_info = self.db.fetch_one("SELECT capacity, current_utilization FROM warehouses WHERE warehouse_id = ?", (warehouse_id,))
        if warehouse_info:
            capacity, utilization = warehouse_info
            if utilization > 90:
                alerts.append({
                    'type': 'high_utilization',
                    'severity': 'high',
                    'message': f"معدل استغلال المخزن مرتفع: {utilization}%"
                })
            elif utilization > 80:
                alerts.append({
                    'type': 'high_utilization',
                    'severity': 'medium',
                    'message': f"معدل استغلال المخزن متوسط: {utilization}%"
                })

        return alerts

    def _calculate_network_overview(self) -> Dict[str, Any]:
        """حساب نظرة عامة على شبكة المخازن"""
        overview = {
            'total_capacity': 0,
            'total_utilization': 0.0,
            'warehouses_by_type': {},
            'active_transfers': 0
        }

        # إجمالي السعة والاستغلال
        query_capacity = "SELECT SUM(capacity), AVG(current_utilization) FROM warehouses WHERE status = 'active'"
        result_capacity = self.db.fetch_one(query_capacity)
        if result_capacity:
            overview['total_capacity'] = result_capacity[0] or 0
            overview['total_utilization'] = float(result_capacity[1] or 0)

        # المخازن حسب النوع
        query_types = "SELECT type, COUNT(*) FROM warehouses WHERE status = 'active' GROUP BY type"
        results_types = self.db.fetch_all(query_types)
        overview['warehouses_by_type'] = {row[0]: row[1] for row in results_types} if results_types else {}

        # النقل النشط
        query_transfers = "SELECT COUNT(*) FROM warehouse_transfers WHERE status IN ('approved', 'in_transit')"
        result_transfers = self.db.fetch_one(query_transfers)
        overview['active_transfers'] = result_transfers[0] if result_transfers else 0

        return overview

    def _generate_network_recommendations(self) -> List[str]:
        """توليد توصيات عامة للشبكة"""
        recommendations = []

        overview = self._calculate_network_overview()

        # توصيات حول الاستغلال
        if overview['total_utilization'] > 85:
            recommendations.append("إضافة مخازن جديدة أو توسيع السعة الحالية")
        elif overview['total_utilization'] < 60:
            recommendations.append("تحسين توزيع المخزون لزيادة الاستغلال")

        # توصيات حول النقل النشط
        if overview['active_transfers'] > 10:
            recommendations.append("مراجعة عملية النقل وتحسين الكفاءة")

        return recommendations