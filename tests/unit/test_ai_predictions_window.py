#!/usr/bin/env python3
"""
اختبارات AI Predictions Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.ai_predictions_window import AIPredictionsWindow

app = QApplication.instance() or QApplication([])


class TestAIPredictionsWindow:
    """اختبارات نافذة توقعات الذكاء الاصطناعي"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        with patch("src.ui.windows.ai_predictions_window.AIPredictionService"), patch(
            "src.ui.windows.ai_predictions_window.PredictionWorker"
        ) as MockWorker:
            # Prevent the mock worker from actually starting a thread
            MockWorker.return_value.start = MagicMock()
            MockWorker.return_value.prediction_finished.connect = MagicMock()
            yield AIPredictionsWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
        assert window.ai_service is not None

    def test_forecast_sales(self, window):
        """اختبار تنبؤ المبيعات"""
        window.sales_days_spin.setValue(10)
        window.forecast_sales()
        assert window.prediction_worker is not None

    def test_forecast_demand(self, window):
        """اختبار تنبؤ الطلب"""
        window.demand_product_combo.addItem("Product 1", 1)
        window.demand_product_combo.setCurrentIndex(1)
        window.forecast_demand()
        assert window.prediction_worker is not None

    def test_predict_churn(self, window):
        """اختبار تحليل فقدان العملاء"""
        window.predict_churn()
        assert window.prediction_worker is not None

    def test_get_recommendations(self, window):
        """اختبار الحصول على التوصيات"""
        window.get_recommendations()
        assert window.prediction_worker is not None

    def test_refresh_data(self, window):
        """اختبار تحديث البيانات"""
        window.refresh_data()
        assert window.statusBar().currentMessage() == "تم التحديث"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
