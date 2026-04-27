import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ai.predictive_analytics import PredictiveEngine

class AIPredictionService:
    """
    The 'Oracle': AI-driven insights for Sales and Inventory.
    Uses simple statistical learning (Regression/Moving Average) to forecast trends.
    """
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self.engine = PredictiveEngine(db_manager)
        
    def get_proactive_insights(self):
        """Delegate to PredictiveEngine"""
        return self.engine.generate_proactive_insights()

    def predict_sales_next_month(self):
        """
        Predict total sales for the upcoming month based on historical daily sales.
        """
        # 1. Fetch Historical Data (Last 90 days)
        query = """
            SELECT sale_date, SUM(total_amount) as daily_total
            FROM sales 
            GROUP BY sale_date 
            ORDER BY sale_date ASC
        """
        conn = self.db.get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty or len(df) < 10:
            return 0.0, "Insufficient data for prediction"

        # 2. Preprocess
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        # Convert dates to ordinal for linear regression
        df['date_ordinal'] = df['sale_date'].map(pd.Timestamp.toordinal)
        
        # 3. Simple Linear Regression (y = mx + b)
        X = df['date_ordinal'].values
        y = df['daily_total'].values
        
        # Calculate slope (m) and intercept (b)
        n = len(X)
        m = (n * np.sum(X*y) - np.sum(X) * np.sum(y)) / (n * np.sum(X**2) - (np.sum(X))**2)
        b = (np.sum(y) - m * np.sum(X)) / n
        
        # 4. Forecast next 30 days
        last_date = df['sale_date'].max()
        future_total = 0
        
        for i in range(1, 31):
            future_date = last_date + timedelta(days=i)
            future_ordinal = future_date.toordinal()
            prediction = m * future_ordinal + b
            if prediction < 0: prediction = 0
            future_total += prediction
            
        return round(future_total, 2), "Growth Trend" if m > 0 else "Decline Trend"

    def detect_anomalies(self):
        """
        Flags sales transactions that are > 3 standard deviations from the mean.
        """
        query = "SELECT id, invoice_number, total_amount FROM sales"
        conn = self.db.get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty: return []
        
        mean = df['total_amount'].mean()
        std = df['total_amount'].std()
        
        # Z-Score Anomaly Detection
        threshold = 3 * std
        anomalies = df[df['total_amount'] > (mean + threshold)]
        
        return anomalies[['invoice_number', 'total_amount']].to_dict('records')
