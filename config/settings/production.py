"""
Production settings for Blinkly project.

Celery & Redis Configuration for Free Hosting Services:
---------------------------------------------------------
When deploying to free cloud platforms (e.g., Render, Railway, Upstash Redis, or Redis Cloud):
1. Create a Redis instance on Upstash (https://upstash.com) or Redis Cloud (https://redis.io/cloud).
2. Set the `REDIS_URL` or `CELERY_BROKER_URL` environment variable in your production hosting dashboard.
   Example URL formats:
   - Standard: redis://default:password@ep-xxx.upstash.io:6379/0
   - SSL/TLS: rediss://default:password@ep-xxx.upstash.io:6379/0
"""

from .base import *  # noqa: F403
from .base import SITE_URL, env


ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[SITE_URL],
)
