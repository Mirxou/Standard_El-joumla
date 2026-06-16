import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة تكامل سلاسل التوريد - Supply Chain Integration Service
إدارة الموردين والمشتريات والتكامل مع سلاسل التوريد
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.services.advanced_inventory_management_service import (
    AdvancedInventoryManagementService,
)
from src.utils.logger import setup_logger


@dataclass
class Supplier:
    """مورد"""

    supplier_id: int
    name: str
    contact_info: Dict[str, Any]
    payment_terms: str
    lead_time_days: int
    reliability_score: float
    status: str  # 'active', 'inactive', 'blacklisted'
    categories: List[str]
    created_at: datetime


@dataclass
class PurchaseOrder:
    """أمر شراء"""

    po_id: str
    supplier_id: int
    items: List[Dict[str, Any]]
    total_amount: Decimal
    status: str  # 'draft', 'sent', 'confirmed', 'received', 'cancelled'
    expected_delivery: Optional[datetime]
    actual_delivery: Optional[datetime]
    created_by: int
    approved_by: Optional[int]
    created_at: datetime


@dataclass
class SupplierPerformance:
    """أداء المورد"""

    supplier_id: int
    on_time_delivery_rate: float
    quality_score: float
    average_lead_time: int
    total_orders: int
    total_value: Decimal
    last_order_date: Optional[datetime]
    performance_rating: str  # 'excellent', 'good', 'average', 'poor'


@dataclass
class SupplyChainAlert:
    """تنبيه سلسلة التوريد"""

    alert_id: str
    alert_type: str  # 'supplier_issue', 'delivery_delay', 'quality_problem', 'stockout_risk'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    affected_items: List[int]
    suggested_actions: List[str]
    created_at: datetime


