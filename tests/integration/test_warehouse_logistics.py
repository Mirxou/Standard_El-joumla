#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار خدمات إدارة المخازن المتعددة وتكامل اللوجستيات - Phase 6 Tests
اختبار شامل لخدمات إدارة المخازن وتكامل اللوجستيات
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager
from src.services.multi_warehouse_management_service import MultiWarehouseManagementService, Warehouse, WarehouseTransfer
from src.services.logistics_integration_service import LogisticsIntegrationService, Shipment, Carrier
from src.services.advanced_inventory_management_service import AdvancedInventoryManagementService
from src.services.sales_prediction_service import SalesPredictionService

class TestMultiWarehouseManagementService(unittest.TestCase):
    """اختبار خدمة إدارة المخازن المتعددة"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.inventory_service = Mock(spec=AdvancedInventoryManagementService)
        self.service = MultiWarehouseManagementService(self.db_manager, self.inventory_service)

    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertIsInstance(self.service, MultiWarehouseManagementService)
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.inventory_service)

    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._insert_warehouse')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._create_default_zones')
    def test_create_warehouse(self, mock_zones, mock_insert):
        """اختبار إنشاء مخزن"""
        warehouse = Warehouse(
            warehouse_id="",
            name="مخزن الرياض",
            location="الرياض",
            type="central",
            capacity=1000,
            current_utilization=50.0,
            status="active"
        )

        warehouse_id = self.service.create_warehouse(warehouse)

        self.assertTrue(warehouse_id.startswith("WH_"))
        mock_insert.assert_called_once()
        mock_zones.assert_called_once()

    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._insert_transfer')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_transfer')
    def test_create_transfer_request(self, mock_get, mock_insert):
        """اختبار إنشاء طلب نقل"""
        mock_get.return_value = None

        transfer = WarehouseTransfer(
            transfer_id="",
            from_warehouse_id="WH001",
            to_warehouse_id="WH002",
            items=[{'product_id': 1, 'quantity': 100, 'unit_price': Decimal('10.50')}],
            status="draft",
            transfer_type="replenishment",
            priority="high"
        )

        transfer_id = self.service.create_transfer_request(transfer)

        self.assertTrue(transfer_id.startswith("WT_"))
        mock_insert.assert_called_once()

    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_transfer')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_warehouse_stock')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._update_transfer_status')
    def test_approve_transfer(self, mock_update, mock_stock, mock_get):
        """اختبار الموافقة على طلب النقل"""
        mock_get.return_value = {
            'status': 'draft',
            'from_warehouse_id': 'WH001',
            'to_warehouse_id': 'WH002',
            'items': '[{"product_id": 1, "quantity": "100"}]'
        }
        mock_stock.return_value = 200  # مخزون كافٍ

        result = self.service.approve_transfer("WT001", 1)

        self.assertTrue(result)
        mock_update.assert_called_once_with("WT001", 'approved', 1)

    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_transfer')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._update_transfer_status')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._update_transfer_delivery')
    def test_execute_transfer(self, mock_delivery, mock_status, mock_get):
        """اختبار تنفيذ النقل"""
        mock_get.return_value = {
            'status': 'approved',
            'from_warehouse_id': 'WH001',
            'to_warehouse_id': 'WH002',
            'items': '[{"product_id": 1, "quantity": "100", "unit_price": "10.50"}]'
        }

        result = self.service.execute_transfer("WT001", 1)

        self.assertTrue(result)
        mock_status.assert_any_call("WT001", 'in_transit', 1)
        mock_status.assert_any_call("WT001", 'received', 1)
        mock_delivery.assert_called_once()

    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_total_product_stock')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_current_distribution')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._calculate_optimal_distribution')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._check_redistribution_needed')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._generate_distribution_recommendations')
    def test_get_inventory_distribution(self, mock_recommendations, mock_needed, mock_optimal, mock_current, mock_total):
        """اختبار الحصول على توزيع المخزون"""
        mock_total.return_value = 1000
        mock_current.return_value = {'WH001': 600, 'WH002': 400}
        mock_optimal.return_value = {'WH001': 500, 'WH002': 500}
        mock_needed.return_value = True
        mock_recommendations.return_value = ['نقل 100 وحدة من WH001 إلى WH002']

        distribution = self.service.get_inventory_distribution(1)

        self.assertIsNotNone(distribution)
        self.assertEqual(distribution.product_id, 1)
        self.assertEqual(distribution.total_stock, 1000)
        self.assertTrue(distribution.redistribution_needed)

    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_active_warehouses')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._calculate_warehouse_metrics')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._calculate_transfer_statistics')
    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService._get_warehouse_alerts')
    def test_get_warehouse_performance_report(self, mock_alerts, mock_stats, mock_metrics, mock_warehouses):
        """اختبار الحصول على تقرير أداء المخزن"""
        mock_metrics.return_value = {'utilization': 75.0}
        mock_stats.return_value = {'total_transfers': 50}
        mock_alerts.return_value = []

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = self.service.get_warehouse_performance_report("WH001", start_date, end_date)

        self.assertIsInstance(report, dict)
        self.assertEqual(report['warehouse_id'], "WH001")
        self.assertIn('metrics', report)
        self.assertIn('transfers', report)
        self.assertIn('alerts', report)

class TestLogisticsIntegrationService(unittest.TestCase):
    """اختبار خدمة تكامل اللوجستيات"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.warehouse_service = Mock(spec=MultiWarehouseManagementService)
        self.service = LogisticsIntegrationService(self.db_manager, self.warehouse_service)

    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertIsInstance(self.service, LogisticsIntegrationService)
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.warehouse_service)

    @patch('services.logistics_integration_service.LogisticsIntegrationService._insert_carrier')
    def test_register_carrier(self, mock_insert):
        """اختبار تسجيل شركة شحن"""
        carrier = Carrier(
            carrier_id="",
            name="شركة الشحن السريع",
            carrier_type="local",
            services=["express", "standard"]
        )

        carrier_id = self.service.register_carrier(carrier)

        self.assertTrue(carrier_id.startswith("CAR_"))
        mock_insert.assert_called_once()

    @patch('services.logistics_integration_service.LogisticsIntegrationService._insert_shipment')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._create_tracking_event')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._calculate_shipping_cost')
    def test_create_shipment(self, mock_cost, mock_tracking, mock_insert):
        """اختبار إنشاء شحنة"""
        mock_cost.return_value = Decimal('150.00')

        shipment = Shipment(
            shipment_id="",
            transfer_id=None,
            carrier_id="CAR001",
            tracking_number="TRACK123",
            status="pending",
            shipment_type="warehouse_transfer",
            origin_address={"city": "الرياض"},
            destination_address={"city": "جدة"},
            items=[{'product_id': 1, 'quantity': 50, 'weight_kg': 25.0}],
            weight_kg=25.0
        )

        shipment_id = self.service.create_shipment(shipment)

        self.assertTrue(shipment_id.startswith("SHIP_"))
        mock_insert.assert_called_once()
        mock_tracking.assert_called_once()

    @patch('services.logistics_integration_service.LogisticsIntegrationService._get_shipment')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._update_shipment_status_db')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._create_tracking_event')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._check_shipment_alerts')
    def test_update_shipment_status(self, mock_alerts, mock_tracking, mock_update, mock_get):
        """اختبار تحديث حالة الشحنة"""
        mock_get.return_value = {'status': 'in_transit'}

        result = self.service.update_shipment_status("SHIP001", "delivered", "تم التسليم بنجاح", 1)

        self.assertTrue(result)
        mock_update.assert_called_once()
        mock_tracking.assert_called_once()
        mock_alerts.assert_called_once()

    @patch('services.logistics_integration_service.LogisticsIntegrationService._get_available_routes')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._create_default_route')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._calculate_route_cost')
    def test_calculate_optimal_route(self, mock_cost, mock_default, mock_routes):
        """اختبار حساب المسار الأمثل"""
        mock_routes.return_value = []
        mock_default.return_value = {
            'route_id': 'ROUTE001',
            'distance_km': 100.0,
            'estimated_duration_hours': 5.0,
            'preferred_carriers': ['CAR001']
        }
        mock_cost.return_value = 50.0

        route = self.service.calculate_optimal_route("WH001", "WH002", 10.0, 2.0)

        self.assertIsNotNone(route)
        self.assertIn('route', route)
        self.assertIn('carrier_id', route)
        self.assertIn('estimated_cost', route)

    @patch('services.logistics_integration_service.LogisticsIntegrationService._calculate_carrier_metrics')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._calculate_delivery_performance')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._get_carrier_issues')
    def test_get_carrier_performance_report(self, mock_issues, mock_performance, mock_metrics):
        """اختبار الحصول على تقرير أداء شركة الشحن"""
        mock_metrics.return_value = {'total_shipments': 100}
        mock_performance.return_value = {'average_delivery_time': 2.5}
        mock_issues.return_value = []

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = self.service.get_carrier_performance_report("CAR001", start_date, end_date)

        self.assertIsInstance(report, dict)
        self.assertEqual(report['carrier_id'], "CAR001")
        self.assertIn('metrics', report)
        self.assertIn('performance', report)
        self.assertIn('issues', report)

    @patch('services.logistics_integration_service.LogisticsIntegrationService._check_delivery_delays')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._check_cost_overruns')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._check_lost_shipments')
    def test_get_logistics_alerts(self, mock_lost, mock_cost, mock_delays):
        """اختبار الحصول على تنبيهات اللوجستيات"""
        from src.services.logistics_integration_service import LogisticsAlert

        mock_delays.return_value = [
            LogisticsAlert(
                alert_id="DELAY001",
                alert_type="delay",
                severity="high",
                shipment_id="SHIP001",
                message="تأخير في الشحنة",
                created_at=datetime.now()
            )
        ]
        mock_cost.return_value = []
        mock_lost.return_value = []

        alerts = self.service.get_logistics_alerts()

        self.assertIsInstance(alerts, list)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, "delay")

    @patch('services.logistics_integration_service.LogisticsIntegrationService._analyze_current_shipping_costs')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._calculate_potential_savings')
    @patch('services.logistics_integration_service.LogisticsIntegrationService._generate_cost_optimization_recommendations')
    def test_optimize_shipping_costs(self, mock_recommendations, mock_savings, mock_costs):
        """اختبار تحسين تكاليف الشحن"""
        mock_costs.return_value = {'total_cost_last_month': 10000.0}
        mock_savings.return_value = {'route_optimization': 1200.0}
        mock_recommendations.return_value = ['دمج الشحنات الصغيرة']

        optimization = self.service.optimize_shipping_costs()

        self.assertIsInstance(optimization, dict)
        self.assertIn('current_costs', optimization)
        self.assertIn('potential_savings', optimization)
        self.assertIn('recommendations', optimization)

