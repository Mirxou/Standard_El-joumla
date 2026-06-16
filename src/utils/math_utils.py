#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات الحسابات المالية الدقيقة - Financial Math Utilities
استخدام Decimal بدلاً من float لضمان الدقة المحاسبية

المشكلة: استخدام float في المال يسبب مشاكل التقريب العشرية
الحل: استخدام Decimal في جميع حسابات الفواتير
"""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Union


def to_decimal(value: Union[str, int, float, Decimal, None]) -> Decimal:
    """
    تحويل آمن لأي قيمة إلى Decimal
    يدعم النصوص التي تحتوي على عملات مثل "100.00 د.ج"

    Args:
        value: القيمة المراد تحويلها (str, int, float, Decimal, None)

    Returns:
        Decimal: القيمة كـ Decimal (0.00 إذا فشل التحويل)

    Examples:
        >>> to_decimal("100.50")
        Decimal('100.50')
        >>> to_decimal(100.5)
        Decimal('100.5')
        >>> to_decimal("100.00 د.ج")
        Decimal('100.00')
        >>> to_decimal(None)
        Decimal('0.00')
    """
    if value is None:
        return Decimal("0.00")

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value))

    if isinstance(value, str):
        # 🔥 CRITICAL FIX: استخراج الأرقام باستخدام pattern ذكي
        # Pattern: -?\d+\.?\d* يجد:
        # - علامة سالبة اختيارية في البداية
        # - رقم واحد أو أكثر
        # - نقطة اختيارية
        # - أرقام بعد النقطة (اختيارية)

        # إزالة الفواصل (للتنسيق العربي مثل 1,234.56)
        value_no_commas = value.replace(",", "").replace("،", "")  # دعم الفاصلة العربية أيضاً

        # البحث عن نمط رقم (مع أو بدون نقطة عشرية)
        matches = re.findall(r"-?\d+\.?\d*", value_no_commas)

        if matches:
            # أخذ أول match (عادة هو الرقم الكامل)
            clean_value = matches[0]
        else:
            # Fallback: استخراج الأرقام والنقطة فقط
            clean_value = re.sub(r"[^\d.]", "", value_no_commas)
            # إزالة النقاط المكررة (الاحتفاظ بنقطة واحدة فقط)
            if clean_value.count(".") > 1:
                # إذا كان هناك أكثر من نقطة، نأخذ الجزء الأول والثاني فقط
                parts = clean_value.split(".")
                clean_value = ".".join(parts[:2])

        # التحقق من أن القيمة ليست فارغة
        if not clean_value or clean_value == "-" or clean_value == ".":
            return Decimal("0.00")

        try:
            return Decimal(clean_value)
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    try:
        # محاولة أخيرة للتحويل
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


def calculate_line_total(
    price: Union[str, int, float, Decimal],
    quantity: Union[str, int, float, Decimal],
    discount: Union[str, int, float, Decimal] = 0,
    tax_rate: Union[str, int, float, Decimal] = 0,
) -> Decimal:
    """
    حساب إجمالي السطر بدقة محاسبية

    الخطوات:
    1. حساب الإجمالي الأولي (السعر × الكمية)
    2. تطبيق الخصم
    3. تطبيق الضريبة
    4. التقريب لعملتين عشريتين (قاعدة البنوك)

    Args:
        price: سعر الوحدة
        quantity: الكمية
        discount: مبلغ الخصم (اختياري)
        tax_rate: نسبة الضريبة (اختياري، كنسبة مئوية)

    Returns:
        Decimal: الإجمالي النهائي بعد الخصم والضريبة

    Examples:
        >>> calculate_line_total(100, 2, 10, 15)
        Decimal('207.00')
        >>> calculate_line_total("100.50", "2.5", "5.25", "10")
        Decimal('264.19')
    """
    # تحويل جميع القيم إلى Decimal
    d_price = to_decimal(price)
    d_qty = to_decimal(quantity)
    d_discount = to_decimal(discount)
    d_tax_rate = to_decimal(tax_rate)

    # 1. الإجمالي الأولي
    subtotal = d_price * d_qty

    # 2. تطبيق الخصم
    after_discount = subtotal - d_discount

    # التأكد من عدم وجود قيم سالبة
    if after_discount < 0:
        after_discount = Decimal("0.00")

    # 3. تطبيق الضريبة
    tax_amount = after_discount * (d_tax_rate / Decimal("100"))
    final_total = after_discount + tax_amount

    # 4. التقريب لعملتين عشريتين (قاعدة البنوك: ROUND_HALF_UP)
    return final_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_subtotal(items: list) -> Decimal:
    """
    حساب الإجمالي الفرعي لجميع العناصر

    Args:
        items: قائمة العناصر (يمكن أن تكون Decimal مباشرة أو dicts/objects مع 'total')

    Returns:
        Decimal: الإجمالي الفرعي
    """
    subtotal = Decimal("0.00")

    for item in items:
        # إذا كان Decimal مباشرة
        if isinstance(item, Decimal):
            subtotal += item
        # إذا كان dict
        elif isinstance(item, dict):
            total = item.get("total") or item.get("total_price") or item.get("line_total") or 0
            subtotal += to_decimal(total)
        # إذا كان object
        elif hasattr(item, "total") or hasattr(item, "total_price") or hasattr(item, "line_total"):
            total = (
                getattr(item, "total", None)
                or getattr(item, "total_price", None)
                or getattr(item, "line_total", None)
                or 0
            )
            subtotal += to_decimal(total)
        # أي نوع آخر (int, float, str)
        else:
            subtotal += to_decimal(item)

    return subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_discount_amount(
    subtotal: Union[str, int, float, Decimal],
    discount: Union[str, int, float, Decimal] = 0,
    is_percentage: bool = False,
    discount_percentage: Union[str, int, float, Decimal] = 0,
    discount_amount: Union[str, int, float, Decimal] = 0,
) -> Decimal:
    """
    حساب مبلغ الخصم (إما نسبة مئوية أو مبلغ ثابت)

    Args:
        subtotal: الإجمالي الفرعي
        discount: قيمة الخصم (يُستخدم مع is_percentage)
        is_percentage: إذا كان True، discount هو نسبة مئوية، وإلا هو مبلغ ثابت
        discount_percentage: نسبة الخصم (كنسبة مئوية) - للتوافق مع الكود القديم
        discount_amount: مبلغ الخصم الثابت - للتوافق مع الكود القديم

    Returns:
        Decimal: مبلغ الخصم
    """
    d_subtotal = to_decimal(subtotal)
    d_discount = to_decimal(discount)
    d_percentage = to_decimal(discount_percentage)
    d_amount = to_decimal(discount_amount)

    # إذا تم تمرير discount_percentage أو discount_amount (الكود القديم)
    if d_amount > 0:
        return min(d_amount, d_subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if d_percentage > 0:
        discount = d_subtotal * (d_percentage / Decimal("100"))
        return discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # الكود الجديد: استخدام discount مع is_percentage
    if is_percentage:
        # discount هو نسبة مئوية
        discount_value = d_subtotal * (d_discount / Decimal("100"))
        return discount_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        # discount هو مبلغ ثابت
        return min(d_discount, d_subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_tax_amount(
    subtotal: Union[str, int, float, Decimal],
    discount_amount: Union[str, int, float, Decimal] = 0,
    tax_rate: Union[str, int, float, Decimal] = 0,
) -> Decimal:
    """
    حساب مبلغ الضريبة

    Args:
        subtotal: الإجمالي الفرعي (قبل الخصم)
        discount_amount: مبلغ الخصم (يُطرح من subtotal قبل حساب الضريبة)
        tax_rate: نسبة الضريبة (كنسبة مئوية أو كـ Decimal مثل 0.15 لـ 15%)

    Returns:
        Decimal: مبلغ الضريبة
    """
    d_subtotal = to_decimal(subtotal)
    d_discount = to_decimal(discount_amount)
    d_tax_rate = to_decimal(tax_rate)

    # حساب المبلغ الخاضع للضريبة (بعد الخصم)
    taxable_amount = d_subtotal - d_discount
    if taxable_amount < 0:
        taxable_amount = Decimal("0.00")

    if d_tax_rate <= 0:
        return Decimal("0.00")

    # إذا كان tax_rate < 1، افترض أنه نسبة عشرية (0.15 = 15%)
    # وإلا افترض أنه نسبة مئوية (15 = 15%)
    if d_tax_rate < 1:
        tax = taxable_amount * d_tax_rate
    else:
        tax = taxable_amount * (d_tax_rate / Decimal("100"))

    return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_grand_total(
    subtotal: Union[str, int, float, Decimal],
    discount: Union[str, int, float, Decimal] = 0,
    tax: Union[str, int, float, Decimal] = 0,
) -> Decimal:
    """
    حساب الإجمالي النهائي

    Args:
        subtotal: الإجمالي الفرعي
        discount: مبلغ الخصم
        tax: مبلغ الضريبة

    Returns:
        Decimal: الإجمالي النهائي
    """
    d_subtotal = to_decimal(subtotal)
    d_discount = to_decimal(discount)
    d_tax = to_decimal(tax)

    total = d_subtotal - d_discount + d_tax

    # التأكد من عدم وجود قيم سالبة
    if total < 0:
        total = Decimal("0.00")

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_currency(
    amount: Union[str, int, float, Decimal],
    currency_symbol: str = "دج",
    decimal_places: int = 2,
) -> str:
    """
    تنسيق المبلغ كعملة

    Args:
        amount: المبلغ
        currency_symbol: رمز العملة (افتراضي: "دج")
        decimal_places: عدد الأرقام العشرية (افتراضي: 2)

    Returns:
        str: المبلغ المنسق

    Examples:
        >>> format_currency(1000.5)
        '1,000.50 دج'
        >>> format_currency("1234.567", "USD", 2)
        '1,234.57 USD'
    """
    d_amount = to_decimal(amount)

    # التقريب
    rounded = d_amount.quantize(Decimal("0." + "0" * decimal_places), rounding=ROUND_HALF_UP)

    # التنسيق مع فواصل الآلاف
    formatted = f"{rounded:,.{decimal_places}f}"

    return f"{formatted} {currency_symbol}"


def safe_divide(
    numerator: Union[str, int, float, Decimal],
    denominator: Union[str, int, float, Decimal],
    default: Decimal = Decimal("0.00"),
) -> Decimal:
    """
    قسمة آمنة (تجنب القسمة على صفر)

    Args:
        numerator: البسط
        denominator: المقام
        default: القيمة الافتراضية في حالة القسمة على صفر

    Returns:
        Decimal: نتيجة القسمة أو القيمة الافتراضية
    """
    d_numerator = to_decimal(numerator)
    d_denominator = to_decimal(denominator)

    if d_denominator == 0:
        return default

    return (d_numerator / d_denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
