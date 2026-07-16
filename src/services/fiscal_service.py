import os

import pandas as pd


class FiscalService:
    """
    Algerian Fiscal Reporting Engine (G50 & Etat 104)
    Generates tax declarations automatically.
    """

    # Configurable tax rates (can be overridden per-instance or via settings)
    DEFAULT_TAP_RATE = 0.02       # Taxe sur l'Activité Professionnelle (2%)
    DEFAULT_TIMBRE_RATE = 0.01    # Timbre Fiscal (1%)

    def __init__(self, db_manager):
        self.db = db_manager
        self.tap_rate = self.DEFAULT_TAP_RATE
        self.timbre_rate = self.DEFAULT_TIMBRE_RATE
        self._load_rates_from_settings()

    def _load_rates_from_settings(self):
        """Load TAP and Timbre rates from the settings table if available."""
        try:
            rows = self.db.execute_query(
                "SELECT key, value FROM app_settings WHERE key IN (?, ?)",
                ("fiscal_tap_rate", "fiscal_timbre_rate"),
            )
            rate_map = {row[0]: float(row[1]) for row in rows}
            if "fiscal_tap_rate" in rate_map:
                self.tap_rate = rate_map["fiscal_tap_rate"]
            if "fiscal_timbre_rate" in rate_map:
                self.timbre_rate = rate_map["fiscal_timbre_rate"]
        except Exception:
            pass  # Fall back to defaults

    def save_rates_to_settings(self, tap_rate: float = None, timbre_rate: float = None) -> bool:
        """Persist TAP and Timbre rates to the settings table."""
        try:
            if tap_rate is not None:
                self.tap_rate = tap_rate
                self.db.execute_query(
                    "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
                    ("fiscal_tap_rate", str(tap_rate)),
                )
            if timbre_rate is not None:
                self.timbre_rate = timbre_rate
                self.db.execute_query(
                    "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
                    ("fiscal_timbre_rate", str(timbre_rate)),
                )
            return True
        except Exception:
            return False

    def generate_g50(self, month: int, year: int) -> dict:
        """
        Calculate G50 Declaration metrics for a specific month.
        Returns calculated TAP, TVA, and Timbre.
        """
        # Fetch Sales for the period
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"

        sales = self.db.execute_query(
            "SELECT total_amount, tax_amount FROM sales WHERE sale_date >= ? AND sale_date < ?",
            (start_date, end_date),
        )

        total_turnover = sum(row[0] for row in sales)
        total_vat_collected = sum(row[1] for row in sales)

        # Algerian Tax Rules (2025)
        # TAP & Timbre rates are configurable via settings or constructor
        tap_amount = total_turnover * self.tap_rate
        timbre_amount = total_turnover * self.timbre_rate

        return {
            "period": f"{month}/{year}",
            "turnover_ht": total_turnover - total_vat_collected,
            "turnover_ttc": total_turnover,
            "vat_collected": total_vat_collected,
            "tap_rate": self.tap_rate,
            "tap_amount": tap_amount,
            "timbre_rate": self.timbre_rate,
            "timbre_amount": timbre_amount,
            "total_to_pay": total_vat_collected + tap_amount + timbre_amount,
        }

    def generate_etat_104(self, year: int, output_path: str):
        """
        Generates 'Etat 104' (Client Annual List) Excel file.
        Lists all clients with annual transactions > 100,000 DA.
        """
        query = """
            SELECT
                c.name as 'Nom et Prénom / Raison Sociale',
                c.tax_id as 'NIF',
                c.address as 'Adresse',
                SUM(s.total_amount) as 'Montant TTC',
                SUM(s.tax_amount) as 'Montant TVA'
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE strftime('%Y', s.sale_date) = ?
            GROUP BY c.id
            HAVING SUM(s.total_amount) > 100000
        """

        conn = self.db.get_connection()
        df = pd.read_sql_query(query, conn, params=(str(year),))
        conn.close()

        if df.empty:
            return False, "لا توجد بيانات (مبيعات > 100,000 دج) لهذا العام."

        # Add HT Column
        df["Montant HT"] = df["Montant TTC"] - df["Montant TVA"]

        # Reorder for Official Format
        df = df[
            [
                "NIF",
                "Nom et Prénom / Raison Sociale",
                "Adresse",
                "Montant HT",
                "Montant TVA",
                "Montant TTC",
            ]
        ]

        # Save to Excel
        try:
            full_path = os.path.join(output_path, f"Etat_104_{year}.xlsx")
            df.to_excel(full_path, index=False)
            return True, full_path
        except Exception as e:
            return False, str(e)
