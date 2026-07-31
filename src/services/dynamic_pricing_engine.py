import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محرك التسعير الديناميكي المتقدم - Advanced Dynamic Pricing Engine
يعدل الأسعار في الوقت الفعلي بناءً على المخزون والطلب والمنافسة والعوامل الأخرى
"""

import random  # nosec B311
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.models.customer import Customer


@dataclass
class PricingSignal:
    """إشارة تسعير ديناميكي"""

    signal_type: str  # 'inventory', 'demand', 'competition', 'seasonal', 'customer_loyalty'
    product_id: int
    adjustment_percentage: Decimal
    confidence_score: float  # 0.0 to 1.0
    reason: str
    timestamp: datetime = datetime.now()
    expires_at: Optional[datetime] = None


@dataclass
class DynamicPricingRule:
    """قاعدة تسعير ديناميكي"""

    id: int
    name: str
    condition_type: str  # 'inventory_level', 'demand_trend', 'competitor_price', 'time_based'
    condition_operator: str  # '>', '<', '>=', '<=', '==', 'between'
    condition_value: Any
    adjustment_type: str  # 'percentage', 'fixed_amount', 'fixed_price'
    adjustment_value: Decimal
    product_id: Optional[int] = None  # None = applies to all products
    customer_segment: Optional[str] = None  # 'retail', 'wholesale', 'vip'
    max_adjustment_percentage: Optional[Decimal] = None  # Safety limit
    is_active: bool = True
    priority: int = 1  # Higher = more important


class DynamicPricingEngine:
    """محرك التسعير الديناميكي المتقدم"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

        # Dynamic pricing parameters
        self.INVENTORY_LOW_THRESHOLD = 10  # Low stock threshold
        self.DEMAND_HIGH_THRESHOLD = 50  # High demand threshold
        self.MAX_PRICE_INCREASE = Decimal("0.20")  # Max 20% increase
        self.MAX_PRICE_DECREASE = Decimal("0.15")  # Max 15% decrease

        # Advanced parameters
        self.signal_expiry_hours = 24
        self.min_confidence_threshold = 0.3
        self.pricing_signals = []
        self.active_rules = []

        # Load configuration and rules
        self._load_active_rules()

    def adjust_price(
        self,
        current_price: Decimal,
        product_id: int,
        customer: Customer,
        quantity: Decimal,
    ) -> Decimal:
        """
        تعديل السعر ديناميكياً بناءً على عوامل متعددة مع إشارات متقدمة

        Args:
            current_price: السعر الحالي
            product_id: معرف المنتج
            customer: العميل
            quantity: الكمية المطلوبة

        Returns:
            السعر المعدل
        """
        try:
            adjustments = []

            # 1. Inventory-based adjustment
            inventory_adjustment = self._calculate_inventory_adjustment(product_id)
            adjustments.append(inventory_adjustment)

            # 2. Demand-based adjustment
            demand_adjustment = self._calculate_demand_adjustment(product_id)
            adjustments.append(demand_adjustment)

            # 3. Customer loyalty adjustment
            loyalty_adjustment = self._calculate_loyalty_adjustment(customer)
            adjustments.append(loyalty_adjustment)

            # 4. Quantity-based adjustment
            quantity_adjustment = self._calculate_quantity_adjustment(quantity)
            adjustments.append(quantity_adjustment)

            # 5. Time-based adjustment (peak hours, seasons)
            time_adjustment = self._calculate_time_adjustment()
            adjustments.append(time_adjustment)

            # 6. Advanced signals adjustment
            signals_adjustment = self._calculate_signals_adjustment(current_price, product_id, customer, quantity)
            adjustments.append(signals_adjustment)

            # 7. Rules-based adjustment
            rules_adjustment = self._calculate_rules_adjustment(product_id, customer, quantity)
            adjustments.append(rules_adjustment)

            # Calculate total adjustment
            total_adjustment = sum(adjustments)

            # Apply limits
            total_adjustment = max(-self.MAX_PRICE_DECREASE, min(self.MAX_PRICE_INCREASE, total_adjustment))

            # Calculate final price
            adjusted_price = current_price * (Decimal("1.00") + total_adjustment)

            # Ensure price doesn't go below cost (basic protection)
            min_price = self._get_minimum_price(product_id)
            if adjusted_price < min_price:
                adjusted_price = min_price

            # Round to 2 decimal places
            return adjusted_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        except Exception as e:
            self.logger.error(f"خطأ في تعديل السعر ديناميكياً: {str(e)}")
            return current_price

    def _calculate_signals_adjustment(
        self,
        base_price: Decimal,
        product_id: int,
        customer: Customer,
        quantity: Decimal,
    ) -> Decimal:
        """تعديل بناءً على الإشارات الديناميكية المتقدمة"""
        try:
            signals = self._get_applicable_signals(product_id, customer, quantity)

            if not signals:
                return Decimal("0")

            # Calculate weighted adjustment based on confidence
            total_weighted_adjustment = Decimal("0")
            total_confidence = Decimal("0")

            for signal in signals:
                if signal.confidence_score >= self.min_confidence_threshold:
                    adjustment = base_price * (signal.adjustment_percentage / Decimal("100"))
                    weight = Decimal(str(signal.confidence_score))

                    total_weighted_adjustment += adjustment * weight
                    total_confidence += weight

            if total_confidence > 0:
                return (total_weighted_adjustment / total_confidence) / base_price
            else:
                return Decimal("0")

        except Exception as e:
            self.logger.error(f"خطأ في حساب تعديل الإشارات: {str(e)}")
            return Decimal("0")

    def _get_applicable_signals(self, product_id: int, customer: Customer, quantity: Decimal) -> List[PricingSignal]:
        """الحصول على جميع الإشارات المطبقة"""
        signals = []

        # Inventory signals
        signals.extend(self._get_inventory_signals(product_id))

        # Demand signals
        signals.extend(self._get_demand_signals(product_id))

        # Competition signals
        signals.extend(self._get_competition_signals(product_id))

        # Customer signals
        signals.extend(self._get_customer_signals(product_id, customer, quantity))

        # Time-based signals
        signals.extend(self._get_time_signals())

        # Filter expired signals
        current_time = datetime.now()
        valid_signals = [signal for signal in signals if not signal.expires_at or signal.expires_at > current_time]

        return valid_signals

    def _get_inventory_signals(self, product_id: int) -> List[PricingSignal]:
        """إشارات بناءً على المخزون"""
        signals = []

        try:
            stock_info = self.db_manager.fetch_one(
                "SELECT current_stock, min_stock_level FROM products WHERE id = ?",
                (product_id,),
            )

            if stock_info and stock_info[0]:
                current_stock = Decimal(str(stock_info[0]))
                min_stock = Decimal(str(stock_info[1] or 0))

                # Critical low stock
                if current_stock <= min_stock:
                    confidence = 1.0
                    signals.append(
                        PricingSignal(
                            signal_type="inventory",
                            product_id=product_id,
                            adjustment_percentage=Decimal("15"),
                            confidence_score=confidence,
                            reason=f"Critical low stock: {current_stock} units",
                            expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                        )
                    )

                # Low stock warning
                elif current_stock <= min_stock * Decimal("1.5"):
                    confidence = min(
                        1.0,
                        float((min_stock * Decimal("1.5") - current_stock) / (min_stock * Decimal("1.5"))),
                    )
                    signals.append(
                        PricingSignal(
                            signal_type="inventory",
                            product_id=product_id,
                            adjustment_percentage=Decimal("8"),
                            confidence_score=confidence,
                            reason=f"Low stock warning: {current_stock} units",
                            expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                        )
                    )

                # Excess stock
                elif current_stock > min_stock * Decimal("3"):
                    confidence = min(
                        1.0,
                        float((current_stock - min_stock * Decimal("3")) / (min_stock * Decimal("3"))),
                    )
                    signals.append(
                        PricingSignal(
                            signal_type="inventory",
                            product_id=product_id,
                            adjustment_percentage=Decimal("-5"),
                            confidence_score=confidence,
                            reason=f"Excess stock: {current_stock} units",
                            expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                        )
                    )

        except Exception as e:
            self.logger.error(f"خطأ في إشارات المخزون: {str(e)}")

        return signals

    def _get_demand_signals(self, product_id: int) -> List[PricingSignal]:
        """إشارات بناءً على الطلب"""
        signals = []

        try:
            # Compare last 7 days vs previous 7 days
            week_ago = datetime.now() - timedelta(days=7)
            two_weeks_ago = datetime.now() - timedelta(days=14)

            recent_sales = self.db_manager.fetch_one(
                """SELECT SUM(quantity) FROM sale_items si
                   JOIN sales s ON si.sale_id = s.id
                   WHERE si.product_id = ? AND s.created_at >= ?""",
                (product_id, week_ago),
            )

            previous_sales = self.db_manager.fetch_one(
                """SELECT SUM(quantity) FROM sale_items si
                   JOIN sales s ON si.sale_id = s.id
                   WHERE si.product_id = ? AND s.created_at BETWEEN ? AND ?""",
                (product_id, two_weeks_ago, week_ago),
            )

            recent_qty = Decimal(str(recent_sales[0] or 0))
            previous_qty = Decimal(str(previous_sales[0] or 0))

            if previous_qty > 0:
                growth_rate = (recent_qty - previous_qty) / previous_qty

                if growth_rate > Decimal("0.2"):  # 20% increase
                    confidence = min(1.0, float(growth_rate / Decimal("0.5")))
                    signals.append(
                        PricingSignal(
                            signal_type="demand",
                            product_id=product_id,
                            adjustment_percentage=Decimal("10"),
                            confidence_score=confidence,
                            reason=f"High demand growth: {growth_rate:.1%}",
                            expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                        )
                    )

                elif growth_rate < Decimal("-0.2"):  # 20% decrease
                    confidence = min(1.0, float(abs(growth_rate) / Decimal("0.5")))
                    signals.append(
                        PricingSignal(
                            signal_type="demand",
                            product_id=product_id,
                            adjustment_percentage=Decimal("-8"),
                            confidence_score=confidence,
                            reason=f"Low demand: {growth_rate:.1%} decline",
                            expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                        )
                    )

        except Exception as e:
            self.logger.error(f"خطأ في إشارات الطلب: {str(e)}")

        return signals

    def _get_competition_signals(self, product_id: int) -> List[PricingSignal]:
        """إشارات بناءً على المنافسة"""
        signals = []

        try:
            # Simulate competitor analysis (would be replaced with real API calls)
            competitor_adjustment = self._simulate_competitor_analysis(product_id)

            if abs(competitor_adjustment) > 0:
                signals.append(
                    PricingSignal(
                        signal_type="competition",
                        product_id=product_id,
                        adjustment_percentage=competitor_adjustment,
                        confidence_score=0.7,
                        reason="Competitor price monitoring",
                        expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                    )
                )

        except Exception as e:
            self.logger.error(f"خطأ في إشارات المنافسة: {str(e)}")

        return signals

    def _get_customer_signals(self, product_id: int, customer: Customer, quantity: Decimal) -> List[PricingSignal]:
        """إشارات بناءً على العميل"""
        signals = []

        try:
            # High-value customer
            if hasattr(customer, "total_purchases") and customer.total_purchases > 50000:
                signals.append(
                    PricingSignal(
                        signal_type="customer_loyalty",
                        product_id=product_id,
                        adjustment_percentage=Decimal("-3"),
                        confidence_score=0.9,
                        reason=f"High-value customer: €{customer.total_purchases}",
                        expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                    )
                )

            # Bulk purchase
            if quantity > 100:
                signals.append(
                    PricingSignal(
                        signal_type="customer_loyalty",
                        product_id=product_id,
                        adjustment_percentage=Decimal("-2"),
                        confidence_score=0.8,
                        reason=f"Bulk purchase: {quantity} units",
                        expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                    )
                )

            # New customer
            if hasattr(customer, "purchases_count") and customer.purchases_count < 3:
                signals.append(
                    PricingSignal(
                        signal_type="customer_loyalty",
                        product_id=product_id,
                        adjustment_percentage=Decimal("-5"),
                        confidence_score=0.6,
                        reason="New customer acquisition",
                        expires_at=datetime.now() + timedelta(hours=self.signal_expiry_hours),
                    )
                )

        except Exception as e:
            self.logger.error(f"خطأ في إشارات العميل: {str(e)}")

        return signals

    def _get_time_signals(self) -> List[PricingSignal]:
        """إشارات بناءً على الوقت"""
        signals = []

        try:
            now = datetime.now()
            hour = now.hour
            weekday = now.weekday()

            # Weekend premium
            if weekday >= 5:  # Saturday = 5, Sunday = 6
                signals.append(
                    PricingSignal(
                        signal_type="seasonal",
                        product_id=0,  # Applies to all products
                        adjustment_percentage=Decimal("3"),
                        confidence_score=0.8,
                        reason="Weekend pricing premium",
                        expires_at=datetime.now() + timedelta(hours=24),
                    )
                )

            # Peak hours (9 AM - 5 PM on weekdays)
            if weekday < 5 and 9 <= hour <= 17:
                signals.append(
                    PricingSignal(
                        signal_type="seasonal",
                        product_id=0,
                        adjustment_percentage=Decimal("2"),
                        confidence_score=0.7,
                        reason="Peak hours pricing",
                        expires_at=datetime.now() + timedelta(hours=1),
                    )
                )

            # End of month clearance
            if now.day > 25:
                signals.append(
                    PricingSignal(
                        signal_type="seasonal",
                        product_id=0,
                        adjustment_percentage=Decimal("-5"),
                        confidence_score=0.7,
                        reason="End of month clearance",
                        expires_at=datetime.now() + timedelta(hours=24),
                    )
                )

        except Exception as e:
            self.logger.error(f"خطأ في إشارات الوقت: {str(e)}")

        return signals

    def _calculate_rules_adjustment(self, product_id: int, customer: Customer, quantity: Decimal) -> Decimal:
        """تعديل بناءً على القواعد الديناميكية"""
        try:
            total_adjustment = Decimal("0")

            for rule in self.active_rules:
                if self._rule_applies(rule, product_id, customer, quantity):
                    if rule.adjustment_type == "percentage":
                        total_adjustment += rule.adjustment_value / Decimal("100")
                    elif rule.adjustment_type == "fixed_amount":
                        # This would need base price context, simplified for now
                        total_adjustment += rule.adjustment_value / Decimal("100")  # Assume percentage for simplicity

            return total_adjustment

        except Exception as e:
            self.logger.error(f"خطأ في تعديل القواعد: {str(e)}")
            return Decimal("0")

    def _rule_applies(
        self,
        rule: DynamicPricingRule,
        product_id: int,
        customer: Customer,
        quantity: Decimal,
    ) -> bool:
        """التحقق من تطبيق القاعدة"""
        try:
            # Product filter
            if rule.product_id and rule.product_id != product_id:
                return False

            # Customer segment filter
            if rule.customer_segment and hasattr(customer, "customer_type"):
                if customer.customer_type != rule.customer_segment:
                    return False

            # Condition evaluation (simplified)
            if rule.condition_type == "inventory_level":
                stock = self.db_manager.fetch_one("SELECT current_stock FROM products WHERE id = ?", (product_id,))
                if stock:
                    current_stock = Decimal(str(stock[0] or 0))
                    return self._evaluate_condition(current_stock, rule.condition_operator, rule.condition_value)

            elif rule.condition_type == "quantity":
                return self._evaluate_condition(quantity, rule.condition_operator, rule.condition_value)

            return True

        except Exception:
            return False

    def _evaluate_condition(self, value: Decimal, operator: str, target: Any) -> bool:
        """تقييم الشرط"""
        try:
            target = Decimal(str(target))

            if operator == ">":
                return value > target
            elif operator == "<":
                return value < target
            elif operator == ">=":
                return value >= target
            elif operator == "<=":
                return value <= target
            elif operator == "==":
                return value == target

            return False

        except Exception:
            return False

    def _simulate_competitor_analysis(self, product_id: int) -> Decimal:
        """محاكاة تحليل المنافسين"""
        # In real implementation, this would call external APIs
        # For now, return small random adjustments
        return Decimal(str(random.uniform(-2, 2)))

    def _load_active_rules(self):
        """تحميل القواعد النشطة"""
        try:
            # This would load from database in real implementation
            self.active_rules = []
        except Exception:
            self.active_rules = []

    def add_pricing_signal(self, signal: PricingSignal):
        """إضافة إشارة تسعير"""
        self.pricing_signals.append(signal)

        # Store in database (would be implemented)
        try:
            # Database storage logic would go here
            pass
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الإشارة: {str(e)}")

    def get_pricing_insights(
        self,
        product_id: int,
        customer: Customer = None,
        quantity: Decimal = Decimal("1"),
    ) -> Dict[str, Any]:
        """الحصول على رؤى التسعير المتقدمة"""
        try:
            bp_row = self.db_manager.fetch_one("SELECT retail_price FROM products WHERE id = ?", (product_id,))

            if not bp_row or not bp_row.get('retail_price'):
                return {}

            base_price = Decimal(str(bp_row.get('retail_price')))

            # Get all adjustments
            inventory_adj = self._calculate_inventory_adjustment(product_id)
            demand_adj = self._calculate_demand_adjustment(product_id)
            loyalty_adj = self._calculate_loyalty_adjustment(customer) if customer else Decimal("0")
            quantity_adj = self._calculate_quantity_adjustment(quantity)
            time_adj = self._calculate_time_adjustment()
            signals_adj = self._calculate_signals_adjustment(base_price, product_id, customer, quantity)
            rules_adj = self._calculate_rules_adjustment(product_id, customer, quantity)

            total_adjustment = (
                inventory_adj + demand_adj + loyalty_adj + quantity_adj + time_adj + signals_adj + rules_adj
            )
            final_price = base_price * (Decimal("1") + total_adjustment)

            # Get applicable signals
            signals = self._get_applicable_signals(product_id, customer, quantity)

            return {
                "product_id": product_id,
                "base_price": float(base_price),
                "adjustments": {
                    "inventory": float(inventory_adj),
                    "demand": float(demand_adj),
                    "loyalty": float(loyalty_adj),
                    "quantity": float(quantity_adj),
                    "time": float(time_adj),
                    "signals": float(signals_adj),
                    "rules": float(rules_adj),
                },
                "total_adjustment": float(total_adjustment),
                "final_price": float(final_price),
                "signals_count": len(signals),
                "signal_types": list(set(s.signal_type for s in signals)),
                "confidence_score": (sum(s.confidence_score for s in signals) / len(signals) if signals else 0),
                "recommendations": self._generate_recommendations(total_adjustment, signals),
            }

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الرؤى: {str(e)}")
            return {}

    def _generate_recommendations(self, total_adjustment: Decimal, signals: List[PricingSignal]) -> List[str]:
        """توليد توصيات بناءً على التحليل"""
        recommendations = []

        if total_adjustment > Decimal("0.1"):  # 10% increase
            recommendations.append("السعر مرتفع - قد يؤثر على المبيعات")
        elif total_adjustment < Decimal("-0.1"):  # 10% decrease
            recommendations.append("السعر منخفض - تحقق من هوامش الربح")

        # Signal-based recommendations
        signal_types = set(s.signal_type for s in signals)
        if "inventory" in signal_types and any(
            s.adjustment_percentage > 0 for s in signals if s.signal_type == "inventory"
        ):
            recommendations.append("زيادة المخزون الموصى بها لتجنب نقص المعروض")
        if "demand" in signal_types and any(s.adjustment_percentage < 0 for s in signals if s.signal_type == "demand"):
            recommendations.append("عرض ترويجي لزيادة الطلب")

        return recommendations

    def _calculate_loyalty_adjustment(self, customer: Customer) -> Decimal:
        """تعديل بناءً على ولاء العميل"""
        try:
            if not customer.purchases_count:
                return Decimal("0.00")

            # VIP customers get better pricing
            if customer.customer_type == "vip":
                return Decimal("-0.05")

            # Long-term customers get loyalty discount
            if customer.purchases_count > 100:
                return Decimal("-0.03")
            elif customer.purchases_count > 50:
                return Decimal("-0.02")
            elif customer.purchases_count > 20:
                return Decimal("-0.01")

            return Decimal("0.00")

        except Exception:
            return Decimal("0.00")

    def _calculate_quantity_adjustment(self, quantity: Decimal) -> Decimal:
        """تعديل بناءً على الكمية المطلوبة"""
        try:
            if quantity >= 1000:
                return Decimal("-0.08")  # Bulk discount
            elif quantity >= 500:
                return Decimal("-0.05")
            elif quantity >= 100:
                return Decimal("-0.03")
            elif quantity >= 50:
                return Decimal("-0.01")

            return Decimal("0.00")

        except Exception:
            return Decimal("0.00")

    def _calculate_time_adjustment(self) -> Decimal:
        """تعديل بناءً على الوقت (الساعات الذروة، المواسم)"""
        try:
            now = datetime.now()
            hour = now.hour

            # Peak hours pricing (9 AM - 5 PM)
            if 9 <= hour <= 17:
                return Decimal("0.02")

            # Off-peak discount
            return Decimal("-0.01")

        except Exception:
            return Decimal("0.00")

    def _get_minimum_price(self, product_id: int) -> Decimal:
        """الحصول على الحد الأدنى للسعر (أعلى من تكلفة الشراء)"""
        try:
            cost_info = self.db_manager.fetch_one("SELECT purchase_price FROM products WHERE id = ?", (product_id,))

            if cost_info and cost_info[0]:
                cost = Decimal(str(cost_info[0]))
                # Minimum price is cost + 10% margin
                return cost * Decimal("1.10")

            return Decimal("0.00")

        except Exception:
            return Decimal("0.00")

    def get_price_recommendation(self, product_id: int) -> Dict[str, Any]:
        """الحصول على توصية تسعير مفصلة"""
        try:
            bp_row = self.db_manager.fetch_one("SELECT retail_price FROM products WHERE id = ?", (product_id,))

            if not bp_row or not bp_row.get('retail_price'):
                return {}

            base_price = Decimal(str(bp_row.get('retail_price')))

            # Create a mock customer for testing
            mock_customer = Customer(id=1, name="Test Customer")  # noqa: F841

            # Calculate adjustments
            inventory_adj = self._calculate_inventory_adjustment(product_id)
            demand_adj = self._calculate_demand_adjustment(product_id)
            time_adj = self._calculate_time_adjustment()

            total_adjustment = inventory_adj + demand_adj + time_adj
            recommended_price = base_price * (Decimal("1.00") + total_adjustment)

            return {
                "product_id": product_id,
                "base_price": float(base_price),
                "inventory_adjustment": float(inventory_adj),
                "demand_adjustment": float(demand_adj),
                "time_adjustment": float(time_adj),
                "total_adjustment": float(total_adjustment),
                "recommended_price": float(recommended_price),
                "confidence": "medium",  # Will be improved with ML
            }

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على توصية التسعير: {str(e)}")
            return {}

    def apply_competitor_pricing(self, product_id: int, competitor_price: Decimal) -> bool:
        """تطبيق تسعير تنافسي (سيتم تطويره لاحقاً)"""
        # Placeholder for competitor price monitoring
        # This would integrate with external APIs to monitor competitor prices
        return False
