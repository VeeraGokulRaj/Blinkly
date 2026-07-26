from .base import *  # noqa: F403
from .base import SITE_URL, env


ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])


CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[SITE_URL],
)

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
