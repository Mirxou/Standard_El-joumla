#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الباركود - Barcode Service
توليد الباركود (EAN-13 / Code128) والتحقق منه وربطه بالمنتجات وطباعة الملصقات.

GAP-1.3 (SRS_ARCHITECTURE.md §2.4): 1D Barcode Generation & Scanner Integration.

Features:
- توليد EAN-13 حتمي (deterministic) لنطاق المتجر الداخلي (prefix "200" حسب اتفاق GS1)
  مع رقم تحقق صحيح + أرقام بديلة (variants) عند تعارض UNIQUE.
- التحقق الكامل من صحة EAN-13 (13 خانة + رقم تحقق).
- تحويل الباركود الممسوح إلى منتج (exact lookup + خريطة عكسية للنطاق الداخلي مع حماية
  من الباركود القديم/الراكد stale-scan guard).
- توليد صور Code128 (Set B) عبر pillow فقط عند الطلب (lazy import) — بدون أي اعتماد
  إلزامي على مكتبات خارجية لعمل الخدمة كاملة عدا الصور.
- بناء نص ملصق الطباعة (30x20mm / 50x25mm) وإرساله لطابعة الملصقات المعدة في
  جدول hardware_config (connection_type='file') مع dry-run آمن.

Money values are handled as ``Decimal`` everywhere. All third-party imports
(PIL/pyserial) are lazy so this module imports with zero external dependencies.

Key Features:
- Deterministic in-store EAN-13 generation (GS1 "200" internal range) with a valid
  check digit, plus variant digits for UNIQUE collisions.
- Full EAN-13 validation (13 digits + correct check digit).
- Scan resolution (exact match + internal reverse map with stale-scan guard).
- Code128 (Set B) image rendering via pillow (lazy import only).
- Label text building (30x20mm / 50x25mm) and printing to the configured
  label printer from ``hardware_config`` (connection_type='file') with safe dry-run.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logger import setup_logger

# ────────────────────────── الثوابت / Constants ──────────────────────────

#: بادئة النطاق الداخلي للمتجر حسب اتفاق GS1 (200-299 محجوزة للاستخدام الداخلي).
#: GS1 in-store internal range prefix ("200".."299" reserved for internal use).
IN_STORE_PREFIX: str = "200"

#: طول جسم EAN-13 قبل رقم التحقق (12 خانة) / EAN-13 body length before the check digit.
EAN13_BODY_LENGTH: int = 12

#: أقصى معرف منتج يُخزَّن داخل الجسم (8 خانات بعد البادئة) — ما بعده يستخدم hash fallback.
#: Max product id storable in the body (8 digits); larger ids use a hash fallback.
MAX_PRODUCT_ID_IN_BODY: int = 99_999_999

#: عدد المحاولات القصوى لأرقام البديلة عند تعارض UNIQUE / Max variant attempts on collision.
MAX_ASSIGN_ATTEMPTS: int = 5

# ── جدول أنماط Code128 الرسمي (107 قيمة، كل نمط 11 وحدة كسلسلة بت) ──
# Official ISO/IEC 15417 Code128 pattern table (values 0..106). Values 0..105 are
# 11-module patterns (bars='1', spaces='0'); value 106 (STOP) is 13 modules and
# includes the 2-module termination bar. Verified character-exact against an
# independent reference implementation.
CODE128_START_B: int = 104
CODE128_STOP: int = 106
CODE128_MODULUS: int = 103
CODE128_QUIET_MODULES: int = 10

CODE128_PATTERNS: Tuple[str, ...] = (
    "11011001100", "11001101100", "11001100110", "10010011000",
    "10010001100", "10001001100", "10011001000", "10011000100",
    "10001100100", "11001001000", "11001000100", "11000100100",
    "10110011100", "10011011100", "10011001110", "10111001100",
    "10011101100", "10011100110", "11001110010", "11001011100",
    "11001001110", "11011100100", "11001110100", "11101101110",
    "11101001100", "11100101100", "11100100110", "11101100100",
    "11100110100", "11100110010", "11011011000", "11011000110",
    "11000110110", "10100011000", "10001011000", "10001000110",
    "10110001000", "10001101000", "10001100010", "11010001000",
    "11000101000", "11000100010", "10110111000", "10110001110",
    "10001101110", "10111011000", "10111000110", "10001110110",
    "11101110110", "11010001110", "11000101110", "11011101000",
    "11011100010", "11011101110", "11101011000", "11101000110",
    "11100010110", "11101101000", "11101100010", "11100011010",
    "11101111010", "11001000010", "11110001010", "10100110000",
    "10100001100", "10010110000", "10010000110", "10000101100",
    "10000100110", "10110010000", "10110000100", "10011010000",
    "10011000010", "10000110100", "10000110010", "11000010010",
    "11001010000", "11110111010", "11000010100", "10001111010",
    "10100111100", "10010111100", "10010011110", "10111100100",
    "10011110100", "10011110010", "11110100100", "11110010100",
    "11110010010", "11011011110", "11011110110", "11110110110",
    "10101111000", "10100011110", "10001011110", "10111101000",
    "10111100010", "11110101000", "11110100010", "10111011110",
    "10111101110", "11101011110", "11110101110", "11010000100",
    "11010010000", "11010011100", "1100011101011",
)

