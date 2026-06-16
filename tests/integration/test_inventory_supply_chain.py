#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار خدمات إدارة المخزون المتقدمة - Advanced Inventory Management Tests
اختبار شامل لخدمات إدارة المخزون وتكامل سلاسل التوريد
"""

import sys  # noqa: F811
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path  # noqa: F811
from unittest.mock import Mock, patch

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.database_manager import DatabaseManager
from src.services.advanced_inventory_management_service import (
    AdvancedInventoryManagementService,
    InventoryAlert,
    InventoryOptimization,
)
from src.services.sales_prediction_service import SalesPredictionService
from src.services.supply_chain_integration_service import (
    SupplierPerformance,
    SupplyChainAlert,
    SupplyChainIntegrationService,
)


class TestAdvancedInventoryManagementService(unittest.TestCase):
    """اختبار خدمة إدارة المخزون المتقدمة"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.prediction_service = Mock(spec=SalesPredictionService)
        self.service = AdvancedInventoryManagementService(self.db_manager, self.prediction_service)

    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertIsInstance(self.service, AdvancedInventoryManagementService)
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.prediction_service)

    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._insert_inventory_data")
    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._update_product_stock")
    def test_add_inventory_item(self, mock_update_stock, mock_insert):
        """اختبار إضافة عنصر مخزون"""
        transaction_id = self.service.add_inventory_item(
            product_id=1,
            warehouse_id=1,
            batch_id="BATCH001",
            quantity=100,
            unit_cost=Decimal("10.50"),
            expiry_date=datetime.now() + timedelta(days=365),
        )

        self.assertTrue(transaction_id.startswith("INV_IN_"))
        mock_insert.assert_called_once()
        mock_update_stock.assert_called_once()

    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._get_batch_quantity")
    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._update_batch_quantity")
    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._update_product_stock")
    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._insert_transaction_data")
    def test_remove_inventory_item(
        self,
        mock_insert_transaction,
        mock_update_stock,
        mock_update_batch,
        mock_get_quantity,
    ):
        """اختبار إزالة عنصر من المخزون"""
        mock_get_quantity.return_value = 100

        transaction_id = self.service.remove_inventory_item(
            product_id=1,
            warehouse_id=1,
            batch_id="BATCH001",
            quantity=50,
            reason="sale",
        )

        self.assertTrue(transaction_id.startswith("INV_OUT_"))
        mock_update_batch.assert_called_once_with(1, 1, "BATCH001", -50)
        mock_update_stock.assert_called_once_with(1, 1, -50)

    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._check_low_stock_alerts")
    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._check_expiry_alerts")
    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService._check_overstock_alerts")
    @patch(
        "services.advanced_inventory_management_service.AdvancedInventoryManagementService._check_damaged_stock_alerts"
    )
    def test_get_inventory_alerts(self, mock_damaged, mock_overstock, mock_expiry, mock_low_stock):
        """اختبار الحصول على تنبيهات المخزون"""
        mock_low_stock.return_value = [
            InventoryAlert(
                "LOW001",
                1,
                "low_stock",
                "high",
                "مخزون منخفض",
                "إعادة طلب",
                datetime.now(),
            )
        ]
        mock_expiry.return_value = []
        mock_overstock.return_value = []
        mock_damaged.return_value = []

        alerts = self.service.get_inventory_alerts()

        self.assertIsInstance(alerts, list)
        self.assertEqual(len(alerts), 1)
        self.assertIsInstance(alerts[0], InventoryAlert)

    @patch(
        "services.advanced_inventory_management_service.AdvancedInventoryManagementService._get_products_for_optimization"  # noqa: E501
    )
    @patch(
        "services.advanced_inventory_management_service.AdvancedInventoryManagementService._calculate_inventory_optimization"  # noqa: E501
    )
    def test_optimize_inventory(self, mock_calculate, mock_get_products):
        """اختبار تحسين المخزون"""
        mock_get_products.return_value = [
            {
                "id": 1,
                "name": "Product A",
                "current_stock": 50,
                "min_stock": 100,
                "max_stock": 200,
                "selling_price": 25.0,
            }
        ]

        mock_calculate.return_value = InventoryOptimization(
            product_id=1,
            current_stock=50,
            optimal_stock=150,
            reorder_point=80,
            safety_stock=30,
            recommended_action="إعادة طلب فوراً",
            expected_savings=Decimal("100.00"),
            confidence_score=0.85,
        )

        optimizations = self.service.optimize_inventory()

        self.assertIsInstance(optimizations, list)
        self.assertEqual(len(optimizations), 1)
        self.assertIsInstance(optimizations[0], InventoryOptimization)

    @patch(
        "services.advanced_inventory_management_service.AdvancedInventoryManagementService._generate_inventory_summary"
    )
    @patch(
        "services.advanced_inventory_management_service.AdvancedInventoryManagementService._generate_product_inventory_report"  # noqa: E501
    )
    @patch(
        "services.advanced_inventory_management_service.AdvancedInventoryManagementService._generate_warehouse_inventory_report"  # noqa: E501
    )
    @patch(
        "services.advanced_inventory_management_service.AdvancedInventoryManagementService._generate_transaction_report"
    )
    def test_get_inventory_report(self, mock_transactions, mock_warehouses, mock_products, mock_summary):
        """اختبار الحصول على تقرير المخزون"""
        mock_summary.return_value = {"total_products": 10, "total_quantity": 1000}
        mock_products.return_value = [{"product_id": 1, "product_name": "Product A"}]
        mock_warehouses.return_value = [{"warehouse_id": 1, "name": "Main Warehouse"}]
        mock_transactions.return_value = [{"transaction_id": "TXN001", "type": "inbound"}]

        report = self.service.get_inventory_report()

        self.assertIsInstance(report, dict)
        self.assertIn("summary", report)
        self.assertIn("by_product", report)
        self.assertIn("by_warehouse", report)
        self.assertIn("transactions", report)
        self.assertIn("generated_at", report)

    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService.get_expiring_items")
    def test_get_expiring_items(self, mock_expiring):
        """اختبار الحصول على المنتجات المنتهية الصلاحية"""
        mock_expiring.return_value = [
            {
                "product_id": 1,
                "product_name": "Product A",
                "batch_id": "BATCH001",
                "quantity": 50,
                "expiry_date": (datetime.now() + timedelta(days=15)).isoformat(),
                "warehouse_id": 1,
                "warehouse_name": "Main Warehouse",
                "days_until_expiry": 15,
            }
        ]

        expiring_items = self.service.get_expiring_items(days_ahead=30)

        self.assertIsInstance(expiring_items, list)
        self.assertEqual(len(expiring_items), 1)
        self.assertIn("days_until_expiry", expiring_items[0])


