from typing import Dict, List, Any
from ..core.database_manager import DatabaseManager

class WholesaleAnalyticsService:
    """
    خدمة تحليلات الجملة
    Provides aggregated data for the Wholesale Dashboard.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        
    def get_kpi_summary(self) -> Dict[str, Any]:
        """
        Get Key Performance Indicators for Wholesale Mode.
        Revenue: Total of 'sales' where source logic implies wholesale (or just all sales if mixed).
        For now, we track ALL sales as 'Wholesale System Sales' since we moved to this mode, 
        OR ideally we filter by 'invoice_number' prefix 'J-' (Joumla).
        """
        # 1. Total Revenue (Joumla)
        sql_rev = """
            SELECT SUM(total_amount), SUM(final_amount), COUNT(*) 
            FROM sales 
            WHERE invoice_number LIKE 'J-%'
        """
        row_rev = self.db.fetch_one(sql_rev)
        total_rev = row_rev[1] if row_rev and row_rev[1] else 0.0
        deal_count = row_rev[2] if row_rev else 0
        
        # 2. Total Profit (from sale_items related to J- sales)
        sql_profit = """
            SELECT SUM(si.profit)
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE s.invoice_number LIKE 'J-%'
        """
        row_prof = self.db.fetch_one(sql_profit)
        total_profit = row_prof[0] if row_prof and row_prof[0] else 0.0
        
        return {
            "total_revenue": total_rev,
            "total_profit": total_profit,
            "deal_count": deal_count
        }

    def get_top_customers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Top Wholesale Customers by Revenue"""
        sql = """
            SELECT customer_name, SUM(final_amount) as total_spent, COUNT(*) as deals
            FROM sales
            WHERE invoice_number LIKE 'J-%'
            GROUP BY customer_name
            ORDER BY total_spent DESC
            LIMIT ?
        """
        rows = self.db.fetch_all(sql, [limit])
        return [
            {"name": r[0], "total": r[1], "count": r[2]} 
            for r in rows
        ]

    def get_top_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Top Moving Products in Wholesale"""
        sql = """
            SELECT p.name, SUM(si.quantity) as total_qty, SUM(si.total_price) as total_val
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN products p ON p.id = si.product_id
            WHERE s.invoice_number LIKE 'J-%'
            GROUP BY p.name
            ORDER BY total_qty DESC
            LIMIT ?
        """
        rows = self.db.fetch_all(sql, [limit])
        return [
            {"name": r[0], "qty": r[1], "value": r[2]}
            for r in rows
        ]
