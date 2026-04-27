class SystemDoctorService:
    """
    The 'System Doctor': Self-healing diagnostic tool.
    Checks for data integrity and fixes common issues.
    Vision 2030 Stability Pillar.
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def diagnose(self):
        issues = []
        
        # Check 0: Database Integrity (SQLite specific)
        try:
            integrity = self.db.execute_scalar("PRAGMA integrity_check")
            if integrity != "ok":
                issues.append(f"CRITICAL: Database integrity check failed: {integrity}")
        except Exception as e:
            issues.append(f"Failed to check integrity: {e}")

        # Check 1: Orphan Sale Items (Items with no parent Invoice)
        q1 = "SELECT count(*) FROM sale_items WHERE sale_id NOT IN (SELECT id FROM sales)"
        try:
            orphans = self.db.execute_scalar(q1)
            if orphans and orphans > 0:
                issues.append(f"Found {orphans} orphaned sale items")
        except Exception:
            pass

        # Check 2: Negative Stock (Logical error)
        q2 = "SELECT count(*) FROM products WHERE current_stock < 0"
        try:
            neg_stock = self.db.execute_scalar(q2)
            if neg_stock and neg_stock > 0:
                issues.append(f"Found {neg_stock} products with negative stock")
        except Exception:
            pass

        return issues

    def check_orphans(self):
        """Compatibility helper: return orphaned sale items count."""
        return self.db.execute_scalar("SELECT count(*) FROM sale_items WHERE sale_id NOT IN (SELECT id FROM sales)") or 0

    def check_negative_stock(self):
        """Compatibility helper: return negative stock count."""
        return self.db.execute_scalar("SELECT count(*) FROM products WHERE current_stock < 0") or 0

    def clean_orphans(self):
        """Compatibility helper: delete orphan items."""
        return self.db.execute_non_query("DELETE FROM sale_items WHERE sale_id NOT IN (SELECT id FROM sales)") or 0

    def fix_negative_stock(self):
        """Compatibility helper: reset negative stock to 0."""
        return self.db.execute_non_query("UPDATE products SET current_stock = 0 WHERE current_stock < 0") or 0

    def heal(self):
        reports = []
        
        # Heal 1: Delete Orphan Items
        try:
            q_fix1 = "DELETE FROM sale_items WHERE sale_id NOT IN (SELECT id FROM sales)"
            count1 = self.db.execute_non_query(q_fix1)
            if count1 > 0:
                reports.append(f"Cleaned up {count1} orphaned items")
        except Exception as e:
            reports.append(f"Failed to fix orphans: {e}")
            
        # Heal 2: Fix Negative Stock (Reset to 0)
        try:
            q_fix2 = "UPDATE products SET current_stock = 0 WHERE current_stock < 0"
            count2 = self.db.execute_non_query(q_fix2)
            if count2 > 0:
                reports.append(f"Reset {count2} products with negative stock to 0")
        except Exception as e:
            reports.append(f"Failed to fix negative stock: {e}")
            
        return reports
