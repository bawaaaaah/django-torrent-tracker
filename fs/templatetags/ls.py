import datetime
import os.path
from settings import FTP_HOMEDIR, MEDIA_ROOT, SCRAPE_URL, MEMCACHE
from shared_classes import Path
from django.template import Library,Node

register = Library()

@register.filter(name="measure")
def measure(bytes):
    from django.template import defaultfilters
    if type(bytes) == str: return ""
    return defaultfilters.filesizeformat(bytes)

@register.filter(name="timestamp")
def format(date, string=None):
    if string:
        result = datetime.date.fromtimestamp(date).strftime(string)
    else:
	result = datetime.date.fromtimestamp(date).strftime('%Y-%m-%d')
    return result

@register.filter(name="basename")
def basename(obj):
    if not obj: return ""
    if type(obj) is Path:
	obj = obj.name
    return os.path.basename(obj)

@register.filter(name="relpath")
def relpath(obj):
    try:
	r = '/'.join(obj.split(FTP_HOMEDIR)[1].split('/')[2:])
    except:
	return ""
    return r

@register.filter(name="splitpath")
def splitpath(obj):
    return obj.split('/')

@register.filter(name="mergepath")
def mergepath(obj, n=None):
    if not n: return ""
    return '/'.join(obj.split('/')[:n])

@register.filter(name="unfold")
def unfold(form):
    result = []
    for i in form.ls:
	result.append((i[1], form[i[0]], type(i[1]) == str))
    #result = map(lambda x,y: (x,y,chk(x,y)), form.ls.values(), [f for f in form if f.name !='path'])
    return result

class ScrapObject(Node):
    def render(self, context):
	context['info'] = {'leechers': 0, 'seeds': 0, 'downloaded': 0}
 	if not context.has_key('torrent'): return ''
	from BitTornado.bencode import bdecode, bencode
	from sha import sha
	from urllib2 import URLError, urlopen
	fn = os.path.join(MEDIA_ROOT, 'torrents', context['torrent'])
	if not os.path.exists(fn): return ''
	try:
	    f = open(fn, 'rb')
	    meta = bdecode(f.read())['info']
	    meta = sha(bencode(meta)).digest()
	    f.close()
	except (IOError, ValueError, KeyError):
	    return ''
	try:
	    f = urlopen(SCRAPE_URL)
	except URLError:
	    return ''
	m = bdecode(f.read())
	f.close()
	if not m.has_key('files'): return ''
	m = m['files']
	if m.has_key(meta):
	    m = m[meta]
	    context['info']['seeds'], context['info']['leechers'], context['info']['downloaded'] = m['complete'], m['incomplete'], m['downloaded']
	return ''

@register.filter(name="get_peers")
def get_peers(the_id):
    import cmemcache as memcache
    import datetime
    mc = memcache.Client([MEMCACHE], debug=0)
    peers = mc.get('peers')
    if not peers:
	return (0, 0)
    now = datetime.datetime.now()
    seeders = len([p for p in peers if p['torrent_id'] == the_id and p['expire_time'] > now and p['left'] == 0])
    leechers = len([p for p in peers if p['torrent_id'] == the_id and p['expire_time'] > now and p['left'] > 0])
    return (seeders, leechers)

@register.filter(name="transcat")
def transcat(cat):
    from django.utils.translation import ugettext_lazy as _
    from fs.models import AKINDS, BKINDS, GKINDS, MKINDS, OKINDS, PKINDS, TKINDS, SECTIONS
    # translate category name
    result = [i[1] for i in AKINDS+BKINDS+GKINDS+MKINDS+OKINDS+PKINDS+TKINDS+SECTIONS+(('misc', _('misc')), ) if i[0] == cat]
    if not result:
	return ''
    return result[0]

@register.filter(name="transstatus")
def transstatus(status):
    from transcoding.models import STATUS
    result = [s[1] for s in STATUS if s[0] == status]
    if not result:
	return ''
    return result[0]

register.tag('scrape', lambda parser, token: ScrapObject())