assert len(CODE128_PATTERNS) == 107, "Code128 table must contain exactly 107 patterns"
assert CODE128_PATTERNS[CODE128_START_B] == "11010010000", "START-B pattern mismatch"
assert CODE128_PATTERNS[CODE128_STOP] == "1100011101011", "STOP pattern mismatch"

#: مواصفات ملصقات الطباعة المدعومة / Supported label formats.
#: name_max = أقصى طول لاسم المنتج في هذا المقاس.
LABEL_FORMATS: Dict[str, Dict[str, int]] = {
    "30x20mm": {"name_max": 20, "barcode_max": 13},
    "50x25mm": {"name_max": 34, "barcode_max": 20},
}


# ────────────────────────── الاستثناءات / Exceptions ──────────────────────────

class BarcodeCollisionError(Exception):
    """تعارض الباركود: كل المحاولات اصطدمت بباركود منتج آخر.

    Raised when barcode assignment fails after exhausting all variant
    attempts because every candidate collides with another product's
    barcode (UNIQUE constraint).
    """


# ─────────────────────── دوال منطقية خالصة / Pure helpers ───────────────────────

def ean13_check_digit(body_12: str) -> int:
    """حساب رقم التحقق لجسم EAN-13 المكوَّن من 12 خانة.

    الموازين حسب مواصفة EAN-13: المواضع الفردية (1، 3، 5...) وزنها 1،
    والزوجية (2، 4، 6...) وزنها 3؛ ثم (10 - المجموع % 10) % 10.

    Compute the EAN-13 check digit for a 12-digit body.
    Weights: odd positions (1st, 3rd, ...) = 1, even positions = 3;
    check = (10 - sum % 10) % 10.

    Raises:
        ValueError: إذا لم يكن الجسم 12 خانة رقمية / if body is not 12 digits.
    """
    body = str(body_12)
    if len(body) != 12 or not body.isdigit():
        raise ValueError("EAN-13 body must be exactly 12 digits / يجب أن يكون الجسم 12 خانة رقمية")
    total = 0
    for index, char in enumerate(body):
        digit = int(char)
        total += digit if index % 2 == 0 else digit * 3
    return (10 - total % 10) % 10


def is_valid_ean13(barcode: str) -> bool:
    """التحقق الكامل من باركود EAN-13 (13 خانة رقمية + رقم تحقق صحيح).

    Full EAN-13 validation: exactly 13 digits with a correct check digit.
    """
    if not isinstance(barcode, str):
        return False
    value = barcode.strip()
    if len(value) != 13 or not value.isdigit():
        return False
    try:
        return ean13_check_digit(value[:12]) == int(value[12])
    except ValueError:
        return False


def code128_encode(value: str) -> List[int]:
    """ترميز نص إلى قائمة رموز Code128 (Set B) خالصة — للفحص والتوليد.

    Pure Code128 (Set B) encoder: returns the symbol-value sequence
    [START_B(104), data..., checksum, STOP(106)] where each data symbol
    is ``ord(char) - 32`` for chars 32..126 and
    ``checksum = (104 + Σ(i × value_i)) % 103`` (i starts at 1).

    Raises:
        ValueError: على نص فارغ أو محارف خارج 32..126 / on empty value
            or characters outside ASCII 32..126.
    """
    if value is None:
        raise ValueError("لا يمكن ترميز قيمة None / cannot encode None")
    text = str(value)
    if not text:
        raise ValueError("لا يمكن ترميز نص فارغ / cannot encode an empty value")
    for char in text:
        code = ord(char)
        if not (32 <= code <= 126):
            raise ValueError(
                f"Code128 Set B لا يدعم المحرف {char!r} (يجب أن يكون بين 32 و 126) / "
                f"Code128 Set B cannot encode {char!r} (must be ASCII 32..126)"
            )
    symbols: List[int] = [CODE128_START_B] + [ord(char) - 32 for char in text]
    checksum = CODE128_START_B
    for position, symbol in enumerate(symbols[1:], start=1):
        checksum += position * symbol
    symbols.append(checksum % CODE128_MODULUS)
    symbols.append(CODE128_STOP)
    return symbols


