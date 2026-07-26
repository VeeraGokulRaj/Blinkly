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
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration


ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[SITE_URL],
)

sentry_sdk.init(
    dsn="https://ad139a357ea01b8b53f573f8b5695d3d@o4511799891197953.ingest.us.sentry.io/4511799899389952",
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=1,
    send_default_pii=True,
)
