from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Instagram Clone Core"

    def ready(self):
        # Import signal handlers so they get registered when the app starts.
        import core.signals  # noqa: F401
