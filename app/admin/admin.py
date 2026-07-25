from django.contrib import admin
from django.utils.html import format_html

from app.models import (
    BackgroundTask,
    BackgroundTaskEvent,
    ClickEvent,
    ShortURL,
    TaskStatus,
)


class BackgroundTaskEventInline(admin.TabularInline):
    model = BackgroundTaskEvent
    extra = 0
    readonly_fields = ("event", "message", "created")
    can_delete = False
    ordering = ("-created",)


@admin.register(BackgroundTask)
class BackgroundTaskAdmin(admin.ModelAdmin):
    list_display = (
        "task_id",
        "name",
        "status_badge",
        "queue",
        "started_at",
        "finished_at",
        "created",
    )
    list_filter = (
        "status",
        "name",
        "queue",
        "created",
    )
    search_fields = (
        "task_id",
        "name",
        "exception",
    )
    readonly_fields = (
        "task_id",
        "name",
        "args",
        "kwargs",
        "queue",
        "created_by",
        "status",
        "started_at",
        "finished_at",
        "exception",
        "created",
        "modified",
    )
    inlines = [BackgroundTaskEventInline]
    ordering = ("-created",)
    list_per_page = 25

    fieldsets = (
        (
            "Task Overview",
            {
                "fields": (
                    "task_id",
                    "name",
                    "status",
                    "queue",
                    "created_by",
                )
            },
        ),
        (
            "Execution Details",
            {
                "fields": (
                    "started_at",
                    "finished_at",
                    "args",
                    "kwargs",
                    "exception",
                )
            },
        ),
        (
            "System Timestamps",
            {
                "classes": ("collapse",),
                "fields": (
                    "created",
                    "modified",
                ),
            },
        ),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        color_map = {
            TaskStatus.PENDING: "#6c757d",
            TaskStatus.RECEIVED: "#17a2b8",
            TaskStatus.STARTED: "#007bff",
            TaskStatus.SUCCESS: "#28a745",
            TaskStatus.FAILURE: "#dc3545",
            TaskStatus.RETRY: "#ffc107",
            TaskStatus.REVOKED: "#343a40",
        }
        color = color_map.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-weight:bold; font-size:0.85em;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(BackgroundTaskEvent)
class BackgroundTaskEventAdmin(admin.ModelAdmin):
    list_display = ("task", "event", "message", "created")
    list_filter = ("event", "created")
    search_fields = ("task__task_id", "task__name", "message")
    readonly_fields = ("task", "event", "message", "created", "modified")


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
