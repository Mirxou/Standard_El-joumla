#!/usr/bin/env python3
"""
اختبار نظام الوكلاء المتعددين - Multi-Agent System Test
"""

from datetime import datetime
from src.ai.multi_agent_coordinator import MultiAgentCoordinator, AgentTask, AgentType
from src.ai.sales_agent import SalesAgent
from src.ai.voice_control_agent import VoiceControlAgent
from src.ai.generative_ui_agent import GenerativeUIAgent


def test_multi_agent_system():
    """اختبار نظام الوكلاء المتعددين"""
    print("🚀 بدء اختبار نظام الوكلاء المتعددين")
    print("=" * 50)

    # إنشاء منسق الوكلاء
    coordinator = MultiAgentCoordinator()

    # تسجيل الوكلاء
    sales_agent = SalesAgent("sales_agent_001")
    voice_agent = VoiceControlAgent("voice_agent_001")
    ui_agent = GenerativeUIAgent("ui_agent_001")

    coordinator.register_agent(sales_agent)
    coordinator.register_agent(voice_agent)
    coordinator.register_agent(ui_agent)

    print(f"✅ تم تسجيل {len(coordinator.agents)} وكيل")
    print()

    # إنشاء مهام اختبار
    test_tasks = [
        AgentTask(
            task_id="task_001",
            agent_type=AgentType.SALES_AGENT,
            description="أنشئ فاتورة جديدة للعميل أحمد",
            priority=1
        ),
        AgentTask(
            task_id="task_002",
            agent_type=AgentType.SALES_AGENT,
            description="تحليل المبيعات لهذا الأسبوع",
            priority=2
        ),
        AgentTask(
            task_id="task_003",
            agent_type=AgentType.VOICE_AGENT,
            description="التعرف على الأمر الصوتي: افتح الفواتير",
            priority=1
        ),
        AgentTask(
            task_id="task_004",
            agent_type=AgentType.UI_AGENT,
            description="أنشئ لوحة تحكم للمبيعات",
            priority=2
        ),
        AgentTask(
            task_id="task_005",
            agent_type=AgentType.UI_AGENT,
            description="أنشئ نموذج إدخال بيانات العميل",
            priority=1
        )
    ]

    # تقديم المهام وتنفيذها
    results = []
    for task in test_tasks:
        print(f"📋 تقديم المهمة: {task.task_id} - {task.description}")

        # تقديم المهمة
        task_id = coordinator.submit_task(task)

        # تعيين المهمة لوكيل
        assigned_agent = coordinator.assign_task(task)
        if assigned_agent:
            print(f"🤖 تم تعيين المهمة لوكيل: {assigned_agent}")

            # تنفيذ المهمة
            result = coordinator.execute_task(task_id)
            if result:
                results.append(result)
                print(f"✅ تم إنجاز المهمة: {result.result.get('message', 'بدون رسالة')}")
            else:
                print("❌ فشل في إنجاز المهمة")
        else:
            print("⚠️ لا يوجد وكيل متاح لهذه المهمة")

        print("-" * 30)

    # عرض تقرير النظام
    print("📊 تقرير النظام النهائي:")
    system_status = coordinator.get_system_status()
    for key, value in system_status.items():
        print(f"  {key}: {value}")

    print()
    print("🎯 تفاصيل الوكلاء:")
    for agent_id, agent in coordinator.agents.items():
        status = coordinator.get_agent_status(agent_id)
        if status:
            print(f"  {agent_id}: {status['status']} - إنجاز {status['tasks_completed']} مهمة")

    print()
    print("🏆 النتائج المحققة:")
    for result in results:
        print(f"  {result.task_id}: {result.result.get('action', 'غير محدد')}")

    # إغلاق النظام
    coordinator.shutdown()

    print()
    print("🎉 انتهى اختبار نظام الوكلاء المتعددين بنجاح!")


if __name__ == "__main__":
    test_multi_agent_system()



