from django.contrib import admin

from app.models import ClickEvent, ShortURL


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = (
        "short_code",
        "target_domain",
        "click_count",
        "last_clicked_at",
        "created",
    )

    search_fields = (
        "short_code",
        "original_url",
        "target_domain",
    )

    list_filter = (
        "created",
        "last_clicked_at",
    )

    ordering = ("-created",)

    readonly_fields = (
        "short_code",
        "target_domain",
        "click_count",
        "created",
        "modified",
        "last_clicked_at",
    )

    date_hierarchy = "created"

    list_per_page = 25

    list_select_related = False

    fieldsets = (
        (
            "URL Information",
            {
                "fields": (
                    "original_url",
                    "target_domain",
                    "short_code",
                )
            },
        ),
        (
            "Analytics",
            {
                "fields": (
                    "click_count",
                    "last_clicked_at",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created",
                    "modified",
                ),
            },
        ),
    )


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = (
        "short_url",
        "clicked_at",
        "country",
        "device_type",
        "browser",
        "operating_system",
    )

    search_fields = (
        "short_url__short_code",
        "country",
        "browser",
        "operating_system",
    )

    list_filter = (
        "device_type",
        "browser",
        "country",
        "operating_system",
        "clicked_at",
    )

    ordering = ("-clicked_at",)

    autocomplete_fields = ("short_url",)

    readonly_fields = (
        "clicked_at",
        "user_agent",
        "referer",
        "created",
        "modified",
    )

    date_hierarchy = "clicked_at"

    list_per_page = 50

    list_select_related = ("short_url",)

    fieldsets = (
        (
            "Click Information",
            {
                "fields": (
                    "short_url",
                    "clicked_at",
                )
            },
        ),
        (
            "Visitor",
            {
                "fields": (
                    "country",
                    "device_type",
                    "browser",
                    "operating_system",
                )
            },
        ),
        (
            "Request Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    "referer",
                    "user_agent",
                ),
            },
        ),
        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created",
                    "modified",
                ),
            },
        ),
    )
