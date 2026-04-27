"""
AI Module - نظام الذكاء الاصطناعي
"""

from .chatbot import ChatbotEngine, chatbot, chat
from .predictive_analytics import (
    PredictiveEngine,
    SalesForecast,
    CustomerInsight
)

# Phase 4: Agentic AI Components
from .multi_agent_coordinator import MultiAgentCoordinator, AgentTask, AgentType
from .sales_agent import SalesAgent
from .voice_control_agent import VoiceControlAgent
from .generative_ui_agent import GenerativeUIAgent

__all__ = [
    'ChatbotEngine',
    'chatbot',
    'chat',
    'PredictiveEngine',
    'SalesForecast',
    'CustomerInsight'
]
