from datetime import datetime, timezone
from typing import Any, Optional


def parse_datetime(value: Any) -> Optional[datetime]:
    """تحليل datetime من أشكال مختلفة (مثل قراءات قاعدة البيانات أو الواجهة)

    Always returns a **naive** datetime (strips tzinfo) so callers never
    accidentally compare offset-naive and offset-aware objects.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        # Strip timezone to guarantee a naive datetime
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            # Convert to naive (local-equivalent) to avoid tz-aware vs tz-naive mismatches
            return dt.replace(tzinfo=None)
        except Exception:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
    return None
