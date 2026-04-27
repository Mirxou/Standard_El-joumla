import pandas as pd
from datetime import datetime
import os

class FiscalService:
    """
    Algerian Fiscal Reporting Engine (G50 & Etat 104)
    Generates tax declarations automatically.
    """
    def __init__(self, db_manager):
        self.db = db_manager

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
            (start_date, end_date)
        )
        
        total_turnover = sum(row[0] for row in sales)
        total_vat_collected = sum(row[1] for row in sales)
        
        # Algerian Tax Rules (2025)
        # TAP (Taxe sur l'Activité Professionnelle) = 1.5% or 2% usually. Let's assume 2%.
        tap_rate = 0.02 
        tap_amount = total_turnover * tap_rate
        
        # Timbre Fiscal (Stamp Duty) - Simplified Logic
        # > 100 DA = 1%
        timbre_amount = total_turnover * 0.01 
        
        return {
            "period": f"{month}/{year}",
            "turnover_ht": total_turnover - total_vat_collected,
            "turnover_ttc": total_turnover,
            "vat_collected": total_vat_collected,
            "tap_amount": tap_amount,
            "timbre_amount": timbre_amount,
            "total_to_pay": total_vat_collected + tap_amount + timbre_amount
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
        df['Montant HT'] = df['Montant TTC'] - df['Montant TVA']
        
        # Reorder for Official Format
        df = df[[
            'NIF', 'Nom et Prénom / Raison Sociale', 'Adresse', 
            'Montant HT', 'Montant TVA', 'Montant TTC'
        ]]
        
        # Save to Excel
        try:
            full_path = os.path.join(output_path, f"Etat_104_{year}.xlsx")
            df.to_excel(full_path, index=False)
            return True, full_path
        except Exception as e:
            return False, str(e)