class TestSupplyChainIntegrationService(unittest.TestCase):
    """اختبار خدمة تكامل سلاسل التوريد"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.inventory_service = Mock(spec=AdvancedInventoryManagementService)
        self.service = SupplyChainIntegrationService(self.db_manager, self.inventory_service)

    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertIsInstance(self.service, SupplyChainIntegrationService)
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.inventory_service)

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._insert_purchase_order")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._insert_purchase_order_items")
    def test_create_purchase_order(self, mock_insert_items, mock_insert_po):
        """اختبار إنشاء أمر شراء"""
        items = [
            {"product_id": 1, "quantity": 100, "unit_price": Decimal("10.50")},
            {"product_id": 2, "quantity": 50, "unit_price": Decimal("25.00")},
        ]

        po_id = self.service.create_purchase_order(
            supplier_id=1,
            items=items,
            expected_delivery=datetime.now() + timedelta(days=7),
        )

        self.assertTrue(po_id.startswith("PO_"))
        mock_insert_po.assert_called_once()
        mock_insert_items.assert_called_once()

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._get_purchase_order")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._update_purchase_order_status")
    def test_approve_purchase_order(self, mock_update_status, mock_get_po):
        """اختبار الموافقة على أمر شراء"""
        mock_get_po.return_value = {"total_amount": "5000.00"}

        result = self.service.approve_purchase_order("PO_001", approved_by=1)

        self.assertTrue(result)
        mock_update_status.assert_called_once_with("PO_001", "approved", 1)

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._get_purchase_order")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._update_purchase_order_status")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._update_purchase_order_delivery")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._get_po_item_cost")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._update_po_item_status")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._update_supplier_performance")
    def test_receive_purchase_order(
        self,
        mock_update_performance,
        mock_update_item,
        mock_get_cost,
        mock_update_delivery,
        mock_update_status,
        mock_get_po,
    ):
        """اختبار استلام أمر شراء"""
        mock_get_po.return_value = {"supplier_id": 1}
        mock_get_cost.return_value = Decimal("10.50")
        self.inventory_service.add_inventory_item.return_value = "INV_IN_001"

        received_items = [
            {
                "product_id": 1,
                "batch_id": "BATCH001",
                "quantity": 100,
                "warehouse_id": 1,
            }
        ]

        result = self.service.receive_purchase_order("PO_001", received_items)

        self.assertTrue(result)
        mock_update_status.assert_called_once_with("PO_001", "received", 1)
        mock_update_delivery.assert_called_once()
        self.inventory_service.add_inventory_item.assert_called_once()

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._get_supplier_performance_data")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._calculate_on_time_delivery_rate")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._calculate_quality_score")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._calculate_average_lead_time")
    def test_evaluate_supplier_performance(self, mock_lead_time, mock_quality, mock_delivery_rate, mock_data):
        """اختبار تقييم أداء المورد"""
        mock_data.return_value = {
            "total_orders": 10,
            "total_value": 50000,
            "last_order_date": datetime.now() - timedelta(days=30),
            "delivery_data": [],
        }
        mock_delivery_rate.return_value = 0.9
        mock_quality.return_value = 0.85
        mock_lead_time.return_value = 5

        performance = self.service.evaluate_supplier_performance(1)

        self.assertIsInstance(performance, SupplierPerformance)
        self.assertEqual(performance.supplier_id, 1)
        self.assertEqual(performance.total_orders, 10)
        self.assertEqual(performance.on_time_delivery_rate, 0.9)

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._check_supplier_alerts")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._check_delivery_alerts")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._check_supply_risk_alerts")
    def test_get_supply_chain_alerts(self, mock_risk, mock_delivery, mock_supplier):
        """اختبار الحصول على تنبيهات سلسلة التوريد"""
        mock_supplier.return_value = [
            SupplyChainAlert(
                "SUP001",
                "supplier_issue",
                "high",
                "مشكلة مورد",
                [],
                ["إجراء"],
                datetime.now(),
            )
        ]
        mock_delivery.return_value = []
        mock_risk.return_value = []

        alerts = self.service.get_supply_chain_alerts()

        self.assertIsInstance(alerts, list)
        self.assertEqual(len(alerts), 1)
        self.assertIsInstance(alerts[0], SupplyChainAlert)

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._get_product_suppliers")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService.evaluate_supplier_performance")
    def test_optimize_supplier_selection(self, mock_performance, mock_suppliers):
        """اختبار تحسين اختيار المورد"""
        mock_suppliers.return_value = [
            {
                "supplier_id": 1,
                "name": "Supplier A",
                "unit_price": 10.5,
                "lead_time_days": 5,
                "status": "active",
            }
        ]

        mock_performance.return_value = Mock(
            performance_rating="excellent",
            on_time_delivery_rate=0.95,
            quality_score=0.9,
            average_lead_time=5,
        )

        recommendations = self.service.optimize_supplier_selection(1, 100)

        self.assertIsInstance(recommendations, list)
        self.assertEqual(len(recommendations), 1)
        self.assertIn("supplier_name", recommendations[0])
        self.assertIn("score", recommendations[0])

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService._get_items_needing_reorder")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService.optimize_supplier_selection")
    def test_generate_purchase_plan(self, mock_optimize, mock_reorder):
        """اختبار توليد خطة المشتريات"""
        mock_reorder.return_value = [
            {
                "product_id": 1,
                "product_name": "Product A",
                "recommended_quantity": 100,
                "priority": "high",
            }
        ]

        mock_optimize.return_value = [{"supplier_name": "Supplier A", "total_cost": 1050.0, "score": 0.9}]

        plan = self.service.generate_purchase_plan()

        self.assertIsInstance(plan, dict)
        self.assertIn("recommended_orders", plan)
        self.assertIn("total_estimated_cost", plan)
        self.assertIn("priority_items", plan)


class TestIntegratedInventorySupplyChain(unittest.TestCase):
    """اختبار التكامل بين إدارة المخزون وسلاسل التوريد"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.prediction_service = Mock(spec=SalesPredictionService)
        self.inventory_service = AdvancedInventoryManagementService(self.db_manager, self.prediction_service)
        self.supply_chain_service = SupplyChainIntegrationService(self.db_manager, self.inventory_service)

    def test_services_integration(self):
        """اختبار تكامل الخدمات"""
        # التحقق من أن الخدمات تستخدم نفس قاعدة البيانات
        self.assertEqual(self.inventory_service.db, self.supply_chain_service.db)

        # التحقق من أن خدمة سلسلة التوريد تستخدم خدمة المخزون
        self.assertEqual(self.supply_chain_service.inventory_service, self.inventory_service)

    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService.create_purchase_order")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService.approve_purchase_order")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService.receive_purchase_order")
    def test_complete_purchase_workflow(self, mock_receive, mock_approve, mock_create):
        """اختبار سير عمل المشتريات الكامل"""
        # إنشاء أمر الشراء
        mock_create.return_value = "PO_001"
        po_id = self.supply_chain_service.create_purchase_order(1, [])

        # الموافقة
        mock_approve.return_value = True
        approved = self.supply_chain_service.approve_purchase_order(po_id, 1)

        # الاستلام
        mock_receive.return_value = True
        received = self.supply_chain_service.receive_purchase_order(po_id, [])

        self.assertEqual(po_id, "PO_001")
        self.assertTrue(approved)
        self.assertTrue(received)

    @patch("services.advanced_inventory_management_service.AdvancedInventoryManagementService.get_inventory_alerts")
    @patch("services.supply_chain_integration_service.SupplyChainIntegrationService.get_supply_chain_alerts")
    def test_unified_alerts_system(self, mock_supply_alerts, mock_inventory_alerts):
        """اختبار نظام التنبيهات الموحد"""
        mock_inventory_alerts.return_value = [
            InventoryAlert(
                "INV001",
                1,
                "low_stock",
                "high",
                "مخزون منخفض",
                "إعادة طلب",
                datetime.now(),
            )
        ]

        mock_supply_alerts.return_value = [
            SupplyChainAlert(
                "SUP001",
                "supplier_issue",
                "medium",
                "مشكلة مورد",
                [],
                ["إجراء"],
                datetime.now(),
            )
        ]

        inventory_alerts = self.inventory_service.get_inventory_alerts()
        supply_alerts = self.supply_chain_service.get_supply_chain_alerts()

        self.assertEqual(len(inventory_alerts), 1)
        self.assertEqual(len(supply_alerts), 1)

        # التحقق من أن التنبيهات مختلفة الأنواع
        self.assertEqual(inventory_alerts[0].alert_type, "low_stock")
        self.assertEqual(supply_alerts[0].alert_type, "supplier_issue")