class SupplyChainIntegrationService:
    """خدمة تكامل سلاسل التوريد"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        inventory_service: AdvancedInventoryManagementService,
    ):
        self.db = db_manager
        self.inventory_service = inventory_service
        self.config = ConfigManager()
        self.logger = setup_logger(__name__)

        # معلمات التكوين
        self.api_base_url = self.config.get("supply_chain.api_base_url", "")
        self.api_key = self.config.get("supply_chain.api_key", "")
        self.auto_po_approval_limit = self.config.get("supply_chain.auto_po_approval_limit", 5000)
        self.supplier_evaluation_period_days = self.config.get("supply_chain.evaluation_period_days", 365)

        # تحميل بيانات الموردين
        self._load_suppliers()

    def create_purchase_order(
        self,
        supplier_id: int,
        items: List[Dict[str, Any]],
        expected_delivery: Optional[datetime] = None,
        created_by: int = 1,
    ) -> str:
        """
        إنشاء أمر شراء

        Args:
            supplier_id: معرف المورد
            items: قائمة بالعناصر (product_id, quantity, unit_price)
            expected_delivery: تاريخ التسليم المتوقع
            created_by: معرف المستخدم المنشئ

        Returns:
            معرف أمر الشراء
        """
        try:
            po_id = f"PO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # حساب الإجمالي
            total_amount = Decimal("0")
            for item in items:
                total_amount += Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))

            # تحويل Decimal إلى string للتسلسل
            serializable_items = []
            for item in items:
                serializable_item = {
                    "product_id": item["product_id"],
                    "quantity": str(item["quantity"]),
                    "unit_price": str(item["unit_price"]),
                }
                serializable_items.append(serializable_item)

            # إنشاء أمر الشراء
            po_data = {
                "po_id": po_id,
                "supplier_id": supplier_id,
                "items": json.dumps(serializable_items),
                "total_amount": str(total_amount),
                "status": "draft",
                "expected_delivery": (expected_delivery.isoformat() if expected_delivery else None),
                "created_by": created_by,
                "created_at": datetime.now().isoformat(),
            }

            # إدراج في قاعدة البيانات
            self._insert_purchase_order(po_data)

            # إدراج عناصر أمر الشراء
            self._insert_purchase_order_items(po_id, items)

            return po_id

        except Exception as e:
            self.logger.error(f"Error creating purchase order: {e}", exc_info=True)
            raise

    def approve_purchase_order(self, po_id: str, approved_by: int) -> bool:
        """
        الموافقة على أمر شراء

        Args:
            po_id: معرف أمر الشراء
            approved_by: معرف المستخدم المعتمد

        Returns:
            نجاح العملية
        """
        try:
            # التحقق من الحد التلقائي
            po_data = self._get_purchase_order(po_id)
            total_amount = Decimal(po_data["total_amount"])

            if total_amount <= self.auto_po_approval_limit:
                # موافقة تلقائية
                self._update_purchase_order_status(po_id, "approved", approved_by)
                return True

            # موافقة يدوية مطلوبة
            self._update_purchase_order_status(po_id, "pending_approval", approved_by)

            # إرسال إشعار للموافقة
            self._send_approval_notification(po_id, total_amount)

            return True

        except Exception as e:
            self.logger.error(f"Error approving purchase order: {e}", exc_info=True)
            return False

    def receive_purchase_order(self, po_id: str, received_items: List[Dict[str, Any]], received_by: int = 1) -> bool:
        """
        استلام أمر شراء

        Args:
            po_id: معرف أمر الشراء
            received_items: العناصر المستلمة (product_id, batch_id, quantity, expiry_date)
            received_by: معرف المستخدم المستلم

        Returns:
            نجاح العملية
        """
        try:
            # تحديث حالة أمر الشراء
            self._update_purchase_order_status(po_id, "received", received_by)
            self._update_purchase_order_delivery(po_id, datetime.now())

            # إضافة العناصر للمخزون
            for item in received_items:
                product_id = item["product_id"]
                batch_id = item["batch_id"]
                quantity = item["quantity"]
                unit_cost = self._get_po_item_cost(po_id, product_id)
                expiry_date = item.get("expiry_date")
                warehouse_id = item.get("warehouse_id", 1)  # المستودع الافتراضي

                # إضافة للمخزون
                transaction_id = self.inventory_service.add_inventory_item(  # noqa: F841
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    batch_id=batch_id,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    expiry_date=expiry_date,
                    performed_by=received_by,
                )

                # تحديث حالة عنصر أمر الشراء
                self._update_po_item_status(po_id, product_id, "received", quantity)

            # تحديث أداء المورد
            po_data = self._get_purchase_order(po_id)
            self._update_supplier_performance(po_data["supplier_id"], po_id)

            return True

        except Exception as e:
            self.logger.error(f"Error receiving purchase order: {e}", exc_info=True)
            return False

    def evaluate_supplier_performance(self, supplier_id: int) -> SupplierPerformance:
        """
        تقييم أداء المورد

        Args:
            supplier_id: معرف المورد

        Returns:
            كائن أداء المورد
        """
        try:
            # جمع بيانات الأداء
            performance_data = self._get_supplier_performance_data(supplier_id)

            # حساب المقاييس
            on_time_delivery_rate = self._calculate_on_time_delivery_rate(performance_data)
            quality_score = self._calculate_quality_score(performance_data)
            average_lead_time = self._calculate_average_lead_time(performance_data)

            # تحديد التصنيف
            performance_rating = self._determine_performance_rating(
                on_time_delivery_rate, quality_score, average_lead_time
            )

            return SupplierPerformance(
                supplier_id=supplier_id,
                on_time_delivery_rate=on_time_delivery_rate,
                quality_score=quality_score,
                average_lead_time=average_lead_time,
                total_orders=performance_data["total_orders"],
                total_value=Decimal(str(performance_data["total_value"])),
                last_order_date=performance_data["last_order_date"],
                performance_rating=performance_rating,
            )

        except Exception as e:
            self.logger.error(f"Error evaluating supplier performance: {e}", exc_info=True)
            return SupplierPerformance(
                supplier_id=supplier_id,
                on_time_delivery_rate=0,
                quality_score=0,
                average_lead_time=0,
                total_orders=0,
                total_value=Decimal("0"),
                last_order_date=None,
                performance_rating="unknown",
            )

    def get_supply_chain_alerts(self) -> List[SupplyChainAlert]:
        """
        الحصول على تنبيهات سلسلة التوريد

        Returns:
            قائمة بتنبيهات سلسلة التوريد
        """
        alerts = []

        try:
            # تنبيهات الموردين
            supplier_alerts = self._check_supplier_alerts()
            alerts.extend(supplier_alerts)

            # تنبيهات التأخير في التسليم
            delivery_alerts = self._check_delivery_alerts()
            alerts.extend(delivery_alerts)

            # تنبيهات المخاطر
            risk_alerts = self._check_supply_risk_alerts()
            alerts.extend(risk_alerts)

            return alerts

        except Exception as e:
            self.logger.error(f"Error getting supply chain alerts: {e}", exc_info=True)
            return []

    def optimize_supplier_selection(self, product_id: int, quantity: int) -> List[Dict[str, Any]]:
        """
        تحسين اختيار المورد

        Args:
            product_id: معرف المنتج
            quantity: الكمية المطلوبة

        Returns:
            قائمة بالموردين المقترحين
        """
        try:
            # العثور على الموردين الذين يقدمون هذا المنتج
            suppliers = self._get_product_suppliers(product_id)

            recommendations = []
            for supplier in suppliers:
                if supplier["status"] != "active":
                    continue

                # تقييم المورد
                performance = self.evaluate_supplier_performance(supplier["supplier_id"])

                # حساب التكلفة الإجمالية
                unit_price = Decimal(str(supplier["unit_price"]))
                total_cost = unit_price * Decimal(str(quantity))

                # حساب الدرجة الإجمالية
                score = self._calculate_supplier_score(performance, unit_price, supplier["lead_time_days"])

                recommendations.append(
                    {
                        "supplier_id": supplier["supplier_id"],
                        "supplier_name": supplier["name"],
                        "unit_price": float(unit_price),
                        "total_cost": float(total_cost),
                        "lead_time_days": supplier["lead_time_days"],
                        "performance_rating": performance.performance_rating,
                        "score": score,
                    }
                )

            # ترتيب حسب الدرجة
            recommendations.sort(key=lambda x: x["score"], reverse=True)

            return recommendations

        except Exception as e:
            self.logger.error(f"Error optimizing supplier selection: {e}", exc_info=True)
            return []

    def generate_purchase_plan(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        توليد خطة المشتريات

        Args:
            days_ahead: عدد الأيام المستقبلية

        Returns:
            خطة المشتريات
        """
        try:
            plan = {
                "recommended_orders": [],
                "total_estimated_cost": 0,
                "priority_items": [],
                "generated_at": datetime.now().isoformat(),
            }

            # الحصول على المنتجات التي تحتاج إعادة طلب
            reorder_items = self._get_items_needing_reorder()

            for item in reorder_items:
                # تحسين اختيار المورد
                suppliers = self.optimize_supplier_selection(item["product_id"], item["recommended_quantity"])

                if suppliers:
                    best_supplier = suppliers[0]
                    plan["recommended_orders"].append(
                        {
                            "product_id": item["product_id"],
                            "product_name": item["product_name"],
                            "recommended_quantity": item["recommended_quantity"],
                            "best_supplier": best_supplier,
                            "estimated_cost": best_supplier["total_cost"],
                            "priority": item["priority"],
                        }
                    )

                    plan["total_estimated_cost"] += best_supplier["total_cost"]

                    if item["priority"] == "high":
                        plan["priority_items"].append(item["product_id"])

            return plan

        except Exception as e:
            self.logger.error(f"Error generating purchase plan: {e}", exc_info=True)
            return {}

    def sync_with_external_suppliers(self) -> Dict[str, Any]:
        """
        المزامنة مع الموردين الخارجيين

        Returns:
            نتائج المزامنة
        """
        try:
            sync_results = {
                "synced_suppliers": 0,
                "synced_products": 0,
                "errors": [],
                "timestamp": datetime.now().isoformat(),
            }

            if not self.api_base_url or not self.api_key:
                sync_results["errors"].append("API configuration missing")
                return sync_results

            # مزامنة بيانات الموردين
            suppliers_data = self._fetch_external_suppliers()
            for supplier_data in suppliers_data:
                try:
                    self._sync_supplier_data(supplier_data)
                    sync_results["synced_suppliers"] += 1
                except Exception as e:
                    sync_results["errors"].append(f"Supplier sync error: {e}")

            # مزامنة بيانات المنتجات
            products_data = self._fetch_external_products()
            for product_data in products_data:
                try:
                    self._sync_product_data(product_data)
                    sync_results["synced_products"] += 1
                except Exception as e:
                    sync_results["errors"].append(f"Product sync error: {e}")

            return sync_results

        except Exception as e:
            self.logger.error(f"Error syncing with external suppliers: {e}", exc_info=True)
            return {"error": str(e)}

    def _load_suppliers(self):
        """تحميل بيانات الموردين"""
        try:
            self.suppliers = {}
            query = """
                SELECT supplier_id, name, contact_info, payment_terms, lead_time_days,
                       reliability_score, status, categories
                FROM suppliers
                WHERE status = 'active'
            """
            data = self.db.execute_query(query, fetch_all=True)

            for row in data:
                self.suppliers[row[0]] = {
                    "name": row[1],
                    "contact_info": json.loads(row[2]) if row[2] else {},
                    "payment_terms": row[3],
                    "lead_time_days": row[4] or 7,
                    "reliability_score": float(row[5] or 0),
                    "status": row[6],
                    "categories": json.loads(row[7]) if row[7] else [],
                }

        except Exception as e:
            self.logger.error(f"Error loading suppliers: {e}", exc_info=True)
            self.suppliers = {}

    def _insert_purchase_order(self, po_data: Dict[str, Any]):
        """إدراج أمر شراء"""
        try:
            query = """
                INSERT INTO purchase_orders
                (po_id, supplier_id, items, total_amount, status, expected_delivery,
                 created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(
                query,
                (
                    po_data["po_id"],
                    po_data["supplier_id"],
                    po_data["items"],
                    po_data["total_amount"],
                    po_data["status"],
                    po_data["expected_delivery"],
                    po_data["created_by"],
                    po_data["created_at"],
                ),
            )

        except Exception as e:
            self.logger.error(f"Error inserting purchase order: {e}", exc_info=True)
            raise

    def _insert_purchase_order_items(self, po_id: str, items: List[Dict[str, Any]]):
        """إدراج عناصر أمر الشراء"""
        try:
            for item in items:
                query = """
                    INSERT INTO purchase_order_items
                    (po_id, product_id, quantity, unit_price, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """
                self.db.execute_query(
                    query,
                    (
                        po_id,
                        item["product_id"],
                        item["quantity"],
                        str(item["unit_price"]),
                    ),
                )

        except Exception as e:
            self.logger.error(f"Error inserting purchase order items: {e}", exc_info=True)
            raise

    def _get_purchase_order(self, po_id: str) -> Dict[str, Any]:
        """الحصول على أمر شراء"""
        try:
            query = "SELECT * FROM purchase_orders WHERE po_id = ?"
            data = self.db.execute_query(query, (po_id,), fetch_one=True)

            if data:
                return {
                    "po_id": data[0],
                    "supplier_id": data[1],
                    "items": json.loads(data[2]) if data[2] else [],
                    "total_amount": data[3],
                    "status": data[4],
                    "expected_delivery": data[5],
                    "actual_delivery": data[6],
                    "created_by": data[7],
                    "approved_by": data[8],
                    "created_at": data[9],
                }

            return {}

        except Exception as e:
            self.logger.error(f"Error getting purchase order: {e}", exc_info=True)
            return {}

    def _update_purchase_order_status(self, po_id: str, status: str, updated_by: int):
        """تحديث حالة أمر الشراء"""
        try:
            query = "UPDATE purchase_orders SET status = ?, approved_by = ? WHERE po_id = ?"
            self.db.execute_query(query, (status, updated_by, po_id))

        except Exception as e:
            self.logger.error(f"Error updating purchase order status: {e}", exc_info=True)

    def _update_purchase_order_delivery(self, po_id: str, delivery_date: datetime):
        """تحديث تاريخ التسليم"""
        try:
            query = "UPDATE purchase_orders SET actual_delivery = ? WHERE po_id = ?"
            self.db.execute_query(query, (delivery_date.isoformat(), po_id))

        except Exception as e:
            self.logger.error(f"Error updating purchase order delivery: {e}", exc_info=True)

    def _get_po_item_cost(self, po_id: str, product_id: int) -> Decimal:
        """الحصول على تكلفة عنصر من أمر الشراء"""
        try:
            query = "SELECT unit_price FROM purchase_order_items WHERE po_id = ? AND product_id = ?"
            data = self.db.execute_query(query, (po_id, product_id), fetch_one=True)
            return Decimal(str(data[0])) if data else Decimal("0")

        except Exception as e:
            self.logger.error(f"Error getting PO item cost: {e}", exc_info=True)
            return Decimal("0")

    def _update_po_item_status(self, po_id: str, product_id: int, status: str, received_quantity: int):
        """تحديث حالة عنصر أمر الشراء"""
        try:
            query = """
                UPDATE purchase_order_items
                SET status = ?, received_quantity = ?
                WHERE po_id = ? AND product_id = ?
            """
            self.db.execute_query(query, (status, received_quantity, po_id, product_id))

        except Exception as e:
            self.logger.error(f"Error updating PO item status: {e}", exc_info=True)

    def _update_supplier_performance(self, supplier_id: int, po_id: str):
        """تحديث أداء المورد"""
        try:
            # حساب التأخير في التسليم
            po_data = self._get_purchase_order(po_id)
            if po_data.get("expected_delivery") and po_data.get("actual_delivery"):
                expected = datetime.fromisoformat(po_data["expected_delivery"])
                actual = datetime.fromisoformat(po_data["actual_delivery"])
                delay_days = (actual - expected).days

                # تحديث درجة الموثوقية
                current_score = self.suppliers.get(supplier_id, {}).get("reliability_score", 0.5)
                if delay_days <= 0:
                    new_score = min(1.0, current_score + 0.1)  # مكافأة للتسليم في الوقت
                else:
                    new_score = max(0.0, current_score - 0.1)  # عقاب للتأخير

                # تحديث في قاعدة البيانات
                query = "UPDATE suppliers SET reliability_score = ? WHERE supplier_id = ?"
                self.db.execute_query(query, (new_score, supplier_id))

                # تحديث في الذاكرة
                if supplier_id in self.suppliers:
                    self.suppliers[supplier_id]["reliability_score"] = new_score

        except Exception as e:
            self.logger.error(f"Error updating supplier performance: {e}", exc_info=True)

    def _send_approval_notification(self, po_id: str, amount: Decimal):
        """إرسال إشعار الموافقة"""
        try:
            # في التطبيق الحقيقي، سيتم إرسال إشعار عبر البريد الإلكتروني أو النظام
            self.logger.info(f"إشعار: أمر شراء {po_id} يحتاج موافقة (المبلغ: {amount})")

        except Exception as e:
            self.logger.error(f"Error sending approval notification: {e}", exc_info=True)

    def _get_supplier_performance_data(self, supplier_id: int) -> Dict[str, Any]:
        """جمع بيانات أداء المورد"""
        try:
            # عدد الطلبات
            orders_query = """
                SELECT COUNT(*) as total_orders, SUM(total_amount) as total_value,
                       MAX(created_at) as last_order
                FROM purchase_orders
                WHERE supplier_id = ? AND status = 'received'
            """
            orders_data = self.db.execute_query(orders_query, (supplier_id,), fetch_one=True)

            # بيانات التسليم
            delivery_query = """
                SELECT expected_delivery, actual_delivery
                FROM purchase_orders
                WHERE supplier_id = ? AND status = 'received'
                AND expected_delivery IS NOT NULL AND actual_delivery IS NOT NULL
            """
            delivery_data = self.db.execute_query(delivery_query, (supplier_id,), fetch_all=True)

            return {
                "total_orders": orders_data[0] or 0 if orders_data else 0,
                "total_value": float(orders_data[1] or 0) if orders_data else 0,
                "last_order_date": orders_data[2] if orders_data else None,
                "delivery_data": delivery_data,
            }

        except Exception as e:
            self.logger.error(f"Error getting supplier performance data: {e}", exc_info=True)
            return {
                "total_orders": 0,
                "total_value": 0,
                "last_order_date": None,
                "delivery_data": [],
            }

    def _calculate_on_time_delivery_rate(self, performance_data: Dict[str, Any]) -> float:
        """حساب معدل التسليم في الوقت"""
        try:
            delivery_data = performance_data.get("delivery_data", [])
            if not delivery_data:
                return 0

            on_time_deliveries = 0
            for row in delivery_data:
                expected = datetime.fromisoformat(row[0])
                actual = datetime.fromisoformat(row[1])
                if actual <= expected:
                    on_time_deliveries += 1

            return on_time_deliveries / len(delivery_data)

        except Exception as e:
            self.logger.error(f"Error calculating on-time delivery rate: {e}", exc_info=True)
            return 0

    def _calculate_quality_score(self, performance_data: Dict[str, Any]) -> float:
        """حساب درجة الجودة"""
        # في التطبيق الحقيقي، سيتم حساب هذا بناءً على تقارير الجودة
        # للآن، نعتمد على معدل التسليم في الوقت كمؤشر للجودة
        return self._calculate_on_time_delivery_rate(performance_data)

    def _calculate_average_lead_time(self, performance_data: Dict[str, Any]) -> int:
        """حساب متوسط وقت الانتظار"""
        try:
            delivery_data = performance_data.get("delivery_data", [])
            if not delivery_data:
                return 7  # افتراضي

            lead_times = []
            for row in delivery_data:
                expected = datetime.fromisoformat(row[0])
                actual = datetime.fromisoformat(row[1])
                lead_times.append((actual - expected).days)

            return int(sum(lead_times) / len(lead_times))

        except Exception as e:
            self.logger.error(f"Error calculating average lead time: {e}", exc_info=True)
            return 7

    def _determine_performance_rating(self, on_time_rate: float, quality_score: float, lead_time: int) -> str:
        """تحديد تصنيف الأداء"""
        try:
            # حساب الدرجة المركبة
            composite_score = (on_time_rate * 0.4) + (quality_score * 0.4) + ((30 - min(lead_time, 30)) / 30 * 0.2)

            if composite_score >= 0.8:
                return "excellent"
            elif composite_score >= 0.6:
                return "good"
            elif composite_score >= 0.4:
                return "average"
            else:
                return "poor"

        except Exception as e:
            self.logger.error(f"Error determining performance rating: {e}", exc_info=True)
            return "unknown"

    def _check_supplier_alerts(self) -> List[SupplyChainAlert]:
        """فحص تنبيهات الموردين"""
        alerts = []

        try:
            for supplier_id, supplier_data in self.suppliers.items():
                # فحص الموثوقية المنخفضة
                if supplier_data["reliability_score"] < 0.5:
                    alerts.append(
                        SupplyChainAlert(
                            alert_id=f"SUPPLIER_LOW_RELIABILITY_{supplier_id}",
                            alert_type="supplier_issue",
                            severity="high",
                            description=f"موثوقية منخفضة للمورد {supplier_data['name']}",
                            affected_items=[],
                            suggested_actions=[
                                "مراجعة بدائل المورد",
                                "تفاوض على شروط أفضل",
                            ],
                            created_at=datetime.now(),
                        )
                    )

                # فحص عدم النشاط
                # (سيتم إضافة منطق إضافي هنا)

        except Exception as e:
            self.logger.error(f"Error checking supplier alerts: {e}", exc_info=True)

        return alerts

    def _check_delivery_alerts(self) -> List[SupplyChainAlert]:
        """فحص تنبيهات التأخير في التسليم"""
        alerts = []

        try:
            query = """
                SELECT po_id, supplier_id, expected_delivery
                FROM purchase_orders
                WHERE status = 'confirmed' AND expected_delivery < ?
            """

            tomorrow = datetime.now() + timedelta(days=1)
            data = self.db.execute_query(query, (tomorrow.isoformat(),), fetch_all=True)

            for row in data:
                po_id, supplier_id, expected_delivery = row
                supplier_name = self.suppliers.get(supplier_id, {}).get("name", "Unknown")

                alerts.append(
                    SupplyChainAlert(
                        alert_id=f"DELAY_{po_id}",
                        alert_type="delivery_delay",
                        severity="medium",
                        description=f"تأخير متوقع في تسليم أمر الشراء {po_id} من {supplier_name}",
                        affected_items=self._get_po_items(po_id),
                        suggested_actions=["الاتصال بالمورد", "البحث عن بدائل"],
                        created_at=datetime.now(),
                    )
                )

        except Exception as e:
            self.logger.error(f"Error checking delivery alerts: {e}", exc_info=True)

        return alerts

    def _check_supply_risk_alerts(self) -> List[SupplyChainAlert]:
        """فحص تنبيهات مخاطر التوريد"""
        alerts = []

        try:
            # فحص المنتجات ذات المورد الوحيد
            single_supplier_products = self._get_single_supplier_products()

            for product in single_supplier_products:
                alerts.append(
                    SupplyChainAlert(
                        alert_id=f"RISK_SINGLE_SUPPLIER_{product['product_id']}",
                        alert_type="stockout_risk",
                        severity="medium",
                        description=f"مخاطر توريد للمنتج {product['name']} (مورد وحيد)",
                        affected_items=[product["product_id"]],
                        suggested_actions=[
                            "البحث عن موردين بديلين",
                            "زيادة المخزون الآمن",
                        ],
                        created_at=datetime.now(),
                    )
                )

        except Exception as e:
            self.logger.error(f"Error checking supply risk alerts: {e}", exc_info=True)

        return alerts

    def _get_product_suppliers(self, product_id: int) -> List[Dict[str, Any]]:
        """الحصول على موردي منتج محدد"""
        try:
            query = """
                SELECT s.supplier_id, s.name, sp.unit_price, s.lead_time_days, s.status
                FROM suppliers s
                JOIN supplier_products sp ON s.supplier_id = sp.supplier_id
                WHERE sp.product_id = ?
            """
            data = self.db.execute_query(query, (product_id,), fetch_all=True)

            suppliers = []
            for row in data:
                suppliers.append(
                    {
                        "supplier_id": row[0],
                        "name": row[1],
                        "unit_price": float(row[2] or 0),
                        "lead_time_days": row[3] or 7,
                        "status": row[4],
                    }
                )

            return suppliers

        except Exception as e:
            self.logger.error(f"Error getting product suppliers: {e}", exc_info=True)
            return []

    def _calculate_supplier_score(self, performance: SupplierPerformance, unit_price: Decimal, lead_time: int) -> float:
        """حساب درجة المورد"""
        try:
            # وزن المقاييس
            performance_weight = 0.4
            price_weight = 0.3
            lead_time_weight = 0.3

            # تحويل التصنيف إلى رقم
            rating_scores = {
                "excellent": 1.0,
                "good": 0.8,
                "average": 0.6,
                "poor": 0.4,
                "unknown": 0.5,
            }

            performance_score = rating_scores.get(performance.performance_rating, 0.5)

            # تطبيع السعر (السعر الأقل أفضل)
            # في التطبيق الحقيقي، سيتم استخدام متوسط السعر للمقارنة
            price_score = 0.8  # افتراضي

            # تطبيع وقت الانتظار (الوقت الأقل أفضل)
            lead_time_score = max(0, 1 - (lead_time / 30))  # تطبيع لمدة 30 يوم

            total_score = (
                performance_score * performance_weight + price_score * price_weight + lead_time_score * lead_time_weight
            )

            return total_score

        except Exception as e:
            self.logger.error(f"Error calculating supplier score: {e}", exc_info=True)
            return 0

    def _get_items_needing_reorder(self) -> List[Dict[str, Any]]:
        """الحصول على المنتجات التي تحتاج إعادة طلب"""
        try:
            query = """
                SELECT p.id, p.name, p.current_stock, p.min_stock,
                       CASE
                           WHEN p.current_stock <= p.min_stock * 0.5 THEN 'high'
                           WHEN p.current_stock <= p.min_stock THEN 'medium'
                           ELSE 'low'
                       END as priority
                FROM products p
                WHERE p.is_active = 1 AND p.current_stock <= p.min_stock * 1.2
            """

            data = self.db.execute_query(query, fetch_all=True)

            items = []
            for row in data:
                product_id, name, current_stock, min_stock, priority = row

                # حساب الكمية الموصى بها
                recommended_quantity = max(min_stock * 2 - current_stock, min_stock - current_stock)

                items.append(
                    {
                        "product_id": product_id,
                        "product_name": name,
                        "current_stock": current_stock,
                        "min_stock": min_stock,
                        "recommended_quantity": int(recommended_quantity),
                        "priority": priority,
                    }
                )

            return items

        except Exception as e:
            self.logger.error(f"Error getting items needing reorder: {e}", exc_info=True)
            return []

    def _get_po_items(self, po_id: str) -> List[int]:
        """الحصول على عناصر أمر الشراء"""
        try:
            query = "SELECT product_id FROM purchase_order_items WHERE po_id = ?"
            data = self.db.execute_query(query, (po_id,), fetch_all=True)
            return [row[0] for row in data]

        except Exception as e:
            self.logger.error(f"Error getting PO items: {e}", exc_info=True)
            return []

    def _get_single_supplier_products(self) -> List[Dict[str, Any]]:
        """الحصول على المنتجات ذات المورد الوحيد"""
        try:
            query = """
                SELECT p.id, p.name, COUNT(sp.supplier_id) as supplier_count
                FROM products p
                LEFT JOIN supplier_products sp ON p.id = sp.product_id
                GROUP BY p.id, p.name
                HAVING supplier_count <= 1
            """

            data = self.db.execute_query(query, fetch_all=True)

            return [{"product_id": row[0], "name": row[1], "supplier_count": row[2]} for row in data]

        except Exception as e:
            self.logger.error(f"Error getting single supplier products: {e}", exc_info=True)
            return []

    def _fetch_external_suppliers(self) -> List[Dict[str, Any]]:
        """جلب بيانات الموردين الخارجيين"""
        try:
            # في التطبيق الحقيقي، سيتم استدعاء API خارجي
            return []

        except Exception as e:
            self.logger.error(f"Error fetching external suppliers: {e}", exc_info=True)
            return []

    def _fetch_external_products(self) -> List[Dict[str, Any]]:
        """جلب بيانات المنتجات الخارجية"""
        try:
            # في التطبيق الحقيقي، سيتم استدعاء API خارجي
            return []

        except Exception as e:
            self.logger.error(f"Error fetching external products: {e}", exc_info=True)
            return []

    def _sync_supplier_data(self, supplier_data: Dict[str, Any]):
        """مزامنة بيانات المورد"""
        try:
            # في التطبيق الحقيقي، سيتم تحديث قاعدة البيانات
            pass

        except Exception as e:
            self.logger.error(f"Error syncing supplier data: {e}", exc_info=True)

    def _sync_product_data(self, product_data: Dict[str, Any]):
        """مزامنة بيانات المنتج"""
        try:
            # في التطبيق الحقيقي، سيتم تحديث قاعدة البيانات
            pass

        except Exception as e:
            self.logger.error(f"Error syncing product data: {e}", exc_info=True)
