#!/usr/bin/env python3
"""
اختبارات Voice Control Agent
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.ai.voice_control_agent import VoiceControlAgent
from src.ai.multi_agent_coordinator import AgentType, AgentTask, AgentResult


class TestVoiceControlAgent:
    """اختبارات وكيل التحكم الصوتي"""
    
    @pytest.fixture
    def agent(self):
        """إنشاء وكيل للاختبارات"""
        return VoiceControlAgent("voice_agent_001")
    
    def test_initialization(self, agent):
        """اختبار تهيئة الوكيل"""
        assert agent is not None
        assert agent.agent_id == "voice_agent_001"
        assert agent.agent_type == AgentType.VOICE_AGENT
        assert isinstance(agent.voice_commands, dict)
        assert isinstance(agent.audio_buffer, list)
        assert agent.is_listening == False
    
    def test_get_capabilities(self, agent):
        """اختبار الحصول على القدرات"""
        capabilities = agent.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "التعرف على الأوامر الصوتية" in capabilities
        assert "تحويل الصوت إلى نص" in capabilities
        assert "تنفيذ الأوامر الصوتية" in capabilities
        assert "التحكم في الواجهة بالصوت" in capabilities
        assert "الرد الصوتي" in capabilities
    
    def test_load_voice_commands(self, agent):
        """اختبار تحميل الأوامر الصوتية"""
        commands = agent._load_voice_commands()
        
        assert isinstance(commands, dict)
        assert len(commands) > 0
        assert "افتح الفواتير" in commands
        assert "اعرض المخزون" in commands
        assert "أنشئ تقرير" in commands
        assert "ابحث عن منتج" in commands
        assert "أغلق النافذة" in commands
    
    def test_execute_task_process_voice(self, agent):
        """اختبار تنفيذ مهمة معالجة صوتية"""
        task = AgentTask(
            task_id="task_001",
            description="معالجة الأمر الصوتي",
            priority="high",
            parameters={"voice_text": "افتح الفواتير"}
        )
        
        result = agent.execute_task(task)
        
        assert result is not None
        assert isinstance(result, AgentResult)
        assert result.task_id == "task_001"
        assert result.agent_id == "voice_agent_001"
        assert result.confidence == 0.9
        assert "message" in result.result
    
    def test_execute_task_start_listening(self, agent):
        """اختبار تنفيذ مهمة بدء الاستماع"""
        task = AgentTask(
            task_id="task_002",
            description="بدء الاستماع",
            priority="medium",
            parameters={"action": "start_listening"}
        )
        
        result = agent.execute_task(task)
        
        assert result is not None
        assert result.task_id == "task_002"
        assert "message" in result.result
        assert "status" in result.result
        assert result.result["status"] == "active"
        assert agent.is_listening == True
    
    def test_execute_task_stop_listening(self, agent):
        """اختبار تنفيذ مهمة إيقاف الاستماع"""
        # بدء الاستماع أولاً
        agent.is_listening = True
        
        task = AgentTask(
            task_id="task_003",
            description="إيقاف الاستماع",
            priority="medium",
            parameters={"action": "stop_listening"}
        )
        
        result = agent.execute_task(task)
        
        assert result is not None
        assert result.task_id == "task_003"
        assert "message" in result.result
        assert "status" in result.result
        assert result.result["status"] == "inactive"
        assert agent.is_listening == False
    
    def test_execute_task_unknown(self, agent):
        """اختبار تنفيذ مهمة غير معروفة"""
        task = AgentTask(
            task_id="task_004",
            description="مهمة عشوائية",
            priority="low",
            parameters={}
        )
        
        result = agent.execute_task(task)
        
        assert result is not None
        assert result.task_id == "task_004"
        assert "message" in result.result
    
    def test_process_voice_command(self, agent):
        """اختبار معالجة الأمر الصوتي"""
        task = AgentTask(
            task_id="task_001",
            description="معالجة الأمر",
            priority="high",
            parameters={"voice_text": "افتح الفواتير"}
        )
        
        result = agent._process_voice_command(task)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "command" in result
        assert "action" in result
        assert "response" in result
        assert "confidence" in result
        assert result["confidence"] >= 0
        assert result["confidence"] <= 1
    
    def test_recognize_command(self, agent):
        """اختبار التعرف على الأمر"""
        # أمر معروف
        result = agent._recognize_command("افتح الفواتير")
        assert result == "افتح الفواتير"
        
        # أمر غير معروف
        result = agent._recognize_command("أمر غير موجود")
        assert result is None
    
    def test_simulate_voice_input(self, agent):
        """اختبار محاكاة الإدخال الصوتي"""
        result = agent._simulate_voice_input()
        
        assert result is not None
        assert isinstance(result, str)
        assert result in agent.voice_commands.keys()
    
    def test_get_voice_commands_list(self, agent):
        """اختبار الحصول على قائمة الأوامر الصوتية"""
        result = agent.get_voice_commands_list()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "افتح الفواتير" in result
    
    def test_add_custom_command(self, agent):
        """اختبار إضافة أمر صوتي مخصص"""
        initial_count = len(agent.voice_commands)
        
        agent.add_custom_command(
            command="أمر مخصص",
            action="custom_action",
            keywords=["مخصص", "خاص"],
            response="تم تنفيذ الأمر المخصص"
        )
        
        assert len(agent.voice_commands) == initial_count + 1
        assert "أمر مخصص" in agent.voice_commands
        assert agent.voice_commands["أمر مخصص"]["action"] == "custom_action"
    
    def test_process_audio_chunk(self, agent):
        """اختبار معالجة قطعة صوتية"""
        audio_data = b"fake_audio_data"
        
        result = agent.process_audio_chunk(audio_data)
        
        # قد يكون None أو قاموس حسب التنفيذ
        assert result is None or isinstance(result, dict)
    
    def test_start_listening_method(self, agent):
        """اختبار طريقة بدء الاستماع مباشرة"""
        task = AgentTask(
            task_id="task_001",
            description="بدء الاستماع",
            priority="medium",
            parameters={}
        )
        
        result = agent._start_listening(task)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] == "active"
        assert agent.is_listening == True
    
    def test_stop_listening_method(self, agent):
        """اختبار طريقة إيقاف الاستماع مباشرة"""
        agent.is_listening = True
        
        task = AgentTask(
            task_id="task_001",
            description="إيقاف الاستماع",
            priority="medium",
            parameters={}
        )
        
        result = agent._stop_listening(task)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] == "inactive"
        assert agent.is_listening == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



