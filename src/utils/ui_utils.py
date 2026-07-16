import time
from functools import wraps


def prevent_double_click(wait_ms=1500):
    """
    Decorator to prevent double-clicks on critical UI buttons (like Save, Pay, Submit).
    It ignores any subsequent calls to the decorated slot for `wait_ms` milliseconds.
    """

    def decorator(fn):
        last_call = 0

        @wraps(fn)
        def wrapper(*args, **kwargs):
            nonlocal last_call
            now = time.time() * 1000
            if now - last_call > wait_ms:
                last_call = now
                return fn(*args, **kwargs)
            else:
                # Silently ignore the duplicate click
                print(f"[{time.strftime('%H:%M:%S')}] Ignored duplicate click on {fn.__name__}")
                return None

        return wrapper

    return decorator
