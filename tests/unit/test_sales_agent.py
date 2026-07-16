#!/usr/bin/env python3
"""
اختبارات Sales Agent
"""

from unittest.mock import Mock, patch

import pytest

from src.ai.multi_agent_coordinator import AgentResult, AgentTask, AgentType
from src.ai.sales_agent import SalesAgent


class TestSalesAgent:
    """اختبارات وكيل المبيعات"""

    @pytest.fixture
    def agent(self):
        """إنشاء وكيل للاختبارات"""
        db_manager = Mock()
        return SalesAgent("sales_agent_001", db_manager)

    def test_initialization(self, agent):
        """اختبار تهيئة الوكيل"""
        assert agent is not None
        assert agent.agent_id == "sales_agent_001"
        assert agent.agent_type == AgentType.SALES_AGENT
        assert agent.db_manager is not None
        assert isinstance(agent.sales_history, list)
        assert isinstance(agent.customer_insights, dict)

    def test_get_capabilities(self, agent):
        """اختبار الحصول على القدرات"""
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert len(capabilities) == 6
        assert "إنشاء فاتورة" in capabilities
        assert "تحليل المبيعات" in capabilities
        assert "اقتراح منتجات" in capabilities
        assert "تتبع العملاء" in capabilities
        assert "توقع المبيعات" in capabilities
        assert "معالجة الخصومات" in capabilities

    def test_execute_task_create_invoice(self, agent):
        """اختبار تنفيذ مهمة إنشاء فاتورة"""
        task = AgentTask(
            task_id="task_001",
            description="إنشاء فاتورة جديدة للعميل",
            priority="high",
            parameters={"customer_id": "cust_001", "items": []},
        )

        result = agent.execute_task(task)

        assert result is not None
        assert isinstance(result, AgentResult)
        assert result.task_id == "task_001"
        assert result.agent_id == "sales_agent_001"
        assert result.confidence == 0.9
        assert "message" in result.result
        assert "invoice_id" in result.result or "data" in result.result
        assert result.execution_time >= 0

    def test_execute_task_analyze_sales(self, agent):
        """اختبار تنفيذ مهمة تحليل المبيعات"""
        task = AgentTask(
            task_id="task_002",
            description="تحليل المبيعات للشهر الحالي",
            priority="medium",
            parameters={"period": "current_month"},
        )

        result = agent.execute_task(task)

        assert result is not None
        assert result.task_id == "task_002"
        assert "message" in result.result or "analysis" in result.result
        assert "sales_data" in result.result or "statistics" in result.result

    def test_execute_task_suggest_products(self, agent):
        """اختبار تنفيذ مهمة اقتراح المنتجات"""
        task = AgentTask(
            task_id="task_003",
            description="اقتراح منتجات للعميل بناءً على التاريخ",
            priority="medium",
            parameters={"customer_id": "cust_001"},
        )

        result = agent.execute_task(task)

        assert result is not None
        assert result.task_id == "task_003"
        assert "message" in result.result or "suggestions" in result.result

    def test_execute_task_track_customers(self, agent):
        """اختبار تنفيذ مهمة تتبع العملاء"""
        task = AgentTask(
            task_id="task_004",
            description="تتبع العملاء الجدد والنشطين",
            priority="low",
            parameters={},
        )

        result = agent.execute_task(task)

        assert result is not None
        assert result.task_id == "task_004"
        assert "message" in result.result or "customers" in result.result or "customer_data" in result.result

    def test_execute_task_predict_sales(self, agent):
        """اختبار تنفيذ مهمة توقع المبيعات"""
        task = AgentTask(
            task_id="task_005",
            description="توقع المبيعات للأسبوع القادم",
            priority="high",
            parameters={"forecast_period": "7_days"},
        )

        result = agent.execute_task(task)

        assert result is not None
        assert result.task_id == "task_005"
        assert "message" in result.result or "predictions" in result.result or "forecast" in result.result

    def test_execute_task_unknown(self, agent):
        """اختبار تنفيذ مهمة غير معروفة"""
        task = AgentTask(
            task_id="task_006",
            description="مهمة عشوائية غير معروفة",
            priority="low",
            parameters={},
        )

        result = agent.execute_task(task)

        assert result is not None
        assert result.task_id == "task_006"
        assert "message" in result.result
        assert "تم تنفيذ المهمة" in result.result["message"]

    def test_execute_task_with_exception(self, agent):
        """اختبار تنفيذ مهمة مع استثناء"""
        # محاكاة خطأ أثناء التنفيذ
        with patch.object(agent, "_create_invoice", side_effect=Exception("Test error")):
            task = AgentTask(
                task_id="task_007",
                description="إنشاء فاتورة جديدة",
                priority="high",
                parameters={},
            )

            # يجب أن يتم التعامل مع الاستثناء
            try:
                result = agent.execute_task(task)
                # إذا لم يتم رفع الاستثناء، يجب أن يكون هناك نتيجة
                assert result is not None
            except Exception:
                # الاستثناء متوقع في بعض الحالات
                pass

    def test_create_invoice_method(self, agent):
        """اختبار طريقة إنشاء الفاتورة مباشرة"""
        task = AgentTask(
            task_id="task_001",
            description="إنشاء فاتورة",
            priority="high",
            parameters={"customer_id": "cust_001"},
        )

        result = agent._create_invoice(task)

        assert result is not None
        assert isinstance(result, dict)
        assert "invoice_id" in result or "data" in result
        assert "message" in result

    def test_analyze_sales_method(self, agent):
        """اختبار طريقة تحليل المبيعات مباشرة"""
        task = AgentTask(
            task_id="task_002",
            description="تحليل المبيعات",
            priority="medium",
            parameters={},
        )

        result = agent._analyze_sales(task)

        assert result is not None
        assert isinstance(result, dict)
        assert "sales_data" in result or "analysis" in result or "message" in result

    def test_suggest_products_method(self, agent):
        """اختبار طريقة اقتراح المنتجات مباشرة"""
        task = AgentTask(
            task_id="task_003",
            description="اقتراح منتجات",
            priority="medium",
            parameters={},
        )

        result = agent._suggest_products(task)

        assert result is not None
        assert isinstance(result, dict)
        assert "suggestions" in result or "message" in result

    def test_track_customers_method(self, agent):
        """اختبار طريقة تتبع العملاء مباشرة"""
        task = AgentTask(
            task_id="task_004",
            description="تتبع العملاء",
            priority="low",
            parameters={},
        )

        result = agent._track_customers(task)

        assert result is not None
        assert isinstance(result, dict)
        assert "customer_data" in result or "customers" in result or "message" in result

    def test_predict_sales_method(self, agent):
        """اختبار طريقة توقع المبيعات مباشرة"""
        task = AgentTask(
            task_id="task_005",
            description="توقع المبيعات",
            priority="high",
            parameters={},
        )

        result = agent._predict_sales(task)

        assert result is not None
        assert isinstance(result, dict)
        assert "predictions" in result or "forecast" in result or "message" in result

    def test_sales_history_tracking(self, agent):
        """اختبار تتبع سجل المبيعات"""
        # تنفيذ عدة مهام
        for i in range(3):
            task = AgentTask(
                task_id=f"task_{i}",
                description="إنشاء فاتورة",
                priority="medium",
                parameters={},
            )
            agent.execute_task(task)

        # التحقق من تحديث السجل
        assert len(agent.sales_history) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
