from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from users.models import User
from tracker.models import Torrent
from fs.models import Topic
from benc import bdecode, bencode

import datetime
from struct import pack
from socket import inet_aton, gethostbyname
import cmemcache as memcache
from random import shuffle

from settings import REQUIRE_ANNOUNCE_PROTOCOL, MAX_ANNOUNCE_RATE, MIN_ANNOUNCE_INTERVAL, EXPIRE_FACTOR, SCRAPE_FACTOR, MEMCACHE, OPEN_TRACKER

def _fail(reason, xhr=False):
    if not xhr:
	return HttpResponse(bencode({'failure reason': reason}))
    r = HttpResponse(mimetype="text/xml")
    r.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    r.write("<result><msg>failure</msg></result>")
    return r

@require_http_methods('GET')
def announce(request):
    request.encoding = 'latin-1'
    if not OPEN_TRACKER:
	if not request.GET.get('passkey'):
	    return _fail("you need to provide passkey")
	if len(request.GET['passkey']) < 40:
	    return _fail("you need to provide valid passkey")
	u = User.objects.filter(passkey=request.GET['passkey'])
	if not u:
	    return _fail("user with this passkey wasn't found")
	else:
	    u = u[0]

    args = {}
    args['ip'] = request.GET.get('ip') or request.META.get('REMOTE_ADDR')
    try:
	gethostbyname(args['ip'])
    except:
	return _fail("unable to resolve host name %s"%args['ip'])

    for key in ['uploaded', 'downloaded', 'port', 'left']:
	if request.GET.has_key(key):
	    try:
		args[key] = int(request.GET[key])
	    except ValueError:
		return _fail("argument '%s' specified incorrectly."%key)
	else:
	    return _fail("argument '%s' not specified."%key)
    event = request.GET.get('event', '')
    if event not in ['completed','stopped','started'] and len(event.strip())>0:
	return _fail("invalid request")

    # is the announce method allowed ?
    if REQUIRE_ANNOUNCE_PROTOCOL == 'no_peer_id':
	if not request.GET.get('compact') and not request.GET.get('no_peer_id'):
	    return _fail("standard announces not allowed; use no_peer_id or compact option")
    elif REQUIRE_ANNOUNCE_PROTOCOL == 'compact':
	if not request.GET.get('compact'):
	    return _fail("tracker requires use of compact option")

    info_hash = request.GET.get('info_hash', '')
    if len(info_hash) < 20 or not request.GET.get('peer_id'):
	return _fail("invalid request")
    try:
	info_hash = info_hash.encode('iso-8859-1').encode('hex')
    except:
	return _fail("invalid request")
    args['peer_id'] = request.GET['peer_id']
    torrent_id = Torrent.objects.filter(info_hash=info_hash).values('id')
    if not torrent_id:
	return _fail("no such torrent")
    else:
	torrent_id = torrent_id[0]['id']

    # calculate announce interval
    now = datetime.datetime.now()

    mc = memcache.Client([MEMCACHE], debug=0)
    peers = mc.get('peers')

    if not peers:
	peers = []

    if not OPEN_TRACKER:
	dwns = len([p for p in peers if p['user_id'] == u.id and p['expire_time']>now])
	cur_dwns = u.attrs.get('max_sim_dwn', 2)
	if dwns >= cur_dwns and cur_dwns != 0:
	    return _fail("maximum number of simultaneous downloads reached: %s"% dwns)

    num_peers = len([p for p in peers if p['expire_time']>now])
    announce_rate = len([p for p in peers if p['update_time']>now-datetime.timedelta(minutes=1)])

    announce_interval = max(num_peers * announce_rate / (MAX_ANNOUNCE_RATE**2) * 60, MIN_ANNOUNCE_INTERVAL)
    # calculate expiration time offset
    if event == 'stopped':
	expire_time = 0
    else:
	expire_time = announce_interval * EXPIRE_FACTOR

    for p in peers:
	if p['peer_id'] == args['peer_id']:
	    peers.remove(p)
    if event == 'completed':
	topic = Topic.objects.filter(torrent__pk=torrent_id)
	if len(topic)>0:
	    topic[0].attrs['downloaded'] = topic[0].attrs.get('downloaded', 0)+1
	    topic[0].save()
    if event != 'stopped':
	peer_dict = {
	    'info_hash': info_hash,
	    'peer_id': args['peer_id'],
	    'ip': args['ip'],
	    'port': args['port'],
	    'uploaded': args['uploaded'],
	    'downloaded': args['downloaded'],
	    'left': args['left'],
	    'expire_time': now+datetime.timedelta(seconds=int(expire_time)),
	    'update_time': now,
	    'torrent_id': torrent_id,
	}
	if not OPEN_TRACKER:
	    peer_dict['user_id'] = u.id
	peers.append(peer_dict)

    mc.set('peers', peers)

    numwant = request.GET.get('numwant', 50)
    try:
	numwant = int(numwant)
    except ValueError:
	numwant = 50
    result = [p for p in peers if p['torrent_id'] == torrent_id and p['expire_time']>now and p['info_hash']==info_hash] #this may be optimized
    shuffle(result)
    result = result[:numwant]

    if request.GET.get('compact'):
	peers = ""
	for peer in result:
	    peers += pack('>4sH', inet_aton(peer['ip']), peer['port'])
    elif request.GET.get('no_peer_id'):
	peers = []
	for peer in result:
	    peers.append({'ip': peer['ip'], 'port': peer['port']})
    else:
	peers = []
	for peer in result:
	    peers.append({'ip': peer['ip'], 'port': peer['port'], 'peer id': peer['peer_id']})

    return HttpResponse(bencode({
	    'interval': int(announce_interval),
	    'peers': peers,
	}),
	mimetype = 'text/plain')

