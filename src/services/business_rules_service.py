#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام تحويل الوحدات - Unit Conversion Service
يدعم تحويل الوحدات المتعددة (كرتونة ↔ علبة ↔ حبة)
مع تسعير مختلف لكل وحدة وخصم مخزون ذكي.

Features:
- Multi-level unit conversion matrix (carton → box → piece)
- Per-unit pricing (buy by carton, sell by piece)
- FEFO (First Expired First Out) batch allocation
- Moving Average costing
- Credit limit enforcement
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logger import setup_logger


logger = setup_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# 1. UNIT CONVERSION SERVICE
# ═══════════════════════════════════════════════════════════════════════

class UnitType(Enum):
    """أنواع الوحدات القياسية"""
    PIECE = "piece"
    BOX = "box"
    CARTON = "carton"
    DOZEN = "dozen"
    KG = "kg"
    GRAM = "gram"
    LITER = "liter"
    ML = "ml"
    METER = "meter"
    ROLL = "roll"
    PACK = "pack"
    BAG = "bag"
    PALLET = "pallet"
    SET = "set"

    @property
    def display_ar(self) -> str:
        names = {
            "piece": "حبة", "box": "علبة", "carton": "كرتونة",
            "dozen": "دزينة", "kg": "كغ", "gram": "غرام",
            "liter": "لتر", "ml": "مل", "meter": "متر",
            "roll": "رول", "pack": "حزمة", "bag": "كيس",
            "pallet": "باليت", "set": "طقم",
        }
        return names.get(self.value, self.value)


@dataclass
class UnitConversion:
    """تعريف تحويل بين وحدتين لنفس المنتج"""
    product_id: int
    from_unit: str       # الوحدة الكبيرة (مثلاً: carton)
    to_unit: str         # الوحدة الصغيرة (مثلاً: box)
    factor: Decimal      # عامل التحويل (مثلاً: 12 = كرتونة تحتوي 12 علبة)
    from_unit_price: Optional[Decimal] = None  # سعر الشراء بالوحدة الكبيرة
    to_unit_price: Optional[Decimal] = None    # سعر البيع بالوحدة الصغيرة


@dataclass
class UnitPrice:
    """تسعير منتج بوحدة محددة"""
    product_id: int
    unit: str
    price: Decimal         # سعر البيع
    cost_price: Decimal    # سعر التكلفة
    barcode: Optional[str] = None  # باركود خاص بهذه الوحدة


