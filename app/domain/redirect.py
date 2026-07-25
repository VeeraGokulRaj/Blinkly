from django.http import Http404

from app.models import ShortURL
from app.tasks.analytics import track_click_task
from django.core.cache import cache
from typing import TypedDict


CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours


class CachedShortURL(TypedDict):
    id: int
    original_url: str


def redirect_short_url(request, short_code: str) -> str:
    """
    Resolve a short code, record analytics, and return
    the destination URL.
    """

    cache_key = f"short_url:{short_code}"

    cached: CachedShortURL | None = cache.get(cache_key)

    if cached is None:
        cached = set_short_url_cache(short_code)

    track_click_task.delay(
        short_url_id=cached["id"],
        user_agent=request.headers.get("User-Agent", ""),
        referer=request.headers.get("Referer", ""),
        country="",
    )

    return cached["original_url"]


def set_short_url_cache(short_code: str) -> CachedShortURL:
    """
    Fetch the short URL from the database, cache it, and return the cached data.
    """
    short_url = (
        ShortURL.objects.only(
            "id",
            "original_url",
        )
        .filter(short_code=short_code)
        .first()
    )

    if short_url is None:
        raise Http404("Short URL does not exist.")

    cached = {
        "id": short_url.pk,
        "original_url": short_url.original_url,
    }

    cache.set(
        f"short_url:{short_code}",
        cached,
        timeout=CACHE_TIMEOUT,
    )

    return cached
