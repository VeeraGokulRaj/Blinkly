from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
    "debug_toolbar",
    "django_browser_reload",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
] + MIDDLEWARE  # noqa: F405

# Local Celery Configuration (Redis Broker)
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/1")  # noqa: F405
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/1")  # noqa: F405
