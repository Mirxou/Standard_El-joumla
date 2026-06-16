#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة تكيف الواجهة المتقدمة - Advanced UI Adaptation Service
تتتبع تفاعلات المستخدم وتعيد ترتيب العناصر حسب الاستخدام المتكرر
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager


class UIInteraction:
    """تفاعل مستخدم مع عنصر واجهة"""

    def __init__(
        self,
        element_id: str,
        interaction_type: str,
        user_id: int,
        timestamp: datetime = None,
        metadata: Dict[str, Any] = None,
    ):
        self.element_id = element_id
        self.interaction_type = interaction_type  # 'click', 'hover', 'focus', 'scroll'
        self.user_id = user_id
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}


class UIElement:
    """عنصر واجهة قابل للتكيف"""

    def __init__(
        self,
        element_id: str,
        element_type: str,
        default_position: int,
        current_position: int = None,
        usage_count: int = 0,
        last_used: datetime = None,
        is_visible: bool = True,
    ):
        self.element_id = element_id
        self.element_type = element_type  # 'button', 'menu_item', 'field', 'panel'
        self.default_position = default_position
        self.current_position = current_position or default_position
        self.usage_count = usage_count
        self.last_used = last_used or datetime.now()
        self.is_visible = is_visible

    def record_interaction(self, interaction_type: str):
        """تسجيل تفاعل مع العنصر"""
        self.usage_count += 1
        self.last_used = datetime.now()

        # Weight different interaction types
        weight = {"click": 3, "focus": 2, "hover": 1, "scroll": 1}.get(interaction_type, 1)

        self.usage_count += weight - 1  # Already added 1 above


