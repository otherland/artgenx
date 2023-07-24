from django.apps import AppConfig

class WebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'artgen'

    def ready(self):
        import artgen.signals  # Import the signals module
