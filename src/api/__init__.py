"""
REST API Module
نظام API RESTful للتكامل الخارجي
"""

from .app import create_app, app

# Optional helpers (may not exist in minimal setups)
try:  # pragma: no cover - optional
	from .middleware import setup_middleware  # type: ignore
except Exception:  # pragma: no cover
	def setup_middleware(*args, **kwargs):  # type: ignore
		return None

try:  # pragma: no cover - optional
	from .routes import register_routes  # type: ignore
except Exception:  # pragma: no cover
	def register_routes(*args, **kwargs):  # type: ignore
		return None

__all__ = ['create_app', 'app', 'setup_middleware', 'register_routes']
