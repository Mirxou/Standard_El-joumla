import os
import unittest

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import os
from pathlib import Path

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.services.carbon_service import CarbonService
from src.services.system_doctor_service import SystemDoctorService

# ==================== Test Constants ====================
# Constants for Carbon Service tests
CARBON_DEFAULT_FACTOR = 2.5  # Default carbon factor
CARBON_MOCK_ITEMS = 100  # Mock items for carbon test
CARBON_EXPECTED_FOOTPRINT = CARBON_MOCK_ITEMS * CARBON_DEFAULT_FACTOR  # 250

# Constants for System Doctor tests
DOCTOR_MOCK_ORPHANS = 5  # Mock orphan records
DOCTOR_MOCK_NEG_STOCK = 2  # Mock negative stock items
DOCTOR_EXPECTED_CLEANED = 5  # Expected cleaned orphans


# ==================== Mock Database ====================
class MockDBManager:
    """Mock Database Manager for testing"""

    def execute_scalar(self, query, params=None):
        """Mock execute_scalar with constant-based responses"""
        # Carbon service queries
        if "PRAGMA integrity_check" in query:
            return "ok"
        if "SUM(quantity)" in query:
            return CARBON_MOCK_ITEMS  # Use constant

        # Doctor Orphan Check
        if "sale_id NOT IN" in query:
            return DOCTOR_MOCK_ORPHANS  # Use constant

        # Doctor Negative Stock
        if "current_stock < 0" in query:
            return DOCTOR_MOCK_NEG_STOCK  # Use constant

        return 0

    def execute_non_query(self, query, params=None):
        """Mock execute_non_query with constant-based responses"""
        if "DELETE FROM sale_items" in query:
            return DOCTOR_MOCK_ORPHANS  # Use constant
        if "UPDATE products" in query:
            return DOCTOR_MOCK_NEG_STOCK  # Use constant
        return 0


# ==================== Test Cases ====================
class TestPhase6(unittest.TestCase):
    """Test Phase 6 - Carbon Service and System Doctor"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = MockDBManager()
        self.carbon = CarbonService(self.mock_db)
        self.doctor = SystemDoctorService(self.mock_db)

    def test_carbon_daily_footprint(self):
        """Test carbon daily footprint calculation"""
        footprint = self.carbon.get_daily_footprint("2026-01-18")
        # Using constants: 100 * 2.5 = 250
        self.assertEqual(footprint, CARBON_EXPECTED_FOOTPRINT)

    def test_carbon_monthly_footprint(self):
        """Test carbon monthly footprint"""
        footprint = self.carbon.get_monthly_footprint("2026-01")
        # Expected: daily footprint * 30 days
        expected = CARBON_EXPECTED_FOOTPRINT * 30
        self.assertEqual(footprint, expected)

    def test_doctor_orphan_check(self):
        """Test system doctor orphan check"""
        orphans = self.doctor.check_orphans()
        self.assertEqual(orphans, DOCTOR_MOCK_ORPHANS)

    def test_doctor_negative_stock(self):
        """Test system doctor negative stock check"""
        neg_stock = self.doctor.check_negative_stock()
        self.assertEqual(neg_stock, DOCTOR_MOCK_NEG_STOCK)

    def test_doctor_fix_operations(self):
        """Test system doctor fix operations"""
        # Test orphan cleaning
        cleaned = self.doctor.clean_orphans()
        self.assertEqual(cleaned, DOCTOR_EXPECTED_CLEANED)

        # Test negative stock fix
        fixed = self.doctor.fix_negative_stock()
        self.assertEqual(fixed, DOCTOR_MOCK_NEG_STOCK)

    def test_integration_carbon_and_doctor(self):
        """Test integration between carbon and doctor services"""
        # Both services should use the same mock DB
        carbon_footprint = self.carbon.get_daily_footprint("2026-01-18")
        doctor_orphans = self.doctor.check_orphans()

        self.assertEqual(carbon_footprint, CARBON_EXPECTED_FOOTPRINT)
        self.assertEqual(doctor_orphans, DOCTOR_MOCK_ORPHANS)


if __name__ == "__main__":
    unittest.main()
