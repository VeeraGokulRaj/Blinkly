from celery import shared_task

from app.domain.background_task import log_progress


@shared_task(bind=True)
def ping(self):
    log_progress(self.request.id, "Sending Pong")
    return "pong"
