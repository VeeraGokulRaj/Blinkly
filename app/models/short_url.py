from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models.base import BaseModel


class ShortURL(BaseModel):
    original_url = models.URLField(
        max_length=2048,
        verbose_name=_("Original URL"),
        help_text=_("The destination URL."),
    )

    target_domain = models.CharField(
        max_length=255,
        db_index=True,
        editable=False,
        help_text=_("Extracted domain from the original URL."),
    )

    short_code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        editable=False,
        help_text=_("Unique short code."),
    )

    click_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Total number of successful redirects."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    last_clicked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Most recent successful redirect."),
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.short_code} → {self.target_domain}"
