"""
خدمة الذكاء التجاري - Phase 8
Business Intelligence Service for Unified Commerce 2030 ERP
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger

@dataclass
class BusinessInsight:
    """رؤية تجارية"""
    insight_id: str
    insight_type: str  # 'trend', 'anomaly', 'opportunity', 'warning', 'pattern'
    title: str
    description: str
    data_source: str
    insight_data: Dict[str, Any]
    confidence_score: float  # 0-1
    impact_level: str  # 'low', 'medium', 'high', 'critical'
    recommended_actions: List[str]
    generated_at: datetime
    expires_at: Optional[datetime] = None

@dataclass
class PredictiveInsight:
    """رؤية تنبؤية"""
    insight_id: str
    prediction_type: str
    target_metric: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    time_horizon: str  # 'short_term', 'medium_term', 'long_term'
    influencing_factors: List[str]
    risk_assessment: Dict[str, Any]
    generated_at: datetime

@dataclass
class CustomerSegment:
    """شريحة عملاء"""
    segment_id: str
    segment_name: str
    customer_count: int
    characteristics: Dict[str, Any]
    behavior_patterns: Dict[str, Any]
    value_metrics: Dict[str, Any]
    created_at: datetime

class BusinessIntelligenceService:
    """
    خدمة الذكاء التجاري
    توفر تحليلات متقدمة ورؤى تجارية ذكية
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = setup_logger(__name__)

        # نماذج التحليل
        self.trend_analyzer = LinearRegression()
        self.cluster_model = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()

    def generate_business_insights(self, time_period: str = '30d') -> List[BusinessInsight]:
        """
        توليد رؤى تجارية ذكية

        Args:
            time_period: الفترة الزمنية للتحليل

        Returns:
            List[BusinessInsight]: قائمة الرؤى المولدة
        """
        try:
            self.logger.info(f"🧠 توليد رؤى تجارية للفترة: {time_period}")

            insights = []

            # رؤى المبيعات
            sales_insights = self._analyze_sales_insights(time_period)
            insights.extend(sales_insights)

            # رؤى المخزون
            inventory_insights = self._analyze_inventory_insights()
            insights.extend(inventory_insights)

            # رؤى العملاء
            customer_insights = self._analyze_customer_insights(time_period)
            insights.extend(customer_insights)

            # رؤى مالية
            financial_insights = self._analyze_financial_insights(time_period)
            insights.extend(financial_insights)

            # حفظ الرؤى
            for insight in insights:
                self._save_business_insight(insight)

            self.logger.info(f"✅ تم توليد {len(insights)} رؤية تجارية")
            return insights

        except Exception as e:
            self.logger.error(f"❌ فشل في توليد الرؤى التجارية: {e}")
            return []

    def detect_anomalies(self, data_source: str, time_period: str = '7d') -> List[Dict[str, Any]]:
        """
        كشف الشذوذ في البيانات

        Args:
            data_source: مصدر البيانات
            time_period: الفترة الزمنية

        Returns:
            List[Dict[str, Any]]: قائمة الشذوذ المكتشفة
        """
        try:
            self.logger.info(f"🔍 كشف الشذوذ في {data_source} للفترة {time_period}")

            anomalies = []

            if data_source == 'sales':
                anomalies = self._detect_sales_anomalies(time_period)
            elif data_source == 'inventory':
                anomalies = self._detect_inventory_anomalies()
            elif data_source == 'customers':
                anomalies = self._detect_customer_anomalies(time_period)

            self.logger.info(f"✅ تم كشف {len(anomalies)} شذوذ")
            return anomalies

        except Exception as e:
            self.logger.error(f"❌ فشل في كشف الشذوذ: {e}")
            return []

    def segment_customers(self) -> List[CustomerSegment]:
        """
        تقسيم العملاء إلى شرائح

        Returns:
            List[CustomerSegment]: شرائح العملاء
        """
        try:
            self.logger.info("👥 تقسيم العملاء إلى شرائح")

            # الحصول على بيانات العملاء
            customer_data = self._get_customer_behavior_data()

            if len(customer_data) < 10:
                self.logger.warning("بيانات العملاء غير كافية للتقسيم")
                return []

            # تحضير البيانات للـ clustering
            features = ['total_purchases', 'avg_order_value', 'purchase_frequency', 'last_purchase_days']
            X = customer_data[features].values

            # تطبيع البيانات
            X_scaled = self.scaler.fit_transform(X)

            # تطبيق K-means clustering
            clusters = self.cluster_model.fit_predict(X_scaled)

            # إنشاء شرائح العملاء
            segments = []
            for i in range(self.cluster_model.n_clusters):
                cluster_data = customer_data[clusters == i]

                segment = CustomerSegment(
                    segment_id=f"SEGMENT_{i+1}",
                    segment_name=f"شريحة {i+1}",
                    customer_count=len(cluster_data),
                    characteristics=self._analyze_cluster_characteristics(cluster_data),
                    behavior_patterns=self._analyze_cluster_behavior(cluster_data),
                    value_metrics=self._calculate_segment_value(cluster_data),
                    created_at=datetime.now()
                )
                segments.append(segment)

            # حفظ الشرائح
            for segment in segments:
                self._save_customer_segment(segment)

            self.logger.info(f"✅ تم إنشاء {len(segments)} شريحة عملاء")
            return segments

        except Exception as e:
            self.logger.error(f"❌ فشل في تقسيم العملاء: {e}")
            return []

    def generate_predictive_insights(self, forecast_days: int = 30) -> List[PredictiveInsight]:
        """
        توليد رؤى تنبؤية

        Args:
            forecast_days: أيام التنبؤ

        Returns:
            List[PredictiveInsight]: الرؤى التنبؤية
        """
        try:
            self.logger.info(f"🔮 توليد رؤى تنبؤية لـ {forecast_days} يوم")

            insights = []

            # تنبؤ المبيعات
            sales_forecast = self._forecast_sales_trend(forecast_days)
            if sales_forecast:
                insights.append(sales_forecast)

            # تنبؤ الطلب
            demand_forecast = self._forecast_demand_trend(forecast_days)
            if demand_forecast:
                insights.append(demand_forecast)

            # تنبؤ التدفق النقدي
            cash_flow_forecast = self._forecast_cash_flow(forecast_days)
            if cash_flow_forecast:
                insights.append(cash_flow_forecast)

            self.logger.info(f"✅ تم توليد {len(insights)} رؤية تنبؤية")
            return insights

        except Exception as e:
            self.logger.error(f"❌ فشل في توليد الرؤى التنبؤية: {e}")
            return []

    def analyze_performance_trends(self, metric: str, time_period: str = '90d') -> Dict[str, Any]:
        """
        تحليل اتجاهات الأداء

        Args:
            metric: المقياس المراد تحليله
            time_period: الفترة الزمنية

        Returns:
            Dict[str, Any]: نتائج تحليل الاتجاهات
        """
        try:
            self.logger.info(f"📈 تحليل اتجاهات {metric} للفترة {time_period}")

            # الحصول على البيانات التاريخية
            historical_data = self._get_metric_history(metric, time_period)

            if not historical_data:
                return {'error': 'no historical data available'}

            # تحليل الاتجاه
            trend_analysis = self._analyze_trend(historical_data)

            # كشف الأنماط
            pattern_analysis = self._detect_patterns(historical_data)

            # حساب المؤشرات الإحصائية
            stats = self._calculate_statistics(historical_data)

            result = {
                'metric': metric,
                'time_period': time_period,
                'trend_analysis': trend_analysis,
                'pattern_analysis': pattern_analysis,
                'statistics': stats,
                'data_points': len(historical_data),
                'analyzed_at': datetime.now().isoformat()
            }

            self.logger.info(f"✅ تم تحليل اتجاهات {metric}")
            return result

        except Exception as e:
            self.logger.error(f"❌ فشل في تحليل الاتجاهات: {e}")
            return {'error': str(e)}

    # طرق تحليل الرؤى
    def _analyze_sales_insights(self, time_period: str) -> List[BusinessInsight]:
        """تحليل رؤى المبيعات"""
        try:
            insights = []

            # تحليل اتجاه المبيعات
            sales_trend = self.analyze_performance_trends('sales', time_period)
            if sales_trend.get('trend_analysis', {}).get('slope', 0) > 0.1:
                insight = BusinessInsight(
                    insight_id=f"INSIGHT_SALES_UP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    insight_type='trend',
                    title='ارتفاع في المبيعات',
                    description='المبيعات تظهر اتجاهاً تصاعدياً إيجابياً',
                    data_source='sales_data',
                    insight_data=sales_trend,
                    confidence_score=0.85,
                    impact_level='high',
                    recommended_actions=[
                        'زيادة المخزون للمنتجات الأكثر مبيعاً',
                        'تعزيز الحملات التسويقية',
                        'مراجعة استراتيجية التسعير'
                    ],
                    generated_at=datetime.now()
                )
                insights.append(insight)

            # كشف الشذوذ في المبيعات
            sales_anomalies = self.detect_anomalies('sales', time_period)
            if sales_anomalies:
                insight = BusinessInsight(
                    insight_id=f"INSIGHT_SALES_ANOMALY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    insight_type='anomaly',
                    title='شذوذ في أنماط المبيعات',
                    description=f'تم كشف {len(sales_anomalies)} شذوذ في أنماط المبيعات',
                    data_source='sales_data',
                    insight_data={'anomalies': sales_anomalies},
                    confidence_score=0.75,
                    impact_level='medium',
                    recommended_actions=[
                        'مراجعة أسباب الشذوذ',
                        'تحليل العوامل المؤثرة',
                        'تعديل خطط المخزون حسب الحاجة'
                    ],
                    generated_at=datetime.now()
                )
                insights.append(insight)

            return insights

        except Exception as e:
            self.logger.error(f"فشل في تحليل رؤى المبيعات: {e}")
            return []

    def _analyze_inventory_insights(self) -> List[BusinessInsight]:
        """تحليل رؤى المخزون"""
        try:
            insights = []

            # فحص المخزون المنخفض
            low_stock_items = self._get_low_stock_items()
            if low_stock_items:
                insight = BusinessInsight(
                    insight_id=f"INSIGHT_LOW_STOCK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    insight_type='warning',
                    title='مخزون منخفض لمنتجات رئيسية',
                    description=f'{len(low_stock_items)} منتج يحتاج إلى إعادة طلب',
                    data_source='inventory_data',
                    insight_data={'low_stock_items': low_stock_items},
                    confidence_score=0.95,
                    impact_level='high',
                    recommended_actions=[
                        'إصدار أوامر شراء فورية',
                        'مراجعة سياسات المخزون',
                        'الاتصال بالموردين'
                    ],
                    generated_at=datetime.now()
                )
                insights.append(insight)

            # تحليل دوران المخزون
            inventory_turnover = self._analyze_inventory_turnover()
            if inventory_turnover.get('slow_moving_items'):
                insight = BusinessInsight(
                    insight_id=f"INSIGHT_SLOW_INVENTORY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    insight_type='opportunity',
                    title='منتجات بطيئة الحركة',
                    description='تحديد منتجات تحتاج إلى تعزيز المبيعات',
                    data_source='inventory_data',
                    insight_data=inventory_turnover,
                    confidence_score=0.80,
                    impact_level='medium',
                    recommended_actions=[
                        'تطبيق عروض ترويجية',
                        'مراجعة استراتيجية التسعير',
                        'تحسين عرض المنتجات'
                    ],
                    generated_at=datetime.now()
                )
                insights.append(insight)

            return insights

        except Exception as e:
            self.logger.error(f"فشل في تحليل رؤى المخزون: {e}")
            return []

    def _analyze_customer_insights(self, time_period: str) -> List[BusinessInsight]:
        """تحليل رؤى العملاء"""
        try:
            insights = []

            # تحليل سلوك العملاء
            customer_behavior = self._analyze_customer_behavior(time_period)

            # كشف العملاء المخلصين
            loyal_customers = customer_behavior.get('loyal_customers', [])
            if loyal_customers:
                insight = BusinessInsight(
                    insight_id=f"INSIGHT_LOYAL_CUSTOMERS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    insight_type='opportunity',
                    title='عملاء مخلصون محددون',
                    description=f'تحديد {len(loyal_customers)} عميل مخلص',
                    data_source='customer_data',
                    insight_data={'loyal_customers': loyal_customers},
                    confidence_score=0.90,
                    impact_level='high',
                    recommended_actions=[
                        'برامج مكافآت خاصة',
                        'عروض حصرية',
                        'برامج ولاء محسنة'
                    ],
                    generated_at=datetime.now()
                )
                insights.append(insight)

            # كشف العملاء المهددين بالخسارة
            at_risk_customers = customer_behavior.get('at_risk_customers', [])
            if at_risk_customers:
                insight = BusinessInsight(
                    insight_id=f"INSIGHT_AT_RISK_CUSTOMERS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    insight_type='warning',
                    title='عملاء مهددون بالخسارة',
                    description=f'{len(at_risk_customers)} عميل لم يشتري منذ فترة طويلة',
                    data_source='customer_data',
                    insight_data={'at_risk_customers': at_risk_customers},
                    confidence_score=0.85,
                    impact_level='high',
                    recommended_actions=[
                        'حملات إعادة جذب',
                        'استطلاعات رضا العملاء',
                        'عروض خاصة للعودة'
                    ],
                    generated_at=datetime.now()
                )
                insights.append(insight)

            return insights

        except Exception as e:
            self.logger.error(f"فشل في تحليل رؤى العملاء: {e}")
            return []

    def _analyze_financial_insights(self, time_period: str) -> List[BusinessInsight]:
        """تحليل رؤى مالية"""
        try:
            insights = []

            # تحليل التدفق النقدي
            cash_flow_analysis = self._analyze_cash_flow_patterns(time_period)

            # كشف الاتجاهات المالية
            if cash_flow_analysis.get('trend') == 'improving':
                insight = BusinessInsight(
                    insight_id=f"INSIGHT_CASH_FLOW_UP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    insight_type='trend',
                    title='تحسن في التدفق النقدي',
                    description='التدفق النقدي يظهر اتجاهاً إيجابياً',
                    data_source='financial_data',
                    insight_data=cash_flow_analysis,
                    confidence_score=0.80,
                    impact_level='high',
                    recommended_actions=[
                        'الاستثمار في فرص النمو',
                        'تحسين إدارة رأس المال العامل',
                        'مراجعة استراتيجية الائتمان'
                    ],
                    generated_at=datetime.now()
                )
                insights.append(insight)

            return insights

        except Exception as e:
            self.logger.error(f"فشل في تحليل الرؤى المالية: {e}")
            return []

    # طرق كشف الشذوذ
    def _detect_sales_anomalies(self, time_period: str) -> List[Dict[str, Any]]:
        """كشف شذوذ المبيعات"""
        try:
            # الحصول على بيانات المبيعات اليومية
            sales_data = self._get_daily_sales_data(time_period)

            if len(sales_data) < 7:
                return []

            # حساب المتوسط والانحراف المعياري
            values = [item['value'] for item in sales_data]
            mean_value = np.mean(values)
            std_value = np.std(values)

            # كشف القيم الشاذة (أكبر من 2 انحراف معياري)
            anomalies = []
            for item in sales_data:
                z_score = abs(item['value'] - mean_value) / std_value if std_value > 0 else 0
                if z_score > 2.0:
                    anomalies.append({
                        'date': item['date'],
                        'value': item['value'],
                        'expected_value': mean_value,
                        'deviation': item['value'] - mean_value,
                        'z_score': z_score,
                        'severity': 'high' if z_score > 3.0 else 'medium'
                    })

            return anomalies

        except Exception as e:
            self.logger.error(f"فشل في كشف شذوذ المبيعات: {e}")
            return []

    def _detect_inventory_anomalies(self) -> List[Dict[str, Any]]:
        """كشف شذوذ المخزون"""
        try:
            # فحص المخزون السالب أو الصفري
            anomalies = []

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, wi.quantity, wi.min_stock
                    FROM warehouse_inventory wi
                    JOIN products p ON wi.product_id = p.id
                    WHERE wi.quantity <= 0 OR wi.quantity < wi.min_stock
                """)

                for row in cursor.fetchall():
                    product_name, quantity, min_stock = row
                    anomalies.append({
                        'product_name': product_name,
                        'current_stock': quantity,
                        'min_stock': min_stock,
                        'deficit': max(0, min_stock - quantity),
                        'anomaly_type': 'low_stock' if quantity < min_stock else 'negative_stock'
                    })

            return anomalies

        except Exception as e:
            self.logger.error(f"فشل في كشف شذوذ المخزون: {e}")
            return []

    def _detect_customer_anomalies(self, time_period: str) -> List[Dict[str, Any]]:
        """كشف شذوذ العملاء"""
        try:
            # كشف العملاء ذوي الأنماط الشاذة
            customer_data = self._get_customer_purchase_patterns(time_period)

            anomalies = []
            for customer in customer_data:
                # كشف العملاء ذوي المشتريات المرتفعة جداً
                if customer.get('total_purchases', 0) > customer.get('avg_customer_purchases', 0) * 3:
                    anomalies.append({
                        'customer_id': customer.get('customer_id'),
                        'anomaly_type': 'high_value_customer',
                        'total_purchases': customer.get('total_purchases'),
                        'avg_customer_purchases': customer.get('avg_customer_purchases')
                    })

            return anomalies

        except Exception as e:
            self.logger.error(f"فشل في كشف شذوذ العملاء: {e}")
            return []

    # طرق التحليل المساعدة
    def _analyze_trend(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل الاتجاه"""
        try:
            if len(data) < 3:
                return {'trend': 'insufficient_data'}

            # تحويل البيانات إلى سلسلة زمنية
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # تطبيق الانحدار الخطي
            X = np.arange(len(df)).reshape(-1, 1)
            y = df['value'].values

            self.trend_analyzer.fit(X, y)
            slope = self.trend_analyzer.coef_[0]
            intercept = self.trend_analyzer.intercept_

            # تحديد نوع الاتجاه
            if slope > 0.01:
                trend = 'increasing'
            elif slope < -0.01:
                trend = 'decreasing'
            else:
                trend = 'stable'

            return {
                'trend': trend,
                'slope': slope,
                'intercept': intercept,
                'r_squared': self.trend_analyzer.score(X, y),
                'trend_strength': abs(slope)
            }

        except Exception as e:
            return {'trend': 'error', 'error': str(e)}

    def _detect_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """كشف الأنماط"""
        try:
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            patterns = {}

            # كشف الأنماط الأسبوعية
            if len(df) >= 14:  # أسبوعين على الأقل
                weekly_pattern = df.groupby(df.index.dayofweek)['value'].mean()
                if weekly_pattern.std() / weekly_pattern.mean() > 0.2:
                    patterns['weekly_pattern'] = {
                        'pattern_type': 'weekly',
                        'peak_day': weekly_pattern.idxmax(),
                        'trough_day': weekly_pattern.idxmin(),
                        'variability': weekly_pattern.std() / weekly_pattern.mean()
                    }

            # كشف الأنماط الشهرية
            if len(df) >= 60:  # شهرين على الأقل
                monthly_pattern = df.groupby(df.index.month)['value'].mean()
                if monthly_pattern.std() / monthly_pattern.mean() > 0.15:
                    patterns['monthly_pattern'] = {
                        'pattern_type': 'monthly',
                        'peak_month': monthly_pattern.idxmax(),
                        'trough_month': monthly_pattern.idxmin(),
                        'variability': monthly_pattern.std() / monthly_pattern.mean()
                    }

            return patterns

        except Exception as e:
            return {'error': str(e)}

    def _calculate_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """حساب الإحصائيات"""
        try:
            values = [item['value'] for item in data]

            return {
                'count': len(values),
                'mean': np.mean(values),
                'median': np.median(values),
                'std_dev': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'cv': np.std(values) / np.mean(values) if np.mean(values) > 0 else 0  # coefficient of variation
            }

        except Exception as e:
            return {'error': str(e)}

    # طرق قاعدة البيانات
    def _save_business_insight(self, insight: BusinessInsight) -> None:
        """حفظ الرؤية التجارية"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO business_insights
                    (insight_id, insight_type, title, description, data_source,
                     insight_data, confidence_score, impact_level, recommended_actions,
                     generated_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    insight.insight_id, insight.insight_type, insight.title,
                    insight.description, insight.data_source,
                    json.dumps(insight.insight_data), insight.confidence_score,
                    insight.impact_level, json.dumps(insight.recommended_actions),
                    insight.generated_at, insight.expires_at
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ الرؤية التجارية: {e}")

    def _save_customer_segment(self, segment: CustomerSegment) -> None:
        """حفظ شريحة العملاء"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO customer_segments
                    (segment_id, segment_name, customer_count, characteristics,
                     behavior_patterns, value_metrics, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    segment.segment_id, segment.segment_name, segment.customer_count,
                    json.dumps(segment.characteristics), json.dumps(segment.behavior_patterns),
                    json.dumps(segment.value_metrics), segment.created_at
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ شريحة العملاء: {e}")

    # طرق الحصول على البيانات
    def _get_daily_sales_data(self, time_period: str) -> List[Dict[str, Any]]:
        """الحصول على بيانات المبيعات اليومية"""
        try:
            days = int(time_period.replace('d', ''))
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DATE(created_at) as date, SUM(total_amount) as value
                    FROM sales
                    WHERE created_at >= ? AND status = 'completed'
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """, (datetime.now() - timedelta(days=days),))

                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            return []

    def _get_customer_behavior_data(self) -> pd.DataFrame:
        """الحصول على بيانات سلوك العملاء"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        c.id as customer_id,
                        c.name,
                        COUNT(s.id) as total_purchases,
                        AVG(s.total_amount) as avg_order_value,
                        COUNT(s.id) * 1.0 / MAX(JULIANDAY('now') - JULIANDAY(c.created_at)) as purchase_frequency,
                        JULIANDAY('now') - JULIANDAY(MAX(s.created_at)) as last_purchase_days
                    FROM customers c
                    LEFT JOIN sales s ON c.id = s.customer_id AND s.status = 'completed'
                    GROUP BY c.id, c.name
                    HAVING total_purchases > 0
                """)

                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()

                return pd.DataFrame(data, columns=columns)
        except Exception as e:
            return pd.DataFrame()

    def _get_metric_history(self, metric: str, time_period: str) -> List[Dict[str, Any]]:
        """الحصول على تاريخ مقياس معين"""
        try:
            days = int(time_period.replace('d', ''))

            if metric == 'sales':
                return self._get_daily_sales_data(time_period)
            elif metric == 'orders':
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DATE(created_at) as date, COUNT(*) as value
                        FROM sales
                        WHERE created_at >= ? AND status = 'completed'
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    """, (datetime.now() - timedelta(days=days),))
                    return [dict(row) for row in cursor.fetchall()]

            return []
        except Exception as e:
            return []

    # طرق إضافية للتحليل
    def _get_low_stock_items(self) -> List[Dict[str, Any]]:
        """الحصول على المنتجات ذات المخزون المنخفض"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, wi.quantity, wi.min_stock, wi.reorder_point
                    FROM warehouse_inventory wi
                    JOIN products p ON wi.product_id = p.id
                    WHERE wi.quantity <= wi.reorder_point OR wi.quantity <= wi.min_stock
                    ORDER BY wi.quantity ASC
                """)

                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            return []

    def _analyze_inventory_turnover(self) -> Dict[str, Any]:
        """تحليل دوران المخزون"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name,
                           SUM(wi.quantity) as current_stock,
                           AVG(si.quantity) as avg_monthly_sales
                    FROM warehouse_inventory wi
                    JOIN products p ON wi.product_id = p.id
                    LEFT JOIN sale_items si ON p.id = si.product_id
                    LEFT JOIN sales s ON si.sale_id = s.id AND s.status = 'completed'
                           AND s.created_at >= date('now', '-30 days')
                    GROUP BY p.id, p.name
                """)

                items = []
                slow_moving = []

                for row in cursor.fetchall():
                    name, stock, avg_sales = row
                    turnover_ratio = avg_sales / stock if stock > 0 else 0

                    item_data = {
                        'product_name': name,
                        'current_stock': stock,
                        'avg_monthly_sales': avg_sales or 0,
                        'turnover_ratio': turnover_ratio
                    }
                    items.append(item_data)

                    # المنتجات البطيئة الحركة (دوران أقل من 1 مرة شهرياً)
                    if turnover_ratio < 1.0 and stock > 0:
                        slow_moving.append(item_data)

                return {
                    'total_items': len(items),
                    'slow_moving_items': slow_moving,
                    'turnover_distribution': items
                }
        except Exception as e:
            return {'error': str(e)}

    def _analyze_customer_behavior(self, time_period: str) -> Dict[str, Any]:
        """تحليل سلوك العملاء"""
        try:
            days = int(time_period.replace('d', ''))

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id, c.name, COUNT(s.id) as purchase_count,
                           SUM(s.total_amount) as total_spent,
                           MAX(s.created_at) as last_purchase,
                           AVG(s.total_amount) as avg_order_value
                    FROM customers c
                    LEFT JOIN sales s ON c.id = s.customer_id AND s.status = 'completed'
                           AND s.created_at >= ?
                    GROUP BY c.id, c.name
                    HAVING purchase_count > 0
                    ORDER BY total_spent DESC
                """, (datetime.now() - timedelta(days=days),))

                customers = []
                loyal_customers = []
                at_risk_customers = []

                for row in cursor.fetchall():
                    customer = dict(row)
                    customers.append(customer)

                    # تعريف العملاء المخلصين (أعلى 20% في الإنفاق)
                    if len(customers) <= len(customers) * 0.2:
                        loyal_customers.append(customer)

                    # العملاء المهددون بالخسارة (لم يشتروا منذ 60 يوماً)
                    last_purchase_days = (datetime.now() - customer['last_purchase']).days if customer['last_purchase'] else 999
                    if last_purchase_days > 60:
                        at_risk_customers.append(customer)

                return {
                    'total_customers': len(customers),
                    'loyal_customers': loyal_customers,
                    'at_risk_customers': at_risk_customers,
                    'customer_analysis': customers
                }
        except Exception as e:
            return {'error': str(e)}

    def _analyze_cash_flow_patterns(self, time_period: str) -> Dict[str, Any]:
        """تحليل أنماط التدفق النقدي"""
        try:
            days = int(time_period.replace('d', ''))

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DATE(transaction_date) as date,
                           SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
                           SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expenses
                    FROM financial_transactions
                    WHERE transaction_date >= ?
                    GROUP BY DATE(transaction_date)
                    ORDER BY date
                """, (datetime.now() - timedelta(days=days),))

                cash_flow_data = []
                for row in cursor.fetchall():
                    cash_flow = row[1] - row[2]  # دخل - مصروف
                    cash_flow_data.append({
                        'date': row[0],
                        'cash_flow': cash_flow,
                        'income': row[1],
                        'expenses': row[2]
                    })

                # تحليل الاتجاه
                if len(cash_flow_data) >= 7:
                    recent_avg = np.mean([item['cash_flow'] for item in cash_flow_data[-7:]])
                    previous_avg = np.mean([item['cash_flow'] for item in cash_flow_data[:-7]]) if len(cash_flow_data) > 7 else recent_avg

                    trend = 'stable'
                    if recent_avg > previous_avg * 1.1:
                        trend = 'improving'
                    elif recent_avg < previous_avg * 0.9:
                        trend = 'declining'

                    return {
                        'trend': trend,
                        'recent_avg': recent_avg,
                        'previous_avg': previous_avg,
                        'change_percent': ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg != 0 else 0,
                        'data': cash_flow_data
                    }

                return {'trend': 'insufficient_data', 'data': cash_flow_data}
        except Exception as e:
            return {'error': str(e)}

    # طرق التنبؤ
    def _forecast_sales_trend(self, forecast_days: int) -> Optional[PredictiveInsight]:
        """تنبؤ اتجاه المبيعات"""
        try:
            # الحصول على بيانات المبيعات التاريخية
            historical_data = self._get_daily_sales_data('90d')

            if len(historical_data) < 14:
                return None

            # تطبيق نموذج التنبؤ البسيط
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # حساب المتوسط المتحرك
            recent_avg = df['value'].tail(7).mean()
            trend = (df['value'].tail(7).mean() - df['value'].tail(14).head(7).mean()) / 7

            # التنبؤ للأيام القادمة
            forecast_value = recent_avg + (trend * forecast_days / 7)

            return PredictiveInsight(
                insight_id=f"PREDICT_SALES_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                prediction_type='sales_forecast',
                target_metric='daily_sales',
                predicted_value=forecast_value,
                confidence_interval=(forecast_value * 0.8, forecast_value * 1.2),
                time_horizon='short_term',
                influencing_factors=['seasonal_patterns', 'recent_trend', 'market_conditions'],
                risk_assessment={
                    'risk_level': 'medium',
                    'factors': ['market_volatility', 'competition_changes'],
                    'mitigation': ['diversify_product_lines', 'monitor_market_indicators']
                },
                generated_at=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"فشل في تنبؤ المبيعات: {e}")
            return None

    def _forecast_demand_trend(self, forecast_days: int) -> Optional[PredictiveInsight]:
        """تنبؤ اتجاه الطلب"""
        try:
            # تحليل الطلب على المنتجات
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, SUM(si.quantity) as total_quantity
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    JOIN products p ON si.product_id = p.id
                    WHERE s.created_at >= date('now', '-30 days') AND s.status = 'completed'
                    GROUP BY p.id, p.name
                    ORDER BY total_quantity DESC
                    LIMIT 5
                """)

                top_products = cursor.fetchall()

                if top_products:
                    # حساب متوسط الطلب اليومي لأفضل المنتجات
                    total_daily_demand = sum(row[1] for row in top_products) / 30

                    return PredictiveInsight(
                        insight_id=f"PREDICT_DEMAND_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        prediction_type='demand_forecast',
                        target_metric='daily_demand',
                        predicted_value=total_daily_demand * (forecast_days / 30),
                        confidence_interval=(total_daily_demand * 0.7, total_daily_demand * 1.3),
                        time_horizon='medium_term',
                        influencing_factors=['product_popularity', 'seasonal_factors', 'marketing_campaigns'],
                        risk_assessment={
                            'risk_level': 'medium',
                            'factors': ['supply_chain_disruptions', 'competitor_actions'],
                            'mitigation': ['maintain_safety_stock', 'diversify_suppliers']
                        },
                        generated_at=datetime.now()
                    )
            return None
        except Exception as e:
            self.logger.error(f"فشل في تنبؤ الطلب: {e}")
            return None

    def _forecast_cash_flow(self, forecast_days: int) -> Optional[PredictiveInsight]:
        """تنبؤ التدفق النقدي"""
        try:
            cash_flow_analysis = self._analyze_cash_flow_patterns('90d')

            if cash_flow_analysis.get('trend') == 'insufficient_data':
                return None

            recent_avg = cash_flow_analysis.get('recent_avg', 0)
            forecast_value = recent_avg * (forecast_days / 30)

            return PredictiveInsight(
                insight_id=f"PREDICT_CASHFLOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                prediction_type='cash_flow_forecast',
                target_metric='monthly_cash_flow',
                predicted_value=forecast_value,
                confidence_interval=(forecast_value * 0.6, forecast_value * 1.4),
                time_horizon='medium_term',
                influencing_factors=['sales_trends', 'payment_terms', 'operating_expenses'],
                risk_assessment={
                    'risk_level': 'high',
                    'factors': ['economic_conditions', 'customer_payment_delays'],
                    'mitigation': ['cash_reserves', 'credit_insurance', 'payment_reminders']
                },
                generated_at=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"فشل في تنبؤ التدفق النقدي: {e}")
            return None

    def _get_customer_purchase_patterns(self, time_period: str) -> List[Dict[str, Any]]:
        """الحصول على أنماط شراء العملاء"""
        try:
            days = int(time_period.replace('d', ''))

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id as customer_id, c.name,
                           COUNT(s.id) as purchase_count,
                           SUM(s.total_amount) as total_purchases,
                           AVG(s.total_amount) as avg_order_value,
                           MAX(s.created_at) as last_purchase
                    FROM customers c
                    LEFT JOIN sales s ON c.id = s.customer_id AND s.status = 'completed'
                           AND s.created_at >= ?
                    GROUP BY c.id, c.name
                """, (datetime.now() - timedelta(days=days),))

                customers = []
                for row in cursor.fetchall():
                    customers.append(dict(row))

                # إضافة متوسط العملاء للمقارنة
                if customers:
                    avg_customer_purchases = np.mean([c['total_purchases'] for c in customers if c['total_purchases']])
                    for customer in customers:
                        customer['avg_customer_purchases'] = avg_customer_purchases

                return customers
        except Exception as e:
            return []

    def _analyze_cluster_characteristics(self, cluster_data: pd.DataFrame) -> Dict[str, Any]:
        """تحليل خصائص المجموعة"""
        try:
            return {
                'avg_total_purchases': cluster_data['total_purchases'].mean(),
                'avg_order_value': cluster_data['avg_order_value'].mean(),
                'avg_purchase_frequency': cluster_data['purchase_frequency'].mean(),
                'avg_last_purchase_days': cluster_data['last_purchase_days'].mean(),
                'size': len(cluster_data)
            }
        except Exception as e:
            return {}

    def _analyze_cluster_behavior(self, cluster_data: pd.DataFrame) -> Dict[str, Any]:
        """تحليل سلوك المجموعة"""
        try:
            return {
                'purchase_frequency': cluster_data['purchase_frequency'].describe().to_dict(),
                'spending_pattern': cluster_data['total_purchases'].describe().to_dict(),
                'loyalty_score': (cluster_data['purchase_frequency'] * cluster_data['total_purchases']).mean()
            }
        except Exception as e:
            return {}

    def _calculate_segment_value(self, cluster_data: pd.DataFrame) -> Dict[str, Any]:
        """حساب قيمة المجموعة"""
        try:
            return {
                'total_revenue': cluster_data['total_purchases'].sum(),
                'avg_customer_value': cluster_data['total_purchases'].mean(),
                'revenue_percentage': 0,  # سيتم حسابه نسبة للإجمالي
                'growth_potential': cluster_data['purchase_frequency'].mean() * 1.2  # تقدير
            }
        except Exception as e:
            return {
}