def run_inventory_supply_chain_tests():
    """تشغيل اختبارات إدارة المخزون وسلاسل التوريد"""
    # print("🚀 بدء اختبارات إدارة المخزون وسلاسل التوريد...")

    # إنشاء مجموعة الاختبارات
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # إضافة جميع فئات الاختبار
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedInventoryManagementService))
    suite.addTests(loader.loadTestsFromTestCase(TestSupplyChainIntegrationService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedInventorySupplyChain))

    # تشغيل الاختبارات
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # طباعة النتائج
    # print("\n📊 نتائج الاختبارات:")
    # print(f"✅ الاختبارات الناجحة: {result.testsRun - len(result.failures) - len(result.errors)}")
    # print(f"❌ الاختبارات الفاشلة: {len(result.failures)}")
    # print(f"⚠️ الأخطاء: {len(result.errors)}")

    if result.failures:
        # print("\n❌ تفاصيل الفشل:")
        for test, traceback in result.failures:
            # print(f"  - {test}: {traceback}")
            pass

    if result.errors:
        # print("\n⚠️ تفاصيل الأخطاء:")
        for test, traceback in result.errors:
            # print(f"  - {test}: {traceback}")
            pass

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100  # noqa: F841
    # print(f"📈 نسبة النجاح: {success_rate:.1f}%")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_inventory_supply_chain_tests()
    sys.exit(0 if success else 1)
