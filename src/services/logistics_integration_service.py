import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة تكامل اللوجستيات - Logistics Integration Service
إدارة النقل، التتبع، والتكامل مع شركات الشحن
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import requests

from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.services.multi_warehouse_management_service import (
    MultiWarehouseManagementService,
)
from src.utils.logger import setup_logger


@dataclass
class Shipment:
    """فئة تمثل الشحنة"""

    shipment_id: str
    transfer_id: Optional[str]
    carrier_id: str
    tracking_number: str
    status: str  # 'pending', 'picked_up', 'in_transit', 'delivered', 'failed'
    shipment_type: str  # 'warehouse_transfer', 'customer_delivery', 'supplier_return'
    origin_address: Dict[str, Any]
    destination_address: Dict[str, Any]
    items: List[Dict[str, Any]]
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Carrier:
    """فئة تمثل شركة الشحن"""

    carrier_id: str
    name: str
    carrier_type: str  # 'local', 'regional', 'international'
    services: List[str]  # قائمة الخدمات المقدمة
    api_config: Optional[Dict[str, Any]] = None
    contact_info: Optional[Dict[str, Any]] = None
    pricing_rules: Optional[Dict[str, Any]] = None
    status: str = "active"
    created_at: Optional[datetime] = None


@dataclass
class Route:
    """فئة تمثل المسار"""

    route_id: str
    origin_warehouse: str
    destination_warehouse: str
    distance_km: float
    estimated_duration_hours: float
    cost_per_km: Decimal
    preferred_carriers: List[str]
    route_type: str  # 'highway', 'air', 'sea', 'rail'
    status: str = "active"


@dataclass
class LogisticsAlert:
    """فئة تمثل تنبيهات اللوجستيات"""

    alert_id: str
    alert_type: str  # 'delay', 'damage', 'lost', 'cost_overrun'
    severity: str  # 'low', 'medium', 'high', 'critical'
    shipment_id: Optional[str] = None
    carrier_id: Optional[str] = None
    message: str = ""
    affected_items: Optional[List[Dict[str, Any]]] = None
    recommended_actions: Optional[List[str]] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: Optional[datetime] = None


