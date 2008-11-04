from django.conf import settings

def global_tracker_settings(request):
    return {
	'is_open_tracker': settings.OPEN_TRACKER,
	'site_name': settings.SITE_NAME,
	'site_domain': settings.SITE_DOMAIN,
    }
