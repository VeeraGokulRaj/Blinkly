import logging
import sys

from celery.signals import (
    before_task_publish,
    task_failure,
    task_postrun,
    task_prerun,
    task_received,
    task_revoked,
    task_success,
)
from django.conf import settings
from django.db import close_old_connections
from django.utils.timezone import now

from app.models import (
    CELERY_STATE_MAP,
    BackgroundTask,
    BackgroundTaskEvent,
    TaskStatus,
)

logger = logging.getLogger(__name__)


def log_progress(task_id: str, message: str) -> None:
    try:
        task = BackgroundTask.objects.get(task_id=task_id)
        BackgroundTaskEvent.objects.create(
            task=task,
            event=BackgroundTaskEvent.EventType.PROGRESS,
            message=message,
        )
    except BackgroundTask.DoesNotExist:
        pass


def log_task_event(
    task_id: str, name: str, event: int, message: str | None = None, **defaults
) -> None:
    request = defaults.pop("request", None)

    args = None
    kwargs = None
    user_id = None
    queue = "default"

    if request:
        args = getattr(request, "args", None)
        kwargs = getattr(request, "kwargs", None)
        if kwargs and isinstance(kwargs, dict):
            user_id = kwargs.get("triggered_by_id")
        delivery_info = getattr(request, "delivery_info", {}) or {}
        queue = (
            delivery_info.get("queue") or delivery_info.get("routing_key") or "default"
        )

    task, _ = BackgroundTask.objects.get_or_create(
        task_id=task_id,
        defaults={
            "name": name,
            "args": args,
            "kwargs": kwargs,
            "queue": queue,
            "created_by_id": user_id,
        },
    )
    if request:
        BackgroundTask.objects.filter(pk=task.pk).update(queue=queue)

    BackgroundTaskEvent.objects.create(task=task, event=event, message=message)


def update_status(task_id: str, celery_state: str, **kwargs) -> None:
    status = CELERY_STATE_MAP.get(celery_state, TaskStatus.PENDING)
    BackgroundTask.objects.filter(task_id=task_id).update(status=status, **kwargs)


@before_task_publish.connect
def create_task_record(sender=None, headers=None, body=None, **kwargs):
    try:
        if not headers:
            return
        task_id = headers.get("id")
        if not task_id:
            return

        args = body[0] if body and len(body) > 0 else None
        kwargs_data = body[1] if body and len(body) > 1 else {}

        user_id = (
            kwargs_data.get("triggered_by_id")
            if isinstance(kwargs_data, dict)
            else None
        )

        BackgroundTask.objects.get_or_create(
            task_id=task_id,
            defaults={
                "name": sender,
                "args": args,
                "kwargs": kwargs_data,
                "created_by_id": user_id,
            },
        )
    except Exception:
        logger.exception("Failed to create task record in before_task_publish handler")


@task_received.connect
def task_received_handler(sender, request=None, **kwargs):
    if not request:
        return

    task_id = request.id
    name = request.name

    try:
        log_task_event(
            task_id,
            name,
            event=BackgroundTaskEvent.EventType.RECEIVED,
            message="Task received",
            request=request,
        )
        update_status(task_id, "RECEIVED")
    except Exception:
        logger.exception("Failed to log task received event")


@task_prerun.connect
def task_prerun_handler(task_id, task, **kwargs):
    try:
        log_task_event(
            task_id,
            task.name,
            event=BackgroundTaskEvent.EventType.STARTED,
            message="Task started",
        )
        update_status(task_id, "STARTED", started_at=now())
    except Exception:
        logger.exception("Failed to log task prerun event")


@task_success.connect
def task_success_handler(sender, result, **kwargs):
    try:
        task_id = getattr(sender.request, "id", None)
        if not task_id:
            return
        message = getattr(sender.request, "success_message", "Task succeeded")
        log_task_event(
            task_id,
            sender.name,
            event=BackgroundTaskEvent.EventType.SUCCEEDED,
            message=message,
        )
        update_status(task_id, "SUCCESS", finished_at=now())
    except Exception:
        logger.exception("Failed to log task success event")


@task_failure.connect
def task_failure_handler(sender, task_id, exception, **kwargs):
    try:
        task_name = getattr(sender, "name", "unknown")
        log_task_event(
            task_id,
            task_name,
            event=BackgroundTaskEvent.EventType.FAILED,
            message=f"Task failed: {exception}",
        )
        update_status(task_id, "FAILURE", finished_at=now(), exception=str(exception))
    except Exception:
        logger.exception("Failed to log task failure event")


@task_revoked.connect
def task_revoked_handler(sender, **kwargs):
    try:
        task_id = getattr(sender.request, "id", None)
        if not task_id:
            return
        log_task_event(
            task_id,
            sender.name,
            event=BackgroundTaskEvent.EventType.REVOKED,
            message="Task revoked",
        )
        update_status(task_id, "REVOKED", finished_at=now())
    except Exception:
        logger.exception("Failed to log task revoked event")


@task_postrun.connect
def close_db_connections(sender=None, **kwargs):
    if "pytest" not in sys.modules and not getattr(settings, "TESTING", False):
        close_old_connections()
