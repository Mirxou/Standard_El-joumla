"""
REST API Module
نظام API RESTful للتكامل الخارجي
"""

# Optional API server (may not exist in desktop-only setups)
try:
	from .app import create_app, app, API_VERSION, API_PREFIX  # type: ignore
except (ImportError, ModuleNotFoundError):
	# API server not available (desktop-only mode)
	create_app = None  # type: ignore
	app = None  # type: ignore
	API_VERSION = None  # type: ignore
	API_PREFIX = None  # type: ignore

# Optional helpers (may not exist in minimal setups)
try:  # pragma: no cover - optional
	from .middleware import setup_middleware  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
	def setup_middleware(*args, **kwargs):  # type: ignore
		return None

try:  # pragma: no cover - optional
	from .routes import router  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
	router = None  # type: ignore

try:  # pragma: no cover - optional
	from .auth import JWTAuthManager  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
	JWTAuthManager = None  # type: ignore

try:  # pragma: no cover - optional
	from .rate_limiter import APIRateLimiter  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
	APIRateLimiter = None  # type: ignore

__all__ = [
	'create_app', 'app', 'setup_middleware', 'router',
	'JWTAuthManager', 'APIRateLimiter',
	'API_VERSION', 'API_PREFIX'
]