class UIAdaptationService:
    """خدمة تكيف الواجهة المتقدمة"""

    def __init__(self, db_manager: DatabaseManager = None, user_id: int = None):
        self.db_manager = db_manager
        self.user_id = user_id
        self.config = ConfigManager() if db_manager else None

        # Configuration
        self.adaptation_enabled = True
        self.learning_period_days = 30
        self.min_interactions_for_adaptation = 10
        self.adaptation_frequency_hours = 24

        if self.config:
            self.adaptation_enabled = self.config.get("ui_adaptation.enabled", True)
            self.learning_period_days = self.config.get("ui_adaptation.learning_period_days", 30)
            self.min_interactions_for_adaptation = self.config.get("ui_adaptation.min_interactions", 10)
            self.adaptation_frequency_hours = self.config.get("ui_adaptation.frequency_hours", 24)

        # In-memory caches
        self.elements_cache: Dict[str, UIElement] = {}
        self.interactions_buffer: List[UIInteraction] = []
        self.interaction_counts = defaultdict(int)
        self.element_usage = defaultdict(int)

        # Load user preferences and element states
        if self.db_manager and self.user_id:
            self.load_user_adaptation_data()

    def track_interaction(
        self,
        element_id: str,
        user_id: int = None,
        interaction_type: str = "click",
        metadata: Dict[str, Any] = None,
    ):
        """
        تتبع تفاعل المستخدم مع عنصر

        Args:
            element_id: معرف العنصر
            user_id: معرف المستخدم (اختياري)
            interaction_type: نوع التفاعل
            metadata: بيانات إضافية
        """
        if not self.adaptation_enabled:
            return

        # Legacy support
        self.interaction_counts[element_id] += 1
        self.element_usage[element_id] += 1

        # Advanced tracking
        if self.user_id or user_id:
            interaction = UIInteraction(
                element_id=element_id,
                interaction_type=interaction_type,
                user_id=user_id or self.user_id,
                metadata=metadata,
            )

            # Add to buffer
            self.interactions_buffer.append(interaction)

            # Update element usage
            if element_id in self.elements_cache:
                self.elements_cache[element_id].record_interaction(interaction_type)
            else:
                # Create new element if not exists
                self.elements_cache[element_id] = UIElement(
                    element_id=element_id,
                    element_type=self._infer_element_type(element_id),
                    default_position=0,
                )
                self.elements_cache[element_id].record_interaction(interaction_type)

            # Flush buffer if it gets too large
            if len(self.interactions_buffer) >= 50:
                self.flush_interactions()

    def generate_optimal_layout(self, user_id: int = None, ui_context: str = "general") -> Dict[str, Any]:
        """
        إنشاء تخطيط مثالي بناءً على الاستخدام

        Args:
            user_id: معرف المستخدم
            ui_context: سياق الواجهة

        Returns:
            قاموس يحتوي على التخطيط المُحسن
        """
        if not self.adaptation_enabled:
            return self.get_default_layout(ui_context)

        # Get elements for this context
        context_elements = self._get_context_elements(ui_context)

        if not context_elements:
            # Fall back to legacy method
            sorted_elements = sorted(self.element_usage.items(), key=lambda x: x[1], reverse=True)

            return {
                "primary_elements": [elem[0] for elem in sorted_elements[:5]],
                "secondary_elements": [elem[0] for elem in sorted_elements[5:10]],
                "hidden_elements": [elem[0] for elem in sorted_elements[10:]],
            }

        # Sort elements by usage frequency and recency
        sorted_elements = self._sort_elements_by_usage(context_elements)

        # Generate adapted layout
        layout = self._generate_adapted_layout(sorted_elements, ui_context)

        return layout

    def _sort_elements_by_usage(self, elements: List[UIElement]) -> List[UIElement]:
        """ترتيب العناصر حسب الاستخدام"""

        def sort_key(element: UIElement) -> Tuple[float, datetime]:
            # Calculate usage score (frequency * recency weight)
            days_since_last_use = (datetime.now() - element.last_used).days
            recency_weight = max(0.1, 1.0 - (days_since_last_use / self.learning_period_days))

            usage_score = element.usage_count * recency_weight

            return (
                -usage_score,
                -element.last_used.timestamp(),
            )  # Negative for descending

        return sorted(elements, key=sort_key)

    def _generate_adapted_layout(self, sorted_elements: List[UIElement], ui_context: str) -> Dict[str, Any]:
        """توليد التخطيط المُكيف"""

        layout = {
            "context": ui_context,
            "elements": [],
            "panels": {},
            "generated_at": datetime.now().isoformat(),
            "adaptation_confidence": self._calculate_adaptation_confidence(sorted_elements),
        }

        # Group elements by type and assign positions
        current_positions = {"buttons": 0, "fields": 0, "menus": 0, "panels": 0}

        for element in sorted_elements:
            if not element.is_visible:
                continue

            # Adaptive positioning logic
            element_type = element.element_type
            if element_type in current_positions:
                adapted_position = current_positions[element_type]
                current_positions[element_type] += 1
            else:
                adapted_position = element.current_position

            element_layout = {
                "id": element.element_id,
                "type": element.element_type,
                "original_position": element.default_position,
                "adapted_position": adapted_position,
                "usage_score": element.usage_count,
                "last_used": element.last_used.isoformat(),
                "is_frequently_used": element.usage_count > self.min_interactions_for_adaptation,
            }

            layout["elements"].append(element_layout)

        # Generate panel layout suggestions
        layout["panels"] = self._generate_panel_layout(sorted_elements)

        return layout

    def _generate_panel_layout(self, elements: List[UIElement]) -> Dict[str, Any]:
        """توليد تخطيط اللوحات"""

        # Group frequently used elements
        frequent_elements = [e for e in elements if e.usage_count > self.min_interactions_for_adaptation]

        panels = {
            "quick_actions": {
                "elements": [e.element_id for e in frequent_elements[:5] if e.element_type == "button"],
                "priority": "high",
            },
            "common_fields": {
                "elements": [e.element_id for e in frequent_elements if e.element_type == "field"][:8],
                "priority": "medium",
            },
            "recent_menus": {
                "elements": [e.element_id for e in frequent_elements if e.element_type == "menu_item"][:6],
                "priority": "low",
            },
        }

        return panels

    def _calculate_adaptation_confidence(self, elements: List[UIElement]) -> float:
        """حساب ثقة التكيف"""

        if not elements:
            return 0.0

        total_interactions = sum(e.usage_count for e in elements)
        avg_interactions = total_interactions / len(elements)

        # Confidence based on interaction volume and distribution
        if avg_interactions >= self.min_interactions_for_adaptation:
            confidence = min(1.0, avg_interactions / (self.min_interactions_for_adaptation * 2))
        else:
            confidence = avg_interactions / self.min_interactions_for_adaptation

        return round(confidence, 2)

    def apply_progressive_disclosure(
        self, current_context: str, user_experience_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        تطبيق الكشف التدريجي المتقدم

        Args:
            current_context: السياق الحالي
            user_experience_level: مستوى خبرة المستخدم
        """
        base_disclosure = {
            "show_basic": True,
            "show_advanced": False,
            "show_expert": False,
        }

        # Adjust based on context
        if current_context == "beginner" or user_experience_level == "beginner":
            base_disclosure.update(
                {
                    "show_basic": True,
                    "show_advanced": False,
                    "show_expert": False,
                    "tooltips_enabled": True,
                    "guided_tour_available": True,
                }
            )
        elif current_context == "expert" or user_experience_level == "expert":
            base_disclosure.update(
                {
                    "show_basic": False,
                    "show_advanced": True,
                    "show_expert": True,
                    "keyboard_shortcuts": True,
                    "power_features": True,
                }
            )
        else:  # intermediate
            base_disclosure.update(
                {
                    "show_basic": True,
                    "show_advanced": True,
                    "show_expert": False,
                    "contextual_help": True,
                }
            )

        # Add adaptive elements based on usage
        if self.adaptation_enabled:
            frequent_actions = self.get_frequent_actions()
            base_disclosure["frequent_actions"] = frequent_actions[:3]  # Top 3

        return base_disclosure

    def get_adaptation_suggestions(self) -> List[Dict[str, Any]]:
        """الحصول على اقتراحات التكيف المتقدمة"""

        suggestions = []

        # Analyze usage patterns
        if self.elements_cache:
            underutilized = [e for e in self.elements_cache.values() if e.usage_count < 3]

            for element in underutilized[:3]:  # Top 3 suggestions
                suggestions.append(
                    {
                        "type": "feature_discovery",
                        "element_id": element.element_id,
                        "message": f"جرب استخدام '{self._get_element_display_name(element.element_id)}' - قد يوفر عليك وقتاً",  # noqa: E501
                        "priority": "low",
                    }
                )

        # Add workflow suggestions
        workflow_suggestions = self._analyze_usage_patterns()
        suggestions.extend(workflow_suggestions[:2])

        return suggestions

    def get_frequent_actions(self) -> List[str]:
        """الحصول على الإجراءات المتكررة"""
        if self.elements_cache:
            sorted_elements = sorted(self.elements_cache.values(), key=lambda x: x.usage_count, reverse=True)
            return [e.element_id for e in sorted_elements if e.usage_count > 5]
        else:
            # Fallback to legacy
            sorted_elements = sorted(self.element_usage.items(), key=lambda x: x[1], reverse=True)
            return [elem[0] for elem in sorted_elements if elem[1] > 5]

    def _analyze_usage_patterns(self) -> List[Dict[str, Any]]:
        """تحليل أنماط الاستخدام"""

        # This would analyze sequences of interactions to find common workflows
        # For now, return mock patterns
        patterns = [
            {
                "type": "workflow_suggestion",
                "elements": ["customer_search", "product_add", "checkout"],
                "message": "البحث عن العميل وإضافة المنتجات وإتمام الشراء",
                "priority": "medium",
            },
            {
                "type": "workflow_suggestion",
                "elements": ["quote_create", "product_configure", "send_quote"],
                "message": "إنشاء عرض أسعار مع تكوين المنتجات",
                "priority": "medium",
            },
        ]

        return patterns

    def reset_adaptation(self, user_id: int = None):
        """إعادة تعيين بيانات التكيف"""

        target_user = user_id or self.user_id
        if not target_user:
            return

        try:
            if self.db_manager:
                query = "DELETE FROM ui_interactions WHERE user_id = ?"
                self.db_manager.execute_query(query, (target_user,), commit=True)

            # Clear cache
            self.elements_cache.clear()
            self.interactions_buffer.clear()
            self.interaction_counts.clear()
            self.element_usage.clear()

        except Exception as e:
            print(f"Error resetting adaptation data: {e}")

    def export_adaptation_data(self) -> Dict[str, Any]:
        """تصدير بيانات التكيف"""

        return {
            "user_id": self.user_id,
            "exported_at": datetime.now().isoformat(),
            "elements": [
                {
                    "id": element.element_id,
                    "type": element.element_type,
                    "usage_count": element.usage_count,
                    "last_used": element.last_used.isoformat(),
                    "current_position": element.current_position,
                    "default_position": element.default_position,
                }
                for element in self.elements_cache.values()
            ],
            "pending_interactions": len(self.interactions_buffer),
        }

    def flush_interactions(self):
        """حفظ التفاعلات المؤقتة"""

        if not self.interactions_buffer or not self.db_manager:
            return

        try:
            for interaction in self.interactions_buffer:
                query = """
                    INSERT INTO ui_interactions
                    (user_id, element_id, interaction_type, timestamp, metadata, context)
                    VALUES (?, ?, ?, ?, ?, ?)
                """

                # Extract context from element_id
                context = interaction.element_id.split("_")[0] if "_" in interaction.element_id else "general"

                params = (
                    interaction.user_id,
                    interaction.element_id,
                    interaction.interaction_type,
                    interaction.timestamp,
                    json.dumps(interaction.metadata) if interaction.metadata else "{}",
                    context,
                )

                self.db_manager.execute_query(query, params, commit=True)

            # Clear buffer
            self.interactions_buffer.clear()

        except Exception as e:
            print(f"Error flushing interactions: {e}")

    def load_user_adaptation_data(self):
        """تحميل بيانات التكيف"""

        if not self.db_manager or not self.user_id:
            return

        try:
            # Load recent interactions
            cutoff_date = datetime.now() - timedelta(days=self.learning_period_days)

            interactions = self.db_manager.execute_query(
                """SELECT element_id, interaction_type, timestamp, metadata
                   FROM ui_interactions
                   WHERE user_id = ? AND timestamp >= ?
                   ORDER BY timestamp DESC""",
                (self.user_id, cutoff_date),
                fetch_all=True,
            )

            # Build elements cache
            element_usage = {}

            for row in interactions:
                element_id, interaction_type, timestamp, metadata = row

                if element_id not in element_usage:
                    element_usage[element_id] = {
                        "type": self._infer_element_type(element_id),
                        "interactions": [],
                    }

                element_usage[element_id]["interactions"].append(
                    {
                        "type": interaction_type,
                        "timestamp": timestamp,
                        "metadata": json.loads(metadata) if metadata else {},
                    }
                )

            # Create UIElement objects
            for element_id, data in element_usage.items():
                usage_count = len(data["interactions"])
                last_used = max(i["timestamp"] for i in data["interactions"])

                element = UIElement(
                    element_id=element_id,
                    element_type=data["type"],
                    default_position=0,
                    usage_count=usage_count,
                    last_used=last_used,
                )

                self.elements_cache[element_id] = element

        except Exception as e:
            print(f"Error loading adaptation data: {e}")

    def _get_context_elements(self, ui_context: str) -> List[UIElement]:
        """الحصول على عناصر سياق محدد"""

        # Filter elements by context
        context_elements = [
            element
            for element in self.elements_cache.values()
            if element.element_id.startswith(f"{ui_context}_") or ui_context in element.element_id
        ]

        return context_elements

    def get_default_layout(self, ui_context: str) -> Dict[str, Any]:
        """الحصول على التخطيط الافتراضي"""

        default_layouts = {
            "sales_ui": {
                "context": "sales_ui",
                "elements": [
                    {"id": "customer_search", "position": 1},
                    {"id": "product_search", "position": 2},
                    {"id": "add_to_cart", "position": 3},
                    {"id": "checkout", "position": 4},
                ],
                "panels": {
                    "customer_panel": {"position": "left", "priority": "high"},
                    "products_panel": {"position": "center", "priority": "high"},
                    "cart_panel": {"position": "right", "priority": "high"},
                },
            }
        }

        return default_layouts.get(
            ui_context,
            {"primary_elements": [], "secondary_elements": [], "hidden_elements": []},
        )

    def _infer_element_type(self, element_id: str) -> str:
        """استنتاج نوع العنصر"""

        if "button" in element_id.lower() or "btn" in element_id.lower():
            return "button"
        elif "field" in element_id.lower() or "input" in element_id.lower():
            return "field"
        elif "menu" in element_id.lower():
            return "menu_item"
        elif "panel" in element_id.lower() or "tab" in element_id.lower():
            return "panel"
        else:
            return "unknown"

    def _get_element_display_name(self, element_id: str) -> str:
        """الحصول على الاسم المعروض"""

        name_map = {
            "customer_search": "البحث عن العميل",
            "product_add": "إضافة منتج",
            "checkout": "إتمام الشراء",
            "quote_create": "إنشاء عرض أسعار",
        }

        return name_map.get(element_id, element_id.replace("_", " ").title())

    def get_adaptation_stats(self) -> Dict[str, Any]:
        """إحصائيات التكيف"""

        total_elements = len(self.elements_cache)
        total_interactions = sum(e.usage_count for e in self.elements_cache.values())
        active_elements = len([e for e in self.elements_cache.values() if e.usage_count > 0])

        return {
            "total_elements": total_elements,
            "active_elements": active_elements,
            "total_interactions": total_interactions,
            "adaptation_enabled": self.adaptation_enabled,
            "pending_interactions": len(self.interactions_buffer),
            "cache_size": sys.getsizeof(self.elements_cache),
            "last_adaptation": datetime.now().isoformat(),
        }

    def reset_tracking(self):
        """إعادة تعيين التتبع"""
        self.interaction_counts.clear()
        self.element_usage.clear()
