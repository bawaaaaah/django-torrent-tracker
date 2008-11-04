#!/usr/bin/python
import sys
sys.path.append('/home/grey/src/df')
import cmemcache as memcache
from settings import MEMCACHE, MIN_ANNOUNCE_INTERVAL
import datetime
mc = memcache.Client([MEMCACHE], debug=0)
peers = mc.get('peers')

now = datetime.datetime.now()
for p in peers[:]:
    if p['expire_time']<=now-datetime.timedelta(seconds=MIN_ANNOUNCE_INTERVAL*2):
	peers.remove(p)

mc.set('peers', peers)
