"""
حوار تفاصيل الجرد
Count Details Dialog - Placeholder for complete implementation
"""
from PySide6.QtWidgets import QDialog, QMessageBox

class CountDetailsDialog(QDialog):
    """حوار تفاصيل الجرد - نسخة مبسطة"""
    
    def __init__(self, db_manager, count_id=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.count_id = count_id
        
        # TODO: Implement full dialog with:
        # - Count information (number, date, location)
        # - Products table with system vs counted quantities
        # - Variance calculations
        # - Load products button
        # - Save and complete functionality
        
        QMessageBox.information(
            self,
            "قيد التطوير",
            "حوار تفاصيل الجرد قيد التطوير.\nيمكن إضافته في المرحلة التالية."
        )
        self.reject()
