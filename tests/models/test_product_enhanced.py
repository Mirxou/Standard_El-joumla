#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج المنتج المحسّن - Enhanced Product Model Tests
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from src.models.product_enhanced import (
    ProductType, PricingPolicy, UnitType,
    ProductVariant, BundleProduct, PricingTier, ProductLabel, Product
)


class TestEnums(unittest.TestCase):
    def test_product_type_values(self):
        self.assertEqual(ProductType.SIMPLE.value, "بسيط")
        self.assertEqual(ProductType.VARIABLE.value, "متغير")
        self.assertEqual(ProductType.BUNDLE.value, "حزمة")
        self.assertEqual(ProductType.DIGITAL.value, "رقمي")

    def test_pricing_policy_values(self):
        self.assertEqual(PricingPolicy.STANDARD.value, "معياري")
        self.assertEqual(PricingPolicy.TIERED.value, "متدرج")
        self.assertEqual(PricingPolicy.CUSTOMER_BASED.value, "عملاء")
        self.assertEqual(PricingPolicy.TIME_BASED.value, "فترات")

    def test_unit_type_values(self):
        self.assertEqual(UnitType.PIECE.value, "قطعة")
        self.assertEqual(UnitType.KG.value, "كيلوجرام")
        self.assertEqual(UnitType.LITER.value, "لتر")
        self.assertEqual(UnitType.METER.value, "متر")
        self.assertEqual(UnitType.BOX.value, "صندوق")
        self.assertEqual(UnitType.DOZEN.value, "دستة")
        self.assertEqual(UnitType.GRAM.value, "جرام")
        self.assertEqual(UnitType.MILLILITER.value, "ميلليتر")


class TestProductVariant(unittest.TestCase):
    def test_post_init_decimal_conversion(self):
        v = ProductVariant(cost_price="10.50", selling_price=20)
        self.assertEqual(v.cost_price, Decimal('10.50'))
        self.assertEqual(v.selling_price, Decimal('20'))

    def test_profit_margin(self):
        v = ProductVariant(cost_price=Decimal('50'), selling_price=Decimal('75'))
        self.assertEqual(v.profit_margin, Decimal('50'))  # (75-50)/50*100 = 50%

    def test_profit_margin_zero_cost(self):
        v = ProductVariant(cost_price=Decimal('0'), selling_price=Decimal('75'))
        self.assertEqual(v.profit_margin, Decimal('0.00'))

    def test_attributes_display(self):
        v = ProductVariant(attributes={"اللون": "أحمر", "الحجم": "M"})
        text = v._attributes_display()
        self.assertIn("اللون: أحمر", text)
        self.assertIn("الحجم: M", text)

    def test_to_dict(self):
        now = datetime.now()
        v = ProductVariant(
            id=1, product_id=2, sku="SKU-1",
            attributes={"المادة": "قطن"},
            cost_price=Decimal('12.5'), selling_price=Decimal('15.0'),
            stock_quantity=5, barcode="111", image_path="/img.png",
            is_active=True, created_at=now, updated_at=now
        )
        d = v.to_dict()
        self.assertEqual(d['id'], 1)
        self.assertEqual(d['product_id'], 2)
        self.assertEqual(d['sku'], "SKU-1")
        self.assertEqual(d['cost_price'], 12.5)
        self.assertIn('profit_margin', d)


class TestBundleProduct(unittest.TestCase):
    def test_total_price_and_to_dict(self):
        b = BundleProduct(id=1, bundle_id=2, product_id=3, product_name="X", quantity=4, unit_price="2.5")
        self.assertEqual(b.unit_price, Decimal('2.5'))
        self.assertEqual(b.total_price, Decimal('10.0'))
        d = b.to_dict()
        self.assertEqual(d['total_price'], 10.0)


class TestPricingTier(unittest.TestCase):
    def test_is_valid_quantity_and_time(self):
        now = datetime.now()
        tier = PricingTier(min_quantity=10, max_quantity=20, price=Decimal('90'), discount_percent=0, valid_from=now - timedelta(days=1), valid_until=now + timedelta(days=1))
        self.assertTrue(tier.is_valid(10))
        self.assertTrue(tier.is_valid(15))
        self.assertTrue(tier.is_valid(20))
        self.assertFalse(tier.is_valid(9))
        self.assertFalse(tier.is_valid(21))

    def test_is_valid_time_window(self):
        now = datetime.now()
        future_tier = PricingTier(min_quantity=1, price=Decimal('5'), valid_from=now + timedelta(days=1))
        past_tier = PricingTier(min_quantity=1, price=Decimal('5'), valid_until=now - timedelta(days=1))
        self.assertFalse(future_tier.is_valid(5))
        self.assertFalse(past_tier.is_valid(5))

    def test_to_dict(self):
        t = PricingTier(id=1, product_id=2, min_quantity=3, max_quantity=4, price=Decimal('10'), discount_percent=Decimal('5'))
        d = t.to_dict()
        self.assertEqual(d['min_quantity'], 3)
        self.assertEqual(d['discount_percent'], 5.0)


