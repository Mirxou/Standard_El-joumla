"""
REST API Module
نظام API RESTful للتكامل الخارجي
"""

from .app import create_app, app
from .middleware import setup_middleware
from .routes import register_routes

__all__ = ['create_app', 'app', 'setup_middleware', 'register_routes']
