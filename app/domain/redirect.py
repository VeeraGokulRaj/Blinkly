from django.http import Http404

from app.domain.analytics import track_click
from app.models import ShortURL

# from .analytics import track_click


def redirect_short_url(request, short_code: str) -> str:
    """
    Resolve a short code, record analytics, and return
    the destination URL.
    """

    short_url = ShortURL.objects.filter(short_code=short_code).first()

    if short_url is None:
        raise Http404("Short URL does not exist.")

    track_click(request, short_url)

    return short_url.original_url
