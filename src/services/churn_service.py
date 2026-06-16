import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Churn Prediction Service
Uses machine learning to predict customer churn.
"""

from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


class ChurnPredictionService:
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.model_path = Path(__file__).parent.parent / "data" / "churn_model.joblib"
        self.model = None
        self.load_model()

    def load_model(self):
        """Loads the trained model from disk."""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                if self.logger:
                    self.logger.info("Churn prediction model loaded successfully.")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to load churn model: {e}")
        else:
            if self.logger:
                self.logger.warning("Churn model not found. Needs training.")

    def _get_feature_data(self):
        """Fetches sales data and engineers features (RFM)."""
        query = "SELECT customer_id, sale_date, final_amount FROM sales WHERE status = 'confirmed'"
        sales_data = self.db_manager.fetch_all(query)
        if not sales_data:
            return pd.DataFrame()

        df = pd.DataFrame(sales_data, columns=["customer_id", "sale_date", "amount"])
        df["sale_date"] = pd.to_datetime(df["sale_date"])

        snapshot_date = df["sale_date"].max() + timedelta(days=1)

        # Calculate RFM features
        rfm = df.groupby("customer_id").agg(
            {
                "sale_date": lambda date: (snapshot_date - date.max()).days,
                "customer_id": "count",
                "amount": "sum",
            }
        )
        rfm.rename(
            columns={
                "sale_date": "Recency",
                "customer_id": "Frequency",
                "amount": "MonetaryValue",
            },
            inplace=True,
        )

        return rfm

    def train_model(self):
        """Trains the churn prediction model and saves it."""
        if self.logger:
            self.logger.info("Starting churn model training...")

        rfm_df = self._get_feature_data()
        if rfm_df.empty:
            if self.logger:
                self.logger.warning("No sales data available to train churn model.")
            return False, "No data"

        # Define churn: inactive for more than 90 days (high recency score)
        rfm_df["Churn"] = (rfm_df["Recency"] > 90).astype(int)

        X = rfm_df[["Recency", "Frequency", "MonetaryValue"]]
        y = rfm_df["Churn"]

        if len(y.unique()) < 2:
            if self.logger:
                self.logger.warning("Not enough churn diversity to train model.")
            return False, "Not enough diversity"

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        model = LogisticRegression(random_state=42)
        model.fit(X_train, y_train)

        # Evaluate model
        preds = model.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        if self.logger:
            self.logger.info(f"Churn model training complete. Accuracy: {accuracy:.2f}")

        # Save model
        try:
            self.model_path.parent.mkdir(exist_ok=True)
            joblib.dump(model, self.model_path)
            self.model = model
            if self.logger:
                self.logger.info(f"Churn model saved to {self.model_path}")
            return True, f"Success, Accuracy: {accuracy:.2f}"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save churn model: {e}")
            return False, str(e)

    def predict_churn_for_customer(self, customer_id: int):
        """Predicts churn probability for a single customer."""
        if not self.model:
            return None, "Model not trained"

        try:
            # Get features for the specific customer
            query = "SELECT sale_date, final_amount FROM sales WHERE customer_id = ? AND status = 'confirmed'"
            sales = self.db_manager.fetch_all(query, (customer_id,))
            if not sales:
                return 0.0, "No sales history"  # No history, low risk

            df = pd.DataFrame(sales, columns=["sale_date", "amount"])
            df["sale_date"] = pd.to_datetime(df["sale_date"])

            snapshot_date = datetime.now()

            recency = (snapshot_date - df["sale_date"].max()).days
            frequency = len(df)
            monetary = df["amount"].sum()

            features = np.array([recency, frequency, monetary]).reshape(1, -1)

            # Predict probability [prob_not_churn, prob_churn]
            churn_probability = self.model.predict_proba(features)[0][1]

            return churn_probability, "Success"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to predict churn for customer {customer_id}: {e}")
            return None, str(e)
