from django.conf.urls.defaults import *
from django.contrib.syndication.views import feed

from feed.site_feeds import AtomByTag, RssByTag, RssBySection, AtomBySection

# Be careful, names of this keys are also used in templates and in feeds.py!
atom_feeds = {
    'tag': AtomByTag,
    'section': AtomBySection,
    }

rss_feeds = {
    'tag': RssByTag,
    'section': RssBySection,
    }

urlpatterns = patterns('',
    url(r'^rss/(?P<url>.*)/$', feed, {'feed_dict': rss_feeds}, name="rss_feed"),
    url(r'^atom/(?P<url>.*)/$', feed, {'feed_dict': atom_feeds}, name="atom_feed"),
)
