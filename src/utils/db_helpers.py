"""Database helper utilities for safe row access.

Provides ``get_value`` to safely extract a value from a row that may be a
``dict`` (returned by ``fetch_one``/``fetch_all``), a ``sqlite3.Row`` (returned
by raw cursors), or a ``tuple``/``list``.
"""
from typing import Any, Optional


def get_value(row: Any, key: str, default: Any = None) -> Any:
    """Return ``row[key]`` if present, else ``default``.

    Works on:
      * ``dict`` — uses ``row.get(key, default)``
      * ``sqlite3.Row`` — uses ``row[key]`` with fallback
      * other mappings — tries ``row[key]`` then falls back to default
    """
    if row is None:
        return default
    # dict-like (the canonical case after fetch_one/fetch_all)
    if isinstance(row, dict):
        return row.get(key, default)
    # sqlite3.Row supports key access via row[key]
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default
    except Exception:
        return default
