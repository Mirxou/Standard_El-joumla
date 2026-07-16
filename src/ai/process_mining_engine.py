import logging
#!/usr/bin/env python3
"""
محرك استخراج العمليات - Process Mining Engine
محرك لاستخراج وتحليل العمليات التجارية من البيانات
"""

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib.pyplot as plt

import networkx as nx


class ProcessType(Enum):
    """نوع العملية"""

    ORDER_TO_CASH = "order_to_cash"
    PURCHASE_TO_PAY = "purchase_to_pay"
    HIRE_TO_RETIRE = "hire_to_retire"
    CUSTOM = "custom"


class EventType(Enum):
    """نوع الحدث"""

    START = "start"
    COMPLETE = "complete"
    SCHEDULE = "schedule"
    ASSIGN = "assign"
    MANUAL = "manual"
    AUTOMATIC = "automatic"


@dataclass
class ProcessEvent:
    """حدث عملية"""

    event_id: str
    case_id: str
    activity: str
    timestamp: datetime
    event_type: EventType
    resource: Optional[str] = None
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class ProcessInstance:
    """مثيل عملية"""

    case_id: str
    events: List[ProcessEvent]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    status: str = "active"

    def __post_init__(self):
        if self.events:
            self.events.sort(key=lambda e: e.timestamp)
            self.start_time = self.events[0].timestamp
            if self._is_completed():
                self.end_time = self.events[-1].timestamp
                self.duration = self.end_time - self.start_time

    def _is_completed(self) -> bool:
        """فحص اكتمال العملية"""
        return any(e.event_type == EventType.COMPLETE for e in self.events)


@dataclass
class ProcessModel:
    """نموذج عملية"""

    process_id: str
    process_type: ProcessType
    activities: Set[str]
    transitions: Dict[Tuple[str, str], int]  # (from_activity, to_activity) -> count
    start_activities: Set[str]
    end_activities: Set[str]
    bottlenecks: List[Dict[str, Any]]
    variants: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]

    def __init__(self, process_id: str, process_type: ProcessType):
        self.process_id = process_id
        self.process_type = process_type
        self.activities = set()
        self.transitions = {}
        self.start_activities = set()
        self.end_activities = set()
        self.bottlenecks = []
        self.variants = []
        self.performance_metrics = {}


