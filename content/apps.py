# content/apps.py
from django.apps import AppConfig

class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "content"
    verbose_name = "GOD CARES 365 Content"

    def ready(self):
        # Ikiwa una signals, zita-load hapa; la sivyo, hupuuza kimya kimya
        try:
            import content.signals  # noqa: F401
        except Exception:
            pass
