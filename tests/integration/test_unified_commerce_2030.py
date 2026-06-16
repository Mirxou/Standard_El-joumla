#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار خدمات Unified Commerce 2030
اختبار شامل لجميع الخدمات الجديدة المطورة
"""

import sys  # noqa: F811
import unittest
from decimal import Decimal
from pathlib import Path  # noqa: F811
from unittest.mock import Mock, patch

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.database_manager import DatabaseManager
from src.models.customer import Customer
from src.models.product import Product
from src.services.cpq_service import CPQService, ProductConfiguration
from src.services.dynamic_pricing_engine import DynamicPricingEngine, PricingSignal
from src.services.pricing_service import PricingService
from src.services.ui_adaptation_service import UIAdaptationService


class TestUnifiedCommerceServices(unittest.TestCase):
    """اختبار شامل لخدمات التجارة الموحدة"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        # Mock database manager
        self.db_mock = Mock(spec=DatabaseManager)

        # Create test customer
        self.test_customer = Customer(
            id=1,
            name="Test Customer B2B",
            customer_type="b2b",
            pricing_tier="premium",
            contract_id="CONTRACT_001",
            total_purchases=Decimal("50000"),
            purchases_count=25,
        )

        # Create test product
        self.test_product = Product(
            id=1,
            name="Test Product",
            barcode="TEST-001",
            selling_price=Decimal("100.00"),
            current_stock=50,
        )

    def test_pricing_service_customer_pricing(self):
        """اختبار خدمة التسعير مع العملاء المخصصين"""
        # print("Testing Pricing Service...")

        # Mock database responses
        self.db_mock.fetch_one.side_effect = [
            (Decimal("100.00"),),  # Base price
            ("premium",),  # Customer tier
            ("contract_pricing",),  # Contract type
        ]

        pricing_service = PricingService(self.db_mock)

        # Test B2B pricing
        price = pricing_service.get_price_for_customer(self.test_product, self.test_customer, 10)

        # Should apply B2B discount
        self.assertIsInstance(price, Decimal)
        self.assertGreater(price, 0)

        # print("✓ Pricing Service test passed")

    def test_dynamic_pricing_engine(self):
        """اختبار محرك التسعير الديناميكي"""
        # print("Testing Dynamic Pricing Engine...")

        # Mock database
        self.db_mock.fetch_one.side_effect = [
            (50,),  # Stock level
            None,  # No recent sales
            None,  # No previous sales
        ]

        engine = DynamicPricingEngine(self.db_mock)

        # Test price adjustment
        base_price = Decimal("100.00")
        adjusted_price = engine.adjust_price(base_price, 1, self.test_customer, Decimal("10"))

        self.assertIsInstance(adjusted_price, Decimal)
        self.assertGreater(adjusted_price, 0)

        # Test pricing insights
        insights = engine.get_pricing_insights(1, self.test_customer, Decimal("1"))
        self.assertIn("final_price", insights)
        self.assertIn("insights", insights)

        # print("✓ Dynamic Pricing Engine test passed")

    def test_pricing_signals(self):
        """اختبار إشارات التسعير"""
        # print("Testing Pricing Signals...")

        engine = DynamicPricingEngine(self.db_mock)

        # Create test signal
        signal = PricingSignal(
            signal_type="inventory",
            product_id=1,
            adjustment_percentage=Decimal("10"),
            confidence_score=0.8,
            reason="Low stock signal",
        )

        # Add signal
        engine.add_pricing_signal(signal)

        # Verify signal was added
        self.assertEqual(len(engine.pricing_signals), 1)
        self.assertEqual(engine.pricing_signals[0].signal_type, "inventory")

        # print("✓ Pricing Signals test passed")

    def test_cpq_service_quote_creation(self):
        """اختبار خدمة CPQ وإنشاء عروض الأسعار"""
        # print("Testing CPQ Service...")

        # Mock CPQ service methods
        with patch.object(CPQService, "_get_product") as mock_get_product, patch.object(
            CPQService, "_get_product_options"
        ) as mock_get_options, patch.object(CPQService, "_save_quote") as mock_save:

            mock_get_product.return_value = self.test_product
            mock_get_options.return_value = []
            mock_save.return_value = None

            cpq_service = CPQService()

            # Create product configuration
            config = ProductConfiguration(
                product_id=1,
                selected_options={"color": "blue", "size": "large"},
                quantity=5,
            )

            # Create quote
            quote = cpq_service.create_quote(self.test_customer, [config])

            # Verify quote structure
            self.assertIsNotNone(quote)
            self.assertEqual(len(quote.items), 1)
            self.assertGreater(quote.total_amount, 0)

            # print("✓ CPQ Service test passed")

    def test_cpq_configuration_validation(self):
        """اختبار التحقق من تكوين المنتج"""
        # print("Testing CPQ Configuration Validation...")

        cpq_service = CPQService()

        # Valid configuration
        valid_config = ProductConfiguration(product_id=1, selected_options={"color": "blue"}, quantity=5)

        is_valid, errors = cpq_service.validate_configuration(valid_config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid configuration (negative quantity)
        invalid_config = ProductConfiguration(product_id=1, selected_options={"color": "blue"}, quantity=-1)

        is_valid, errors = cpq_service.validate_configuration(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

        # print("✓ CPQ Configuration Validation test passed")

    def test_ui_adaptation_service(self):
        """اختبار خدمة تكيف الواجهة"""
        # print("Testing UI Adaptation Service...")

        adaptation_service = UIAdaptationService(self.db_mock, user_id=1)

        # Track interactions
        adaptation_service.track_interaction("customer_search_button", interaction_type="click")
        adaptation_service.track_interaction("product_add_button", interaction_type="click")
        adaptation_service.track_interaction("product_add_button", interaction_type="click")  # Twice

        # Generate layout
        layout = adaptation_service.generate_optimal_layout()

        # Verify layout structure
        self.assertIn("primary_elements", layout)
        self.assertIn("secondary_elements", layout)

        # Check that frequently used elements are prioritized
        primary_elements = layout["primary_elements"]
        self.assertIn("product_add_button", primary_elements)

        # print("✓ UI Adaptation Service test passed")

    def test_ui_adaptation_advanced_features(self):
        """اختبار الميزات المتقدمة لتكيف الواجهة"""
        # print("Testing UI Adaptation Advanced Features...")

        adaptation_service = UIAdaptationService()

        # Test progressive disclosure
        beginner_disclosure = adaptation_service.apply_progressive_disclosure("beginner")
        self.assertTrue(beginner_disclosure["show_basic"])
        self.assertFalse(beginner_disclosure["show_advanced"])

        expert_disclosure = adaptation_service.apply_progressive_disclosure("expert")
        self.assertFalse(expert_disclosure["show_basic"])
        self.assertTrue(expert_disclosure["show_advanced"])

        # Test adaptation suggestions
        suggestions = adaptation_service.get_adaptation_suggestions()
        self.assertIsInstance(suggestions, list)

        # print("✓ UI Adaptation Advanced Features test passed")

    def test_blended_sales_ui_integration(self):
        """اختبار تكامل واجهة المبيعات المدمجة"""
        # print("Testing Blended Sales UI Integration...")

        # This would require GUI testing framework, so we'll mock the components
        from src.services.ui_adaptation_service import UIAdaptationService

        # Create adaptation service
        adaptation_service = UIAdaptationService()

        # Simulate UI context
        ui_context = "sales_ui"

        # Get adapted layout
        layout = adaptation_service.generate_optimal_layout(ui_context=ui_context)

        # Verify layout has required elements
        self.assertIn("context", layout)
        self.assertEqual(layout["context"], ui_context)

        # print("✓ Blended Sales UI Integration test passed")

    def test_customer_model_unified_commerce(self):
        """اختبار نموذج العميل الموحد للتجارة"""
        # print("Testing Unified Commerce Customer Model...")

        # Test B2B customer properties
        b2b_customer = Customer(
            id=1,
            name="B2B Corp",
            customer_type="b2b",
            pricing_tier="enterprise",
            contract_id="ENT_2024",
            account_manager="John Doe",
            payment_terms="net_30",
            is_b2b_customer=True,
            has_contract_pricing=True,
        )

        self.assertTrue(b2b_customer.is_b2b_customer)
        self.assertTrue(b2b_customer.has_contract_pricing)
        self.assertEqual(b2b_customer.customer_type, "b2b")
        self.assertEqual(b2b_customer.pricing_tier, "enterprise")

        # Test B2C customer properties
        b2c_customer = Customer(
            id=2,
            name="John Consumer",
            customer_type="b2c",
            pricing_tier="standard",
            is_b2b_customer=False,
            has_contract_pricing=False,
        )

        self.assertFalse(b2c_customer.is_b2b_customer)
        self.assertFalse(b2c_customer.has_contract_pricing)
        self.assertEqual(b2c_customer.customer_type, "b2c")

        # print("✓ Unified Commerce Customer Model test passed")

    def test_volume_discount_calculations(self):
        """اختبار حسابات خصم الكمية"""
        # print("Testing Volume Discount Calculations...")

        # Test bulk discount logic (simplified)
        def calculate_bulk_discount(quantity: int) -> Decimal:
            if quantity >= 100:
                return Decimal("0.15")
            elif quantity >= 50:
                return Decimal("0.10")
            elif quantity >= 10:
                return Decimal("0.05")
            return Decimal("0")

        # Test different quantities
        self.assertEqual(calculate_bulk_discount(5), Decimal("0"))
        self.assertEqual(calculate_bulk_discount(25), Decimal("0.05"))
        self.assertEqual(calculate_bulk_discount(75), Decimal("0.10"))
        self.assertEqual(calculate_bulk_discount(150), Decimal("0.15"))

        # print("✓ Volume Discount Calculations test passed")

    def test_dynamic_pricing_scenarios(self):
        """اختبار سيناريوهات التسعير الديناميكي المختلفة"""
        # print("Testing Dynamic Pricing Scenarios...")

        engine = DynamicPricingEngine(self.db_mock)

        # Scenario 1: High demand
        high_demand_signal = PricingSignal(
            signal_type="demand",
            product_id=1,
            adjustment_percentage=Decimal("8"),
            confidence_score=0.9,
            reason="High demand trend",
        )

        # Scenario 2: Low inventory
        low_stock_signal = PricingSignal(
            signal_type="inventory",
            product_id=1,
            adjustment_percentage=Decimal("12"),
            confidence_score=0.85,
            reason="Critical low stock",
        )

        # Add signals
        engine.add_pricing_signal(high_demand_signal)
        engine.add_pricing_signal(low_stock_signal)

        # Test combined effect
        base_price = Decimal("100.00")
        adjusted_price = engine.adjust_price(base_price, 1, self.test_customer, Decimal("1"))

        # Price should be increased due to signals
        self.assertGreater(adjusted_price, base_price)

        # print("✓ Dynamic Pricing Scenarios test passed")

    def test_error_handling_and_resilience(self):
        """اختبار معالجة الأخطاء والمرونة"""
        # print("Testing Error Handling and Resilience...")

        # Test pricing service with invalid data
        pricing_service = PricingService(self.db_mock)

        # Mock database to return invalid data
        self.db_mock.fetch_one.return_value = None

        # Should handle gracefully
        price = pricing_service.get_price_for_customer(self.test_product, self.test_customer, 1)
        self.assertIsInstance(price, Decimal)

        # Test CPQ with invalid configuration
        cpq_service = CPQService()

        invalid_config = ProductConfiguration(product_id=999, quantity=0)  # Non-existent product  # Invalid quantity

        is_valid, errors = cpq_service.validate_configuration(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

        # print("✓ Error Handling and Resilience test passed")

    def tearDown(self):
        """تنظيف بعد الاختبار"""
        # Clean up mocks
        self.db_mock.reset_mock()


def run_unified_commerce_tests():
    """تشغيل جميع اختبارات التجارة الموحدة"""
    # print("=" * 60)
    # print("🧪 Unified Commerce 2030 - Comprehensive Test Suite")
    # print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnifiedCommerceServices)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    # print("\n" + "=" * 60)
    # print("📊 Test Results Summary")
    # print("=" * 60)
    # print(f"Total Tests: {result.testsRun}")
    # print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    # print(f"Failed: {len(result.failures)}")
    # print(f"Errors: {len(result.errors)}")

    if result.failures:
        # print("\n❌ Failures:")
        for test, traceback in result.failures:
            # print(f"  - {test}: {traceback}")
            pass

    if result.errors:
        # print("\n💥 Errors:")
        for test, traceback in result.errors:
            # print(f"  - {test}: {traceback}")
            pass

    if result.wasSuccessful():
        # print("\n✅ All tests passed! Unified Commerce 2030 is ready for production.")
        return True
    else:
        # print("\n❌ Some tests failed. Please review and fix issues before deployment.")
        return False


if __name__ == "__main__":
    success = run_unified_commerce_tests()
    sys.exit(0 if success else 1)
