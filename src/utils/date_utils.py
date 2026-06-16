from datetime import datetime
from typing import Any, Optional


def parse_datetime(value: Any) -> Optional[datetime]:
    """تحليل datetime من أشكال مختلفة (مثل قراءات قاعدة البيانات أو الواجهة)"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
    return None
