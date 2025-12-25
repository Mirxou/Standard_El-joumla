#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics Service - خدمة التحليلات المتقدمة
تحليلات متقدمة، Data Visualization، Custom Dashboards
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)


class AnalyticsService:
    """خدمة التحليلات المتقدمة"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة التحليلات
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
    
    # ============================================================================
    # Sales Analytics - تحليلات المبيعات
    # ============================================================================
    
    def get_sales_trends(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        تحليل اتجاهات المبيعات
        
        Args:
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            
        Returns:
            Dict مع البيانات والاتجاهات
        """
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            query = """
                SELECT 
                    DATE(sale_date) as date,
                    COUNT(*) as sale_count,
                    SUM(total_amount) as total_amount,
                    AVG(total_amount) as avg_amount
                FROM sales
                WHERE sale_date >= ? AND sale_date <= ?
            """
            params = [start_date.date(), end_date.date()]
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            query += " GROUP BY DATE(sale_date) ORDER BY date"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            if not rows:
                return {"error": "لا توجد بيانات"}
            
            data = [dict(row) for row in rows]
            
            # حساب الاتجاهات
            if PANDAS_AVAILABLE and len(data) > 1:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                
                # حساب معدل النمو
                growth_rate = ((df['total_amount'].iloc[-1] - df['total_amount'].iloc[0]) / df['total_amount'].iloc[0] * 100) if df['total_amount'].iloc[0] > 0 else 0
                
                # حساب المتوسط المتحرك
                df['moving_avg'] = df['total_amount'].rolling(window=7, min_periods=1).mean()
                
                return {
                    "success": True,
                    "data": data,
                    "trends": {
                        "growth_rate": float(growth_rate),
                        "total_sales": float(df['total_amount'].sum()),
                        "avg_daily": float(df['total_amount'].mean()),
                        "peak_day": df.loc[df['total_amount'].idxmax(), 'date'].isoformat() if len(df) > 0 else None,
                        "moving_avg": df['moving_avg'].tolist()
                    }
                }
            else:
                total = sum(item['total_amount'] for item in data)
                return {
                    "success": True,
                    "data": data,
                    "trends": {
                        "total_sales": float(total),
                        "avg_daily": float(total / len(data)) if data else 0
                    }
                }
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل اتجاهات المبيعات: {e}", exc_info=True)
            return {"error": str(e)}
    
    def get_sales_by_category(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """تحليل المبيعات حسب الفئة"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            query = """
                SELECT 
                    c.name as category_name,
                    COUNT(DISTINCT s.id) as sale_count,
                    SUM(si.quantity) as total_quantity,
                    SUM(si.total_price) as total_amount
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE s.sale_date >= ? AND s.sale_date <= ?
            """
            params = [start_date.date(), end_date.date()]
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                query += " AND s.company_id = ?"
                params.append(company_id)
            
            query += " GROUP BY c.id, c.name ORDER BY total_amount DESC"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            return {
                "success": True,
                "data": [
                    {
                        "category": row['category_name'] or 'بدون فئة',
                        "sale_count": row['sale_count'],
                        "total_quantity": row['total_quantity'],
                        "total_amount": float(row['total_amount'])
                    }
                    for row in rows
                ]
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل المبيعات حسب الفئة: {e}", exc_info=True)
            return {"error": str(e)}
    
    def get_sales_by_customer(self, limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """تحليل المبيعات حسب العميل"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            query = """
                SELECT 
                    c.id,
                    c.name as customer_name,
                    COUNT(DISTINCT s.id) as sale_count,
                    SUM(s.total_amount) as total_amount,
                    AVG(s.total_amount) as avg_amount
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE s.sale_date >= ? AND s.sale_date <= ?
            """
            params = [start_date.date(), end_date.date()]
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                query += " AND s.company_id = ?"
                params.append(company_id)
            
            query += " GROUP BY c.id, c.name ORDER BY total_amount DESC LIMIT ?"
            params.append(limit)
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            return {
                "success": True,
                "data": [
                    {
                        "customer_id": row['id'],
                        "customer_name": row['customer_name'],
                        "sale_count": row['sale_count'],
                        "total_amount": float(row['total_amount']),
                        "avg_amount": float(row['avg_amount'])
                    }
                    for row in rows
                ]
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل المبيعات حسب العميل: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # Inventory Analytics - تحليلات المخزون
    # ============================================================================
    
    def get_inventory_turnover(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """تحليل معدل دوران المخزون"""
        try:
            query = """
                SELECT 
                    p.id,
                    p.name,
                    p.current_stock,
                    SUM(si.quantity) as total_sold,
                    AVG(p.cost_price) as avg_cost_price
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id
                WHERE 1=1
            """
            params = []
            
            if product_id:
                query += " AND p.id = ?"
                params.append(product_id)
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                query += " AND p.company_id = ?"
                params.append(company_id)
            
            query += " GROUP BY p.id, p.name, p.current_stock"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            results = []
            for row in rows:
                current_stock = row['current_stock'] or 0
                total_sold = row['total_sold'] or 0
                
                # حساب معدل الدوران (عدد المرات التي تم بيع المخزون فيها)
                turnover_rate = (total_sold / current_stock) if current_stock > 0 else 0
                
                # حساب أيام المخزون (كم يوم يحتاج لبيع المخزون الحالي)
                days_of_inventory = (current_stock / (total_sold / 30)) if total_sold > 0 else 999
                
                results.append({
                    "product_id": row['id'],
                    "product_name": row['name'],
                    "current_stock": current_stock,
                    "total_sold": total_sold,
                    "turnover_rate": float(turnover_rate),
                    "days_of_inventory": float(days_of_inventory),
                    "status": "HIGH" if turnover_rate > 2 else "MEDIUM" if turnover_rate > 1 else "LOW"
                })
            
            return {
                "success": True,
                "data": results
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل معدل دوران المخزون: {e}", exc_info=True)
            return {"error": str(e)}
    
    def get_stock_alerts(self) -> Dict[str, Any]:
        """تحليل تنبيهات المخزون"""
        try:
            query = """
                SELECT 
                    p.id,
                    p.name,
                    p.current_stock,
                    p.min_stock,
                    p.selling_price,
                    (p.current_stock - p.min_stock) as stock_diff
                FROM products p
                WHERE p.is_active = 1
            """
            params = []
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                query += " AND p.company_id = ?"
                params.append(company_id)
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            low_stock = []
            out_of_stock = []
            overstocked = []
            
            for row in rows:
                current_stock = row['current_stock'] or 0
                min_stock = row['min_stock'] or 0
                
                if current_stock <= 0:
                    out_of_stock.append({
                        "product_id": row['id'],
                        "product_name": row['name'],
                        "current_stock": current_stock,
                        "min_stock": min_stock
                    })
                elif current_stock <= min_stock:
                    low_stock.append({
                        "product_id": row['id'],
                        "product_name": row['name'],
                        "current_stock": current_stock,
                        "min_stock": min_stock,
                        "needed": min_stock - current_stock
                    })
                elif current_stock > min_stock * 3:
                    overstocked.append({
                        "product_id": row['id'],
                        "product_name": row['name'],
                        "current_stock": current_stock,
                        "min_stock": min_stock
                    })
            
            return {
                "success": True,
                "alerts": {
                    "out_of_stock": out_of_stock,
                    "low_stock": low_stock,
                    "overstocked": overstocked
                },
                "summary": {
                    "out_of_stock_count": len(out_of_stock),
                    "low_stock_count": len(low_stock),
                    "overstocked_count": len(overstocked)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل تنبيهات المخزون: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # Financial Analytics - التحليلات المالية
    # ============================================================================
    
    def get_profit_margin_analysis(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """تحليل هامش الربح"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            query = """
                SELECT 
                    p.id,
                    p.name,
                    SUM(si.quantity) as total_quantity,
                    SUM(si.total_price) as total_revenue,
                    SUM(si.quantity * p.cost_price) as total_cost,
                    (SUM(si.total_price) - SUM(si.quantity * p.cost_price)) as total_profit
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE s.sale_date >= ? AND s.sale_date <= ?
            """
            params = [start_date.date(), end_date.date()]
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                query += " AND s.company_id = ?"
                params.append(company_id)
            
            query += " GROUP BY p.id, p.name ORDER BY total_profit DESC"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            
            results = []
            total_revenue = 0
            total_cost = 0
            
            for row in rows:
                revenue = float(row['total_revenue'])
                cost = float(row['total_cost'])
                profit = float(row['total_profit'])
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                total_revenue += revenue
                total_cost += cost
                
                results.append({
                    "product_id": row['id'],
                    "product_name": row['name'],
                    "total_quantity": row['total_quantity'],
                    "revenue": revenue,
                    "cost": cost,
                    "profit": profit,
                    "margin_percent": float(margin)
                })
            
            overall_margin = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0
            
            return {
                "success": True,
                "data": results,
                "summary": {
                    "total_revenue": total_revenue,
                    "total_cost": total_cost,
                    "total_profit": total_revenue - total_cost,
                    "overall_margin_percent": float(overall_margin)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل هامش الربح: {e}", exc_info=True)
            return {"error": str(e)}
    
    def get_cash_flow_analysis(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """تحليل التدفق النقدي"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # المبيعات (تدفق نقدي وارد)
            sales_query = """
                SELECT 
                    DATE(sale_date) as date,
                    SUM(total_amount) as amount
                FROM sales
                WHERE sale_date >= ? AND sale_date <= ?
            """
            sales_params = [start_date.date(), end_date.date()]
            
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            if company_id:
                sales_query += " AND company_id = ?"
                sales_params.append(company_id)
            
            sales_query += " GROUP BY DATE(sale_date) ORDER BY date"
            
            sales_rows = self.db_manager.fetch_all(sales_query, tuple(sales_params))
            
            # المشتريات (تدفق نقدي صادر)
            purchases_query = """
                SELECT 
                    DATE(purchase_date) as date,
                    SUM(total_amount) as amount
                FROM purchases
                WHERE purchase_date >= ? AND purchase_date <= ?
            """
            purchases_params = [start_date.date(), end_date.date()]
            
            if company_id:
                purchases_query += " AND company_id = ?"
                purchases_params.append(company_id)
            
            purchases_query += " GROUP BY DATE(purchase_date) ORDER BY date"
            
            purchases_rows = self.db_manager.fetch_all(purchases_query, tuple(purchases_params))
            
            # المدفوعات (تدفق نقدي صادر)
            payments_query = """
                SELECT 
                    DATE(payment_date) as date,
                    SUM(amount) as amount
                FROM payments
                WHERE payment_date >= ? AND payment_date <= ?
            """
            payments_params = [start_date.date(), end_date.date()]
            
            if company_id:
                payments_query += " AND company_id = ?"
                payments_params.append(company_id)
            
            payments_query += " GROUP BY DATE(payment_date) ORDER BY date"
            
            payments_rows = self.db_manager.fetch_all(payments_query, tuple(payments_params))
            
            # تجميع البيانات
            cash_flow = {}
            
            for row in sales_rows:
                date = row['date']
                if date not in cash_flow:
                    cash_flow[date] = {"inflow": 0, "outflow": 0}
                cash_flow[date]["inflow"] += float(row['amount'])
            
            for row in purchases_rows:
                date = row['date']
                if date not in cash_flow:
                    cash_flow[date] = {"inflow": 0, "outflow": 0}
                cash_flow[date]["outflow"] += float(row['amount'])
            
            for row in payments_rows:
                date = row['date']
                if date not in cash_flow:
                    cash_flow[date] = {"inflow": 0, "outflow": 0}
                cash_flow[date]["outflow"] += float(row['amount'])
            
            # تحويل إلى قائمة
            flow_data = [
                {
                    "date": date.isoformat() if isinstance(date, datetime) else str(date),
                    "inflow": flow["inflow"],
                    "outflow": flow["outflow"],
                    "net_flow": flow["inflow"] - flow["outflow"]
                }
                for date, flow in sorted(cash_flow.items())
            ]
            
            total_inflow = sum(item["inflow"] for item in flow_data)
            total_outflow = sum(item["outflow"] for item in flow_data)
            
            return {
                "success": True,
                "data": flow_data,
                "summary": {
                    "total_inflow": total_inflow,
                    "total_outflow": total_outflow,
                    "net_flow": total_inflow - total_outflow
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل التدفق النقدي: {e}", exc_info=True)
            return {"error": str(e)}
    
    # ============================================================================
    # Export Functions - وظائف التصدير
    # ============================================================================
    
    def export_to_json(self, data: Dict[str, Any], file_path: str) -> bool:
        """تصدير البيانات إلى JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            self.logger.error(f"❌ خطأ في تصدير JSON: {e}", exc_info=True)
            return False
    
    def export_to_csv(self, data: List[Dict[str, Any]], file_path: str) -> bool:
        """تصدير البيانات إلى CSV"""
        try:
            if not PANDAS_AVAILABLE:
                return False
            
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            self.logger.error(f"❌ خطأ في تصدير CSV: {e}", exc_info=True)
            return False
    
    def export_to_excel(self, data: Dict[str, List[Dict[str, Any]]], file_path: str) -> bool:
        """تصدير البيانات إلى Excel (متعدد الأوراق)"""
        try:
            if not PANDAS_AVAILABLE:
                return False
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, sheet_data in data.items():
                    df = pd.DataFrame(sheet_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return True
        except Exception as e:
            self.logger.error(f"❌ خطأ في تصدير Excel: {e}", exc_info=True)
            return False

