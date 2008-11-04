from datetime import datetime as dt
from django.contrib.sitemaps import Sitemap

from fs.models import Topic

class TopicSiteMap(Sitemap):
    changefreq = "never"
    priority = 0.8
    
    def items(self):
	return Topic.objects.filter(approved=True).exclude(created__gt=dt.now())

    def lastmod(self, obj):
	return obj.created
	