class LogisticsIntegrationService:
    """
    خدمة تكامل اللوجستيات
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        warehouse_service: MultiWarehouseManagementService,
    ):
        self.db = db_manager
        self.warehouse_service = warehouse_service
        self.logger = setup_logger(__name__)
        self.config = ConfigManager()

        # إعدادات API لشركات الشحن
        self.api_endpoints = {
            "aramex": "https://api.aramex.com/v1",
            "dhl": "https://api.dhl.com/v1",
            "fedex": "https://api.fedex.com/v1",
            "ups": "https://api.ups.com/v1",
        }

    def register_carrier(self, carrier: Carrier) -> str:
        """
        تسجيل شركة شحن جديدة

        Args:
            carrier: بيانات شركة الشحن

        Returns:
            str: معرف شركة الشحن
        """
        try:
            carrier_id = f"CAR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            data = {
                "carrier_id": carrier_id,
                "name": carrier.name,
                "carrier_type": carrier.carrier_type,
                "services": json.dumps(carrier.services),
                "api_config": (json.dumps(carrier.api_config) if carrier.api_config else None),
                "contact_info": (json.dumps(carrier.contact_info) if carrier.contact_info else None),
                "pricing_rules": (json.dumps(carrier.pricing_rules) if carrier.pricing_rules else None),
                "status": carrier.status,
                "created_at": datetime.now().isoformat(),
            }

            self._insert_carrier(data)

            self.logger.info(f"تم تسجيل شركة الشحن: {carrier_id}")
            return carrier_id

        except Exception as e:
            self.logger.error(f"خطأ في تسجيل شركة الشحن: {e}")
            raise

    def create_shipment(self, shipment: Shipment) -> str:
        """
        إنشاء شحنة جديدة

        Args:
            shipment: بيانات الشحنة

        Returns:
            str: معرف الشحنة
        """
        try:
            shipment_id = f"SHIP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # حساب التكلفة التقديرية
            estimated_cost = self._calculate_shipping_cost(
                shipment.carrier_id,
                shipment.origin_address,
                shipment.destination_address,
                shipment.weight_kg or 0,
                shipment.volume_m3 or 0,
            )

            # تحويل العناصر إلى JSON
            serializable_items = []
            for item in shipment.items:
                serializable_item = {
                    "product_id": item["product_id"],
                    "quantity": str(item["quantity"]),
                    "weight_kg": str(item.get("weight_kg", 0)),
                    "volume_m3": str(item.get("volume_m3", 0)),
                }
                serializable_items.append(serializable_item)

            data = {
                "shipment_id": shipment_id,
                "transfer_id": shipment.transfer_id,
                "carrier_id": shipment.carrier_id,
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "shipment_type": shipment.shipment_type,
                "origin_address": json.dumps(shipment.origin_address),
                "destination_address": json.dumps(shipment.destination_address),
                "items": json.dumps(serializable_items),
                "weight_kg": str(shipment.weight_kg) if shipment.weight_kg else None,
                "volume_m3": str(shipment.volume_m3) if shipment.volume_m3 else None,
                "estimated_cost": str(estimated_cost) if estimated_cost else None,
                "estimated_delivery": (
                    shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None
                ),
                "created_by": shipment.created_by,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            self._insert_shipment(data)

            # إنشاء تتبع أولي
            self._create_tracking_event(shipment_id, "created", "تم إنشاء الشحنة")

            self.logger.info(f"تم إنشاء الشحنة: {shipment_id}")
            return shipment_id

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء الشحنة: {e}")
            raise

    def update_shipment_status(self, shipment_id: str, status: str, notes: str = "", updated_by: int = None) -> bool:
        """
        تحديث حالة الشحنة

        Args:
            shipment_id: معرف الشحنة
            status: الحالة الجديدة
            notes: ملاحظات
            updated_by: معرف المحدث

        Returns:
            bool: نجاح العملية
        """
        try:
            # التحقق من وجود الشحنة
            shipment_data = self._get_shipment(shipment_id)
            if not shipment_data:
                raise ValueError(f"الشحنة غير موجودة: {shipment_id}")

            # تحديث الحالة
            self._update_shipment_status_db(shipment_id, status, updated_by)

            # إنشاء حدث تتبع
            self._create_tracking_event(shipment_id, status, notes)

            # إذا تم التسليم، تحديث تاريخ التسليم الفعلي
            if status == "delivered":
                self._update_shipment_delivery(shipment_id, datetime.now())

            # التحقق من التنبيهات
            self._check_shipment_alerts(shipment_id, status)

            self.logger.info(f"تم تحديث حالة الشحنة {shipment_id} إلى {status}")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في تحديث حالة الشحنة: {e}")
            raise

    def get_shipment_tracking(self, shipment_id: str) -> List[Dict[str, Any]]:
        """
        الحصول على تتبع الشحنة

        Args:
            shipment_id: معرف الشحنة

        Returns:
            List[Dict[str, Any]]: قائمة أحداث التتبع
        """
        try:
            query = """
                SELECT event_type, description, location, timestamp, created_by
                FROM shipment_tracking
                WHERE shipment_id = ?
                ORDER BY timestamp DESC
            """
            results = self.db.fetch_all(query, (shipment_id,))
            return [dict(row) for row in results] if results else []

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على تتبع الشحنة: {e}")
            raise

    def calculate_optimal_route(
        self,
        origin_warehouse: str,
        destination_warehouse: str,
        weight_kg: float,
        volume_m3: float,
    ) -> Dict[str, Any]:
        """
        حساب المسار الأمثل للشحن

        Args:
            origin_warehouse: المخزن الأصل
            destination_warehouse: المخزن الوجهة
            weight_kg: الوزن بالكيلوغرام
            volume_m3: الحجم بالمتر المكعب

        Returns:
            Dict[str, Any]: تفاصيل المسار الأمثل
        """
        try:
            # الحصول على المسارات المتاحة
            routes = self._get_available_routes(origin_warehouse, destination_warehouse)

            if not routes:
                # إنشاء مسار افتراضي
                route = self._create_default_route(origin_warehouse, destination_warehouse)
                routes = [route]

            optimal_route = None
            min_cost = float("inf")

            for route in routes:
                # حساب التكلفة لكل شركة شحن
                for carrier_id in route["preferred_carriers"]:
                    cost = self._calculate_route_cost(route, carrier_id, weight_kg, volume_m3)
                    if cost < min_cost:
                        min_cost = cost
                        optimal_route = {
                            "route": route,
                            "carrier_id": carrier_id,
                            "estimated_cost": cost,
                            "estimated_duration": route["estimated_duration_hours"],
                        }

            return optimal_route

        except Exception as e:
            self.logger.error(f"خطأ في حساب المسار الأمثل: {e}")
            raise

    def get_carrier_performance_report(
        self, carrier_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        الحصول على تقرير أداء شركة الشحن

        Args:
            carrier_id: معرف شركة الشحن
            start_date: تاريخ البداية
            end_date: تاريخ النهاية

        Returns:
            Dict[str, Any]: تقرير الأداء
        """
        try:
            report = {
                "carrier_id": carrier_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "metrics": {},
                "performance": {},
                "issues": [],
            }

            # مقاييس الأداء الأساسية
            report["metrics"] = self._calculate_carrier_metrics(carrier_id, start_date, end_date)

            # أداء التسليم
            report["performance"] = self._calculate_delivery_performance(carrier_id, start_date, end_date)

            # المشاكل والتنبيهات
            report["issues"] = self._get_carrier_issues(carrier_id, start_date, end_date)

            return report

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء تقرير أداء شركة الشحن: {e}")
            raise

    def sync_with_carrier_api(self, carrier_id: str, shipment_id: str) -> bool:
        """
        مزامنة مع API شركة الشحن

        Args:
            carrier_id: معرف شركة الشحن
            shipment_id: معرف الشحنة

        Returns:
            bool: نجاح المزامنة
        """
        try:
            # الحصول على إعدادات API
            carrier_config = self._get_carrier_api_config(carrier_id)
            if not carrier_config:
                self.logger.warning(f"لا توجد إعدادات API لشركة الشحن: {carrier_id}")
                return False

            # الحصول على بيانات الشحنة
            shipment_data = self._get_shipment(shipment_id)
            if not shipment_data:
                raise ValueError(f"الشحنة غير موجودة: {shipment_id}")

            # مزامنة حالة الشحنة
            api_status = self._call_carrier_api(
                carrier_config,
                "get_status",
                {"tracking_number": shipment_data["tracking_number"]},
            )

            if api_status:
                # تحديث الحالة محلياً
                self.update_shipment_status(
                    shipment_id,
                    api_status["status"],
                    f"مزامنة مع API: {api_status['description']}",
                )

                # إضافة أحداث التتبع
                for event in api_status.get("events", []):
                    self._create_tracking_event(
                        shipment_id,
                        event["status"],
                        event["description"],
                        event.get("location"),
                        event["timestamp"],
                    )

            self.logger.info(f"تم مزامنة الشحنة {shipment_id} مع API شركة الشحن {carrier_id}")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في مزامنة مع API شركة الشحن: {e}")
            return False

    def get_logistics_alerts(self) -> List[LogisticsAlert]:
        """
        الحصول على تنبيهات اللوجستيات

        Returns:
            List[LogisticsAlert]: قائمة التنبيهات
        """
        try:
            alerts = []

            # تنبيهات التأخير
            delay_alerts = self._check_delivery_delays()
            alerts.extend(delay_alerts)

            # تنبيهات التكلفة
            cost_alerts = self._check_cost_overruns()
            alerts.extend(cost_alerts)

            # تنبيهات الشحنات المفقودة
            lost_alerts = self._check_lost_shipments()
            alerts.extend(lost_alerts)

            return alerts

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على تنبيهات اللوجستيات: {e}")
            raise

    def optimize_shipping_costs(self) -> Dict[str, Any]:
        """
        تحسين تكاليف الشحن

        Returns:
            Dict[str, Any]: توصيات التحسين
        """
        try:
            optimization = {
                "current_costs": {},
                "potential_savings": {},
                "recommendations": [],
                "generated_at": datetime.now().isoformat(),
            }

            # تحليل التكاليف الحالية
            optimization["current_costs"] = self._analyze_current_shipping_costs()

            # حساب التوفيرات المحتملة
            optimization["potential_savings"] = self._calculate_potential_savings()

            # توليد التوصيات
            optimization["recommendations"] = self._generate_cost_optimization_recommendations()

            return optimization

        except Exception as e:
            self.logger.error(f"خطأ في تحسين تكاليف الشحن: {e}")
            raise

    # طرق مساعدة لقاعدة البيانات
    def _insert_carrier(self, data: Dict[str, Any]) -> None:
        """إدراج شركة شحن في قاعدة البيانات"""
        query = """
            INSERT INTO carriers (
                carrier_id, name, carrier_type, services, api_config,
                contact_info, pricing_rules, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["carrier_id"],
            data["name"],
            data["carrier_type"],
            data["services"],
            data["api_config"],
            data["contact_info"],
            data["pricing_rules"],
            data["status"],
            data["created_at"],
        )
        self.db.execute_non_query(query, params)

    def _insert_shipment(self, data: Dict[str, Any]) -> None:
        """إدراج شحنة في قاعدة البيانات"""
        query = """
            INSERT INTO shipments (
                shipment_id, transfer_id, carrier_id, tracking_number, status,
                shipment_type, origin_address, destination_address, items,
                weight_kg, volume_m3, estimated_cost, estimated_delivery,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["shipment_id"],
            data["transfer_id"],
            data["carrier_id"],
            data["tracking_number"],
            data["status"],
            data["shipment_type"],
            data["origin_address"],
            data["destination_address"],
            data["items"],
            data["weight_kg"],
            data["volume_m3"],
            data["estimated_cost"],
            data["estimated_delivery"],
            data["created_by"],
            data["created_at"],
            data["updated_at"],
        )
        self.db.execute_non_query(query, params)

    def _get_shipment(self, shipment_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات الشحنة"""
        query = "SELECT * FROM shipments WHERE shipment_id = ?"
        result = self.db.fetch_one(query, (shipment_id,))
        return dict(result) if result else None

    def _update_shipment_status_db(self, shipment_id: str, status: str, updated_by: int) -> None:
        """تحديث حالة الشحنة في قاعدة البيانات"""
        query = "UPDATE shipments SET status = ?, updated_at = ? WHERE shipment_id = ?"
        params = (status, datetime.now().isoformat(), shipment_id)
        self.db.execute_non_query(query, params)

    def _update_shipment_delivery(self, shipment_id: str, delivery_date: datetime) -> None:
        """تحديث تاريخ التسليم الفعلي"""
        query = "UPDATE shipments SET actual_delivery = ? WHERE shipment_id = ?"
        params = (delivery_date.isoformat(), shipment_id)
        self.db.execute_non_query(query, params)

    def _create_tracking_event(
        self,
        shipment_id: str,
        event_type: str,
        description: str,
        location: str = None,
        timestamp: str = None,
    ) -> None:
        """إنشاء حدث تتبع"""
        if not timestamp:
            timestamp = datetime.now().isoformat()

        query = """
            INSERT INTO shipment_tracking (
                shipment_id, event_type, description, location, timestamp
            ) VALUES (?, ?, ?, ?, ?)
        """
        params = (shipment_id, event_type, description, location, timestamp)
        self.db.execute_non_query(query, params)

    def _calculate_shipping_cost(
        self,
        carrier_id: str,
        origin: Dict[str, Any],
        destination: Dict[str, Any],
        weight: float,
        volume: float,
    ) -> Optional[Decimal]:
        """حساب تكلفة الشحن"""
        try:
            # الحصول على قواعد التسعير
            carrier = self._get_carrier(carrier_id)
            if not carrier or not carrier.get("pricing_rules"):
                return None

            pricing_rules = json.loads(carrier["pricing_rules"])

            # حساب المسافة (تبسيط - يمكن تحسينه باستخدام Google Maps API)
            distance = self._calculate_distance(origin, destination)

            # حساب التكلفة الأساسية
            base_cost = pricing_rules.get("base_cost", 0)
            cost_per_kg = pricing_rules.get("cost_per_kg", 0)
            cost_per_km = pricing_rules.get("cost_per_km", 0)

            total_cost = base_cost + (weight * cost_per_kg) + (distance * cost_per_km)

            return Decimal(str(total_cost))

        except Exception as e:
            self.logger.error(f"خطأ في حساب تكلفة الشحن: {e}")
            return None

    def _calculate_distance(self, origin: Dict[str, Any], destination: Dict[str, Any]) -> float:
        """حساب المسافة بين نقطتين (تبسيط)"""
        # هذا حساب تقريبي - يمكن تحسينه باستخدام خدمة خرائط
        try:
            # افتراض أن العناوين تحتوي على إحداثيات
            origin_lat = origin.get("latitude", 0)
            origin_lng = origin.get("longitude", 0)
            dest_lat = destination.get("latitude", 0)
            dest_lng = destination.get("longitude", 0)

            # حساب المسافة باستخدام صيغة هافرساين (Haversine formula)
            import math

            R = 6371  # نصف قطر الأرض بالكيلومتر

            dlat = math.radians(dest_lat - origin_lat)
            dlng = math.radians(dest_lng - origin_lng)

            a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(origin_lat)) * math.cos(
                math.radians(dest_lat)
            ) * math.sin(dlng / 2) * math.sin(dlng / 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            distance = R * c
            return distance

        except Exception:
            # إرجاع مسافة افتراضية في حالة الخطأ
            return 100.0

    def _get_carrier(self, carrier_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات شركة الشحن"""
        query = "SELECT * FROM carriers WHERE carrier_id = ?"
        result = self.db.fetch_one(query, (carrier_id,))
        return dict(result) if result else None

    def _get_available_routes(self, origin: str, destination: str) -> List[Dict[str, Any]]:
        """الحصول على المسارات المتاحة"""
        query = """
            SELECT * FROM routes
            WHERE origin_warehouse = ? AND destination_warehouse = ? AND status = 'active'
        """
        results = self.db.fetch_all(query, (origin, destination))
        return [dict(row) for row in results] if results else []

    def _create_default_route(self, origin: str, destination: str) -> Dict[str, Any]:
        """إنشاء مسار افتراضي"""
        route_id = f"ROUTE_{origin}_{destination}"

        # إدراج المسار في قاعدة البيانات
        query = """
            INSERT OR IGNORE INTO routes (
                route_id, origin_warehouse, destination_warehouse,
                distance_km, estimated_duration_hours, cost_per_km,
                preferred_carriers, route_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            route_id,
            origin,
            destination,
            100.0,
            5.0,
            Decimal("0.5"),
            '["local_carrier"]',
            "highway",
            "active",
        )
        self.db.execute_non_query(query, params)

        return {
            "route_id": route_id,
            "origin_warehouse": origin,
            "destination_warehouse": destination,
            "distance_km": 100.0,
            "estimated_duration_hours": 5.0,
            "cost_per_km": Decimal("0.5"),
            "preferred_carriers": ["local_carrier"],
            "route_type": "highway",
        }

    def _calculate_route_cost(self, route: Dict[str, Any], carrier_id: str, weight: float, volume: float) -> float:
        """حساب تكلفة المسار"""
        try:
            base_cost = route["distance_km"] * float(route["cost_per_km"])

            # إضافة تكلفة الوزن والحجم حسب شركة الشحن
            carrier = self._get_carrier(carrier_id)
            if carrier and carrier.get("pricing_rules"):
                pricing = json.loads(carrier["pricing_rules"])
                weight_cost = weight * pricing.get("cost_per_kg", 0)
                volume_cost = volume * pricing.get("cost_per_m3", 0)
                base_cost += weight_cost + volume_cost

            return base_cost

        except Exception:
            return float("inf")

    def _check_shipment_alerts(self, shipment_id: str, status: str) -> None:
        """التحقق من تنبيهات الشحنة"""
        try:
            shipment = self._get_shipment(shipment_id)
            if not shipment:
                return

            alerts = []

            # تنبيه التأخير
            if status == "in_transit" and shipment.get("estimated_delivery"):
                estimated = datetime.fromisoformat(shipment["estimated_delivery"])
                if datetime.now() > estimated:
                    alerts.append(
                        {
                            "alert_type": "delay",
                            "severity": "medium",
                            "message": f"تأخير في الشحنة {shipment_id}",
                            "shipment_id": shipment_id,
                        }
                    )

            # تنبيه تجاوز التكلفة
            if shipment.get("actual_cost") and shipment.get("estimated_cost"):
                actual = Decimal(shipment["actual_cost"])
                estimated = Decimal(shipment["estimated_cost"])
                if actual > estimated * Decimal("1.2"):  # تجاوز 20%
                    alerts.append(
                        {
                            "alert_type": "cost_overrun",
                            "severity": "high",
                            "message": f"تجاوز التكلفة في الشحنة {shipment_id}",
                            "shipment_id": shipment_id,
                        }
                    )

            # إدراج التنبيهات
            for alert in alerts:
                self._insert_logistics_alert(alert)

        except Exception as e:
            self.logger.error(f"خطأ في التحقق من تنبيهات الشحنة: {e}")

    def _insert_logistics_alert(self, alert_data: Dict[str, Any]) -> None:
        """إدراج تنبيه لوجستي"""
        alert_id = f"LOG_ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        query = """
            INSERT INTO logistics_alerts (
                alert_id, alert_type, severity, shipment_id, carrier_id,
                message, affected_items, recommended_actions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            alert_id,
            alert_data["alert_type"],
            alert_data["severity"],
            alert_data.get("shipment_id"),
            alert_data.get("carrier_id"),
            alert_data["message"],
            json.dumps(alert_data.get("affected_items", [])),
            json.dumps(alert_data.get("recommended_actions", [])),
            datetime.now().isoformat(),
        )
        self.db.execute_non_query(query, params)

    def _get_carrier_api_config(self, carrier_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على إعدادات API لشركة الشحن"""
        carrier = self._get_carrier(carrier_id)
        if carrier and carrier.get("api_config"):
            return json.loads(carrier["api_config"])
        return None

    def _call_carrier_api(
        self, config: Dict[str, Any], endpoint: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """استدعاء API شركة الشحن"""
        try:
            base_url = config.get("base_url")
            api_key = config.get("api_key")

            if not base_url or not api_key:
                return None

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            url = f"{base_url}/{endpoint}"
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"فشل استدعاء API: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"خطأ في استدعاء API شركة الشحن: {e}")
            return None

    def _calculate_carrier_metrics(self, carrier_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """حساب مقاييس أداء شركة الشحن"""
        metrics = {
            "total_shipments": 0,
            "on_time_delivery_rate": 0.0,
            "average_cost_per_kg": 0.0,
            "damage_rate": 0.0,
        }

        # إجمالي الشحنات
        query_total = """
            SELECT COUNT(*) FROM shipments
            WHERE carrier_id = ? AND created_at BETWEEN ? AND ?
        """
        result_total = self.db.fetch_one(query_total, (carrier_id, start_date.isoformat(), end_date.isoformat()))
        metrics["total_shipments"] = result_total[0] if result_total else 0

        # معدل التسليم في الوقت المحدد
        query_ontime = """
            SELECT COUNT(*) FROM shipments
            WHERE carrier_id = ? AND status = 'delivered'
            AND actual_delivery <= estimated_delivery
            AND created_at BETWEEN ? AND ?
        """
        result_ontime = self.db.fetch_one(query_ontime, (carrier_id, start_date.isoformat(), end_date.isoformat()))
        if metrics["total_shipments"] > 0:
            metrics["on_time_delivery_rate"] = (
                (result_ontime[0] / metrics["total_shipments"]) * 100 if result_ontime else 0
            )

        return metrics

    def _calculate_delivery_performance(
        self, carrier_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """حساب أداء التسليم"""
        performance = {
            "average_delivery_time": 0.0,
            "reliability_score": 0.0,
            "customer_satisfaction": 0.0,
        }

        # متوسط وقت التسليم
        query_avg_time = """
            SELECT AVG(JULIANDAY(actual_delivery) - JULIANDAY(estimated_delivery))
            FROM shipments
            WHERE carrier_id = ? AND status = 'delivered'
            AND actual_delivery IS NOT NULL AND estimated_delivery IS NOT NULL
            AND created_at BETWEEN ? AND ?
        """
        result_avg = self.db.fetch_one(query_avg_time, (carrier_id, start_date.isoformat(), end_date.isoformat()))
        performance["average_delivery_time"] = result_avg[0] if result_avg and result_avg[0] else 0.0

        return performance

    def _get_carrier_issues(self, carrier_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """الحصول على مشاكل شركة الشحن"""
        issues = []

        # الشحنات المتأخرة
        query_delays = """
            SELECT COUNT(*) FROM shipments
            WHERE carrier_id = ? AND status = 'delivered'
            AND actual_delivery > estimated_delivery
            AND created_at BETWEEN ? AND ?
        """
        result_delays = self.db.fetch_one(query_delays, (carrier_id, start_date.isoformat(), end_date.isoformat()))
        if result_delays and result_delays[0] > 0:
            issues.append(
                {
                    "type": "delays",
                    "count": result_delays[0],
                    "description": f"{result_delays[0]} شحنة متأخرة",
                }
            )

        return issues

    def _check_delivery_delays(self) -> List[LogisticsAlert]:
        """التحقق من تأخيرات التسليم"""
        alerts = []

        query = """
            SELECT shipment_id, carrier_id, estimated_delivery
            FROM shipments
            WHERE status IN ('pending', 'picked_up', 'in_transit')
            AND estimated_delivery < ?
        """
        delayed_shipments = self.db.fetch_all(query, (datetime.now().isoformat(),))

        for shipment in delayed_shipments:
            alerts.append(
                LogisticsAlert(
                    alert_id=f"DELAY_{shipment[0]}",
                    alert_type="delay",
                    severity="high",
                    shipment_id=shipment[0],
                    carrier_id=shipment[1],
                    message=f"تأخير في الشحنة {shipment[0]}",
                    recommended_actions=["الاتصال بشركة الشحن", "إعادة جدولة التسليم"],
                    created_at=datetime.now(),
                )
            )

        return alerts

    def _check_cost_overruns(self) -> List[LogisticsAlert]:
        """التحقق من تجاوز التكاليف"""
        alerts = []

        query = """
            SELECT shipment_id, carrier_id, estimated_cost, actual_cost
            FROM shipments
            WHERE actual_cost > estimated_cost * 1.2
            AND actual_cost IS NOT NULL
        """
        overruns = self.db.fetch_all(query)

        for overrun in overruns:
            alerts.append(
                LogisticsAlert(
                    alert_id=f"COST_{overrun[0]}",
                    alert_type="cost_overrun",
                    severity="medium",
                    shipment_id=overrun[0],
                    carrier_id=overrun[1],
                    message=f"تجاوز التكلفة في الشحنة {overrun[0]}",
                    recommended_actions=["مراجعة الفاتورة", "التفاوض مع شركة الشحن"],
                    created_at=datetime.now(),
                )
            )

        return alerts

    def _check_lost_shipments(self) -> List[LogisticsAlert]:
        """التحقق من الشحنات المفقودة"""
        alerts = []

        # شحنات في حالة "in_transit" لأكثر من 30 يوم
        cutoff_date = datetime.now() - timedelta(days=30)

        query = """
            SELECT shipment_id, carrier_id, created_at
            FROM shipments
            WHERE status = 'in_transit'
            AND created_at < ?
        """
        lost_shipments = self.db.fetch_all(query, (cutoff_date.isoformat(),))

        for shipment in lost_shipments:
            alerts.append(
                LogisticsAlert(
                    alert_id=f"LOST_{shipment[0]}",
                    alert_type="lost",
                    severity="critical",
                    shipment_id=shipment[0],
                    carrier_id=shipment[1],
                    message=f"شحنة مفقودة {shipment[0]}",
                    recommended_actions=["الاتصال بشركة الشحن", "بدء إجراءات التأمين"],
                    created_at=datetime.now(),
                )
            )

        return alerts

    def _analyze_current_shipping_costs(self) -> Dict[str, Any]:
        """تحليل التكاليف الحالية للشحن"""
        analysis = {
            "total_cost_last_month": 0.0,
            "average_cost_per_shipment": 0.0,
            "cost_by_carrier": {},
            "cost_trends": [],
        }

        # التكلفة الإجمالية للشهر الماضي
        last_month = datetime.now() - timedelta(days=30)
        query_total = """
            SELECT SUM(CAST(actual_cost AS DECIMAL))
            FROM shipments
            WHERE created_at >= ?
        """
        result_total = self.db.fetch_one(query_total, (last_month.isoformat(),))
        analysis["total_cost_last_month"] = float(result_total[0]) if result_total and result_total[0] else 0.0

        # متوسط التكلفة لكل شحنة
        query_avg = """
            SELECT AVG(CAST(actual_cost AS DECIMAL))
            FROM shipments
            WHERE actual_cost IS NOT NULL
            AND created_at >= ?
        """
        result_avg = self.db.fetch_one(query_avg, (last_month.isoformat(),))
        analysis["average_cost_per_shipment"] = float(result_avg[0]) if result_avg and result_avg[0] else 0.0

        return analysis

    def _calculate_potential_savings(self) -> Dict[str, Any]:
        """حساب التوفيرات المحتملة"""
        savings = {
            "route_optimization": 0.0,
            "carrier_negotiation": 0.0,
            "consolidation": 0.0,
        }

        # توفيرات تحسين المسارات (تقدير 10-15%)
        current_costs = self._analyze_current_shipping_costs()
        savings["route_optimization"] = current_costs["total_cost_last_month"] * 0.12

        # توفيرات التفاوض مع شركات الشحن (تقدير 5-8%)
        savings["carrier_negotiation"] = current_costs["total_cost_last_month"] * 0.065

        # توفيرات دمج الشحنات (تقدير 8-12%)
        savings["consolidation"] = current_costs["total_cost_last_month"] * 0.10

        return savings

    def _generate_cost_optimization_recommendations(self) -> List[str]:
        """توليد توصيات تحسين التكاليف"""
        recommendations = [
            "دمج الشحنات الصغيرة لتقليل التكاليف",
            "التفاوض مع شركات الشحن للحصول على أسعار أفضل",
            "تحسين تخطيط المسارات لتقليل المسافات",
            "استخدام شركات شحن بديلة للمسارات عالية التكلفة",
            "جدولة الشحنات في أوقات ذروة للحصول على تخفيضات",
        ]

        return recommendations
