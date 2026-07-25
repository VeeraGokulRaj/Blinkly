from django.http import Http404

from app.models import ShortURL
from app.tasks.analytics import track_click_task

# from .analytics import track_click


def redirect_short_url(request, short_code: str) -> str:
    """
    Resolve a short code, record analytics, and return
    the destination URL.
    """

    short_url = ShortURL.objects.filter(short_code=short_code).first()

    if short_url is None:
        raise Http404("Short URL does not exist.")

    track_click_task.delay(
        short_url_id=short_url.pk,
        user_agent=request.headers.get("User-Agent", ""),
        referer=request.headers.get("Referer", ""),
        country="",
    )

    return short_url.original_url
