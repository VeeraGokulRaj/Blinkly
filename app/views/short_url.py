from django.shortcuts import render

from app.domain.short_url import create_short_url
from app.forms import ShortURLForm
from django.core.exceptions import ValidationError


def create_short_url_view(request):
    short_url = None

    if request.method == "POST":
        form = ShortURLForm(request.POST)

        if form.is_valid():
            try:
                short_url = create_short_url(
                    form.cleaned_data["original_url"],
                )
            except ValidationError as exc:
                form.add_error(
                    "original_url",
                    exc.message,
                )
    else:
        form = ShortURLForm()

    return render(
        request,
        "base.html",
        {
            "form": form,
            "short_url": short_url,
        },
    )
