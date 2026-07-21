from django.shortcuts import redirect

from app.domain.redirect import redirect_short_url


def redirect_view(request, short_code):
    """
    Redirect a visitor to the original URL.
    """

    original_url = redirect_short_url(
        request,
        short_code,
    )

    return redirect(original_url)
