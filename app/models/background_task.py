from django.conf import settings
from django.db import models

from app.models.base import BaseModel


class TaskStatus(models.IntegerChoices):
    PENDING = 0, "Pending"
    RECEIVED = 1, "Received"
    STARTED = 2, "Started"
    SUCCESS = 3, "Success"
    FAILURE = 4, "Failure"
    RETRY = 5, "Retry"
    REVOKED = 6, "Revoked"


CELERY_STATE_MAP = {
    "PENDING": TaskStatus.PENDING,
    "RECEIVED": TaskStatus.RECEIVED,
    "STARTED": TaskStatus.STARTED,
    "SUCCESS": TaskStatus.SUCCESS,
    "FAILURE": TaskStatus.FAILURE,
    "RETRY": TaskStatus.RETRY,
    "REVOKED": TaskStatus.REVOKED,
}


class BackgroundTask(BaseModel):
    task_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    args = models.JSONField(null=True, blank=True)
    kwargs = models.JSONField(null=True, blank=True)
    queue = models.CharField(max_length=100, null=True, blank=True, default="default")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    status = models.PositiveSmallIntegerField(
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    exception = models.TextField(null=True, blank=True, max_length=5000)

    class Meta:
        ordering = ("-created",)
        verbose_name = "Background Task"
        verbose_name_plural = "Background Tasks"

    def __str__(self):
        return f"{self.name} [{self.task_id}]"


class BackgroundTaskEvent(BaseModel):
    class EventType(models.IntegerChoices):
        RECEIVED = 1, "Received"
        STARTED = 2, "Started"
        SUCCEEDED = 3, "Succeeded"
        FAILED = 4, "Failed"
        REVOKED = 5, "Revoked"
        PROGRESS = 6, "Progress"

    task = models.ForeignKey(
        BackgroundTask,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event = models.PositiveSmallIntegerField(
        choices=EventType.choices,
        default=EventType.PROGRESS,
    )
    message = models.TextField(null=True, blank=True, max_length=5000)

    class Meta:
        ordering = ("-created",)
        verbose_name = "Background Task Event"
        verbose_name_plural = "Background Task Events"

    def __str__(self):
        return f"{self.get_event_display()} - {self.task.name}"
