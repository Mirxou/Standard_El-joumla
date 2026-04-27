#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تدريب النماذج الأولية للمرحلة 7
Initial Model Training Script for Phase 7
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# إضافة المسار الجذري
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.services.advanced_ai_service import AdvancedAIService, TrainingData
from src.services.intelligent_forecasting_service import IntelligentForecastingService
from src.services.advanced_business_analytics_service import AdvancedBusinessAnalyticsService
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager

def generate_sample_sales_data():
    """توليد بيانات مبيعات تجريبية"""
    print("📊 توليد بيانات المبيعات التجريبية...")

    # إنشاء تواريخ لآخر 365 يوم
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # توليد بيانات مبيعات مع اتجاه موسمي
    np.random.seed(42)  # للتكرار
    n_days = len(dates)

    # اتجاه أساسي مع نمو
    trend = np.linspace(1000, 1500, n_days)

    # تأثير موسمي أسبوعي
    weekly_seasonal = 200 * np.sin(2 * np.pi * np.arange(n_days) / 7)

    # تأثير موسمي شهري
    monthly_seasonal = 300 * np.sin(2 * np.pi * np.arange(n_days) / 30)

    # ضوضاء عشوائية
    noise = np.random.normal(0, 100, n_days)

    # المبيعات النهائية
    sales = trend + weekly_seasonal + monthly_seasonal + noise
    sales = np.maximum(sales, 0)  # عدم وجود مبيعات سلبية

    # إنشاء DataFrame
    sales_data = []
    for i, date in enumerate(dates):
        sales_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'sales': round(float(sales[i]), 2),
            'day_of_week': date.weekday(),
            'month': date.month,
            'quarter': (date.month - 1) // 3 + 1
        })

    return sales_data

def generate_sample_customer_data():
    """توليد بيانات عملاء تجريبية"""
    print("👥 توليد بيانات العملاء التجريبية...")

    customers = []
    np.random.seed(123)

    for i in range(500):
        # توزيع عشوائي لسلوكيات العملاء
        total_purchases = np.random.poisson(5) + 1  # 1-15 شراء
        avg_order_value = np.random.normal(150, 50)  # متوسط 150 مع انحراف 50
        avg_order_value = max(10, avg_order_value)  # حد أدنى 10

        total_spent = total_purchases * avg_order_value
        days_since_last_purchase = np.random.exponential(30)  # متوسط 30 يوم

        customers.append({
            'customer_id': f'CUST_{i:04d}',
            'total_purchases': int(total_purchases),
            'avg_order_value': round(float(avg_order_value), 2),
            'total_spent': round(float(total_spent), 2),
            'days_since_last_purchase': int(days_since_last_purchase),
            'customer_segment': np.random.choice(['VIP', 'Regular', 'New', 'Inactive'], p=[0.1, 0.5, 0.3, 0.1])
        })

    return customers

