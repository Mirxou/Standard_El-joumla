# AI Module - نظام الذكاء الاصطناعي

## نظرة عامة
هذا المجلد يحتوي على وحدات الذكاء الاصطناعي للتطبيق، بما في ذلك Chatbot والتحليلات التنبؤية.

## الملفات

### `chatbot.py` (336 سطر)
**الوصف**: نظام Chatbot ذكي مع دعم NLP للعربية والإنجليزية

**الميزات**:
- ✅ معالجة اللغة الطبيعية (NLP)
- ✅ دعم متعدد اللغات (العربية والإنجليزية)
- ✅ قاعدة معرفة قابلة للتخصيص
- ✅ تتبع تاريخ المحادثات
- ✅ اكتشاف النية (Intent Detection)
- ✅ ردود ذكية بناءً على السياق

**الاستخدام**:
```python
from src.ai import chatbot, chat

# استخدام الدالة المختصرة
response = chat("مرحبا")
print(response)

# استخدام الـ Engine مباشرة
result = chatbot.process_message("كيف أضيف منتج جديد؟", user_id="user123")
print(result["response"])
print(f"Confidence: {result['confidence']}")
```

**الكلاسات والدوال**:
- `ChatbotEngine` - محرك Chatbot الرئيسي
  - `process_message()` - معالجة الرسالة وإرجاع الرد
  - `get_conversation_history()` - الحصول على تاريخ المحادثة
  - `clear_history()` - مسح تاريخ المحادثة
- `chatbot` - مثيل عام للـ Chatbot
- `chat()` - دالة مختصرة للتحدث

### `predictive_analytics.py` (395 سطر)
**الوصف**: محرك التحليلات التنبؤية للتنبؤ بالمبيعات وتحليل سلوك العملاء

**الميزات**:
- ✅ التنبؤ بالمبيعات (Sales Forecasting)
- ✅ التنبؤ بنفاذ المخزون (Stock-out Prediction)
- ✅ تحليل سلوك العملاء (Customer Behavior Analysis)
- ✅ التوصيات الذكية (Smart Recommendations)
- ✅ اكتشاف الشذوذ (Anomaly Detection)
- ✅ تصنيف العملاء (Customer Segmentation)

**الاستخدام**:
```python
from src.ai import PredictiveEngine, SalesForecast, CustomerInsight
from src.core.database_manager import DatabaseManager

# تهيئة المحرك
db = DatabaseManager("data/inventory.db")
db.initialize()
engine = PredictiveEngine(db)

# التنبؤ بالمبيعات
forecasts = engine.forecast_sales(days=30)
for forecast in forecasts:
    print(f"{forecast.product_name}: {forecast.predicted_sales} units")
    print(f"Days until stockout: {forecast.days_until_stockout}")

# تحليل سلوك العملاء
insights = engine.analyze_customer_behavior()
for insight in insights:
    print(f"{insight.customer_name}: {insight.customer_segment}")
```

**الكلاسات**:
- `SalesForecast` - نموذج توقعات المبيعات
  - `product_id`, `product_name`
  - `current_stock`, `predicted_sales`
  - `days_until_stockout`
  - `recommended_reorder_quantity`
  - `confidence`
- `CustomerInsight` - رؤى العملاء
  - `customer_id`, `customer_name`
  - `total_purchases`, `average_order_value`
  - `purchase_frequency`
  - `predicted_next_purchase`
  - `customer_segment`, `lifetime_value`
- `PredictiveEngine` - محرك التنبؤات
  - `forecast_sales()` - التنبؤ بالمبيعات
  - `analyze_customer_behavior()` - تحليل سلوك العملاء
  - `get_product_recommendations()` - التوصيات الذكية
  - `detect_anomalies()` - اكتشاف الشذوذ

### `__init__.py` (20 سطر)
**الوصف**: ملف التهيئة للمودول

**الصادرات**:
- `ChatbotEngine`, `chatbot`, `chat`
- `PredictiveEngine`, `SalesForecast`, `CustomerInsight`

