#!/usr/bin/python
# removes images  which not belong to any post
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from fs.models import Topic
from board.models import Post
from settings import MEDIA_ROOT
from sets import Set
proot = os.path.join(MEDIA_ROOT, 'poster')
iproot = os.path.join(MEDIA_ROOT, 'iposter')
posters = [f.poster for f in Topic.objects.all()]
posters += [f.image for f in Post.objects.all()]
files = Set(os.listdir(proot))
files.difference_update(posters)
for f in files:
    if os.path.isdir(os.path.join(proot, f)) or \
	os.path.isdir(os.path.join(iproot, f)):
	continue
    try:
	os.unlink(os.path.join(proot, f))
    except:
	pass
    try:
	os.unlink(os.path.join(iproot, f))
    except:
	pass
