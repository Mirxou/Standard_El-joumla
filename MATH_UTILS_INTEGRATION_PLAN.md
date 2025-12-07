# 🔢 خطة دمج Math Utils في النظام

## الهدف
استبدال جميع العمليات الحسابية باستخدام `float` بـ `Decimal` من `math_utils` لضمان الدقة المحاسبية.

---

## 📍 الأماكن التي تحتاج إلى التعديل

### 1. **`src/models/sale.py`** (أولوية عالية)

#### أ) `SaleItem.calculate_total()` - السطر 60-74
**الكود الحالي:**
```python
def calculate_total(self):
    """حساب المجموع"""
    subtotal = self.unit_price * self.quantity
    
    # خصم
    if self.discount_percentage > 0:
        self.discount_amount = subtotal * (self.discount_percentage / 100)
    
    after_discount = subtotal - self.discount_amount
    
    # ضريبة
    if self.tax_percentage > 0:
        self.tax_amount = after_discount * (self.tax_percentage / 100)
    
    self.total_amount = after_discount + self.tax_amount
```

**الكود الجديد:**
```python
def calculate_total(self):
    """حساب المجموع"""
    from src.utils.math_utils import calculate_line_total, to_decimal
    
    # استخدام الدالة المركزية للحساب
    self.total_amount = calculate_line_total(
        price=self.unit_price,
        quantity=self.quantity,
        discount=self.discount_amount,
        tax_rate=self.tax_percentage
    )
    
    # حساب الخصم إذا كان نسبة مئوية
    if self.discount_percentage > 0:
        from src.utils.math_utils import calculate_discount_amount
        subtotal = to_decimal(self.unit_price) * to_decimal(self.quantity)
        self.discount_amount = calculate_discount_amount(
            subtotal=subtotal,
            discount_percentage=self.discount_percentage
        )
    
    # حساب الضريبة
    if self.tax_percentage > 0:
        from src.utils.math_utils import calculate_tax_amount
        subtotal = to_decimal(self.unit_price) * to_decimal(self.quantity)
        after_discount = subtotal - self.discount_amount
        self.tax_amount = calculate_tax_amount(
            subtotal=after_discount,
            tax_rate=self.tax_percentage
        )
```

#### ب) `Sale.calculate_totals()` - السطر 147-161
**الكود الحالي:**
```python
def calculate_totals(self):
    """حساب المجاميع"""
    self.subtotal = sum(item.unit_price * item.quantity for item in self.items)
    
    # خصم إجمالي
    if self.discount_percentage > 0:
        self.discount_amount = self.subtotal * (self.discount_percentage / 100)
    
    after_discount = self.subtotal - self.discount_amount
    
    # ضريبة إجمالية
    if self.tax_percentage > 0:
        self.tax_amount = after_discount * (self.tax_percentage / 100)
    
    self.total_amount = after_discount + self.tax_amount
    self.remaining_amount = self.total_amount - self.paid_amount
```

**الكود الجديد:**
```python
def calculate_totals(self):
    """حساب المجاميع"""
    from src.utils.math_utils import calculate_subtotal, calculate_discount_amount, calculate_tax_amount, calculate_grand_total, to_decimal
    
    # حساب الإجمالي الفرعي
    self.subtotal = calculate_subtotal(self.items)
    
    # حساب الخصم
    self.discount_amount = calculate_discount_amount(
        subtotal=self.subtotal,
        discount_percentage=self.discount_percentage,
        discount_amount=self.discount_amount
    )
    
    # حساب الضريبة
    after_discount = self.subtotal - self.discount_amount
    self.tax_amount = calculate_tax_amount(
        subtotal=after_discount,
        tax_rate=self.tax_percentage
    )
    
    # حساب الإجمالي النهائي
    self.total_amount = calculate_grand_total(
        subtotal=self.subtotal,
        discount=self.discount_amount,
        tax=self.tax_amount
    )
    
    self.remaining_amount = self.total_amount - to_decimal(self.paid_amount)
```

---

### 2. **`src/ui/dialogs/sales_dialog.py`** (أولوية عالية)

