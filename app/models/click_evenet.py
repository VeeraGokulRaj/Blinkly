from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models.base import BaseModel


class DeviceType(models.TextChoices):
    DESKTOP = "desktop", _("Desktop")
    MOBILE = "mobile", _("Mobile")
    TABLET = "tablet", _("Tablet")
    BOT = "bot", _("Bot")
    UNKNOWN = "unknown", _("Unknown")


class ClickEvent(BaseModel):
    short_url = models.ForeignKey(
        "ShortURL",
        on_delete=models.CASCADE,
        related_name="click_events",
        help_text=_("The shortened URL that was accessed."),
    )

    clicked_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_("When the redirect happened."),
    )

    browser = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Detected browser name."),
    )

    operating_system = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Detected operating system."),
    )

    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.UNKNOWN,
        help_text=_("Detected device type."),
    )

    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Detected visitor country."),
    )

    referer = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text=_("HTTP Referer header, if present."),
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text=_("Raw User-Agent header."),
    )

    class Meta:
        ordering = ("-clicked_at",)

    def __str__(self):
        return (
            f"{self.short_url.short_code} | "
            f"{self.clicked_at:%Y-%m-%d %H:%M:%S} | "
            f"{self.device_type}"
        )
