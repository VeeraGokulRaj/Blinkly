import pytest
from django.conf import settings
from app.models import BackgroundTask, TaskStatus
from app.tasks import ping


@pytest.mark.django_db
def test_ping_task_execution():
    # Execute ping task synchronously
    res = ping.apply()
    assert res.result == "pong"

    # Verify BackgroundTask record was created and updated via signals
    task_record = BackgroundTask.objects.filter(task_id=res.id).first()
    assert task_record is not None
    assert task_record.status == TaskStatus.SUCCESS
    assert task_record.finished_at is not None

    # Verify BackgroundTaskEvent progress and success events
    events = list(task_record.events.values_list("message", flat=True))
    assert any("Sending Pong" in msg for msg in events)


def test_celery_settings():
    assert hasattr(settings, "CELERY_BROKER_URL")
    assert hasattr(settings, "CELERY_RESULT_BACKEND")
    assert settings.CELERY_TASK_TRACK_STARTED is True
    assert settings.CELERY_ACCEPT_CONTENT == ["json"]