class ProcessMiningEngine:
    """محرك استخراج العمليات"""

    def __init__(self):
        self.event_logs: Dict[str, List[ProcessEvent]] = {}
        self.process_models: Dict[str, ProcessModel] = {}
        self.logger = logging.getLogger(__name__)

        # إعداد التسجيل
        self._setup_logging()

    def _setup_logging(self):
        """إعداد نظام التسجيل"""
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - Process Mining - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def load_event_log(self, log_id: str, events: List[ProcessEvent]) -> Dict[str, Any]:
        """تحميل سجل الأحداث"""
        self.event_logs[log_id] = events

        # تحليل السجل
        analysis = self._analyze_event_log(events)

        self.logger.info(f"Event log loaded: {log_id} ({len(events)} events)")

        return {
            "status": "loaded",
            "log_id": log_id,
            "events_count": len(events),
            "cases_count": analysis["cases_count"],
            "activities_count": analysis["activities_count"],
            "analysis": analysis,
        }

    def discover_process_model(self, log_id: str, process_type: ProcessType = ProcessType.CUSTOM) -> str:
        """استخراج نموذج العملية"""
        if log_id not in self.event_logs:
            raise ValueError(f"Event log not found: {log_id}")

        events = self.event_logs[log_id]
        process_id = f"process_{log_id}_{int(datetime.now().timestamp())}"

        # إنشاء نموذج العملية
        model = ProcessModel(process_id, process_type)

        # استخراج الأنشطة والانتقالات
        self._extract_activities_and_transitions(events, model)

        # تحديد أنشطة البداية والنهاية
        self._identify_start_end_activities(events, model)

        # اكتشاف الاختناقات
        model.bottlenecks = self._discover_bottlenecks(events)

        # استخراج المتغيرات
        model.variants = self._extract_process_variants(events)

        # حساب مقاييس الأداء
        model.performance_metrics = self._calculate_performance_metrics(events)

        self.process_models[process_id] = model

        self.logger.info(f"Process model discovered: {process_id}")

        return process_id

    def analyze_process_performance(self, process_id: str) -> Dict[str, Any]:
        """تحليل أداء العملية"""
        if process_id not in self.process_models:
            raise ValueError(f"Process model not found: {process_id}")

        model = self.process_models[process_id]

        return {
            "process_id": process_id,
            "performance_metrics": model.performance_metrics,
            "bottlenecks": model.bottlenecks,
            "recommendations": self._generate_performance_recommendations(model),
        }

    def compare_process_variants(self, process_id: str) -> Dict[str, Any]:
        """مقارنة متغيرات العملية"""
        if process_id not in self.process_models:
            raise ValueError(f"Process model not found: {process_id}")

        model = self.process_models[process_id]

        return {
            "process_id": process_id,
            "variants": model.variants,
            "comparison": self._compare_variants(model.variants),
        }

    def detect_process_anomalies(self, process_id: str) -> Dict[str, Any]:
        """كشف شذوذ العملية"""
        if process_id not in self.process_models:
            raise ValueError(f"Process model not found: {process_id}")

        model = self.process_models[process_id]
        events = self._get_events_for_process(process_id)

        anomalies = self._detect_anomalies(events, model)

        return {
            "process_id": process_id,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "anomaly_types": self._categorize_anomalies(anomalies),
        }

    def visualize_process_model(self, process_id: str, output_path: str = None) -> str:
        """تصور نموذج العملية"""
        if process_id not in self.process_models:
            raise ValueError(f"Process model not found: {process_id}")

        model = self.process_models[process_id]

        # إنشاء رسم بياني
        G = nx.DiGraph()

        # إضافة العقد
        for activity in model.activities:
            G.add_node(activity)

        # إضافة الحواف
        for (from_act, to_act), weight in model.transitions.items():
            G.add_edge(from_act, to_act, weight=weight)

        # رسم الرسم البياني
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)

        # رسم العقد
        nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=2000, alpha=0.7)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

        # رسم الحواف
        edges = G.edges()
        weights = [G[u][v]["weight"] for u, v in edges]
        nx.draw_networkx_edges(
            G,
            pos,
            width=[w / 10 for w in weights],
            alpha=0.6,
            edge_color="gray",
            arrows=True,
            arrowsize=20,
        )

        # إضافة تسميات الحواف
        edge_labels = {(u, v): f"{G[u][v]['weight']}" for u, v in edges}
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

        plt.title(f"Process Model: {process_id}")
        plt.axis("off")

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()
            return output_path
        else:
            output_path = f"process_model_{process_id}_{int(datetime.now().timestamp())}.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()
            return output_path

    def generate_process_report(self, process_id: str) -> Dict[str, Any]:
        """توليد تقرير العملية"""
        if process_id not in self.process_models:
            raise ValueError(f"Process model not found: {process_id}")

        model = self.process_models[process_id]

        return {
            "process_id": process_id,
            "process_type": model.process_type.value,
            "summary": {
                "activities_count": len(model.activities),
                "transitions_count": len(model.transitions),
                "start_activities": list(model.start_activities),
                "end_activities": list(model.end_activities),
            },
            "performance": model.performance_metrics,
            "bottlenecks": model.bottlenecks,
            "variants": model.variants,
            "recommendations": self._generate_process_recommendations(model),
            "generated_at": datetime.now().isoformat(),
        }

    def _analyze_event_log(self, events: List[ProcessEvent]) -> Dict[str, Any]:
        """تحليل سجل الأحداث"""
        cases = set(e.case_id for e in events)
        activities = set(e.activity for e in events)

        # حساب الإحصائيات الأساسية
        case_durations = []
        case_events = defaultdict(list)

        for event in events:
            case_events[event.case_id].append(event)

        for case_id, case_events_list in case_events.items():
            if len(case_events_list) > 1:
                start_time = min(e.timestamp for e in case_events_list)
                end_time = max(e.timestamp for e in case_events_list)
                duration = end_time - start_time
                case_durations.append(duration.total_seconds())

        return {
            "cases_count": len(cases),
            "activities_count": len(activities),
            "events_count": len(events),
            "avg_events_per_case": len(events) / len(cases) if cases else 0,
            "avg_case_duration": (statistics.mean(case_durations) if case_durations else 0),
            "total_duration": sum(case_durations) if case_durations else 0,
        }

    def _extract_activities_and_transitions(self, events: List[ProcessEvent], model: ProcessModel):
        """استخراج الأنشطة والانتقالات"""
        # تجميع الأحداث حسب الحالة
        case_events = defaultdict(list)
        for event in events:
            case_events[event.case_id].append(event)

        # استخراج الأنشطة والانتقالات
        for case_id, events_list in case_events.items():
            events_list.sort(key=lambda e: e.timestamp)

            for i in range(len(events_list) - 1):
                current_event = events_list[i]
                next_event = events_list[i + 1]

                model.activities.add(current_event.activity)
                model.activities.add(next_event.activity)

                transition = (current_event.activity, next_event.activity)
                model.transitions[transition] = model.transitions.get(transition, 0) + 1

    def _identify_start_end_activities(self, events: List[ProcessEvent], model: ProcessModel):
        """تحديد أنشطة البداية والنهاية"""
        case_events = defaultdict(list)
        for event in events:
            case_events[event.case_id].append(event)

        start_activities = set()
        end_activities = set()

        for case_id, events_list in case_events.items():
            if events_list:
                events_list.sort(key=lambda e: e.timestamp)
                start_activities.add(events_list[0].activity)
                end_activities.add(events_list[-1].activity)

        model.start_activities = start_activities
        model.end_activities = end_activities

    def _discover_bottlenecks(self, events: List[ProcessEvent]) -> List[Dict[str, Any]]:
        """اكتشاف الاختناقات"""
        bottlenecks = []

        # حساب متوسط الوقت لكل نشاط
        activity_times = defaultdict(list)

        case_events = defaultdict(list)
        for event in events:
            case_events[event.case_id].append(event)

        for case_id, events_list in case_events.items():
            events_list.sort(key=lambda e: e.timestamp)

            activity_start_times = {}

            for event in events_list:
                if event.event_type == EventType.START:
                    activity_start_times[event.activity] = event.timestamp
                elif event.event_type == EventType.COMPLETE and event.activity in activity_start_times:
                    start_time = activity_start_times[event.activity]
                    duration = (event.timestamp - start_time).total_seconds()
                    activity_times[event.activity].append(duration)

        # تحديد الاختناقات (الأنشطة ذات الوقت الأطول)
        for activity, times in activity_times.items():
            if times:
                avg_time = statistics.mean(times)
                max_time = max(times)
                if avg_time > 300:  # أكثر من 5 دقائق
                    bottlenecks.append(
                        {
                            "activity": activity,
                            "avg_duration": avg_time,
                            "max_duration": max_time,
                            "occurrences": len(times),
                            "severity": "high" if avg_time > 600 else "medium",
                        }
                    )

        return sorted(bottlenecks, key=lambda x: x["avg_duration"], reverse=True)

    def _extract_process_variants(self, events: List[ProcessEvent]) -> List[Dict[str, Any]]:
        """استخراج متغيرات العملية"""
        variants = []

        # تجميع تسلسل الأنشطة لكل حالة
        case_sequences = defaultdict(list)

        case_events = defaultdict(list)
        for event in events:
            case_events[event.case_id].append(event)

        for case_id, events_list in case_events.items():
            events_list.sort(key=lambda e: e.timestamp)
            sequence = [e.activity for e in events_list]
            case_sequences[tuple(sequence)].append(case_id)

        # تحليل المتغيرات
        for sequence, case_ids in case_sequences.items():
            variants.append(
                {
                    "sequence": list(sequence),
                    "frequency": len(case_ids),
                    "percentage": len(case_ids) / len(case_events) * 100,
                    "case_ids": case_ids[:5],  # أول 5 حالات كمثال
                }
            )

        return sorted(variants, key=lambda x: x["frequency"], reverse=True)

    def _calculate_performance_metrics(self, events: List[ProcessEvent]) -> Dict[str, Any]:
        """حساب مقاييس الأداء"""
        case_events = defaultdict(list)
        for event in events:
            case_events[event.case_id].append(event)

        case_durations = []
        case_event_counts = []

        for case_id, events_list in case_events.items():
            if len(events_list) > 1:
                start_time = min(e.timestamp for e in events_list)
                end_time = max(e.timestamp for e in events_list)
                duration = (end_time - start_time).total_seconds()
                case_durations.append(duration)
                case_event_counts.append(len(events_list))

        return {
            "total_cases": len(case_events),
            "completed_cases": len([c for c in case_events.values() if len(c) > 1]),
            "avg_case_duration": (statistics.mean(case_durations) if case_durations else 0),
            "median_case_duration": (statistics.median(case_durations) if case_durations else 0),
            "min_case_duration": min(case_durations) if case_durations else 0,
            "max_case_duration": max(case_durations) if case_durations else 0,
            "avg_events_per_case": (statistics.mean(case_event_counts) if case_event_counts else 0),
            "total_events": len(events),
        }

    def _generate_performance_recommendations(self, model: ProcessModel) -> List[str]:
        """توليد توصيات الأداء"""
        recommendations = []

        # توصيات للاختناقات
        if model.bottlenecks:
            recommendations.append(f"تحسين الأداء في {len(model.bottlenecks)} نشاط محتمل الاختناق")

        # توصيات للمتغيرات
        if len(model.variants) > 1:
            recommendations.append("توحيد عمليات العمل لتقليل المتغيرات")

        # توصيات للأداء
        metrics = model.performance_metrics
        if metrics.get("avg_case_duration", 0) > 3600:  # أكثر من ساعة
            recommendations.append("تبسيط العملية لتقليل وقت الإنجاز")

        return recommendations

    def _compare_variants(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """مقارنة المتغيرات"""
        if len(variants) < 2:
            return {"comparison": "غير كافٍ للمقارنة"}

        # مقارنة الطول والتكرار
        lengths = [len(v["sequence"]) for v in variants]
        frequencies = [v["frequency"] for v in variants]

        return {
            "variant_count": len(variants),
            "avg_sequence_length": statistics.mean(lengths),
            "most_common_variant": variants[0]["sequence"] if variants else None,
            "variant_diversity": len(set(tuple(v["sequence"]) for v in variants)),
            "frequency_distribution": {
                "min": min(frequencies),
                "max": max(frequencies),
                "avg": statistics.mean(frequencies),
            },
        }

    def _detect_anomalies(self, events: List[ProcessEvent], model: ProcessModel) -> List[Dict[str, Any]]:
        """كشف الشذوذ"""
        anomalies = []

        # كشف الأنشطة غير الشائعة
        activity_counts = Counter(e.activity for e in events)
        total_events = len(events)

        for activity, count in activity_counts.items():
            frequency = count / total_events
            if frequency < 0.01:  # أقل من 1%
                anomalies.append(
                    {
                        "type": "rare_activity",
                        "activity": activity,
                        "frequency": frequency,
                        "severity": "low",
                    }
                )

        # كشف الانتقالات غير الشائعة
        transition_counts = Counter()
        case_events = defaultdict(list)

        for event in events:
            case_events[event.case_id].append(event)

        for case_id, events_list in case_events.items():
            events_list.sort(key=lambda e: e.timestamp)
            for i in range(len(events_list) - 1):
                transition = (events_list[i].activity, events_list[i + 1].activity)
                transition_counts[transition] += 1

        total_transitions = sum(transition_counts.values())

        for transition, count in transition_counts.items():
            frequency = count / total_transitions
            if frequency < 0.01:  # أقل من 1%
                anomalies.append(
                    {
                        "type": "rare_transition",
                        "from_activity": transition[0],
                        "to_activity": transition[1],
                        "frequency": frequency,
                        "severity": "medium",
                    }
                )

        return anomalies

    def _categorize_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """تصنيف الشذوذ"""
        categories = defaultdict(int)
        for anomaly in anomalies:
            categories[anomaly["type"]] += 1
        return dict(categories)

    def _get_events_for_process(self, process_id: str) -> List[ProcessEvent]:
        """الحصول على الأحداث للعملية"""
        # البحث عن سجل الأحداث المرتبط بالعملية
        for log_id, events in self.event_logs.items():
            if log_id in process_id:
                return events
        return []

    def _generate_process_recommendations(self, model: ProcessModel) -> List[str]:
        """توليد توصيات العملية"""
        recommendations = []

        # توصيات للاختناقات
        if model.bottlenecks:
            recommendations.append(f"معالجة {len(model.bottlenecks)} اختناق في العملية")

        # توصيات للمتغيرات
        if len(model.variants) > 10:
            recommendations.append("تقليل عدد متغيرات العملية")

        # توصيات للأداء
        metrics = model.performance_metrics
        if metrics.get("avg_case_duration", 0) > 7200:  # أكثر من ساعتين
            recommendations.append("إعادة تصميم العملية لتحسين الكفاءة")

        return recommendations