class TestProductLabel(unittest.TestCase):
    def test_is_current_basic(self):
        lbl = ProductLabel(is_active=True)
        self.assertTrue(lbl.is_current())

    def test_is_current_with_dates(self):
        lbl = ProductLabel(is_active=True, start_date=datetime.now() - timedelta(days=1), end_date=datetime.now() + timedelta(days=1))
        self.assertTrue(lbl.is_current())
        lbl2 = ProductLabel(is_active=True, start_date=datetime.now() + timedelta(days=1))
        self.assertFalse(lbl2.is_current())
        lbl3 = ProductLabel(is_active=True, end_date=datetime.now() - timedelta(days=1))
        self.assertFalse(lbl3.is_current())

    def test_label_to_dict(self):
        now = datetime.now()
        lbl = ProductLabel(id=1, product_id=2, label_type="جديد", label_text="وصل حديثاً", label_color="#fff000", priority=3, start_date=now, end_date=now, is_active=True)
        d = lbl.to_dict()
        self.assertEqual(d['label_text'], "وصل حديثاً")
        self.assertEqual(d['priority'], 3)


class TestProductCoreProps(unittest.TestCase):
    def test_post_init_decimal_conversion(self):
        p = Product(cost_price="10.5", base_price=20, average_rating="4.5")
        self.assertEqual(p.cost_price, Decimal('10.5'))
        self.assertEqual(p.base_price, Decimal('20'))
        self.assertEqual(p.average_rating, Decimal('4.5'))

    def test_available_stock_and_aliases(self):
        p = Product(current_stock=100, reserved_stock=30)
        self.assertEqual(p.available_stock, 70)
        self.assertEqual(p.stock_quantity, 100)

    def test_selling_price_alias(self):
        p = Product(base_price=Decimal('50'))
        self.assertEqual(p.selling_price, Decimal('50'))
        p.selling_price = "75"
        self.assertEqual(p.base_price, Decimal('75'))

    def test_low_stock_and_reorder_flags(self):
        p = Product(current_stock=10, min_stock=10, reserved_stock=0, reorder_point=5)
        self.assertTrue(p.is_low_stock)
        self.assertFalse(p.requires_reorder)
        p2 = Product(current_stock=20, min_stock=10, reserved_stock=10, reorder_point=5)
        self.assertFalse(p2.requires_reorder)
        p2.reorder_point = 10
        self.assertTrue(p2.requires_reorder)

    def test_profit_fields_and_stock_value(self):
        p = Product(cost_price=Decimal('40'), base_price=Decimal('60'), current_stock=10)
        self.assertEqual(p.profit_amount, Decimal('20'))
        self.assertEqual(p.profit_margin, Decimal('50'))
        self.assertEqual(p.stock_value, Decimal('400'))


class TestProductRelationsAndPricing(unittest.TestCase):
    def test_active_labels_filter(self):
        p = Product()
        active = ProductLabel(is_active=True)
        inactive = ProductLabel(is_active=False)
        p.add_label(active)
        p.add_label(inactive)
        self.assertEqual(len(p.active_labels), 1)

    def test_add_variant_and_bundle_item(self):
        p = Product(id=10)
        v = ProductVariant(sku="V1")
        b = BundleProduct(product_id=5, product_name="X", quantity=2, unit_price=Decimal('3'))
        p.add_variant(v)
        p.add_bundle_item(b)
        self.assertEqual(v.product_id, 10)
        self.assertEqual(b.bundle_id, 10)
        self.assertEqual(len(p.variants), 1)
        self.assertEqual(len(p.bundle_items), 1)

    def test_get_price_for_quantity_standard(self):
        p = Product(base_price=Decimal('100'), pricing_policy=PricingPolicy.STANDARD.value)
        self.assertEqual(p.get_price_for_quantity(1), Decimal('100'))

    def test_get_price_for_quantity_tiered(self):
        p = Product(base_price=Decimal('100'), pricing_policy=PricingPolicy.TIERED.value)
        # tier with discount percent
        t1 = PricingTier(min_quantity=10, price=Decimal('90'), discount_percent=Decimal('10'))
        # tier with absolute price
        t2 = PricingTier(min_quantity=5, price=Decimal('80'), discount_percent=Decimal('0'))
        p.pricing_tiers = [t1, t2]
        price_12 = p.get_price_for_quantity(12)
        price_6 = p.get_price_for_quantity(6)
        self.assertEqual(price_12, Decimal('90'))  # 100 * (1 - 10%) = 90
        self.assertEqual(price_6, Decimal('80'))

    def test_to_dict_include_related(self):
        now = datetime.now()
        p = Product(
            id=1, name="منتج", sku="SKU", category_id=2, supplier_id=3,
            product_type=ProductType.SIMPLE.value, unit=UnitType.PIECE.value,
            cost_price=Decimal('10'), base_price=Decimal('15'), current_stock=5,
            reserved_stock=1, min_stock=1, reorder_point=2, max_stock=10,
            images=["/a.png"], tags=["جديد"], created_at=now, updated_at=now,
        )
        p.add_variant(ProductVariant(sku="V1", cost_price=5, selling_price=7))
        p.add_bundle_item(BundleProduct(product_id=3, product_name="X", quantity=2, unit_price=3))
        p.pricing_tiers = [PricingTier(min_quantity=1, price=Decimal('14'), discount_percent=0)]
        p.add_label(ProductLabel(label_type="جديد", label_text="NEW"))

        d = p.to_dict(include_related=True)
        self.assertEqual(d['id'], 1)
        self.assertIn('variants', d)
        self.assertIn('bundle_items', d)
        self.assertIn('pricing_tiers', d)
        self.assertIn('labels', d)
        self.assertIn('active_labels', d)

    def test_to_dict_exclude_related(self):
        p = Product(id=1, name="منتج")
        d = p.to_dict(include_related=False)
        self.assertEqual(d['id'], 1)
        self.assertNotIn('variants', d)
        self.assertIn('active_labels', d)


if __name__ == '__main__':
    unittest.main()