## التكامل مع التطبيق

### Chatbot
يتم استخدام Chatbot في:
- `src/services/smart_assistant.py` - المساعد الذكي
- `src/ui/windows/smart_dashboard_window.py` - Dashboard الذكي
- واجهة المستخدم للدعم والمساعدة

### Predictive Analytics
يتم استخدام التحليلات التنبؤية في:
- `src/services/ai_service.py` - خدمة AI
- تقارير المبيعات والمخزون
- Dashboard للتنبؤات

## الاختبارات

### اختبار Chatbot
```bash
python src/ai/chatbot.py
```

### اختبار Predictive Analytics
```bash
python src/ai/predictive_analytics.py
```

## TODO / التحسينات المطلوبة

### في `predictive_analytics.py`:
1. **السطر 365**: `_get_customer_purchases()` - تنفيذ استعلام قاعدة البيانات الفعلي
2. **السطر 386**: `_get_product_sales_count()` - تنفيذ استعلام قاعدة البيانات الفعلي
3. **السطر 345**: `_get_sales_history()` - تحسين استعلام قاعدة البيانات

**ملاحظة**: هذه الدوال تحتاج إلى تنفيذ استعلامات قاعدة البيانات الفعلية بدلاً من إرجاع قوائم فارغة.

## قاعدة المعرفة

يستخدم Chatbot ملف `locales/chatbot_knowledge.json` (إن وجد) أو قاعدة معرفة افتراضية مدمجة.

**الهيكل**:
```json
{
  "ar": {
    "greetings": {
      "patterns": ["مرحبا", "السلام عليكم"],
      "responses": ["مرحباً بك!", "أهلاً وسهلاً!"]
    },
    ...
  },
  "en": {
    "greetings": {
      "patterns": ["hello", "hi"],
      "responses": ["Hello!", "Hi there!"]
    },
    ...
  }
}
```

## الخوارزميات المستخدمة

### Chatbot
- **اكتشاف اللغة**: تحليل الأحرف والكلمات
- **اكتشاف النية**: مطابقة الأنماط (Pattern Matching)
- **اختيار الرد**: عشوائي من قائمة الردود المتاحة

### Predictive Analytics
- **التنبؤ بالمبيعات**: المتوسط المتحرك (Moving Average)
- **تحليل العملاء**: RFM Analysis (Recency, Frequency, Monetary)
- **التصنيف**: قواعد بسيطة بناءً على القيم

## التبعيات

- `typing` - Type hints
- `datetime` - التعامل مع التواريخ
- `json` - تحميل قاعدة المعرفة
- `pathlib` - التعامل مع الملفات
- `statistics` - الحسابات الإحصائية
- `dataclasses` - نماذج البيانات

## الأداء

- **Chatbot**: سريع جداً (< 10ms لكل رسالة)
- **Predictive Analytics**: يعتمد على حجم البيانات
  - صغير (< 1000 منتج): < 100ms
  - متوسط (1000-10000): < 1s
  - كبير (> 10000): قد يحتاج تحسين

## الأمان

- ✅ لا يوجد وصول مباشر إلى قاعدة البيانات (يتم تمرير db_manager)
- ✅ معالجة آمنة للأخطاء
- ✅ لا يوجد كود تنفيذي خطير

## التطوير المستقبلي

### Chatbot
- [ ] دعم المزيد من اللغات
- [ ] تكامل مع قاعدة البيانات للردود الديناميكية
- [ ] استخدام ML models للتحسين
- [ ] دعم الصوت (Voice)

### Predictive Analytics
- [ ] استخدام ML models متقدمة (LSTM, ARIMA)
- [ ] تحسين دقة التنبؤات
- [ ] دعم المزيد من أنواع التحليلات
- [ ] تصدير التقارير تلقائياً

## المراجع

- `src/services/smart_assistant.py` - استخدام Chatbot
- `src/services/ai_service.py` - خدمة AI متكاملة
- `src/ui/windows/smart_dashboard_window.py` - واجهة المستخدم

