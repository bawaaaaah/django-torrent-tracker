#!/usr/bin/python
import sys
import os
import base64
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fs.models import Topic
from tracker.models import Torrent
from benc import bdecode, bencode
from users.models import User

user = User.objects.get(username='grey')
dest = os.path.join(os.path.dirname(__file__),'ex')

for t in Topic.objects.all():
    content = base64.b64decode(t.torrent.info)
    content = bdecode(content)
    content['announce'] += "?passkey=%s"%user.passkey
    content = bencode(content)
    f = open(os.path.join(dest, t.torrent.fn), 'wb')
    f.write(content)
    f.close()
    print t.torrent.fn