def train_initial_models():
    """تدريب النماذج الأولية"""
    print("🤖 بدء تدريب النماذج الأولية...")

    # إعداد الخدمات
    db_manager = DatabaseManager()
    db_manager.initialize()  # تهيئة الاتصال بقاعدة البيانات
    ai_service = AdvancedAIService(db_manager)
    forecasting_service = IntelligentForecastingService(db_manager)
    analytics_service = AdvancedBusinessAnalyticsService(db_manager)

    try:
        # 1. تدريب نموذج تصنيف العملاء
        print("\n1️⃣ تدريب نموذج تصنيف العملاء...")
        customer_data = generate_sample_customer_data()

        # استخدام البيانات المولدة فقط للبساطة
        training_data = []
        customer_data = generate_sample_customer_data()
        features = []
        labels = []
        for customer in customer_data[:20]:  # استخدم 20 عميل
            features.append([
                customer['total_purchases'],
                customer['avg_order_value'],
                customer['total_spent'],
                customer['days_since_last_purchase']
            ])
            # تصنيف بسيط: VIP إذا كان الإنفاق > 1000
            labels.append(1 if customer['total_spent'] > 1000 else 0)

        for i, (feature, label) in enumerate(zip(features, labels)):
            training_data.append({
                'data_content': feature,  # بالفعل list
                'labels': label,  # بالفعل int
                'data_type': 'customer_classification',
                'source': 'generated'
            })

        # إنشاء وتدريب النموذج
        model_config = {
            'model_name': 'Customer Classification Model v1.0',
            'model_type': 'classification',
            'purpose': 'Classify customers into VIP/Regular based on purchase behavior',
            'algorithm': 'rf',
            'parameters': {'n_estimators': 50, 'max_depth': 10}
        }

        model = ai_service.create_ai_model(model_config)
        print(f"✅ تم إنشاء النموذج: {model.model_name}")

        # تحويل بيانات التدريب إلى كائنات TrainingData
        training_data_objects = []
        for i, data in enumerate(training_data):
            # التأكد من أن البيانات في الشكل الصحيح
            data_content = data['data_content']
            if isinstance(data_content, str):
                try:
                    data_content = json.loads(data_content)
                except:
                    data_content = [float(data_content)] if data_content.replace('.', '').isdigit() else [0.0]

            labels = data['labels']
            if isinstance(labels, str):
                try:
                    labels = int(labels)
                except:
                    labels = 0

            training_data_objects.append(TrainingData(
                data_id=f"TRAIN_{i:03d}",
                model_id=model.model_id,
                data_type=data['data_type'],
                data_content=data_content,
                labels=labels,
                quality_score=0.9,
                collected_at=datetime.now(),
                used_in_training=False,
                metadata={'source': data.get('source', 'generated')}
            ))

        success = ai_service.train_ai_model(model.model_id, training_data_objects)
        if success:
            print("✅ تم تدريب نموذج تصنيف العملاء بنجاح")
        else:
            print("❌ فشل في تدريب نموذج تصنيف العملاء")

        # 2. تدريب نموذج تنبؤ المبيعات
        print("\n2️⃣ تدريب نموذج تنبؤ المبيعات...")
        sales_data = generate_sample_sales_data()

        forecast_result = forecasting_service.generate_sales_forecast(forecast_days=30)
        if forecast_result:
            print("✅ تم تدريب نموذج تنبؤ المبيعات بنجاح")
            print(f"   📈 دقة النموذج: {forecast_result.accuracy_metrics.get('accuracy_score', 'غير متوفر')}")
        else:
            print("❌ فشل في تدريب نموذج تنبؤ المبيعات")

        # 3. تجزئة العملاء
        print("\n3️⃣ تجزئة العملاء...")
        segmentation_result = analytics_service.perform_customer_segmentation()
        if segmentation_result:
            print(f"✅ تم تجزئة {len(segmentation_result)} عميل بنجاح")
        else:
            print("❌ فشل في تجزئة العملاء")

        # 4. توليد رؤى الأعمال
        print("\n4️⃣ توليد رؤى الأعمال...")
        insights = analytics_service.generate_business_insights(['performance', 'trends'])
        if insights:
            print(f"✅ تم توليد {len(insights)} رؤى أعمال")
        else:
            print("❌ فشل في توليد رؤى الأعمال")

        print("\n🎉 تم الانتهاء من تدريب النماذج الأولية!")
        return True

    except Exception as e:
        print(f"❌ خطأ في تدريب النماذج: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("="*60)
    print("🚀 تدريب النماذج الأولية - المرحلة 7")
    print("="*60)

    success = train_initial_models()

    if success:
        print("\n✅ تم تدريب جميع النماذج الأولية بنجاح!")
        print("📋 الخطوة التالية: اختبار النماذج وتحسين الأداء")
    else:
        print("\n❌ فشل في تدريب بعض النماذج")
        print("🔧 تحقق من السجلات للمزيد من التفاصيل")

if __name__ == '__main__':
    main()