#### أ) `calculate_totals()` - السطر 968-999
**الكود الحالي:**
```python
def calculate_totals(self):
    """حساب المجاميع"""
    try:
        # المجموع الفرعي
        subtotal = sum(item.total_price for item in self.sale_items)
        
        # الخصم
        discount = Decimal(str(self.discount_spin.value()))
        if self.discount_percent_button.isChecked():
            # خصم بالنسبة المئوية
            discount = subtotal * (discount / 100)
        
        # المجموع بعد الخصم
        after_discount = subtotal - discount
        
        # الضريبة
        tax_rate = Decimal(str(self.tax_rate_spin.value())) / 100
        tax_amount = after_discount * tax_rate
        
        # المجموع الكلي
        total = after_discount + tax_amount
```

**الكود الجديد:**
```python
def calculate_totals(self):
    """حساب المجاميع"""
    try:
        from src.utils.math_utils import calculate_subtotal, calculate_discount_amount, calculate_tax_amount, calculate_grand_total, to_decimal
        
        # المجموع الفرعي
        subtotal = calculate_subtotal(self.sale_items)
        
        # الخصم
        discount_value = to_decimal(self.discount_spin.value())
        if self.discount_percent_button.isChecked():
            discount = calculate_discount_amount(
                subtotal=subtotal,
                discount_percentage=discount_value
            )
        else:
            discount = discount_value
        
        # المجموع بعد الخصم
        after_discount = subtotal - discount
        
        # الضريبة
        tax_rate = to_decimal(self.tax_rate_spin.value())
        tax_amount = calculate_tax_amount(
            subtotal=after_discount,
            tax_rate=tax_rate
        )
        
        # المجموع الكلي
        total = calculate_grand_total(
            subtotal=subtotal,
            discount=discount,
            tax=tax_amount
        )
```

#### ب) أماكن أخرى في `sales_dialog.py`
- السطر 816: `existing_item.total_price = existing_item.unit_price * existing_item.quantity - existing_item.discount_amount`
- السطر 924: `item.total_price = item.unit_price * item.quantity - item.discount_amount`
- السطر 938: `item.total_price = item.unit_price * item.quantity - item.discount_amount`

**يجب استبدالها بـ:**
```python
from src.utils.math_utils import calculate_line_total

item.total_price = calculate_line_total(
    price=item.unit_price,
    quantity=item.quantity,
    discount=item.discount_amount,
    tax_rate=0  # أو tax_rate إذا كان موجوداً
)
```

---

### 3. **`src/models/purchase.py`** (أولوية متوسطة)

- `PurchaseItem.calculate_totals()` - مشابه لـ `SaleItem.calculate_total()`
- `Purchase.calculate_totals()` - مشابه لـ `Sale.calculate_totals()`

---

### 4. **أماكن أخرى** (أولوية منخفضة)

- `src/models/quote.py` - `QuoteItem.calculate_total()`
- `src/models/return_invoice.py` - حسابات المرتجعات
- `src/models/purchase_order.py` - حسابات أوامر الشراء

---

## ⚠️ ملاحظات مهمة

1. **التحويل من Decimal إلى float:**
   - عند الحفظ في قاعدة البيانات، قد نحتاج `float(value)`
   - استخدم `float(to_decimal(value))` بدلاً من `float(value)` مباشرة

2. **الاختبار:**
   - بعد كل تعديل، اختبر الحسابات
   - تأكد من أن النتائج متطابقة (أو أكثر دقة)

3. **الأداء:**
   - `Decimal` أبطأ قليلاً من `float`، لكن الدقة أهم في الحسابات المالية

---

## 📝 خطة التنفيذ

1. ✅ **المرحلة 1:** اختبار الإشارات (قبل الدمج)
2. ⏳ **المرحلة 2:** دمج `math_utils` في `SaleItem.calculate_total()`
3. ⏳ **المرحلة 3:** دمج `math_utils` في `Sale.calculate_totals()`
4. ⏳ **المرحلة 4:** دمج `math_utils` في `SalesDialog.calculate_totals()`
5. ⏳ **المرحلة 5:** دمج `math_utils` في أماكن أخرى في `sales_dialog.py`
6. ⏳ **المرحلة 6:** اختبار شامل للحسابات
7. ⏳ **المرحلة 7:** دمج في `Purchase` و `Quote` (اختياري)

---

## 🎯 النتيجة المتوقعة

بعد الدمج:
- ✅ دقة محاسبية 100% (لا مشاكل تقريب)
- ✅ حسابات متسقة في جميع أنحاء النظام
- ✅ سهولة الصيانة (كود مركزي)