@require_http_methods('GET')
def scrape(request):
    request.encoding = 'latin-1'
    xhr = request.GET.get('xhr')

    info_hash = request.GET.get('info_hash', '')
    if len(info_hash) < 20:
	return _fail("invalid request", xhr=xhr)
    try:
	info_hash = info_hash.encode('iso-8859-1').encode('hex')
    except:
	return _fail("invalid request", xhr=xhr)
    t = Torrent.objects.filter(info_hash=info_hash).values('id')
    if not t:
	return _fail("no such torrent", xhr=xhr)

    mc = memcache.Client([MEMCACHE], debug=0)
    peers = mc.get('peers')

    if not peers:
	peers = []

    # calculate scrape interval
    now = datetime.datetime.now()
    num_peers = len([p for p in peers if p['expire_time']>now])
    announce_rate = len([p for p in peers if p['update_time']>now-datetime.timedelta(minutes=1)])
    scrape_interval = max(num_peers * announce_rate / MAX_ANNOUNCE_RATE**2 * 60, MIN_ANNOUNCE_INTERVAL) * SCRAPE_FACTOR

    result = {info_hash: {'complete': 0, 'incomplete': 0, 'downloaded': 0}}
    for p in peers:
	if p['info_hash'] == info_hash:
	    if p['left'] == 0 and p['expire_time']>now:
		result[info_hash]['complete'] += 1
	    elif p['left'] > 0 and p['expire_time']>now:
		result[info_hash]['incomplete'] += 1
	    elif p['left'] == 0:
		result[info_hash]['downloaded'] += 1
    if xhr:
	r = HttpResponse(mimetype="text/xml")
	r.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
	r.write("""<scraper><msg>success</msg>
	    <leechers>%s</leechers>
	    <seeds>%s</seeds>
	    <downloaded>%s</downloaded>
	    </scraper>""" % (
		result[info_hash].get('incomplete', 0),
		result[info_hash].get('complete', 0),
		result[info_hash].get('downloaded', 0),
	    )
	)
	return r
    return HttpResponse(bencode({
	    'files': result,
	    'flags': {'min_request_interval': int(scrape_interval)},
	}),
    mimetype = 'text/plain')