def code128_bitstream(value: str) -> str:
    """ترميز نص إلى سلسلة بتات Code128 (bars='1', spaces='0') — بدون الوحدات الهامشية.

    Encode text into the raw Code128 bit string (11-module patterns
    concatenated, STOP included; quiet zones are added by the renderer).
    """
    return "".join(CODE128_PATTERNS[symbol] for symbol in code128_encode(value))


def _as_decimal(value: Any) -> Decimal:
    """تحويل آمن إلى Decimal (المال دائماً Decimal) / Safe conversion to Decimal."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


# ──────────────────────────── الخدمة / Service ────────────────────────────

class BarcodeService:
    """خدمة توليد الباركود وربطه بالمنتجات وقراءة الملصقات.

    Barcode generation/validation/resolution + label printing. Depends only on
    ``DatabaseManager``; PIL is imported lazily inside :meth:`generate_code128_image`.

    Usage:
        svc = BarcodeService(db_manager)
        barcode = svc.assign_barcode_to_product(product_id)   # يخزَّن في products.barcode
        product = svc.resolve_barcode(scanned_value)          # dict أو None
    """

    def __init__(self, db_manager, logger=None):
        """تهيئة الخدمة.

        Args:
            db_manager: مدير قاعدة البيانات (DatabaseManager) — مطلوب.
            logger: مسجّل اختياري / optional logger.
        """
        if db_manager is None:
            raise ValueError("BarcodeService requires a db_manager / يجب تمرير مدير قاعدة البيانات")
        self.db = db_manager
        self.logger = logger or setup_logger(__name__)
        #: آخر نص ملصق تم "طباعته" (يُستخدم في dry-run والاختبارات).
        self.last_output: Optional[str] = None

    # ────────────────── توليد EAN-13 / EAN-13 generation ──────────────────

    @staticmethod
    def _ean13_body(product_id: int, variant: int = 0) -> str:
        """بناء جسم EAN-13 من 12 خانة: "200" + معرف المنتج (8 خانات) + رقم بديل.

        Layout: "200" (GS1 internal prefix) + zero-padded product id (8 digits,
        hashed modulo 10^8 when id > 99,999,999) + variant digit (0..9) used for
        collision handling. Deterministic: same inputs always yield the same body.

        Raises:
            ValueError: على معرف سالب أو بديل خارج 0..9.
        """
        pid = int(product_id)
        if pid < 0:
            raise ValueError("معرف المنتج يجب أن يكون موجباً / product_id must be non-negative")
        if pid > MAX_PRODUCT_ID_IN_BODY:
            # Hash fallback حتمي: نفس المعرف يعطي نفس القيمة دائماً.
            digest = hashlib.sha256(str(pid).encode("utf-8")).hexdigest()
            pid = int(digest, 16) % (MAX_PRODUCT_ID_IN_BODY + 1)
        if not 0 <= int(variant) <= 9:
            raise ValueError("الرقم البديل يجب أن يكون بين 0 و 9 / variant must be a digit 0..9")
        return f"{IN_STORE_PREFIX}{pid:08d}{int(variant)}"

    def generate_ean13(self, product_id: int) -> str:
        """توليد باركود EAN-13 حتمي لمعرف منتج (نفس المعرف ⇒ نفس الباركود دائماً).

        Deterministic EAN-13 for a product id (idempotent): body = "200" +
        8-digit id + variant 0, followed by the correct check digit.
        """
        body = self._ean13_body(product_id, variant=0)
        return body + str(ean13_check_digit(body))

    def generate_ean13_variant(self, product_id: int, variant: int = 0) -> str:
        """توليد باركود EAN-13 برقم بديل محدد (يُستخدم عند تعارض UNIQUE).

        EAN-13 with an explicit variant digit (0..9); variants are the
        collision-handling mechanism of :meth:`assign_barcode_to_product`.
        """
        body = self._ean13_body(product_id, variant=variant)
        return body + str(ean13_check_digit(body))

    # ────────────── ربط الباركود بالمنتج / Barcode assignment ──────────────

    def assign_barcode_to_product(self, product_id: int, barcode: Optional[str] = None) -> str:
        """ربط باركود بمنتج وتخزينه في products.barcode داخل معاملة.

        If ``barcode`` is None a deterministic in-store EAN-13 is generated;
        on UNIQUE collision the generator retries with variant digits 1..4
        (up to :data:`MAX_ASSIGN_ATTEMPTS` attempts) before raising
        :class:`BarcodeCollisionError`. An explicitly provided barcode is
        stored as-is and raises immediately on collision (never silently
        mutated or overwriting another product).

        Args:
            product_id: معرف المنتج / target product id.
            barcode: باركود اختياري صريح / optional explicit barcode value.

        Returns:
            str: الباركود النهائي المخزَّن / the final persisted barcode.

        Raises:
            ValueError: إذا لم يوجد المنتج أو كان الباركود الفارغ.
            BarcodeCollisionError: إذا اصطدمت كل المحاولات بمنتج آخر.
        """
        pid = int(product_id)
        existing = self.db.fetch_one("SELECT id FROM products WHERE id = ?", (pid,))
        if existing is None:
            raise ValueError(f"المنتج {pid} غير موجود / product {pid} not found")

        if barcode is not None:
            candidate = str(barcode).strip()
            if not candidate:
                raise ValueError("لا يمكن ربط باركود فارغ / barcode cannot be empty")
            candidates: List[str] = [candidate]
        else:
            candidates = [
                self.generate_ean13_variant(pid, variant)
                for variant in range(MAX_ASSIGN_ATTEMPTS)
            ]

        last_error: Optional[Exception] = None
        for attempt, candidate in enumerate(candidates, start=1):
            try:
                with self.db.transaction():
                    updated = self.db.execute_non_query(
                        "UPDATE products SET barcode = ?, updated_at = CURRENT_TIMESTAMP "
                        "WHERE id = ?",
                        (candidate, pid),
                    )
                if updated:
                    self.logger.info(
                        f"تم ربط الباركود {candidate} بالمنتج {pid} "
                        f"(محاولة {attempt}/{len(candidates)})"
                    )
                    return candidate
                # UPDATE لم يؤثر على أي صف (نافذة ضيقة: حُذف المنتج للتو).
                raise ValueError(f"المنتج {pid} غير موجود / product {pid} not found")
            except sqlite3.IntegrityError as exc:
                # تعارض UNIQUE مع منتج آخر → جرّب الرقم البديل التالي.
                last_error = exc
                self.logger.warning(
                    f"تعارض الباركود {candidate} مع منتج آخر — محاولة بديل "
                    f"({attempt}/{len(candidates)})"
                )
                continue
        raise BarcodeCollisionError(
            f"كل محاولات الباركود للمنتج {pid} اصطدمت بمنتجات أخرى "
            f"({len(candidates)} محاولات) / all {len(candidates)} barcode attempts "
            f"collided for product {pid}"
        ) from last_error

    # ─────────────────────── التحقق / Validation ───────────────────────

    def validate_ean13(self, barcode: str) -> bool:
        """التحقق من باركود EAN-13 (13 خانة رقمية + رقم تحقق صحيح).

        Validates an EAN-13 barcode (13 digits + correct check digit).
        Accepts None / non-string / wrong length gracefully (False).
        """
        return is_valid_ean13(barcode)

    # ─────────────────────── القراءة / Resolution ───────────────────────

    _PRODUCT_COLUMNS = "id, name, name_en, barcode, selling_price, cost_price, unit, current_stock"

    def resolve_barcode(self, barcode: Any) -> Optional[Dict[str, Any]]:
        """تحويل باركود ممسوح إلى قاموس منتج (أو None إذا لم يُطابق).

        Resolution strategy:
        1. Exact match ``WHERE barcode = ?``.
        2. If the value is a valid in-store EAN-13 (prefix "200"), reverse-map
           it: strip the prefix, parse the embedded product id (8 digits) and
           verify the product exists **and** its stored barcode equals the
           scanned value (stale-scan guard against re-used/renumbered labels).

        Money fields (``selling_price``/``cost_price``) are normalized to
        :class:`Decimal`. None/empty/malformed input returns None.

        Args:
            barcode: الباركود الممسوح / scanned value (str or int).

        Returns:
            Optional[Dict[str, Any]]: قاموس المنتج أو None.
        """
        if barcode is None:
            return None
        value = str(barcode).strip()
        if not value:
            return None

        row = self.db.fetch_one(
            f"SELECT {self._PRODUCT_COLUMNS} FROM products WHERE barcode = ?",
            (value,),
        )
        if row is not None:
            return self._normalize_product(row)

        # الخريطة العكسية للنطاق الداخلي: "200" + معرف (8 خانات) + بديل + تحقق.
        if is_valid_ean13(value) and value.startswith(IN_STORE_PREFIX):
            try:
                embedded_pid = int(value[3:11])
            except ValueError:
                return None
            product = self.db.fetch_one(
                f"SELECT {self._PRODUCT_COLUMNS} FROM products WHERE id = ?",
                (embedded_pid,),
            )
            # حماية من الباركود الراكد: يجب أن يطابق المخزَّن فعلياً.
            if product is not None and str(product.get("barcode") or "").strip() == value:
                return self._normalize_product(product)
        return None

    @staticmethod
    def _normalize_product(row: Dict[str, Any]) -> Dict[str, Any]:
        """توحيد قاموس المنتج: المال Decimal وأرقام صحيحة / Normalize a product row."""
        product = dict(row)
        product["selling_price"] = _as_decimal(product.get("selling_price"))
        product["cost_price"] = _as_decimal(product.get("cost_price"))
        try:
            product["id"] = int(product.get("id"))
        except (TypeError, ValueError):
            pass
        try:
            product["current_stock"] = float(product.get("current_stock") or 0)
        except (TypeError, ValueError):
            product["current_stock"] = 0.0
        return product

    # ─────────────── توليد صور Code128 / Code128 image rendering ───────────────

    def generate_code128_image(self, value: str, width: int = 400, height: int = 120):
        """توليد صورة باركود Code128 (Set B) كقناة PIL grayscale.

        Renders a Code128-B symbol for ``value`` using the official pattern
        table (:data:`CODE128_PATTERNS`) with a 10-module quiet zone on each
        side, scaled to exactly ``(width, height)`` pixels.

        pillow is imported lazily — the rest of the service works without it.

        Args:
            value: القيمة المراد ترميزها (ASCII 32..126 فقط).
            width: عرض الصورة بالبكسل (يجب أن يستوعب كل الوحدات).
            height: ارتفاع الصورة بالبكسل.

        Returns:
            PIL.Image.Image: صورة وضع "L" (أبيض 255 / أسود 0).

        Raises:
            ImportError: إذا لم يكن pillow مثبتاً.
            ValueError: على قيمة فارغة/محارف غير مدعومة/أبعاد صغيرة جداً.
        """
        try:
            from PIL import Image, ImageDraw  # noqa: WPS433 — اعتماد كسول مقصود
        except ImportError as exc:  # pragma: no cover — يعتمد على البيئة
            raise ImportError(
                "ثبّت pillow لتوليد صور الباركود: pip install pillow"
            ) from exc

        bitstream = code128_bitstream(value)  # يتحقق من الفراغ/المحارف أيضاً
        width = int(width)
        height = int(height)
        total_modules = CODE128_QUIET_MODULES * 2 + len(bitstream)
        if width < total_modules or height < 1:
            raise ValueError(
                f"الأبعاد صغيرة جداً: تحتاج عرضاً ≥ {total_modules} بكسل "
                f"(الطلب {width}×{height})"
            )

        image = Image.new("L", (width, int(height)), 255)  # خلفية بيضاء
        draw = ImageDraw.Draw(image)
        module_width = width / total_modules
        offset = CODE128_QUIET_MODULES
        for index, bit in enumerate(bitstream):
            if bit != "1":
                continue
            x0 = int(round((offset + index) * module_width))
            x1 = int(round((offset + index + 1) * module_width))
            draw.rectangle([x0, 0, max(x0, x1 - 1), height - 1], fill=0)
        return image

    # ─────────────────────── الملصقات / Label printing ───────────────────────

    def build_label_text(self, product: Dict[str, Any], label_format: str = "30x20mm") -> str:
        """بناء تخطيط نصي لملصق باركود (اسم/سعر/باركود) حسب المقاس المطلوب.

        Builds the text layout of a barcode label: header with the format tag,
        product name (truncated per format), price line and barcode line.

        Supported formats: ``"30x20mm"`` (name ≤ 20 chars) و ``"50x25mm"``
        (name ≤ 34 chars).

        Raises:
            ValueError: على مقاس غير مدعوم / unsupported format.
        """
        fmt = str(label_format or "").strip().lower()
        config = LABEL_FORMATS.get(fmt)
        if config is None:
            supported = "، /, ".join(sorted(LABEL_FORMATS))
            raise ValueError(f"مقاس ملصق غير مدعوم: {label_format!r} (المدعوم: {supported})")

        name = str(product.get("name") or product.get("name_en") or "").strip()
        name = name[: config["name_max"]]
        price = _as_decimal(product.get("selling_price"))
        barcode = str(product.get("barcode") or "").strip()[: config["barcode_max"]]

        lines = [
            f"=== {fmt} ===",
            name,
            f"السعر/Price: {price:.2f}",
            barcode,
        ]
        return "\n".join(lines)

    def print_barcode_label(self, product_id: int, label_format: str = "30x20mm") -> bool:
        """طباعة ملصق باركود لمنتج على طابعة الملصقات المعدة في hardware_config.

        Resolves the product (auto-assigning a generated EAN-13 when the product
        has no barcode yet), builds the label text and hands it to
        :meth:`_write_to_label_printer`. Never raises: returns False on
        missing product / generation failure.

        Args:
            product_id: معرف المنتج / product id.
            label_format: مقاس الملصق ("30x20mm" أو "50x25mm").

        Returns:
            bool: True عند النجاح (بما فيها dry-run) / False عند الفشل.
        """
        try:
            pid = int(product_id)
            product = self.db.fetch_one(
                f"SELECT {self._PRODUCT_COLUMNS} FROM products WHERE id = ?", (pid,)
            )
            if product is None:
                self.logger.warning(f"تعذّرت طباعة الملصق: المنتج {pid} غير موجود")
                return False

            if not str(product.get("barcode") or "").strip():
                product["barcode"] = self.assign_barcode_to_product(pid)

            text = self.build_label_text(product, label_format)
            return self._write_to_label_printer(text)
        except BarcodeCollisionError as exc:
            self.logger.error(f"فشل توليد باركود للطباعة: {exc}")
            return False
        except (ValueError, sqlite3.Error) as exc:
            self.logger.error(f"خطأ أثناء طباعة الملصق للمنتج {product_id}: {exc}")
            return False

    # ──────────────── التواصل مع الطابعة / Printer transport ────────────────

    def _get_label_printer_config(self) -> Optional[Dict[str, Any]]:
        """قراءة إعدادات طابعة الملصقات من hardware_config (بأمان).

        Fetch the active label printer row; returns None when the table does
        not exist yet or no printer is configured (⇒ dry-run mode).
        """
        try:
            return self.db.fetch_one(
                "SELECT * FROM hardware_config "
                "WHERE device_type = 'label_printer' AND is_active = 1 "
                "ORDER BY is_default DESC, id DESC LIMIT 1"
            )
        except Exception:  # noqa: BLE001 — الجدول قد لا يكون موجوداً بعد
            return None

    def _write_to_label_printer(self, text: str) -> bool:
        """إرسال نص الملصق للطابعة — يدعم connection_type='file' فقط في هذه النسخة.

        Minimal self-contained writer: for ``connection_type='file'`` the label
        text is appended to the configured file path; any other connection type
        (usb/network/serial) or a missing config falls back to a safe dry-run
        that stores the payload in :attr:`last_output` and returns True.
        Never raises.
        """
        self.last_output = text
        config = self._get_label_printer_config()
        if config is not None:
            connection_type = str(config.get("connection_type") or "").strip().lower()
            params = config.get("connection_params")
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except (json.JSONDecodeError, TypeError):
                    params = {}
            params = params if isinstance(params, dict) else {}

            if connection_type == "file":
                path = str(
                    params.get("path") or params.get("file_path") or params.get("device_path") or ""
                ).strip()
                if path:
                    try:
                        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                        with open(path, "a", encoding="utf-8") as handle:
                            handle.write(text + "\n")
                        self.logger.info(f"تم إرسال الملصق إلى الملف {path}")
                        return True
                    except OSError as exc:
                        self.logger.warning(f"فشل الكتابة لملف الطابعة {path}: {exc}")
            else:
                self.logger.info(
                    f"نوع اتصال الطابعة {connection_type!r} غير مدعوم هنا — dry-run"
                )
        self.logger.info("طابعة الملصقات غير مهيأة — تخزين الملصق في last_output (dry-run)")
        return True
