from django import template
from django.db import connection
from django.db.models import Q

import cmemcache as memcache
from operator import itemgetter
import datetime

from fs.models import Topic, SECTIONS
from fs.util import sort_result
from settings import RESULTS_ON_PAGE, MEMCACHE
from utils import order_by

register = template.Library()

def summary(context):
    mc = memcache.Client([MEMCACHE], debug=0)
    peers = mc.get('peers')
    render_dict = {}
    if not peers:
	for s in SECTIONS:
	    render_dict.update({s[0]: Topic.objects.filter(section=s[0], approved=True).order_by('-created')[:10]})
	return render_dict
    now = datetime.datetime.now()
    cursor = connection.cursor()
    for s in SECTIONS:
	ids = [t['torrent__id'] for t in Topic.objects.filter(section=s[0], approved=True).order_by('-created').values('torrent__id')]
	render_dict.update({s[0]: sort_result(ids, peers, limit=10)})
    connection.close()
    context.update(render_dict)
    return context

register.inclusion_tag("summary.htm", takes_context=True)(summary)
