#!/usr/bin/env python3
"""
وكيل التحكم الصوتي - Voice Control Agent
يتعامل مع الأوامر الصوتية ويحولها إلى إجراءات
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .multi_agent_coordinator import AgentResult, AgentTask, AgentType, BaseAgent
import random  # nosec B311


class VoiceControlAgent(BaseAgent):
    """وكيل التحكم الصوتي"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.VOICE_AGENT)
        self.voice_commands = self._load_voice_commands()
        self.audio_buffer = []
        self.is_listening = False

    def get_capabilities(self) -> List[str]:
        """قدرات وكيل الصوت"""
        return [
            "التعرف على الأوامر الصوتية",
            "تحويل الصوت إلى نص",
            "تنفيذ الأوامر الصوتية",
            "التحكم في الواجهة بالصوت",
            "الرد الصوتي",
        ]

    def _load_voice_commands(self) -> Dict[str, Dict[str, Any]]:
        """تحميل قاموس الأوامر الصوتية"""
        return {
            "افتح الفواتير": {
                "action": "open_invoices",
                "keywords": ["افتح", "فواتير", "الفواتير"],
                "response": "جاري فتح شاشة الفواتير",
            },
            "أنشئ فاتورة": {
                "action": "create_invoice",
                "keywords": ["أنشئ", "فاتورة", "جديدة"],
                "response": "سأساعدك في إنشاء فاتورة جديدة",
            },
            "أرني المبيعات": {
                "action": "show_sales",
                "keywords": ["أرني", "المبيعات", "مبيعات"],
                "response": "عرض تقرير المبيعات",
            },
            "ابحث عن عميل": {
                "action": "search_customer",
                "keywords": ["ابحث", "عميل", "عن"],
                "response": "ما اسم العميل الذي تريد البحث عنه؟",
            },
            "أضف منتج": {
                "action": "add_product",
                "keywords": ["أضف", "منتج", "جديد"],
                "response": "سأفتح نافذة إضافة منتج جديد",
            },
            "أغلق": {
                "action": "close_window",
                "keywords": ["أغلق", "إغلاق", "خروج"],
                "response": "إغلاق النافذة الحالية",
            },
            "مساعدة": {
                "action": "help",
                "keywords": ["مساعدة", "مساعدة", "أوامر"],
                "response": "يمكنك قول: افتح الفواتير، أنشئ فاتورة، أرني المبيعات، أو مساعدة",
            },
            # Expected by unit tests:
            "اعرض المخزون": {
                "action": "show_inventory",
                "keywords": ["اعرض", "المخزون", "مخزون"],
                "response": "عرض حالة المخزون الحالي",
            },
            "أنشئ تقرير": {
                "action": "create_report",
                "keywords": ["أنشئ", "تقرير", "تقرير جديد"],
                "response": "جاري إنشاء التقرير المطلوب",
            },
            "ابحث عن منتج": {
                "action": "search_product",
                "keywords": ["ابحث", "منتج", "البحث"],
                "response": "ما هو المنتج الذي تريد البحث عنه؟",
            },
            "أغلق النافذة": {
                "action": "close_window",
                "keywords": ["أغلق", "النافذة", "إغلاق"],
                "response": "تم إغلاق النافذة بنجاح",
            },
        }

    def execute_task(self, task: AgentTask) -> AgentResult:
        """تنفيذ مهمة صوتية"""
        start_time = datetime.now()

        try:
            if "التعرف على الصوت" in task.description or "معالجة" in task.description:
                result = self._process_voice_command(task)
            elif "تشغيل الاستماع" in task.description or "بدء الاستماع" in task.description:
                result = self._start_listening(task)
            elif "إيقاف الاستماع" in task.description:
                result = self._stop_listening(task)
            else:
                result = {"message": f"تم تنفيذ المهمة الصوتية: {task.description}"}

            execution_time = (datetime.now() - start_time).total_seconds()
            confidence = result.get("confidence", 0.85) if isinstance(result, dict) else 0.85

            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result=result,
                confidence=confidence,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result={"error": str(e)},
                confidence=0.0,
                execution_time=execution_time,
            )

    def _process_voice_command(self, task: AgentTask) -> Dict[str, Any]:
        """معالجة الأمر الصوتي"""
        voice_text = None
        if task.parameters and "voice_text" in task.parameters:
            voice_text = task.parameters["voice_text"]
        if not voice_text:
            voice_text = self._simulate_voice_input()

        recognized_command = self._recognize_command(voice_text)

        if recognized_command:
            action_data = self.voice_commands[recognized_command]
            return {
                "action": "voice_command_recognized",
                "command": recognized_command,
                "recognized_text": voice_text,
                "action_data": action_data,
                "response": action_data["response"],
                "confidence": 0.9,
                "message": f"تم التعرف على الأمر: {recognized_command}",
            }
        else:
            return {
                "action": "voice_command_not_recognized",
                "recognized_text": voice_text,
                "response": "لم أفهم الأمر. يمكنك قول: مساعدة",
                "confidence": 0.0,
                "message": "لم يتم التعرف على الأمر الصوتي",
            }

    def _recognize_command(self, voice_text: str) -> Optional[str]:
        """التعرف على الأمر من النص"""
        voice_text_lower = voice_text.lower()

        for command, data in self.voice_commands.items():
            keywords_found = sum(1 for keyword in data["keywords"] if keyword in voice_text_lower)
            if keywords_found >= len(data["keywords"]) * 0.6:  # 60% من الكلمات المفتاحية
                return command

        return None

    def _simulate_voice_input(self) -> str:
        """محاكاة إدخال صوتي (للاختبار)"""
        return random.choice(list(self.voice_commands.keys()))

    def _start_listening(self, task: AgentTask) -> Dict[str, Any]:
        """بدء الاستماع للأوامر الصوتية"""
        self.is_listening = True
        return {
            "action": "listening_started",
            "message": "بدأت في الاستماع للأوامر الصوتية",
            "status": "active",
        }

    def _stop_listening(self, task: AgentTask) -> Dict[str, Any]:
        """إيقاف الاستماع"""
        self.is_listening = False
        return {
            "action": "listening_stopped",
            "message": "تم إيقاف الاستماع للأوامر الصوتية",
            "status": "inactive",
        }

    def get_voice_commands_list(self) -> List[str]:
        """الحصول على قائمة الأوامر الصوتية المتاحة"""
        return list(self.voice_commands.keys())

    def add_custom_command(self, command: str, action: str, keywords: List[str], response: str):
        """إضافة أمر صوتي مخصص"""
        self.voice_commands[command] = {
            "action": action,
            "keywords": keywords,
            "response": response,
        }

    def process_audio_chunk(self, audio_data: bytes) -> Optional[Dict[str, Any]]:
        """معالجة قطعة صوتية (للتكامل مع مكتبات الصوت)"""
        if not self.is_listening:
            return None

        recognized_text = self._simulate_voice_input()
        command = self._recognize_command(recognized_text)

        if command:
            return {
                "recognized": True,
                "command": command,
                "text": recognized_text,
                "action": self.voice_commands[command]["action"],
            }
        else:
            return {
                "recognized": False,
                "text": recognized_text,
                "suggestion": "جرب قول: مساعدة",
            }

