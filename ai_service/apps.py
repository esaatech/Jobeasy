from django.apps import AppConfig


class AiServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_service'
    verbose_name = 'AI Service'

    def ready(self) -> None:
        # Ensure admin registrations load even if autodiscover order differs in production.
        from . import admin  # noqa: F401