class TestIntegratedWarehouseLogistics(unittest.TestCase):
    """اختبار التكامل بين إدارة المخازن واللوجستيات"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.inventory_service = Mock(spec=AdvancedInventoryManagementService)
        self.warehouse_service = MultiWarehouseManagementService(self.db_manager, self.inventory_service)
        self.logistics_service = LogisticsIntegrationService(self.db_manager, self.warehouse_service)

    def test_services_integration(self):
        """اختبار تكامل الخدمات"""
        # التحقق من أن الخدمات تستخدم نفس قاعدة البيانات
        self.assertEqual(self.warehouse_service.db, self.logistics_service.db)

        # التحقق من أن خدمة اللوجستيات تستخدم خدمة المخازن
        self.assertEqual(self.logistics_service.warehouse_service, self.warehouse_service)

    @patch('services.multi_warehouse_management_service.MultiWarehouseManagementService.create_transfer_request')
    @patch('services.logistics_integration_service.LogisticsIntegrationService.create_shipment')
    def test_transfer_to_shipment_workflow(self, mock_shipment, mock_transfer):
        """اختبار سير العمل من النقل إلى الشحن"""
        mock_transfer.return_value = "WT001"
        mock_shipment.return_value = "SHIP001"

        # إنشاء طلب نقل
        transfer = WarehouseTransfer(
            transfer_id="",
            from_warehouse_id="WH001",
            to_warehouse_id="WH002",
            items=[{'product_id': 1, 'quantity': 100, 'unit_price': Decimal('10.50')}],
            status="draft",
            transfer_type="replenishment",
            priority="high"
        )

        transfer_id = self.warehouse_service.create_transfer_request(transfer)

        # إنشاء شحنة للنقل
        shipment = Shipment(
            shipment_id="",
            transfer_id=transfer_id,
            carrier_id="CAR001",
            tracking_number="TRACK123",
            status="pending",
            shipment_type="warehouse_transfer",
            origin_address={"warehouse": "WH001", "city": "الرياض"},
            destination_address={"warehouse": "WH002", "city": "جدة"},
            items=[{'product_id': 1, 'quantity': 100, 'weight_kg': 50.0}],
            weight_kg=50.0
        )

        shipment_id = self.logistics_service.create_shipment(shipment)

        self.assertEqual(transfer_id, "WT001")
        self.assertEqual(shipment_id, "SHIP001")
        self.assertEqual(shipment.transfer_id, transfer_id)

def run_warehouse_logistics_tests():
    """تشغيل اختبارات إدارة المخازن واللوجستيات"""
    print("🚀 بدء اختبارات إدارة المخازن واللوجستيات...")

    # إنشاء مجموعة الاختبارات
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # إضافة جميع فئات الاختبار
    suite.addTests(loader.loadTestsFromTestCase(TestMultiWarehouseManagementService))
    suite.addTests(loader.loadTestsFromTestCase(TestLogisticsIntegrationService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedWarehouseLogistics))

    # تشغيل الاختبارات
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # طباعة النتائج
    print(f"\n📊 نتائج الاختبارات:")
    print(f"✅ الاختبارات الناجحة: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ الاختبارات الفاشلة: {len(result.failures)}")
    print(f"⚠️ الأخطاء: {len(result.errors)}")

    if result.failures:
        print("\n❌ تفاصيل الفشل:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n⚠️ تفاصيل الأخطاء:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"📈 نسبة النجاح: {success_rate:.1f}%")

    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_warehouse_logistics_tests()
    sys.exit(0 if success else 1)




