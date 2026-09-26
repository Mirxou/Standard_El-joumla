"""Database helper utilities for safe row access.

Provides ``get_value`` to safely extract a value from a row that may be a
``dict`` (returned by ``fetch_one``/``fetch_all``), a ``sqlite3.Row`` (returned
by raw cursors), or a ``tuple``/``list``.

Also provides input validation helpers:
- ``escape_like_wildcards`` – escape ``%`` and ``_`` in strings used with SQL LIKE
- ``validate_path_within_base`` – prevent path-traversal attacks on user-supplied paths
- ``validate_email`` – basic email format validation
- ``validate_phone`` – basic phone format validation
- ``safe_int`` – safe int() conversion with default on failure
- ``safe_float`` – safe float() conversion with default on failure
"""
import os
import re
from pathlib import Path
from typing import Any, Optional, Union


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


# ==================== Input Validation Helpers ====================

def escape_like_wildcards(value: str) -> str:
    """Escape SQL LIKE wildcard characters (``%`` and ``_``) in *value*.

    When user input is embedded in a ``LIKE`` pattern such as
    ``f'%{value}%'``, any literal ``%`` or ``_`` inside *value* would be
    interpreted as a wildcard by the database engine, leading to
    unintended matches.  This function escapes them so they are treated
    as literal characters.

    Usage::

        # Instead of:
        params.append(f'%{user_input}%')
        # Use:
        params.append(f'%{escape_like_wildcards(user_input)}%')

    Args:
        value: Raw user input string.

    Returns:
        The string with ``%`` → ``\\%`` and ``_`` → ``\\_``.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def validate_path_within_base(
    path: Union[str, Path],
    base_dir: Union[str, Path],
    *,
    resolve: bool = True,
) -> Path:
    """Validate that *path* resolves to a location inside *base_dir*.

    Prevents path-traversal attacks (e.g. ``../../etc/passwd``).

    Args:
        path: User-supplied path (absolute or relative).
        base_dir: The allowed base directory.
        resolve: If True, resolve symlinks before checking.

    Returns:
        The resolved ``Path`` object.

    Raises:
        ValueError: If the path escapes *base_dir*.
    """
    base = Path(base_dir).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    # Always resolve to eliminate '..' components
    target = target.resolve()
    # Use os.path commonpath or ensure base is a proper prefix with a separator
    # to prevent bypass (e.g. /app/dataevil matching /app/data)
    base_str = str(base)
    target_str = str(target)
    if not (target_str == base_str or target_str.startswith(base_str + os.sep)):
        raise ValueError(
            f"Path '{path}' is outside the allowed directory '{base_dir}'"
        )
    return target


# Simple email regex – covers the vast majority of real-world addresses
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> bool:
    """Return True if *email* matches a basic email format.

    This is **not** RFC-5322-complete but rejects obvious mistakes such as
    missing ``@``, spaces, or no TLD.
    """
    if not email or not isinstance(email, str):
        return False
    return bool(_EMAIL_RE.match(email.strip()))


# Phone: digits, spaces, dashes, parens, plus sign – at least 7 digit chars
_PHONE_RE = re.compile(r"^[+]?[()\s\d-]{7,20}$")


def validate_phone(phone: str) -> bool:
    """Return True if *phone* looks like a plausible phone number.

    Allows digits, spaces, dashes, parentheses, and a leading ``+``.
    Requires at least 7 digit characters.
    """
    if not phone or not isinstance(phone, str):
        return False
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return False
    return bool(_PHONE_RE.match(phone.strip()))


def safe_int(value: Any, default: int = 0) -> int:
    """Convert *value* to ``int`` safely, returning *default* on failure.

    Handles None, empty strings, non-numeric strings, and float values.

    Use this when reading IDs from UI table cells that might be empty or
    non-numeric::

        row_id = safe_int(id_cell.text(), default=-1)
        if row_id <= 0:
            return  # invalid
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert *value* to ``float``, returning *default* on failure.

    Handles None, empty strings, and non-numeric strings.

    Usage::

        price = safe_float(price_cell.text(), default=0.0)
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ==================== Retry Utility ====================

def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    logger=None,
):
    """Retry a function with exponential backoff.

    Calls *func* repeatedly until it succeeds or *max_retries* is exhausted.
    On each failure the delay doubles: ``base_delay * (2 ** attempt)``.

    Args:
        func: Zero-argument callable to retry.
        max_retries: Maximum number of retry attempts (total calls = max_retries).
        base_delay: Base delay in seconds for the first retry.
        exceptions: Tuple of exception types that trigger a retry.
        logger: Optional logger; if provided, retries are logged at warning level.

    Returns:
        The return value of *func* on success.

    Raises:
        The last caught exception if all retries are exhausted.

    Example::

        result = retry_with_backoff(
            lambda: smtp_server.send_message(msg),
            max_retries=3,
            base_delay=1.0,
            exceptions=(smtplib.SMTPException, OSError),
        )
    """
    import time as _time

    last_exc = None
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                if logger:
                    logger.warning(
                        "retry_with_backoff: attempt %d/%d failed (%s), "
                        "retrying in %.1fs",
                        attempt + 1, max_retries, exc, delay,
                    )
                _time.sleep(delay)
            else:
                if logger:
                    logger.error(
                        "retry_with_backoff: all %d attempts exhausted: %s",
                        max_retries, exc,
                    )
    # If we get here, all retries failed
    raise last_exc


# ==================== Timeout Utility ====================

def run_with_timeout(func, args=(), kwargs=None, timeout=30, default=None):
    """Run a function with a timeout. Returns default if timeout expires.

    Executes *func* in a daemon thread and waits up to *timeout* seconds.
    If the thread completes in time, its return value is returned (or any
    exception it raised is re-raised).  If the deadline expires, *default*
    is returned.

    Args:
        func: Callable to run.
        args: Positional arguments for *func*.
        kwargs: Keyword arguments for *func* (None → empty dict).
        timeout: Maximum seconds to wait.
        default: Value to return on timeout.

    Returns:
        The return value of *func*, or *default* on timeout.

    Raises:
        Exception: Any exception raised by *func* (if it finishes in time).

    Example::

        result = run_with_timeout(
            expensive_prediction,
            args=(product_id,),
            timeout=30,
            default=[],
        )
    """
    if kwargs is None:
        kwargs = {}
    import threading
    result = [default]
    exception = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return default
    if exception[0] is not None:
        raise exception[0]
    return result[0]
