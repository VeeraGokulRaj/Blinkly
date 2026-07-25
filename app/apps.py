from django.apps import AppConfig


class BlinklyConfig(AppConfig):
    name = "app"

    def ready(self):
        import app.domain.background_task  # noqa: F401