class UnitConversionService:
    """
    خدمة تحويل الوحدات المتعددة.

    تدعم:
    - تحويل الكميات بين الوحدات (كرتونة → علبة → حبة)
    - التسعير لكل وحدة
    - خصم المخزون بوحدة مختلفة عن وحدة الشراء
    - باركود خاص لكل وحدة

    Example:
        # شراء: 10 كرتونات × 12 علبة = 120 علبة
        svc.set_conversion(product_id=1, from_unit="carton", to_unit="box", factor=12)
        svc.set_conversion(product_id=1, from_unit="box", to_unit="piece", factor=24)

        # تحويل: 2 كرتونة = ? حبة
        pieces = svc.convert(product_id=1, qty=2, from_unit="carton", to_unit="piece")
        # ← 2 × 12 × 24 = 576 حبة
    """

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or setup_logger(__name__)
        self._ensure_tables()

    def _ensure_tables(self):
        """ضمان وجود جداول تحويل الوحدات"""
        try:
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS unit_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    from_unit TEXT NOT NULL,
                    to_unit TEXT NOT NULL,
                    factor DECIMAL(10,4) NOT NULL CHECK(factor > 0),
                    from_unit_price DECIMAL(10,2),
                    to_unit_price DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(product_id, from_unit, to_unit),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS unit_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    unit TEXT NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    cost_price DECIMAL(10,2) NOT NULL,
                    barcode TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(product_id, unit),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)
            self.db.execute_non_query("""
                CREATE INDEX IF NOT EXISTS idx_unit_conv_product
                ON unit_conversions(product_id)
            """)
            self.db.execute_non_query("""
                CREATE INDEX IF NOT EXISTS idx_unit_prices_product
                ON unit_prices(product_id)
            """)
        except Exception as e:
            self.logger.warning("Failed to create unit conversion tables: %s", e)

    def set_conversion(
        self,
        product_id: int,
        from_unit: str,
        to_unit: str,
        factor: Decimal,
        from_unit_price: Optional[Decimal] = None,
        to_unit_price: Optional[Decimal] = None,
    ) -> bool:
        """تعريف تحويل بين وحدتين (upsert)"""
        try:
            factor = Decimal(str(factor))
            if factor <= 0:
                self.logger.warning("Conversion factor must be > 0, got %s", factor)
                return False

            self.db.execute_non_query("""
                INSERT INTO unit_conversions (product_id, from_unit, to_unit, factor, from_unit_price, to_unit_price)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id, from_unit, to_unit) DO UPDATE SET
                    factor = excluded.factor,
                    from_unit_price = excluded.from_unit_price,
                    to_unit_price = excluded.to_unit_price,
                    updated_at = CURRENT_TIMESTAMP
            """, (product_id, from_unit, to_unit, float(factor),
                  float(from_unit_price) if from_unit_price else None,
                  float(to_unit_price) if to_unit_price else None))

            # Also store the inverse conversion (to_unit → from_unit = 1/factor)
            inverse = Decimal("1") / factor
            self.db.execute_non_query("""
                INSERT INTO unit_conversions (product_id, from_unit, to_unit, factor, from_unit_price, to_unit_price)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id, from_unit, to_unit) DO UPDATE SET
                    factor = excluded.factor,
                    updated_at = CURRENT_TIMESTAMP
            """, (product_id, to_unit, from_unit, float(inverse),
                  float(to_unit_price) if to_unit_price else None,
                  float(from_unit_price) if from_unit_price else None))

            return True
        except Exception as e:
            self.logger.error("Failed to set conversion: %s", e)
            return False

    def set_unit_price(
        self,
        product_id: int,
        unit: str,
        price: Decimal,
        cost_price: Decimal,
        barcode: Optional[str] = None,
        is_default: bool = False,
    ) -> bool:
        """تعيين سعر لوحدة محددة من المنتج"""
        try:
            self.db.execute_non_query("""
                INSERT INTO unit_prices (product_id, unit, price, cost_price, barcode, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id, unit) DO UPDATE SET
                    price = excluded.price,
                    cost_price = excluded.cost_price,
                    barcode = excluded.barcode,
                    is_default = excluded.is_default
            """, (product_id, unit, float(price), float(cost_price), barcode, int(is_default)))
            return True
        except Exception as e:
            self.logger.error("Failed to set unit price: %s", e)
            return False

    def convert(
        self,
        product_id: int,
        quantity: Decimal,
        from_unit: str,
        to_unit: str,
    ) -> Decimal:
        """
        تحويل كمية من وحدة إلى أخرى.

        يستخدم البحث عن مسار التحويل (BFS) للوصول من from_unit إلى to_unit
        عبر سلسلة من التحويلات المعرفة.

        Example:
            convert(1, 2, "carton", "piece")  # 2 كرتونة → 576 حبة
        """
        quantity = Decimal(str(quantity))
        if from_unit == to_unit:
            return quantity

        # Try direct conversion first
        direct = self.db.fetch_one(
            "SELECT factor FROM unit_conversions WHERE product_id = ? AND from_unit = ? AND to_unit = ?",
            (product_id, from_unit, to_unit),
        )
        if direct:
            return (quantity * Decimal(str(direct.get("factor", 0) or 0))).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # BFS path search for multi-step conversion
        result = self._find_conversion_path(product_id, from_unit, to_unit)
        if result is not None:
            path_factor = result
            return (quantity * path_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        self.logger.warning(
            "No conversion path from %s to %s for product %d",
            from_unit, to_unit, product_id,
        )
        return quantity  # Return original if no conversion found

    def _find_conversion_path(
        self, product_id: int, from_unit: str, to_unit: str
    ) -> Optional[Decimal]:
        """BFS للعثور على مسار تحويل عبر وحدات وسيطة"""
        rows = self.db.fetch_all(
            "SELECT from_unit, to_unit, factor FROM unit_conversions WHERE product_id = ?",
            (product_id,),
        )
        if not rows:
            return None

        # Build adjacency list
        graph: Dict[str, List[Tuple[str, Decimal]]] = {}
        for row in rows:
            fu = row.get("from_unit", "")
            tu = row.get("to_unit", "")
            f = Decimal(str(row.get("factor", 1) or 1))
            graph.setdefault(fu, []).append((tu, f))

        # BFS
        from collections import deque
        queue = deque([(from_unit, Decimal("1"))])
        visited = {from_unit}

        while queue:
            current, accumulated = queue.popleft()
            for next_unit, factor in graph.get(current, []):
                new_factor = accumulated * factor
                if next_unit == to_unit:
                    return new_factor
                if next_unit not in visited:
                    visited.add(next_unit)
                    queue.append((next_unit, new_factor))

        return None

    def get_price_for_unit(
        self, product_id: int, unit: str
    ) -> Optional[Dict[str, Decimal]]:
        """الحصول على سعر البيع والتكلفة لوحدة محددة"""
        row = self.db.fetch_one(
            "SELECT price, cost_price, barcode FROM unit_prices WHERE product_id = ? AND unit = ?",
            (product_id, unit),
        )
        if row:
            return {
                "price": Decimal(str(row.get("price", 0) or 0)),
                "cost_price": Decimal(str(row.get("cost_price", 0) or 0)),
                "barcode": row.get("barcode"),
            }
        return None

    def get_all_conversions(self, product_id: int) -> List[Dict]:
        """الحصول على كل تحويلات منتج"""
        rows = self.db.fetch_all(
            "SELECT from_unit, to_unit, factor, from_unit_price, to_unit_price FROM unit_conversions WHERE product_id = ?",
            (product_id,),
        )
        return [dict(r) for r in rows] if rows else []

    def get_all_unit_prices(self, product_id: int) -> List[Dict]:
        """الحصول على كل أسعار الوحدات لمنتج"""
        rows = self.db.fetch_all(
            "SELECT unit, price, cost_price, barcode, is_default FROM unit_prices WHERE product_id = ? ORDER BY is_default DESC",
            (product_id,),
        )
        return [dict(r) for r in rows] if rows else []

    def deduct_stock_by_unit(
        self,
        product_id: int,
        quantity: Decimal,
        unit: str,
        base_unit: str = "piece",
    ) -> Tuple[Decimal, bool]:
        """
        خصم مخزون بوحدة مختلفة عن الوحدة الأساسية.

        Returns:
            (equivalent_base_qty, success)
        """
        base_qty = self.convert(product_id, quantity, unit, base_unit)
        return base_qty, True  # Actual deduction done by caller


# ═══════════════════════════════════════════════════════════════════════
# 2. FEFO BATCH ALLOCATION SERVICE
# ═══════════════════════════════════════════════════════════════════════

class AllocationStrategy(Enum):
    """استراتيجيات تخصيص الدفعات"""
    FIFO = "fifo"          # أولاً دخل أولاً خرج
    FEFO = "fefo"          # أولاً تنتهي صلاحيته أولاً خرج
    LIFO = "lifo"          # آخر دخل أولاً خرج
    MANUAL = "manual"      # يدوي (المستخدم يختار)
    PREFER_AVAILABLE = "prefer_available"  # يفضل الدفعة الأكثر توفراً


@dataclass
class BatchAllocation:
    """تخصيص كمية من دفعة محددة"""
    batch_id: int
    batch_number: str
    quantity: Decimal
    cost_price: Decimal
    expiry_date: Optional[str] = None


class BatchAllocationService:
    """
    خدمة تخصيص الدفعات عند البيع.

    FEFO: First Expired First Out — يختار الدفعة الأقرب انتهاءً أولاً
    FIFO: First In First Out — يختار أقدم دفعة أولاً
    """

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or setup_logger(__name__)

    def allocate_batches(
        self,
        product_id: int,
        required_quantity: Decimal,
        strategy: AllocationStrategy = AllocationStrategy.FEFO,
        warehouse_id: Optional[int] = None,
        exclude_batch_ids: Optional[List[int]] = None,
    ) -> List[BatchAllocation]:
        """
        تخصيص الكمية المطلوبة من الدفعات حسب الاستراتيجية.

        Args:
            product_id: معرف المنتج
            required_quantity: الكمية المطلوبة
            strategy: استراتيجية التخصيص (FEFO افتراضياً)
            warehouse_id: مستودع محدد (اختياري)
            exclude_batch_ids: دفعات مستثناة (اختياري)

        Returns:
            قائمة BatchAllocation مع الكميات المخصصة من كل دفعة
        """
        required = Decimal(str(required_quantity))
        if required <= 0:
            return []

        # Fetch available batches
        batches = self._get_available_batches(product_id, warehouse_id, exclude_batch_ids)
        if not batches:
            self.logger.warning(
                "No batches available for product %d (strategy=%s)",
                product_id, strategy.value,
            )
            return []

        # Sort by strategy
        sorted_batches = self._sort_batches(batches, strategy)

        # Allocate from sorted batches
        allocations = []
        remaining = required

        for batch in sorted_batches:
            if remaining <= 0:
                break

            available = Decimal(str(batch.get("quantity", 0) or 0))
            if available <= 0:
                continue

            take = min(available, remaining)
            allocations.append(BatchAllocation(
                batch_id=batch.get("id", 0),
                batch_number=batch.get("batch_number", ""),
                quantity=take,
                cost_price=Decimal(str(batch.get("cost_price", 0) or 0)),
                expiry_date=batch.get("expiry_date"),
            ))
            remaining -= take

        if remaining > 0:
            self.logger.warning(
                "Insufficient batch stock for product %d: needed %s, allocated %s",
                product_id, required, required - remaining,
            )

        return allocations

    def _get_available_batches(
        self,
        product_id: int,
        warehouse_id: Optional[int] = None,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        """الحصول على الدفعات المتاحة"""
        query = """
            SELECT b.id, b.batch_number, b.quantity, b.cost_price,
                   b.expiry_date, b.purchase_date
            FROM batches b
            WHERE b.product_id = ?
              AND b.quantity > 0
              AND b.is_active = 1
              AND (b.is_deleted = 0 OR b.is_deleted IS NULL)
              AND (b.expiry_date IS NULL OR b.expiry_date > date('now'))
        """
        params: list = [product_id]

        if warehouse_id:
            query += " AND b.warehouse_id = ?"
            params.append(warehouse_id)

        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            query += f" AND b.id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        rows = self.db.fetch_all(query, tuple(params))
        return [dict(r) for r in rows] if rows else []

    def _sort_batches(
        self, batches: List[Dict], strategy: AllocationStrategy
    ) -> List[Dict]:
        """ترتيب الدفعات حسب الاستراتيجية"""
        if strategy == AllocationStrategy.FEFO:
            # الأقرب انتهاءً أولاً (NULL آخر)
            return sorted(batches, key=lambda b: (
                0 if b.get("expiry_date") else 1,
                b.get("expiry_date") or "9999-12-31",
            ))

        if strategy == AllocationStrategy.FIFO:
            # أقدم دفعة أولاً (حسب تاريخ الشراء)
            return sorted(batches, key=lambda b: b.get("purchase_date") or "9999-12-31")

        if strategy == AllocationStrategy.LIFO:
            # آخر دفعة أولاً
            return sorted(batches, key=lambda b: b.get("purchase_date") or "", reverse=True)

        if strategy == AllocationStrategy.PREFER_AVAILABLE:
            # الدفعة الأكثر توفراً أولاً
            return sorted(batches, key=lambda b: float(b.get("quantity", 0) or 0), reverse=True)

        # MANUAL or unknown — return as-is
        return batches

    def execute_allocation(
        self,
        allocations: List[BatchAllocation],
        reference_id: Optional[int] = None,
        reference_type: str = "sale",
    ) -> bool:
        """
        تنفيذ التخصيص فعلياً — خصم الكميات من الدفعات في قاعدة البيانات.

        Returns True if ALL deductions succeeded.
        """
        all_ok = True
        for alloc in allocations:
            try:
                # Atomic deduction with WHERE quantity >= ?
                self.db.execute_non_query(
                    "UPDATE batches SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ? AND quantity >= ?",
                    (float(alloc.quantity), alloc.batch_id, float(alloc.quantity)),
                )
                # Check rowcount
                row = self.db.fetch_one(
                    "SELECT changes() as affected"
                )
                affected = row.get("affected", 0) if row else 0
                if affected == 0:
                    self.logger.error(
                        "Batch %d deduction failed: insufficient quantity",
                        alloc.batch_id,
                    )
                    all_ok = False
            except Exception as e:
                self.logger.error("Batch %d deduction error: %s", alloc.batch_id, e)
                all_ok = False

        return all_ok


# ═══════════════════════════════════════════════════════════════════════
# 3. MOVING AVERAGE COSTING SERVICE
# ═══════════════════════════════════════════════════════════════════════

class CostingMethod(Enum):
    """طرق حساب التكلفة"""
    STANDARD = "standard"          # تكلفة قياسية (ثابتة)
    MOVING_AVERAGE = "moving_avg"  # متوسط متحرك
    FIFO = "fifo"                  # أولاً دخل أولاً خرج
    FIFO_PERPETUAL = "fifo_perpetual"  # FIFO مستمر (طبقات تكلفة)


@dataclass
class CostLayer:
    """طبقة تكلفة FIFO"""
    id: Optional[int] = None
    product_id: int = 0
    quantity: Decimal = Decimal("0")
    unit_cost: Decimal = Decimal("0")
    remaining: Decimal = Decimal("0")
    purchase_id: Optional[int] = None
    created_at: Optional[str] = None


class CostingService:
    """
    خدمة حساب التكلفة — تدعم Moving Average و FIFO و Standard.

    Moving Average:
        عند كل عملية شراء:
        new_avg = (old_avg × old_qty + purchase_cost × purchase_qty) / (old_qty + purchase_qty)

    FIFO:
        كل دفعة مشتراة = طبقة تكلفة منفصلة
        عند البيع: خصم من أقدم طبقة أولاً
    """

    COSTING_CONFIG_KEY = "costing_method"

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or setup_logger(__name__)
        self._ensure_tables()

    def _ensure_tables(self):
        """ضمان وجود جداول طبقات التكلفة"""
        try:
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS cost_layers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    quantity DECIMAL(10,4) NOT NULL,
                    remaining DECIMAL(10,4) NOT NULL,
                    unit_cost DECIMAL(10,4) NOT NULL,
                    purchase_id INTEGER,
                    batch_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)
            self.db.execute_non_query("""
                CREATE INDEX IF NOT EXISTS idx_cost_layers_product
                ON cost_layers(product_id, created_at)
            """)
        except Exception as e:
            self.logger.warning("Failed to create cost layers table: %s", e)

    def get_costing_method(self) -> CostingMethod:
        """الحصول على طريقة التكلفة الحالية من إعدادات النظام"""
        try:
            row = self.db.fetch_one(
                "SELECT value FROM system_settings WHERE key = ?",
                (self.COSTING_CONFIG_KEY,),
            )
            if row:
                method_str = row.get("value", "standard") or "standard"
                return CostingMethod(method_str)
        except Exception:
            pass
        return CostingMethod.STANDARD  # الافتراضي

    def set_costing_method(self, method: CostingMethod) -> bool:
        """تعيين طريقة التكلفة"""
        try:
            self.db.execute_non_query("""
                INSERT INTO system_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (self.COSTING_CONFIG_KEY, method.value))
            self.logger.info("Costing method set to: %s", method.value)
            return True
        except Exception as e:
            self.logger.error("Failed to set costing method: %s", e)
            return False

    def on_purchase(
        self,
        product_id: int,
        quantity: Decimal,
        unit_cost: Decimal,
        purchase_id: Optional[int] = None,
        batch_id: Optional[int] = None,
    ) -> Decimal:
        """
        معالجة عملية شراء — تحديث التكلفة حسب الطريقة المختارة.

        Returns the new cost_price for the product.
        """
        quantity = Decimal(str(quantity))
        unit_cost = Decimal(str(unit_cost))

        if quantity <= 0 or unit_cost < 0:
            return unit_cost

        method = self.get_costing_method()

        if method == CostingMethod.MOVING_AVERAGE:
            return self._update_moving_average(product_id, quantity, unit_cost)

        if method in (CostingMethod.FIFO, CostingMethod.FIFO_PERPETUAL):
            return self._add_fifo_layer(product_id, quantity, unit_cost, purchase_id, batch_id)

        # STANDARD — just return the cost as-is
        return unit_cost

    def _update_moving_average(
        self, product_id: int, new_qty: Decimal, new_cost: Decimal
    ) -> Decimal:
        """
        حساب المتوسط المتحرك.

        new_avg = (old_avg × old_qty + new_cost × new_qty) / (old_qty + new_qty)
        """
        try:
            product = self.db.fetch_one(
                "SELECT cost_price, current_stock FROM products WHERE id = ?",
                (product_id,),
            )
            if not product:
                return new_cost

            old_cost = Decimal(str(product.get("cost_price", 0) or 0))
            old_qty = Decimal(str(product.get("current_stock", 0) or 0))

            if old_qty + new_qty == 0:
                return new_cost

            # Moving average formula
            total_old = old_cost * old_qty
            total_new = new_cost * new_qty
            new_avg = (total_old + total_new) / (old_qty + new_qty)

            # Round to 2 decimal places
            new_avg = new_avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Update product's cost_price
            self.db.execute_non_query(
                "UPDATE products SET cost_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (float(new_avg), product_id),
            )

            self.logger.info(
                "Moving Average updated for product %d: "
                "old (%s × %s) + new (%s × %s) / total (%s) = %s",
                product_id, old_cost, old_qty, new_cost, new_qty,
                old_qty + new_qty, new_avg,
            )

            return new_avg

        except Exception as e:
            self.logger.error("Moving average calculation failed: %s", e)
            return new_cost

    def _add_fifo_layer(
        self,
        product_id: int,
        quantity: Decimal,
        unit_cost: Decimal,
        purchase_id: Optional[int] = None,
        batch_id: Optional[int] = None,
    ) -> Decimal:
        """إضافة طبقة تكلفة FIFO جديدة"""
        try:
            self.db.execute_non_query("""
                INSERT INTO cost_layers (product_id, quantity, remaining, unit_cost, purchase_id, batch_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, float(quantity), float(quantity), float(unit_cost),
                  purchase_id, batch_id))

            # Update product cost_price to the latest layer cost
            self.db.execute_non_query(
                "UPDATE products SET cost_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (float(unit_cost), product_id),
            )

            return unit_cost
        except Exception as e:
            self.logger.error("FIFO layer creation failed: %s", e)
            return unit_cost

    def get_cost_of_goods_sold(
        self,
        product_id: int,
        quantity: Decimal,
    ) -> Decimal:
        """
        حساب تكلفة البضاعة المباعة (COGS) حسب طريقة التكلفة.

        For FIFO: خصم من أقدم طبقات التكلفة.
        For Moving Average: استخدم cost_price الحالي.
        For Standard: استخدم cost_price الثابت.
        """
        quantity = Decimal(str(quantity))
        method = self.get_costing_method()

        if method in (CostingMethod.STANDARD, CostingMethod.MOVING_AVERAGE):
            # Use current cost_price directly
            product = self.db.fetch_one(
                "SELECT cost_price FROM products WHERE id = ?",
                (product_id,),
            )
            cost = Decimal(str(product.get("cost_price", 0) or 0)) if product else Decimal("0")
            return (cost * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if method in (CostingMethod.FIFO, CostingMethod.FIFO_PERPETUAL):
            return self._fifo_cogs(product_id, quantity)

        return Decimal("0")

    def _fifo_cogs(self, product_id: int, quantity: Decimal) -> Decimal:
        """حساب COGS بطريقة FIFO — من أقدم طبقة"""
        total_cogs = Decimal("0")
        remaining = quantity

        layers = self.db.fetch_all(
            "SELECT id, remaining, unit_cost FROM cost_layers "
            "WHERE product_id = ? AND remaining > 0 "
            "ORDER BY created_at ASC",
            (product_id,),
        )

        if not layers:
            # Fallback to product cost_price
            product = self.db.fetch_one(
                "SELECT cost_price FROM products WHERE id = ?",
                (product_id,),
            )
            cost = Decimal(str(product.get("cost_price", 0) or 0)) if product else Decimal("0")
            return cost * quantity

        for layer in layers:
            if remaining <= 0:
                break

            layer_remaining = Decimal(str(layer.get("remaining", 0) or 0))
            unit_cost = Decimal(str(layer.get("unit_cost", 0) or 0))
            layer_id = layer.get("id", 0)

            take = min(layer_remaining, remaining)
            total_cogs += take * unit_cost
            remaining -= take

            # Update layer remaining
            new_remaining = layer_remaining - take
            self.db.execute_non_query(
                "UPDATE cost_layers SET remaining = ? WHERE id = ?",
                (float(new_remaining), layer_id),
            )

        return total_cogs.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ═══════════════════════════════════════════════════════════════════════
# 4. CREDIT LIMIT ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════

class CreditLimitError(Exception):
    """استثناء تجاوز السقف الائتماني"""
    def __init__(self, customer_id: int, credit_limit: Decimal, current_balance: Decimal, requested: Decimal):
        self.customer_id = customer_id
        self.credit_limit = credit_limit
        self.current_balance = current_balance
        self.requested = requested
        available = credit_limit - current_balance
        super().__init__(
            f"تجاوز السقف الائتماني للعميل {customer_id}: "
            f"السقف={credit_limit}, الرصيد={current_balance}, "
            f"المتاح={available}, المطلوب={requested}"
        )


class ARAgingReport:
    """تقرير تقادم الذمم المدينة"""
    def __init__(self):
        self.current = Decimal("0")       # 0-30 يوم
        self.days_31_60 = Decimal("0")    # 31-60 يوم
        self.days_61_90 = Decimal("0")    # 61-90 يوم
        self.over_90 = Decimal("0")       # أكثر من 90 يوم
        self.total = Decimal("0")

    def to_dict(self) -> Dict:
        return {
            "current_0_30": float(self.current),
            "days_31_60": float(self.days_31_60),
            "days_61_90": float(self.days_61_90),
            "over_90_days": float(self.over_90),
            "total": float(self.total),
        }


class CreditService:
    """
    خدمة إدارة الائتمان — تطبيق السقف الائتماني + تقادم الذمم.

    Features:
    - فحص السقف الائتماني قبل البيع الآجل
    - تقارير تقادم الذمم المدينة (0-30, 31-60, 61-90, 90+)
    - تجميد حسابات العملاء المتجاوزين للسقف
    """

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or setup_logger(__name__)

    def check_credit_limit(
        self,
        customer_id: int,
        sale_amount: Decimal,
        raise_on_exceed: bool = True,
    ) -> Dict[str, Any]:
        """
        فحص السقف الائتماني قبل السماح بالبيع الآجل.

        Args:
            customer_id: معرف العميل
            sale_amount: مبلغ الفاتورة
            raise_on_exceed: رفع CreditLimitError إذا تجاوز

        Returns:
            dict with: allowed, credit_limit, current_balance, available, requested, over_by
        """
        sale_amount = Decimal(str(sale_amount))

        customer = self.db.fetch_one(
            "SELECT id, name, credit_limit, current_balance, is_active FROM customers WHERE id = ?",
            (customer_id,),
        )

        if not customer:
            return {"allowed": False, "reason": "customer_not_found"}

        credit_limit = Decimal(str(customer.get("credit_limit", 0) or 0))
        current_balance = Decimal(str(customer.get("current_balance", 0) or 0))
        available = credit_limit - current_balance

        result = {
            "customer_id": customer_id,
            "customer_name": customer.get("name", ""),
            "credit_limit": float(credit_limit),
            "current_balance": float(current_balance),
            "available_credit": float(available),
            "requested": float(sale_amount),
            "over_by": float(max(Decimal("0"), sale_amount - available)),
        }

        if credit_limit == 0:
            # No credit limit set = unlimited credit
            result["allowed"] = True
            return result

        if sale_amount > available:
            result["allowed"] = False
            result["reason"] = "credit_limit_exceeded"

            if raise_on_exceed:
                raise CreditLimitError(
                    customer_id, credit_limit, current_balance, sale_amount
                )
            return result

        result["allowed"] = True
        return result

    def get_ar_aging(self, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        تقرير تقادم الذمم المدينة (AR Aging Report).

        يقسم الرصيد المستحق إلى فئات حسب عدد أيام التأخير:
        - Current: 0-30 يوم
        - 31-60 يوم
        - 61-90 يوم
        - أكثر من 90 يوم
        """
        query = """
            SELECT
                c.id as customer_id,
                c.name as customer_name,
                s.id as sale_id,
                s.remaining_amount,
                s.sale_date,
                s.due_date,
                CASE
                    WHEN s.due_date IS NOT NULL THEN
                        CAST(julianday('now') - julianday(s.due_date) AS INTEGER)
                    ELSE
                        CAST(julianday('now') - julianday(s.sale_date) AS INTEGER)
                END as days_overdue
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.remaining_amount > 0
              AND s.payment_method IN ('credit', 'آجل')
              AND s.status != 'cancelled'
              AND (c.is_deleted = 0 OR c.is_deleted IS NULL)
        """
        params: tuple = ()

        if customer_id:
            query += " AND c.id = ?"
            params = (customer_id,)

        rows = self.db.fetch_all(query, params)

        aging = {
            "customers": [],
            "summary": {
                "current_0_30": 0.0,
                "days_31_60": 0.0,
                "days_61_90": 0.0,
                "over_90": 0.0,
                "total": 0.0,
            },
        }

        customer_map: Dict[int, Dict] = {}

        for row in rows:
            cid = row.get("customer_id", 0)
            amount = float(row.get("remaining_amount", 0) or 0)
            days = row.get("days_overdue", 0) or 0

            if cid not in customer_map:
                customer_map[cid] = {
                    "customer_id": cid,
                    "customer_name": row.get("customer_name", ""),
                    "current_0_30": 0.0,
                    "days_31_60": 0.0,
                    "days_61_90": 0.0,
                    "over_90": 0.0,
                    "total": 0.0,
                }

            # Classify into aging buckets
            if days <= 30:
                customer_map[cid]["current_0_30"] += amount
                aging["summary"]["current_0_30"] += amount
            elif days <= 60:
                customer_map[cid]["days_31_60"] += amount
                aging["summary"]["days_31_60"] += amount
            elif days <= 90:
                customer_map[cid]["days_61_90"] += amount
                aging["summary"]["days_61_90"] += amount
            else:
                customer_map[cid]["over_90"] += amount
                aging["summary"]["over_90"] += amount

            customer_map[cid]["total"] += amount
            aging["summary"]["total"] += amount

        aging["customers"] = list(customer_map.values())
        return aging

    def get_over_limit_customers(self) -> List[Dict]:
        """الحصول على العملاء المتجاوزين للسقف الائتماني"""
        rows = self.db.fetch_all("""
            SELECT id, name, credit_limit, current_balance,
                   (current_balance - credit_limit) as over_amount
            FROM customers
            WHERE credit_limit > 0
              AND current_balance > credit_limit
              AND is_active = 1
              AND (is_deleted = 0 OR is_deleted IS NULL)
            ORDER BY over_amount DESC
        """)
        return [dict(r) for r in rows] if rows else []
