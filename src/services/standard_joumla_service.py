"""
Standard EL-joumLa Intelligence Service
خدمة ذكاء الجملة المعيارية - تحليل الهوامش والفرص
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from ..core.database_manager import DatabaseManager
from ..models.search import SearchQuery, SearchResult, SearchEntity

class StandardJoumLaService:
    """
    خدمة ذكاء الجملة المعيارية
    توفر تحليلات متقدمة لهوامش الربح وفرص الجملة
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def custom_read_sql(self, query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """
        تنفيذ استعلام SQL وإرجاع النتيجة كـ DataFrame
        """
        try:
            results = self.db.execute_query(query, params if params else [])
            if not results:
                return pd.DataFrame()
            return pd.DataFrame(results)
        except Exception as e:
            print(f"Error executing query: {e}")
            return pd.DataFrame()

    def analyze_wholesale_opportunities(self, query: SearchQuery) -> Dict[str, Any]:
        """
        تحليل فرص الجملة بناءً على معايير البحث
        """
        # 1. Fetch raw data (Prices, Costs, Stock, Sales Velocity)
        # We assume Sales Velocity is calculated elsewhere or we approximate it here
        # For this version, we'll fetch basic product data + calculated fields
        
        sql = """
            SELECT 
                p.id, p.name, p.sku, p.barcode,
                p.cost_price, p.wholesale_price, p.selling_price as retail_price,
                p.current_stock, p.min_stock,
                (p.wholesale_price - p.cost_price) as margin_value,
                CASE 
                    WHEN p.wholesale_price > 0 THEN ((p.wholesale_price - p.cost_price) / p.wholesale_price) * 100 
                    ELSE 0 
                END as margin_percent,
                (p.current_stock * p.wholesale_price) as stock_valuation
            FROM products p
            WHERE p.is_active = 1
        """
        
        params = []
        if query.keyword:
            sql += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.barcode LIKE ?)"
            params.extend([f"%{query.keyword}%"] * 3)

        df = self.custom_read_sql(sql, params)
        
        if df.empty:
            return {
                "records": [],
                "summary": {"total_valuation": 0, "avg_margin": 0}
            }
            
        # 2. Advanced Analysis using Pandas
        # Categorize Margins
        conditions = [
            (df['margin_percent'] < 5),
            (df['margin_percent'] >= 5) & (df['margin_percent'] < 15),
            (df['margin_percent'] >= 15)
        ]
        choices = ['حرج', 'متوسط', 'ممتاز']
        df['profitability_grade'] = np.select(conditions, choices, default='غير معروف')
        
        # Opportunity Score: (Margin % * Stock) / 100 (Simple heuristic for now)
        # In a real scenario, we'd multiply by Sales Velocity
        df['opportunity_score'] = (df['margin_percent'] * df['current_stock']) / 100
        
        # Sort by Opportunity Score Descending
        df = df.sort_values(by='opportunity_score', ascending=False)
        
        # 3. Apply Pagination (Manual since we pulled all for analysis - optimization needed for huge DBs)
        start = query.offset
        end = start + query.limit
        paginated_df = df.iloc[start:end]
        
        # 4. Prepare Result
        records = paginated_df.to_dict('records')
        
        summary = {
            "total_valuation": float(df['stock_valuation'].sum()),
            "avg_margin": float(df['margin_percent'].mean()),
            "potential_profit": float((df['margin_value'] * df['current_stock']).sum())
        }
        
        return {
            "records": records,
            "summary": summary,
            "total_count": len(df)
        }

    def get_margin_heatmap_color(self, margin_percent: float) -> str:
        """
        إرجاع كود اللون (Hex) بناءً على نسبة الهامش
        Visual Heatmap helper
        """
        if margin_percent < 0:
            return "#EF4444"  # Red (Loss)
        elif margin_percent < 5:
            return "#F97316"  # Orange (Low)
        elif margin_percent < 15:
            return "#EAB308"  # Yellow (Moderate)
        elif margin_percent < 25:
            return "#22C55E"  # Green (Good)
        else:
            return "#3B82F6"  # Blue (Excellent/Supercharged)

    def update_wholesale_price(self, product_id: int, new_price: float) -> bool:
        """
        تحديث سعر الجملة لمنتج
        """
        try:
            sql = "UPDATE products SET wholesale_price = ? WHERE id = ?"
            self.db.execute_update(sql, [new_price, product_id])
            return True
        except Exception as e:
            print(f"Error updating wholesale price: {e}")
            return False
