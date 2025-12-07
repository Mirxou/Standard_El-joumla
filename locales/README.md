# ملفات الترجمة - Translation Files

## نظرة عامة

هذا المجلد يحتوي على ملفات الترجمة للتطبيق باللغتين العربية والإنجليزية.

## الملفات

- `ar.json` - الترجمة العربية (118 مفتاح)
- `en.json` - الترجمة الإنجليزية (118 مفتاح)
- `fr.json` - الترجمة الفرنسية (118 مفتاح) - جديد!
- `de.json` - الترجمة الألمانية (118 مفتاح) - جديد!
- `es.json` - الترجمة الإسبانية (118 مفتاح) - جديد!

## الاستخدام

### في Python (API)

```python
from src.utils.i18n_api import I18n

i18n = I18n(locales_dir="locales")

# الحصول على رسالة بالعربية (الافتراضية)
message = i18n.get_message("welcome")  # "مرحباً"

# الحصول على رسالة بالإنجليزية
message = i18n.get_message("welcome", locale="en")  # "Welcome"

# الحصول على رسالة بالفرنسية
message = i18n.get_message("welcome", locale="fr")  # "Bienvenue"

# الحصول على رسالة بالألمانية
message = i18n.get_message("welcome", locale="de")  # "Willkommen"

# الحصول على رسالة بالإسبانية
message = i18n.get_message("welcome", locale="es")  # "Bienvenido"

# رسالة مع متغيرات
message = i18n.get_message("order_created", order_id=123)
# العربية: "تم إنشاء الطلب 123 بنجاح"
# الإنجليزية: "Order 123 created successfully"
# الفرنسية: "Commande 123 créée avec succès"
# الألمانية: "Bestellung 123 erfolgreich erstellt"
# الإسبانية: "Pedido 123 creado exitosamente"

# الحصول على اللغات المتاحة
locales = i18n.get_available_locales()  # ["ar", "en", "fr", "de", "es"]

# التحقق من وجود لغة
if i18n.has_locale("fr"):
    message = i18n.get_message("welcome", locale="fr")
```

### في UI (PySide6)

```python
from src.utils.i18n import get_translation_manager

tm = get_translation_manager()

# الحصول على ترجمة
text = tm.t("welcome")  # "مرحباً"

# تغيير اللغة
tm.set_language(Language.ENGLISH)
text = tm.t("welcome")  # "Welcome"
```

## المفاتيح المتاحة

### الأساسية
- `app_title`, `welcome`, `login`, `logout`
- `username`, `password`

### الوحدات
- `dashboard`, `sales`, `purchases`, `inventory`
- `products`, `customers`, `suppliers`
- `reports`, `settings`, `orders`, `invoices`
- `quotes`, `returns`, `refunds`

### الإجراءات
- `save`, `delete`, `edit`, `add`
- `search`, `filter`, `export`, `import`, `print`
- `confirm`, `cancel`

### الرسائل
- `success`, `error`, `warning`, `info`
- `order_created`, `order_updated`, `order_not_found`
- `payment_received`, `refund_created`, `return_created`
- `stock_received`, `po_status_updated`

### الأخطاء
- `insufficient_privileges`, `authentication_failed`
- `invalid_token`, `rate_limit_exceeded`
- `validation_error`, `internal_error`, `not_found`

### الحالة
- `status`, `draft`, `pending`, `approved`
- `completed`, `cancelled`, `paid`, `unpaid`, `partial`

### المالية
- `total`, `subtotal`, `tax`, `discount`
- `quantity`, `price`, `amount`, `date`

## إضافة ترجمات جديدة

1. أضف المفتاح والقيمة في `ar.json`:
```json
{
  "new_key": "القيمة بالعربية"
}
```

2. أضف نفس المفتاح في `en.json`:
```json
{
  "new_key": "English value"
}
```

3. تأكد من تطابق المفاتيح في كلا الملفين

## التحقق من الاتساق

```bash
# التحقق من تطابق المفاتيح
python -c "import json; ar = json.load(open('locales/ar.json', encoding='utf-8')); en = json.load(open('locales/en.json', encoding='utf-8')); print('✅ All keys match!' if set(ar.keys()) == set(en.keys()) else '❌ Keys mismatch')"
```

## ملاحظات

- جميع المفاتيح يجب أن تكون متطابقة في كلا الملفين
- استخدم `{variable_name}` للمتغيرات في الرسائل
- تأكد من ترميز UTF-8 عند التحرير
- استخدم JSON صالح (لا فواصل زائدة)

