"""
REST API Module
نظام API RESTful للتكامل الخارجي
"""

# Optional API server (may not exist in desktop-only setups)
try:
	from .app import create_app, app  # type: ignore
except (ImportError, ModuleNotFoundError):
	# API server not available (desktop-only mode)
	create_app = None  # type: ignore
	app = None  # type: ignore

# Optional helpers (may not exist in minimal setups)
try:  # pragma: no cover - optional
	from .middleware import setup_middleware  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
	def setup_middleware(*args, **kwargs):  # type: ignore
		return None

try:  # pragma: no cover - optional
	from .routes import register_routes  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
	def register_routes(*args, **kwargs):  # type: ignore
		return None

__all__ = ['create_app', 'app', 'setup_middleware', 'register_routes']
