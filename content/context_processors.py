# content/context_processors.py
from .models import SiteSetting

def site_settings(request):
    try:
        s = SiteSetting.objects.get(pk=1)
    except SiteSetting.DoesNotExist:
        s = SiteSetting()  # defaults
    return {"site_settings": s}
