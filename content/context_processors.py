# content/context_processors.py
from .models import SiteSettings

def site_settings(request):
    s = SiteSettings.objects.first()
    return {"SITE_SETTINGS": s}
