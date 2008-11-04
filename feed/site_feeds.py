from datetime import datetime as dt

from django.contrib.syndication.feeds import Feed as RssFeed
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.db.models import Q

from atom import Feed as AtomFeed
from fs.models import Topic, SECTIONS, get_cat
from utils import reverse
from tagging.models import Tag, TaggedItem


def link(location):
    return 'http://%s/%s/' % (settings.SITE_DOMAIN, location)

def _ByTag(Feed, type='atom'):
    class ByTag(Feed):
        def get_object(self, bits):
            if len(bits) != 1:
                raise ObjectDoesNotExist
            else:
#                return Tag.objects.get(name=bits[0])
		return bits[0]

        def feed_id(self, obj):
            if not obj:
                raise Http404
            return link(reverse('by_tag', tag=obj))

        link = feed_id

        def feed_title(self, obj):
            return u"%s posts with tag %s" % (SITE_NAME, obj)

        title = feed_title

        def feed_authors(self):
            return ({"name": user.name} for user in User.objects.all())

        def feed_links(self, obj):
            return ({'rel': u'alternate', 'href': self.feed_id(obj)}, {'rel': u'self', 'href': link(reverse('%s_feed' % type, '/'.join(['tag', obj.name])))})

        def items(self, obj):
            return TaggedItem.objects.get_by_model(Topic, obj)[:5]

        def item_id(self, item):
            return link('~%s/%s/'%(item.author.username, item.slug))

        def item_title(self, item):
            return 'html', item.title

        def item_updated(self, item):
            return item.created

        def item_content(self, item):
            return {'type': 'html'}, item.text

        def item_links(self, item):
            return ({'rel': u'self', 'href': self.item_id(item)}, {'rel': u'alternate', 'href': self.item_id(item)})
    return ByTag

def _BySection(Feed, type='atom'):
    class BySection(Feed):
        def get_object(self, bits):
            if len(bits) != 1:
                raise ObjectDoesNotExist
	    result = Topic.objects.filter(Q(section=bits[0])|Q(subcat=bits[0]))
	    if not result:
		raise ObjectDoesNotExist
            return (bits[0], result)

        def feed_id(self, obj):
            return link(reverse('by_section', slug=obj[0]))
        link = feed_id

        def feed_title(self, obj):
            return u"%s: '%s' posts" % (settings.SITE_NAME, get_cat(obj[0]))

        title = feed_title

        def feed_authors(self):
            return ({"name": user.name} for user in User.objects.all())

        def feed_links(self, obj):
            return ({'rel': u'alternate', 'href': self.feed_id(obj[1])}, {'rel': u'self', 'href': link(reverse('%s_feed' % type, '/'.join(['tag', obj[1]])))})

        def items(self, obj):
    	    return obj[1].filter(approved=True).exclude(created__gt=dt.now()).order_by('-created')[:5]

        def item_id(self, item):
            return link('~%s/%s/'%(item.author.username, item.slug))

        def item_title(self, item):
            return 'html', item.title

        def item_updated(self, item):
            return item.created

        def item_content(self, item):
            return {'type': 'html'}, item.text

        def item_links(self, item):
            return ({'rel': u'self', 'href': self.item_id(item)}, {'rel': u'alternate', 'href': self.item_id(item)})
    return BySection

# Ok, time to build our feeds!
AtomByTag = _ByTag(AtomFeed)
AtomByTag = _ByTag(AtomFeed)
RssByTag = _ByTag(RssFeed, 'rss')
RssBySection = _BySection(RssFeed, 'rss')
AtomBySection = _BySection(AtomFeed, 'atom')
