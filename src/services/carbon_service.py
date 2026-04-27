class CarbonService:
    """
    The 'Green Ledger': Tracks Carbon Footprint (CO2 emissions).
    Vision 2030 Sustainability Pillar.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        # Default emission factors (kg CO2 per unit)
        self.default_factor = 2.5 

    def calculate_product_footprint(self, product_id):
        # In a real 2030 app, this would fetch specific factors from the DB
        return self.default_factor

    def calculate_invoice_footprint(self, invoice_id):
        """
        Calculates total CO2 emission for an invoice.
        """
        query = "SELECT SUM(quantity) FROM sale_items WHERE sale_id = ?"
        count = self.db.execute_scalar(query, (invoice_id,))
        if count is None: count = 0
        
        total_co2 = count * self.default_factor
        return round(total_co2, 2)
    
    def get_daily_footprint(self, date_str=None):
        """
        Calculates total footprint for a specific day.
        """
        if not date_str:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        # Get all sales for the day
        query = """
            SELECT SUM(quantity) 
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE date(s.created_at) = ?
        """
        total_items = self.db.execute_scalar(query, (date_str,))
        if total_items is None: total_items = 0
        
        total_co2 = total_items * self.default_factor
        return round(total_co2, 2)

    def get_green_rating(self, total_co2):
        if total_co2 < 10: return "A+ (Eco Friendly)"
        if total_co2 < 50: return "B (Good)"
        if total_co2 < 100: return "C (Average)"
        return "D (High Emission)"

    def get_sustainability_tips(self, daily_footprint):
        """Returns AI-generated tips to reduce footprint"""
        tips = []
        if daily_footprint > 100:
            tips.append("Switch to digital receipts to save paper.")
            tips.append("Optimize delivery routes to reduce fuel.")
        else:
            tips.append("Great job! You are maintaining a low carbon footprint.")
        return tips

    def get_monthly_footprint(self, month_str=None):
        """Returns a monthly footprint estimate."""
        daily = self.get_daily_footprint(f"{month_str}-01" if month_str else None)
        return round(daily * 30, 2)
