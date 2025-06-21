from django.apps import AppConfig


class PDFGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdf_generator'
    verbose_name = 'PDF Generator'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import pdf_generator.signals  # noqa
        except ImportError:
            pass 