#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Prediction Service - خدمة التنبؤ بالذكاء الاصطناعي
تنبؤات المبيعات، الطلب، Customer Churn، وتوصيات المنتجات
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)


class AIPredictionService:
    """خدمة التنبؤ بالذكاء الاصطناعي"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة التنبؤ
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
        
        if not ML_AVAILABLE:
            self.logger.warning("⚠️ scikit-learn غير متاح - بعض الميزات لن تعمل")
    
    # ============================================================================
    # Sales Forecasting - تنبؤات المبيعات
    # ============================================================================
    
    def forecast_sales(self, days_ahead: int = 30, product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        تنبؤ المبيعات للفترة القادمة
        
        Args:
            days_ahead: عدد الأيام للتنبؤ بها
            product_id: معرف المنتج (اختياري - إذا None، تنبؤ عام)
            
        Returns:
            Dict مع التنبؤات والثقة
        """
        try:
            if not ML_AVAILABLE:
                return {"error": "ML libraries not available"}
            
            # جلب بيانات المبيعات التاريخية
            sales_data = self._get_sales_history(product_id, days=90)
            
            if len(sales_data) < 7:
                return {
                    "error": "لا توجد بيانات كافية للتنبؤ",
                    "min_days_required": 7
                }
            
            # تحضير البيانات
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # إنشاء features
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_month'] = df['date'].dt.day
            df['month'] = df['date'].dt.month
            df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
            
            # إعداد البيانات للتدريب
            X = df[['day_of_week', 'day_of_month', 'month', 'days_since_start']].values
            y = df['total_amount'].values
            
            # تقسيم البيانات
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # تدريب النموذج
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # تقييم النموذج
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            # التنبؤ للفترة القادمة
            last_date = df['date'].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=days_ahead,
                freq='D'
            )
            
            future_features = []
            for date in future_dates:
                days_since_start = (date - df['date'].min()).days
                future_features.append([
                    date.dayofweek,
                    date.day,
                    date.month,
                    days_since_start
                ])
            
            future_predictions = model.predict(future_features)
            
            # حساب الثقة (بناءً على التباين)
            confidence = max(0, min(100, 100 - (rmse / np.mean(y) * 100)))
            
            return {
                "success": True,
                "forecast": [
                    {
                        "date": date.isoformat(),
                        "predicted_amount": float(pred),
                        "confidence": round(confidence, 2)
                    }
                    for date, pred in zip(future_dates, future_predictions)
                ],
                "metrics": {
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "confidence": round(confidence, 2)
                },
                "total_predicted": float(np.sum(future_predictions))
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تنبؤ المبيعات: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # Demand Forecasting - تنبؤات الطلب
    # ============================================================================
    
    def forecast_demand(self, product_id: int, days_ahead: int = 30) -> Dict[str, Any]:
        """
        تنبؤ الطلب على منتج محدد
        
        Args:
            product_id: معرف المنتج
            days_ahead: عدد الأيام للتنبؤ بها
            
        Returns:
            Dict مع التنبؤات
        """
        try:
            if not ML_AVAILABLE:
                return {"error": "ML libraries not available"}
            
            # جلب بيانات المبيعات للمنتج
            sales_data = self._get_product_sales_history(product_id, days=90)
            
            if len(sales_data) < 7:
                return {
                    "error": "لا توجد بيانات كافية للتنبؤ",
                    "min_days_required": 7
                }
            
            # تحضير البيانات
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # تجميع حسب التاريخ
            daily_demand = df.groupby('date')['quantity'].sum().reset_index()
            
            # إنشاء features
            daily_demand['day_of_week'] = daily_demand['date'].dt.dayofweek
            daily_demand['day_of_month'] = daily_demand['date'].dt.day
            daily_demand['month'] = daily_demand['date'].dt.month
            daily_demand['days_since_start'] = (
                daily_demand['date'] - daily_demand['date'].min()
            ).dt.days
            
            # إعداد البيانات
            X = daily_demand[['day_of_week', 'day_of_month', 'month', 'days_since_start']].values
            y = daily_demand['quantity'].values
            
            # تدريب النموذج
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # التنبؤ
            last_date = daily_demand['date'].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=days_ahead,
                freq='D'
            )
            
            future_features = []
            for date in future_dates:
                days_since_start = (date - daily_demand['date'].min()).days
                future_features.append([
                    date.dayofweek,
                    date.day,
                    date.month,
                    days_since_start
                ])
            
            future_predictions = model.predict(future_features)
            
            total_demand = float(np.sum(future_predictions))
            avg_daily_demand = float(np.mean(future_predictions))
            
            return {
                "success": True,
                "product_id": product_id,
                "forecast": [
                    {
                        "date": date.isoformat(),
                        "predicted_quantity": float(pred)
                    }
                    for date, pred in zip(future_dates, future_predictions)
                ],
                "summary": {
                    "total_demand": total_demand,
                    "avg_daily_demand": avg_daily_demand,
                    "max_daily_demand": float(np.max(future_predictions)),
                    "min_daily_demand": float(np.min(future_predictions))
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تنبؤ الطلب: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # Customer Churn Prediction - تنبؤ فقدان العملاء
    # ============================================================================
    
    def predict_customer_churn(self, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        تنبؤ فقدان العملاء
        
        Args:
            customer_id: معرف العميل (اختياري - إذا None، تنبؤ لجميع العملاء)
            
        Returns:
            Dict مع التنبؤات
        """
        try:
            if not ML_AVAILABLE:
                return {"error": "ML libraries not available"}
            
            # جلب بيانات العملاء
            customers_data = self._get_customers_data(customer_id)
            
            if len(customers_data) < 10:
                return {
                    "error": "لا توجد بيانات كافية للتنبؤ",
                    "min_customers_required": 10
                }
            
            # تحضير البيانات
            df = pd.DataFrame(customers_data)
            
            # تحديد العملاء المفقودين (لم يشتروا في آخر 90 يوم)
            cutoff_date = datetime.now() - timedelta(days=90)
            df['is_churned'] = (pd.to_datetime(df['last_purchase_date']) < cutoff_date).astype(int)
            
            # إنشاء features
            features = ['total_purchases', 'avg_order_value', 'days_since_last_purchase']
            X = df[features].values
            y = df['is_churned'].values
            
            # تدريب النموذج
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # التنبؤ
            predictions = model.predict(X)
            probabilities = model.predict_proba(X)[:, 1]
            
            # إضافة النتائج
            df['churn_probability'] = probabilities
            df['predicted_churn'] = predictions
            
            # ترتيب حسب احتمالية الفقدان
            df = df.sort_values('churn_probability', ascending=False)
            
            return {
                "success": True,
                "predictions": [
                    {
                        "customer_id": int(row['customer_id']),
                        "customer_name": row.get('customer_name', 'N/A'),
                        "churn_probability": float(row['churn_probability']),
                        "predicted_churn": bool(row['predicted_churn']),
                        "risk_level": self._get_risk_level(row['churn_probability'])
                    }
                    for _, row in df.iterrows()
                ],
                "summary": {
                    "total_customers": len(df),
                    "high_risk": len(df[df['churn_probability'] > 0.7]),
                    "medium_risk": len(df[(df['churn_probability'] > 0.4) & (df['churn_probability'] <= 0.7)]),
                    "low_risk": len(df[df['churn_probability'] <= 0.4])
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تنبؤ فقدان العملاء: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # Product Recommendations - توصيات المنتجات
    # ============================================================================
    
    def get_product_recommendations(
        self,
        customer_id: Optional[int] = None,
        product_id: Optional[int] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        الحصول على توصيات المنتجات
        
        Args:
            customer_id: معرف العميل (للتوصيات الشخصية)
            product_id: معرف المنتج (للمنتجات المشابهة)
            limit: عدد التوصيات
            
        Returns:
            Dict مع التوصيات
        """
        try:
            if customer_id:
                # توصيات شخصية للعميل
                return self._get_personalized_recommendations(customer_id, limit)
            elif product_id:
                # منتجات مشابهة
                return self._get_similar_products(product_id, limit)
            else:
                # توصيات عامة (الأكثر مبيعاً)
                return self._get_popular_products(limit)
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على التوصيات: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _get_personalized_recommendations(self, customer_id: int, limit: int) -> Dict[str, Any]:
        """توصيات شخصية للعميل"""
        # جلب تاريخ مشتريات العميل
        customer_purchases = self._get_customer_purchases(customer_id)
        
        if not customer_purchases:
            return self._get_popular_products(limit)
        
        # جلب المنتجات المشتراة
        purchased_product_ids = [p['product_id'] for p in customer_purchases]
        
        # جلب المنتجات المشابهة
        similar_products = []
        for product_id in purchased_product_ids[:5]:  # أول 5 منتجات
            similar = self._get_similar_products(product_id, limit=5)
            if similar.get('success'):
                similar_products.extend(similar.get('products', []))
        
        # إزالة التكرارات والمنتجات المشتراة مسبقاً
        seen = set(purchased_product_ids)
        recommendations = []
        for product in similar_products:
            if product['id'] not in seen:
                recommendations.append(product)
                seen.add(product['id'])
                if len(recommendations) >= limit:
                    break
        
        # إذا لم تكن كافية، أضف منتجات شائعة
        if len(recommendations) < limit:
            popular = self._get_popular_products(limit - len(recommendations))
            if popular.get('success'):
                for product in popular.get('products', []):
                    if product['id'] not in seen:
                        recommendations.append(product)
                        seen.add(product['id'])
        
        return {
            "success": True,
            "type": "personalized",
            "customer_id": customer_id,
            "products": recommendations[:limit]
        }
    
    def _get_similar_products(self, product_id: int, limit: int) -> Dict[str, Any]:
        """منتجات مشابهة"""
        # جلب معلومات المنتج
        product = self._get_product(product_id)
        if not product:
            return {"error": "المنتج غير موجود"}
        
        # جلب المنتجات من نفس الفئة
        category_products = self._get_category_products(product.get('category_id'))
        
        # ترتيب حسب الشعبية
        category_products.sort(key=lambda x: x.get('total_sales', 0), reverse=True)
        
        # إزالة المنتج الحالي
        similar = [p for p in category_products if p['id'] != product_id]
        
        return {
            "success": True,
            "type": "similar",
            "product_id": product_id,
            "products": similar[:limit]
        }
    
    def _get_popular_products(self, limit: int) -> Dict[str, Any]:
        """المنتجات الأكثر شعبية"""
        query = """
            SELECT 
                p.id,
                p.name,
                p.selling_price,
                COUNT(si.id) as total_sales,
                SUM(si.quantity) as total_quantity
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id
            WHERE p.is_active = 1
            GROUP BY p.id
            ORDER BY total_sales DESC, total_quantity DESC
            LIMIT ?
        """
        
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        params = [limit]
        
        if company_id:
            query = query.replace("WHERE", "WHERE p.company_id = ? AND")
            params.insert(0, company_id)
        
        rows = self.db_manager.fetch_all(query, tuple(params))
        
        return {
            "success": True,
            "type": "popular",
            "products": [
                {
                    "id": row['id'],
                    "name": row['name'],
                    "price": float(row['selling_price']),
                    "total_sales": row['total_sales'] or 0,
                    "total_quantity": row['total_quantity'] or 0
                }
                for row in rows
            ]
        }
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def _get_sales_history(self, product_id: Optional[int], days: int) -> List[Dict[str, Any]]:
        """جلب تاريخ المبيعات"""
        query = """
            SELECT 
                DATE(s.sale_date) as date,
                SUM(s.total_amount) as total_amount,
                COUNT(s.id) as sale_count
            FROM sales s
            WHERE s.sale_date >= date('now', '-' || ? || ' days')
        """
        params = [days]
        
        if product_id:
            query += """
                AND EXISTS (
                    SELECT 1 FROM sale_items si
                    WHERE si.sale_id = s.id AND si.product_id = ?
                )
            """
            params.append(product_id)
        
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        if company_id:
            query += " AND s.company_id = ?"
            params.append(company_id)
        
        query += " GROUP BY DATE(s.sale_date) ORDER BY date"
        
        rows = self.db_manager.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]
    
    def _get_product_sales_history(self, product_id: int, days: int) -> List[Dict[str, Any]]:
        """جلب تاريخ مبيعات منتج"""
        query = """
            SELECT 
                DATE(s.sale_date) as date,
                SUM(si.quantity) as quantity,
                SUM(si.total_price) as total_price
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE si.product_id = ?
                AND s.sale_date >= date('now', '-' || ? || ' days')
        """
        params = [product_id, days]
        
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        if company_id:
            query += " AND s.company_id = ?"
            params.append(company_id)
        
        query += " GROUP BY DATE(s.sale_date) ORDER BY date"
        
        rows = self.db_manager.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]
    
    def _get_customers_data(self, customer_id: Optional[int]) -> List[Dict[str, Any]]:
        """جلب بيانات العملاء"""
        query = """
            SELECT 
                c.id as customer_id,
                c.name as customer_name,
                COUNT(DISTINCT s.id) as total_purchases,
                AVG(s.total_amount) as avg_order_value,
                MAX(s.sale_date) as last_purchase_date,
                julianday('now') - julianday(MAX(s.sale_date)) as days_since_last_purchase
            FROM customers c
            LEFT JOIN sales s ON c.id = s.customer_id
            WHERE 1=1
        """
        params = []
        
        if customer_id:
            query += " AND c.id = ?"
            params.append(customer_id)
        
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        if company_id:
            query += " AND c.company_id = ?"
            params.append(company_id)
        
        query += " GROUP BY c.id HAVING total_purchases > 0"
        
        rows = self.db_manager.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]
    
    def _get_customer_purchases(self, customer_id: int) -> List[Dict[str, Any]]:
        """جلب مشتريات العميل"""
        query = """
            SELECT DISTINCT si.product_id
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.customer_id = ?
        """
        params = [customer_id]
        
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        if company_id:
            query += " AND s.company_id = ?"
            params.append(company_id)
        
        rows = self.db_manager.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]
    
    def _get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """جلب معلومات منتج"""
        query = "SELECT * FROM products WHERE id = ?"
        row = self.db_manager.fetch_one(query, (product_id,))
        return dict(row) if row else None
    
    def _get_category_products(self, category_id: Optional[int]) -> List[Dict[str, Any]]:
        """جلب منتجات الفئة"""
        if not category_id:
            return []
        
        query = """
            SELECT 
                p.id,
                p.name,
                p.selling_price,
                COUNT(si.id) as total_sales
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            WHERE p.category_id = ? AND p.is_active = 1
            GROUP BY p.id
        """
        params = [category_id]
        
        company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
        if company_id:
            query += " AND p.company_id = ?"
            params.append(company_id)
        
        rows = self.db_manager.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]
    
    def _get_risk_level(self, probability: float) -> str:
        """تحديد مستوى الخطر"""
        if probability > 0.7:
            return "HIGH"
        elif probability > 0.4:
            return "MEDIUM"
        else:
            return "LOW"

