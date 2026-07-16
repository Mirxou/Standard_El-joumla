"""REST API Module
نظام API RESTful للتكامل الخارجي
"""

__all__ = [
    "create_app",
    "app",
    "setup_middleware",
    "router",
    "JWTAuthManager",
    "APIRateLimiter",
    "API_VERSION",
    "API_PREFIX",
]


def __getattr__(name):
    """Lazy exports to avoid importing the whole API stack on simple imports."""
    if name in {"create_app", "app", "API_VERSION", "API_PREFIX"}:
        from .app import API_PREFIX, API_VERSION, app, create_app

        return {
            "create_app": create_app,
            "app": app,
            "API_VERSION": API_VERSION,
            "API_PREFIX": API_PREFIX,
        }[name]
    if name == "setup_middleware":
        from .middleware import setup_middleware

        return setup_middleware
    if name == "router":
        from .routes import router

        return router
    if name == "JWTAuthManager":
        from .auth import JWTAuthManager

        return JWTAuthManager
    if name == "APIRateLimiter":
        from .rate_limiter import APIRateLimiter

        return APIRateLimiter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
