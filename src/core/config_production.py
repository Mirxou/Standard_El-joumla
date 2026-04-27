# Production Configuration
# إعدادات الإنتاج لـ Unified Commerce 2030 ERP

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = os.getenv('SECRET_KEY')  # Required - must be set in production
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'unified_erp'),
        'USER': os.getenv('DB_USER', 'erp_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),  # Required - no default for security
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require' if os.getenv('DB_SSL', 'false').lower() == 'true' else 'prefer',
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'retry_on_timeout': True,
            },
            'PASSWORD': os.getenv('REDIS_PASSWORD', ''),
        }
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Riyadh'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@unifiedcommerce.com')

# File Storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'unified-erp-files')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com')
AWS_DEFAULT_ACL = 'private'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Static Files
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# Media Files
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SSL/HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/unified_erp.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'unified_erp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Performance Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# AI/ML Settings
AI_MODEL_CACHE_TIMEOUT = 3600  # 1 hour
AI_MAX_CONCURRENT_REQUESTS = 10
AI_REQUEST_TIMEOUT = 30  # seconds

# Monitoring
PROMETHEUS_METRICS_ENABLED = True
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Third-party Integrations
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Feature Flags
ENABLE_AI_FEATURES = True
ENABLE_ADVANCED_REPORTING = True
ENABLE_REAL_TIME_ANALYTICS = True
ENABLE_MOBILE_APP = True

# Rate Limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "https://app.unifiedcommerce.com",
    "https://admin.unifiedcommerce.com",
]
CORS_ALLOW_CREDENTIALS = True

# Maintenance Mode
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "النظام قيد الصيانة، يرجى المحاولة لاحقاً."